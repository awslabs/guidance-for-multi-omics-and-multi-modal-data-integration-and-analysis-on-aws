#!/bin/bash -e

export AWS_DEFAULT_OUTPUT=text

project_name=$1

# start imaging crawlers
imaging_crawlers=$(
    aws cloudformation describe-stack-resources \
        --stack-name "${project_name}-Imaging" \
        --query 'StackResources[?ResourceType==`AWS::Glue::Crawler`].PhysicalResourceId')

for img_crawler_name in ${imaging_crawlers}; do
    aws glue start-crawler --name ${img_crawler_name}
done
printf "Crawlers started successfully\n"

# start glue jobs (not needed)
#workflow_name=$(aws cloudformation describe-stacks \
#                    --stack-name "${project_name}-Imaging" \
#                    --query 'Stacks[0].Outputs[?OutputKey==`TCGAWorkflow`].OutputValue')
#
#aws glue start-workflow-run --name ${workflow_name}
