# Incident: Suspected AWS access key exposure (knowledge blob user)

## TL;DR

An AWS access key for the IAM user `knowledge-blob-user` was flagged by AWS as potentially exposed. We confirmed anomalous API calls from unknown IPs. We rotated credentials immediately, updated the App Runner service to use the new key, disabled then deleted the compromised key, and verified production functionality end-to-end (including new doc generation by the worker Lambda writing to the S3 blob). CloudTrail evidence shows reconnaissance-style calls to SES/SNS that were denied. We did not observe successful privileged actions in CloudTrail management events, but we cannot conclusively rule out S3 object access because S3 data events were not confirmed to be enabled. Next steps focus on tightening monitoring and eliminating long-lived IAM user keys by moving S3 access to IAM roles.

---

## Summary

AWS detected anomalous activity involving an AWS access key belonging to IAM user `knowledge-blob-user`. This user has permissions to read/write/delete objects in the knowledge blob S3 bucket. The observed activity looks like automated probing of additional services (SES and SNS), which failed due to missing permissions. We rotated the key and updated production to stop using the compromised credential.

## Severity

Medium (confirmed credential exposure; limited evidence of successful abuse; S3 data access cannot be fully confirmed from current logs).

---

## Timeline (UTC unless stated otherwise)

* **2025-12-26 02:01:09 UTC**: AWS reported an event `GetCallerIdentity` using the exposed access key from IP `95.173.222.10` (FR).
* **2025-12-24 to 2025-12-26**: CloudTrail Event History contains multiple calls using the same key from IP `193.32.126.230` and `95.173.222.10`.
* **2025-12-26 (morning, local time)**: Key rotation performed:

    * Created a new access key for `knowledge-blob-user`
    * Updated App Runner (`conversational-ui`) environment variables `BLOB_ACCESS_KEY_ID` and `BLOB_READ_WRITE_TOKEN` in the AWS Console
* **2025-12-26 ~12:30 (local time)**: Compromised key revocation completed:

    * Marked old key inactive
    * Deleted old key
* **Post-rotation (same day)**: Production validated end-to-end:

    * Streaming screenshot analysis works
    * Access to previously generated docs works
    * **Doc generation executed successfully and newly generated docs were uploaded to the blob, confirming worker Lambda S3 access after rotation**

---

## Detection and evidence

### AWS notification

AWS Support reported potential third-party access to an access key and recommended immediate deletion and investigation.

### CloudTrail findings (management events)

We queried CloudTrail Event History for the compromised access key and observed the following notable events:

* **SESv2 probing**

    * `ses:GetSendQuota`
    * `ses:GetAccount`
    * All returned `AccessDenied` (the IAM user is not authorized for SES actions)

* **SNS probing**

    * `sns:GetSMSAttributes`
    * Returned `AccessDenied` (the IAM user is not authorized for SNS actions)

Additional details:

* User agent strings indicate common SDKs (Go SDK and .NET SDK on Windows), consistent with automated tooling.
* Source IPs were not recognized as part of our infrastructure.

### What we did not see in CloudTrail management events

* No successful IAM mutations (no `CreateUser`, `CreateAccessKey`, `AttachUserPolicy`, etc.)
* No evidence of privilege escalation via this IAM user
* No successful SES/SNS usage

### Important limitation

The IAM user has S3 object permissions for the knowledge bucket. S3 object reads/writes are typically captured as **S3 data events**, which may not be available in CloudTrail Event History unless explicitly enabled. As a result, CloudTrail management events alone cannot prove whether any S3 objects were read, modified, or deleted.

---

## Impact assessment

### Confirmed impact

* The access key was used by an unknown party to call AWS APIs.
* Attempts were made to query SES and SNS configuration/quota details.

### Likely intent

Reconnaissance: validating what this credential can access, and checking whether SES/SNS could be abused for email or SMS sending.

### Observed outcome

* SES/SNS calls failed with `AccessDenied`.
* No CloudTrail management evidence of destructive or mutating actions.

### Potential impact that cannot be fully ruled out

* S3 object access (read/write/delete) on the knowledge bucket, depending on whether S3 data event logging was enabled at the time.

---

## Root cause (most plausible)

The access key and secret key for `knowledge-blob-user` were exposed outside of a strictly controlled secret store. In this setup, the key existed as a long-lived IAM user credential and was configured directly into runtime environment variables for services that access S3.

We do not have definitive evidence of the exact leak vector yet, but common vectors in this pattern include Terraform state exposure, CI/CD logs, local environment files, or accidental sharing.

---

## Remediation performed

1. **Credential rotation**

    * Created a new access key for `knowledge-blob-user`
    * Updated App Runner (`conversational-ui`) environment variables to use the new key
2. **Credential revocation**

    * Marked the compromised key as inactive
    * Deleted the compromised key at ~12:30 local time on 2025-12-26
3. **Production verification (end-to-end)**

    * Confirmed conversational UI still runs and streaming works
    * Confirmed read access to existing generated docs still works
    * **Confirmed new doc generation succeeds and uploads new artifacts to the knowledge blob S3 bucket (worker Lambda path validated)**

---

## Next steps (prevent recurrence and close gaps)

### 1) Confirm whether S3 data events are enabled

* If not enabled, enable CloudTrail **S3 data events** for the knowledge bucket going forward.
* This provides auditability for `GetObject`, `PutObject`, `DeleteObject`.

### 2) Remove long-lived IAM user keys (recommended architectural fix)

Move S3 access to IAM roles instead of IAM user keys:

* App Runner: attach S3 permissions to the App Runner instance role, remove `BLOB_ACCESS_KEY_ID` and `BLOB_READ_WRITE_TOKEN` entirely.
* Lambda: attach S3 permissions to the Lambda execution role.
  This eliminates static credentials and makes rotation unnecessary.

### 3) Tighten controls and monitoring

* Ensure least-privilege policies for S3 actions (only required prefixes if possible).
* Add budget alerts and anomaly detection for spend.
* Add alerts for unusual access key usage (new IPs, new regions, unusual services).
* Confirm root account MFA and general account security posture.

### 4) Close the AWS Support Case

Respond with:

* The compromised key was deleted (~12:30 local time, 2025-12-26)
* Investigation summary (SES/SNS probing denied, no observed IAM mutations)
* Acknowledgement of the S3 data event logging limitation, plus planned mitigation
* Confirmation that production is healthy after rotation and worker doc generation was validated

---

## Action items

* [ ] Enable CloudTrail S3 data events for the knowledge bucket
* [ ] Refactor App Runner and Lambda to use IAM roles for S3 access, remove IAM user keys
* [ ] Audit possible secret leak sources (Terraform state access, CI logs, env files, repo scanning)
* [ ] Add cost and security alerts, and document the credential handling policy

---

## Current status

* Compromised key is deleted.
* Production services are healthy after rotation.
* Worker Lambda blob write path is confirmed working post-rotation.
* Longer-term fix is planned: eliminate static IAM user keys and improve S3 auditability.
