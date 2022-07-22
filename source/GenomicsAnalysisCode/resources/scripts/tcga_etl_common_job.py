# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
### Glue job to fetch and aggregate gene expression data from TCGA
## Command line arguments:
## --project - the TCGA project (e.g TCGA-BRCA for breast cancer)
## --output_bucket - the output bucket where results are to be written to
## --data_type - the type of data to be retrieved

import sys, os
import re
import boto3
import requests 
import json
import pandas as pd
import gzip

from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.types import Row, StringType, IntegerType, ArrayType, \
    StructType, DoubleType, BooleanType, DateType
from pyspark.sql.functions import input_file_name, concat, col
from pyspark.sql.functions import first, last
from pyspark.sql.types import IntegerType
from pyspark.sql.functions import udf, struct, explode

sc = SparkContext.getOrCreate()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)


## Get the argumentlist

args = getResolvedOptions(
    sys.argv,
    ['JOB_NAME', 'project', 'data_type', 'output_bucket']
)

## The GDC endpoint for files and the NCI endpoint to query for the S3 URL

files_endpt = 'https://api.gdc.cancer.gov/files'
data_endpt = 'https://api.gdc.cancer.gov/data'

s3 = boto3.resource('s3')
output_bucket = args['output_bucket']

project_id = args['project']


def get_data(uuid, sample_submitter_id):
    """Query the NCI endpoint for the S3 path.

    Inputs to this method are the UUID and submitter ID from the GDC
    endpoint query.

    """
    s3c = boto3.client('s3')
    query_response = requests.get(data_endpt + "/" + uuid)
    if 'Content-Disposition' in query_response.headers:
        filename = re.findall(
            r'filename=(.+)',
            query_response.headers['content-disposition']
        )[0]
        filename = filename.strip('"\'')
    else:
        filename = uuid
    key = f'tcga-raw-objects-by-uuid/{uuid}/{filename}'
    s3c.put_object(Bucket=output_bucket, Key=key, Body=query_response.content)
    return f's3://{output_bucket}/{key}'
    

### Step 1: Query the GDC endpoint to retrieve the list of files
### associated with the specified project.

# Build a comma-separated list of fields
fields = [
    "file_name",
    "cases.primary_site",
    "cases.case_id",
    "cases.project.project_id",
    "cases.submitter_id",
    "cases.samples.submitter_id",
    "cases.samples.sample_id",

]
fields = ','.join(fields)

size = 5000
data_type = args['data_type']

# Define the core filters for the query
filters = {
    "op": "and",
    "content":[{
        "op": "in",
        "content": {
            "field": "cases.project.project_id",
            "value": [project_id]
        }
    }, {
        "op": "in",
        "content": {
            "field": "files.data_type",
            "value": [data_type]
        }
    }]
}

# Add additional filters on a per-data-type basis
if data_type == 'Gene Expression Quantification':
    exp_wftype = 'STAR-Counts'
    exp_wftype_filter = 'STAR - Counts'
    
    filters['content'].append({
        "op": "in",
        "content": {
            "field": "files.analysis.workflow_type",
            "value": [exp_wftype_filter]
        }
    })

elif data_type == 'Gene Level Copy Number':
    filters['content'].append({
        "op": "in",
        "content": {
            "field": "files.data_category",
            "value": ["Copy Number Variation"]
        }
    })

elif data_type == 'Masked Somatic Mutation':
    filters['content'].extend([{
        "op": "in",
        "content": {
            "field": "files.data_category",
            "value": ["Simple Nucleotide Variation"]
        }
    }, {
        "op": "in",
        "content": {
            "field": "files.data_format",
            "value": ["MAF"]
        }
    }])
    
elif data_type == 'Clinical Supplement':
    filters['content'].extend([{
        "op": "in",
        "content": {
            "field": "files.data_category",
            "value": ["Clinical"]
        }
    }, {
        "op": "in",
        "content": {
            "field": "files.data_format",
            "value": ["BCR Biotab"]
        }
    }])

# With a GET request, the filters parameter needs to be converted
# from a dictionary to JSON-formatted string

params = {
    "filters": json.dumps(filters),
    "fields": fields,
    "format": "JSON",
    "size": size
}

# query the files endpoint and get back JSON response
query_response = requests.get(files_endpt, params=params)
json_response = json.loads(
    query_response.content.decode("utf-8"))["data"]["hits"]

print(len(json_response))


### Step 2: Read the query response into a Spark DataFrame, and then
### use Spark parallelization to resolve the file UUID to an S3 path
### via the UDF defined above.

# Parallel read of JSON object and repartition to distribute to all workers
df = spark.read.json(sc.parallelize([json_response]))
df2 = df.repartition(8)

if data_type == 'Gene Expression Quantification':
    uf = df2.select(
        "id",
        explode(df2.cases.samples)
    ).toDF(
        "id", "samples"
    ).select(
        'id','samples.submitter_id','samples.sample_id'
    )

else:
    uf = df2.select(
        'id', 'cases.submitter_id'
    )
    
# Call the get_data() function defined above as a Spark user-defined
# function (UDF) to convert the UUIDs stored in the 'id' column into
# S3 paths. This is done using this mechanism in order to parallelize
# the process, improving throughput.
urldf = udf(get_data)
inputpath = uf.withColumn('Result', urldf('id', 'submitter_id'))

# Convert the data frame back into a native Python list
inputlist = list(inputpath.select('Result').toPandas()['Result'])


### Step 3: Read the CSV files in the input list and perform any
### required per-data-type translation.

if data_type == 'Clinical Supplement':
    
    ## Clinical data is treated differently since we will process each
    ## input file individually to create one table for each type of
    ## clinical data available.    
    for filename in inputlist:
        dfname = os.path.splitext(
            os.path.basename(filename)
        )[0].replace("nationwidechildrens.org_","")
        trim = max(i for i in range(len(project_id))
                   if dfname.lower().endswith(project_id[-i:].lower()))
        dfname = dfname[:-trim].rstrip('_')

        # Read the file in CSV format into a dataframe
        output_df = spark.read.option("sep","\t").csv(filename,header=True)

        # Remove rows that have obviously superfluous data
        any_column = output_df.columns[0]
        output_df = output_df.filter(~ (
            (output_df[any_column] == any_column) | 
            (output_df[any_column].startswith('CDE_ID:'))
        ))
        
        table_part = f'{dfname}/{project_id}'
        if dfname == 'clinical_nte':
            # workaround for one table
            table_part = f'{dfname}_{project_id}'
        
        dest = f's3://{output_bucket}/tcga-clinical/{table_part}'
        output_df.write.mode("overwrite").parquet(dest)
    
else:
    ## Read the inputlist into a single dataframe

    # Certain data types require specific read options or pre-processing
    if data_type == 'Gene Expression Quantification':
        data = spark.read.option("sep", "\t").csv(
            inputlist, header=True, mode="DROPMALFORMED", comment="#",
            inferSchema=True
        )
        data = data.filter(~ (data.gene_id.startswith('N_')))

    elif data_type == 'Masked Somatic Mutation':
        data = spark.read.format("csv")\
            .option("header", "true")\
            .option("inferSchema", "true")\
            .option("delimiter", "\t")\
            .option("comment", "#")\
            .load(inputlist)

        # Reformat submitter_id column
        data = data.withColumn('new_submitter_id',
                               data.Tumor_Sample_Barcode.substr(1, 12))
        
    else:
        data = spark.read.option("sep", "\t").csv(
            inputlist, header=True, mode="DROPMALFORMED"
        )

    ## Add a column with file path, which adds the s3 file path from which
    ## row is extracted
    data = data.withColumn("fullpath", input_file_name())

    ## Add a column which is a substring of full s3 path and gives
    ## filename so that we can match and join with Json data
    data = data.withColumn("file", data.fullpath.substr(55,100))
    if data_type in ('Gene Level Copy Number',
                     'Gene Expression Quantification'):
        data = data.withColumn("EnsemblGene", data.gene_id.substr(1,15))

    ## Join the data with the frame that includes submitter ID
    output_df = data.join(inputpath,data["fullpath"]==inputpath["Result"])

    ## Perform per-data-type post-processing and define the destination path
        
    if data_type == 'Gene Expression Quantification':
        ## Select only relevant columns
        expression_col = 'tpm_unstranded'
        allgene = output_df.select(
            "EnsemblGene",
            output_df["submitter_id"].getItem(0),
            expression_col
        ).withColumnRenamed("submitter_id[0]", "submitter_id")

        ## Pivot the dataframe to form the expression matrix
        output_df = allgene.groupBy('EnsemblGene') \
                           .pivot('submitter_id') \
                           .agg(first(expression_col))
        dest = f's3://{output_bucket}/tcga-expression/expression_{project_id}/{exp_wftype}'

    elif data_type == 'Gene Level Copy Number':
        dest = f's3://{output_bucket}/tcga-cnv/{project_id}'

    elif data_type == 'Masked Somatic Mutation':
        output_df = output_df.drop('submitter_id')\
                             .withColumnRenamed('new_submitter_id',
                                                'submitter_id')
        
        dest = f's3://{output_bucket}/tcga-mutation/{project_id}'
        
    ## Write the data frame to the output bucket
    output_df.write.mode("overwrite").parquet(dest)

    
job.commit()
