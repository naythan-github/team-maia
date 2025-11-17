# Patch Manager Plus API Specialist Agent - Test Plan

**Project**: v2.2 Enhanced Agent Validation
**Date**: 2025-11-14
**Target**: 550-600 line agent with 95% confidence rating

---

## 1. Test Categories

### 1.1 Structural Validation (v2.2 Template Compliance)
**Purpose**: Ensure agent follows v2.2 Enhanced template structure

**Tests**:
- [ ] **T1.1**: Core Behavior Principles section exists (4 principles including Self-Reflection)
- [ ] **T1.2**: 2-3 comprehensive few-shot examples (80-100 lines each)
- [ ] **T1.3**: At least ONE example includes ReACT pattern (THOUGHT → ACTION → OBSERVATION → REFLECTION)
- [ ] **T1.4**: At least ONE example includes self-review checkpoint
- [ ] **T1.5**: Problem-Solving template section exists
- [ ] **T1.6**: "When to Use Prompt Chaining" section exists
- [ ] **T1.7**: Explicit Handoff Declaration pattern documented
- [ ] **T1.8**: Integration Points section with handoff triggers defined
- [ ] **T1.9**: Total length: 550-600 lines
- [ ] **T1.10**: No placeholder text (all "[Domain-specific]" replaced with actual content)

**Pass Criteria**: 10/10 tests pass

---

### 1.2 API Coverage Validation
**Purpose**: Ensure all confirmed API operations documented

**Tests**:
- [ ] **T2.1**: Authentication examples for all 3 methods (Local, AD, OAuth 2.0)
- [ ] **T2.2**: List patches endpoint documented (`GET api/1.4/patch/allpatches`)
- [ ] **T2.3**: Patch filtering examples (severity, approval status, platform)
- [ ] **T2.4**: Pagination handling explained
- [ ] **T2.5**: Deploy patches endpoint documented (`POST api/1.3/patch/installpatch`)
- [ ] **T2.6**: Deployment scheduling parameters explained (`installaftertime`, `deadlineTime`, `expirytime`)
- [ ] **T2.7**: Reboot handling options documented (`forceRebootOption`: 0/1/2)
- [ ] **T2.8**: Uninstall/rollback endpoint documented (`POST api/1.3/patch/uninstallpatch`)
- [ ] **T2.9**: Approval settings endpoint documented (`GET api/1.4/patch/approvalsettings`)
- [ ] **T2.10**: Deployment policy templates endpoint referenced (`GET api/1.4/patch/deploymentpolicies`)

**Pass Criteria**: 10/10 tests pass

---

### 1.3 Code Example Quality
**Purpose**: Ensure working Python examples with production-grade error handling

**Tests**:
- [ ] **T3.1**: At least 3 complete Python code examples
- [ ] **T3.2**: Authentication example includes base64 encoding for password
- [ ] **T3.3**: API requests include proper headers (`Authorization: authtoken`)
- [ ] **T3.4**: Error handling for common codes (401, 403, 404, 500)
- [ ] **T3.5**: Retry logic with exponential backoff demonstrated
- [ ] **T3.6**: Environment variable usage for credentials (not hardcoded)
- [ ] **T3.7**: Structured logging example included
- [ ] **T3.8**: Rate limiting guidance included
- [ ] **T3.9**: SSL certificate validation mentioned
- [ ] **T3.10**: OAuth token refresh workflow explained (cloud version)

**Pass Criteria**: 9/10 tests pass (T3.10 optional if OAuth not primary focus)

---

### 1.4 Use Case Coverage
**Purpose**: Ensure practical MSP/enterprise scenarios demonstrated

**Few-Shot Example 1 Requirements**:
- [ ] **T4.1**: Title references specific workflow (not generic)
- [ ] **T4.2**: Scenario description includes MSP or enterprise context
- [ ] **T4.3**: Complete workflow (authentication → query → process → act → verify)
- [ ] **T4.4**: ReACT pattern applied (THOUGHT/ACTION/OBSERVATION/REFLECTION labels visible)
- [ ] **T4.5**: Working Python code included (not pseudocode)
- [ ] **T4.6**: Error handling demonstrated
- [ ] **T4.7**: Self-review checkpoint included
- [ ] **T4.8**: 80-100 lines length

**Few-Shot Example 2 Requirements**:
- [ ] **T4.9**: Different use case from Example 1
- [ ] **T4.10**: Multi-step workflow or multi-tenant scenario
- [ ] **T4.11**: Prompt chaining pattern OR integration with external tool (ServiceNow, Slack)
- [ ] **T4.12**: Complete working code
- [ ] **T4.13**: 80-100 lines length

**Few-Shot Example 3 Requirements** (Optional - if agent >550 lines):
- [ ] **T4.14**: Third distinct use case
- [ ] **T4.15**: Emergency/incident response scenario OR compliance reporting
- [ ] **T4.16**: Error recovery demonstrated
- [ ] **T4.17**: 80-100 lines length

**Pass Criteria**: 13/17 tests pass (Examples 1&2 required, Example 3 optional)

---

### 1.5 SRE Production Readiness
**Purpose**: Ensure production-grade reliability guidance

**Tests**:
- [ ] **T5.1**: Retry logic with exponential backoff documented (max retries, backoff range)
- [ ] **T5.2**: Circuit breaker pattern mentioned or demonstrated
- [ ] **T5.3**: Structured logging format explained (timestamp, endpoint, status code, latency)
- [ ] **T5.4**: Rate limiting strategy provided (requests/minute recommendation)
- [ ] **T5.5**: Security best practices section (no hardcoded credentials, SSL validation)
- [ ] **T5.6**: Error handling covers 401, 403, 404, 429, 500 response codes
- [ ] **T5.7**: OAuth token refresh automation explained (if cloud version covered)
- [ ] **T5.8**: Performance metrics defined (response time targets, error rate thresholds)
- [ ] **T5.9**: Health check or API connectivity validation explained
- [ ] **T5.10**: Graceful degradation strategy mentioned

**Pass Criteria**: 8/10 tests pass

---

### 1.6 Integration Points & Handoffs
**Purpose**: Ensure proper agent collaboration patterns

**Tests**:
- [ ] **T6.1**: Explicit Handoff Declaration pattern example included
- [ ] **T6.2**: Handoff to ManageEngine Desktop Central agent defined (UI operations)
- [ ] **T6.3**: Handoff to SRE Principal Engineer agent defined (production deployment)
- [ ] **T6.4**: Handoff to Security Specialist agent defined (CVE prioritization)
- [ ] **T6.5**: External integration examples (ServiceNow, Slack, Terraform, Ansible)
- [ ] **T6.6**: Handoff triggers clearly documented (when to hand off)
- [ ] **T6.7**: Context preservation format shown (JSON structure with work completed, current state, next steps)

**Pass Criteria**: 6/7 tests pass

---

### 1.7 ManageEngine-Specific Domain Expertise
**Purpose**: Ensure specialist knowledge beyond generic API patterns

**Tests**:
- [ ] **T7.1**: Patch Manager Plus vs Desktop Central distinction explained
- [ ] **T7.2**: Cloud vs on-premises differences documented (OAuth vs local auth)
- [ ] **T7.3**: Deployment policy template concept explained
- [ ] **T7.4**: Reboot requirement handling strategies provided
- [ ] **T7.5**: Retry configuration best practices (when to use logon/startup vs refresh retries)
- [ ] **T7.6**: Multi-tenant MSP patterns demonstrated (iterate customers, segment reporting)
- [ ] **T7.7**: Approval workflow integration explained (`isOnlyApproved` flag usage)
- [ ] **T7.8**: Self-Service Portal deployment option explained (`deploymentType`: 1)
- [ ] **T7.9**: Rollback/uninstall strategy documented
- [ ] **T7.10**: Troubleshooting section with common errors (401, 403, SSL cert issues)

**Pass Criteria**: 9/10 tests pass

---

### 1.8 Documentation Quality
**Purpose**: Ensure agent is self-documenting and clear

**Tests**:
- [ ] **T8.1**: Agent Overview section clearly explains role and target users
- [ ] **T8.2**: Core Capabilities section lists specific operations (not vague)
- [ ] **T8.3**: Key Commands section exists (if applicable to agent structure)
- [ ] **T8.4**: Known Limitations section included (deployment status monitoring, rate limits)
- [ ] **T8.5**: API version compatibility documented (tested with v1.3/v1.4)
- [ ] **T8.6**: Model Selection Strategy section exists (Sonnet default, Opus permission required)
- [ ] **T8.7**: Production Status section with readiness indicator
- [ ] **T8.8**: Value Proposition section explaining ROI for users
- [ ] **T8.9**: No broken references or incomplete sections
- [ ] **T8.10**: Grammar and formatting professional (no typos in examples)

**Pass Criteria**: 9/10 tests pass

---

## 2. Overall Pass/Fail Criteria

### Minimum Viable Agent (MVP)
**Requirements**:
- Structural Validation: ≥8/10
- API Coverage: ≥8/10
- Code Examples: ≥7/10
- Use Case Coverage: ≥10/17 (Examples 1&2 complete)
- SRE Readiness: ≥6/10
- Integration Points: ≥5/7
- Domain Expertise: ≥7/10
- Documentation: ≥7/10

**Total Minimum**: 58/84 tests (69% pass rate)

### Production-Ready Agent (Target)
**Requirements**:
- Structural Validation: ≥9/10 (90%)
- API Coverage: 10/10 (100%)
- Code Examples: ≥9/10 (90%)
- Use Case Coverage: ≥13/17 (76%)
- SRE Readiness: ≥8/10 (80%)
- Integration Points: ≥6/7 (86%)
- Domain Expertise: ≥9/10 (90%)
- Documentation: ≥9/10 (90%)

**Total Target**: 73/84 tests (87% pass rate)

---

## 3. Test Execution Plan

### Phase 4 (Implementation) Testing
1. **During Writing** (real-time checks):
   - Line count tracking (target: 550-600)
   - Section completion checklist
   - Code syntax validation

2. **After First Draft**:
   - Run all 84 tests
   - Document failures
   - Calculate pass rate

3. **Refinement Cycle**:
   - Fix critical failures (API coverage, structural validation)
   - Enhance examples if <90% on code quality
   - Add missing integration points
   - Re-test until ≥73/84 (87%)

4. **Final Validation**:
   - Read-through for clarity
   - Grammar/typo check
   - Verify all Python examples use consistent style
   - Confirm no placeholder text remains

---

## 4. Success Metrics

**Quality Score**: Pass Rate × Confidence Rating
- Target: 87% pass rate × 95% confidence = **82.6/100 quality score**
- MVP Minimum: 69% × 85% = 58.6/100

**Time to Complete**:
- Implementation: 90-120 minutes
- Testing: 20-30 minutes
- Refinement: 20-40 minutes
- **Total**: 2.5-3.5 hours

**Deliverables**:
1. `patch_manager_plus_api_specialist_agent.md` (550-600 lines)
2. Test results documentation (this file with checkboxes completed)
3. Updated capability_index.md entry

---

## 5. Test Results (To Be Completed)

**Execution Date**: [Pending]
**Tester**: Prompt Engineer Agent + SRE Principal Engineer Agent

### Summary
- Total Tests: 84
- Passed: __/84
- Failed: __/84
- Pass Rate: __%
- Quality Score: __/100

### Failed Tests
[List failures here after testing]

### Remediation Actions
[List fixes applied here]

---

**Status**: Test Plan Ready
**Next Step**: Proceed to Phase 4 (Implementation)
