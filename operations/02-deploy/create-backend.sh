#!/bin/bash
set -e # Fail the entire script if any line fails
set -o pipefail # Fail a pipe if any sub-command fails.
set -u # Treat unset variables as an error
set -x # Print the command before executing it


# AWS_PROFILE is the first argument, if not provided, it will use "umans" as default
AWS_PROFILE=${1:-umans}
# AWS_REGION is the second argument, if not provided, it will use "eu-west-3" as default
AWS_REGION=${2:-eu-west-3}
BUCKET_NAME="terraform-state-umans-platform"

function create_backend_bucket_with_enabled_versioning() {
  aws --profile "${AWS_PROFILE}" --region "${AWS_REGION}" \
      s3api create-bucket --bucket "${BUCKET_NAME}" \
      --create-bucket-configuration "LocationConstraint=${AWS_REGION}"

  aws --profile "${AWS_PROFILE}" --region "${AWS_REGION}" \
      s3api put-bucket-versioning --bucket "${BUCKET_NAME}" \
      --versioning-configuration Status=Enabled
}

create_backend_bucket_with_enabled_versioning