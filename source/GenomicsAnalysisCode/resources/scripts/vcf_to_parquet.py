import sys

from pyspark import SparkContext, SparkConf

from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from awsglue.job import Job

import hail as hl

hl.init(
    app_name='Running Hail on Glue',
    default_reference='GRCh38',
    spark_conf={
        'spark.sql.files.maxPartitionBytes': '1099511627776',
        'spark.sql.files.openCostInBytes': '1099511627776'
    }
)

sc = SparkContext.getOrCreate()

args = getResolvedOptions(sys.argv, ['JOB_NAME', 'input_path', 'output_path'])

glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)


vds = hl.import_vcf(args['input_path'])

vds.make_table().to_spark().write.mode('overwrite').parquet(args['output_path'])

job.commit()
