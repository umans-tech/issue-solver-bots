# Vector Store Cleanup Tooling

This document describes the comprehensive vector store cleanup system designed to help manage OpenAI's 100GB storage limit effectively and safely.

## Overview

The cleanup system provides a two-phase approach:
1. **Planning Phase**: Analyze current vector stores and show what would be deleted
2. **Execution Phase**: Perform cleanup with user confirmation and detailed reporting

## Features

- ✅ **Safety First**: Production stores are protected from deletion
- ✅ **Dry Run Mode**: Test cleanup without actual deletions
- ✅ **User Confirmation**: Required before any actual deletions
- ✅ **Detailed Reporting**: Comprehensive JSON reports of all operations
- ✅ **Error Handling**: Robust retry logic and error recovery
- ✅ **Progress Tracking**: Real-time logging of cleanup operations

## Quick Start

### Prerequisites

1. **OpenAI API Key**: Set the `OPENAI_API_KEY` environment variable
2. **Production Store IDs**: Update `issue-solver/scripts/production_vector_stores.csv` with your production vector store IDs

### Basic Usage

```bash
# 1. Plan cleanup (safe - no deletions)
just plan-cleanup

# 2. Execute cleanup with confirmation
just cleanup

# 3. Dry run (shows what would happen)
just cleanup-dry-run
```

## Detailed Usage

### Planning Phase

Shows what would be deleted without making any changes:

```bash
just plan-cleanup
```

This will:
- Fetch all vector stores from OpenAI
- Classify them as production vs non-production
- Show detailed statistics about current usage
- Display which stores would be deleted and which kept
- Save a plan report to `reports/vector_store_plan_*.json`

### Execution Phase

Executes the cleanup plan with user confirmation:

```bash
just cleanup
```

This will:
- Generate the cleanup plan
- Display the plan for review
- Ask for user confirmation
- Execute deletions (if confirmed)
- Save a detailed execution report

### Dry Run Mode

Test the cleanup without actual deletions:

```bash
just cleanup-dry-run
```

Performs all steps except actual deletion, useful for:
- Testing the cleanup logic
- Reviewing what would be deleted
- Validating production store protection

## Configuration

### Production Vector Stores

Edit `issue-solver/scripts/production_vector_stores.csv` to list production vector store IDs (one per line):

```csv
vs_prod_123abc4567890def
vs_prod_456def7890123abc
vs_prod_789ghi0123456def
```

**Important**: Any vector store ID listed in this file will be protected from deletion.

### Cleanup Rules

The current cleanup strategy:
- **Keep**: All production stores (listed in CSV)
- **Keep**: Non-production stores created in the last 7 days
- **Delete**: Non-production stores older than 7 days

## Safety Measures

### Production Protection
- Vector stores listed in `issue-solver/scripts/production_vector_stores.csv` are **never** deleted
- The system clearly marks production stores in all reports

### User Confirmation
- Before any deletions, the system shows exactly what will be deleted
- User must explicitly confirm with 'y' or 'yes'
- Default action is to cancel (pressing Enter cancels)

### Dry Run Mode
- `--dry-run` flag shows all actions without executing them
- Perfect for testing and validation

### Error Handling
- Robust retry logic with exponential backoff
- Failed deletions are logged and reported
- Partial failures don't stop the entire cleanup process

## Reports

All cleanup operations generate detailed JSON reports in the `reports/` directory:

### Plan Reports
- **Filename**: `vector_store_plan_YYYYMMDD_HHMMSS.json`
- **Content**: Current state analysis and cleanup plan

### Cleanup Reports  
- **Filename**: `vector_store_cleanup_YYYYMMDD_HHMMSS.json`
- **Content**: Full execution details, success/failure statistics

### Report Structure

```json
{
  "plan": {
    "total_stores": 25,
    "production_stores": 5,
    "non_production_stores": 20,
    "total_size_bytes": 10737418240,
    "estimated_savings_gb": 8.5,
    "stores_to_delete": [...],
    "stores_to_keep": [...]
  },
  "execution_started": "2024-12-16T14:30:22",
  "execution_completed": "2024-12-16T14:35:45",
  "deleted_stores": [...],
  "failed_deletions": [...],
  "actual_savings_gb": 8.3,
  "success_rate": 95.0
}
```

## Advanced Usage

### Custom Production CSV

Specify a different CSV file:

```bash
# Using custom CSV file
python scripts/vector_store_cleanup.py plan --production-csv /path/to/custom.csv
python scripts/vector_store_cleanup.py cleanup --production-csv /path/to/custom.csv
```

### Direct Script Usage

Run the script directly for more control:

```bash
# Plan only
python scripts/vector_store_cleanup.py plan

# Cleanup with confirmation
python scripts/vector_store_cleanup.py cleanup

# Dry run
python scripts/vector_store_cleanup.py cleanup --dry-run

# Show help
python scripts/vector_store_cleanup.py --help
```

## Monitoring and Maintenance

### Regular Cleanup Schedule

Consider running cleanup regularly:

```bash
# Weekly cleanup planning
just plan-cleanup

# Monthly actual cleanup (after review)
just cleanup
```

### Storage Monitoring

Monitor your OpenAI storage usage:
- The plan command shows current total usage
- Reports track savings over time
- Set up alerts when approaching 100GB limit

### Report Management

- Reports are kept indefinitely for audit trail
- Consider archiving old reports to save disk space
- Reports can be used for billing and usage analysis

## Troubleshooting

### Common Issues

1. **"OPENAI_API_KEY environment variable not set"**
   - Set your OpenAI API key: `export OPENAI_API_KEY=your_key_here`

2. **"Production CSV file not found"**
   - Create `issue-solver/scripts/production_vector_stores.csv` or specify correct path
   - File can be empty if no production stores exist

3. **"Error fetching vector stores"**
   - Check internet connection
   - Verify API key has correct permissions
   - Check OpenAI service status

### Logging

The script provides detailed logging:
- INFO level: Normal operations
- WARNING level: Non-critical issues  
- ERROR level: Serious problems requiring attention

### Recovery

If cleanup fails partially:
- Check the cleanup report for failed deletions
- Re-run cleanup to retry failed deletions
- Failed stores are clearly identified in reports

## Security Considerations

- **API Key Protection**: Never commit API keys to version control
- **Production Safety**: Always verify production store list before cleanup
- **Access Control**: Limit access to cleanup tools to authorized personnel
- **Audit Trail**: All operations are logged and reported for compliance

## Best Practices

1. **Always Plan First**: Run `just plan-cleanup` before actual cleanup
2. **Review Production List**: Regularly update `issue-solver/scripts/production_vector_stores.csv`
3. **Start with Dry Run**: Use `--dry-run` when testing changes
4. **Monitor Reports**: Review cleanup reports for patterns and issues
5. **Regular Maintenance**: Schedule periodic cleanups to prevent storage overflow

## Technical Details

### Dependencies

The cleanup script requires:
- `openai`: OpenAI API client
- `tenacity`: Retry logic for API calls
- Standard library: `argparse`, `csv`, `json`, `datetime`, `pathlib`

### Performance

- Parallel operations where possible (file deletions)
- Retry logic with exponential backoff
- Efficient API usage to minimize costs
- Progress tracking for large operations

### Extensibility

The script is designed to be easily extended:
- Pluggable cleanup strategies
- Configurable retention policies  
- Custom reporting formats
- Integration with monitoring systems