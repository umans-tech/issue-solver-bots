# App Runner Certificate Validation Workaround

## Problem
When deploying AWS App Runner services with custom domains, Terraform encounters an error when trying to use `for_each` to create DNS validation records:

```
Error: Invalid for_each argument
The "for_each" map includes keys derived from resource attributes that
cannot be determined until apply, and so Terraform cannot determine the
full set of keys that will identify the instances of this resource.
```

This happens because `certificate_validation_records` are only known after the `aws_apprunner_custom_domain_association` resource is created.

## Solution
We use a workaround that replaces `for_each` with `count` and `tolist()`:

1. **Static Count**: We use a fixed count (typically 3) based on AWS's behavior
2. **tolist() Function**: This creates a runtime dependency instead of a static one
3. **Separate Resources**: We create separate validation resources for each domain

## Configuration
The number of validation records is configurable via the `cert_validation_records_count` local variable in `conversational-ui.tf`.

## Troubleshooting

### Error: Index out of bounds
If you get an error like "index 2 out of bounds for list with 2 elements", it means the actual number of validation records is less than `cert_validation_records_count`.

**Solution**: Reduce the value of `cert_validation_records_count` in the locals block.

### Error: Not enough validation records
If SSL certificate validation fails, you might need more validation records.

**Solution**: Increase the value of `cert_validation_records_count` in the locals block.

### Finding the right count
To determine the correct number of validation records:
1. Deploy the `aws_apprunner_custom_domain_association` resource first using `-target`
2. Check the output of `terraform show` to see how many validation records were created
3. Update `cert_validation_records_count` accordingly

## References
- [GitHub Issue #23460](https://github.com/hashicorp/terraform-provider-aws/issues/23460)
- [Terraform for_each limitations](https://www.terraform.io/language/meta-arguments/for_each#limitations-on-values-used-in-for_each) 