#!/usr/bin/env python3
"""
Direct MCP Queue Processor
==========================

Processes the MCP queue by directly calling MCP functions.
This script runs in the same environment as Claude Code with MCP access.
"""

import json
import os
from pathlib import Path
from datetime import datetime
import sys

def process_mcp_queue_directly():
    """Process MCP queue by calling MCP functions directly"""
    
    project_root = Path(__file__).parent.parent.parent
    mcp_queue_dir = project_root / "claude/data/mcp_queue"
    
    if not mcp_queue_dir.exists():
        print("📁 No MCP queue directory found")
        return True
    
    # Find all JSON request files
    json_files = list(mcp_queue_dir.glob("*.json"))
    
    if not json_files:
        print("✅ No pending MCP requests in queue")
        return True
    
    print(f"📋 Found {len(json_files)} pending email(s) to send")
    
    # Import MCP functions (this will work when running in Claude Code environment)
    try:
        # This import will work when running in Claude Code with MCP
        from claude.mcp import mcp__zapier__gmail_send_email
        mcp_available = True
        print("🤖 MCP functions available - processing directly")
    except ImportError:
        # Fallback to external call
        mcp_available = False
        print("⚠️ MCP functions not available in this environment")
        return False
    
    success_count = 0
    
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                request = json.load(f)
            
            print(f"📧 Sending: {request['parameters']['subject']}")
            
            if mcp_available:
                # Call MCP function directly
                result = mcp__zapier__gmail_send_email(
                    instructions=request['parameters']['instructions'],
                    to=request['parameters']['to'],
                    subject=request['parameters']['subject'],
                    body=request['parameters']['body'],
                    body_type=request['parameters']['body_type']
                )
                
                if result and 'results' in result:
                    print(f"✅ Sent successfully: {request['parameters']['subject']}")
                    
                    # Move to processed folder
                    processed_dir = mcp_queue_dir / "processed"
                    processed_dir.mkdir(exist_ok=True)
                    processed_file = processed_dir / f"{json_file.stem}_direct_mcp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    json_file.rename(processed_file)
                    
                    success_count += 1
                else:
                    print(f"❌ MCP call failed: {json_file.name}")
            
        except Exception as e:
            print(f"❌ Error processing {json_file.name}: {e}")
    
    print(f"📊 Successfully sent {success_count}/{len(json_files)} emails")
    return success_count == len(json_files)

if __name__ == "__main__":
    success = process_mcp_queue_directly()
    sys.exit(0 if success else 1)