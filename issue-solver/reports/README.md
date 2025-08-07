# Vector Store Cleanup Reports

This directory contains detailed reports from vector store cleanup operations.

## Report Types

### Plan Reports (`vector_store_plan_*.json`)
Generated when running `just plan-cleanup`, these reports show:
- Current state of all vector stores
- Which stores would be deleted vs kept
- Estimated storage savings
- Detailed store information

### Cleanup Reports (`vector_store_cleanup_*.json`)
Generated after running `just cleanup`, these reports include:
- The original cleanup plan
- Execution details (start/end times)
- Successfully deleted stores
- Failed deletions (if any)
- Actual storage savings achieved
- Success rate statistics

## Report Format

All reports are saved in JSON format with timestamps in the filename:
- Format: `vector_store_{type}_{YYYYMMDD_HHMMSS}.json`
- Example: `vector_store_cleanup_20241216_143022.json`

## Report Contents

### Plan Report Structure
```json
{
  "plan": {
    "total_stores": 25,
    "production_stores": 5,
    "non_production_stores": 20,
    "estimated_savings_gb": 15.6,
    "stores_to_delete": [...],
    "stores_to_keep": [...]
  },
  "execution_started": "2024-12-16T14:30:22",
  "execution_completed": "2024-12-16T14:30:22",
  "dry_run": false
}
```

### Cleanup Report Structure
```json
{
  "plan": {...},
  "execution_started": "2024-12-16T14:30:22",
  "execution_completed": "2024-12-16T14:35:45",
  "deleted_stores": [...],
  "failed_deletions": [...],
  "actual_savings_bytes": 16777216000,
  "actual_savings_gb": 15.6,
  "success_rate": 95.0,
  "dry_run": false
}
```

## Report Retention

Reports are kept indefinitely to provide a historical record of cleanup activities. Consider archiving or removing old reports periodically to save disk space.