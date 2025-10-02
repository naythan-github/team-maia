# Design Agent Orchestration Workflows

## Overview
Comprehensive orchestration patterns for the hybrid design agent architecture: **Product Designer Agent** (primary) coordinating with **UX Research Agent** and **UI Systems Agent** (specialists) for optimal design outcomes.

## Agent Architecture Summary

### 🎨 **Product Designer Agent** (Primary Hub)
- **Role**: 80% of design workflows, coordination hub
- **Capabilities**: End-to-end design, wireframes to mockups, basic UX research
- **Escalation Authority**: Determines when to engage specialists

### 🔍 **UX Research Agent** (Research Specialist)
- **Role**: Deep user research, usability analysis, data validation
- **Activation**: Complex research needs, usability testing, accessibility audits
- **Integration**: Provides evidence-based insights for design decisions

### 🎭 **UI Systems Agent** (Systems Specialist)  
- **Role**: Design systems, visual excellence, component architecture
- **Activation**: System-level design, brand development, advanced components
- **Integration**: Ensures design consistency and scalability

## Orchestration Workflows

### **Workflow 1: Simple Design Task** (Solo Product Designer)
```markdown
# Command: design_simple_interface

## Execution Pattern: Single Agent
**Trigger**: Basic interface design, straightforward UX requirements
**Agent**: Product Designer Agent only
**Duration**: 1-3 hours

### Process Flow:
1. **Requirements Analysis** (Product Designer)
   - Parse design brief and constraints
   - Identify user needs and business objectives
   - Determine if specialist expertise needed

2. **Design Execution** (Product Designer)
   - Create wireframes and user flows
   - Develop visual mockups
   - Apply basic UX principles and accessibility

3. **Delivery** (Product Designer)
   - Generate design specifications
   - Create handoff documentation
   - Present design rationale

### Success Criteria:
- Design meets functional requirements
- Basic usability principles applied
- Development-ready specifications delivered
```

### **Workflow 2: Research-Informed Design** (Product Designer + UX Research)
```markdown
# Command: design_research_validated_interface

## Execution Pattern: Primary + Research Specialist
**Trigger**: Complex user flows, unclear user needs, usability-critical interfaces
**Agents**: Product Designer Agent + UX Research Agent
**Duration**: 1-2 weeks

### Process Flow:
1. **Research Planning** (Product Designer → UX Research)
   - Product Designer identifies research questions
   - UX Research Agent designs research methodology
   - Define success metrics and validation criteria

2. **Research Execution** (UX Research Agent)
   - Conduct user interviews, usability tests, or surveys
   - Analyze behavior data and identify patterns
   - Synthesize insights into actionable design requirements

3. **Design Implementation** (UX Research → Product Designer)
   - Product Designer receives research insights
   - Creates research-informed design solutions
   - Iterates based on evidence and data

4. **Validation & Refinement** (Both Agents)
   - UX Research Agent validates design against research findings
   - Product Designer refines design based on validation
   - Joint review ensures research integration

### Success Criteria:
- Design decisions backed by user research data
- Measurable usability improvements achieved
- Research insights documented for future reference
```

### **Workflow 3: System-Level Design** (Product Designer + UI Systems)
```markdown
# Command: design_systematic_interface

## Execution Pattern: Primary + Systems Specialist  
**Trigger**: Component library needs, brand implementation, design consistency requirements
**Agents**: Product Designer Agent + UI Systems Agent
**Duration**: 2-4 weeks

### Process Flow:
1. **System Architecture** (Product Designer → UI Systems)
   - Product Designer identifies system-level requirements
   - UI Systems Agent architects component library approach
   - Define design token strategy and governance

2. **Component Development** (UI Systems Agent)
   - Create comprehensive component specifications
   - Develop design system documentation
   - Ensure cross-platform consistency and accessibility

3. **System Implementation** (UI Systems → Product Designer)
   - Product Designer applies system components to product design
   - Validates component usage and effectiveness
   - Identifies gaps or optimization opportunities

4. **System Optimization** (Both Agents)
   - UI Systems Agent refines components based on implementation feedback
   - Product Designer ensures design goals achieved with system approach
   - Joint documentation of system evolution and learnings

### Success Criteria:
- Reusable component system established
- Design consistency across product interfaces
- Development efficiency improvements demonstrated
```

### **Workflow 4: Comprehensive Design Project** (All Three Agents)
```markdown
# Command: comprehensive_design_solution

## Execution Pattern: Full Multi-Agent Orchestration
**Trigger**: Major redesign, new product development, complex user experience challenges
**Agents**: Product Designer Agent + UX Research Agent + UI Systems Agent
**Duration**: 1-3 months

### Process Flow:

#### Phase 1: Research & Discovery (Weeks 1-2)
1. **Research Strategy** (Product Designer → UX Research)
   - Product Designer defines research objectives
   - UX Research Agent creates comprehensive research plan
   - Stakeholder alignment on research scope and timeline

2. **User Research Execution** (UX Research Agent)
   - Conduct multi-methodology research (interviews, usability tests, analytics)
   - Analyze competitive landscape and industry benchmarks
   - Synthesize findings into user personas and journey maps

3. **System Assessment** (UI Systems Agent)
   - Audit existing design systems and components
   - Analyze design debt and consistency issues
   - Recommend system architecture improvements

#### Phase 2: Design Strategy (Weeks 3-4)
4. **Insight Integration** (All Agents)
   - Joint synthesis session combining research and system insights
   - Product Designer leads design strategy development
   - Define design principles and success metrics

5. **System Architecture** (UI Systems Agent)
   - Design comprehensive component library architecture
   - Create design token system and brand implementation plan
   - Develop system governance and adoption strategy

#### Phase 3: Design Execution (Weeks 5-8)
6. **Wireframe & Flow Design** (Product Designer)
   - Create comprehensive user flows and wireframes
   - Apply research insights to information architecture
   - Coordinate with UI Systems for component alignment

7. **Component Development** (UI Systems Agent)
   - Build comprehensive component library
   - Ensure accessibility compliance and performance optimization
   - Create detailed usage documentation and guidelines

8. **Design Validation** (UX Research Agent)
   - Test design concepts with target users
   - Validate component usability and effectiveness
   - Provide iteration recommendations based on testing

#### Phase 4: Integration & Optimization (Weeks 9-12)
9. **System Integration** (Product Designer + UI Systems)
   - Apply component system to complete product design
   - Ensure design consistency and system compliance
   - Optimize for development handoff and implementation

10. **Final Validation** (UX Research Agent)
    - Comprehensive usability testing of integrated design
    - Accessibility audit and compliance verification
    - Performance impact analysis and optimization recommendations

11. **Documentation & Handoff** (All Agents)
    - Product Designer creates comprehensive design specifications
    - UI Systems Agent provides system documentation and maintenance guides
    - UX Research Agent documents research findings and future recommendations

### Success Criteria:
- Research-validated, system-consistent design solution
- Comprehensive component library and design system
- Measurable improvements in user experience metrics
- Clear roadmap for system maintenance and evolution
```

## Agent Communication Protocols

### **Message Bus Integration**
```json
{
  "design_collaboration": {
    "primary_agent": "product_designer",
    "specialist_agents": ["ux_research", "ui_systems"],
    "communication_patterns": {
      "escalation_request": "product_designer → specialist",
      "insight_delivery": "specialist → product_designer",
      "joint_review": "all_agents → collaborative_session"
    }
  }
}
```

### **Context Sharing Standards**
```markdown
## Shared Context Structure
- **Design Brief**: Requirements, constraints, objectives
- **User Research**: Personas, journeys, behavioral insights
- **System Guidelines**: Components, tokens, brand standards
- **Iteration History**: Design evolution and decision rationale
```

## Workflow Selection Logic

### **Decision Tree for Agent Selection**
```markdown
1. **Complexity Assessment**
   - Simple interface → Product Designer only
   - User behavior questions → + UX Research Agent
   - System/brand requirements → + UI Systems Agent
   - Major project → All three agents

2. **Resource Optimization**
   - Time constraints → Minimize agent orchestration
   - Quality requirements → Maximize specialist involvement
   - Budget considerations → Balance efficiency vs. expertise

3. **Project Impact**
   - Internal tool → Product Designer focus
   - Customer-facing → Include UX Research
   - Multi-product → Require UI Systems
   - Strategic initiative → Full orchestration
```

## Success Metrics & KPIs

### **Orchestration Effectiveness**
- **Agent Utilization Efficiency**: Specialist agents used appropriately (not over/under-utilized)
- **Workflow Completion Time**: Projects completed within estimated timeframes
- **Quality Consistency**: Design outputs meet quality standards regardless of agent combination

### **Design Outcome Quality**
- **User Experience Metrics**: Task completion, user satisfaction, accessibility compliance
- **System Consistency**: Component reuse rate, design token adherence, brand compliance
- **Development Efficiency**: Design-to-development handoff quality, implementation accuracy

### **Business Impact**
- **Project ROI**: Design improvements translate to measurable business outcomes
- **Team Productivity**: Designer efficiency and output quality improvements
- **System Scalability**: Design system adoption and evolution success

## Integration with Existing Maia Ecosystem

### **Command Integration**
- Commands can invoke single agents or orchestrated workflows
- Automatic workflow selection based on request complexity
- Integration with existing project management and documentation systems

### **Tool Integration**
- Design tools (Figma, Sketch) integration for asset generation
- Analytics tools integration for performance measurement  
- Documentation tools integration for knowledge capture and sharing

### **Agent Ecosystem Integration**
- **Personal Assistant Agent**: Project scheduling and stakeholder coordination
- **Company Research Agent**: Competitive analysis and market insights
- **Blog Writer Agent**: Design case study development and thought leadership
- **Security Specialist Agent**: Security compliance review for design implementations

This orchestration framework ensures optimal design outcomes through intelligent agent coordination while maintaining the efficiency and systematic approach that defines the Maia ecosystem.