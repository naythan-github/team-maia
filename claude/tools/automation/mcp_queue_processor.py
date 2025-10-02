#!/usr/bin/env python3
"""
MCP Queue Processor - Manual Processing Helper
==============================================

Processes queued MCP requests and provides easy copy-paste commands for Claude Code.
"""

import json
from pathlib import Path
from datetime import datetime
import sys

def process_mcp_queue():
    """Process all queued MCP requests and provide instructions"""
    
    project_root = Path(__file__).parent.parent.parent
    mcp_queue_dir = project_root / "claude/data/mcp_queue"
    
    if not mcp_queue_dir.exists():
        print("📁 No MCP queue directory found")
        return
    
    # Find all JSON request files
    json_files = list(mcp_queue_dir.glob("*.json"))
    
    if not json_files:
        print("✅ No pending MCP requests in queue")
        return
    
    print(f"📋 Found {len(json_files)} pending MCP request(s)")
    print("=" * 50)
    
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                request = json.load(f)
            
            print(f"\n📧 **MCP Request**: {json_file.name}")
            print(f"⏰ **Created**: {request['timestamp']}")
            print(f"📨 **To**: {request['parameters']['to']}")
            print(f"📝 **Subject**: {request['parameters']['subject']}")
            print(f"📏 **Content Length**: {request['metadata']['content_length']} chars")
            
            # Create the MCP command
            print(f"\n🤖 **Claude Code Command to Execute:**")
            print("```")
            print(f"Use mcp__zapier__gmail_send_email with:")
            print(f"- instructions: {request['parameters']['instructions']}")
            print(f"- to: {request['parameters']['to']}")
            print(f"- subject: {request['parameters']['subject']}")
            print(f"- body_type: {request['parameters']['body_type']}")
            print(f"- body: (copy HTML content below)")
            print("```")
            
            # Show HTML content for copy-paste (truncated for display)
            html_content = request['parameters']['body']
            if len(html_content) > 500:
                preview = html_content[:250] + "...[TRUNCATED]..." + html_content[-250:]
                print(f"\n📄 **HTML Content Preview**:")
                print(f"```html")
                print(preview)
                print(f"```")
                print(f"\n📋 **Full HTML Content** (copy this entire block):")
                print(f"```html")
                print(html_content)
                print(f"```")
            else:
                print(f"\n📋 **HTML Content**:")
                print(f"```html")
                print(html_content)
                print(f"```")
            
            print(f"\n🗑️  **After sending, delete**: {json_file}")
            print("=" * 50)
            
        except Exception as e:
            print(f"❌ Error processing {json_file.name}: {e}")
    
    print(f"\n✅ **Instructions**:")
    print("1. Copy the MCP command above")
    print("2. Paste into Claude Code")
    print("3. Copy the HTML content and paste as the 'body' parameter")
    print("4. Execute the MCP command")
    print("5. Delete the processed JSON file from the queue")

def clean_processed_requests():
    """Clean up old processed requests"""
    project_root = Path(__file__).parent.parent.parent
    mcp_queue_dir = project_root / "claude/data/mcp_queue"
    
    # Move to processed folder instead of deleting
    processed_dir = mcp_queue_dir / "processed"
    processed_dir.mkdir(exist_ok=True)
    
    json_files = list(mcp_queue_dir.glob("*.json"))
    
    if json_files:
        print(f"🧹 Found {len(json_files)} files to clean")
        for f in json_files:
            if f.name != "processed":  # Don't move the processed directory
                processed_file = processed_dir / f"{f.stem}_processed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                f.rename(processed_file)
                print(f"📁 Moved {f.name} → {processed_file.name}")
    else:
        print("✅ No files to clean")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "clean":
        clean_processed_requests()
    else:
        process_mcp_queue()