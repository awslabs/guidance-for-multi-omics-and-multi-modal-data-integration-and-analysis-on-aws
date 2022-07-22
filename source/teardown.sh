#!/bin/bash

export AWS_DEFAULT_OUTPUT=text

export RESOURCE_PREFIX=${PROJECT_NAME:-GenomicsAnalysis}
export RESOURCE_PREFIX_LOWERCASE=$(echo ${RESOURCE_PREFIX} | tr '[:upper:]' '[:lower:]')

export ZONE_STACKNAME=${RESOURCE_PREFIX}-LandingZone
export PIPE_STACKNAME=${RESOURCE_PREFIX}-Pipeline
export GENE_STACKNAME=${RESOURCE_PREFIX}-Genomics
export IMG_STACKNAME=${RESOURCE_PREFIX}-Imaging
export QS_STACKNAME=${RESOURCE_PREFIX}-Quicksight

export REPOSITORY_NAME=${RESOURCE_PREFIX_LOWERCASE}

HAS_QS_STACK=$(aws cloudformation describe-stacks --stack-name ${QS_STACKNAME} && echo 1)
HAS_GENE_STACK=$(aws cloudformation describe-stacks --stack-name ${GENE_STACKNAME} && echo 1)
HAS_IMG_STACK=$(aws cloudformation describe-stacks --stack-name ${IMG_STACKNAME} && echo 1)
HAS_PIPE_STACK=$(aws cloudformation describe-stacks --stack-name ${PIPE_STACKNAME} && echo 1)
HAS_ZONE_STACK=$(aws cloudformation describe-stacks --stack-name ${ZONE_STACKNAME} && echo 1)

set -e

# Clear Buckets

if [[ -n $HAS_PIPE_STACK ]]; then
    BUILD_BUCKET=$(aws cloudformation describe-stacks --stack-name ${PIPE_STACKNAME} --query 'Stacks[].Outputs[?OutputKey==`BuildBucket`].OutputValue'); echo ${BUILD_BUCKET}
    RESOURCES_BUCKET=$(aws cloudformation describe-stacks --stack-name ${PIPE_STACKNAME} --query 'Stacks[].Outputs[?OutputKey==`ResourcesBucket`].OutputValue'); echo ${RESOURCES_BUCKET}
    DATALAKE_BUCKET=$(aws cloudformation describe-stacks --stack-name ${PIPE_STACKNAME} --query 'Stacks[].Outputs[?OutputKey==`DataLakeBucket`].OutputValue'); echo ${DATALAKE_BUCKET}
    LOGS_BUCKET=$(aws cloudformation describe-stacks --stack-name ${PIPE_STACKNAME} --query 'Stacks[].Outputs[?OutputKey==`LogsBucket`].OutputValue'); echo ${LOGS_BUCKET}

    [[ -n $BUILD_BUCKET ]] && aws s3 rm --recursive s3://${BUILD_BUCKET}/
    [[ -n $RESOURCES_BUCKET ]] && aws s3 rm --recursive s3://${RESOURCES_BUCKET}/
    [[ -n $DATALAKE_BUCKET ]] && aws s3 rm --recursive s3://${DATALAKE_BUCKET}/
    [[ -n $LOGS_BUCKET ]] && aws s3 rm --recursive s3://${LOGS_BUCKET}/ 
fi

# Disable Termination Protection on Stacks

[[ -n $HAS_PIPE_STACK ]] && aws cloudformation update-termination-protection --no-enable-termination-protection --stack-name ${PIPE_STACKNAME} 
[[ -n $HAS_ZONE_STACK ]] && aws cloudformation update-termination-protection --no-enable-termination-protection --stack-name ${ZONE_STACKNAME}

# Get Repo Names from Stacks

PIPE_REPO=$(aws cloudformation describe-stacks --stack-name ${ZONE_STACKNAME} --query 'Stacks[].Outputs[?OutputKey==`RepoName`].OutputValue'); echo ${PIPE_REPO}
CODE_REPO=$(aws cloudformation describe-stacks --stack-name ${PIPE_STACKNAME} --query 'Stacks[].Outputs[?OutputKey==`RepoName`].OutputValue'); echo ${CODE_REPO}

# Delete Stacks

if [[ -n $HAS_QS_STACK ]]; then
    aws cloudformation delete-stack --stack-name ${QS_STACKNAME}
    aws cloudformation wait stack-delete-complete --stack-name ${QS_STACKNAME}
fi
if [[ -n $HAS_IMG_STACK ]]; then
    aws cloudformation delete-stack --stack-name ${IMG_STACKNAME}
    aws cloudformation wait stack-delete-complete --stack-name ${IMG_STACKNAME}
fi
if [[ -n $HAS_GENE_STACK ]]; then
    aws cloudformation delete-stack --stack-name ${GENE_STACKNAME}
    aws cloudformation wait stack-delete-complete --stack-name ${GENE_STACKNAME}
fi
if [[ -n $HAS_PIPE_STACK ]]; then
    aws cloudformation delete-stack --stack-name ${PIPE_STACKNAME}
    aws cloudformation wait stack-delete-complete --stack-name ${PIPE_STACKNAME}
    if [[ -n $LOGS_BUCKET ]]; then
        aws s3 rm --recursive s3://${LOGS_BUCKET}/
        sleep 1
        aws s3 rb s3://${LOGS_BUCKET}
    fi
fi
if [[ -n $HAS_ZONE_STACK ]]; then
    aws cloudformation delete-stack --stack-name ${ZONE_STACKNAME}
    aws cloudformation wait stack-delete-complete --stack-name ${ZONE_STACKNAME}
fi

# Delete Repos

[[ -n $PIPE_REPO ]] && aws codecommit delete-repository --repository-name ${PIPE_REPO}
[[ -n $CODE_REPO ]] && aws codecommit delete-repository --repository-name ${CODE_REPO}

# Cleanup Local Git Repo

find . \( -name ".git" -o -name ".gitignore" -o -name ".gitmodules" -o -name ".gitattributes" \) -exec rm -rf -- {} +
