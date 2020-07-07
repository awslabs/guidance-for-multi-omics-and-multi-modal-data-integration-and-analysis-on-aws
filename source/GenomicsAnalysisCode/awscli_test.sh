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

printf "Test:Crawlers started successfully\n"

exit $exit_code
