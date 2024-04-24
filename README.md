# Guidance for Multi-Omics and Multi-Modal Data Integration and Analysis on AWS
This guidance creates a scalable environment in AWS to prepare genomic, clinical, mutation, expression and imaging data for large-scale analysis and perform interactive queries against a data lake. This solution demonstrates how to 1) build, package, and deploy libraries used for genomics data conversion, 2) provision serverless data ingestion pipelines for multi-modal data preparation and cataloging, 3) visualize and explore clinical data through an interactive interface, and 4) run interactive analytic queries against a multi-modal data lake. This solution also demonstrates how to use AWS Omics to create and work with a Sequence Store, Reference Store and Variant Store in a multi-modal context.

# Setup
You can setup the solution in your account by clicking the "Deploy sample code on Console" button on the [solution home page](https://aws.amazon.com/ko/solutions/guidance/multi-omics-and-multi-modal-data-integration-and-analysis/).

# Customization

## Running unit tests for customization
* Clone the repository, then make the desired code changes
* Next, run unit tests to make sure added customization passes the tests
```
cd ./deployment
chmod +x ./run-unit-tests.sh
./run-unit-tests.sh
```

## Prerequisites

1. Create a distribution bucket, i.e., my-bucket-name
2. Create a region based distribution, i.e., bucket my-bucket-name-us-west-2
3. Create a Cloud9 environment.
4. Clone this repo into that environment.

## Building and deploying distributable for customization
Configure the bucket name and region of your target Amazon S3 distribution bucket and run the following statements. 

```
_Note:_ You would have to create an S3 bucket with the prefix 'my-bucket-name-<aws_region>'; aws_region is where you are testing the customized solution.
```

```
#bucket where customized code will reside (without -<region> at the end. The -<region will be added>)
export DIST_OUTPUT_BUCKET=my-bucket-name 

#default region where resources will get created
#Use "us-east-1" to get publicly available data from AWS solution bucket
export REGION=my-region

#default name of the solution (use this name to get publicly available test datasets from AWS S3 bucket)
export SOLUTION_NAME=genomics-tertiary-analysis-and-data-lakes-using-aws-glue-and-amazon-athena

#version number for the customized code (use this version to get publicly available test datasets from AWS S3 bucket)
export VERSION=latest
```

#### Change to deployment directory.
```
cd deployment
```

#### Build the distributable.
```
chmod +x ./build-s3-dist.sh
./build-s3-dist.sh $DIST_OUTPUT_BUCKET $SOLUTION_NAME $VERSION
```

#### Deploy the distributable to an Amazon S3 bucket in your account. _Note:_ you must have the AWS Command Line Interface installed
```
aws s3 cp ./$SOLUTION_NAME.template s3://$DIST_OUTPUT_BUCKET-$REGION/$SOLUTION_NAME/$VERSION/
```

#### Deploy the global assets.

```
aws s3 cp ./global-s3-assets/ s3://$DIST_OUTPUT_BUCKET-$REGION/$SOLUTION_NAME/$VERSION --recursive
```

#### Deploy the regional assets.
 
```
aws s3 cp ./regional-s3-assets/ s3://$DIST_OUTPUT_BUCKET-$REGION/$SOLUTION_NAME/$VERSION --recursive
```

#### Copy the static assets.
 
```
./copy-static-files.sh [Optional]AWSProfile
```

#### Go to the DIST_OUTPUT_BUCKET and copy the OBJECT URL for latest/guidance-for-multi-omics-and-multi-modal-data-integration-and-analysis-on-aws.template.

#### Go to the AWS CloudFormation Console and create a new stack using the template URL copied.

# File Structure
The overall file structure for the application.

```
.
├── ATTRIBUTION.txt
├── CHANGELOG.md
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
├── LICENSE.txt
├── NOTICE.txt
├── README.md
├── buildspec.yml
├── deploy.sh
├── deployment
│   ├── build-s3-dist.sh
│── source
│   ├── GenomicsAnalysisCode
│   │   ├── TCIA_etl.yaml
│   │   ├── code_cfn.yml
│   │   ├── copyresources_buildspec.yml
│   │   ├── omics_cfn.yml
│   │   ├── omicsresources_buildspec.yml
│   │   ├── quicksight_cfn.yml
│   │   ├── resources
│   │   │   ├── notebooks
│   │   │   │   ├── cohort-building.ipynb
│   │   │   │   ├── runbook.ipynb
│   │   │   │   └── summarize-tcga-datasets.ipynb
│   │   │   ├── omics
│   │   │   │   ├── create_annotation_store_lambda.py
│   │   │   │   ├── create_reference_store_lambda.py
│   │   │   │   ├── create_variant_store_lambda.py
│   │   │   │   ├── import_annotation_lambda.py
│   │   │   │   ├── import_reference_lambda.py
│   │   │   │   └── import_variant_lambda.py
│   │   │   └── scripts
│   │   │       ├── create_tcga_summary.py
│   │   │       ├── image_api_glue.py
│   │   │       ├── run_tests.py
│   │   │       ├── tcga_etl_common_job.py
│   │   │       └── transfer_tcia_images_glue.py
│   │   ├── run_crawlers.sh
│   │   └── setup
│   │       ├── lambda.py
│   │       └── requirements.txt
│   ├── GenomicsAnalysisPipe
│   │   └── pipe_cfn.yml
│   ├── GenomicsAnalysisZone
│   │   └── zone_cfn.yml
│   ├── TCIA_etl.yaml
│   ├── setup.sh
│   ├── setup_cfn.yml
│   └── teardown.sh
├── template_cfn.yml
```

***

This solution collects anonymous operational metrics to help AWS improve the
quality of features of the solution. For more information, including how to disable
this capability, please see the [implementation guide](https://docs.aws.amazon.com/solutions/latest/guidance-for-multi-omics-and-multi-modal-data-integration-and-analysis-on-aws/appendix-i.html).

---

Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.

Licensed under the Apache License Version 2.0 (the "License"). You may not use this file except in compliance with the License. A copy of the License is located at

    http://www.apache.org/licenses/

or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, express or implied. See the License for the specific language governing permissions and limitations under the License.
