# TDD Development Protocol - Maia Standard Workflow

## Overview
Established protocol for Test-Driven Development projects to prevent requirements drift and ensure comprehensive coverage before implementation.

## Key Problems Addressed
- Requirements drift during implementation
- Premature test creation before complete requirements gathering  
- Lost decisions and requirements through conversation
- Better outcomes consistently observed with TDD approach

## Standard TDD Workflow

### Phase 1: Requirements Discovery (NO CODING/TESTS)
**CRITICAL**: No tests or code until requirements are complete and confirmed

1. **Core Purpose Discovery**
   - What problem are we solving?
   - Who will use this?
   - What's the success criteria?

2. **Functional Requirements Gathering**
   - Input: What goes in?
   - Processing: What transformations?
   - Output: What comes out?
   - Error cases: What could go wrong?

3. **Example-Driven Clarification**
   - "Walk me through a typical use case"
   - "What happens if [edge case]?"
   - "Show me example input/output"
   - Request at least 3 concrete usage examples

4. **Non-Functional Requirements**
   - Performance requirements?
   - Security constraints?
   - Integration points?
   - Future extensibility needs?

5. **Explicit Confirmation Checkpoint**
   - Summarize all requirements discovered
   - Ask "What am I missing?"
   - Wait for explicit "requirements complete" confirmation
   - **HARD GATE**: Do not proceed without confirmation

### Phase 2: Requirements Documentation
1. Create `requirements.md` with all discovered requirements
2. Include acceptance criteria for each requirement
3. Document example scenarios and edge cases
4. Get explicit approval of documented requirements

### Phase 3: Test Design (ONLY after requirements confirmed)
1. Set up appropriate test framework
2. Create `test_requirements.py` (or language-appropriate test file)
3. Write failing tests for EACH requirement
4. Confirm test coverage matches requirements
5. No implementation until all requirement tests exist

### Phase 4: Implementation
1. Standard TDD red-green-refactor cycle
2. Make tests pass one at a time
3. Regular verification against requirements.md
4. Update documentation if requirements evolve

## Conversation Management

### Starting a TDD Project
- User: "Let's do TDD" or "Let's do TDD with requirements tracking"
- Maia: Initiates Phase 1 discovery questions
- Maia: Creates requirements.md and test files only after confirmation

### During Development
- Start each session: "Let me read the requirements file"
- After design decisions: "Updating requirements with our decisions..."
- Before implementing: "Let me verify against our test suite"
- Regular checkpoint: "Are we still aligned with requirements?"

### Key Phrases
- **"Let's do TDD"** - Triggers full discovery protocol
- **"Requirements complete"** - User signal to proceed to test phase
- **"Check requirements"** - Prompts re-reading of requirements.md
- **"Update requirements"** - Captures new decisions
- **"Show me the tests"** - Validates test coverage
- **"Start coding"** - Bypasses discovery (only if user wants to skip)

## File Structure for TDD Projects
```
project_name/
├── requirements.md          # Living requirements document
├── test_requirements.py     # Tests encoding all requirements  
├── implementation.py        # Actual implementation
└── README.md               # Project overview
```

## Success Metrics
- Zero requirement misses after implementation
- All initial tests remain valid (no deletion due to misunderstanding)
- Requirements document stays current with implementation
- No "oh, I forgot to mention" moments after test creation

## Quality Gates
1. **Requirements Gate**: No tests until "requirements complete" confirmation
2. **Test Gate**: No implementation until all tests written
3. **Implementation Gate**: No feature complete until all tests pass
4. **Documentation Gate**: Requirements.md updated with any changes

## Risk Mitigation
- Active probing during discovery phase
- Multiple concrete examples required
- Explicit confirmation checkpoints
- Regular requirements verification
- Test-first discipline enforcement

## Why This Works
1. **Persistent Documentation**: Requirements survive context resets
2. **Executable Verification**: Tests prove requirements are met
3. **Double Verification**: Both documentation and tests must align
4. **Systematic Discovery**: Comprehensive requirements before coding
5. **Clear Checkpoints**: Explicit gates prevent premature progress

## Integration with Maia Principles
- **Solve Once**: Capture requirements properly first time
- **System Design**: Systematic approach over ad-hoc development
- **Continuous Learning**: Update protocol based on project outcomes
- **Documentation-First**: Always update requirements when decisions change

---
*Last Updated: 2025-01-22*
*Status: Active Protocol*
*Usage: Standard for all TDD development projects*