#!/bin/bash -e

export AWS_DEFAULT_OUTPUT=text

project_name=${PROJECT_NAME:-GenomicsAnalysis}

resource_prefix=${project_name}

resource_prefix_lowercase=$(echo ${resource_prefix} | tr '[:upper:]' '[:lower:]')

annotation_crawler_name="${resource_prefix_lowercase}-annotation"
cohort_crawler_name="${resource_prefix_lowercase}-cohort"
sample_crawler_name="${resource_prefix_lowercase}-sample"

aws glue start-crawler --name ${annotation_crawler_name}
aws glue start-crawler --name ${cohort_crawler_name}
aws glue start-crawler --name ${sample_crawler_name}

imaging_crawlers=$(
    aws cloudformation describe-stack-resources \
        --stack-name "${project_name}-Imaging" \
        --query 'StackResources[?ResourceType==`AWS::Glue::Crawler`].PhysicalResourceId')

for img_crawler_name in ${imaging_crawlers}; do
    aws glue start-crawler --name ${img_crawler_name}
done

printf "Test:Crawlers started successfully\n"

#workflow_name=$(aws cloudformation describe-stacks \
#                    --stack-name "${project_name}-Imaging" \
#                    --query 'Stacks[0].Outputs[?OutputKey==`TCGAWorkflow`].OutputValue')
#
#aws glue start-workflow-run --name ${workflow_name}
