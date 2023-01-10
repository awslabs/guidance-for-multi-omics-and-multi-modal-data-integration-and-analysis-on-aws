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
    create_omics_variant_store(event, context)


@helper.update
def update(event, context):
    logger.info("Got Update")
    create_omics_variant_store(event, context)


@helper.delete
def delete(event, context):
    logger.info("Got Delete - attempting to delete")
    delete_omics_variant_store(event, context)
    

@helper.poll_create
def poll_create(event, context):
    logger.info("Got Create poll")
    return check_variant_store_status(event, context)


@helper.poll_update
def poll_update(event, context):
    logger.info("Got Update poll")
    return check_variant_store_status(event, context)


@helper.poll_delete
def poll_delete(event, context):
    logger.info("Got Delete poll")
    return "poll delete"


def handler(event, context):
    helper(event, context)


def list_omics_variant_store(variant_store_name):
    try:
        response = omics_client.get_variant_store(name=variant_store_name)
    except ClientError as e:
        raise Exception( "boto3 client error : " + e.__str__())
    except Exception as e:
       raise Exception( "Unexpected error : " +    e.__str__())
    logger.info(response)
    
def create_omics_variant_store(event, context):
    
    variant_store_name = event['ResourceProperties']['VariantStoreName']
    reference_arn = event['ResourceProperties']['ReferenceArn']
    reference_arn_dict = {
        "referenceArn": reference_arn
    }
    try:
        print("Attempt to create variant store")
        response = omics_client.create_variant_store(
            name=variant_store_name,
            reference=reference_arn_dict
            )
    except ClientError as e:
        raise Exception( "boto3 client error : " + e.__str__())
    except Exception as e:
       raise Exception( "Unexpected error : " +    e.__str__())
    logger.info(response)
    helper.Data.update({"VariantStoreId": response['id']})

def delete_omics_variant_store(event, context):
    
    variant_store_name = event['ResourceProperties']['VariantStoreName']
    try:
        print("Attempt to delete variant store")
        response = omics_client.delete_variant_store(
            name=variant_store_name
            )
    except ClientError as e:
        raise Exception( "boto3 client error : " + e.__str__())
    except Exception as e:
       raise Exception( "Unexpected error : " +    e.__str__())
    logger.info(response)
    return helper.Data.get("VariantStoreId")

def check_variant_store_status(event, context):
    variant_store_name = event['ResourceProperties']['VariantStoreName']

    try:
        response = omics_client.get_variant_store(name=variant_store_name)
    except ClientError as e:
        raise Exception( "boto3 client error : " + e.__str__())
    except Exception as e:
       raise Exception( "Unexpected error : " +    e.__str__())
    status = response['status']
    
    if status in ['CREATING', 'UPDATING', 'IN_PROGRESS']:
        logger.info(status)
        return None
    else:
        if status in ['READY', 'COMPLETED', 'ACTIVE', 'COMPLETE']:
            logger.info(status)
            return True
        else:
            msg = f"Variant store; {variant_store_name} has status {status}, exiting"
            logger.info(msg)
            raise ValueError(msg)

