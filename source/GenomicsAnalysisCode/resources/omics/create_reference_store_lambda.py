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
    create_omics_reference_store(event, context)


@helper.update
def update(event, context):
    logger.info("Got Update")
    create_omics_reference_store(event, context)


@helper.delete
def delete(event, context):
    logger.info("Got Delete - attempting to delete")
    delete_omics_reference_store(event, context)

@helper.poll_create
def poll_create(event, context):
    logger.info("Got Create poll")
    return True


@helper.poll_update
def poll_update(event, context):
    logger.info("Got Update poll")
    return True

@helper.poll_delete
def poll_delete(event, context):
    logger.info("Got Delete poll")
    return True

def handler(event, context):
    helper(event, context)

def create_omics_reference_store(event, context):
    reference_store_name = event['ResourceProperties']['ReferenceStoreName']
    try:
        print(f"Attempt to create reference store: {reference_store_name}")
        response = omics_client.create_reference_store(
            name=reference_store_name
            )
    except ClientError as e:
        raise Exception( "boto3 client error : " + e.__str__())
    except Exception as e:
       raise Exception( "Unexpected error : " +    e.__str__())
    logger.info(response)
    helper.Data.update({"ReferenceStoreArn": response['arn']})
    helper.Data.update({"ReferenceStoreId": response['id']})
    return True

def delete_omics_reference_store(event, context):
    reference_store_name = event['ResourceProperties']['ReferenceStoreName']
    # list reference store and filter by name
    try:
        reference_stores = omics_client.list_reference_stores(filter={
            "name": reference_store_name
        })
    except ClientError as e:
        raise Exception( "boto3 client error : " + e.__str__())
    except Exception as e:
       raise Exception( "Unexpected error : " +    e.__str__())
    if reference_stores is None:
        return "No reference stores found"
    else:
        if "referenceStores" in reference_stores and reference_stores["referenceStores"] == 0:
            return "No reference stores found"
        else:
            reference_store_id = reference_stores["referenceStores"][0]['id']      
    # get references
    try:
        references = omics_client.list_references(referenceStoreId=reference_store_id)
    except ClientError as e:
        raise Exception( "boto3 client error : " + e.__str__())
    except Exception as e:
       raise Exception( "Unexpected error : " +    e.__str__())
    
    # delete all references
    ids = []
    if "references" not in references:
        print("No references found in reference store")
    else:
        for i in references["references"]:
            print(i)
            ids.append(i['id'])
        for _id in ids:
            try:
                print(f"deleting reference with id: {_id}")
                response = omics_client.delete_reference(id=_id, referenceStoreId=reference_store_id)
            except ClientError as e:
                raise Exception( "boto3 client error : " + e.__str__())
            except Exception as e:
                raise Exception( "Unexpected error : " +    e.__str__())
            logger.info(response)
    
    # delete reference store
    try:
        print(f"Attempt to delete reference store: {reference_store_name}")
        response = omics_client.delete_reference_store(
            id=reference_store_id
            )
    except ClientError as e:
        raise Exception( "boto3 client error : " + e.__str__())
    except Exception as e:
       raise Exception( "Unexpected error : " +    e.__str__())
    logger.info(response)
    return reference_store_id
