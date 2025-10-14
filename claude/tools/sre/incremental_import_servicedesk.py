#!/usr/bin/env python3
"""
ServiceDesk Incremental Data Import Tool
Handles tickets, comments, and timesheets with metadata tracking
Cloud-touched logic: Imports all data for tickets where Cloud roster members worked
"""

import pandas as pd
import sqlite3
from datetime import datetime
from pathlib import Path
import sys

DB_PATH = Path.home() / "git/maia/claude/data/servicedesk_tickets.db"
CUTOFF_DATE = datetime(2025, 7, 1)  # System migration date - HARD CUTOFF

class ServiceDeskImporter:
    """Incremental import handler with Cloud-touched logic and metadata tracking"""

    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH))

    def record_import(self, source_type, file_name, records, start_date, end_date, filter_note):
        """Record import metadata"""
        query = """
            INSERT INTO import_metadata
            (source_type, file_name, records_imported, date_range_start, date_range_end, filter_applied)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        cursor = self.conn.execute(query, (
            source_type, file_name, records,
            start_date.isoformat() if start_date else None,
            end_date.isoformat() if end_date else None,
            filter_note
        ))
        self.conn.commit()
        return cursor.lastrowid

    def import_comments(self, file_path):
        """Import comments - identifies Cloud-touched tickets"""
        print(f"\n💬 STEP 1: Importing comments from: {file_path}")

        # Load CSV or Excel based on extension (first 10 columns only - rest are empty)
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path, encoding='utf-8-sig', usecols=range(10), low_memory=False)
        else:
            df = pd.read_excel(file_path, usecols=range(10))
        print(f"   Loaded {len(df):,} rows")

        # Clean column names
        df = df.rename(columns={
            'CT-COMMENT-ID': 'comment_id',
            'CT-TKT-ID': 'ticket_id',
            'CT-COMMENT': 'comment_text',
            'CT-USERID': 'user_id',
            'CT-USERIDNAME': 'user_name',
            'CT-OWNERTYPE': 'owner_type',
            'CT-DATEAMDTIME': 'created_time',
            'CT-VISIBLE-CUSTOMER': 'visible_to_customer',
            'CT-TYPE': 'comment_type',
            'CT-TKT-TEAM': 'team'
        })

        # Parse date (dayfirst=True for DD/MM/YYYY format)
        df['created_time'] = pd.to_datetime(df['created_time'], dayfirst=True, errors='coerce')
        df = df.dropna(subset=['created_time'])

        # HARD CUTOFF: July 1+ only (no pre-migration data)
        df_filtered = df[df['created_time'] >= CUTOFF_DATE].copy()
        print(f"   ✅ Filtered to {len(df_filtered):,} rows (July 1+ only)")

        # Get Cloud roster usernames
        roster_users = pd.read_sql_query("SELECT username FROM cloud_team_roster", self.conn)['username'].tolist()
        print(f"   📋 Cloud roster: {len(roster_users)} members")

        # Identify Cloud-touched tickets (convert to int for consistent matching with tickets CSV)
        cloud_touched = df_filtered[df_filtered['user_name'].isin(roster_users)]['ticket_id'].dropna().astype(int).unique()
        print(f"   🎯 Identified {len(cloud_touched):,} Cloud-touched tickets")

        # Keep ALL comments for Cloud-touched tickets (including non-Cloud collaborators)
        # Convert ticket_id to int for filtering
        df_filtered['ticket_id_int'] = df_filtered['ticket_id'].astype(int)
        df_final = df_filtered[df_filtered['ticket_id_int'].isin(cloud_touched)].drop(columns=['ticket_id_int'])
        print(f"   ✅ Keeping ALL comments for Cloud-touched tickets: {len(df_final):,} rows")

        # Import to database
        df_final.to_sql('comments', self.conn, if_exists='replace', index=False)

        # Record metadata
        start_date = df_final['created_time'].min()
        end_date = df_final['created_time'].max()
        import_id = self.record_import(
            'comments',
            Path(file_path).name,
            len(df_final),
            start_date,
            end_date,
            f'July 1+ only, {len(cloud_touched)} Cloud-touched tickets, all collaborators'
        )

        print(f"   ✅ Imported as import_id={import_id}")
        print(f"   📅 Date range: {start_date.date()} to {end_date.date()}")

        return import_id, list(cloud_touched)

    def import_tickets(self, file_path, cloud_touched_ids):
        """Import tickets for Cloud-touched ticket IDs"""
        print(f"\n📋 STEP 2: Importing tickets from: {file_path}")

        # Load CSV
        df = pd.read_csv(file_path, low_memory=False)
        print(f"   Loaded {len(df):,} rows")

        # Find column names
        date_col = [c for c in df.columns if 'Created' in c and 'Time' in c][0]
        ticket_id_col = [c for c in df.columns if 'Ticket ID' in c][0]

        # Parse date (dayfirst=True for DD/MM/YYYY format)
        df[date_col] = pd.to_datetime(df[date_col], dayfirst=True)

        # Filter to Cloud-touched tickets (no date filter - tickets may predate July 1 but have Cloud comments after)
        df_final = df[df[ticket_id_col].isin(cloud_touched_ids)].copy()
        print(f"   🎯 Cloud-touched tickets: {len(df_final):,} rows (no date filter - filtered by Cloud activity)")

        # Import to database
        df_final.to_sql('tickets', self.conn, if_exists='replace', index=False)

        # Record metadata
        start_date = df_final[date_col].min()
        end_date = df_final[date_col].max()
        import_id = self.record_import(
            'tickets',
            Path(file_path).name,
            len(df_final),
            start_date,
            end_date,
            f'Cloud-touched tickets (filtered by activity, not creation date), {len(cloud_touched_ids)} IDs'
        )

        print(f"   ✅ Imported as import_id={import_id}")
        print(f"   📅 Date range: {start_date.date()} to {end_date.date()}")

        return import_id

    def import_timesheets(self, file_path, cloud_touched_ids):
        """Import timesheets - keeps ALL entries including orphaned"""
        print(f"\n⏱️  STEP 3: Importing timesheets from: {file_path}")

        # Load CSV
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        print(f"   Loaded {len(df):,} rows")

        # Find columns
        date_col = [c for c in df.columns if 'Date' in c][0]
        crm_col = [c for c in df.columns if 'Crm' in c or 'CRM' in c][0]

        # Parse DD/MM/YYYY format
        df[date_col] = pd.to_datetime(df[date_col], format='%d/%m/%Y', errors='coerce')
        df = df.dropna(subset=[date_col])

        # HARD CUTOFF: July 1+ only
        df_filtered = df[df[date_col] >= CUTOFF_DATE].copy()
        print(f"   ✅ Filtered to {len(df_filtered):,} rows (July 1+ only)")

        # Identify orphaned entries (no matching ticket)
        orphaned = ~df_filtered[crm_col].isin(cloud_touched_ids)
        orphaned_count = orphaned.sum()
        print(f"   ⚠️  Found {orphaned_count:,} orphaned timesheet entries ({orphaned_count/len(df_filtered)*100:.1f}%)")
        print(f"   ✅ Keeping ALL entries (orphaned = data quality issue to analyze separately)")

        # Import ALL timesheets
        df_filtered.to_sql('timesheets', self.conn, if_exists='replace', index=False)

        # Record metadata
        start_date = df_filtered[date_col].min()
        end_date = df_filtered[date_col].max()
        import_id = self.record_import(
            'timesheets',
            Path(file_path).name,
            len(df_filtered),
            start_date,
            end_date,
            f'July 1+ only, {orphaned_count} orphaned entries for separate analysis'
        )

        print(f"   ✅ Imported as import_id={import_id}")
        print(f"   📅 Date range: {start_date.date()} to {end_date.date()}")

        return import_id

    def full_import(self, comments_path, tickets_path, timesheets_path):
        """Complete import workflow with Cloud-touched logic"""
        print("\n" + "="*80)
        print("SERVICEDESK DATA IMPORT - Cloud-Touched Logic")
        print("="*80)

        # Step 1: Import comments (identifies Cloud-touched tickets)
        comments_id, cloud_touched_ids = self.import_comments(comments_path)

        # Step 2: Import tickets for Cloud-touched IDs only
        tickets_id = self.import_tickets(tickets_path, cloud_touched_ids)

        # Step 3: Import timesheets (all entries, flag orphaned)
        timesheets_id = self.import_timesheets(timesheets_path, cloud_touched_ids)

        print("\n" + "="*80)
        print("✅ IMPORT COMPLETE")
        print("="*80)
        print(f"   Comments import_id: {comments_id}")
        print(f"   Tickets import_id: {tickets_id}")
        print(f"   Timesheets import_id: {timesheets_id}")
        print(f"   Cloud-touched tickets: {len(cloud_touched_ids):,}")
        print("\nRun 'python3 incremental_import_servicedesk.py history' to see full metadata")

    def show_import_history(self):
        """Display import history"""
        query = "SELECT * FROM import_metadata ORDER BY import_id DESC"
        df = pd.read_sql_query(query, self.conn)
        print("\n📊 Import History:")
        print(df.to_string(index=False))

    def close(self):
        self.conn.close()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 incremental_import_servicedesk.py <command>")
        print("\nCommands:")
        print("  history              - Show import history")
        print("  import <c> <t> <ts>  - Full import (comments, tickets, timesheets paths)")
        sys.exit(1)

    importer = ServiceDeskImporter()

    if sys.argv[1] == 'history':
        importer.show_import_history()
    elif sys.argv[1] == 'import' and len(sys.argv) == 5:
        importer.full_import(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        print("Invalid command. Use 'history' or 'import <comments> <tickets> <timesheets>'")

    importer.close()
