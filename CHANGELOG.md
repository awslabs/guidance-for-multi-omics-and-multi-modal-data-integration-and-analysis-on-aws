# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2020-07-07
### Added
- initial release

## [1.0.1] - 2020-08-20
### Added
- Removed "Admin" as a key administrator from data catalog encryption key so an "Admin" role is not required to exist in the account for the solution to install and work.

## [2.0.0] - 2022-06-20
### Added
- Added guidance for multi-omics multi-modal analysis using The Cancer Genome Atlas (TCGA) and The Cancer Genome Imaging Atlas (TCIA)

## [3.0.0] - 2023-01-10
### Added
- Added guidance on working with a Reference Store, Variant Store & Annotation Store in Amazon Omics in a multi-modal context.
- Replaced ETL pipelines for Genomics data (1k, clinvar and example VCF) with Amazon Omics 

## [3.0.0] - 2023-04-28
### Added
- Update bucket creation steps to comply with https://aws.amazon.com/about-aws/whats-new/2023/04/amazon-s3-two-security-best-practices-buckets-default/