#!/usr/bin/env python3
"""
Vector Store Cleanup Tool

This script provides comprehensive cleanup functionality for OpenAI vector stores
to help manage the 100GB storage limit. It includes both planning and execution
phases with detailed reporting.

Usage:
    python scripts/vector_store_cleanup.py plan [--production-csv PATH]
    python scripts/vector_store_cleanup.py cleanup [--production-csv PATH] [--dry-run]
"""

import argparse
import csv
import json
import logging
import os
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_random_exponential

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class VectorStoreInfo:
    """Information about a vector store."""

    id: str
    name: str
    file_counts: int
    usage_bytes: int
    created_at: int
    last_active_at: Optional[int] = None
    is_production: bool = False


@dataclass
class CleanupPlan:
    """Cleanup plan with statistics."""

    total_stores: int
    production_stores: int
    non_production_stores: int
    total_size_bytes: int
    stores_to_delete: List[VectorStoreInfo]
    stores_to_keep: List[VectorStoreInfo]
    estimated_savings_bytes: int
    estimated_savings_gb: float


@dataclass
class CleanupReport:
    """Report of cleanup execution."""

    plan: CleanupPlan
    execution_started: datetime
    execution_completed: datetime
    deleted_stores: List[VectorStoreInfo]
    failed_deletions: List[Dict]
    actual_savings_bytes: int
    actual_savings_gb: float
    success_rate: float


class VectorStoreCleanup:
    """Main cleanup orchestrator."""

    def __init__(
        self, production_csv_path: Optional[str] = None, dry_run: bool = False
    ):
        """Initialize the cleanup tool."""
        self.client = OpenAI()
        self.dry_run = dry_run
        self.production_ids = self._load_production_ids(production_csv_path)
        self.reports_dir = Path("reports")
        self.reports_dir.mkdir(exist_ok=True)

        logger.info(
            f"Initialized cleanup tool with {len(self.production_ids)} production vector stores"
        )
        if self.dry_run:
            logger.info("DRY RUN MODE: No actual deletions will be performed")

    def _load_production_ids(self, csv_path: Optional[str]) -> Set[str]:
        """Load production vector store IDs from CSV file."""
        # Default to CSV located next to this script if not explicitly provided
        default_csv_path = Path(__file__).parent / "production_vector_stores.csv"
        production_ids: set[str] = set()
        csv_file = Path(csv_path) if csv_path else default_csv_path

        if not csv_file.exists():
            logger.warning(f"Production CSV file not found: {csv_path}")
            logger.warning("All vector stores will be considered non-production")
            return production_ids

        try:
            with open(csv_file, "r", newline="") as f:
                reader = csv.reader(f)
                for row in reader:
                    if row and row[0].strip():  # Skip empty rows
                        production_ids.add(row[0].strip())

            logger.info(
                f"Loaded {len(production_ids)} production vector store IDs from {csv_path}"
            )
            return production_ids

        except Exception as e:
            logger.error(f"Error reading production CSV file {csv_path}: {e}")
            return production_ids

    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(3))
    def _get_vector_store_info(self, store_id: str) -> Optional[VectorStoreInfo]:
        """Get detailed information about a vector store."""
        try:
            store = self.client.vector_stores.retrieve(store_id)

            return VectorStoreInfo(
                id=store.id,
                name=store.name or f"Vector Store {store.id[:8]}",
                file_counts=store.file_counts.total,
                usage_bytes=store.usage_bytes,
                created_at=store.created_at,
                last_active_at=store.last_active_at,
                is_production=store.id in self.production_ids,
            )
        except Exception as e:
            logger.error(f"Error getting info for vector store {store_id}: {e}")
            return None

    def get_all_vector_stores(self) -> List[VectorStoreInfo]:
        """Get information about all vector stores."""
        logger.info("Fetching all vector stores...")

        stores = []
        try:
            for store in self.client.vector_stores.list(limit=100):
                store_info = self._get_vector_store_info(store.id)
                if store_info:
                    stores.append(store_info)

            logger.info(f"Found {len(stores)} vector stores")
            return stores

        except Exception as e:
            logger.error(f"Error fetching vector stores: {e}")
            return []

    def create_cleanup_plan(self) -> CleanupPlan:
        """Create a cleanup plan showing what would be deleted."""
        logger.info("Creating cleanup plan...")

        all_stores = self.get_all_vector_stores()

        if not all_stores:
            logger.warning("No vector stores found")
            return CleanupPlan(
                total_stores=0,
                production_stores=0,
                non_production_stores=0,
                total_size_bytes=0,
                stores_to_delete=[],
                stores_to_keep=[],
                estimated_savings_bytes=0,
                estimated_savings_gb=0.0,
            )

        # Separate production and non-production stores
        production_stores = [s for s in all_stores if s.is_production]
        non_production_stores = [s for s in all_stores if not s.is_production]

        # For this implementation, we'll delete non-production stores older than 7 days
        # and keep production stores safe
        cutoff_timestamp = int((datetime.now().timestamp() - (7 * 24 * 60 * 60)))

        stores_to_delete = [
            s for s in non_production_stores if s.created_at < cutoff_timestamp
        ]

        stores_to_keep = production_stores + [
            s for s in non_production_stores if s.created_at >= cutoff_timestamp
        ]

        total_size = sum(s.usage_bytes for s in all_stores)
        estimated_savings = sum(s.usage_bytes for s in stores_to_delete)

        plan = CleanupPlan(
            total_stores=len(all_stores),
            production_stores=len(production_stores),
            non_production_stores=len(non_production_stores),
            total_size_bytes=total_size,
            stores_to_delete=stores_to_delete,
            stores_to_keep=stores_to_keep,
            estimated_savings_bytes=estimated_savings,
            estimated_savings_gb=estimated_savings / (1024**3),
        )

        return plan

    def print_cleanup_plan(self, plan: CleanupPlan):
        """Print a detailed cleanup plan."""
        print("\n" + "=" * 80)
        print("VECTOR STORE CLEANUP PLAN")
        print("=" * 80)

        print("\n📊 STATISTICS:")
        print(f"   Total vector stores: {plan.total_stores}")
        print(f"   Production stores: {plan.production_stores}")
        print(f"   Non-production stores: {plan.non_production_stores}")
        print(f"   Total storage used: {plan.total_size_bytes / (1024**3):.2f} GB")

        print("\n🗑️  CLEANUP PLAN:")
        print(f"   Stores to delete: {len(plan.stores_to_delete)}")
        print(f"   Stores to keep: {len(plan.stores_to_keep)}")
        print(f"   Estimated savings: {plan.estimated_savings_gb:.2f} GB")

        if plan.stores_to_delete:
            print("\n📋 STORES TO DELETE:")
            for store in sorted(
                plan.stores_to_delete, key=lambda x: x.usage_bytes, reverse=True
            ):
                created_date = datetime.fromtimestamp(store.created_at).strftime(
                    "%Y-%m-%d"
                )
                size_mb = store.usage_bytes / (1024**2)
                print(
                    f"   • {store.name[:40]:<40} | {store.id[:12]} | {created_date} | {size_mb:8.1f} MB | {store.file_counts:4} files"
                )

        if plan.stores_to_keep:
            print("\n✅ STORES TO KEEP (Production + Recent):")
            for store in sorted(
                plan.stores_to_keep, key=lambda x: x.usage_bytes, reverse=True
            ):
                created_date = datetime.fromtimestamp(store.created_at).strftime(
                    "%Y-%m-%d"
                )
                size_mb = store.usage_bytes / (1024**2)
                prod_flag = " [PROD]" if store.is_production else ""
                print(
                    f"   • {store.name[:40]:<40} | {store.id[:12]} | {created_date} | {size_mb:8.1f} MB | {store.file_counts:4} files{prod_flag}"
                )

        print("=" * 80)

    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(3))
    def _delete_vector_store(self, store: VectorStoreInfo) -> bool:
        """Delete a single vector store."""
        try:
            if self.dry_run:
                logger.info(
                    f"DRY RUN: Would delete vector store {store.name} ({store.id})"
                )
                return True

            # Delete all files in the vector store first
            for file in self.client.vector_stores.files.list(
                vector_store_id=store.id, limit=100
            ):
                try:
                    self.client.vector_stores.files.delete(
                        vector_store_id=store.id, file_id=file.id
                    )
                except Exception as e:
                    logger.warning(
                        f"Error deleting file {file.id} from vector store {store.id}: {e}"
                    )

            # Delete the vector store
            self.client.vector_stores.delete(store.id)
            logger.info(
                f"Deleted vector store {store.name} ({store.id}) - freed {store.usage_bytes / (1024**2):.1f} MB"
            )
            return True

        except Exception as e:
            logger.error(f"Error deleting vector store {store.name} ({store.id}): {e}")
            return False

    def execute_cleanup(self, plan: CleanupPlan) -> CleanupReport:
        """Execute the cleanup plan."""
        execution_started = datetime.now()
        logger.info(f"Starting cleanup execution at {execution_started}")

        if not plan.stores_to_delete:
            logger.info("No vector stores to delete")
            return CleanupReport(
                plan=plan,
                execution_started=execution_started,
                execution_completed=datetime.now(),
                deleted_stores=[],
                failed_deletions=[],
                actual_savings_bytes=0,
                actual_savings_gb=0.0,
                success_rate=100.0,
            )

        deleted_stores = []
        failed_deletions = []

        for store in plan.stores_to_delete:
            if self._delete_vector_store(store):
                deleted_stores.append(store)
            else:
                failed_deletions.append(
                    {
                        "store_id": store.id,
                        "store_name": store.name,
                        "error": "Failed to delete",
                    }
                )

        execution_completed = datetime.now()
        actual_savings_bytes = sum(s.usage_bytes for s in deleted_stores)
        success_rate = (
            (len(deleted_stores) / len(plan.stores_to_delete)) * 100
            if plan.stores_to_delete
            else 100
        )

        report = CleanupReport(
            plan=plan,
            execution_started=execution_started,
            execution_completed=execution_completed,
            deleted_stores=deleted_stores,
            failed_deletions=failed_deletions,
            actual_savings_bytes=actual_savings_bytes,
            actual_savings_gb=actual_savings_bytes / (1024**3),
            success_rate=success_rate,
        )

        logger.info(
            f"Cleanup completed. Deleted {len(deleted_stores)}/{len(plan.stores_to_delete)} stores"
        )
        return report

    def save_report(self, report: CleanupReport, report_type: str = "cleanup"):
        """Save cleanup report to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.reports_dir / f"vector_store_{report_type}_{timestamp}.json"

        # Convert dataclasses to dictionaries for JSON serialization
        report_dict = {
            "plan": {
                "total_stores": report.plan.total_stores,
                "production_stores": report.plan.production_stores,
                "non_production_stores": report.plan.non_production_stores,
                "total_size_bytes": report.plan.total_size_bytes,
                "estimated_savings_bytes": report.plan.estimated_savings_bytes,
                "estimated_savings_gb": report.plan.estimated_savings_gb,
                "stores_to_delete": [
                    asdict(store) for store in report.plan.stores_to_delete
                ],
                "stores_to_keep": [
                    asdict(store) for store in report.plan.stores_to_keep
                ],
            },
            "execution_started": report.execution_started.isoformat(),
            "execution_completed": report.execution_completed.isoformat(),
            "deleted_stores": [asdict(store) for store in report.deleted_stores],
            "failed_deletions": report.failed_deletions,
            "actual_savings_bytes": report.actual_savings_bytes,
            "actual_savings_gb": report.actual_savings_gb,
            "success_rate": report.success_rate,
            "dry_run": self.dry_run,
        }

        with open(report_path, "w") as f:
            json.dump(report_dict, f, indent=2)

        logger.info(f"Report saved to {report_path}")
        return report_path

    def confirm_cleanup(self, plan: CleanupPlan) -> bool:
        """Ask user for confirmation before cleanup."""
        if not plan.stores_to_delete:
            logger.info("No stores to delete, no confirmation needed")
            return True

        print("\n⚠️  CONFIRMATION REQUIRED")
        print(f"You are about to delete {len(plan.stores_to_delete)} vector stores")
        print(f"This will free up {plan.estimated_savings_gb:.2f} GB of storage")

        if self.dry_run:
            print("This is a DRY RUN - no actual deletions will be performed")
            return True

        while True:
            response = input("\nDo you want to proceed? [y/N]: ").strip().lower()
            if response in ["y", "yes"]:
                return True
            elif response in ["n", "no", ""]:
                return False
            else:
                print("Please answer 'y' for yes or 'n' for no")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="OpenAI Vector Store Cleanup Tool")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Plan command
    plan_parser = subparsers.add_parser(
        "plan", help="Show cleanup plan without executing"
    )
    plan_parser.add_argument(
        "--production-csv",
        help="Path to CSV file containing production vector store IDs",
        default=None,
    )

    # Cleanup command
    cleanup_parser = subparsers.add_parser(
        "cleanup", help="Execute cleanup with confirmation"
    )
    cleanup_parser.add_argument(
        "--production-csv",
        help="Path to CSV file containing production vector store IDs",
        default=None,
    )
    cleanup_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY environment variable not set")
        return 1

    try:
        cleanup_tool = VectorStoreCleanup(
            production_csv_path=args.production_csv,
            dry_run=getattr(args, "dry_run", False),
        )

        if args.command == "plan":
            plan = cleanup_tool.create_cleanup_plan()
            cleanup_tool.print_cleanup_plan(plan)

            # Save plan as report
            dummy_report = CleanupReport(
                plan=plan,
                execution_started=datetime.now(),
                execution_completed=datetime.now(),
                deleted_stores=[],
                failed_deletions=[],
                actual_savings_bytes=0,
                actual_savings_gb=0.0,
                success_rate=100.0,
            )
            cleanup_tool.save_report(dummy_report, "plan")

        elif args.command == "cleanup":
            plan = cleanup_tool.create_cleanup_plan()
            cleanup_tool.print_cleanup_plan(plan)

            if cleanup_tool.confirm_cleanup(plan):
                report = cleanup_tool.execute_cleanup(plan)
                cleanup_tool.save_report(report, "cleanup")

                print("\n✅ Cleanup completed!")
                print(f"   Deleted stores: {len(report.deleted_stores)}")
                print(f"   Failed deletions: {len(report.failed_deletions)}")
                print(f"   Actual savings: {report.actual_savings_gb:.2f} GB")
                print(f"   Success rate: {report.success_rate:.1f}%")
            else:
                print("Cleanup cancelled by user")
                return 1

        return 0

    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
