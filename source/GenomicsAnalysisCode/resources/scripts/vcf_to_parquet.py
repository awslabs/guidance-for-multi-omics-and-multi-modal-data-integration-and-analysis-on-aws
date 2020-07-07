import sys

from pyspark import SparkContext, SparkConf

from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from awsglue.job import Job

from hail import *

conf = SparkConf()
conf.set('spark.app.name', u'Running Hail on Glue')
conf.set('spark.sql.files.maxPartitionBytes', '1099511627776')
conf.set('spark.sql.files.openCostInBytes', '1099511627776')

sc = SparkContext(conf=conf)
sc._jsc.hadoopConfiguration().set("mapred.output.committer.class", "org.apache.hadoop.mapred.FileOutputCommitter")
sc.getConf().getAll()

args = getResolvedOptions(sys.argv, ['JOB_NAME', 'input_path', 'output_path'])

glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

hc = HailContext(sc)
vds = hc.import_vcf(args['input_path'])

vds.variants_table().to_dataframe().write.mode('overwrite').parquet(args['output_path'])

job.commit()
