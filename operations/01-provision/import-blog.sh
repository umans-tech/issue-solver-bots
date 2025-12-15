#!/usr/bin/env bash
set -euo pipefail

# Import existing blog infrastructure into the 01-provision state
# so resources are adopted without recreation. Intended to be used
# in CI after the blog module was moved from 02-deploy to 01-provision.
#
# Requirements:
#   - terraform, aws cli, jq installed
#   - AWS credentials with rights to read CloudFront/ACM/Route53/S3
#   - WORKSPACE env var (optional) matches terraform workspace.
#     Defaults to the same logic as the justfile (production/main vs pr-<branch>).
#
# Usage:
#   WORKSPACE=production ./import-blog.sh
#   WORKSPACE=pr-123 ./import-blog.sh
#

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${REPO_ROOT}/operations/01-provision"

command -v aws >/dev/null || { echo "aws CLI is required" >&2; exit 1; }
command -v terraform >/dev/null || { echo "terraform is required" >&2; exit 1; }

DRY_RUN="${DRY_RUN:-false}"

# Derive workspace like the justfile to stay consistent across CI/local
WORKSPACE="${WORKSPACE:-$(
  if [[ -n "${GH_PR_NUMBER:-}" ]]; then
    echo "pr-${GH_PR_NUMBER}"
  else
    branch="$(git rev-parse --abbrev-ref HEAD | sed 's@[\\/]@-@g')"
    if [[ "${branch}" == "main" ]]; then
      echo "production"
    else
      echo "pr-${branch}"
    fi
  fi
)}"

if [[ "${WORKSPACE}" == "production" ]]; then
  ENV_SUFFIX=""
  DOMAIN_PREFIX=""
else
  ENV_SUFFIX="-${WORKSPACE}"
  DOMAIN_PREFIX="${WORKSPACE}."
fi

BLOG_DOMAIN="blog.${DOMAIN_PREFIX}umans.ai"
ALIAS_NAME="${BLOG_DOMAIN}."
BUCKET_NAME="blog${ENV_SUFFIX}-umans-site"
OAC_NAME="blog${ENV_SUFFIX}-oac"
CF_FUNCTION_NAME="blog-${WORKSPACE}-index-rewrite"

AWS_REGION_US_EAST_1="${AWS_REGION_US_EAST_1:-us-east-1}"

echo ">>> Workspace: ${WORKSPACE}"
echo ">>> Blog domain: ${BLOG_DOMAIN}"
echo ">>> Blog bucket: ${BUCKET_NAME}"
echo ">>> OAC name: ${OAC_NAME}"
echo ">>> DRY_RUN: ${DRY_RUN}"

run_tf() {
  if [[ "${DRY_RUN}" == "true" ]]; then
    echo "[DRY-RUN] terraform $*"
  else
    terraform "$@"
  fi
}

# Ensure workspace & init (skipped during dry-run)
if [[ "${DRY_RUN}" != "true" ]]; then
  run_tf workspace select "${WORKSPACE}" >/dev/null 2>&1 || run_tf workspace new "${WORKSPACE}"
fi

import_if_missing() {
  local address="$1"
  local id="$2"
  if [[ "${DRY_RUN}" == "true" ]]; then
    echo "[DRY-RUN] would import ${address} -> ${id}"
    return
  fi
  if terraform state show "${address}" >/dev/null 2>&1; then
    echo "✅ ${address} already in state"
  else
    echo "⏬ Importing ${address} -> ${id}"
    terraform import "${address}" "${id}"
  fi
}

# Route53 zone for umans.ai
ZONE_ID="${ROUTE53_ZONE_ID:-$(aws route53 list-hosted-zones-by-name \
  --dns-name "umans.ai" \
  --query 'HostedZones[0].Id' --output text)}"
ZONE_ID="${ZONE_ID#/hostedzone/}"
echo ">>> Route53 zone id: ${ZONE_ID}"

# CloudFront distribution ID by alias
CF_DIST_ID="$(aws cloudfront list-distributions \
  --query "DistributionList.Items[?Aliases.Items && contains(Aliases.Items, '${BLOG_DOMAIN}')].Id | [0]" \
  --output text)"

# Origin Access Control id by name
OAC_ID="$(aws cloudfront list-origin-access-controls \
  --query "OriginAccessControlList.Items[?Name=='${OAC_NAME}'].Id | [0]" \
  --output text)"

# Try to pick the certificate actually attached to the CloudFront distribution first
CF_CERT_ARN="$(aws cloudfront get-distribution --id "${CF_DIST_ID}" \
  --query 'Distribution.DistributionConfig.ViewerCertificate.ACMCertificateArn' \
  --output text 2>/dev/null || true)"

# Fallback: find an ACM cert that matches the domain (exact first, then wildcard)
find_cert() {
  aws acm list-certificates \
    --region "${AWS_REGION_US_EAST_1}" \
    --certificate-statuses ISSUED PENDING_VALIDATION \
    --query 'CertificateSummaryList[].{Arn:CertificateArn,Domain:DomainName}' \
    --output text | while read -r arn domain; do
      if [[ "${domain}" == "${BLOG_DOMAIN}" ]]; then
        echo "${arn}"
        return
      fi
    done
}

if [[ -n "${CF_CERT_ARN}" && "${CF_CERT_ARN}" != "None" ]]; then
  CERT_ARN="${CF_CERT_ARN}"
else
  CERT_ARN="$(find_cert || true)"
fi

if [[ -z "${CF_DIST_ID}" || "${CF_DIST_ID}" == "None" ]]; then
  echo "CloudFront distribution for ${BLOG_DOMAIN} not found" >&2
  exit 1
fi
if [[ -z "${OAC_ID}" || "${OAC_ID}" == "None" ]]; then
  echo "CloudFront OAC ${OAC_NAME} not found" >&2
  exit 1
fi
if [[ -z "${CERT_ARN}" || "${CERT_ARN}" == "None" ]]; then
  echo "ACM certificate for ${BLOG_DOMAIN} not found in ${AWS_REGION_US_EAST_1}" >&2
  exit 1
fi

echo ">>> CloudFront distribution id: ${CF_DIST_ID}"
echo ">>> OAC id: ${OAC_ID}"
echo ">>> Certificate arn: ${CERT_ARN}"

# --- Import order matters to avoid unknown for_each keys ---
# 1) Certificate first so domain_validation_options are known
import_if_missing aws_acm_certificate.blog "${CERT_ARN}"
# 2) Validation records depend on certificate DVOs
DVO_OUTPUT="$(aws acm describe-certificate \
  --region "${AWS_REGION_US_EAST_1}" \
  --certificate-arn "${CERT_ARN}" \
  --query 'Certificate.DomainValidationOptions[*].[DomainName,ResourceRecord.Name,ResourceRecord.Type]' \
  --output text)"

if [[ -n "${DVO_OUTPUT}" && "${DVO_OUTPUT}" != "None" ]]; then
  while IFS=$' \t' read -r domain_name rr_name rr_type; do
    if [[ -n "${domain_name}" && -n "${rr_name}" && -n "${rr_type}" && "${rr_name}" != "None" ]]; then
      import_if_missing "aws_route53_record.blog_cert_validation[\"${domain_name}\"]" "${ZONE_ID}_${rr_name}_${rr_type}"
    fi
  done <<< "${DVO_OUTPUT}"
fi

# 3) CloudFront + S3
import_if_missing aws_cloudfront_origin_access_control.blog "${OAC_ID}"
import_if_missing aws_cloudfront_function.blog_index_rewrite "${CF_FUNCTION_NAME}"
import_if_missing aws_cloudfront_distribution.blog "${CF_DIST_ID}"

import_if_missing aws_s3_bucket.blog_site "${BUCKET_NAME}"
import_if_missing aws_s3_bucket_public_access_block.blog_site "${BUCKET_NAME}"
import_if_missing aws_s3_bucket_versioning.blog_site "${BUCKET_NAME}"
import_if_missing aws_s3_bucket_policy.blog_site "${BUCKET_NAME}"
# 5) Alias records
import_if_missing aws_route53_record.blog_alias "${ZONE_ID}_${ALIAS_NAME}_A"
import_if_missing aws_route53_record.blog_alias_ipv6 "${ZONE_ID}_${ALIAS_NAME}_AAAA"

echo "✅ Blog resources imported into 01-provision state for workspace '${WORKSPACE}'."

# Optionally prune old state from 02-deploy to prevent Terraform from planning destroys.
if [[ "${CLEAN_DEPLOY_STATE:-false}" == "true" ]]; then
  if [[ "${DRY_RUN}" == "true" ]]; then
    echo "[DRY-RUN] Would remove blog resources from 02-deploy state (CLEAN_DEPLOY_STATE=true)"
    exit 0
  fi

  echo ">>> CLEAN_DEPLOY_STATE enabled; removing blog resources from 02-deploy state"
  pushd "${REPO_ROOT}/operations/02-deploy" >/dev/null
  terraform init -reconfigure >/dev/null
  terraform workspace select "${WORKSPACE}" >/dev/null 2>&1 || terraform workspace new "${WORKSPACE}"

  state_rm_if_present() {
    local addr="$1"
    if terraform state show "${addr}" >/dev/null 2>&1; then
      terraform state rm "${addr}"
      echo "🧹 Removed ${addr} from 02-deploy state"
    else
      echo "ℹ️  ${addr} not present in 02-deploy state"
    fi
  }

  state_rm_if_present aws_s3_bucket.blog_site
  state_rm_if_present aws_s3_bucket_public_access_block.blog_site
  state_rm_if_present aws_s3_bucket_versioning.blog_site
  state_rm_if_present aws_s3_bucket_policy.blog_site
  state_rm_if_present aws_cloudfront_origin_access_control.blog
  state_rm_if_present aws_cloudfront_function.blog_index_rewrite
  state_rm_if_present aws_cloudfront_distribution.blog
  state_rm_if_present aws_acm_certificate.blog
  state_rm_if_present 'aws_route53_record.blog_cert_validation["'"${BLOG_DOMAIN}"'"]'
  state_rm_if_present aws_route53_record.blog_alias
  state_rm_if_present aws_route53_record.blog_alias_ipv6

  popd >/dev/null
  echo "✅ Old blog resources removed from 02-deploy state for workspace '${WORKSPACE}'."
fi
