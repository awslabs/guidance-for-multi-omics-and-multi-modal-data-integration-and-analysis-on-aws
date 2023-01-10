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
    create_omics_annotation_store(event, context)


@helper.update
def update(event, context):
    logger.info("Got Update")
    create_omics_annotation_store(event, context)


@helper.delete
def delete(event, context):
    logger.info("Got Delete - attempt to delete")
    delete_omics_annotation_store(event, context)
    
@helper.poll_create
def poll_create(event, context):
    logger.info("Got Create poll")
    return check_annotation_store_status(event, context)


@helper.poll_update
def poll_update(event, context):
    logger.info("Got Update poll")
    return check_annotation_store_status(event, context)


@helper.poll_delete
def poll_delete(event, context):
    logger.info("Got Delete poll")
    return "got delete"

def handler(event, context):
    helper(event, context)

def create_omics_annotation_store(event, context):
    annotation_store_name = event['ResourceProperties']['AnnotationStoreName']
    reference_arn = event['ResourceProperties']['ReferenceArn']
    store_format = event['ResourceProperties']['AnnotationStoreFormat']
    try:
        print(f"Attempt to create annotation store: {annotation_store_name}")
        response = omics_client.create_annotation_store(
            name=annotation_store_name,
            reference={"referenceArn": reference_arn},
            storeFormat=store_format
            )
    except ClientError as e:
        raise Exception( "boto3 client error : " + e.__str__())
    except Exception as e:
       raise Exception( "Unexpected error : " +    e.__str__())
    logger.info(response)
    helper.Data.update({"AnnotationStoreId": response['id']})
    return True

def delete_omics_annotation_store(event, context):
    
    annotation_store_name = event['ResourceProperties']['AnnotationStoreName']
    try:
        print("Attempt to delete annotation store")
        response = omics_client.delete_annotation_store(
            name=annotation_store_name
            )
    except ClientError as e:
        raise Exception( "boto3 client error : " + e.__str__())
    except Exception as e:
       raise Exception( "Unexpected error : " +    e.__str__())
    logger.info(response)
    return helper.Data.get("AnnotationStoreId")

def check_annotation_store_status(event, context):
    annotation_store_name = event['ResourceProperties']['AnnotationStoreName']

    try:
        response = omics_client.get_annotation_store(name=annotation_store_name)
    except ClientError as e:
        raise Exception( "boto3 client error : " + e.__str__())
    except Exception as e:
       raise Exception( "Unexpected error : " +    e.__str__())
    status = response['status']
    
    if status in ['CREATING', 'UPDATING', 'IN_PROGRESS']:
        logger.info(status)
        return None
    else:
        if status in ['READY', 'COMPLETED', 'ACTIVE', 'CREATED', 'COMPLETE']:
            logger.info(status)
            return True
        else:
            msg = f"Variant store; {annotation_store_name} has status {status}, exiting"
            logger.info(msg)
            raise ValueError(msg)  

