#!/bin/bash -e

aws s3 cp s3://solutions-$REGION/$SOLUTION_NAME/v2.0.0/variants/onekg-chr22-by_sample/chr22.parquet.zip s3://$DIST_OUTPUT_BUCKET-$REGION/$SOLUTION_NAME/$VERSION/variants/onekg-chr22-by_sample/chr22.parquet.zip
aws s3 cp s3://solutions-$REGION/$SOLUTION_NAME/v2.0.0/variants/vcf/variants.vcf.bgz s3://$DIST_OUTPUT_BUCKET-$REGION/$SOLUTION_NAME/$VERSION/variants/vcf/variants.vcf.bgz
aws s3 cp s3://solutions-$REGION/$SOLUTION_NAME/v2.0.0/variants/vcf/part-00000-a73946db-afb7-49a5-8bbb-621cb57637c2-c000.snappy.parquet s3://$DIST_OUTPUT_BUCKET-$REGION/$SOLUTION_NAME/$VERSION/variants/vcf/part-00000-a73946db-afb7-49a5-8bbb-621cb57637c2-c000.snappy.parquet
aws s3 cp s3://solutions-$REGION/$SOLUTION_NAME/v2.0.0/variants/vcf/part-00001-a73946db-afb7-49a5-8bbb-621cb57637c2-c000.snappy.parquet s3://$DIST_OUTPUT_BUCKET-$REGION/$SOLUTION_NAME/$VERSION/variants/vcf/part-00001-a73946db-afb7-49a5-8bbb-621cb57637c2-c000.snappy.parquet

aws s3 cp s3://solutions-$REGION/$SOLUTION_NAME/v2.0.0/annotation/clinvar/variant_summary.txt.gz s3://$DIST_OUTPUT_BUCKET-$REGION/$SOLUTION_NAME/$VERSION/annotation/clinvar/variant_summary.txt.gz
aws s3 cp s3://solutions-$REGION/$SOLUTION_NAME/v2.0.0/annotation/clinvar/part-00000-38061af6-1c74-4605-a37d-ba7b260ad06a-c000.snappy.parquet s3://$DIST_OUTPUT_BUCKET-$REGION/$SOLUTION_NAME/$VERSION/annotation/clinvar/part-00000-38061af6-1c74-4605-a37d-ba7b260ad06a-c000.snappy.parquet

aws s3 cp s3://solutions-$REGION/$SOLUTION_NAME/v2.0.0/tcga/tcga-clinical.zip s3://$DIST_OUTPUT_BUCKET-$REGION/$SOLUTION_NAME/$VERSION/tcga/tcga-clinical.zip
aws s3 cp s3://solutions-$REGION/$SOLUTION_NAME/v2.0.0/tcga/tcga-cnv.zip s3://$DIST_OUTPUT_BUCKET-$REGION/$SOLUTION_NAME/$VERSION/tcga/tcga-cnv.zip
aws s3 cp s3://solutions-$REGION/$SOLUTION_NAME/v2.0.0/tcga/tcga-expression.zip s3://$DIST_OUTPUT_BUCKET-$REGION/$SOLUTION_NAME/$VERSION/tcga/tcga-expression.zip
aws s3 cp s3://solutions-$REGION/$SOLUTION_NAME/v2.0.0/tcga/tcga-mutation.zip s3://$DIST_OUTPUT_BUCKET-$REGION/$SOLUTION_NAME/$VERSION/tcga/tcga-mutation.zip
aws s3 cp s3://solutions-$REGION/$SOLUTION_NAME/v2.0.0/tcga/tcia-metadata.zip s3://$DIST_OUTPUT_BUCKET-$REGION/$SOLUTION_NAME/$VERSION/tcga/tcia-metadata.zip
aws s3 cp s3://solutions-$REGION/$SOLUTION_NAME/v2.0.0/tcga/tcga-summary.zip s3://$DIST_OUTPUT_BUCKET-$REGION/$SOLUTION_NAME/$VERSION/tcga/tcga-summary.zip

