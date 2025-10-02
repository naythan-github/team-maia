# RAG Background Service Management

## Overview
Automated RAG document intelligence monitoring and indexing service that keeps your knowledge base current without manual intervention.

## Service Architecture

### **Smart Monitoring System**
- **Directory Change Detection**: Monitors file modifications using hash-based change detection
- **Intelligent Scheduling**: Full scans (daily) + incremental updates (hourly) optimized per source
- **Resource Optimization**: Processes during low-usage periods with configurable frequency
- **Multi-Source Support**: Handles directories, code repositories, and Confluence simultaneously

### **Default Monitored Sources**
1. **Maia Context** (`/claude/context`) - Scanned every 6 hours, incremental every 30 minutes
2. **Maia Commands** (`/claude/commands`) - Scanned every 12 hours, incremental every hour  
3. **Maia Repository** (`/git/maia`) - Documentation scanned daily, incremental every 2 hours
4. **Personal Documents** (`~/Documents`) - Scanned daily, incremental every 3 hours

### **Enterprise Features**
- **SQLite Database**: Persistent service state, scan history, and performance analytics
- **Error Handling**: Comprehensive logging and graceful failure recovery
- **Service Management**: Professional start/stop/status operations with daemon support
- **Performance Monitoring**: Scan statistics, success rates, and processing metrics

## Quick Start

### **Start Automated Service**
```bash
# Start background service (daemon mode)
python3 claude/tools/rag_background_service.py start --daemon

# Start service with console output
python3 claude/tools/rag_background_service.py start
```

### **Service Management**
```bash
# Check service status
python3 claude/tools/rag_background_service.py status

# Stop service
python3 claude/tools/rag_background_service.py stop

# Force immediate scan of all sources
python3 claude/tools/rag_background_service.py scan

# Force scan specific source
python3 claude/tools/rag_background_service.py scan --source-id maia_context
```

### **Monitor Sources**
```bash
# List all monitored sources
python3 claude/tools/rag_background_service.py sources

# Add new source
python3 claude/tools/rag_background_service.py add-source \
  --source-id my_project \
  --path /Users/naythan/git/my-project \
  --type repository
```

## Python API Usage

### **Service Control**
```python
from claude.tools.rag_background_service import RAGBackgroundService

# Initialize and start service
service = RAGBackgroundService()
service.start()

# Check status
status = service.get_status()
print(f"Documents indexed: {status.total_documents_indexed}")
print(f"Sources monitored: {status.total_sources_monitored}")
print(f"Next scan: {status.next_scheduled_scan}")

# Force immediate scan
results = service.force_scan()
for source_id, result in results.items():
    print(f"{source_id}: {result['files_indexed']} files indexed")

# Stop service
service.stop()
```

### **Add Custom Sources**
```python
from claude.tools.rag_background_service import MonitoredSource

# Add custom directory monitoring
custom_source = MonitoredSource(
    source_id="company_docs",
    source_type="directory",
    path="/Users/naythan/Company/Documentation",
    scan_frequency_hours=12,      # Full scan every 12 hours
    incremental_frequency_minutes=60  # Check for changes every hour
)

service.add_source(custom_source)
```

### **Integration with Existing RAG**
```python
# Service automatically indexes documents
# Query indexed content immediately with existing RAG system
from claude.tools.graphrag_enhanced_knowledge_graph import quick_graphrag_query

# Documents are automatically indexed by background service
answer = quick_graphrag_query("What's our latest deployment process?", "technical")
print(answer)  # Includes recently indexed documents automatically
```

## Service Configuration

### **Default Configuration** (`rag_service_config.json`)
```json
{
  "sources": [
    {
      "source_id": "maia_context",
      "source_type": "directory",
      "path": "${MAIA_ROOT}/claude/context",
      "enabled": true,
      "scan_frequency_hours": 6,
      "incremental_frequency_minutes": 30
    },
    {
      "source_id": "maia_repository", 
      "source_type": "repository",
      "path": "${MAIA_ROOT}",
      "enabled": true,
      "scan_frequency_hours": 24,
      "incremental_frequency_minutes": 120
    }
  ]
}
```

### **Advanced Configuration Options**
- **scan_frequency_hours**: How often to perform full document scans
- **incremental_frequency_minutes**: How often to check for file changes
- **enabled**: Enable/disable monitoring for specific sources
- **Custom paths**: Add any directory, repository, or Confluence space

## Integration Patterns

### **Morning Briefing Enhancement**
```python
# Background service ensures briefings include latest indexed documents
from claude.tools.automated_morning_briefing import generate_personalized_briefing

# Briefing automatically includes insights from recently indexed documents
briefing = generate_personalized_briefing(include_indexed_context=True)
```

### **Agent Integration**
```python
# All specialized agents benefit from automatically updated knowledge base
from claude.agents.company_research_agent import quick_company_research

# Research enhanced by automatically indexed company documentation
research = quick_company_research("Orro Group", use_indexed_docs=True)
```

### **Dashboard Integration**
```python
# Add RAG service monitoring to AI Business Intelligence Dashboard
from claude.tools.rag_background_service import RAGBackgroundService

service = RAGBackgroundService()
status = service.get_status()

dashboard_data = {
    'rag_service_status': 'active' if status.is_running else 'inactive',
    'documents_indexed': status.total_documents_indexed,
    'sources_monitored': status.total_sources_monitored,
    'next_scan': status.next_scheduled_scan.isoformat() if status.next_scheduled_scan else None
}
```

## Performance and Monitoring

### **Service Statistics**
- **Scan History**: Complete record of all indexing operations with success/failure tracking
- **Performance Metrics**: Processing time, files indexed, error rates per source
- **Change Detection**: Intelligent monitoring avoids unnecessary processing
- **Resource Optimization**: Scheduled during low-usage periods

### **Log Monitoring**
```bash
# Monitor service logs in real-time
tail -f ~/Library/Application\ Support/Maia/backups/logs/rag_service.log

# View recent service activity
grep "RAG Service" ~/Library/Application\ Support/Maia/backups/logs/rag_service.log | tail -20
```

### **Database Inspection**
```sql
-- View scan history
SELECT source_id, scan_type, start_time, files_indexed, success 
FROM scan_history 
ORDER BY start_time DESC LIMIT 10;

-- View source status
SELECT source_id, last_scan, file_count, enabled 
FROM monitored_sources;

-- Performance statistics
SELECT stat_date, total_scans, total_files_indexed, avg_scan_time_seconds 
FROM service_stats 
ORDER BY stat_date DESC LIMIT 7;
```

## Production Deployment

### **System Service Setup** (Optional)
Create macOS LaunchAgent for automatic startup:

```xml
<!-- ~/Library/LaunchAgents/com.maia.rag-service.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.maia.rag-service</string>
    <key>ProgramArguments</key>
    <array>
        <string>/opt/homebrew/bin/python3</string>
        <string>${MAIA_ROOT}/claude/tools/rag_background_service.py</string>
        <string>start</string>
        <string>--daemon</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/naythan/Library/Application Support/Maia/backups/logs/rag_service.out</string>
    <key>StandardErrorPath</key>
    <string>/Users/naythan/Library/Application Support/Maia/backups/logs/rag_service.err</string>
</dict>
</plist>
```

Load system service:
```bash
launchctl load ~/Library/LaunchAgents/com.maia.rag-service.plist
launchctl start com.maia.rag-service
```

### **Health Monitoring**
```bash
# Check if service is running
launchctl list | grep maia.rag-service

# View service status
python3 claude/tools/rag_background_service.py status
```

## Troubleshooting

### **Common Issues**

1. **Service won't start**
   - Check Python path and dependencies
   - Verify database permissions
   - Review error logs for specific issues

2. **Sources not being scanned**
   - Verify paths exist and are accessible
   - Check source enabled status
   - Review scan frequency settings

3. **Performance issues**
   - Adjust scan frequencies for large directories
   - Monitor system resources during scans
   - Consider excluding large binary files

### **Debug Commands**
```bash
# Verbose service status
python3 claude/tools/rag_background_service.py status

# Test single source scan
python3 claude/tools/rag_background_service.py scan --source-id maia_context

# Check RAG system status
python3 -c "
from claude.tools.graphrag_enhanced_knowledge_graph import get_graphrag_knowledge_graph
kg = get_graphrag_knowledge_graph()
stats = kg.get_stats()
print(f'Total documents: {stats[\"total_documents\"]}')
print(f'Document chunks: {stats[\"total_document_chunks\"]}')
"
```

### **Reset Service State**
```bash
# Stop service
python3 claude/tools/rag_background_service.py stop

# Remove service database (will recreate with defaults)
rm ~/Library/Application\ Support/Maia/backups/databases/rag_service.db

# Remove configuration (will recreate with defaults)  
rm ~/Library/Application\ Support/Maia/backups/rag_service_config.json

# Restart service
python3 claude/tools/rag_background_service.py start
```

## Enterprise Value

### **Engineering Manager Demonstration**
- **Production Architecture**: Showcases enterprise-grade service design with automated operations
- **Zero-Touch Intelligence**: Demonstrates sophisticated automation thinking beyond manual processes
- **Professional Portfolio**: Self-managing knowledge intelligence platform for organizational efficiency

### **Technical Leadership**
- **Advanced Monitoring**: Smart change detection and resource optimization
- **Service Management**: Professional daemon architecture with comprehensive logging
- **Integration Capability**: Seamless enhancement of existing automation workflows

### **Business Impact**
- **Always-Current Knowledge**: Information discovery reduced from hours to seconds
- **Productivity Enhancement**: Zero cognitive load for knowledge base maintenance
- **Strategic Intelligence**: Automated inclusion of latest documents in decision-making processes

This automated RAG background service transforms document intelligence from manual task to intelligent, self-managing infrastructure suitable for enterprise environments.