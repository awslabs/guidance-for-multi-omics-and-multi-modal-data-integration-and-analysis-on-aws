import io
import sys
import hashlib
import requests
from zipfile import ZipFile

from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

import boto3

API = "https://services.cancerimagingarchive.net/services/v4/TCIA/query/"

args = getResolvedOptions(sys.argv, ['JOB_NAME', 'database', 'output_bucket'])

DATABASE = args['database']
BUCKET_NAME = args['output_bucket']

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

image_series = glueContext.create_dynamic_frame.from_catalog(
    database=DATABASE,
    table_name="tcia_image_series",
    transformation_ctx="datasource0"
)


def get_image_stream_unzip(row):
    """Get Zip file from API, unpack in memory and write to S3 bucket"""
    S3_CLIENT = boto3.resource("s3")
    url = API + "getImage"
    seriesuid = row.SeriesInstanceUID
    modality = row.Modality
    parameters = {"SeriesInstanceUID": seriesuid}
    with requests.get(url, params=parameters, stream=True) as req:
        req.raise_for_status()
        with io.BytesIO() as byte_stream:
            for chunk in req.iter_content(chunk_size=10000):
                byte_stream.write(chunk)
            with ZipFile(byte_stream, "r") as zo:
                list_of_files = [i for i in zo.namelist() if i.endswith("dcm")]
                for dcm in list_of_files:
                    item = zo.read(dcm)
                    bucket_key = f"{seriesuid}/{modality}/{dcm.replace('./', '')}"
                    S3_CLIENT.Bucket(BUCKET_NAME).put_object(Key=bucket_key, Body=item)
                    print(
                        f"[INFO] Writing DICOM object: {bucket_key} to bucket: {BUCKET_NAME}\n\n"
                    )

image_series.toDF().foreach(get_image_stream_unzip)

job.commit()
