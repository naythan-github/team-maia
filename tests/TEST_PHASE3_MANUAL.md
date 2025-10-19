# Phase 3 Manual Testing Guide

**Status**: Phase 3 requires PostgreSQL instance for integration testing

## Why Manual Testing?

Phase 3 enhanced migration involves complex PostgreSQL operations:
- Schema creation/deletion
- Transaction management  
- pg_dump/restore operations
- Real database queries

Mocking all PostgreSQL operations is fragile and doesn't test real behavior.

## Manual Test Procedure

### Prerequisites
```bash
# Start PostgreSQL Docker container
docker run --name servicedesk-postgres-test \
  -e POSTGRES_DB=servicedesk \
  -e POSTGRES_USER=servicedesk_user \
  -e POSTGRES_PASSWORD=servicedesk_pass \
  -p 5433:5432 \
  -d postgres:15
```

### Test 1: Quality Gate
```bash
python3 claude/infrastructure/servicedesk-dashboard/migration/migrate_sqlite_to_postgres_enhanced.py \
  --source tests/fixtures/test_tickets.db \
  --mode simple \
  --min-quality 80
```

Expected: Migration proceeds if quality ≥80, fails if <80

### Test 2: Canary Deployment
```bash
python3 claude/infrastructure/servicedesk-dashboard/migration/migrate_sqlite_to_postgres_enhanced.py \
  --source tests/fixtures/test_tickets.db \
  --mode canary
```

Expected: Creates canary schema, validates, drops canary, full migration

### Test 3: Blue-Green Deployment
```bash
python3 claude/infrastructure/servicedesk-dashboard/migration/migrate_sqlite_to_postgres_enhanced.py \
  --source tests/fixtures/test_tickets.db \
  --mode blue-green
```

Expected: Creates versioned schema, returns cutover/rollback commands

### Test 4: Complete Workflow
```bash
python3 claude/infrastructure/servicedesk-dashboard/migration/migrate_sqlite_to_postgres_enhanced.py \
  --source tests/fixtures/test_tickets.db \
  --mode complete \
  --min-quality 80
```

Expected: Quality gate → Canary → Blue-green all execute successfully

## Validation Queries

```sql
-- Check schemas created
SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE 'servicedesk%';

-- Check row count
SELECT COUNT(*) FROM servicedesk.tickets;

-- Check column types (should be TIMESTAMP not TEXT)
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_schema = 'servicedesk' AND table_name = 'tickets';
```

## Success Criteria

- ✅ Quality gate blocks low-quality data (<80)
- ✅ Canary validates 10% sample before full migration
- ✅ Blue-green creates versioned schema
- ✅ TIMESTAMP columns created (not TEXT)
- ✅ Rollback commands work
- ✅ Zero manual schema fixes required

