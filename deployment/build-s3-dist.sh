#!/bin/bash
#
# This assumes all of the OS-level configuration has been completed and git repo has already been cloned
#
# This script should be run from the repo's deployment directory
# cd deployment
# ./build-s3-dist.sh source-bucket-base-name solution-name version-code
#
# Paramenters:
#  - source-bucket-base-name: Name for the S3 bucket location where the template will source the Lambda
#    code from. The template will append '-[region_name]' to this bucket name.
#    For example: ./build-s3-dist.sh solutions my-solution v1.0.0
#    The template will then expect the source code to be located in the solutions-[region_name] bucket
#
#  - solution-name: name of the solution for consistency
#
#  - version-code: version of the package

# Check to see if input has been provided:
if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ]; then
    echo "Please provide the base source bucket name, trademark approved solution name and version where the lambda code will eventually reside."
    echo "For example: ./build-s3-dist.sh solutions trademarked-solution-name v1.0.0"
    exit 1
fi

# Get reference for all important folders
template_dir="$PWD"
template_dist_dir="$template_dir/global-s3-assets"
build_dist_dir="$template_dir/regional-s3-assets"
source_dir="$template_dir/../source"

cp $source_dir/setup_cfn.yml $template_dir/genomics-tertiary-analysis-and-data-lakes-using-aws-glue-and-amazon-athena.template

echo "------------------------------------------------------------------------------"
echo "[Init] Clean old dist"
echo "------------------------------------------------------------------------------"
echo "rm -rf $template_dist_dir"
rm -rf $template_dist_dir
echo "mkdir -p $template_dist_dir"
mkdir -p $template_dist_dir
echo "rm -rf $build_dist_dir"
rm -rf $build_dist_dir
echo "mkdir -p $build_dist_dir"
mkdir -p $build_dist_dir

echo "------------------------------------------------------------------------------"
echo "[Packing] Templates"
echo "------------------------------------------------------------------------------"
echo "cp $template_dir/*.template $template_dist_dir/"
cp $template_dir/*.template $template_dist_dir/
echo "copy yaml templates and rename"
cp $template_dir/*.yml $template_dist_dir/
cd $template_dist_dir
# Rename all *.yaml to *.template
for f in *.yml; do
    mv -- "$f" "${f%.yml}.template"
done

cd ..
echo "Updating code source bucket in template with $1"
replace="s/%%BUCKET_NAME%%/$1/g"
echo "sed -i '' -e $replace $template_dist_dir/*.template"
sed -i '' -e $replace $template_dist_dir/*.template
replace="s/%%SOLUTION_NAME%%/$2/g"
echo "sed -i '' -e $replace $template_dist_dir/*.template"
sed -i '' -e $replace $template_dist_dir/*.template
replace="s/%%VERSION%%/$3/g"
echo "sed -i '' -e $replace $template_dist_dir/*.template"
sed -i '' -e $replace $template_dist_dir/*.template

mkdir $build_dist_dir/variants
mkdir $build_dist_dir/variants/onekg-chr22-by_sample/
mkdir $build_dist_dir/variants/vcf/
mkdir $build_dist_dir/annotation
mkdir $build_dist_dir/annotation/clinvar/

wget https://aws-batch-genomics-shared.s3.amazonaws.com/human-ngs/analysis/variants/1000genomes/chr22.parquet.zip
cp chr22.parquet.zip $build_dist_dir/variants/onekg-chr22-by_sample/chr22.parquet.zip

wget https://aws-batch-genomics-shared.s3.amazonaws.com/human-ngs/analysis/variants/vcf/variants.vcf.bgz
cp variants.vcf.bgz $build_dist_dir/variants/vcf/variants.vcf.bgz
wget https://aws-batch-genomics-shared.s3.amazonaws.com/human-ngs/analysis/variants/vcf/part-00000-a73946db-afb7-49a5-8bbb-621cb57637c2-c000.snappy.parquet
cp part-00000-a73946db-afb7-49a5-8bbb-621cb57637c2-c000.snappy.parquet $build_dist_dir/variants/vcf/part-00000-a73946db-afb7-49a5-8bbb-621cb57637c2-c000.snappy.parquet
wget https://aws-batch-genomics-shared.s3.amazonaws.com/human-ngs/analysis/variants/vcf/part-00001-a73946db-afb7-49a5-8bbb-621cb57637c2-c000.snappy.parquet
cp part-00001-a73946db-afb7-49a5-8bbb-621cb57637c2-c000.snappy.parquet $build_dist_dir/variants/vcf/part-00001-a73946db-afb7-49a5-8bbb-621cb57637c2-c000.snappy.parquet

wget https://aws-batch-genomics-shared.s3.amazonaws.com/human-ngs/analysis/annotations/clinvar/variant_summary.txt.gz
cp variant_summary.txt.gz $build_dist_dir/annotation/clinvar/variant_summary.txt.gz
wget https://aws-batch-genomics-shared.s3.amazonaws.com/human-ngs/analysis/annotation/clinvar/part-00000-38061af6-1c74-4605-a37d-ba7b260ad06a-c000.snappy.parquet
cp part-00000-38061af6-1c74-4605-a37d-ba7b260ad06a-c000.snappy.parquet $build_dist_dir/annotation/clinvar/part-00000-38061af6-1c74-4605-a37d-ba7b260ad06a-c000.snappy.parquet

part-00000-38061af6-1c74-4605-a37d-ba7b260ad06a-c000.snappy.parquet

echo "------------------------------------------------------------------------------"
echo "[Rebuild] Solution"
echo "------------------------------------------------------------------------------"

cd $source_dir

bundle_dir="$source_dir/../bundle"
mkdir -p $bundle_dir

# create the lambda function deployment pacakage for the solution setup
cd $source_dir/GenomicsAnalysisCode/setup
pip install -t . crhelper
zip -r $bundle_dir/SolutionSetup.zip .

# package the solution
cd $source_dir
zip -r $bundle_dir/Solution.zip .

cd $bundle_dir
cp Solution.zip $template_dist_dir/
cp SolutionSetup.zip $template_dist_dir/
cp Solution.zip $build_dist_dir/
cp SolutionSetup.zip $build_dist_dir/
