import boto3
import pandas as pd
import io
import re
import time
import sys

from awsglue.utils import getResolvedOptions

args = getResolvedOptions(sys.argv, ['database', 'bucket'])

session = boto3.Session()

def start_query_execution(client, params):
    
    response = client.start_query_execution(
        QueryString=params["query"],
        QueryExecutionContext={
            'Database': params['database']
        },
        ResultConfiguration={
            'OutputLocation': 's3://' + params['bucket'] + '/' + params['path']
        }
    )
    return response

def run_query(session, params, max_execution = 5):
    client = session.client('athena')
    execution = start_query_execution(client, params)
    execution_id = execution['QueryExecutionId']
    state = 'RUNNING'

    while (max_execution > 0 and state in ['RUNNING']):
        max_execution = max_execution - 1
        response = client.get_query_execution(QueryExecutionId = execution_id)

        if 'QueryExecution' in response and \
                'Status' in response['QueryExecution'] and \
                'State' in response['QueryExecution']['Status']:
            state = response['QueryExecution']['Status']['State']
            if state == 'FAILED':
                return None
            elif state == 'SUCCEEDED':
                response = client.get_query_results(QueryExecutionId=execution_id)
                if 'ResultSet' in response and 'Rows' in response['ResultSet']:
                    return response['ResultSet']['Rows']
                else:
                    return None
        time.sleep(1)
    
    return None

rows = run_query(session, params={
    'database': args['database'],
    'bucket': args['bucket'],
    'path': 'results/test/annotation',
    'query': 'select * from clinvar limit 10;'
})
assert len(rows) == 10 + 1

rows = run_query(session, params={
    'database': args['database'],
    'bucket': args['bucket'],
    'path': 'results/test/vcf',
    'query': 'select * from vcf limit 10;'
})
assert len(rows) == 10 + 1

rows = run_query(session, params={
    'database': args['database'],
    'bucket': args['bucket'],
    'path': 'results/test/cohort',
    'query': 'select * from onekg_chr22_by_sample limit 10;'
})
assert len(rows) == 10 + 1