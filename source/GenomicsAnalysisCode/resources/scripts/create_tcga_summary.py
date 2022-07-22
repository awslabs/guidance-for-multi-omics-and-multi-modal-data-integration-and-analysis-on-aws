import boto3
import pandas as pd
import io
import re
import time
import sys
import json

from awsglue.utils import getResolvedOptions

args = getResolvedOptions(sys.argv, ['database', 'bucket', 'workgroup'])

session = boto3.Session()

def start_query_execution(client, params):
    response = client.start_query_execution(
        QueryString=params["query"],
        QueryExecutionContext={
            'Database': params['database']
        },
        ResultConfiguration={
            'OutputLocation': 's3://' + params['bucket'] + '/' + params['path']
        },
        WorkGroup=params['workgroup']
    )
    return response

def run_query(session, params, max_execution=6):
    print(json.dumps(params))
    print(params['query'])
    client = session.client('athena')
    execution = start_query_execution(client, params)
    execution_id = execution['QueryExecutionId']
    state = 'RUNNING'

    while max_execution > 0 and state in ['RUNNING']:
        time.sleep(5)
        max_execution = max_execution - 1
        response = client.get_query_execution(QueryExecutionId=execution_id)
        print(response)

        if 'QueryExecution' in response and \
                'Status' in response['QueryExecution'] and \
                'State' in response['QueryExecution']['Status']:
            state = response['QueryExecution']['Status']['State']
            if state == 'FAILED':
                raise Exception('Athena query execution failed: ' + str(response['QueryExecution']['Status']))
            elif state == 'SUCCEEDED':
                response = client.get_query_results(QueryExecutionId=execution_id)
                print(response)
                if 'ResultSet' in response and 'Rows' in response['ResultSet']:
                    return response['ResultSet']['Rows']
                else:
                    return None

# If the tcga_summary table exists, remove it along with its data
rows = run_query(session, params={
    'workgroup': args['workgroup'],
    'database': args['database'],
    'bucket': args['bucket'],
    'path': 'results/create-summary',
    'query': "DROP TABLE IF EXISTS tcga_summary;"
})
print(rows)

s3 = boto3.resource('s3')
s3_bucket = s3.Bucket(args['bucket'])
s3_bucket.objects.filter(Prefix="tcga-summary/").delete()

# This is the main query to create the tcga_summary table. It consists
# of a SELECT from the clinical_patient table, with a number of joins
# which count the number of records in the other tables in the data
# set.
QUERY = """
CREATE TABLE tcga_summary 
WITH (
    external_location = 's3://{bucket}/tcga-summary/',
    format = 'PARQUET',
    parquet_compression = 'SNAPPY'
)
AS
SELECT clinical_patient.bcr_patient_barcode as patient_id,
    QTY_IMGS.quantity as num_images,
    QTY_IMG_SER.quantity as num_image_series,
    QTY_MUT.quantity as num_mutation_records,
    QTY_EXP.quantity as num_expression_records,
    QTY_CNV.quantity as num_cnv_records,
    QTY_CLIN_DRUG.quantity as num_clin_drug_records,
    QTY_CLIN_RAD.quantity as num_clin_rad_records,
    QTY_CLIN_FOL.quantity as num_clin_fol_records,
    QTY_CLIN_OMF.quantity as num_clin_omf_records,
    QTY_CLIN_NTE.quantity as num_clin_nte_records
FROM clinical_patient

LEFT JOIN
    (   SELECT COUNT(tcia_patients.patientid) AS quantity, 
            tcia_patients.patientid 
        FROM tcia_patients
        GROUP BY tcia_patients.patientid
    ) AS QTY_IMGS
ON clinical_patient.bcr_patient_barcode = QTY_IMGS.patientid

LEFT JOIN
    (   SELECT COUNT(tcia_image_series.patientid) AS quantity, 
            tcia_image_series.patientid 
        FROM tcia_image_series
        GROUP BY tcia_image_series.patientid
    ) AS QTY_IMG_SER
ON clinical_patient.bcr_patient_barcode = QTY_IMG_SER.patientid

LEFT JOIN
    (   SELECT COUNT(tcga_mutation.submitter_id) AS quantity, 
            tcga_mutation.submitter_id
        FROM tcga_mutation
        GROUP BY tcga_mutation.submitter_id
    ) AS QTY_MUT
ON clinical_patient.bcr_patient_barcode = QTY_MUT.submitter_id

-- The expression data is stored in a unique format - each patient ID is a column in one of two tables.
-- In order to query this, we use the `information_schema` special table which contains the metadata
-- about all tables in the database. This special table is first filtered and transformed via a computed
-- table expression and then grouped and joined to match the results of the other tables.
LEFT JOIN     
    (   WITH expression_patients AS (
            SELECT upper(substring(column_name, 1, 12)) AS patientid
            FROM information_schema.columns
            WHERE table_schema = '{database_name}'
            AND table_name LIKE 'expression_tcga_%'
            AND upper(column_name) LIKE 'TCGA-%'
        )
        SELECT COUNT(expression_patients.patientid) AS quantity, 
            expression_patients.patientid
        FROM expression_patients
        GROUP BY expression_patients.patientid
    ) AS QTY_EXP
ON clinical_patient.bcr_patient_barcode = QTY_EXP.patientid

LEFT JOIN
    (   SELECT COUNT(tcga_cnv.submitter_id[1]) AS quantity, 
            tcga_cnv.submitter_id[1] as submitter_id
        FROM tcga_cnv
        WHERE copy_number IS NOT NULL
        GROUP BY tcga_cnv.submitter_id[1]
    ) AS QTY_CNV
ON clinical_patient.bcr_patient_barcode = QTY_CNV.submitter_id

LEFT JOIN
    (   SELECT COUNT(clinical_drug.bcr_patient_barcode) AS quantity, 
            clinical_drug.bcr_patient_barcode
        FROM clinical_drug
        GROUP BY clinical_drug.bcr_patient_barcode
    ) AS QTY_CLIN_DRUG
ON clinical_patient.bcr_patient_barcode = QTY_CLIN_DRUG.bcr_patient_barcode

LEFT JOIN
    (   SELECT COUNT(clinical_radiation.bcr_patient_barcode) AS quantity, 
            clinical_radiation.bcr_patient_barcode
        FROM clinical_radiation
        GROUP BY clinical_radiation.bcr_patient_barcode
    ) AS QTY_CLIN_RAD
ON clinical_patient.bcr_patient_barcode = QTY_CLIN_RAD.bcr_patient_barcode

LEFT JOIN
    (   SELECT COUNT(clinical_follow_up_v1_0.bcr_patient_barcode) AS quantity, 
            clinical_follow_up_v1_0.bcr_patient_barcode
        FROM clinical_follow_up_v1_0
        GROUP BY clinical_follow_up_v1_0.bcr_patient_barcode
    ) AS QTY_CLIN_FOL
ON clinical_patient.bcr_patient_barcode = QTY_CLIN_FOL.bcr_patient_barcode

LEFT JOIN
    (   SELECT COUNT(clinical_omf_v4_0.bcr_patient_barcode) AS quantity, 
            clinical_omf_v4_0.bcr_patient_barcode
        FROM clinical_omf_v4_0
        GROUP BY clinical_omf_v4_0.bcr_patient_barcode
    ) AS QTY_CLIN_OMF
ON clinical_patient.bcr_patient_barcode = QTY_CLIN_OMF.bcr_patient_barcode

-- The NTE data is split across two tables, so in order to have one quantity for both tables, we union
-- the results of the same query together.

LEFT JOIN
    (   SELECT COUNT(clinical_nte_tcga_luad.bcr_patient_barcode) AS quantity, 
            clinical_nte_tcga_luad.bcr_patient_barcode
        FROM clinical_nte_tcga_luad
        GROUP BY clinical_nte_tcga_luad.bcr_patient_barcode
        UNION ALL 
        SELECT COUNT(clinical_nte_tcga_lusc.bcr_patient_barcode) AS quantity,
            clinical_nte_tcga_lusc.bcr_patient_barcode
        FROM clinical_nte_tcga_lusc
        GROUP BY clinical_nte_tcga_lusc.bcr_patient_barcode
    ) AS QTY_CLIN_NTE
ON clinical_patient.bcr_patient_barcode = QTY_CLIN_NTE.bcr_patient_barcode
""".format(database_name=args['database'], bucket=args['bucket'])

rows = run_query(session, params={
    'workgroup': args['workgroup'],
    'database': args['database'],
    'bucket': args['bucket'],
    'path': 'results/create-summary',
    'query': QUERY
})
print(rows)
