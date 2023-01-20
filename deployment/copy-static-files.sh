#!/bin/bash -e

aws s3 cp s3://solutions-$REGION/$SOLUTION_NAME/v3.0.0/annotation/clinvar/clinvar.vcf.gz s3://$DIST_OUTPUT_BUCKET-$REGION/$SOLUTION_NAME/$VERSION/annotation/clinvar/clinvar.vcf.gz --copy-props none
aws s3 cp s3://solutions-$REGION/$SOLUTION_NAME/v3.0.0/variants/vcf/variants.vcf.gz s3://$DIST_OUTPUT_BUCKET-$REGION/$SOLUTION_NAME/$VERSION/variants/vcf/variants.vcf.gz --copy-props none
aws s3 cp s3://solutions-$REGION/$SOLUTION_NAME/v3.0.0/references/hg38/Homo_sapiens_assembly38.fasta s3://$DIST_OUTPUT_BUCKET-$REGION/$SOLUTION_NAME/$VERSION/references/hg38/Homo_sapiens_assembly38.fasta --copy-props none
aws s3 cp s3://solutions-$REGION/$SOLUTION_NAME/v3.0.0/variants/1kg/ALL.chr22.shapeit2_integrated_snvindels_v2a_27022019.GRCh38.phased.filtNA.vcf.gz s3://$DIST_OUTPUT_BUCKET-$REGION/$SOLUTION_NAME/$VERSION/variants/1kg/ALL.chr22.shapeit2_integrated_snvindels_v2a_27022019.GRCh38.phased.filtNA.vcf.gz --copy-props none

aws s3 cp s3://solutions-$REGION/$SOLUTION_NAME/v3.0.0/tcga/tcga-clinical.zip s3://$DIST_OUTPUT_BUCKET-$REGION/$SOLUTION_NAME/$VERSION/tcga/tcga-clinical.zip --copy-props none
aws s3 cp s3://solutions-$REGION/$SOLUTION_NAME/v3.0.0/tcga/tcga-cnv.zip s3://$DIST_OUTPUT_BUCKET-$REGION/$SOLUTION_NAME/$VERSION/tcga/tcga-cnv.zip --copy-props none
aws s3 cp s3://solutions-$REGION/$SOLUTION_NAME/v3.0.0/tcga/tcga-expression.zip s3://$DIST_OUTPUT_BUCKET-$REGION/$SOLUTION_NAME/$VERSION/tcga/tcga-expression.zip --copy-props none 
aws s3 cp s3://solutions-$REGION/$SOLUTION_NAME/v3.0.0/tcga/tcga-mutation.zip s3://$DIST_OUTPUT_BUCKET-$REGION/$SOLUTION_NAME/$VERSION/tcga/tcga-mutation.zip --copy-props none 
aws s3 cp s3://solutions-$REGION/$SOLUTION_NAME/v3.0.0/tcga/tcia-metadata.zip s3://$DIST_OUTPUT_BUCKET-$REGION/$SOLUTION_NAME/$VERSION/tcga/tcia-metadata.zip --copy-props none 
aws s3 cp s3://solutions-$REGION/$SOLUTION_NAME/v3.0.0/tcga/tcga-summary.zip s3://$DIST_OUTPUT_BUCKET-$REGION/$SOLUTION_NAME/$VERSION/tcga/tcga-summary.zip --copy-props none 

