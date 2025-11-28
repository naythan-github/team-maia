# Available Specialized Agents

## System Overview
All agents automatically load UFC context and operate within Maia's coordinated ecosystem framework. The system has evolved from individual agents with JSON handoffs to real-time communication via message bus with enhanced context preservation and intelligent orchestration.

### **Phase 204 Drata Live Specialist Agent** ⭐ **NEW - COMPLIANCE AUTOMATION EXPERT**
The Drata Live Specialist Agent provides comprehensive expertise in Drata platform compliance automation for GRC frameworks, evidence collection, custom integrations, and audit preparation:
- **Compliance Frameworks**: SOC 2 (CC controls for access, security, confidentiality), ISO 27001 (Annex A controls for ISMS), HIPAA (164.308 administrative safeguards), PCI DSS (Requirement 8 access control), GDPR (data protection controls), NIST 800-53 (security/privacy controls)
- **Evidence Automation**: 200+ integrations (Azure AD, AWS IAM, GitHub, Google Workspace, Okta continuous monitoring), automated collection (daily sync for critical controls, weekly for asset inventory, monthly for policy acknowledgments), Test Builder logic (conditional validation, threshold-based alerting, effectiveness measurement), evidence freshness tracking (24-hour SLA, variance alerting >5%)
- **Custom API Integrations**: Open API development (POST /api/v1/custom-evidence for JSON payloads, GET /api/v1/controls for status), Test Builder creation (POST /api/v1/tests for validation logic), integration architecture (CMDB/HR/identity systems custom connectors), validation patterns (cross-check evidence count with source systems, automated drift detection)
- **Audit Preparation**: Gap analysis workflows (framework requirements mapping, current state assessment, remediation roadmaps), control mapping (SOC 2 CC6.1 → Azure AD provisioning, ISO 27001 A.8.1 → asset inventory, HIPAA 164.308(a)(3) → PIM role-based access), evidence organization (audit-ready packages, control effectiveness validation), auditor collaboration (evidence requests, control testing, finding remediation)
- **Trust Center Management**: Security questionnaire automation (AI-powered response generation), documentation search (AI library scanning), public trust pages (customer-facing security documentation), vendor risk assessment (automated questionnaire workflows)
- **Few-Shot Examples**: (1) SOC 2 access review automation (quarterly manual effort 3 weeks → automated 2 hours, Azure AD + AWS IAM + GitHub daily sync, Test Builder logic for 90-day privileged access validation, automated approval workflow, CC6.1/CC6.2 fully automated with continuous monitoring), (2) Custom CMDB integration for ISO 27001 asset tracking (custom API not in 200+ integrations, Python integration using Open API, asset inventory synced daily, Test Builder validation for >5% variance, ISO 27001 A.8.1 controls automated, audit trail with timestamps)
- **Problem-Solving Approach**: Phase 1 Assess & Map (framework requirements, current controls, evidence gaps, integration opportunities), Phase 2 Automate & Integrate (configure Drata integrations, build custom APIs, Test Builder logic, test frequently with validation), Phase 3 Validate & Optimize (control effectiveness testing, audit readiness review, self-reflection checkpoint), Phase 4 Monitor & Maintain (continuous monitoring, evidence freshness, control drift detection)
- **Control Testing Patterns**: Scheduled cadence (weekly/monthly/quarterly evidence collection), condition-based validation (If privileged_role AND no_mfa THEN fail_control), threshold validation (If variance >5% THEN alert_compliance_team), automated effectiveness measurement (control passing percentage, trend analysis)
- **Integration**: Works with Cloud Security Principal Agent (Drata evidence shows Azure AD MFA gap → need zero-trust architecture design), IT Service Manager Agent (change management integration for control updates), Data Engineer Agent (custom data pipelines for evidence from proprietary systems)
- **Common Control Mappings**: SOC 2 CC6.1 (access provisioning/deprovisioning from Azure AD/Okta/Google Workspace), ISO 27001 A.9.2.1 (user registration from HR systems/identity providers), HIPAA 164.308(a)(3) (workforce authorization with role-based access/PIM), PCI DSS 8.1 (unique user accounts with MFA enforcement)
- **API Endpoints**: POST /api/v1/custom-evidence (send custom JSON for evidence), GET /api/v1/controls (list controls and status), POST /api/v1/tests (create Test Builder validation), GET /api/v1/integrations (connected systems sync status)
- **Evidence Best Practices**: Daily sync for critical controls (access provisioning, MFA enforcement, encryption status), weekly sync for asset inventory and vulnerability scans, monthly sync for policy acknowledgments and training completion, validation with cross-check evidence count against source system
- **Test Builder Logic Examples**: `{"condition": "all_privileged_users_reviewed_90_days", "data_source": "azure_ad_pim", "validation": "approval_workflow_complete"}`, `{"condition": "variance_threshold", "threshold": 0.05, "action": "alert_compliance_team"}`
- **Business Impact**: 60-96% time reduction on recurring compliance tasks (access reviews 3 weeks → 2 hours), 100% evidence automation vs manual quarterly collection, audit-ready continuous monitoring (eliminates pre-audit scramble), custom integration capability for non-standard systems (CMDB, legacy HR, proprietary tools)
- **Real-World Use Cases**: SOC 2 Type II preparation (automated evidence collection across all CC controls), ISO 27001 certification (continuous ISMS monitoring), HIPAA compliance (healthcare access controls automation), multi-framework compliance (SOC 2 + ISO 27001 + HIPAA with shared controls), custom system integration (CMDB asset tracking, legacy HR user provisioning)
- **v2.3 Production**: 214 lines, 2 comprehensive few-shot examples (SOC 2 access review automation with Test Builder logic and daily sync, custom CMDB integration for ISO 27001 with Open API development and variance alerting), all 5 v2.3 advanced patterns (self-reflection, test frequently, checkpoints, prompt chaining, explicit handoff), control mapping reference tables, API endpoint documentation, Test Builder patterns

### **Phase 202 Azure Local Specialist Agent** ⭐ **NEW - HYBRID INFRASTRUCTURE EXPERT**
The Azure Local Specialist Agent (formerly Azure Stack HCI) provides comprehensive expertise in on-premises hyper-converged infrastructure, Arc-enabled hybrid operations, edge deployments, and AI/ML workloads:
- **Cluster Design & Architecture**: Hardware platform selection (Dell AX-640/AX-740xd Premier solutions, Lenovo ThinkAgile MX3530/MX1020 GPU/edge validated, HPE ProLiant DL380 Gen11 HCI-certified), node configurations (2-node ROBO/budget, 3-node small datacenter, 4-16 node enterprise/AI, 2+2 stretch disaster recovery), Storage Spaces Direct (3-way mirror N-2 failures, parity cost-optimized, all-flash NVMe/SSD, hybrid SSD+HDD, nested resilience for stretch), network topology (25GbE/100GbE cluster networking, RDMA for GPU east-west traffic, management separation)
- **Hybrid Operations & Arc Integration**: Azure Arc management (Azure portal, Resource Graph, Policy, RBAC), Arc-enabled services (Monitor, Log Analytics, Update Manager, Backup, Defender for Cloud, Sentinel, Key Vault), cloud witness for quorum (stretch clusters, internet connectivity required), hybrid networking (ExpressRoute, VPN Gateway, on-prem to Azure connectivity), Azure workloads on-prem (AKS, Azure Virtual Desktop, Arc-enabled VMs)
- **Edge & ROBO Scenarios**: Disconnected operations (Preview 2024 - local AD DS, USB/disk witness, manual updates, cached policies), low-bandwidth optimization (batch telemetry upload, offline AKS deployment, local container registry), edge device support (reduced hardware requirements, low-cost Premier solutions like Lenovo MX1020), unstable internet resilience (offline capability, sync when connected, no Arc dependency for core operations)
- **AI/ML Workload Deployment**: GPU cluster configuration (NVIDIA A2/T4 Tensor Core GPUs, GPU operator for Kubernetes, validated hardware platforms), local AI search with RAG (on-prem data privacy, retrieval-augmented generation, small and large language models), AKS offline deployment (Kubernetes v1.28+, CSI driver for Storage Spaces Direct, no internet dependency), containerized inference (local container registry, model persistence, batch training pipelines)
- **Migration & Deployment**: P2V conversion (Azure Migrate offline mode, local appliance), VM migration from legacy (rsync for data transfer, validation benchmarks), deployment timelines (2-week small clusters, 12-week multi-site rollout), air-gapped deployment (USB-based updates, offline Kubernetes, manual driver installation)
- **Few-Shot Examples**: (1) Retail edge deployment (45 stores × 20 VMs per store, Dell AX-640 2-node clusters, disconnected mode with USB witness, Arc-enabled when online for backup/monitoring, $810K hardware + $2,700/month Azure services, 12-week rollout at 5 stores/week), (2) Manufacturing AI workload (vision inspection system, Lenovo ThinkAgile MX3530 4-node GPU cluster with 8× NVIDIA A2 per node, 50TB model storage, air-gapped AKS deployment, 120ms→<100ms inference improvement 17%, $280K hardware with zero cloud costs)
- **Hardware Validation & OEM Catalog**: 100+ validated platforms (Dell Premier AX series, Lenovo ThinkAgile MX series, HPE ProLiant Gen11), validated hardware requirements (OEM catalog check before purchase, firmware automation for Premier solutions, extended support contracts), cluster quorum (2-node USB/cloud witness, 3+ node majority, stretch cloud witness), compute/memory/storage sizing (vCPU calculation with N+1 failover, memory 8-16GB per VM avg, storage 50% growth buffer)
- **Disconnected Mode Requirements**: Local authentication (AD DS on-prem, no Entra ID dependency), quorum witness (USB/disk witness, no cloud witness), update staging (manual quarterly cycles, security patch priority), monitoring (local event logs, batch upload when online, cached Defender policies)
- **Arc Services Comparison**: Connected mode (Monitor batch upload, Backup nightly with weekly sync, Defender cached policies, Update Manager cloud-based), disconnected mode (local event logs only, manual backup to external storage, cached policies only, manual updates)
- **Problem-Solving Approach**: Phase 1 Requirements (workload analysis VMs/containers/AI, edge constraints bandwidth/uptime, compliance data sovereignty), Phase 2 Design (hardware selection with OEM validation, network topology, storage sizing, test frequently with validation benchmarks), Phase 3 Implementation (cluster deployment, Arc integration if connected, workload migration with self-reflection checkpoint on completion)
- **Integration**: Works with Azure Solutions Architect Agent (hybrid networking design, ExpressRoute to Azure), SRE Principal Engineer Agent (monitoring strategy, SLOs for hybrid infrastructure), Cloud Security Specialist Agent (Defender for Cloud configuration, compliance validation SOC2/ISO27001)
- **Common Patterns**: 2-node ROBO cluster (Dell AX-640, USB witness, disconnected mode, Arc when online), GPU AI cluster (Lenovo MX3530, AKS offline, local container registry), stretch cluster (2+2 nodes across sites, cloud witness, synchronous replication), edge manufacturing (air-gapped, manual updates, local authentication)
- **Cluster Configuration Examples**: Small ROBO `2× Dell AX-640, 56 cores, 256GB RAM, 4× 3.84TB NVMe per node, 2× 25GbE cluster + 1× 1GbE mgmt, USB witness`, Enterprise AI `4× Lenovo MX3530, 64 cores, 256GB RAM, 8× NVIDIA A2 GPU, 8× 7.68TB NVMe per node, 2× 100GbE RDMA + 2× 25GbE mgmt, node majority quorum`
- **v1.0 Production**: 222 lines, 2 comprehensive few-shot examples (retail edge with disconnected operations and Arc batch sync, manufacturing AI with air-gapped AKS and GPU inference optimization), all 5 v2.3 advanced patterns (self-reflection, test frequently, checkpoints, prompt chaining, explicit handoff), validated against OEM catalog with specific hardware models and budget estimates
- **Differentiation**: Specialized on-prem HCI focus vs existing Azure agents (Azure Architect cloud-only Well-Architected/FinOps, Azure Solutions Architect surface-level hybrid 1-line mention), Microsoft rebrand Azure Stack HCI → Azure Local (Nov 2024) signals distinct product category warranting dedicated specialist

### **Phase 191 Wget Specialist Agent** ⭐ **NEW - DOWNLOAD & ARCHIVAL EXPERT**
The Wget Specialist Agent provides comprehensive expertise in wget operations for downloads, mirroring, archival, and ethical web scraping:
- **Download Operations**: Single file downloads with retry logic, bulk downloads from URL lists, resumable transfers with `-c` continue, authentication (basic/digest/certificate), bandwidth throttling with `--limit-rate`, timeout and retry configuration (`-t 5 --waitretry=10 --timeout=30`)
- **Site Mirroring**: Recursive downloads with `-m` mirror mode, link conversion for offline browsing `-k`, page requisites CSS/JS/images `-p`, depth limits `-l N`, parent directory exclusion `--no-parent`, adjust extensions `-E` for proper file types
- **Ethical Scraping**: robots.txt compliance `--robots=on` (CRITICAL), rate limiting `--wait=2` between requests, random delays `--random-wait` (0.5-1.5x wait), bandwidth limits `--limit-rate=200k`, custom user agents identifying purpose/contact, Terms of Service validation
- **Advanced Operations**: WARC archival format `--warc-file=archive --warc-cdx` for web preservation, SSL handling `--no-check-certificate` when needed, timestamping for incremental updates, filtering with `--accept/--reject` patterns, regex-based filtering `--accept-regex/--reject-regex`
- **Error Recovery**: Retry logic with `-t N` tries, resume interrupted downloads `-c`, connection refused retry `--retry-connrefused`, wait between retries `--waitretry=10`, failure isolation (extract failed URLs from logs for manual retry with increased timeout)
- **Few-Shot Examples**: (1) Site mirroring with ethics (documentation site mirror with robots.txt compliance, 2s wait + random delays, 200k/s rate limit, link conversion for offline browsing, dry-run validation with `--spider`, 247 files mirrored in ~15min), (2) Bulk authenticated download (500 firmware files with basic auth, input file `-i urls.txt`, 5 retries per file, failure tracking and extraction, 478/500 automatic success with 22 failures isolated for manual review)
- **Problem-Solving Approach**: Phase 1 Requirements Analysis (target type single/bulk/mirror, auth needs, ethical constraints, output format), Phase 2 Command Construction (build wget with appropriate flags, test frequently with `--spider` or small subset), Phase 3 Execution & Validation (run with logging, monitor progress, self-reflection checkpoint on completion), Phase 4 Failure Handling (extract failed URLs, retry with adjusted params, validate final state)
- **Common Patterns**: Simple download `wget -c -t 5 --waitretry=10 <URL>`, mirror with ethics `wget -m -k -p --robots=on --wait=2 --random-wait --limit-rate=200k <URL>`, bulk authenticated `wget -i urls.txt --user=X --ask-password -c -t 5 --no-clobber -P out/`, WARC archival `wget --warc-file=archive --warc-cdx -p -r -l 3 <URL>`
- **Ethical Checklist**: ✅ `--robots=on` enabled, ✅ `--wait` ≥1 second between requests, ✅ `--random-wait` to avoid pattern detection, ✅ `--limit-rate` to avoid bandwidth saturation, ✅ Custom `--user-agent` identifying purpose/contact, ✅ Check site's Terms of Service for scraping policy
- **Integration**: Works with SRE Principal Engineer (infrastructure for large downloads, monitoring, error handling), Security Specialist (credential management, authenticated portal access), Data Analyst (post-download processing, dataset transformation)
- **v2.3 Compressed**: 183 lines, 2 comprehensive few-shot examples (site mirroring with ethical scraping + dry-run validation, bulk authenticated download with failure isolation), all 5 advanced patterns (self-reflection, test frequently, checkpoints, prompt chaining, explicit handoff), compressed domain reference with common patterns and key flags

### **Phase 186 Essential Eight Specialist Agent** ⭐ **NEW - ACSC COMPLIANCE EXPERT**
The Essential Eight Specialist Agent provides comprehensive expertise in ACSC Essential Eight maturity assessment, ML1-ML3 implementation, and Australian government cybersecurity compliance:
- **Core Capabilities**: Maturity assessment (current state evaluation across all 8 strategies), roadmap planning (ML0→ML1→ML2→ML3 progression with dependencies), implementation management (strategy-specific controls, validation, audit prep), compliance validation (ACSC alignment, evidence packages, certification)
- **The 8 Mitigation Strategies**: (1) Application Control - whitelist only, (2) Patch Applications - 48h extreme risk, (3) Configure Office Macros - disable/restrict, (4) User Application Hardening - block Flash/Java/ads, (5) Patch OS - risk-based, (6) Restrict Admin Privileges - PAM, (7) Multi-Factor Authentication - 2+ factors, (8) Regular Backups - daily/tested/offsite
- **Maturity Levels**: ML0 (no implementation, all threats), ML1 (partial, blocks opportunistic attackers), ML2 (mostly aligned, blocks commodity malware/phishing), ML3 (fully aligned ASD baseline, blocks sophisticated APT tradecraft) | **Critical rule**: Same ML across ALL 8 strategies before advancing
- **Few-Shot Examples**: (1) Government ML0→ML3 roadmap (1200 users, 800 workstations, 50 servers, 18-month timeline with phased rollout: ML1 foundation 6mo, ML2 hardening 6mo, ML3 maturity 6mo, evidence package + external assessment, $620K total cost), (2) SMB ML1 quick win (80-person company, 100 endpoints Win/Mac, leverage M365 E5 features, 90-day implementation, $15K one-time + $3K/mo ongoing, insurance compliance validated with 15% premium reduction)
- **Problem-Solving Approach**: Phase 1 Assessment (<2wk current maturity + evidence + gaps), Phase 2 Plan (<1wk roadmap + dependencies + cost-benefit), Phase 3 Implement (3-18mo phased rollout with self-reflection checkpoints at ML transitions), Phase 4 Validate (<2wk external assessment + evidence finalization + audit prep)
- **Integration**: Works with Airlock Digital Specialist Agent (Strategy 1 Application Control ML3 deep-dive), Security Specialist (threat modeling), SRE Principal (automation), Compliance (audit prep), Azure Architect (cloud-native controls)
- **ACSC Resources**: Essential Eight Maturity Model (November 2023), cyber.gov.au implementation guidance, strategy-specific guides
- **v2.3 Compressed**: 184 lines, 2 comprehensive few-shot examples (enterprise ML3 18-month program + SMB ML1 90-day quick win), all 5 advanced patterns (self-reflection, test frequently, checkpoints, prompt chaining, explicit handoff)

### **Phase 159 IT Glue Specialist Agent** ⭐ **NEW - MSP DOCUMENTATION EXPERT**
The IT Glue Specialist Agent provides comprehensive expertise in IT documentation platform implementation, multi-tenant architecture, REST API automation, and password management workflows:
- **Documentation Architecture Design**: Multi-tenant information hierarchy (Organizations → Configurations → Flexible Assets → Documents 3-tier structure), relationship mapping strategies (link configurations/passwords/contacts/domains for 1-click retrieval), standardized template development (SOP templates/network diagrams/runbooks for consistency), version control workflows (track changes/revert to previous versions)
- **REST API Integration & Automation**: REST API endpoint usage (organizations/configurations/flexible_assets/passwords/domains/contacts), authentication & security (API key generation with 90-day expiry management, rate limiting 3000 req/5min), PSA/RMM synchronization (Autotask PSA/ConnectWise PSA/Datto RMM bi-directional sync), automated data population (Active Directory sync/Azure AD sync/network discovery)
- **Password Management & Automation**: Password architecture (integrated password management/relationship mapping to assets), automated password rotation (M365/Azure AD/Active Directory - Select/Enterprise tiers), MyGlue client portal (client password self-service/SSO/mobile app/policy hub), audit trail & compliance (immutable audit log/SOC 2 compliance/access control)
- **Network Glue & Automation**: Network discovery automation (network device detection/Active Directory discovery), automated network diagramming (relationship mapping/topology visualization), configuration documentation (network device configs/IP addressing/VLAN design)
- **AI-Powered Automation (2024-2025 Updates)**: IT Glue Copilot Smart Assist (identify stale assets/auto-cleanup outdated docs/passwords), AI-powered SOP Generator (capture clicks/keystrokes automatically - Select/Enterprise tiers), Device Lifecycle Management (track hardware lifecycle/warranty expiration)
- **Few-Shot Examples**: (1) Multi-tenant documentation architecture design (75 clients with 3-tier structure Organizations→Configurations→Flexible Assets, relationship mapping for 50-80% time savings, standardized template library enforcement via Taxonomist governance, phased rollout pilot 5 clients → 70 clients → automation phase), (2) REST API automation for PSA sync (Autotask PSA bi-directional sync with Python automation script, upsert logic check serial number exists, rate limiting 3000 req/5min with exponential backoff, 90-day API key expiry handling, scheduled 4-hour sync + real-time webhook trigger)
- **Integration Ecosystem**: 60+ native integrations (PSA/RMM/ITSM/cloud platforms), REST API (api.itglue.com base URL US, api.eu.itglue.com EU, x-api-key authentication header), Autotask PSA (configuration item sync/company mapping), ConnectWise PSA (CI synchronization), Datto RMM (asset sync), Microsoft Intune/Azure AD/M365 (automated sync), PowerShell wrapper (github.com/itglue/powershellwrapper official)
- **Performance Metrics**: 50-80% time savings on information retrieval (user-reported feedback), 30%+ productivity gains post-implementation, >95% documentation coverage target (vs <50% manual), 90% user recommendation rate (IT Glue verified), >99% PSA/RMM sync success rate
- **Business Impact**: Automated documentation (PSA/RMM sync eliminates manual updates), SOC 2 compliance (immutable audit trail password access tracking), scalable architecture (unlimited organizations support 500+ clients), client self-service (MyGlue portal reduces ticket volume 20-30%), standardization enforcement (Taxonomist governance + template library)
- **Multi-Tenant Best Practices**: Information hierarchy (Inbox folder for drafts, Flags for status tracking Draft/Review/Approved, one Taxonomist for governance), relationship mapping (Server → Password + Contact + Flexible Asset + Document for zero search time), standardization ("How will information be best presented to team?" not "How does IT Glue want it?"), prioritization (automate routine tasks: 30 sec savings × 10/day > complex tasks: 2 min savings × 1/week)
- **Real-World Use Cases**: MSP multi-tenant documentation rollout (50-200 clients standardized architecture), PSA/RMM integration automation (Autotask/ConnectWise/Datto sync), password management workflows (automated M365/Azure AD/AD rotation), Network Glue implementation (automated network discovery + diagramming), client collaboration portals (MyGlue password self-service reducing ticket volume)
- **Integration**: Works with Autotask PSA Specialist Agent (PSA workflow optimization/API integration), Datto RMM Specialist Agent (RMM asset sync/monitoring integration), SonicWall Specialist Agent (network device documentation/firewall config backups), M365 Integration Agent (Azure AD sync/M365 license tracking/Entra ID password rotation), SRE Principal Engineer Agent (API reliability/monitoring/error handling review)
- **v2.2 Enhanced Template**: 650 lines, 2 comprehensive few-shot examples (multi-tenant architecture design with ReACT pattern + self-review, REST API automation for PSA sync with rate limiting + error handling), self-reflection checkpoint validation (scalability to 100+ clients, completeness of integration points, security multi-tenant isolation, testability actual API endpoints, reliability rate limiting + error scenarios), explicit handoff declaration pattern for agent collaboration, prompt chaining guidance for enterprise-scale migrations

### **Phase 157 Snowflake Data Cloud Specialist Agent** ⭐ **NEW - DATA PLATFORM EXPERT**
The Snowflake Data Cloud Specialist Agent provides comprehensive expertise in cloud-native data architecture, AI/ML enablement, real-time analytics, and cost optimization:
- **Platform Architecture & Design**: Multi-cloud architecture (AWS/Azure/GCP deployment strategies, region selection, account structure), storage vs compute separation (elastic scaling patterns, warehouse-per-workload design), data sharing ecosystems (secure cross-organization collaboration, provider-consumer patterns), disaster recovery (data replication, failover automation, time travel 90 days, zero-copy cloning), multi-tenant patterns (MTT for 50-500 tenants with RLS, OPT for <50 or >1000, hybrid regional)
- **AI/ML Enablement**: Cortex AI (LLM functions for text generation/classification, Cortex Analyst semantic models YAML, Cortex Search RAG for unstructured data, Cortex Guard safety nets), Snowpark (Python/Java/Scala data engineering, DataFrame API, pandas-on-Snowflake, ML pipelines), Snowflake ML (model training, deployment, MLOps workflows, feature engineering), AI architecture patterns (multi-tenancy MTT vs OPT, Model Context Protocol MCP integration, conversational context management)
- **Real-Time Analytics & Streaming**: Iceberg Tables (managed vs external, ACID transactions, multi-engine interoperability Spark/Trino/Presto, snapshot-based querying), Snowpipe Streaming (auto-ingest from S3/Azure/GCS, near-real-time CDC, Kafka integration, millisecond latency), Streams & Tasks (change data capture, incremental processing, DAG orchestration), Openflow (managed Apache NiFi for CDC replication and event streaming), Confluent Tableflow (Kafka topics → Iceberg tables materialization, 80% cost savings vs Snowpipe for high volume)
- **Cost Optimization & Performance**: Warehouse sizing (X-SMALL → 6X-LARGE selection criteria, spillage analysis local vs remote, start small and scale up), scaling strategies (scale-up for complex queries 2x faster = same cost, scale-out for concurrency only, multi-cluster auto-scaling min=1 max=4), query optimization (clustering keys 60-95% micro-partition pruning, materialized views, search optimization, result caching 60%+ hit rate), Query Acceleration Service QAS (BI dashboards 20-40% cost reduction), auto-suspend policies (1-5 min aggressive tuning, resource monitors for cost alerts)
- **Data Governance & Security**: Snowflake Horizon (unified catalog, tag-based classification, lineage tracking, compliance), RBAC (role hierarchy design, privilege management, custom roles, 100% coverage), row-level security RLS (dynamic policies with session context variables CURRENT_SESSION_CONTEXT('TENANT_ID'), automatic tenant isolation), data masking (tag-based masking policies automatic PII detection, dynamic masking based on user roles), data classification (automated PII detection, tag propagation across clones)
- **Data Engineering Workflows**: Snowpipe (continuous loading 1-min intervals, auto-ingest from cloud storage), Snowpark Python (ETL/ELT pipelines, DataFrame API, pandas compatibility), Tasks & Streams (serverless orchestration, DAG workflows, incremental CDC processing), zero-copy cloning (dev/test/prod environments without duplication), time travel (data recovery 90 days, historical analysis, query rewind), file loading optimization (100-250 MB compressed per file)
- **Few-Shot Examples**: (1) Cortex AI multi-tenant SaaS architecture (50 customers with RLS isolation via session TENANT_ID, semantic model YAML with verified queries, conversational history cost control 5-turn truncation = 85% cost reduction, security validation cross-tenant query tests, 4-phase implementation roadmap), (2) Real-time Kafka streaming (50K events/sec = 4.3B events/day, Confluent Tableflow → Iceberg → Snowflake external tables, <5 min latency with 2-min auto-refresh, 80% cost savings vs Snowpipe Streaming, Spark interoperability same Parquet files, clustering on event_timestamp for 95%+ pruning)
- **Performance Targets**: P95 <3s simple queries, P95 <30s complex aggregations, 100+ concurrent users with multi-cluster auto-scale, <5 min data freshness streaming, 99.9% uptime with multi-region failover for 99.99%
- **Cost Efficiency Targets**: >70% warehouse utilization aggressive auto-suspend, >60% cache hit rate for BI dashboards, <5% query spillage remote = resize warehouse, <20% storage growth month-over-month
- **Multi-Tenancy Patterns**: MTT (Multi-Tenant Tables) shared resources single schema RLS isolation for 50-500 tenants, OPT (Object-Per-Tenant) physical isolation independent scaling for <50 or >1000 tenants, hybrid regional MTT (1 database per region, MTT within region for 100-500 customers), session context variables for RLS dynamic filtering
- **Streaming Architecture**: Low volume <1K events/sec Snowpipe 1-min intervals $0.06/GB, medium volume 1K-10K events/sec Snowpipe Streaming with Iceberg sub-minute, high volume >10K events/sec Confluent Tableflow → Iceberg → Snowflake 80% cost savings, CDC patterns (Oracle CDC Connector, Openflow for database replication)
- **Business Impact**: Architecture guidance (multi-cloud, AI/ML, streaming, governance), cost optimization (warehouse sizing, query tuning, 20-80% savings), real-time analytics (Iceberg + Kafka, <5 min latency), production patterns (multi-tenancy, security isolation, disaster recovery)
- **Real-World Use Cases**: AI-powered SaaS analytics (Cortex AI natural language queries, multi-tenant data isolation), real-time dashboards (Kafka+Iceberg streaming <5 min freshness), data lakehouse (open Iceberg format multi-engine access), enterprise data warehouse consolidation (on-prem → Snowflake migration)
- **Integration**: Azure/AWS/GCP multi-cloud (Private Link secure access, managed identity, VNet peering), Apache Spark interoperability (same Iceberg snapshots), Confluent Kafka (Tableflow materialization), dbt data transformation (SQL-based modeling), Fivetran/Airbyte ETL
- **v2.2 Enhanced Template**: 580 lines, 2 comprehensive few-shot examples (Cortex AI multi-tenancy with RLS security + conversational cost optimization, real-time Kafka streaming with Iceberg+Tableflow architecture), self-reflection checkpoint validation (architecture completeness, cost efficiency, scalability, security compliance, performance), warehouse sizing methodology, prompt chaining guidance for enterprise migrations

### **Phase 156 Document Conversion Specialist Agent** ⭐ **NEW - DOCUMENT AUTOMATION EXPERT**
The Document Conversion Specialist Agent provides expertise in DOCX creation, corporate template extraction, multi-format conversion, and custom conversion tool development:
- **Template Extraction & Analysis**: Corporate template extraction (parse existing Word docs for styles/structure/placeholders), style analysis (fonts/colors/spacing/margins/header/footer patterns), structure mapping (paragraph hierarchy/table layouts/image positions), Jinja2 template creation (convert static → dynamic with `{{ placeholders }}`)
- **Multi-Format Conversion**: Markdown → DOCX (preserve headings/code/tables/lists), HTML → DOCX (web content with CSS style mapping), PDF → DOCX (text extraction, OCR limitations noted), DOCX → DOCX (template-based data population), reference template usage (apply corporate styles via `--reference-doc=template.docx`)
- **Document Generation Workflows**: Data-driven generation (populate from JSON/CSV/database), batch processing (100s-1000s documents from templates), dynamic content (conditional sections/loops/calculated fields with Jinja2), quality validation (automated style consistency/completeness checks)
- **Custom Tool Development**: Conversion tool architecture (CLI/API design for specific workflows), library selection (python-docx/docxtpl/Pandoc/docx2python guidance), error handling (graceful degradation for unsupported features/file corruption), performance optimization (streaming for large files, parallel batch processing)
- **Library Ecosystem Expertise**: python-docx (DOCX manipulation: read/write/modify, paragraph/run/table/image handling, style customization), docxtpl/python-docx-template (Jinja2 templating for DOCX with placeholders/loops/conditionals, v0.20.2 Nov 2025, Python 3.7-3.13), Pandoc (universal converter: MD/HTML/LaTeX → DOCX, reference template support, table of contents generation), docx2python (structure extraction for analysis/reverse engineering), pypandoc (Python wrapper with binary-inclusive package)
- **Template Workflows**: Extract styles from existing docs (XPath for complex elements: `//w:p` paragraphs, `//w:tbl` tables), create Jinja2 placeholders (`{{ variable }}`, `{% for %}`, `{% if %}`), populate from data sources, validate preservation (fonts/colors/spacing/margins), handle Run-level styling (Word stores text in multiple Run objects with independent styles)
- **Few-Shot Examples**: (1) Corporate QBR template extraction (96% time savings: 2-3h → 5min, Jinja2 placeholders, style inventory JSON, usage guide), (2) MD→DOCX converter with corporate styling (Pandoc + reference templates, code block handling, 95/100 fidelity score), (3) HTML email archival system (image extraction/embedding, metadata preservation, date-based organization, 100% success rate on 15 test emails)
- **Conversion Quality Metrics**: 95+ structure preservation (headings/lists/tables/code maintained), 90+ style accuracy (fonts/colors/spacing match reference), 85+ image handling (embedded or placeholder), <5s performance target for typical docs (5-20 pages)
- **Business Impact**: 60-96% time reduction (recurring documents: QBRs 2-3h → 5min), 100% branding consistency (vs 70-80% manual), batch scalability (100s-1000s docs vs 5-10/day manual), compliance archival automation (7-year retention)
- **Real-World Use Cases**: Recurring reports (quarterly business reviews, monthly updates, annual reports), email archival (HTML → DOCX for compliance retention), multi-format pipelines (Markdown → DOCX → PDF workflows), corporate template libraries (version-controlled, reusable), contract generation (template + data population), documentation automation (technical writers: MD → corporate DOCX)
- **Existing Tool Integration**: cv_converter.py (CV-specific MD→DOCX with 3 modes: styled/ATS/readable) - Agent provides general conversion expertise and tool development guidance for broader use cases
- **v2.2 Enhanced Template**: 880 lines, 3 comprehensive few-shot examples (template extraction, multi-format conversion, custom tool development), self-reflection checkpoint pattern, library selection framework, XPath extraction patterns, style preservation strategies

### **Phase 115 Information Management System** ⭐ **COMPLETE - PHASE 2.1 AGENT ORCHESTRATION**
Complete information management ecosystem with proper agent-tool architecture separation:

**Architecture**: Agent-Tool Separation Pattern
- **7 Tools** (Python .py files in `claude/tools/`): DO the work - execute database operations, calculations, data retrieval
- **3 Agents** (Markdown .md files in `claude/agents/`): ORCHESTRATE tools - natural language interface, multi-tool workflows, response synthesis

**Phase 1: Production Systems** (4 tools, 2,750 lines):
- `enhanced_daily_briefing_strategic.py` - Executive intelligence with 0-10 impact scoring
- `meeting_context_auto_assembly.py` - Automated meeting prep (80% time reduction)
- `unified_action_tracker_gtd.py` - GTD workflow with 7 context tags
- `weekly_strategic_review.py` - 90-min guided review across 6 stages

**Phase 2: Management Tools** (3 tools, 2,150 lines):
- **Tool Location**: `claude/tools/information_management/` and `claude/tools/productivity/`
- `stakeholder_intelligence.py` - CRM-style relationship health monitoring (0-100 scoring), 33 stakeholders auto-discovered, color-coded dashboard (🟢🟡🟠🔴)
- `executive_information_manager.py` - 5-tier prioritization (critical→noise), 15-30 min morning ritual, energy-aware batch processing
- `decision_intelligence.py` - 8 decision templates, 6-dimension quality framework (60 pts), outcome tracking, pattern analysis

**Phase 2.1: Agent Orchestration Layer** (3 agents, 700 lines) ⭐ **NEW**
- **Agent Location**: `claude/agents/`
- **Purpose**: Natural language interface transforming CLI tools into conversational workflows

**1. Information Management Orchestrator** ✅ **OPERATIONAL**
- **Location**: `claude/agents/information_management_orchestrator.md` (300 lines)
- **Type**: Master Orchestrator Agent
- **Purpose**: Coordinates all 7 information management tools with natural language interface
- **Capabilities**: 6 core workflows (daily priorities, stakeholder management, decision capture, meeting prep, GTD workflow, strategic synthesis)
- **Natural Language Examples**:
  - "what should i focus on" → orchestrates executive_information_manager.py + stakeholder_intelligence.py + enhanced_daily_briefing_strategic.py
  - "help me decide on [topic]" → guides through decision_intelligence.py workflow
  - "weekly review" → orchestrates weekly_strategic_review.py + stakeholder portfolio
- **Tool Delegation**: Multi-tool workflows with response synthesis and quality coaching

**2. Stakeholder Intelligence Agent** ✅ **OPERATIONAL**
- **Location**: `claude/agents/stakeholder_intelligence_agent.md` (200 lines)
- **Type**: Specialist Agent (Relationship Management)
- **Purpose**: Natural language interface for stakeholder relationship management
- **Capabilities**: 6 workflows (health queries, portfolio overview, at-risk identification, meeting prep, commitment tracking, interaction logging)
- **Natural Language Examples**:
  - "how's my relationship with Hamish" → context --id <resolved_id>
  - "who needs attention" → dashboard (filter health <70)
  - "meeting prep for Russell tomorrow" → context --id + recent commitments
- **Tool Delegation**: Delegates to stakeholder_intelligence.py tool with name resolution and quality coaching

**3. Decision Intelligence Agent** ✅ **OPERATIONAL**
- **Location**: `claude/agents/decision_intelligence_agent.md` (200 lines)
- **Type**: Specialist Agent (Decision Capture & Learning)
- **Purpose**: Guided decision capture workflow with quality coaching
- **Capabilities**: 5 workflows (guided capture, review & quality scoring, outcome tracking, pattern analysis, templates & guidance)
- **Natural Language Examples**:
  - "i need to decide on [topic]" → guided workflow with template selection
  - "review my decision on [topic]" → quality scoring + coaching
  - "track outcome of [decision]" → outcome recording + lessons learned
- **Tool Delegation**: Delegates to decision_intelligence.py tool with decision type classification and 6-dimension quality framework

**Project Metrics**:
- **Total Code**: 7,000+ lines (Phase 1: 2,750 lines + Phase 2: 2,150 lines + Phase 2.1: 700 lines + databases: 1,350 lines)
- **Development Time**: 16 hours across 5 sessions (Phase 1: 3 hrs, Phase 2: 10 hrs, Phase 2.1: 3 hrs)
- **Business Value**: $50,400/year savings vs $2,400 cost = 2,100% ROI
- **Architecture**: Proper agent-tool separation (agents orchestrate, tools implement)
- **Integration**: Cross-system workflows with natural language interface

### **Phase 144 PagerDuty Specialist Agent** ⭐ **NEW - AIOPS INCIDENT MANAGEMENT SPECIALIST**
The PagerDuty Specialist Agent provides expert incident management with Event Intelligence (AIOps), ML-powered alert grouping, and Modern Incident Response for PagerDuty platform:
- **Event Intelligence & AIOps**: Intelligent Alert Grouping (ML-powered, 60-80% noise reduction), Content-Based Grouping (rule-based, immediate impact), Time-Based Grouping (alert storm handling), Global Alert Grouping (cross-service incidents), deduplication via `dedup_key`
- **Modern Incident Response**: Status Pages (automated subscriber updates), Stakeholder Communication (real-time non-technical updates), Post-Incident Reviews (structured retrospectives), Response Plays (pre-defined workflows), AI-Powered Collaboration (Slack/Teams with generative AI)
- **Event Orchestration & Automation**: Dynamic Routing (ML-driven based on historical context), Event Orchestration Variables (custom automation logic), Runbook Automation (auto-diagnostics and remediation), Auto-Resolution (close when underlying issues resolve), Webhook Automation (custom integrations)
- **On-Call Management**: Schedule Templates (fair rotations), Escalation Policies (multi-level with time-based routing), Live Call Routing (phone bridge for P1), On-Call Analytics (workload tracking, burnout prevention), Follow-the-Sun (24/7 regional coverage)
- **Integration Ecosystem (700+ Tools)**: Monitoring (Datadog, Splunk, AWS CloudWatch, Prometheus, Azure Monitor), ITSM (Jira, ServiceNow, Zendesk bi-directional sync), Collaboration (Slack, Microsoft Teams with AI), Change Management (GitHub, GitLab deployment correlation)
- **Analytics & Operational Intelligence**: MTTA/MTTR tracking with benchmarks, Event Intelligence ML recommendations, Incident frequency analysis, Business impact metrics (customer-facing downtime, revenue correlation), Team health monitoring
- **Research-Backed Best Practices (2024-2025)**: 90-minute AIOps setup, minimal ML training (7-14 days), 68% avg noise reduction validated, 50-70% faster MTTA with Event Intelligence
- **Real-World Optimization**: 1,296 → 384 incidents/week (68% reduction examples), 8.2 → 3.4 min MTTA (59% improvement), follow-the-sun scheduling across 3 regions, multi-source integration (AWS + Datadog + Splunk)
- **Business Impact**: $450K+ annual savings (3 FTE equivalent capacity recovered), 50-70% faster MTTA, 40-60% faster MTTR, 60-80% noise reduction via ML, 50%+ burnout risk reduction
- **v2.2 Enhanced Template**: 590 lines, comprehensive few-shot examples (Event Intelligence deployment, Follow-the-Sun scheduling), self-reflection checkpoint pattern, AIOps-specific guidance
- **Collaborations**: SRE Principal Engineer (SLO/SLI), OpsGenie Specialist (platform migration), DevOps Principal Architect (CI/CD integration), Service Desk Manager (ITSM workflows), Security Specialist (security incidents)
- **Model**: Claude Sonnet (Event Intelligence configuration, ML training validation, architecture decisions)
- **Status**: ✅ Production Ready (2025-11-05)

### **Phase 143 OpsGenie Specialist Agent** ⭐ **INCIDENT MANAGEMENT SPECIALIST** (Enhanced 2025-11-05)
The OpsGenie Specialist Agent provides expert incident management, alerting optimization, on-call scheduling, AND platform migration export for Atlassian OpsGenie platform:
- **Incident Management Architecture**: Service-aware incident grouping, workflow design for varying priorities, alert-to-incident routing, post-incident reviews
- **Alerting Optimization**: Alert routing rules (by tags, priority, source, time), deduplication & noise reduction (entity-based grouping), alert enrichment (runbooks, dashboards), alert fatigue prevention (65-75% noise reduction achievable)
- **On-Call Management**: Schedule design (fair rotations with override/swap), multi-level escalation policies, follow-the-sun coverage (24/7 across regions), on-call analytics (workload tracking, burnout prevention)
- **Integration Architecture**: Monitoring tools (AWS CloudWatch, Datadog, Prometheus, Azure Monitor), collaboration platforms (Slack, Teams), ITSM integration (Jira Service Management, ServiceNow)
- **Metrics & Continuous Improvement**: MTTA/MTTR tracking, alert effectiveness analysis (actionability rate, false positives), incident trend analysis, runbook effectiveness measurement
- **Platform Migration & Export** ⭐ **NEW**: Configuration export (teams, users, schedules, escalation policies, integrations via OpsGenie API), OpsGenie → PagerDuty/JSM mapping documentation, gap analysis (feature comparison), parallel validation strategy (2-3 day migration + 2-4 week validation), OpsGenie EOL support (April 5, 2027 deadline)
- **Research-Backed Best Practices**: Entity-based deduplication, time-window aggregation, alert dependencies, multi-level escalation (5/10/15 min delays), business hours coverage
- **Real-World Optimization**: Alert fatigue reduction (312 → 85 alerts/day examples), follow-the-sun scheduling across 3 regions, AWS CloudWatch integration patterns, complete migration export (12 teams, 15 schedules, 8 policies, 22 integrations)
- **Business Impact**: 40-60% faster MTTA, 50%+ burnout risk reduction, 30-50% MTTR improvement, 11+ hours/day recovered from noise reduction
- **v2.2 Enhanced Template**: 896 lines (includes migration export capability), 3 comprehensive few-shot examples (alert fatigue, on-call design, PagerDuty migration export), self-reflection checkpoint pattern
- **Collaborations**: **PagerDuty Specialist** (migration import, Event Intelligence) ⭐ **NEW**, SRE Principal Engineer (SLO/SLI), Service Desk Manager (ITSM integration), DevOps Principal Architect (CI/CD integration), Security Specialist (security incidents)
- **Model**: Claude Sonnet (complex routing logic, architecture decisions, migration planning)
- **Status**: ✅ Production Ready (2025-11-05) with Migration Export Capability

### **Phase 153 ManageEngine Patch Manager Plus API Specialist Agent** ⭐ **NEW - API AUTOMATION EXPERT** (2025-11-17)
The ManageEngine Patch Manager Plus API Specialist Agent provides expert REST API automation guidance for programmatic patch management, multi-tenant MSP operations, and enterprise integration workflows:
- **API Authentication & Security**: Local authentication (base64 password encoding, authtoken management), Active Directory auth (domain integration, multi-domain scenarios), OAuth 2.0 cloud (grant token workflow, access/refresh token management, scope configuration `PatchManagerPlusCloud.PatchMgmt.READ/UPDATE`), security best practices (environment variables, SSL validation, token rotation, AWS Secrets Manager/Azure Key Vault integration)
- **Patch Discovery & Querying**: List all patches (`GET /api/1.4/patch/allpatches`) with filters (severity 0-4, approval status 211/212, platform Windows/Mac, patch status 201 Installed/202 Missing), pagination handling (iterate 25/page, calculate total pages, efficient batch processing), patch details by ID/bulletin ID (KB numbers, CVE IDs), compliance queries (missing critical patches, patch coverage %, aging patches >30 days)
- **Patch Deployment Automation**: Deploy patches (`POST /api/1.3/patch/installpatch`) with scheduling (`installaftertime`, `deadlineTime`, `expirytime`), reboot options (0: Not configured, 1: Within window, 2: Outside window), retry configuration (1-10 attempts), target selection (ResourceIDs, resourceNames, customGroups, ipAddresses, remoteOffices), deployment modes (Deploy on agent contact, Deploy Immediately instant execution, Draft save without deploying, Self-Service Portal `deploymentType: 1`), approval integration (`isOnlyApproved: true` filter)
- **Rollback & Uninstall Operations**: Patch uninstall (`POST /api/1.3/patch/uninstallpatch`) for rollback scenarios (patch conflicts, boot failures, application compatibility), emergency rollback (immediate uninstall for critical failures), post-rollback validation (query patch status, confirm removal, test affected systems)
- **Production-Grade Error Handling (SRE)**: Retry logic (exponential backoff 1s→60s, max 3 retries, idempotency validation), circuit breaker (fail fast after 5 consecutive 500 errors, auto-recovery after 5 min cooldown), rate limiting (conservative 50-100 req/min, adaptive throttling on 429 responses), structured logging (JSON format: timestamp, endpoint, method, status_code, latency_ms, error_details), monitoring integration (Prometheus metrics export, Grafana dashboards, PagerDuty/OpsGenie alerts)
- **Multi-Tenant MSP Patterns**: Customer segmentation (iterate customer list, separate API credentials per tenant, aggregate compliance reports), bulk operations (batch patch approvals, parallel deployment with ThreadPoolExecutor, progress tracking), SLA compliance (automated patch deployment within 24h critical/7d high/30d moderate windows, compliance reporting per customer)
- **Research-Backed Best Practices (2024-2025)**: OAuth token refresh automation (3600s expiration, 100s buffer), test-first deployment pattern (test group 5-10 endpoints → validate 80% success → production rollout), emergency CVE workflow (zero-day response in 75 min for 1000 endpoints), multi-tenant parallel execution (max 10 concurrent customers via ThreadPoolExecutor), deployment policy templates (retrieve via `GET /api/1.4/patch/deploymentpolicies`)
- **Real-World Optimization**: **Critical patch deployment** (500 endpoints in 2 min API vs 30 min manual = 93% time savings), **Multi-tenant compliance reporting** (50 customers in 10 min via parallel execution vs 8 hours manual = 98% reduction), **Emergency CVE deployment** (1000 endpoints test→production in 75 min with automated rollback vs 3 days manual), **Approval-aware workflows** (check approval mode via `GET /api/1.4/patch/approvalsettings` → filter approved patches → deploy with `isOnlyApproved: true`)
- **Business Impact**: **93% time savings** (30 min manual → 2 min API for 50 endpoints), **98% reduction in reporting time** (8 hrs → 10 min for 50 customers), **1 engineer managing 5000 endpoints** vs 500 manual limit (10x scalability), **$1,500/month savings** (15 hrs/month recovered at $100/hr), **95%+ patch coverage** vs 70-80% manual, **Automated SLA adherence** (patch within 24h/7d/30d windows)
- **v2.2 Enhanced Template**: 1,324 lines, 3 comprehensive few-shot examples (OAuth critical patch deployment with test→production workflow, multi-tenant compliance reporting for 50 customers with parallel execution, emergency CVE deployment with automated rollback), production-grade Python code (complete executable examples with error handling, retry logic, structured logging, rate limiting), self-reflection checkpoint pattern
- **Collaborations**: **ManageEngine Desktop Central Specialist** (UI operations: agent cache cleanup, connectivity troubleshooting, manual patch approval), **SRE Principal Engineer** (production deployment planning: canary deployments, blue-green strategies, monitoring integration), **Security Specialist** (CVE prioritization: risk scoring, vulnerability assessment, emergency response coordination), **Data Analyst** (compliance analytics: trend analysis, predictive modeling for patch failures, SLA violation forecasting)
- **API Endpoints Confirmed**: `GET /api/1.3/desktop/authentication` (auth token retrieval), `GET /api/1.4/patch/allpatches` (patch queries with filters), `POST /api/1.3/patch/installpatch` (deployment automation), `POST /api/1.3/patch/uninstallpatch` (rollback/uninstall), `GET /api/1.4/patch/approvalsettings` (approval mode check), `GET /api/1.4/patch/deploymentpolicies` (policy templates)
- **Known Limitations**: Deployment status monitoring endpoint undocumented (use manual UI verification), rate limits undocumented (recommend 50-100 req/min), no official Python SDK (use `requests` library), OAuth token refresh requires multi-step setup (Zoho API Console), patch approval endpoint not found (use `isOnlyApproved` filter in deployment)
- **Test Results**: 95.2% pass rate (80/84 tests), 90.4/100 quality score, production approved
- **Model**: Claude Sonnet (API workflow design, Python code generation, error handling strategies, compliance reporting)
- **Status**: ✅ Production Ready (2025-11-17) - Complete v2.2 Enhanced agent with confirmed API endpoints

### **Phase 147 Datto RMM Specialist Agent** ⭐ **NEW - MSP CLOUD-NATIVE RMM EXPERT** (2025-11-07)
The Datto RMM Specialist Agent provides expert MSP operations guidance for cloud-native endpoint management, patch automation, component development, PSA integration, and Datto BCDR workflows:
- **Patch Management Automation**: Windows patch policies (global, site, device-level with age-based approval 7/14/30 days), severity & classification rules (Critical/Security auto-approve), maintenance windows (Patch Tuesday, daily, weekly, monthly), failure resolution guidance, **Limitations**: ❌ NO Linux patching (monitoring only), ❌ NO automated rollback (manual via Windows or Datto BCDR restore)
- **Component Development & Automation**: PowerShell components (Input Variables, UDFs, error handling), Bash components (Linux monitoring, limited management), ComStore integration (200+ pre-built components), desktop shortcut deployment (`C:\Users\Public\Desktop\` all users or `$env:USERPROFILE\Desktop\` current user), self-healing automation (alert-triggered with PSA ticket escalation)
- **Monitoring & Alerting**: Real-time monitoring (60-second agent check-ins vs 10-min ManageEngine), performance monitoring (30-day historical graphs, threshold alerts, auto-remediation), service monitoring (Windows service auto-restart, process monitoring), Event Log monitoring (Windows + Linux syslog/journalctl), alert delivery (email, webhooks Teams/Slack, PSA ticketing)
- **PSA Integration Workflows**: ConnectWise PSA (bidirectional: ticket creation, time tracking sync, CI sync, company/device association), Autotask PSA (Single System of Record SSoR with direct PSA access from RMM console), ticket automation (alert-based creation, auto-resolution on self-healing success, time entry sync), billing integration (device count sync, service billing alignment, contract management), agent-based ticketing (end users submit tickets via Datto agent UI)
- **Datto BCDR Integration**: Native BCDR integration (unified backup status in RMM console, direct backup/restore from RMM), **25% technician time reduction** (Datto-documented metric), automated workflows (agent deployment for BCDR, backup policy enforcement, recovery testing), rollback strategy (use BCDR restore for patch rollback - Datto RMM lacks auto-rollback)
- **Research-Backed Best Practices (2024-2025)**: Desktop shortcut deployment (Public Desktop for all users vs current user), self-healing workflow design (monitor → trigger → remediate → escalate on failure → auto-resolve on success), monthly Patch Tuesday automation (global policy + site overrides + 24-hour client notification + PSA ticket failures + compliance reporting), Datto agent architecture (60-second check-ins, .NET service auto-updating, IPv4 only, port 443 outbound HTTPS), Component system (PowerShell/Bash/Batch/Python, Input Variables for reusability, UDFs for platform data)
- **Real-World Optimization**: Self-healing disk cleanup (80% auto-resolution rate, 5-10 alerts/week → 1-2 tickets/week, <2 min response time, 5-8 hours/month saved per MSP), monthly Patch Tuesday workflow (20 clients, 95-98% patch compliance, 30-60 min deployment time, 2-5% failure rate, 80% time savings vs manual), desktop shortcut deployment (50 workstations, 2-3 min per device, 95-98% success rate)
- **Business Impact**: **Patch automation: 80% reduction** vs manual (8 hours → 1.6 hours per Patch Tuesday), **Self-healing: 5-8 hours/month saved** per MSP (50 servers, 10% alert frequency), **Datto BCDR integration: 25% technician time reduction** (Datto-documented), **MSP profitability: $2K-4K/month labor cost reduction**, **Contract retention: 85%+** (proactive service = higher renewal rates)
- **v2.2 Enhanced Template**: 580 lines, 4 core behavior principles with self-reflection checkpoint (5 criteria: technical accuracy, MSP impact, platform compatibility, completeness, client transparency), 2 comprehensive few-shot examples (Self-Healing Disk Cleanup 95 lines Chain-of-Thought, Patch Tuesday Workflow 90 lines Structured Framework), desktop shortcut deployment guidance (PowerShell component), prompt chaining for enterprise component library migration
- **Collaborations**: Autotask PSA Specialist (PSA SSoR workflows, ticket automation, billing integration), ManageEngine Specialist (platform comparison, Linux patching needs, migration assessment), SRE Principal Engineer (monitoring optimization, alert threshold tuning, incident response), Service Desk Manager (client communication templates, escalation procedures, SLA management)
- **Model**: Claude Sonnet (component development, policy configuration, troubleshooting workflows, PSA integration design)
- **Status**: ✅ Production Ready (2025-11-07)

### **Phase 146 SonicWall Specialist Agent** ⭐ **FIREWALL & VPN EXPERT** (2025-11-05)
The SonicWall Specialist Agent provides comprehensive firewall policy management, SSL-VPN/NetExtender configuration, IPsec site-to-site VPN troubleshooting, and security services optimization for network administrators managing SonicWall platforms (TZ, NSa, NSsp series).

### **Phase 145 Autotask PSA Specialist Agent** ⭐ **MSP OPERATIONS EXCELLENCE** (2025-11-05)
The Autotask PSA Specialist Agent provides expert MSP operations management with workflow automation, REST API integration patterns, 12-month transformation roadmaps, and revenue operations (RevOps) optimization for Autotask Professional Services Automation platform.

### **Phase 131 Asian Low-Sodium Cooking Agent** ⭐ **CULINARY SPECIALIST**
The Asian Low-Sodium Cooking Agent provides specialized culinary consulting for sodium reduction in Asian cuisines while preserving authentic flavor profiles:
- **Multi-Cuisine Expertise**: Chinese, Japanese, Thai, Korean, and Vietnamese cooking traditions with sodium-specific knowledge
- **Scientific Sodium Reduction**: Ingredient substitution ratios, umami enhancement without salt, flavor balancing (acid/fat/heat compensation)
- **Practical Recipe Modification**: Step-by-step adaptation guidance with expected flavor outcomes and authenticity ratings (X/10 scale)
- **Ingredient Intelligence**: Low-sodium alternatives with availability guidance (mainstream vs. specialty), multiple options (budget to premium)
- **Cuisine-Specific Strategies**: Tailored approaches for each Asian cuisine's unique sodium profiles and flavor priorities
- **Umami Without Salt**: Natural glutamate sources (mushrooms, seaweed, tomatoes), fermentation techniques, Maillard reaction optimization
- **Flexibility Assessment**: Dish categorization (high/moderate/low sodium flexibility) to set realistic expectations
- **Flavor Troubleshooting**: Solutions for common issues (too bland, missing depth, unbalanced) when reducing sodium
- **Health-Conscious**: Practical guidance (60-80% sodium reduction achievable) without sacrificing authentic flavor experience
- **Complements Lifestyle Agents**: Works alongside Cocktail Mixologist and Restaurant Discovery agents in Maia's culinary ecosystem
- **Model**: Claude Sonnet (creative substitutions and recipe analysis require strategic reasoning)
- **Status**: ✅ Production Ready (2025-10-18)

### **Phase 108 Team Knowledge Sharing Agent** ⭐ **PREVIOUS ENHANCEMENT**
The Team Knowledge Sharing Agent creates compelling team onboarding materials, documentation, and presentations demonstrating AI system value across multiple audience types:
- **Audience-Specific Content Creation**: Tailored documentation for management (executive summaries, ROI focus), technical staff (architecture guides, integration details), and operations (quick starts, practical examples)
- **Value Proposition Articulation**: Transform technical capabilities into quantified business outcomes (cost savings, productivity gains, quality improvements, strategic advantages)
- **Multi-Format Production**: Executive presentations (board-ready with financial lens), onboarding packages (5-8 documents <60 min), demo scripts, quick reference guides
- **Knowledge Transfer Design**: Progressive disclosure workflows (5-min overviews → 30-min deep dives → hands-on practice)
- **Real Metrics Integration**: Extract concrete outcomes from SYSTEM_STATE.md (no generic placeholders) - Phase 107 quality (92.8/100), Phase 75 M365 ROI ($9-12K), Phase 42 DevOps (653% ROI)
- **Publishing Ready**: Confluence-formatted content, presentation decks with speaker notes, maintenance guidance included

### **Phase 61 Confluence Organization Agent** ⭐ **PREVIOUS ENHANCEMENT**
The Confluence Organization Agent provides intelligent Confluence space management with automated content analysis and interactive placement decisions:
- **Intelligent Space Analysis**: Complete space hierarchy scanning with content analysis, gap detection, and organizational pattern recognition
- **Interactive Content Placement**: AI-powered placement suggestions with confidence scoring and reasoning for optimal content organization
- **Smart Folder Creation**: Automated creation of logical folder hierarchies based on content analysis and user preferences
- **Space Audit Capabilities**: Comprehensive organizational assessment with improvement recommendations and cleanup strategies
- **Production Integration**: Uses existing SRE-grade `reliable_confluence_client.py` with enhanced API reliability and proper empty query handling
- **User Learning**: Adapts to organizational preferences over time for consistent, intelligent content management across sessions

### **Phase 42 DevOps/SRE Agent Ecosystem** ⭐ **PREVIOUS ENHANCEMENT**
The enterprise DevOps and SRE agent ecosystem provides specialized expertise for cloud engineering teams:
- **DevOps Principal Architect Agent**: Enterprise CI/CD architecture, infrastructure automation, container orchestration, and cloud platform design expertise
- **SRE Principal Engineer Agent**: Site reliability engineering with SLA/SLI/SLO design, incident response automation, performance optimization, and chaos engineering
- **Enterprise Integration Framework**: Specialized knowledge for GitHub Enterprise, Terraform Cloud, Kubernetes, and monitoring systems integration
- **Strategic Intelligence Positioning**: Agents designed for hybrid intelligence strategy delivering 653% ROI through architectural guidance rather than task automation

### **Phase 75 Microsoft 365 Integration Agent** ⭐ **LATEST ENHANCEMENT - ENTERPRISE M365**
The Microsoft 365 Integration Agent provides enterprise-grade M365 automation using official Microsoft Graph SDK with local LLM intelligence:
- **Official Microsoft Graph SDK**: Enterprise-grade M365 integration (Outlook, Teams, Calendar) with Azure AD OAuth2 authentication
- **99.3% Cost Savings via Local LLMs**: CodeLlama 13B for technical content, StarCoder2 15B for security, Llama 3B for simple tasks
- **Zero Cloud Transmission**: 100% local processing for sensitive Orro Group content with Western models only (no DeepSeek)
- **Hybrid Intelligence Routing**: Local LLMs for analysis (99.3% savings), Gemini Pro for large context (58.3% savings), Sonnet for strategic
- **Enterprise Security**: AES-256 encrypted credentials, read-only mode, SOC2/ISO27001 compliance, complete audit trails
- **Engineering Manager Value**: 2.5-3 hours/week productivity gains, $9,000-12,000 annual value, enterprise-grade portfolio demonstration

### **Phase 24A Microsoft Teams Intelligence** ⭐ **FOUNDATION ENHANCEMENT**
The Microsoft Teams Meeting Intelligence system (now enhanced by M365 Integration Agent):
- **Enterprise Meeting Automation**: Automated action item extraction and meeting intelligence processing
- **Multi-LLM Cost Optimization**: 58.3% cost savings via Gemini Pro routing for transcript analysis
- **M365 Agent Integration**: Full coordination with Microsoft 365 Integration Agent for comprehensive workflows
- **Professional Productivity**: 2.5-3 hours/week time savings for Engineering Manager workflows

### **Phase 39 Multi-Collection RAG Integration** ⭐ **FOUNDATIONAL ENHANCEMENT**
All agents now benefit from the **Multi-Collection RAG Architecture**:
- **Email Intelligence Access**: Agents can search email history through dedicated email_archive collection with semantic understanding
- **Cross-Source Queries**: Unified search across documents, emails, and knowledge bases for comprehensive intelligence
- **Intelligent Query Routing**: Automatic selection of optimal collections based on query content and agent specialization
- **Real-Time Email Search**: Sub-second email queries replacing external API calls with local vector search
- **Scalable Knowledge Base**: Architecture supports 25,000+ emails and documents with maintained performance

### **Phase 21 Learning Integration** ⭐ **FOUNDATIONAL ENHANCEMENT**
All agents now benefit from the **Contextual Memory & Learning System**:
- **Learned Preferences**: Agents access user preferences learned from previous interactions (70% overall confidence)
- **Behavioral Adaptation**: Agent workflows adapt to user decision-making patterns (7 patterns identified)
- **Cross-Session Memory**: Agents remember user context and preferences across sessions (95% retention)
- **Feedback Integration**: Agent recommendations improve from user feedback (4.44/5.0 satisfaction)
- **Personalized Operations**: Agent outputs are personalized based on learned patterns (40% learning weight)

This transforms all agents from stateless automation to adaptive, learning-enhanced intelligence.

## Active Agents

### Cocktail Mixologist Agent ⭐ **NEW - BEVERAGE & HOSPITALITY SPECIALIST**
**Location**: `claude/agents/cocktail_mixologist_agent.md`
- **Purpose**: Expert cocktail mixologist and beverage consultant providing classic and contemporary cocktail recipes, mixology techniques, and hospitality guidance
- **Specialties**: Classic cocktails (IBA official recipes), modern mixology (molecular techniques, craft cocktails), spirits knowledge (whiskey, gin, rum, vodka, tequila, liqueurs), techniques (shaking, stirring, muddling, layering, infusions), flavor profiles and ingredient pairing, dietary accommodations (mocktails, low-alcohol options)
- **Key Commands**: provide_cocktail_recipe, recommend_cocktail_by_occasion, teach_mixology_technique, suggest_by_available_ingredients, create_custom_variation, explain_cocktail_history, design_cocktail_menu, provide_allergen_safe_alternatives
- **Integration**: Personal Assistant (event planning, shopping lists), Holiday Research Agent (destination-specific drinks), Perth Restaurant Discovery (local cocktail scene)
- **Response Format**: Structured recipes with precise measurements, technique explanations, difficulty levels, tasting notes, pro tips, safety reminders
- **Value Proposition**: Educational cocktail guidance, occasion-based recommendations, ingredient substitution intelligence, responsible consumption emphasis, home bartending skill development

### Governance Policy Engine Agent ⭐ **NEW - PHASE 5 ML-ENHANCED GOVERNANCE**
**Location**: `claude/agents/governance_policy_engine_agent.md`
**Specialization**: ML-enhanced repository governance with adaptive learning capabilities
- **Advanced Pattern Recognition**: ML-based violation detection and predictive policy violations using RandomForest and IsolationForest models
- **Adaptive Policy Management**: YAML-based policy configuration with ML-driven recommendations and effectiveness scoring  
- **Integration Intelligence**: Seamless coordination with existing governance infrastructure (analyzer, monitor, remediation, dashboard)
- **Local ML Execution**: 99.3% cost savings through local model training and inference with lightweight ML approach
- **Real-Time Governance**: Continuous policy evaluation and adaptive updates based on violation history patterns

### Service Desk Manager Agent ⭐ **NEW - PHASE 95 ESCALATION & ROOT CAUSE ANALYSIS**
**Location**: `claude/agents/service_desk_manager_agent.md`
- **Purpose**: Operational Service Desk Manager for Orro, designed to rapidly analyze customer complaints, identify root causes, detect escalation patterns, and provide actionable recommendations for service improvement
- **Specialties**: Customer complaint management, escalation intelligence, root cause analysis (5-Whys), workflow bottleneck detection, process efficiency optimization, staff performance analysis, predictive escalation modeling
- **Key Commands**: analyze_customer_complaints, analyze_escalation_patterns, detect_workflow_bottlenecks, run_root_cause_analysis, predict_escalation_risk, generate_improvement_roadmap, urgent_escalation_triage, complaint_recovery_plan
- **Integration**: Escalation Intelligence FOB (handoff analysis, trigger detection, prediction), Core Analytics FOB (ticket metrics, SLA tracking), Temporal Analytics FOB (time patterns), Client Intelligence FOB (account analysis), SRE/SOE/Azure agents (technical escalations)
- **Escalation Framework**: Risk scoring (0-100), severity classification (P1-P4), efficiency scoring (0-100 with A-F grades), 5-step complaint resolution process
- **Value Proposition**: <15min complaint response, <1hr root cause analysis, >90% customer recovery, 15% escalation rate reduction, 25% resolution time improvement, 15-20% team productivity gains

### Technical Recruitment Agent ⭐ **NEW - PHASE 94 MSP/CLOUD TECHNICAL HIRING**
**Location**: `claude/agents/technical_recruitment_agent.md`
- **Purpose**: AI-augmented recruitment specialist for Orro MSP/Cloud technical roles, designed to rapidly screen and evaluate candidates across cloud infrastructure, endpoint management, networking, and modern workplace specializations
- **Specialties**: MSP/Cloud technical assessment (Azure, M365, Intune, networking, security), role-specific evaluation (Service Desk, SOE, Azure Engineers), certification validation, technical skill depth analysis, MSP cultural fit assessment, rapid CV screening (<5 min vs 20-30 min manual)
- **Key Commands**: screen_technical_cv, batch_cv_screening, technical_skill_validation, evaluate_service_desk_candidate, evaluate_soe_specialist, evaluate_azure_engineer, evaluate_m365_specialist, certification_verification_assessment, generate_candidate_scorecard, interview_question_generator
- **Integration**: SOE Principal Engineer (endpoint validation), SRE Principal Engineer (infrastructure assessment), DevOps Principal Architect (automation validation), Principal IDAM Engineer (identity assessment), Cloud Security Principal (security validation), Azure Architect (cloud architecture), Interview Prep Professional (question generation), Engineering Manager Mentor (hiring strategy)
- **Orro Technical Scoring**: 100-point framework (Technical Skills 40pts, Certifications 20pts, MSP Experience 20pts, Experience Quality 10pts, Cultural Fit 10pts) with structured scorecards and red flag detection
- **Value Proposition**: Sub-5-minute CV screening, 15-20 hours saved per open role, 70%+ interview success rate, 85%+ placement success, consistent technical evaluation, faster time-to-hire

### Senior Construction Recruitment Agent ⭐ **PREVIOUS - AI-AUGMENTED RECRUITMENT SPECIALIST**
**Location**: `claude/agents/senior_construction_recruitment_agent.md`
- **Purpose**: AI-augmented recruitment operations specialist for construction industry senior leadership positions, designed to scale small team capabilities through intelligent automation and deep industry expertise
- **Specialties**: Construction industry intelligence (head constructors, project coordinators, project managers, CFO roles), AI-powered sourcing and matching, predictive candidate success modeling, automated screening workflows, operational scaling for small teams
- **Key Commands**: ai_candidate_sourcing_automation, intelligent_candidate_matching, analyze_construction_cv_intelligence, predict_candidate_success_probability, automate_screening_workflow, ai_interview_optimization, scale_recruitment_operations, create_ai_enhanced_recruitment_strategy
- **Integration**: Company Research Agent (client intelligence), LinkedIn AI Advisor Agent (network analysis), Personal Assistant Agent (client management), Data Analyst Agent (recruitment metrics), construction industry platforms, ATS systems
- **Value Proposition**: Transform construction recruitment through AI automation - 10x candidate processing capacity, 80% time reduction on routine tasks, 5x pipeline capacity for small teams, predictive success modeling for higher placement rates

### Microsoft 365 Integration Agent ⭐ **NEW - PHASE 75 ENTERPRISE M365**
**Location**: `claude/agents/microsoft_365_integration_agent.md`
- **Purpose**: Enterprise-grade Microsoft 365 automation using official Graph SDK with local LLM intelligence for cost optimization and privacy
- **Specialties**: Outlook/Exchange email operations, Teams meeting intelligence, Calendar automation, **99.3% cost savings via local LLMs**, zero cloud transmission for sensitive content
- **Key Commands**: m365_intelligent_email_triage, m365_teams_meeting_intelligence, m365_smart_scheduling, m365_draft_professional_email, m365_channel_content_analysis, m365_automated_teams_summary
- **Integration**: Official Microsoft Graph SDK, Azure AD OAuth2, CodeLlama 13B (technical), StarCoder2 15B (security), Llama 3B (lightweight), Gemini Pro (large context), existing Teams intelligence
- **Local LLM Strategy**: CodeLlama 13B for email drafting and technical content (99.3% savings), StarCoder2 15B for security/compliance (Western model), Llama 3B for categorization (99.7% savings), local processing for Orro Group client data
- **Enterprise Security**: AES-256 encrypted credentials via mcp_env_manager, read-only mode, SOC2/ISO27001 compliance, complete audit trails, Western models only (no DeepSeek exposure)
- **Value Proposition**: 2.5-3 hours/week productivity gains, $9,000-12,000 annual value for Engineering Manager workflows, enterprise-grade portfolio demonstration

### Jobs Agent
**Location**: `claude/agents/jobs_agent.md`
- **Purpose**: Comprehensive job opportunity analysis and application management
- **Specialties**: Email processing, job scraping, AI-powered scoring, application strategy
- **Key Commands**: complete_job_analyzer, automated_job_scraper, intelligent_job_filter
- **Integration**: Gmail, LinkedIn, Seek.com.au, market intelligence

### LinkedIn Optimizer Agent
**Location**: `claude/agents/linkedin_optimizer.md`
- **Purpose**: LinkedIn profile optimization and professional networking
- **Specialties**: Profile optimization, keyword strategy, content strategy, network analysis
- **Key Commands**: optimize_profile, keyword_analysis, content_strategy, network_audit
- **Integration**: LinkedIn API, market research, personal branding

### Security Specialist Agent ⭐ **ENHANCED - Phase 15 Enterprise Ready**
**Location**: `claude/agents/security_specialist.md`
- **Purpose**: Enterprise-grade security analysis, automated hardening, and compliance management
- **Specialties**: Code security review, Azure cloud security, enterprise compliance, **automated vulnerability remediation**, **SOC2/ISO27001 compliance tracking**
- **Key Commands**: security_review, vulnerability_scan, compliance_check, azure_security_audit, **automated_security_hardening**, **enterprise_compliance_audit**
- **New Capabilities**:
  - **Zero Critical Vulnerabilities**: 100% elimination of high-severity findings through automated hardening
  - **Continuous Monitoring**: 24/7 security scanning with intelligent alerting and reporting
  - **Enterprise Compliance**: SOC2 & ISO27001 compliance tracking with 100% achievement score
  - **AI Security**: Prompt injection defense for web operations with 29 threat pattern detection
  - **Production Security**: 285-tool ecosystem secured for enterprise deployment with audit readiness

### Azure Architect Agent
**Location**: `claude/agents/azure_architect_agent.md`
- **Purpose**: Azure cloud architecture, optimization, and enterprise compliance
- **Specialties**: Well-Architected Framework, cost optimization, IaC generation, migration planning
- **Key Commands**: analyze_azure_architecture, cost_optimization_analysis, security_posture_assessment, migration_assessment
- **Integration**: Azure APIs, Terraform, compliance frameworks

### DevOps Principal Architect Agent ⭐ **NEW - PHASE 42 ENTERPRISE SPECIALIST**
**Location**: `claude/agents/devops_principal_architect_agent.md`
- **Purpose**: Advanced DevOps architecture specialist for enterprise-scale infrastructure automation, CI/CD optimization, and cloud-native system design for 30+ engineer teams
- **Specialties**: Enterprise CI/CD architecture (GitLab, Jenkins, GitHub Actions), Infrastructure as Code mastery (Terraform, OpenTofu, Pulumi), container orchestration (Kubernetes, Docker, Helm), monitoring & observability (Prometheus, Grafana, ELK Stack), security integration (DevSecOps, SAST/DAST)
- **Key Commands**: architect_devops_pipeline, optimize_infrastructure_deployment, design_monitoring_strategy, evaluate_devops_toolchain, assess_deployment_architecture, design_gitops_workflow
- **Integration**: Enterprise deployment analysis, cost optimization with FinOps, compliance automation (SOC2/ISO27001), team scaling patterns, AI-enhanced automation
- **Enterprise Capabilities**: Multi-cloud strategy, platform engineering, reliability engineering, performance optimization, C-level communication

### SRE Principal Engineer Agent ⭐ **NEW - PHASE 42 RELIABILITY SPECIALIST**
**Location**: `claude/agents/sre_principal_engineer_agent.md`
- **Purpose**: Site Reliability Engineering specialist focused on production system reliability, incident response automation, and performance optimization for large-scale distributed systems
- **Specialties**: Reliability engineering (SLA/SLI/SLO design, error budget management), incident response (automated detection, root cause analysis, post-mortem analysis), performance optimization (latency reduction, throughput optimization, capacity planning), chaos engineering (fault injection, resilience testing), production operations (change management, deployment safety)
- **Key Commands**: design_reliability_architecture, automate_incident_response, optimize_system_performance, implement_chaos_engineering, design_monitoring_alerting, conduct_postmortem_analysis
- **Integration**: DevOps Principal Architect (infrastructure reliability), Security Specialist (incident response), Azure Architect (cloud reliability patterns), AI-powered analysis and automated remediation
- **Advanced Capabilities**: Large-scale systems experience, microservices reliability, database reliability, network reliability, compliance operations (SOC2/ISO27001)

### Principal Endpoint Engineer Agent ⭐ **NEW - ENDPOINT MANAGEMENT SPECIALIST**
**Location**: `claude/agents/principal_endpoint_engineer_agent.md`
- **Purpose**: Enterprise endpoint architecture and security specialist for designing and optimizing endpoint management strategies across diverse device ecosystems
- **Specialties**: Endpoint management platforms (Intune, SCCM, Workspace ONE, Tanium), zero trust security implementation, device lifecycle management, modern workplace engineering (Autopilot, DEP), endpoint protection (EDR/XDR), compliance enforcement
- **Key Commands**: endpoint_architecture_assessment, zero_trust_roadmap, platform_migration_strategy, autopilot_deployment_design, compliance_policy_framework, endpoint_health_diagnostic
- **Integration**: Cloud Security Principal (security architecture), SOE Principal Engineer (operating environment), Azure Architect (identity and infrastructure), Security Specialist (threat response)
- **Advanced Capabilities**: 10,000+ endpoint scalability, multi-platform management (Windows, macOS, iOS, Android, Linux), predictive analytics, AI-powered security, automated incident response

### Principal IDAM Engineer Agent ⭐ **NEW - IDENTITY & ACCESS MANAGEMENT SPECIALIST**
**Location**: `claude/agents/principal_idam_engineer_agent.md`
- **Purpose**: Enterprise identity and access management architecture specialist for designing and implementing comprehensive IAM strategies across hybrid and multi-cloud environments
- **Specialties**: Identity platforms (Azure AD/Entra ID, Okta, Ping, ForgeRock), zero trust identity, privileged access management (CyberArk, BeyondTrust), identity governance (SailPoint, Saviynt), modern authentication (OAuth, OIDC, SAML, FIDO2)
- **Key Commands**: idam_architecture_assessment, zero_trust_identity_roadmap, sso_implementation_design, pam_solution_architecture, identity_governance_framework, identity_security_assessment
- **Integration**: Cloud Security Principal (security architecture), Principal Endpoint Engineer (device identity), Azure Architect (Azure AD/Entra ID), Security Specialist (threat response), DevOps Principal Architect (secrets management)
- **Advanced Capabilities**: 100,000+ identity scalability, passwordless authentication, decentralized identity, behavioral analytics, continuous adaptive trust, quantum-safe cryptography readiness

### Prompt Engineer Agent
**Location**: `claude/agents/prompt_engineer_agent.md`
- **Purpose**: Advanced prompt design, optimization, and engineering
- **Specialties**: Prompt analysis, weakness identification, systematic optimization, A/B testing
- **Key Commands**: analyze_prompt, optimize_prompt, prompt_templates, test_prompt_variations
- **Integration**: Natural language interface design, AI interaction patterns, business communication

### Company Research Agent
**Location**: `claude/agents/company_research_agent.md`
- **Purpose**: Deep-dive company intelligence gathering for job applications and interviews
- **Specialties**: Company analysis, cultural assessment, strategic intelligence, leadership profiling
- **Key Commands**: deep_company_research, quick_company_profile, interview_prep_research, company_culture_analysis
- **Integration**: Jobs Agent enhancement, LinkedIn optimization, interview preparation

### Interview Prep Professional Agent
**Location**: `claude/agents/interview_prep_agent.md`
- **Purpose**: Specialized interview coaching and preparation for senior technology leadership roles
- **Specialties**: Behavioral coaching, technical leadership discussions, multi-stakeholder strategy, mock interviews
- **Key Commands**: interview_strategy_session, behavioral_coaching, technical_interview_prep, mock_interview_session
- **Integration**: Company Research Agent intelligence, career experience database, role-specific positioning

### Holiday Research Agent
**Location**: `claude/agents/holiday_research_agent.md`
- **Purpose**: Comprehensive holiday research and travel planning specializing in destination analysis and logistics
- **Specialties**: Destination research, travel logistics, itinerary planning, seasonal analysis, budget optimization
- **Key Commands**: destination_analysis, seasonal_travel_planner, comprehensive_itinerary, cultural_immersion_planner
- **Integration**: Web research, weather APIs, travel sites, maps integration, currency tools

### Travel Monitor & Alert Agent
**Location**: `claude/agents/travel_monitor_alert_agent.md`
- **Purpose**: Real-time travel price monitoring and intelligent alert system for both cash fares and frequent flyer awards
- **Specialties**: Cash fare tracking, award space monitoring, cross-reference analysis, intelligent alerting, seasonal intelligence
- **Key Commands**: track_route_pricing, award_availability_tracker, value_comparison_engine, booking_window_optimizer
- **Integration**: Flight search engines, airline direct sites, award search tools, alert delivery channels

### Perth Restaurant Discovery Agent ⭐ **NEW - LOCAL INTELLIGENCE SPECIALIST**
**Location**: `claude/agents/perth_restaurant_discovery_agent.md`
- **Purpose**: Specialized agent for discovering exceptional dining experiences specifically in Perth, Western Australia with local expertise and real-time intelligence
- **Specialties**: Real-time availability tracking, social media intelligence, Perth neighborhood expertise, hidden gem discovery, seasonal menu analysis, booking strategy optimization
- **Key Commands**: discover_perth_restaurants, analyze_restaurant_availability, perth_neighborhood_dining_guide, track_perth_restaurant_specials, perth_seasonal_dining_recommendations
- **Integration**: Booking platforms (OpenTable, Resy), social media monitoring, Perth event calendar, weather service, local transport systems
- **Local Intelligence**: 300+ Perth restaurants, neighborhood cultural context, parking/transport logistics, Perth dining customs and timing
- **Performance**: 98%+ menu accuracy, 85%+ booking success rate, distinctly Perth dining experiences

### Token Optimization Agent
**Location**: `claude/agents/token_optimization_agent.md`
- **Purpose**: Systematic identification and implementation of token cost reduction strategies while maintaining quality
- **Specialties**: Usage analysis, local tool substitution, template generation, preprocessing pipelines, ROI optimization
- **Key Commands**: analyze_token_usage, identify_optimization_opportunities, implement_local_tools, measure_optimization_roi
- **Integration**: Security toolkit, template systems, batch processing, performance monitoring

### AI Specialists Agent
**Location**: `claude/agents/ai_specialists_agent.md`
- **Purpose**: Meta-agent specialized in analyzing, optimizing, and evolving Maia's AI agent ecosystem and processes
- **Specialties**: Agent architecture analysis, workflow optimization, agent design patterns, performance monitoring, system intelligence
- **Key Commands**: analyze_agent_ecosystem, optimize_workflow_performance, design_new_agent, agent_performance_audit
- **Integration**: All agents (meta-analysis), orchestration framework, system metrics, continuous improvement cycles

### LinkedIn AI Advisor Agent ⭐ **ENHANCED - Phase 30 Production Integration**
**Location**: `claude/agents/linkedin_ai_advisor_agent.md`
- **Purpose**: AI/Automation leadership positioning and LinkedIn strategy for professional transformation **with automated daily content generation**
- **Specialties**: AI thought leadership, technical-business bridging, AI community networking, content strategy for AI expertise, **network-aware content automation**, **7-day thematic content strategy**
- **Key Commands**: ai_leadership_rebrand, maia_case_study_content, ai_thought_leadership_content, ai_community_networking, ai_speaking_opportunities, **daily_linkedin_content_generation**
- **Integration**: **✅ PRODUCTION INTEGRATED** - Morning briefing system, RSS intelligence feeds, 1,135 LinkedIn network analysis, Microsoft/MSP contact targeting
- **Enhanced Capabilities**:
  - **Network Intelligence**: Leverages 8 Microsoft contacts, 90+ MSP contacts for strategic content targeting
  - **Daily Automation**: 7:30 AM automated content ideas via morning briefing system
  - **RSS Intelligence Integration**: Content themes derived from 14 premium industry sources
  - **Perth Market Positioning**: Azure Extended Zone market leadership content strategy
  - **Professional ROI**: 5-10 minutes daily content ideation time savings with strategic network optimization

### Personal Assistant Agent ⭐ **ENHANCED - PHASE 82 TRELLO INTEGRATION**
**Location**: `claude/agents/personal_assistant_agent.md`
- **Purpose**: **ENHANCED** - Now serves as central coordinator for the intelligent assistant hub with Trello workflow intelligence
- **Specialties**: Daily scheduling, communication management, task orchestration, **Trello workflow intelligence**, travel coordination, strategic productivity optimization, **multi-agent workflow coordination**
- **Key Commands**: daily_executive_briefing, intelligent_email_management, comprehensive_calendar_optimization, travel_logistics_coordinator, **trello_workflow_intelligence**, **intelligent_assistant_orchestration**
- **Trello Integration** (Phase 82): Board organization, card prioritization, deadline management, workflow analysis via `trello_fast.py`
- **Integration**: **Central hub** - Coordinates all Maia agents via message bus with real-time communication and context enrichment, Trello Fast API client
- **Design Philosophy**: Following UFC "do one thing well" - integrated Trello capabilities rather than creating dedicated agent (validate demand first)
- **New Capabilities**: Intelligent request routing, agent performance monitoring, workflow optimization, Trello board management

### Financial Advisor Agent ⭐ **NEW**
**Location**: `claude/agents/financial_advisor_agent.md`
- **Purpose**: Comprehensive financial advisory services for Australian high-income earners with real-time market integration
- **Specialties**: Investment analysis, Australian tax optimization, superannuation strategy, property investment, risk management, **knowledge graph integration**
- **Key Commands**: comprehensive_financial_health_checkup, australian_tax_optimization_strategy, investment_portfolio_analysis, superannuation_strategy_optimizer, australian_property_investment_analyzer
- **Integration**: Financial Planner Agent (strategic coordination), Personal Assistant (financial review scheduling), **Personal Knowledge Graph (pattern learning)**, market data sources
- **System Integration**: Full message bus communication, context preservation with reasoning chains

### Financial Planner Agent ⭐ **NEW**
**Location**: `claude/agents/financial_planner_agent.md`
- **Purpose**: Strategic long-term financial planning and life goal coordination with AI-driven insights
- **Specialties**: Life-centered financial strategy, multi-generational planning, major life transition management, estate planning, retirement lifestyle design, **predictive financial modeling**
- **Key Commands**: life_financial_masterplan, major_life_event_planner, scenario_planning_engine, education_funding_architect
- **Integration**: Financial Advisor Agent (tactical implementation), Personal Assistant (life planning sessions), Jobs Agent (career transitions), **Knowledge Graph (life pattern analysis)**
- **System Integration**: Enhanced context management, quality feedback loops, performance analytics

### Team Knowledge Sharing Agent ⭐ **NEW - PHASE 108 TEAM ONBOARDING SPECIALIST**
**Location**: `claude/agents/team_knowledge_sharing_agent.md`
- **Purpose**: Create compelling team onboarding materials, documentation, and presentations demonstrating AI system value across multiple audience types
- **Specialties**: Audience-specific content creation (management/technical/operations), value proposition articulation with quantified metrics, multi-format production (presentations, onboarding packages, demo scripts), knowledge transfer design (progressive disclosure workflows)
- **Key Commands**: create_team_onboarding_package, create_stakeholder_presentation, create_quick_reference_guide, create_demo_script, create_case_study_showcase
- **Integration**: Confluence Organization Agent (publishing), Blog Writer Agent (content repurposing), LinkedIn AI Advisor (external positioning), UI Systems Agent (presentation design)
- **Real Metrics**: Extracts concrete outcomes from SYSTEM_STATE.md - Phase 107 quality (92.8/100), Phase 75 M365 ROI ($9-12K), Phase 42 DevOps (653% ROI)
- **Performance**: <60 min for complete onboarding package (5-8 documents), >90% audience comprehension in <15 min, 100% publishing-ready content

### Blog Writer Agent ⭐ **NEW**
**Location**: `claude/agents/blog_writer_agent.md`
- **Purpose**: Specialized technical thought leadership and content strategy for business technology professionals and AI implementation leaders
- **Specialties**: Technical thought leadership, case study development, tutorial creation, industry analysis, Maia system showcase, **SEO content strategy**
- **Key Commands**: create_technical_blog_post, develop_case_study, industry_analysis_blog, maia_showcase_series, cross_platform_content_strategy
- **Integration**: LinkedIn AI Advisor Agent (content amplification), Company Research Agent (industry intelligence), Personal Assistant (scheduling and tracking), **Knowledge Graph (expertise positioning)**, **Team Knowledge Sharing Agent (internal to external content transformation)**
- **System Integration**: Message bus communication, enhanced context preservation, A/B testing framework, professional positioning optimization

### Product Designer Agent ⭐ **NEW - HYBRID DESIGN ARCHITECTURE**
**Location**: `claude/agents/product_designer_agent.md`
- **Purpose**: Primary design agent providing comprehensive UI/UX design capabilities for web and application interfaces, coordinating with specialist agents for deep expertise
- **Specialties**: Visual design, user experience design, design systems, prototyping, responsive design, accessibility compliance, design strategy integration
- **Key Commands**: design_interface_wireframes, design_user_flows, create_design_mockups, design_responsive_layouts, analyze_design_usability, create_design_presentation
- **Integration**: **UX Research Agent** (research coordination), **UI Systems Agent** (system architecture), Blog Writer Agent (design content), Personal Assistant (project coordination)
- **Hybrid Architecture**: Handles 80% of design workflows independently while escalating to specialists for advanced research and system-level requirements

### UX Research Agent ⭐ **NEW - RESEARCH SPECIALIST**
**Location**: `claude/agents/ux_research_agent.md`
- **Purpose**: Specialist agent focused on comprehensive user experience research, usability analysis, and data-driven design validation
- **Specialties**: User research methodologies, usability analysis, behavioral psychology, accessibility auditing, information architecture, analytics integration
- **Key Commands**: design_research_study, conduct_usability_testing, analyze_user_interviews, perform_accessibility_audit, map_user_journeys, synthesize_research_findings
- **Integration**: **Product Designer Agent** (research-informed design), Company Research Agent (competitive UX analysis), Personal Assistant (research scheduling)
- **Advanced Capabilities**: Statistical analysis, A/B testing, cross-platform research, WCAG 2.1 AAA compliance, behavioral analytics

### UI Systems Agent ⭐ **NEW - SYSTEMS SPECIALIST**
**Location**: `claude/agents/ui_systems_agent.md`
- **Purpose**: Advanced specialist focused on design systems architecture, visual design excellence, and component library development
- **Specialties**: Design systems architecture, advanced visual design, component engineering, system governance, brand implementation, multi-platform consistency
- **Key Commands**: architect_design_system, develop_component_library, create_design_tokens, design_brand_system, develop_visual_language, audit_design_consistency
- **Integration**: **Product Designer Agent** (system implementation), **UX Research Agent** (component validation), Security Specialist (system security), Azure Architect (system deployment)
- **Advanced Capabilities**: Atomic design methodology, performance optimization, accessibility-first architecture, cross-platform component systems

## Agent Selection & Intelligent Routing ⭐ **ENHANCED**
Maia's **Intelligent Assistant Hub** automatically selects and coordinates agents based on:
- **ML-driven intent analysis** and request classification
- Required domain expertise and agent capabilities
- **Knowledge graph insights** for context-aware routing
- Previous interaction patterns and success rates
- **Real-time agent availability** and workload balancing

## Enhanced Usage Patterns
- **Explicit Invocation**: "Use the jobs agent to analyze my latest opportunities"
- **Implicit Selection**: "Optimize my LinkedIn profile" → LinkedIn Optimizer Agent
- **Intelligent Routing**: "Plan my financial future and career transition" → **Multi-agent coordination** (Financial Advisor + Jobs Agent + LinkedIn AI Advisor)
- **Context-Aware Orchestration**: Agents share enriched context via **knowledge graph integration**
- **Real-Time Coordination**: **Message bus communication** for streaming data and progress updates

## Enhanced Multi-Agent Ecosystem Integration ⭐ **UPGRADED**
All agents participate in the **coordinated ecosystem** with advanced capabilities:

### Advanced Commands Available
- `complete_application_pipeline` - End-to-end job application workflow (6 agents)
- `professional_brand_optimization` - Comprehensive brand building (5 agents)
- `market_intelligence_report` - Multi-source market analysis (4 agents)
- **`intelligent_assistant_orchestration`** - Dynamic multi-agent workflows with real-time coordination
- **`virtual_security_operations`** - **NEW** - Complete Virtual Security Assistant workflow (proactive threat intelligence + alert management + automated response)
- **`orro_security_incident_response`** - **NEW** - Orro Group specific security incident management with playbook automation
- **`executive_security_briefing`** - **NEW** - Strategic security briefing with threat predictions and business impact analysis
- **`design_simple_interface`** - Single-agent interface design workflow (Product Designer)
- **`design_research_validated_interface`** - Research-informed design workflow (Product Designer + UX Research)
- **`design_systematic_interface`** - System-level design workflow (Product Designer + UI Systems)
- **`comprehensive_design_solution`** - Full design project workflow (all 3 design agents)
- **`comprehensive_data_analysis`** - **NEW** - Complete operational data analysis workflow (Data Analyst Agent)
- **`operational_intelligence_briefing`** - **NEW** - Executive operational intelligence with multi-agent insights (Data Analyst + Personal Assistant)
- **`data_preparation_to_analysis_pipeline`** - **NEW** - End-to-end data preparation → analysis → visualization (Data Cleaning + Data Analyst + UI Systems)
- **`etl_orchestration_with_monitoring`** - **NEW** - Scheduled ETL with health monitoring (Data Cleaning + Personal Assistant + Data Analyst)
- **`ai_recruitment_operations_pipeline`** - **NEW** - Complete AI-augmented recruitment workflow (Senior Construction Recruitment + Company Research + LinkedIn AI Advisor + Data Analyst)
- **`construction_talent_acquisition_strategy`** - **NEW** - End-to-end construction industry recruitment strategy with automation (Senior Construction Recruitment + Company Research + Personal Assistant)

### Enhanced Agent Communication Protocols ⭐ **TRANSFORMED**
- **Data Flow**: **Real-time message bus** communication replacing JSON handoffs
- **Context Sharing**: **Enhanced context manager** with 95% retention and reasoning chains
- **Error Handling**: **Intelligent error classification** and automatic recovery strategies
- **Quality Gates**: **ML-driven validation** with confidence scoring and feedback loops
- **Performance Monitoring**: **Real-time analytics** and optimization recommendations

## Cloud Practice Agents ⭐ **NEW** - Orro Group Support

### FinOps Engineering Agent
**Location**: `claude/agents/finops_engineering_agent.md`
- **Purpose**: Cloud financial optimization specialist addressing critical FinOps skills shortage
- **Specialties**: Multi-cloud cost analysis, rightsizing, financial governance, ROI analysis, compliance controls
- **Key Commands**: cloud_cost_analysis, rightsizing_recommendations, reserved_instance_strategy, multi_cloud_cost_comparison, finops_dashboard_design, cloud_budget_forecasting
- **Integration**: Azure Cost Management, AWS Cost Intelligence, GCP Financial Management, executive reporting automation
- **Value Proposition**: 15-30% cost reduction, immediate client ROI, addresses #1 enterprise pain point

### Virtual Security Assistant Agent ⭐ **NEW - PHASE 2 COMPLETE - AGENTIC SOC REVOLUTION**
**Location**: `claude/agents/virtual_security_assistant_agent.md`
- **Purpose**: Next-generation SOC assistant providing proactive threat intelligence, automated response orchestration, and intelligent alert management. Transforms reactive security operations into predictive, automated defense.
- **Specialties**: Proactive threat anticipation (behavioral analytics, threat prediction), intelligent alert management (50-70% fatigue reduction), automated response orchestration (80% MTTR reduction), Orro Group specific playbooks
- **Key Commands**: virtual_security_briefing, anticipate_emerging_threats, intelligent_alert_processing, automated_threat_response, security_effectiveness_analysis, threat_hunting_automation
- **Integration**: **COMPLETE INFRASTRUCTURE** - Security Integration Hub, 16 alert sources, 8 Orro playbooks, real-time dashboard, existing Maia security tools (19+ tools)
- **Value Proposition**: **REVOLUTIONARY IMPACT** - 50-70% alert fatigue reduction, 80% faster threat response, 60% increase in early detection, 40% SOC productivity improvement
- **Measurable Outcomes**: Alert suppression (automated), threat prediction (ML-driven), response automation (safety-controlled), executive briefings (strategic)

### Cloud Security Principal Agent ⭐ **ENHANCED - Phase 15 Enterprise Security**
**Location**: `claude/agents/cloud_security_principal_agent.md`
- **Purpose**: Strategic cloud security leadership with zero-trust architecture and Australian compliance expertise, **now enhanced by Virtual Security Assistant automation**
- **Specialties**: Zero-trust architecture, multi-cloud security, ACSC/SOC2/ISO27001 compliance, threat modeling, DevSecOps automation, **automated security hardening**, **continuous compliance monitoring**
- **Key Commands**: cloud_security_posture_assessment, zero_trust_architecture_design, compliance_gap_analysis, threat_modeling_and_analysis, devsecops_integration_strategy, incident_response_planning, **enterprise_security_transformation**, **automated_compliance_reporting**
- **Integration**: Azure Security Center/Sentinel, AWS Security Hub/GuardDuty, GCP Security Command Center, Australian Government requirements, **Virtual Security Assistant coordination**
- **Value Proposition**: Government client focus, enterprise security transformation, critical security+cloud skills shortage, **enhanced by Virtual Security Assistant automation and intelligence**

### SOE Principal Consultant Agent ⭐ **NEW - MSP BUSINESS STRATEGY SPECIALIST**
**Location**: `claude/agents/soe_principal_consultant_agent.md`
- **Purpose**: Strategic technology evaluation and business alignment specialist for MSP environment management platforms, focusing on ROI modeling and competitive positioning
- **Specialties**: Strategic technology evaluation, MSP operational excellence, vendor assessment, competitive positioning, ROI modeling, technology roadmapping, business impact analysis
- **Key Commands**: strategic_technology_evaluation, msp_operational_excellence_analysis, vendor_competitive_assessment, roi_modeling_and_business_case, technology_roadmap_development, business_alignment_strategy
- **Integration**: MSP platform analysis, Confluence documentation, competitive intelligence, cost optimization strategies, client requirement mapping
- **Value Proposition**: MSP client environment management expertise, strategic decision-making support, comprehensive platform evaluation frameworks

### SOE Principal Engineer Agent ⭐ **NEW - MSP TECHNICAL ARCHITECTURE SPECIALIST**
**Location**: `claude/agents/soe_principal_engineer_agent.md`
- **Purpose**: Technical architecture and implementation assessment specialist for MSP platforms, focusing on security, scalability, and integration complexity analysis
- **Specialties**: Technical architecture assessment, security evaluation, scalability engineering, integration complexity analysis, performance optimization, compliance validation, migration planning
- **Key Commands**: technical_architecture_assessment, security_and_compliance_evaluation, scalability_and_performance_analysis, integration_complexity_assessment, migration_strategy_development, technical_risk_evaluation
- **Integration**: Security Specialist Agent (compliance validation), Azure Architect Agent (cloud integration), DevOps Principal Architect (implementation patterns), technical documentation systems
- **Value Proposition**: Deep technical MSP platform expertise, comprehensive security and scalability assessment, enterprise-grade technical evaluation frameworks

### Azure Solutions Architect Agent
**Location**: `claude/agents/azure_solutions_architect_agent.md`
- **Purpose**: Deep Azure expertise leveraging Orro's Microsoft partnership for Well-Architected Framework implementations
- **Specialties**: Azure Well-Architected Framework, enterprise landing zones, hybrid integration, modern app platforms, data analytics
- **Key Commands**: azure_architecture_assessment, azure_landing_zone_design, azure_migration_strategy, azure_cost_optimization_analysis, azure_disaster_recovery_design, azure_security_architecture
- **Integration**: Azure services ecosystem, Microsoft partnership benefits, hybrid cloud patterns, Australian market specialization
- **Value Proposition**: Enhances existing Microsoft strength, enterprise Azure transformations, government compliance

### Principal Cloud Architect Agent
**Location**: `claude/agents/principal_cloud_architect_agent.md`
- **Purpose**: Executive-level cloud architecture leadership for strategic engagements and digital transformation
- **Specialties**: Strategic architecture leadership, multi-cloud architecture, enterprise integration, architectural governance, executive communication
- **Key Commands**: enterprise_architecture_strategy, multi_cloud_architecture_design, technology_evaluation_framework, architecture_governance_design, digital_transformation_roadmap
- **Integration**: All cloud practice agents coordination, C-level communication, strategic decision making, industry specialization
- **Value Proposition**: Strategic client engagements, competitive differentiation, enterprise transformation leadership

### Microsoft Licensing Specialist Agent ⭐ **NEW - LICENSING EXPERTISE**
**Location**: `claude/agents/microsoft_licensing_specialist_agent.md`
- **Purpose**: Deep Microsoft licensing expertise for CSP partner tiers, NCE transitions, and strategic licensing optimization
- **Specialties**: CSP tier 1/2 models, support responsibilities, NCE 2026 changes, compliance management, financial optimization, Azure/M365/Dynamics licensing
- **Key Commands**: analyze_licensing_model, tier1_support_assessment, nce_2026_impact_analysis, compliance_audit_preparation, margin_optimization_strategy, licensing_migration_planning
- **Integration**: Azure Architect Agent (cloud licensing), FinOps Agent (cost optimization), SOE Principal Consultant (MSP licensing strategy), Company Research (competitive intelligence)
- **Value Proposition**: Critical for MSP operations, 2026 NCE preparation, support boundary clarification, compliance risk mitigation, margin optimization strategies

### Confluence Organization Agent ⭐ **NEW - INTELLIGENT SPACE MANAGEMENT SPECIALIST**
**Location**: `claude/agents/confluence_organization_agent.md`
- **Purpose**: Intelligent Confluence space organization and content management specialist providing automated folder management, content analysis, and interactive placement decisions
- **Specialties**: Space hierarchy analysis, intelligent content placement, interactive folder selection, organizational pattern recognition, automated folder creation
- **Key Commands**: scan_confluence_spaces, suggest_content_placement, interactive_folder_selection, create_intelligent_folders, organize_confluence_content, confluence_space_audit
- **Integration**: Reliable Confluence Client (SRE-grade API), RAG document intelligence, personal knowledge graph, preference learning system
- **Advanced Capabilities**: 
  - **Intelligent Space Analysis**: Analyze existing page structures and organizational patterns across all accessible Confluence spaces
  - **Content Analysis**: Understand document types, topics, and relationships for optimal placement suggestions with confidence scoring
  - **Interactive Organization**: Present organized choices for content placement with visual confidence indicators and reasoning
  - **Smart Folder Creation**: Automatically create logical folder hierarchies when needed based on content analysis
  - **User Preference Learning**: Adapt to user organizational preferences over time with cross-session memory
- **Production Value**: **CONFLUENCE ORGANIZATION INTELLIGENCE** - Transform chaotic Confluence spaces into well-structured, navigable knowledge bases with learned organizational patterns
- **Production Status**: ✅ **ACTIVE** - Successfully scanned 9 Confluence spaces with 47 total pages, interactive placement workflow operational

### Data Cleaning & ETL Expert Agent ⭐ **NEW - DATA PREPARATION SPECIALIST**
**Location**: `claude/agents/data_cleaning_etl_expert_agent.md`
- **Purpose**: Specialized agent for data preparation, cleaning, quality assessment, and ETL pipeline design - transforms messy real-world data into analysis-ready datasets with auditable transformations
- **Specialties**: Data profiling & quality assessment, automated cleaning workflows (missing values, duplicates, outliers, standardization), ETL pipeline design, data validation & lineage tracking, business rule enforcement
- **Key Commands**: data_quality_assessment, automated_data_cleaning, etl_pipeline_design, data_profiling_report, data_validation_framework, data_transformation_pipeline, duplicate_detection_resolution, data_lineage_documentation
- **Integration**: **Data Analyst Agent** (cleaning → analysis handoff), Personal Assistant (scheduled ETL), ServiceDesk analytics (ticket cleaning), Cloud Billing intelligence (multi-source integration)
- **Value Proposition**: **90%+ DATA QUALITY IMPROVEMENT** - Automated cleaning eliminates manual effort, 5-10x faster data preparation, reduced analysis errors, audit-ready documentation with complete lineage tracking
- **Production Status**: ✅ **READY FOR IMPLEMENTATION** - Complete specification with 8 key commands and integration patterns

### Data Analyst Agent ⭐ **ENHANCED - SERVICEDESK INTELLIGENCE SPECIALIST WITH FEEDBACK**
**Location**: `claude/agents/data_analyst_agent.md`
- **Purpose**: Specialized agent for comprehensive data analysis, pattern detection, and business intelligence reporting with **ENHANCED ServiceDesk analytics capabilities** including pattern feedback, team coaching, and automation opportunity identification
- **Specialties**: Statistical analysis (descriptive statistics, trend analysis, correlation analysis, time series analysis), pattern detection (anomaly detection, clustering analysis, behavioral patterns), data visualization (interactive charts, dashboards, executive reporting), business intelligence (operational insights, performance metrics, predictive analytics), **ServiceDesk Intelligence** (ticket pattern analysis, automation opportunity identification, team coaching, process optimization with proven $350,460 annual savings methodology)
- **Key Commands**: comprehensive_data_analysis, operational_intelligence_report, trend_analysis_and_forecasting, pattern_detection_analysis, performance_metrics_dashboard, data_quality_assessment, incident_pattern_analysis, resource_utilization_analysis, service_level_analysis, servicedesk_full_analysis, servicedesk_fcr_analysis, servicedesk_documentation_audit, servicedesk_handoff_analysis, servicedesk_executive_briefing, **servicedesk_pattern_feedback**, **servicedesk_team_coaching**, **servicedesk_process_recommendations**, **servicedesk_automation_opportunities**
- **Enhanced Capabilities**:
  - **ServiceDesk Dashboard Expertise**: Complete knowledge of industry-standard KPIs (SLA >95%, FCR 70-80%, CSAT >4.0), visualization formats, refresh intervals (10s critical, 1-5min operational, 15-30min analytics)
  - **Pattern Feedback & Coaching**: Actionable recommendations from ticket pattern analysis with ROI projections, team-specific performance feedback, evidence-based process improvements
  - **Automation Intelligence**: Alert pattern recognition (35.8% volume coverage validated), self-healing opportunity identification with specific technical implementations (PowerShell DSC, Azure Logic Apps), proven $350,460 annual savings ROI analysis
  - **Industry Research Integration**: ITIL 4 framework compliance, Gartner/Forrester best practices, vendor documentation analysis (ServiceNow, Jira Service Management)
- **Integration**: **PRODUCTION ENHANCED** - ServiceDesk Analytics Suite integration, industry-standard dashboard creation, UI Systems Agent collaboration, executive briefing workflows with automation recommendations, team coaching reports, **Data Cleaning Agent** (receives clean datasets)
- **Value Proposition**: **ENTERPRISE SERVICEDESK INTELLIGENCE WITH ACTIONABLE FEEDBACK** - Transform operational data into industry-compliant insights, automation opportunity identification with ROI validation (4.1-month payback), team coaching guidance, comprehensive dashboard design, executive-ready recommendations
- **Production Status**: ✅ **ENHANCED** - ServiceDesk pattern feedback capabilities added, 11,372 tickets analyzed, 35.8% repetitive pattern identification, automation ROI methodology validated

### macOS 26 Specialist Agent ⭐ **NEW - MACOS SYSTEM MASTERY**
**Location**: `claude/agents/macos_26_specialist_agent.md`
- **Purpose**: macOS 26 (Sequoia successor) system administration, automation, and deep integration specialist for power users and developers
- **Specialties**: System administration (preferences, privacy/security, SIP, launch agents), automation (shell scripting, AppleScript, Shortcuts, keyboard shortcuts), developer tools (Homebrew, development environments), audio/video configuration, security hardening
- **Key Commands**: analyze_macos_system_health, optimize_macos_performance, configure_privacy_security, create_keyboard_shortcut, setup_voice_dictation, automate_workflow, diagnose_audio_issues, configure_microphone, integrate_maia_system
- **Integration**: Deep Maia system integration (Whisper dictation, UFC context, hooks system), coordination with Security Specialist (security hardening), DevOps/SRE agents (infrastructure automation), Personal Assistant (scheduled maintenance)
- **Specialized Knowledge**: Keyboard shortcut implementation (skhd, Karabiner-Elements), Whisper dictation integration, development environment optimization, Apple Silicon performance tuning, APFS management
- **Value Proposition**: System mastery for macOS 26 power users, automated workflows, optimized performance, seamless Maia integration, enterprise-grade security configuration

### DNS Specialist Agent ⭐ **NEW - DNS & EMAIL INFRASTRUCTURE EXPERT**
**Location**: `claude/agents/dns_specialist_agent.md`
- **Purpose**: Expert DNS and email infrastructure specialist providing comprehensive DNS management, SMTP configuration, email security implementation, and domain architecture design for MSP operations
- **Specialties**: DNS architecture (zone design, DNSSEC, GeoDNS, traffic management), SMTP infrastructure (mail server configuration, relay setup, queue management), email authentication (SPF/DKIM/DMARC/MTA-STS/BIMI), email deliverability (reputation management, blacklist monitoring), MSP multi-tenant DNS management
- **Key Commands**: dns_architecture_assessment, smtp_infrastructure_design, email_authentication_implementation, dns_security_hardening, email_deliverability_optimization, msp_dns_tenant_strategy, dns_migration_planning, smtp_compliance_audit
- **Integration**: Cloud Security Principal (DNS security), Azure Solutions Architect (Azure DNS, M365), Microsoft 365 Integration (Exchange Online DNS), SRE Principal Engineer (DNS monitoring, SMTP reliability), Security Specialist (email security controls)
- **Critical Capabilities**: DMARC enforcement compliance (2024+ Google/Yahoo requirements), SPF flattening (10 DNS lookup limit optimization), zero-downtime DNS migrations, deliverability crisis response, anti-spoofing protection
- **Value Proposition**: Zero email downtime, DMARC compliance readiness, >95% inbox placement rates, automated DNS management, domain security hardening, MSP client onboarding workflows

## Enhanced Multi-Agent Ecosystem Integration ⭐ **EXPANDED**

### Cloud Practice Integration Patterns
- **Strategic Orchestration**: Principal Cloud Architect coordinates all cloud practice agents for complex enterprise engagements
- **Specialized Collaboration**: FinOps + Security + Azure agents collaborate on Well-Architected implementations
- **Executive Briefings**: Multi-agent synthesis for C-level presentations and strategic planning
- **Compliance Coordination**: Security + Azure agents ensure government and enterprise compliance requirements

### System Transformation Summary
**From**: Individual agents with basic JSON handoffs
**To**: **Coordinated ecosystem** with:
- Real-time communication via message bus
- Knowledge graph integration for semantic insights
- ML-driven pattern recognition and optimization
- Enhanced context preservation (95% retention)
- Intelligent error handling and recovery
- Performance monitoring and analytics
- **Cloud practice specialization** for enterprise market leadership
