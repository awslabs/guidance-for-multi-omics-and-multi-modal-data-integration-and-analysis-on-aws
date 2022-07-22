import sys
import datetime
import requests

from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

from pyspark.sql.functions import udf, struct, explode
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DateType, ArrayType

sc = SparkContext.getOrCreate()
glueContext = GlueContext(sc)
spark = glueContext.spark_session

API = "https://services.cancerimagingarchive.net/services/v4/TCIA/query/"

args = getResolvedOptions(sys.argv, ['JOB_NAME', 'project', 'output_bucket'])
project_id = args['project']
output_bucket = args['output_bucket']


def get_patient_study(api_url, project, patient_id):
    parameters = {"format": "json", "Collection": project, "PatientID": patient_id}
    patient_study_url = api_url + "getPatientStudy"
    r = requests.get(patient_study_url, parameters)
    print(f"[INFO] GET request from:\n '{r.url}'...")
    return r.json()


def get_all_patients(api_url, project):
    parameters = {"format": "json", "Collection": project}
    url = api_url + "getPatient"
    r = requests.get(url, parameters)
    print(f"[INFO] GET request from:\n '{r.url}'...")
    return r.json()


def get_series(api_url: str, patient_id: str, study_instance_uid: str) -> list:
    """Parameter: `patient_id` and `study_instance_uid` are strings from
    an entry in `build_patient_metadata`'s returned list. Returns a
    list of all metadata and SeriesInstanceUIDs associated with
    PatientID and StudyInstanceUID. There may be many
    SeriesInstanceUIDs associated wtih a StudyInstanceUID, and many
    StudyInstanceUIDs associated wtih each Patient.

    """
    parameters = {
        "format": "json",
        "PatientID": patient_id,
        "StudyInstanceUID": study_instance_uid
    }
    url = api_url + "getSeries"
    r = requests.get(url, parameters)
    print(f"[INFO] GET request from:\n '{r.url}'...")
    return r.json()


def fmt_age(patient_dict):
    age = patient_dict.get("PatientAge", "")
    if not age:
        return None
    try:
        return int(age.replace("Y", "").replace("y", ""))
    except ValueError as e:
        print(f"[WARNING] Problem parsing: '{age}' to an integer. Exception"
              f" is '{e}'")
        return None


def fmt_date(datestr):
    if datestr is None:
        return None
    return datetime.datetime.strptime(datestr, "%Y-%m-%d").date()
    

metadata_udf_schema = ArrayType(StructType([
    StructField("Collection", StringType(), False),
    StructField("PatientID", StringType(), False),
    StructField("PatientSex", StringType(), False),
    StructField("StudyDate", DateType(), False),
    StructField("PatientAge", IntegerType(), True),
    StructField("SeriesCount", IntegerType(), False),
    StructField("StudyInstanceUID", StringType(), False),
    StructField("StudyDescription", StringType(), True)
]))

@udf(returnType=metadata_udf_schema)
def build_patient_metadata_udf(collection, patient_id):
    """builds the data table for a study given a patient."""
    r = []
    for patient_study in get_patient_study(API, collection, patient_id):
        r.append((
            patient_study["Collection"],
            patient_study["PatientID"],
            patient_study.get("PatientSex", "unknown"),
            fmt_date(patient_study["StudyDate"]),
            fmt_age(patient_study),
            patient_study["SeriesCount"],
            patient_study["StudyInstanceUID"],
            patient_study.get("StudyDescription", "")
        ))
    return r


image_udf_schema = ArrayType(StructType([
    StructField("Collection", StringType(), False),
    StructField("PatientID", StringType(), False),
    StructField("SeriesInstanceUID", StringType(), False),
    StructField("ImageCount", IntegerType(), False),
    StructField("BodyPartExamined", StringType(), True),
    StructField("Modality", StringType(), True),
    StructField("Manufacturer", StringType(), True),
    StructField("ManufacturerModelName", StringType(), True),
    StructField("ProtocolName", StringType(), True),
    StructField("SeriesDate", DateType(), True),
    StructField("SeriesDescription", StringType(), True),
    StructField("SeriesNumber", StringType(), True),
    StructField("SoftwareVersions", StringType(), True),
    StructField("Visibility", StringType(), True)
]))

@udf(returnType=image_udf_schema)
def build_image_metadata_udf(collection, patient_id, study_instance_uid):
    r = []
    for series in get_series(API, patient_id, study_instance_uid):
        r.append((
            series['Collection'],
            series['PatientID'],
            series['SeriesInstanceUID'],
            series['ImageCount'],
            series.get('BodyPartExamined'),
            series.get('Modality'),
            series.get('Manufacturer'),
            series.get('ManufacturerModelName'),
            series.get('ProtocolName'),
            fmt_date(series.get('SeriesDate')),
            series.get('SeriesDescription'),
            series.get('SeriesNumber'),
            series.get('SoftwareVersions'),
            series.get('Visibility')
        ))
    return r
            
            

## Step 1: Read a JSON structure and create a dataframe.
#
# This calls get_all_patients, passes it through the sc.parallelize()
# method to turn it into an RDD, and then uses spark.read.json() to
# turn the array into a structure with rows and columns. The resulting
# structure will mostly just be a list of patients along with their
# associated project ID.

df = spark.read.json(sc.parallelize([get_all_patients(API, project_id)]))
print(f'Patients: {df.count()} Columns: {df.columns}')
assert df.count() > 0, 'Error: no rows retrieved from API'

df = df.repartition(8)

## Step 2: Apply a UDF to the dataframe to get data on a per-patient level.
#
# We need to make one API request per patient to get the full set of
# metadata. By doing it through a UDF, PySpark will parallelize the
# requests across all of the allocated workers, which will improve
# performance.

# Apply the build_patient_metadata_udf to every row in df, and store
# the result in the Result column.
patient_df = df.withColumn(
    'Result', explode(build_patient_metadata_udf('Collection', 'PatientID'))
)
patient_df.printSchema()

# The Result column now has a nested structure with the multiple
# fields returned from build_patient_metadata_udf. We can flatten that
# out by using the select call and dot-syntax to select the nested
# columns.
patient_df = patient_df.select(
    "Collection", "PatientID", "PatientName", "PatientSex",
    "Result.StudyDate", "Result.PatientAge", "Result.SeriesCount",
    "Result.StudyInstanceUID", "Result.StudyDescription"
)
patient_df.printSchema()

## Step 3: Write the output to S3 in Parquet format.
#
# This is straightforward - define an S3 destination as a prefix (aka
# folder) and call the patient_df.write.parquet method. The
# mode("overwrite") call ensures that we are not going to append to
# data already present in that prefix.

dest = f's3://{output_bucket}/tcia-metadata/tcia-patients/{project_id}'
patient_df.write.mode("overwrite").parquet(dest)


## Now we're going to repeat this process for the images

# Get the relevant parts of the patient_df to start building the image_df
image_df = patient_df.select("Collection", "PatientID", "StudyInstanceUID")

# Apply the UDF
image_df = image_df.withColumn(
    'Result', explode(build_image_metadata_udf('Collection', 'PatientID',
                                               'StudyInstanceUID'))
)
image_df.printSchema()

image_df = image_df.select(
    "Collection", "PatientID", "StudyInstanceUID",
    "Result.SeriesInstanceUID", "Result.ImageCount", "Result.BodyPartExamined",
    "Result.Modality", "Result.Manufacturer", "Result.ManufacturerModelName",
    "Result.ProtocolName", "Result.SeriesDate", "Result.SeriesDescription",
    "Result.SeriesNumber", "Result.SoftwareVersions", "Result.Visibility"
)
image_df.printSchema()

dest = f's3://{output_bucket}/tcia-metadata/tcia-image-series/{project_id}'
image_df.write.mode("overwrite").parquet(dest)
