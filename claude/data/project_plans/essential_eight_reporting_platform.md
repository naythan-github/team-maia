# Essential Eight Monthly Reporting Platform - Project Plan

**Project ID**: essential8-reporting-platform
**Timeline**: 6 weeks (MVP)
**Budget**: $60K development
**Operating Cost**: $15/month (50 customers)
**Architecture**: Azure-native, serverless, monthly batch processing

---

## Executive Summary

Build automated monthly Essential Eight Strategy 1 (Application Control) compliance reporting platform using Azure Functions + Azure SQL Serverless. Collects data from Airlock Digital API, Microsoft Intune, and Windows Event Logs once per month, generates PDF/Excel reports, delivers via email.

**Key Constraint**: Monthly reporting only (NOT real-time monitoring, NOT a SIEM)

---

## Phase 1: MVP - Single Customer (Week 1-2)

### Deliverables
- ✅ Azure environment provisioned
- ✅ Single customer data collection (Airlock API only)
- ✅ Azure Table Storage with monthly metrics
- ✅ Manual PDF report generation (local Python script)

### Tasks

#### Week 1: Azure Environment Setup
**Day 1-2: Provision Azure Resources**
```bash
# Azure CLI commands (exact specifications)

# 1. Create Resource Group
az group create \
  --name rg-essential8-reporting-dev \
  --location australiaeast

# 2. Create Storage Account
az storage account create \
  --name st8reportingdev \
  --resource-group rg-essential8-reporting-dev \
  --location australiaeast \
  --sku Standard_LRS \
  --kind StorageV2

# 3. Create Function App (Consumption Plan)
az functionapp create \
  --name func-essential8-reporting-dev \
  --resource-group rg-essential8-reporting-dev \
  --storage-account st8reportingdev \
  --consumption-plan-location australiaeast \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --os-type Linux

# 4. Create Key Vault
az keyvault create \
  --name kv-e8-reporting-dev \
  --resource-group rg-essential8-reporting-dev \
  --location australiaeast \
  --enable-rbac-authorization false

# 5. Add secrets (Airlock API key example)
az keyvault secret set \
  --vault-name kv-e8-reporting-dev \
  --name airlock-api-key \
  --value "YOUR_API_KEY_HERE"
```

**Day 3-4: Local Development Setup**
```bash
# Create project structure
mkdir -p ~/work_projects/essential8-reporting-platform
cd ~/work_projects/essential8-reporting-platform

# Project structure
essential8-reporting-platform/
├── functions/
│   ├── data_collection/
│   │   ├── __init__.py
│   │   ├── function.json
│   │   └── airlock_collector.py
│   └── report_generation/
│       ├── __init__.py
│       ├── function.json
│       └── report_generator.py
├── shared/
│   ├── __init__.py
│   ├── azure_storage.py
│   ├── config.py
│   └── models.py
├── templates/
│   └── monthly_report.html
├── tests/
│   ├── test_airlock_collector.py
│   └── test_report_generator.py
├── requirements.txt
├── host.json
├── local.settings.json
└── README.md

# Initialize Python environment
python3 -m venv venv
source venv/bin/activate
pip install azure-functions azure-data-tables azure-identity \
    requests python-dateutil jinja2 weasyprint openpyxl pytest
```

**Day 5: Data Model Design**
```python
# shared/models.py
from dataclasses import dataclass
from datetime import date
from typing import Dict, List

@dataclass
class MonthlyMetrics:
    """Monthly Essential Eight Strategy 1 metrics"""
    customer_id: str
    report_month: date  # First day of month (2024-12-01)

    # Coverage metrics
    endpoints_total: int
    endpoints_protected: int
    coverage_pct: float

    # Threat prevention
    blocks_total: int
    blocks_by_location: Dict[str, int]  # {"%TEMP%": 67, "Downloads": 38, ...}
    blocks_by_risk: Dict[str, int]  # {"critical": 0, "high": 12, ...}

    # False positives
    false_positives_count: int
    false_positives_avg_resolution_hours: float

    # Exceptions
    exception_requests_count: int
    exception_approval_rate_pct: float

    # Ruleset health
    ruleset_publisher_pct: float
    ruleset_path_pct: float
    ruleset_hash_pct: float
    ruleset_last_update_days: int

    # Compliance
    maturity_level: str  # "ML1", "ML2", "ML3"

    def to_dict(self) -> dict:
        """Convert to Azure Table Storage entity"""
        return {
            'PartitionKey': self.customer_id,
            'RowKey': self.report_month.strftime('%Y-%m'),
            'endpoints_total': self.endpoints_total,
            'endpoints_protected': self.endpoints_protected,
            'coverage_pct': self.coverage_pct,
            'blocks_total': self.blocks_total,
            'blocks_by_location': str(self.blocks_by_location),  # JSON string
            'false_positives_count': self.false_positives_count,
            # ... all other fields
        }
```

#### Week 2: Data Collection Implementation

**Day 1-2: Airlock API Integration**
```python
# functions/data_collection/airlock_collector.py
import os
from datetime import datetime, timedelta
import requests
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from shared.models import MonthlyMetrics

class AirlockCollector:
    """Collect monthly stats from Airlock Digital API"""

    def __init__(self, customer_id: str):
        self.customer_id = customer_id
        self.api_base = os.environ['AIRLOCK_API_BASE']
        self.api_key = self._get_api_key()

    def _get_api_key(self) -> str:
        """Fetch API key from Azure Key Vault"""
        credential = DefaultAzureCredential()
        vault_url = os.environ['KEY_VAULT_URL']
        client = SecretClient(vault_url=vault_url, credential=credential)
        secret = client.get_secret(f"airlock-api-key-{self.customer_id}")
        return secret.value

    def collect_monthly_stats(self, year: int, month: int) -> MonthlyMetrics:
        """
        Collect metrics for specified month from Airlock API

        Args:
            year: 2024
            month: 12 (December)

        Returns:
            MonthlyMetrics object with all collected data
        """
        # Calculate date range (first day to last day of month)
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(days=1)

        # Query Airlock API for monthly stats
        response = requests.get(
            f"{self.api_base}/api/v1/statistics/monthly",
            params={
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d')
            },
            headers={
                'Authorization': f'Bearer {self.api_key}',
                'Accept': 'application/json'
            },
            timeout=30
        )
        response.raise_for_status()
        data = response.json()

        # Parse response into MonthlyMetrics
        return MonthlyMetrics(
            customer_id=self.customer_id,
            report_month=start_date.date(),
            endpoints_total=data['endpoints']['total'],
            endpoints_protected=data['endpoints']['protected'],
            coverage_pct=data['endpoints']['coverage_percentage'],
            blocks_total=data['blocks']['total'],
            blocks_by_location=data['blocks']['by_location'],
            blocks_by_risk=data['blocks']['by_risk_level'],
            false_positives_count=data['false_positives']['count'],
            false_positives_avg_resolution_hours=data['false_positives']['avg_resolution_hours'],
            exception_requests_count=data['exceptions']['total_requests'],
            exception_approval_rate_pct=data['exceptions']['approval_rate'],
            ruleset_publisher_pct=data['ruleset']['publisher_percentage'],
            ruleset_path_pct=data['ruleset']['path_percentage'],
            ruleset_hash_pct=data['ruleset']['hash_percentage'],
            ruleset_last_update_days=data['ruleset']['days_since_update'],
            maturity_level=data['compliance']['maturity_level']
        )

# Azure Function entry point
def main(mytimer) -> None:
    """Triggered on 1st of month at 2:00 AM"""
    import logging
    from shared.azure_storage import save_monthly_metrics

    logging.info('Starting monthly data collection...')

    # Get customer list (hardcoded for MVP, later from config)
    customers = ['customer_abc']  # MVP: single customer

    for customer_id in customers:
        try:
            collector = AirlockCollector(customer_id)

            # Collect last month's data
            now = datetime.now()
            last_month = (now.replace(day=1) - timedelta(days=1))

            metrics = collector.collect_monthly_stats(
                year=last_month.year,
                month=last_month.month
            )

            # Save to Azure Table Storage
            save_monthly_metrics(metrics)

            logging.info(f'✅ Collected metrics for {customer_id}')

        except Exception as e:
            logging.error(f'❌ Failed for {customer_id}: {e}')
            # Continue to next customer (don't fail entire batch)
```

**Day 3: Azure Table Storage Integration**
```python
# shared/azure_storage.py
from azure.data.tables import TableServiceClient
from azure.identity import DefaultAzureCredential
from shared.models import MonthlyMetrics

class MetricsStorage:
    """Azure Table Storage for monthly metrics"""

    def __init__(self):
        connection_string = os.environ['AZURE_STORAGE_CONNECTION_STRING']
        self.table_service = TableServiceClient.from_connection_string(connection_string)
        self.table_name = 'monthlymetrics'

        # Create table if not exists
        self.table_client = self.table_service.create_table_if_not_exists(self.table_name)

    def save_metrics(self, metrics: MonthlyMetrics) -> None:
        """Save monthly metrics to Table Storage"""
        entity = metrics.to_dict()
        self.table_client.upsert_entity(entity)

    def get_metrics(self, customer_id: str, months: int = 3) -> list:
        """
        Retrieve last N months of metrics for customer

        Args:
            customer_id: Customer identifier
            months: Number of months to retrieve (default 3 for trend analysis)

        Returns:
            List of MonthlyMetrics objects, newest first
        """
        entities = self.table_client.query_entities(
            query_filter=f"PartitionKey eq '{customer_id}'",
            select=['*']
        )

        # Convert entities to MonthlyMetrics objects
        results = []
        for entity in entities:
            # Parse entity back to MonthlyMetrics
            # (implementation details...)
            results.append(entity)

        # Sort by date descending, limit to N months
        results.sort(key=lambda x: x['RowKey'], reverse=True)
        return results[:months]

# Helper function for Azure Function
def save_monthly_metrics(metrics: MonthlyMetrics):
    storage = MetricsStorage()
    storage.save_metrics(metrics)
```

**Day 4-5: Manual Report Generation (Local Script)**
```python
# scripts/generate_report_local.py
"""
MVP: Manual report generation script (runs locally)
Later: Convert to Azure Function for automation
"""
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
import weasyprint
from shared.azure_storage import MetricsStorage

def generate_monthly_report(customer_id: str, year: int, month: int):
    """Generate PDF report for customer"""

    # 1. Fetch data from Azure Table Storage
    storage = MetricsStorage()
    metrics_history = storage.get_metrics(customer_id, months=3)

    current_month = metrics_history[0]
    prior_months = metrics_history[1:3] if len(metrics_history) > 1 else []

    # 2. Calculate trends
    trends = calculate_trends(current_month, prior_months)

    # 3. Render HTML from template
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('monthly_report.html')

    html_content = template.render(
        customer_id=customer_id,
        report_month=f"{year}-{month:02d}",
        metrics=current_month,
        prior_months=prior_months,
        trends=trends,
        generated_date=datetime.now().strftime('%Y-%m-%d %H:%M')
    )

    # 4. Generate PDF
    pdf_filename = f"reports/{customer_id}_{year}-{month:02d}_report.pdf"
    weasyprint.HTML(string=html_content).write_pdf(pdf_filename)

    print(f"✅ Report generated: {pdf_filename}")
    return pdf_filename

def calculate_trends(current, prior_months):
    """Calculate month-over-month trends"""
    if not prior_months:
        return {'status': 'No historical data'}

    last_month = prior_months[0]

    return {
        'coverage_change': current['coverage_pct'] - last_month['coverage_pct'],
        'blocks_change_pct': ((current['blocks_total'] - last_month['blocks_total'])
                               / last_month['blocks_total'] * 100),
        'fp_change': current['false_positives_count'] - last_month['false_positives_count']
    }

if __name__ == '__main__':
    # MVP: Run manually for testing
    generate_monthly_report('customer_abc', 2024, 12)
```

---

## Phase 2: Automation + Additional Sources (Week 3-4)

### Deliverables
- ✅ Intune Graph API integration
- ✅ Windows Event Log collection
- ✅ Automated report generation (Azure Function)
- ✅ Email delivery (SendGrid)

### Tasks

#### Week 3: Additional Data Sources

**Day 1-2: Microsoft Intune Graph API**
```python
# functions/data_collection/intune_collector.py
import requests
from msal import ConfidentialClientApplication

class IntuneCollector:
    """Collect device compliance from Microsoft Intune"""

    def __init__(self, customer_tenant_id: str):
        self.tenant_id = customer_tenant_id
        self.client_id = os.environ['GRAPH_API_CLIENT_ID']
        self.client_secret = self._get_client_secret()
        self.token = self._get_access_token()

    def _get_access_token(self) -> str:
        """Authenticate with Microsoft Graph API"""
        authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        app = ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=authority
        )

        result = app.acquire_token_for_client(
            scopes=["https://graph.microsoft.com/.default"]
        )
        return result['access_token']

    def get_device_compliance(self) -> dict:
        """Query Intune for device compliance status"""
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }

        # Get all managed devices
        response = requests.get(
            'https://graph.microsoft.com/v1.0/deviceManagement/managedDevices',
            params={'$select': 'id,deviceName,complianceState,operatingSystem'},
            headers=headers
        )
        devices = response.json()['value']

        total = len(devices)
        compliant = sum(1 for d in devices if d['complianceState'] == 'compliant')

        return {
            'total_devices': total,
            'compliant_devices': compliant,
            'coverage_percentage': (compliant / total * 100) if total > 0 else 0
        }
```

**Day 3-4: Windows Event Log Collection**
```python
# functions/data_collection/windows_events_collector.py
import subprocess
import json
from datetime import datetime, timedelta

class WindowsEventsCollector:
    """Collect AppLocker block events from Windows Event Logs"""

    def __init__(self, event_collector_server: str):
        self.server = event_collector_server

    def collect_applocker_blocks(self, start_date: datetime, end_date: datetime) -> list:
        """
        Query Windows Event Collector via PowerShell Remoting

        Returns: List of blocked execution attempts
        """
        # PowerShell script to query remote Event Collector
        ps_script = f"""
        $startDate = [datetime]::Parse('{start_date.isoformat()}')
        $endDate = [datetime]::Parse('{end_date.isoformat()}')

        Get-WinEvent -ComputerName {self.server} -FilterHashtable @{{
            LogName='Microsoft-Windows-AppLocker/EXE and DLL'
            ID=8003,8004
            StartTime=$startDate
            EndTime=$endDate
        }} | Select-Object TimeCreated, MachineName, Message | ConvertTo-Json
        """

        # Execute via PowerShell (requires WinRM configured)
        result = subprocess.run(
            ['pwsh', '-Command', ps_script],
            capture_output=True,
            text=True,
            timeout=300
        )

        events = json.loads(result.stdout)

        # Parse events into structured data
        blocks = []
        for event in events:
            blocks.append({
                'timestamp': event['TimeCreated'],
                'endpoint': event['MachineName'],
                'blocked_file': self._parse_blocked_file(event['Message']),
                'location': self._parse_location(event['Message']),
                'risk_level': self._assess_risk(event['Message'])
            })

        return blocks

    def _parse_blocked_file(self, message: str) -> str:
        """Extract file path from event message"""
        # Example: "\\Device\\HarddiskVolume2\\Users\\user\\Downloads\\malware.exe was prevented from running"
        import re
        match = re.search(r'([A-Z]:\\.*?\.exe)', message)
        return match.group(1) if match else 'Unknown'

    def _parse_location(self, message: str) -> str:
        """Categorize block location"""
        if '%TEMP%' in message or '\\Temp\\' in message:
            return '%TEMP%'
        elif '\\Downloads\\' in message:
            return 'Downloads'
        elif '\\AppData\\Local\\' in message:
            return 'AppData\\Local'
        else:
            return 'Other'

    def _assess_risk(self, message: str) -> str:
        """Assess risk level based on patterns"""
        # Simple heuristic (enhance with threat intelligence)
        high_risk_patterns = ['powershell', 'cmd', 'wscript', 'cscript']
        if any(pattern in message.lower() for pattern in high_risk_patterns):
            return 'high'
        return 'medium'
```

#### Week 4: Automated Report Generation

**Day 1-2: Azure Function for Report Generation**
```python
# functions/report_generation/__init__.py
import azure.functions as func
from datetime import datetime, timedelta
from jinja2 import Environment, FileSystemLoader
import weasyprint
from openpyxl import Workbook
from shared.azure_storage import MetricsStorage
from azure.storage.blob import BlobServiceClient

def main(mytimer: func.TimerRequest) -> None:
    """
    Triggered on 2nd of month at 8:00 AM
    Generates reports for all customers
    """
    import logging
    logging.info('Starting monthly report generation...')

    customers = get_customer_list()

    for customer_id in customers:
        try:
            # Generate report
            pdf_bytes, excel_bytes = generate_report(customer_id)

            # Upload to Blob Storage
            upload_report(customer_id, pdf_bytes, excel_bytes)

            # Send email
            send_email_notification(customer_id, pdf_bytes, excel_bytes)

            logging.info(f'✅ Report generated for {customer_id}')

        except Exception as e:
            logging.error(f'❌ Failed for {customer_id}: {e}')

def generate_report(customer_id: str) -> tuple:
    """Generate PDF and Excel reports"""
    # Fetch data
    storage = MetricsStorage()
    metrics_history = storage.get_metrics(customer_id, months=3)

    # Render HTML template
    env = Environment(loader=FileSystemLoader('/home/site/wwwroot/templates'))
    template = env.get_template('monthly_report.html')
    html = template.render(
        customer_id=customer_id,
        current=metrics_history[0],
        prior=metrics_history[1:],
        trends=calculate_trends(metrics_history)
    )

    # Generate PDF
    pdf_bytes = weasyprint.HTML(string=html).write_pdf()

    # Generate Excel
    excel_bytes = generate_excel(metrics_history)

    return pdf_bytes, excel_bytes

def upload_report(customer_id: str, pdf: bytes, excel: bytes):
    """Upload reports to Azure Blob Storage"""
    connection_string = os.environ['AZURE_STORAGE_CONNECTION_STRING']
    blob_service = BlobServiceClient.from_connection_string(connection_string)

    # Create container if not exists
    container_name = 'reports'
    container_client = blob_service.get_container_client(container_name)

    report_month = (datetime.now().replace(day=1) - timedelta(days=1)).strftime('%Y-%m')

    # Upload PDF
    blob_client = container_client.get_blob_client(
        f"{customer_id}/{report_month}-report.pdf"
    )
    blob_client.upload_blob(pdf, overwrite=True)

    # Upload Excel
    blob_client = container_client.get_blob_client(
        f"{customer_id}/{report_month}-report.xlsx"
    )
    blob_client.upload_blob(excel, overwrite=True)
```

**Day 3-4: Email Delivery Integration**
```python
# shared/email_sender.py
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment
import base64

def send_report_email(customer_email: str, pdf_bytes: bytes, excel_bytes: bytes):
    """Send monthly report via SendGrid"""

    message = Mail(
        from_email='reports@your-company.com',
        to_emails=customer_email,
        subject=f'Essential Eight Monthly Report - {datetime.now().strftime("%B %Y")}',
        html_content='''
        <h2>Essential Eight Compliance Report</h2>
        <p>Your monthly Application Control (Strategy 1) compliance report is attached.</p>
        <p>This report covers the period: {report_month}</p>
        <p>Best regards,<br>Compliance Team</p>
        '''
    )

    # Attach PDF
    pdf_attachment = Attachment(
        file_content=base64.b64encode(pdf_bytes).decode(),
        file_name=f'essential8-report-{datetime.now().strftime("%Y-%m")}.pdf',
        file_type='application/pdf',
        disposition='attachment'
    )
    message.add_attachment(pdf_attachment)

    # Attach Excel
    excel_attachment = Attachment(
        file_content=base64.b64encode(excel_bytes).decode(),
        file_name=f'essential8-metrics-{datetime.now().strftime("%Y-%m")}.xlsx',
        file_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        disposition='attachment'
    )
    message.add_attachment(excel_attachment)

    # Send via SendGrid
    sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
    response = sg.send(message)

    return response.status_code
```

---

## Phase 3: Multi-Tenant + Production (Week 5-6)

### Deliverables
- ✅ Customer configuration management
- ✅ Multi-tenant data isolation
- ✅ Production deployment
- ✅ Monitoring & alerting
- ✅ 5 pilot customers onboarded

### Week 5: Multi-Tenant Configuration

**Customer Configuration Schema**
```json
// customers/customer_abc.json
{
    "customer_id": "customer_abc",
    "customer_name": "ABC Corporation",
    "contact_email": "compliance@abc.com",
    "azure_tenant_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "data_sources": {
        "airlock": {
            "enabled": true,
            "api_endpoint": "https://airlock.abc.com/api",
            "api_key_vault_secret": "airlock-api-key-customer-abc"
        },
        "intune": {
            "enabled": true,
            "tenant_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
        },
        "windows_events": {
            "enabled": true,
            "event_collector_server": "wec01.abc.local",
            "authentication": "kerberos"
        }
    },
    "report_settings": {
        "maturity_level_target": "ML2",
        "custom_branding": false,
        "delivery_method": "email"
    }
}
```

### Week 6: Production Deployment

**Production Environment**
```bash
# Production resource group
az group create \
  --name rg-essential8-reporting-prod \
  --location australiaeast

# Deploy Function App to production
func azure functionapp publish func-essential8-reporting-prod

# Configure monitoring
az monitor log-analytics workspace create \
  --resource-group rg-essential8-reporting-prod \
  --workspace-name law-essential8-reporting

# Create alert rules
az monitor metrics alert create \
  --name "Function Execution Failures" \
  --resource-group rg-essential8-reporting-prod \
  --scopes /subscriptions/{sub-id}/resourceGroups/rg-essential8-reporting-prod/providers/Microsoft.Web/sites/func-essential8-reporting-prod \
  --condition "count FunctionExecutionCount > 0 where ResultCode != 200" \
  --window-size 1h \
  --evaluation-frequency 5m \
  --action email your-email@company.com
```

---

## Testing Strategy

### Unit Tests
```python
# tests/test_airlock_collector.py
import pytest
from unittest.mock import Mock, patch
from functions.data_collection.airlock_collector import AirlockCollector

def test_collect_monthly_stats():
    """Test Airlock API data collection"""
    collector = AirlockCollector('test_customer')

    with patch('requests.get') as mock_get:
        # Mock API response
        mock_get.return_value.json.return_value = {
            'endpoints': {'total': 100, 'protected': 95, 'coverage_percentage': 95.0},
            'blocks': {'total': 127, 'by_location': {'%TEMP%': 67, 'Downloads': 38}},
            # ... mock data
        }

        metrics = collector.collect_monthly_stats(2024, 12)

        assert metrics.customer_id == 'test_customer'
        assert metrics.endpoints_total == 100
        assert metrics.coverage_pct == 95.0
```

### Integration Tests
```python
# tests/test_end_to_end.py
def test_full_workflow():
    """Test complete monthly workflow"""
    # 1. Collect data
    # 2. Store in Table Storage
    # 3. Generate report
    # 4. Validate PDF output
    pass
```

---

## Success Metrics

**Week 2 MVP Success Criteria**:
- ✅ Single customer data collected from Airlock API
- ✅ Data stored in Azure Table Storage
- ✅ PDF report generated manually (matches template format)

**Week 4 Automation Success Criteria**:
- ✅ Automated collection from 3 data sources (Airlock, Intune, Events)
- ✅ Azure Functions running on schedule
- ✅ Email delivery working

**Week 6 Production Success Criteria**:
- ✅ 5 pilot customers onboarded
- ✅ 100% successful report generation
- ✅ <5% data collection errors
- ✅ Production monitoring active

---

## Risk Mitigation

**Risk 1**: Airlock API authentication fails
- **Mitigation**: Test API integration in Week 1, validate credentials upfront

**Risk 2**: Windows Event Log access denied
- **Mitigation**: Configure WinRM access Week 3 Day 1, fallback to manual CSV upload

**Risk 3**: PDF generation fails on Azure Functions
- **Mitigation**: Test WeasyPrint deployment Week 4 Day 1, fallback to ReportLab

**Risk 4**: Azure costs exceed budget
- **Mitigation**: Set cost alerts ($50/month threshold), use serverless auto-pause

---

## Next Immediate Steps (This Week)

**Day 1 (Today)**:
1. Provision Azure resources (Resource Group, Function App, Storage, Key Vault)
2. Create project structure locally
3. Initialize Git repository

**Day 2-3**:
1. Implement Airlock API collector (single customer)
2. Test API authentication and data retrieval
3. Store first month's data in Azure Table Storage

**Day 4-5**:
1. Create HTML report template
2. Generate first PDF report (manual script)
3. Validate output matches template format

**End of Week 1 Checkpoint**:
- Demo: Show PDF report for single customer
- Decision: Proceed to Week 2 (automation) or iterate on Week 1

---

## Budget Tracking

| Phase | Budget | Actual | Status |
|-------|--------|--------|--------|
| Week 1-2 (MVP) | $20K | TBD | In Progress |
| Week 3-4 (Automation) | $20K | TBD | Not Started |
| Week 5-6 (Production) | $20K | TBD | Not Started |
| **Total** | **$60K** | **$0** | **0% Complete** |

---

## Contact & Escalation

**Project Lead**: [Your Name]
**Technical Lead**: SRE Principal Engineer Agent
**Stakeholders**: Essential Eight Specialist Agent (compliance validation)

**Escalation Path**:
- Technical blockers → SRE Principal Engineer
- Compliance questions → Essential Eight Specialist
- Customer onboarding → IT Glue Specialist (if MSP)
