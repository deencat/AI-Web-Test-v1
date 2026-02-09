#!/usr/bin/env python3
"""
Clean up old debug session directories.

This script removes debug session browser profiles older than the specified age.
Can be run manually or as a cron job.

Usage:
    python cleanup_debug_sessions.py [--max-age-hours HOURS]
"""
import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from app.services.debug_session_service import get_debug_session_service


def main():
    parser = argparse.ArgumentParser(
        description="Clean up old debug session directories"
    )
    parser.add_argument(
        "--max-age-hours",
        type=int,
        default=48,
        help="Maximum age of sessions in hours (default: 48)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting"
    )
    
    args = parser.parse_args()
    
    # Get service instance
    service = get_debug_session_service()
    
    if args.dry_run:
        print(f"DRY RUN: Would clean up sessions older than {args.max_age_hours} hours")
        print(f"Directory: {service.user_data_base}")
        
        import time
        current_time = time.time()
        cutoff_time = current_time - (args.max_age_hours * 3600)
        
        if service.user_data_base.exists():
            count = 0
            for session_dir in service.user_data_base.iterdir():
                if session_dir.is_dir():
                    dir_mtime = session_dir.stat().st_mtime
                    if dir_mtime < cutoff_time:
                        age_hours = (current_time - dir_mtime) / 3600
                        print(f"  Would remove: {session_dir.name} (age: {age_hours:.1f}h)")
                        count += 1
            print(f"\nTotal directories to remove: {count}")
        else:
            print("No debug sessions directory found")
    else:
        print(f"Cleaning up debug sessions older than {args.max_age_hours} hours...")
        removed = service.cleanup_old_sessions(max_age_hours=args.max_age_hours)
        print(f"Removed {removed} old debug session(s)")


if __name__ == "__main__":
    main()
