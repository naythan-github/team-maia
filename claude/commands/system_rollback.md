# System Rollback Command

## Overview
Execute comprehensive system rollbacks using checkpoint-based recovery procedures for Maia infrastructure.

## Usage

```bash
# Create rollback checkpoint before major changes
maia system_rollback checkpoint "data_migration" "Moving databases to iCloud Drive" --files-affected claude/tools/config/data_paths.py claude/tools/backlog_manager.py

# List available rollback checkpoints
maia system_rollback list

# Get rollback recommendations for current issues
maia system_rollback recommendations --issues "database access errors" "import failures"

# Execute full rollback to specific checkpoint
maia system_rollback execute checkpoint_20250909_143022 --type full

# Execute partial rollback (git only)
maia system_rollback execute checkpoint_20250909_143022 --type git_only

# Verify system health after changes
maia system_rollback verify
```

## Command Parameters

### create_checkpoint
- **change_type**: Type of change being made (data_migration, architecture, tool_update, security, etc.)
- **description**: Clear description of the change
- **--files-affected**: Optional list of files that will be modified
- **--backup-databases**: Include database backups (default: true)
- **--backup-critical-files**: Include critical file backups (default: true)

### execute_rollback
- **checkpoint_id**: ID of checkpoint to rollback to
- **--type**: Rollback type
  - `full`: Complete rollback (git + data + files)
  - `git_only`: Only rollback git repository
  - `data_only`: Only rollback databases
  - `files_only`: Only rollback critical files
- **--confirm**: Skip confirmation prompt
- **--verify**: Run health check after rollback

### list_checkpoints
- **--recent**: Only show checkpoints from last 7 days
- **--type**: Filter by change type
- **--detailed**: Show detailed checkpoint information

### get_recommendations
- **--issues**: List of current system issues
- **--max-recommendations**: Maximum recommendations to return (default: 5)
- **--confidence-threshold**: Minimum confidence level (default: 0.7)

## Implementation

```python
#!/usr/bin/env python3
import sys
import argparse
from pathlib import Path

# Add Maia tools to path
sys.path.append(str(Path(__file__).parent.parent / "tools"))

from operations.rollback_procedures import MaiaRollbackManager

def main():
    parser = argparse.ArgumentParser(description="Maia System Rollback Management")
    subparsers = parser.add_subparsers(dest="command", help="Rollback operations")

    # Create checkpoint command
    checkpoint_parser = subparsers.add_parser("checkpoint", help="Create rollback checkpoint")
    checkpoint_parser.add_argument("change_type", help="Type of change being made")
    checkpoint_parser.add_argument("description", help="Description of the change")
    checkpoint_parser.add_argument("--files-affected", nargs="*", help="Files that will be modified")

    # List checkpoints command
    list_parser = subparsers.add_parser("list", help="List available checkpoints")
    list_parser.add_argument("--recent", action="store_true", help="Show only recent checkpoints")
    list_parser.add_argument("--type", help="Filter by change type")
    list_parser.add_argument("--detailed", action="store_true", help="Show detailed information")

    # Execute rollback command
    execute_parser = subparsers.add_parser("execute", help="Execute rollback to checkpoint")
    execute_parser.add_argument("checkpoint_id", help="Checkpoint ID to rollback to")
    execute_parser.add_argument("--type", default="full",
                              choices=["full", "git_only", "data_only", "files_only"],
                              help="Type of rollback to execute")
    execute_parser.add_argument("--confirm", action="store_true", help="Skip confirmation")
    execute_parser.add_argument("--verify", action="store_true", help="Run health check after rollback")

    # Get recommendations command
    rec_parser = subparsers.add_parser("recommendations", help="Get rollback recommendations")
    rec_parser.add_argument("--issues", nargs="*", help="Current system issues")
    rec_parser.add_argument("--max-recommendations", type=int, default=5, help="Max recommendations")
    rec_parser.add_argument("--confidence-threshold", type=float, default=0.7, help="Min confidence")

    # Verify system command
    verify_parser = subparsers.add_parser("verify", help="Verify system health")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    manager = MaiaRollbackManager()

    try:
        if args.command == "checkpoint":
            checkpoint_id = manager.create_rollback_checkpoint(
                args.change_type,
                args.description,
                args.files_affected
            )
            print(f"✅ Checkpoint created: {checkpoint_id}")

        elif args.command == "list":
            checkpoints = manager.list_checkpoints()

            if args.recent:
                from datetime import datetime, timedelta
                week_ago = datetime.now() - timedelta(days=7)
                checkpoints = [cp for cp in checkpoints
                             if datetime.fromisoformat(cp["timestamp"]) > week_ago]

            if args.type:
                checkpoints = [cp for cp in checkpoints if cp.get("change_type") == args.type]

            print(f"📋 Available checkpoints: {len(checkpoints)}")
            for cp in checkpoints:
                if args.detailed:
                    print(f"\n🏷️  {cp['checkpoint_id']}")
                    print(f"   📅 {cp['timestamp']}")
                    print(f"   🔧 {cp['change_type']}")
                    print(f"   📝 {cp['description']}")
                    print(f"   📦 Git: {cp['git_commit']}")
                else:
                    print(f"  • {cp['checkpoint_id']} ({cp['change_type']}) - {cp['description'][:60]}...")

        elif args.command == "execute":
            if not args.confirm:
                print(f"⚠️  You are about to rollback to checkpoint: {args.checkpoint_id}")
                print(f"🔧 Rollback type: {args.type}")
                response = input("❓ Continue? (yes/no): ").lower().strip()
                if response not in ["yes", "y"]:
                    print("❌ Rollback cancelled")
                    return 0

            success = manager.execute_rollback(args.checkpoint_id, args.type)

            if success:
                print("✅ Rollback completed successfully")
                if args.verify:
                    manager._verify_rollback_health()
            else:
                print("❌ Rollback failed - check logs for details")
                return 1

        elif args.command == "recommendations":
            recommendations = manager.get_rollback_recommendations(args.issues)

            # Filter by confidence threshold
            recommendations = [r for r in recommendations
                             if r["confidence"] >= args.confidence_threshold][:args.max_recommendations]

            print(f"💡 Rollback recommendations ({len(recommendations)}):")
            for i, rec in enumerate(recommendations, 1):
                print(f"\n{i}. {rec['checkpoint_id']}")
                print(f"   🎯 Confidence: {rec['confidence']:.1%}")
                print(f"   📝 Reason: {rec['reason']}")
                print(f"   ⏱️  Time: {rec['estimated_time']}")
                print(f"   ⚠️  Risks: {', '.join(rec['risks'])}")

        elif args.command == "verify":
            print("🏥 Running system health verification...")
            health = manager._verify_rollback_health()

            failed_checks = [check for check, result in health.items() if not result]
            if failed_checks:
                print(f"\n❌ Health check failed: {len(failed_checks)} issues found")
                return 1
            else:
                print("\n✅ All health checks passed")

    except Exception as e:
        print(f"💥 Command failed: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
```

## Rollback Types

### Full Rollback (`full`)
- Resets git repository to checkpoint commit
- Restores all databases from backups
- Restores all critical files from backups
- Runs comprehensive health check
- **Use for**: Complete system restoration after failed major changes

### Git Only Rollback (`git_only`)
- Only resets git repository to checkpoint commit
- Preserves current data and configuration files
- **Use for**: Code-only issues, reverting bad commits while preserving data

### Data Only Rollback (`data_only`)
- Restores databases from checkpoint backups
- Preserves current git state and files
- **Use for**: Database corruption or migration issues

### Files Only Rollback (`files_only`)
- Restores critical files from checkpoint backups
- Preserves git state and databases
- **Use for**: Configuration file corruption or accidental deletions

## Safety Features

### Checkpoint Creation
- Automatic git commit hash recording
- Complete database backups before changes
- Critical file backups
- System state capture for verification
- Rollback operation logging

### Rollback Execution
- Confirmation prompts for safety
- Backup branch creation before git rollbacks
- Step-by-step rollback with failure tracking
- Automatic health verification
- Detailed logging of all operations

### Health Verification
- Git repository integrity check
- Database accessibility verification
- Critical tool import validation
- Python environment verification
- System configuration validation

## Integration with Maia Workflows

### Pre-Change Checklist
1. Create rollback checkpoint: `maia system_rollback checkpoint`
2. Document change in checkpoint description
3. Execute planned changes
4. Verify system health: `maia system_rollback verify`
5. If issues occur, execute rollback: `maia system_rollback execute`

### Emergency Recovery
1. Identify current issues
2. Get recommendations: `maia system_rollback recommendations --issues "issue descriptions"`
3. Review recommendation confidence and risks
4. Execute recommended rollback
5. Verify system health post-rollback
6. Document incident and lessons learned

This command provides comprehensive safety net for Maia system modifications, ensuring rapid recovery from any architectural or data changes that cause issues.
