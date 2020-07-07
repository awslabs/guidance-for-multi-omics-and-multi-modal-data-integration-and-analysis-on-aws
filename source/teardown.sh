#!/bin/bash -e

export AWS_DEFAULT_OUTPUT=text

export RESOURCE_PREFIX=${PROJECT_NAME:-GenomicsAnalysis}
export RESOURCE_PREFIX_LOWERCASE=$(echo ${RESOURCE_PREFIX} | tr '[:upper:]' '[:lower:]')

export ZONE_STACKNAME=${RESOURCE_PREFIX}-LandingZone
export PIPE_STACKNAME=${RESOURCE_PREFIX}-Pipeline
export CODE_STACKNAME=${RESOURCE_PREFIX}

export REPOSITORY_NAME=${RESOURCE_PREFIX_LOWERCASE}

# Clear Buckets

BUILD_BUCKET=$(aws cloudformation describe-stacks --stack-name ${PIPE_STACKNAME} --query 'Stacks[].Outputs[?OutputKey==`BuildBucket`].OutputValue'); echo ${BUILD_BUCKET}
RESOURCES_BUCKET=$(aws cloudformation describe-stacks --stack-name ${PIPE_STACKNAME} --query 'Stacks[].Outputs[?OutputKey==`ResourcesBucket`].OutputValue'); echo ${RESOURCES_BUCKET}
DATALAKE_BUCKET=$(aws cloudformation describe-stacks --stack-name ${PIPE_STACKNAME} --query 'Stacks[].Outputs[?OutputKey==`DataLakeBucket`].OutputValue'); echo ${DATALAKE_BUCKET}
LOGS_BUCKET=$(aws cloudformation describe-stacks --stack-name ${PIPE_STACKNAME} --query 'Stacks[].Outputs[?OutputKey==`LogsBucket`].OutputValue'); echo ${LOGS_BUCKET}

aws s3 rm --recursive s3://${BUILD_BUCKET}/
aws s3 rm --recursive s3://${RESOURCES_BUCKET}/
aws s3 rm --recursive s3://${DATALAKE_BUCKET}/
aws s3 rm --recursive s3://${LOGS_BUCKET}/

# Disable Termination Protection on Stacks

aws cloudformation update-termination-protection --no-enable-termination-protection --stack-name ${PIPE_STACKNAME} 
aws cloudformation update-termination-protection --no-enable-termination-protection --stack-name ${ZONE_STACKNAME}

# Get Repo Names from Stacks

PIPE_REPO=$(aws cloudformation describe-stacks --stack-name ${ZONE_STACKNAME} --query 'Stacks[].Outputs[?OutputKey==`RepoName`].OutputValue'); echo ${PIPE_REPO}
CODE_REPO=$(aws cloudformation describe-stacks --stack-name ${PIPE_STACKNAME} --query 'Stacks[].Outputs[?OutputKey==`RepoName`].OutputValue'); echo ${CODE_REPO}

# Delete Stacks

aws cloudformation delete-stack --stack-name ${CODE_STACKNAME}; aws cloudformation wait stack-delete-complete --stack-name ${CODE_STACKNAME}
aws cloudformation delete-stack --stack-name ${PIPE_STACKNAME}; aws cloudformation wait stack-delete-complete --stack-name ${PIPE_STACKNAME}
aws cloudformation delete-stack --stack-name ${ZONE_STACKNAME}; aws cloudformation wait stack-delete-complete --stack-name ${ZONE_STACKNAME}

# Delete Repos

aws codecommit delete-repository --repository-name ${PIPE_REPO}
aws codecommit delete-repository --repository-name ${CODE_REPO}

# Cleanup Local Git Repo

find . \( -name ".git" -o -name ".gitignore" -o -name ".gitmodules" -o -name ".gitattributes" \) -exec rm -rf -- {} +
