# ServiceDesk Semantic Analysis - Excel Report Guide

**File**: `ServiceDesk_Semantic_Analysis_Report.xlsx`
**Generated**: 2025-10-27
**Size**: 1.8 MB (10,939 tickets analyzed)
**Analysis Method**: E5-base-v2 semantic embeddings + UMAP + HDBSCAN clustering

---

## 📊 Workbook Structure (10 Worksheets)

### **1. Executive Summary**
**Purpose**: High-level overview metrics

**Key Metrics**:
- Total Tickets: 10,939
- Unique Categories: 21
- Unique Root Causes: 23
- Unique Client Accounts: 144
- Date Range: Full timeline coverage
- Tickets with Descriptions/Solutions
- Analysis metadata (date, model used)

**Use Cases**:
- Quick executive dashboard
- Report summary for stakeholders
- Baseline metrics reference

---

### **2. All Tickets** ⭐ **MASTER DATASET**
**Purpose**: Complete queryable dataset of all 10,939 tickets

**Columns** (12 fields):
1. **Ticket ID** - Unique identifier
2. **Title** - Ticket subject/summary
3. **Category** - Primary ticket category (21 categories)
4. **Status** - Current ticket status
5. **Account Name** - Client/customer name
6. **Created Time** - Ticket creation timestamp
7. **Closed Time** - Ticket closure timestamp
8. **Assigned To** - Current assignee
9. **Root Cause** - Identified root cause (23 types)
10. **Has Description** - Yes/No flag
11. **Has Solution** - Yes/No flag
12. **Document Excerpt** - First 500 chars of description + solution

**Features**:
- ✅ **Filterable** - Auto-filters enabled on all columns
- ✅ **Sortable** - Pre-sorted by Category → Root Cause → Account
- ✅ **Searchable** - Use Excel Ctrl+F to find specific tickets

**Query Examples**:
```excel
# Find all Security tickets for Zenitas
Filter: Category = "Support Tickets" AND Account Name = "Zenitas" AND Root Cause = "Security"

# Find tickets without solutions
Filter: Has Solution = "No"

# Find tickets for specific assignee
Filter: Assigned To = "John Smith"
```

---

### **3. Category Analysis**
**Purpose**: Deep-dive breakdown of all 21 ticket categories

**Columns** (8 fields):
1. **Category** - Category name
2. **Total Tickets** - Count
3. **Percentage** - % of total tickets
4. **Top Root Causes** - Top 5 root causes with counts (pipe-separated)
5. **Top Affected Accounts** - Top 3 clients with counts
6. **Common Keywords** - 15 most common keywords from ticket text
7. **Tickets with Solutions** - Count
8. **Avg Resolution Rate** - Percentage with solutions

**Sorted**: By Total Tickets (descending)

**Key Insights**:
- **Support Tickets** (6,141, 56.1%) - Account (1,581), Software (712), Security (650)
- **Alert** (4,036, 36.9%) - Security (3,906 - 96.8%!)
- **PHI Support Tickets** (468, 4.3%) - Primary Health Insights (342)

**Use Cases**:
- Category performance analysis
- Identify high-volume categories
- Pattern recognition (keywords)
- Resolution rate tracking

---

### **4. Root Cause Analysis**
**Purpose**: Breakdown by root cause (23 types)

**Columns** (6 fields):
1. **Root Cause** - Root cause name
2. **Total Tickets** - Count
3. **Percentage** - % of total tickets
4. **Top Categories** - Top 5 categories (pipe-separated)
5. **Top Affected Accounts** - Top 3 clients
6. **Common Keywords** - 15 most common keywords

**Sorted**: By Total Tickets (descending)

**Key Insights**:
- **Security** (4,573, 41.8%) - Alerts (3,906), Support (650)
- **Account** (1,687, 15.4%) - User provisioning, access
- **Software** (769, 7.0%) - Chrome, OneDrive, M365
- **Hosted Service** (719, 6.6%) - Azure, cloud infrastructure
- **User Modifications** (554, 5.1%) - Config changes

**Use Cases**:
- Root cause trending
- Training needs identification
- Process improvement opportunities
- SLA impact analysis

---

### **5. Account Analysis**
**Purpose**: Top 50 client accounts by ticket volume

**Columns** (6 fields):
1. **Account Name** - Client name
2. **Total Tickets** - Count
3. **Percentage** - % of total tickets
4. **Top Categories** - Top 3 categories
5. **Top Root Causes** - Top 3 root causes
6. **Tickets with Solutions** - Count

**Sorted**: By Total Tickets (descending)

**Key Insights**:
- **Orro Cloud** (5,075, 46.4%) - Internal alerts/monitoring
- **Zenitas** (1,023, 9.4%) - Account, software, hardware
- **KD Bus** (792, 7.2%) - Security, account, software
- **Wyvern Private Hospital** (500, 4.6%) - Account, hardware
- **MIPS** (470, 4.3%) - Account, security, user mods

**Use Cases**:
- Client health monitoring
- Account prioritization
- SLA compliance tracking
- Customer success insights

---

### **6. Category x Root Cause Matrix** ⭐ **PIVOT TABLE**
**Purpose**: Cross-tabulation of categories vs root causes

**Structure**: Pivot table with:
- **Rows**: 21 Categories
- **Columns**: 23 Root Causes
- **Values**: Ticket counts
- **Margins**: Row/column totals

**Use Cases**:
- Pattern identification (e.g., "Alert + Security = 3,906")
- Gap analysis (empty cells = no occurrences)
- Heat map visualization potential
- Cross-dimensional queries

**Example Insights**:
- Support Tickets span all root causes (most diverse)
- Alert category is 96.8% Security (highly concentrated)
- PHI Support Tickets primarily Primary Health Insights root cause

---

### **7. Timeline Analysis**
**Purpose**: Monthly ticket trends by category

**Structure**: Time-series pivot table
- **Rows**: Year-Month (e.g., "2024-01", "2024-02")
- **Columns**: Categories
- **Values**: Ticket counts per month
- **Total Column**: Overall monthly volume

**Use Cases**:
- Seasonality detection
- Trend analysis (increasing/decreasing volume)
- Capacity planning
- Budget forecasting
- Incident spike identification

**Chart Recommendations**:
- Line chart: Total column (overall trend)
- Stacked area chart: All categories (composition over time)
- Bar chart: Month-over-month comparison

---

### **8. Sample Tickets**
**Purpose**: Representative examples from top 20 categories

**Columns** (8 fields):
1. **Category**
2. **Ticket ID**
3. **Title**
4. **Account Name**
5. **Root Cause**
6. **Status**
7. **Created Time**
8. **Document Excerpt** (first 300 chars)

**Sampling**: 5 tickets per category (top 20 categories)

**Use Cases**:
- Manual review/validation
- Training material examples
- Documentation samples
- Quality assurance spot checks

---

### **9. Top Issues by Category**
**Purpose**: Most common recurring issues per category

**Columns** (6 fields):
1. **Category**
2. **Issue/Title** - Common ticket title (truncated to 100 chars)
3. **Occurrence Count** - How many times this exact issue occurred
4. **Root Cause** - Most common root cause for this issue
5. **Sample Ticket ID** - Reference ticket
6. **Has Solution** - Yes/No flag

**Sorted**: By Category, then Occurrence Count (descending)

**Key Insights**:
- Identifies repetitive issues (automation candidates)
- Shows issue frequency patterns
- Resolution tracking per issue type

**Use Cases**:
- Knowledge base article creation
- FAQ development
- Automation opportunity identification
- Process standardization

---

### **10. Automation Opportunities** ⭐ **ACTIONABLE INSIGHTS**
**Purpose**: High-volume repetitive tickets (automation candidates)

**Columns** (7 fields):
1. **Category**
2. **Repetitive Issue** - Recurring ticket title
3. **Occurrences** - Frequency (filtered: ≥5 occurrences)
4. **Root Cause** - Most common root cause
5. **Solution Rate** - % with documented solutions
6. **Automation Potential** - High/Medium/Low rating
7. **Sample Ticket IDs** - Up to 3 reference tickets

**Automation Potential Scoring**:
- **High**: ≥20 occurrences AND ≥70% solution rate (ready to automate)
- **Medium**: ≥10 occurrences (needs solution standardization)
- **Low**: 5-9 occurrences (monitor for growth)

**Sorted**: By Occurrences (descending)

**Visual Indicators**:
- ✅ High potential = Green highlighting
- Standard Medium/Low = No highlighting

**Use Cases**:
- Automation roadmap planning
- ROI calculation (volume × time savings)
- Workflow standardization
- Self-service portal opportunities

---

## 🔍 How to Query the Excel Report

### **Basic Filtering** (All Tickets sheet)
1. Click any column header dropdown
2. Select specific values (e.g., Category = "Alert")
3. Use "Text Filters" for partial matches
4. Combine multiple filters for complex queries

### **Advanced Queries** (Excel formulas)
```excel
# Count tickets by category and root cause
=COUNTIFS('All Tickets'!$C:$C, "Support Tickets", 'All Tickets'!$I:$I, "Security")

# Average solution rate per account
=COUNTIFS('All Tickets'!$E:$E, "Zenitas", 'All Tickets'!$K:$K, "Yes") / COUNTIF('All Tickets'!$E:$E, "Zenitas")

# Find tickets without solutions for specific category
Filter: Category = "Alert" AND Has Solution = "No"
```

### **Pivot Table Queries** (Category x Root Cause Matrix)
1. Use row/column headers to find intersections
2. Identify empty cells (zero occurrences)
3. Compare row totals (category volume)
4. Compare column totals (root cause volume)

### **Timeline Queries** (Timeline Analysis)
1. Filter by date range
2. Compare month-over-month changes
3. Calculate growth rates
4. Identify seasonal patterns

---

## 📈 Common Analysis Scenarios

### **Scenario 1: Find Automation Opportunities**
**Sheets**: Automation Opportunities, Top Issues by Category

**Steps**:
1. Open "Automation Opportunities" sheet
2. Filter "Automation Potential" = "High"
3. Sort by "Occurrences" (descending)
4. Review "Sample Ticket IDs" for pattern validation
5. Calculate ROI: Occurrences × Avg Resolution Time × Hourly Rate

**Example**:
- SSL Expiring alerts: 100+ occurrences → Automate renewal monitoring

---

### **Scenario 2: Client Health Dashboard**
**Sheets**: Account Analysis, All Tickets

**Steps**:
1. Open "Account Analysis" sheet
2. Find target client (e.g., "Zenitas")
3. Note Total Tickets, Top Categories, Top Root Causes
4. Switch to "All Tickets" sheet
5. Filter "Account Name" = "Zenitas"
6. Analyze trends, resolution rates, recurring issues

**Metrics**:
- Ticket volume trend (increasing/decreasing?)
- Resolution rate (Has Solution %)
- Most common root causes (training needs?)
- Escalation patterns (Assigned To changes)

---

### **Scenario 3: Category Deep-Dive**
**Sheets**: Category Analysis, Category x Root Cause Matrix, Sample Tickets

**Steps**:
1. Open "Category Analysis" sheet
2. Find category (e.g., "Alert")
3. Note keywords, root causes, affected accounts
4. Switch to "Category x Root Cause Matrix"
5. View row for "Alert" → See root cause breakdown
6. Open "Sample Tickets" → Review examples

**Insights**:
- Alert category = 96.8% Security root cause
- Keywords: _x000d_, email, security, cisco
- Affected: Orro Cloud (3,693), KD Bus (215)
- **Action**: Security alert automation opportunity

---

### **Scenario 4: Root Cause Training Needs**
**Sheets**: Root Cause Analysis, All Tickets

**Steps**:
1. Open "Root Cause Analysis" sheet
2. Find problematic root cause (e.g., "Software")
3. Note total tickets (769, 7.0%)
4. Review keywords (version, microsoft, onedrive, chrome)
5. Switch to "All Tickets" sheet
6. Filter "Root Cause" = "Software"
7. Analyze common issues (Chrome, OneDrive, Edge)

**Training Plan**:
- Chrome troubleshooting (frequent issue)
- OneDrive sync issues (recurring pattern)
- Microsoft 365 configuration (common requests)

---

## 🎯 Key Performance Indicators (KPIs)

### **From Executive Summary**
- **Total Tickets**: 10,939
- **Unique Categories**: 21
- **Unique Root Causes**: 23
- **Solution Coverage**: Check "Tickets with Solutions" metric

### **From Category Analysis**
- **Top Category**: Support Tickets (56.1%)
- **Second Category**: Alert (36.9%)
- **Average Resolution Rate**: Calculate weighted average from "Avg Resolution Rate" column

### **From Root Cause Analysis**
- **Top Root Cause**: Security (41.8%)
- **Second Root Cause**: Account (15.4%)
- **Third Root Cause**: Software (7.0%)

### **From Account Analysis**
- **Largest Client**: Orro Cloud (46.4%)
- **Second Largest**: Zenitas (9.4%)
- **Top 5 Clients**: Represent ~72% of all tickets

### **From Automation Opportunities**
- **High Potential Count**: Count rows with "High" automation potential
- **Estimated Time Savings**: Sum of (Occurrences × Avg Resolution Time)
- **ROI Potential**: Time Savings × Hourly Rate

---

## 💡 Best Practices

### **For Querying**:
1. ✅ Always start with "All Tickets" sheet for custom queries
2. ✅ Use filters instead of deleting rows
3. ✅ Save filtered views as separate Excel files (File → Save As)
4. ✅ Use "Category x Root Cause Matrix" for cross-dimensional analysis

### **For Analysis**:
1. ✅ Validate findings with "Sample Tickets" sheet
2. ✅ Compare trends in "Timeline Analysis"
3. ✅ Check "Common Keywords" for pattern confirmation
4. ✅ Cross-reference multiple sheets for comprehensive insights

### **For Reporting**:
1. ✅ Use "Executive Summary" for stakeholder reports
2. ✅ Include "Automation Opportunities" in improvement plans
3. ✅ Reference "Top Issues by Category" for knowledge base planning
4. ✅ Use "Timeline Analysis" charts for trend visualization

---

## 📝 Notes

- **Data Source**: ChromaDB semantic embeddings collection
- **Embedding Model**: E5-base-v2 (768 dimensions)
- **Clustering**: UMAP + HDBSCAN (119 clusters, 0.69 silhouette score)
- **Keywords**: TF-IDF style extraction from ticket descriptions + solutions
- **Filters**: All filterable sheets have auto-filters enabled
- **Performance**: 1.8 MB file size optimized for quick loading

---

## 🔄 Refreshing the Report

To regenerate with updated data:

```bash
# Re-run semantic analysis (if new tickets added to database)
python3 claude/tools/sre/servicedesk_semantic_ticket_analyzer.py

# Regenerate Excel report
python3 claude/tools/sre/generate_semantic_excel_report.py
```

**Frequency Recommendation**: Monthly or quarterly, depending on ticket volume growth

---

**Report Generated**: 2025-10-27
**Analysis Coverage**: 10,939 tickets across 21 categories, 23 root causes, 144 accounts
**File Location**: `claude/data/ServiceDesk_Semantic_Analysis_Report.xlsx`
