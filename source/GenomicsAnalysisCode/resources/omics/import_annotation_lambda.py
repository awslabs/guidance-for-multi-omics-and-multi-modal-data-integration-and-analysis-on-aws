# /*********************************************************************************************************************
# *  Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.                                           *
# *                                                                                                                    *
# *  Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file except in compliance    *
# *  with the License. A copy of the License is located at                                                             *
# *                                                                                                                    *
# *      http://www.apache.org/licenses/LICENSE-2.0                                                                    *
# *                                                                                                                    *
# *  or in the 'license' file accompanying this file. This file is distributed on an 'AS IS' BASIS, WITHOUT WARRANTIES *
# *  OR CONDITIONS OF ANY KIND, express or implied. See the License for the specific language governing permissions    *
# *  and limitations under the License.                                                                                *
# *********************************************************************************************************************/

from crhelper import CfnResource
import logging
import boto3
from botocore.exceptions import ClientError 

logger = logging.getLogger(__name__)
# Initialise the helper, all inputs are optional, this example shows the defaults
helper = CfnResource(json_logging=False, log_level='DEBUG', boto_level='CRITICAL')

# Initiate client
try:
    print("Attempt to initiate client")
    omics_session = boto3.Session()
    omics_client = omics_session.client('omics')
    print("Attempt to initiate client complete")
except Exception as e:
    helper.init_failure(e)


@helper.create
def create(event, context):
    logger.info("Got Create")
    import_annotation(event, context)


@helper.update
def update(event, context):
    logger.info("Got Update")
    import_annotation(event, context)


@helper.delete
def delete(event, context):
    logger.info("Got Delete")
    return "delete"
    # Delete never returns anything. Should not fail if the underlying resources are already deleted. Desired state.

@helper.poll_create
def poll_create(event, context):
    logger.info("Got Create poll")
    return check_annotation_import_status(event, context)


@helper.poll_update
def poll_update(event, context):
    logger.info("Got Update poll")
    return check_annotation_import_status(event, context)


@helper.poll_delete
def poll_delete(event, context):
    logger.info("Got Delete poll")
    return "delete poll"

def handler(event, context):
    helper(event, context)

def import_annotation(event, context):
    omics_import_role_arn = event['ResourceProperties']['OmicsImportAnnotationRoleArn']
    annotation_source_s3_uri = event['ResourceProperties']['AnnotationSourceS3Uri']
    annotation_store_name = event['ResourceProperties']['AnnotationStoreName']
    try:
        print(f"Attempt to import annotation file: {annotation_source_s3_uri} to store: {annotation_store_name}")
        response = omics_client.start_annotation_import_job(
            destinationName=annotation_store_name,
            roleArn=omics_import_role_arn,
            items=[{'source': annotation_source_s3_uri}]
            )
    except ClientError as e:
        raise Exception( "boto3 client error : " + e.__str__())
    except Exception as e:
       raise Exception( "Unexpected error : " +    e.__str__())
    logger.info(response)
    helper.Data.update({"AnnotationImportJobId": response['jobId']})
    return True

def check_annotation_import_status(event, context):
    annotation_import_job_id = helper.Data.get("AnnotationImportJobId")

    try:
        response = omics_client.get_annotation_import_job(
            jobId=annotation_import_job_id
            )
    except ClientError as e:
        raise Exception( "boto3 client error : " + e.__str__())
    except Exception as e:
       raise Exception( "Unexpected error : " +    e.__str__())
    status = response['status']
    
    if status in ['SUBMITTED', 'IN_PROGRESS', 'RUNNING', 'CREATING', 'QUEUED']:
        logger.info(status)
        return None
    else:
        if status in ['READY', 'ACTIVE', 'COMPLETED', 'COMPLETE']:
            logger.info(status)
            return True
        else:
            msg = f"Annotation Import Job ID : {annotation_import_job_id} has status {status}, exiting"
            logger.info(msg)
            raise ValueError(msg)

