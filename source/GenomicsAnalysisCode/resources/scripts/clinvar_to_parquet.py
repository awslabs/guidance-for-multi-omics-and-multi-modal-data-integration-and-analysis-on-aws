import sys
import urllib2
import StringIO
import gzip

from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.types import Row, StringType, IntegerType, ArrayType, StructType, DoubleType, BooleanType, DateType

args = getResolvedOptions(sys.argv, ['JOB_NAME', 'input_path', 'output_path'])

sc = SparkContext.getOrCreate()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)

schema = StructType() \
    .add("AlleleID", StringType(), True) \
    .add("Type", StringType(), True) \
    .add("Name", StringType(), True) \
    .add("GeneID", StringType(), True) \
    .add("GeneSymbol", StringType(), True) \
    .add("HGNC_ID", StringType(), True) \
    .add("ClinicalSignificance", StringType(), True) \
    .add("ClinSigSimple", StringType(), True) \
    .add("LastEvaluated", StringType(), True) \
    .add("RSID", StringType(), True) \
    .add("DBVarID", StringType(), True) \
    .add("RCVaccession", StringType(), True) \
    .add("PhenotypeIDS", StringType(), True) \
    .add("PhenotypeList", StringType(), True) \
    .add("Origin", StringType(), True) \
    .add("OriginSimple", StringType(), True) \
    .add("Assembly", StringType(), True) \
    .add("ChromosomeAccession", StringType(), True) \
    .add("Chromosome", StringType(), True) \
    .add("Start", StringType(), True) \
    .add("Stop", StringType(), True) \
    .add("ReferenceAllele", StringType(), True) \
    .add("AlternateAllele", StringType(), True) \
    .add("Cytogenetic", StringType(), True) \
    .add("ReviewStatus", StringType(), True) \
    .add("NumberSubmitters", StringType(), True) \
    .add("Guidelines", StringType(), True) \
    .add("TestedInGTR", StringType(), True) \
    .add("OtherIDs", StringType(), True) \
    .add("SubmitterCategories", StringType(), True) \
    .add("VariationID", StringType(), True) \

df = spark.read.option("sep", "\t").csv(args['input_path'], header=True, mode="DROPMALFORMED", schema=schema)
df = df.withColumn("Start", df["Start"].cast(IntegerType()))
df = df.withColumn("Stop", df["Stop"].cast(IntegerType()))

df.write.mode('overwrite').parquet(args['output_path'])

job.commit()

