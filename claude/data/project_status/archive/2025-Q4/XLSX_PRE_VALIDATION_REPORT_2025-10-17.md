================================================================================
XLSX PRE-IMPORT VALIDATION REPORT
================================================================================
Generated: 2025-10-17 16:05:27


✅ COMMENTS: comments.xlsx
   Quality Score: 90.0/100
   Total Rows: 204,625
   Total Columns: 10

   ❌ [WARNING] Found 1 non-numeric ticket IDs
   ❌ [WARNING] Found 25 unparseable dates
   ✅ [INFO] ✅ All 10 expected columns present
   ✅ [INFO] ✅ All 5 required columns present
   ✅ [INFO] ✅ CT-VISIBLE-CUSTOMER: 2.50% populated (sparse but present)
   ✅ [INFO] ✅ Comment text: Average 2159 chars
   ✅ [INFO] Row count reasonable: 204,625 (pre-filter)

✅ TICKETS: tickets.xlsx
   Quality Score: 100.0/100
   Total Rows: 652,681
   Total Columns: 60

   ✅ [INFO] ✅ Ticket ID column: TKT-Ticket ID
   ✅ [INFO] ✅ Created Time column: TKT-Created Date-Time
   ✅ [INFO] Column count in expected range: 60
   ✅ [INFO] Row count reasonable: 652,681 (pre-filter)

✅ TIMESHEETS: timesheets.xlsx
   Quality Score: 100.0/100
   Total Rows: 732,959
   Total Columns: 21

   ✅ [INFO] ✅ Date column: Date
   ✅ [INFO] ✅ CRM column: Crm
   ✅ [INFO] Column count in expected range: 21
   ✅ [INFO] Row count reasonable: 732,959 (pre-filter)

================================================================================
VALIDATION SUMMARY
================================================================================
✅ PASS: comments.xlsx (Score: 90.0/100)
✅ PASS: tickets.xlsx (Score: 100.0/100)
✅ PASS: timesheets.xlsx (Score: 100.0/100)

⚠️  2 warnings detected - review before import

================================================================================
RECOMMENDATION
================================================================================
⚠️  PROCEED WITH CAUTION - Minor warnings acceptable