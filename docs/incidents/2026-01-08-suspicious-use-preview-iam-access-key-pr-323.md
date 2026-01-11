# Postmortem — 2026-01-08 — Suspicious use of AWS access key (preview IAM user `knowledge-blob-user-pr-323`)

## Summary

On **2026-01-08**, AWS flagged suspicious activity involving the access key **`AKIAQQABDFFF2QS5HDEX`** attached to the
preview IAM user **`knowledge-blob-user-pr-323`** (PR-323 preview environment).  
We investigated CloudTrail across all regions for this AccessKeyId over **2025-12-20 → 2026-01-11**. The activity
observed was primarily **permission probing** (STS identity check + denied attempts). No successful mutating actions
were found.

The preview IAM user was **already deleted** as part of the automatic preview teardown after merge, which invalidated
the key.

## Status

**Resolved** (AWS support case replied to and closed)

## Severity

**Low** (key used, but no successful mutating actions observed)

## Impact

- No EC2 key pair was imported (attempt failed + key pair not present).
- No EC2 instance enumeration succeeded (DescribeInstances failed).
- SES account probes were denied in many regions.
- One successful API call was observed: `sts:GetCallerIdentity` (identity check only).
- No evidence of resource creation/modification tied to this key in the investigated window.

## What happened

AWS reported an anomalous `ImportKeyPair` attempt for:

- **Access Key:** `AKIAQQABDFFF2QS5HDEX`
- **IAM User:** `knowledge-blob-user-pr-323`
- **Event:** `ec2:ImportKeyPair`
- **Time:** `2026-01-08T14:55:39Z`
- **IP:** `144.172.93.67` (US)

CloudTrail evidence confirms the attempts occurred, but were denied by IAM policy.

## Timeline (UTC)

- **2026-01-08T14:49:17Z** — `sts:GetCallerIdentity` (SUCCESS) — `us-east-1` — source IP `144.172.93.67`
- **2026-01-08T14:49:17Z → 14:49:39Z** — multiple `ses:GetAccount` calls across regions (DENIED) — source IP
  `144.172.93.67`
- **2026-01-08T14:55:39Z** — `ec2:ImportKeyPair` (DENIED) — `ap-south-1` — source IP `144.172.93.67`
- **2026-01-08T14:55:40Z** — `ec2:DescribeInstances` (DENIED) — `ap-south-1` — source IP `144.172.93.67`
- **2026-01-09T10:23:57Z** — `sts:GetCallerIdentity` (SUCCESS) — `us-east-1` — source IP `36.70.237.18`
- **2026-01-09T10:23:59Z** — `cloudformation:CreateStack` (DENIED) — `us-east-1` — source IP `36.70.237.18`
- **2026-01-09T10:31:33Z** — `servicequotas:GetServiceQuota` (DENIED) — `us-east-1` — source IP `36.70.237.18`
- **2026-01-11** — Investigation completed, AWS case marked resolved.

## Detection

- AWS automated monitoring raised a Support Case (email alert).
- Internal investigation relied on CloudTrail Event History queries across regions.

## Root cause (most likely)

**Access key exposure** for an ephemeral preview IAM user.

We did not identify the exact leakage path during this investigation, but plausible sources include:

- CI/CD secrets injection (GitHub Actions) into preview workloads
- Logging/telemetry capturing env vars
- Credentials present on ephemeral compute outside our VPC (US-hosted runner / micro-VM) and later exfiltrated

## Contributing factors

- Use of **long-lived IAM access keys** (even for ephemeral environments).
- Preview workloads executing outside our VPC / outside our controlled network perimeter.
- Lack of guardrails like region restrictions / “deny-by-default” for non-required services in preview identities.

## Response / mitigation

- Verified the preview IAM user **no longer exists** (automatic preview teardown), and thus the access key is **no
  longer usable**.
- Confirmed all observed EC2/SES actions tied to the key were **denied** (no successful mutations).
- Responded to AWS support case with evidence and closed the case.

## Follow-up actions (recommended)

1) **Stop using long-lived access keys for CI/preview**
    - Move CI to **OIDC → AssumeRole** (short-lived credentials).
    - Ensure preview workloads receive short-lived credentials only.

2) **Enforce least privilege + explicit deny guardrails**
    - Add explicit denies for services/regions not required by preview environments.
    - Consider SCPs (if using AWS Organizations) or permission boundaries for preview identities.

3) **Improve observability for data-plane actions**
    - Ensure CloudTrail trails include S3 **data events** for sensitive buckets if impact analysis requires proof of no
      reads.

4) **Automated secret hygiene**
    - Secret scanning + rotation runbook for any alert.
    - Reduce logging of environment variables and sanitize application logs.

---

## Appendix — Commands and evidence

### A) Confirm the preview IAM user is deleted

```bash
aws iam get-user --user-name knowledge-blob-user-pr-323
# => NoSuchEntity
````

### B) Locate the `ImportKeyPair` event across regions

```bash
START="2026-01-08T14:45:00Z"
END="2026-01-08T15:10:00Z"

for r in $(aws ec2 describe-regions --query 'Regions[].RegionName' --output text); do
  echo "== $r =="
  aws cloudtrail lookup-events \
    --region "$r" \
    --start-time "$START" \
    --end-time "$END" \
    --lookup-attributes AttributeKey=EventName,AttributeValue=ImportKeyPair \
    --max-results 50 \
    --query 'Events[].{EventTime:EventTime,Username:Username,EventId:EventId,CloudTrailEvent:CloudTrailEvent}' \
    --output json
done
```

**Result (key points):**

* Region: `ap-south-1`
* Source IP: `144.172.93.67`
* `errorCode: Client.UnauthorizedOperation`
* `requestParameters.keyName: buatbeldimobilbaim`
* userAgent: `Boto3/...`

### C) Extract structured fields (jq)

```bash
REGION="ap-south-1"
START="2026-01-08T14:45:00Z"
END="2026-01-08T15:10:00Z"

aws cloudtrail lookup-events \
  --region "$REGION" \
  --start-time "$START" \
  --end-time "$END" \
  --lookup-attributes AttributeKey=EventName,AttributeValue=ImportKeyPair \
  --max-results 50 \
  --output json \
| jq -r '
  .Events[]
  | (.CloudTrailEvent | fromjson)
  | {
      eventTime, awsRegion, eventName, eventSource,
      sourceIPAddress, userAgent,
      errorCode, errorMessage,
      userIdentity: (.userIdentity | {type, arn, userName, accessKeyId}),
      requestParameters
    }'
```

### D) Verify the key pair was not created

```bash
REGION="ap-south-1"
KEYNAME="buatbeldimobilbaim"

aws ec2 describe-key-pairs --region "$REGION" --key-names "$KEYNAME"
# => InvalidKeyPair.NotFound
```

### E) All events for this AccessKeyId across all regions (evidence set)

```bash
KEY="AKIAQQABDFFF2QS5HDEX"
START="2025-12-20T00:00:00Z"
END="2026-01-11T00:00:00Z"

for r in $(aws ec2 describe-regions --query 'Regions[].RegionName' --output text); do
  out=$(aws cloudtrail lookup-events \
    --region "$r" \
    --start-time "$START" \
    --end-time "$END" \
    --lookup-attributes AttributeKey=AccessKeyId,AttributeValue="$KEY" \
    --max-results 50 \
    --output json 2>/dev/null)

  echo "$out" | jq -e '.Events | length > 0' >/dev/null || continue

  echo "== $r =="
  echo "$out" | jq -r '
    .Events[]
    | (.CloudTrailEvent | fromjson)
    | {eventTime,eventName,eventSource,awsRegion,sourceIPAddress,errorCode}'
done
```

**Observed successful calls:**

* `sts:GetCallerIdentity` (us-east-1) — `2026-01-08T14:49:17Z` from `144.172.93.67`
* `sts:GetCallerIdentity` (us-east-1) — `2026-01-09T10:23:57Z` from `36.70.237.18`

**Observed denied calls (examples):**

* `ec2:ImportKeyPair` — `Client.UnauthorizedOperation`
* `ec2:DescribeInstances` — `Client.UnauthorizedOperation`
* `ses:GetAccount` — `AccessDenied`
* `cloudformation:CreateStack` — `AccessDenied`
* `servicequotas:GetServiceQuota` — `AccessDenied`

### F) Decode the attempted SSH public key material

```bash
echo "<base64_publicKeyMaterial>" | base64 -d
# => ssh-rsa ... root@localhost
```

### G) IAM credential report (spot-check remaining active keys/users)

```bash
aws iam generate-credential-report
aws iam get-credential-report --query 'Content' --output text | base64 -d > credential_report.csv
# Used internally to audit access key usage and rotation status.
```
