# Candidate Screening → Technical Assessment → Interview Recommendation Chain

## Workflow Metadata
- **Chain ID**: `candidate_screening_assessment_interview_chain`
- **Version**: 1.0
- **Primary Agent**: Recruitment & Hiring Specialist Agent
- **Supporting Agents**: Technical Interview Agent, LinkedIn AI Advisor
- **Estimated Time**: 45-60 minutes (15-20 min per subtask)
- **Expected Improvement**: +50% candidate quality prediction, +35% interview efficiency

## Workflow Purpose
Transform recruitment from resume keyword matching into comprehensive candidate evaluation combining resume analysis, technical skills assessment, and interview strategy. Uses structured evaluation rubrics and data-driven decision-making to reduce bias and improve hire quality.

## Input Requirements
```json
{
  "job_req_id": "JR-2025-089",
  "role": {
    "title": "Senior Site Reliability Engineer",
    "level": "Senior (L5) | Staff (L6) | Principal (L7)",
    "team": "Platform Engineering",
    "location": "Melbourne, Australia | Remote",
    "required_skills": ["Kubernetes", "Terraform", "Python", "Azure/AWS"],
    "preferred_skills": ["GitOps", "Prometheus", "Incident Response"],
    "years_experience": "5-8 years"
  },
  "candidate": {
    "name": "Jane Smith",
    "resume_url": "https://linkedin.com/in/janesmith",
    "linkedin_profile": "https://linkedin.com/in/janesmith",
    "github_profile": "https://github.com/janesmith",
    "email": "jane.smith@example.com",
    "current_company": "Atlassian",
    "current_title": "SRE II",
    "years_experience": 6,
    "location": "Melbourne, Australia"
  },
  "evaluation_criteria": {
    "technical_skills": 40,
    "experience_relevance": 25,
    "culture_fit": 20,
    "career_trajectory": 15
  }
}
```

## Subtasks

---

### Subtask 1: Resume & Profile Screening
**Agent**: Recruitment & Hiring Specialist Agent
**Goal**: Extract structured data from resume/LinkedIn, score against job requirements
**Input Variables**: `job_req_id`, `role`, `candidate`, `evaluation_criteria`
**Output Variables**: `candidate_profile`, `skills_match`, `experience_analysis`, `screening_score`

**Prompt**:
```
You are the Recruitment & Hiring Specialist agent conducting initial candidate screening.

CONTEXT:
- Job Requisition: {{job_req_id}} - {{role.title}}
- Required Skills: {{role.required_skills}}
- Preferred Skills: {{role.preferred_skills}}
- Experience Level: {{role.years_experience}}
- Candidate Name: {{candidate.name}}
- Resume: {{candidate.resume_url}}
- LinkedIn: {{candidate.linkedin_profile}}
- GitHub: {{candidate.github_profile}}

TASK:
Perform comprehensive resume and profile analysis:

1. **Skills Extraction & Matching**
   Extract all technical skills mentioned in:
   - Resume work experience sections
   - LinkedIn "Skills & Endorsements"
   - GitHub project README files
   - Certifications and training

   Categorize skills:
   - **Hard match**: Exact skill name match (e.g., "Kubernetes" = "Kubernetes")
   - **Soft match**: Related skills (e.g., "Docker Swarm" ≈ "Kubernetes orchestration")
   - **Missing**: Required skills not found anywhere

   Scoring:
   - Required skill (hard match): +10 points each
   - Required skill (soft match): +5 points each
   - Preferred skill (hard match): +5 points each
   - Preferred skill (soft match): +2 points each
   - Missing required skill: -10 points each

2. **Experience Depth Analysis**
   For each required skill, determine proficiency level:
   - **Expert (5+ years)**: Multiple projects, lead role, mentored others
   - **Advanced (3-5 years)**: Production experience, problem-solving examples
   - **Intermediate (1-3 years)**: Solid foundation, some production use
   - **Beginner (<1 year)**: Learning, side projects, no production experience
   - **No evidence**: Skill mentioned but no details

   Evidence sources:
   - Work experience: "Led migration of 50 microservices to Kubernetes" → Expert
   - Projects: GitHub repo with 500+ stars using technology → Advanced
   - Certifications: CKA (Certified Kubernetes Administrator) → Advanced
   - Generic mention: "Familiar with Kubernetes" (no details) → Beginner

3. **Career Trajectory Assessment**
   Analyze career progression:
   - **Upward trajectory**: Promotions, increasing responsibility, expanding scope
   - **Lateral moves**: Job changes at same level (neutral, not negative)
   - **Stagnation**: Same role/level for 5+ years (investigate reasons)
   - **Red flags**: Frequent short tenures (<1 year), gaps (>6 months unexplained)

   Company quality signals:
   - Tier 1: FAANG, unicorn startups ($1B+ valuation), top consulting firms
   - Tier 2: Public tech companies, established startups, large enterprises
   - Tier 3: Small companies, agencies, lesser-known organizations

4. **Relevance Scoring**
   How relevant is candidate's experience to this role?
   - Industry relevance: SaaS > Enterprise > Government > Other
   - Team size experience: Managed 30+ engineers = high relevance for senior roles
   - Technical domain: Cloud-native > On-prem; Platform engineering > Application development
   - Scale experience: Petabyte-scale data, million QPS, 99.99% SLAs = high relevance

5. **Red Flags & Green Flags**
   **Red Flags**:
   - Frequent job hopping (<1 year tenures)
   - Unexplained employment gaps (>6 months)
   - Skill inflation (claims expert but no evidence)
   - Generic resume (not tailored to role)
   - Typos and grammatical errors

   **Green Flags**:
   - Open source contributions (GitHub stars/forks)
   - Speaking engagements (conferences, meetups)
   - Technical blog posts (demonstrates communication skills)
   - Community leadership (meetup organizer, mentor)
   - Certifications (CKA, AWS SA Pro, etc.)

OUTPUT FORMAT (JSON):
{
  "candidate_profile": {
    "name": "Jane Smith",
    "current_role": "SRE II at Atlassian",
    "years_experience": 6,
    "location": "Melbourne, Australia",
    "education": "Bachelor of Computer Science, University of Melbourne (2017)",
    "certifications": ["CKA (Certified Kubernetes Administrator)", "AWS Solutions Architect Associate"],
    "github_stats": {
      "repositories": 45,
      "stars_received": 234,
      "contributions_last_year": 892
    }
  },
  "skills_match": {
    "required_skills": [
      {
        "skill": "Kubernetes",
        "match_type": "Hard match",
        "proficiency": "Expert",
        "evidence": "Led Kubernetes migration for 50 microservices at Atlassian (2022-2024), CKA certified",
        "years_experience": 4,
        "score": 10
      },
      {
        "skill": "Terraform",
        "match_type": "Hard match",
        "proficiency": "Advanced",
        "evidence": "Managed 100K+ lines of Terraform code for multi-cloud infrastructure",
        "years_experience": 3,
        "score": 10
      },
      {
        "skill": "Python",
        "match_type": "Hard match",
        "proficiency": "Advanced",
        "evidence": "Built automation tools in Python, 5K+ lines of code in GitHub repos",
        "years_experience": 5,
        "score": 10
      },
      {
        "skill": "Azure/AWS",
        "match_type": "Soft match (AWS only)",
        "proficiency": "Advanced",
        "evidence": "AWS Solutions Architect certified, 4 years AWS experience, no Azure experience",
        "years_experience": 4,
        "score": 5
      }
    ],
    "preferred_skills": [
      {
        "skill": "GitOps",
        "match_type": "Hard match",
        "proficiency": "Advanced",
        "evidence": "Implemented ArgoCD for multi-cluster GitOps at Atlassian",
        "years_experience": 2,
        "score": 5
      },
      {
        "skill": "Prometheus",
        "match_type": "Hard match",
        "proficiency": "Intermediate",
        "evidence": "Configured Prometheus for Kubernetes monitoring, basic PromQL knowledge",
        "years_experience": 2,
        "score": 5
      },
      {
        "skill": "Incident Response",
        "match_type": "Hard match",
        "proficiency": "Expert",
        "evidence": "On-call rotation for 2 years, reduced MTTR from 45min to 15min",
        "years_experience": 2,
        "score": 5
      }
    ],
    "missing_required_skills": [],
    "additional_relevant_skills": ["Docker", "Helm", "Grafana", "Datadog", "PostgreSQL"],
    "total_score": 50,
    "max_score": 50,
    "match_percentage": 100
  },
  "experience_analysis": {
    "career_progression": [
      {"year": 2017, "role": "Graduate Software Engineer", "company": "REA Group", "duration": "1 year"},
      {"year": 2018, "role": "Software Engineer", "company": "REA Group", "duration": "2 years"},
      {"year": 2020, "role": "SRE I", "company": "Atlassian", "duration": "2 years"},
      {"year": 2022, "role": "SRE II", "company": "Atlassian", "duration": "2 years (current)"}
    ],
    "trajectory": "Upward - promoted twice in 6 years, moved to Tier 1 company (Atlassian)",
    "company_quality": "Tier 1 (Atlassian) and Tier 2 (REA Group) - strong companies",
    "tenure_pattern": "Healthy - 1-2 year tenures, no job hopping",
    "relevance_score": 90,
    "relevance_notes": "Strong cloud-native SRE experience at scale (Atlassian serves 100K+ customers)"
  },
  "screening_score": {
    "technical_skills": 40,
    "experience_relevance": 23,
    "career_trajectory": 14,
    "total": 77,
    "max": 80,
    "percentage": 96.25,
    "verdict": "✅ STRONG MATCH - Proceed to technical assessment"
  },
  "red_flags": [],
  "green_flags": [
    "CKA certification (demonstrates Kubernetes expertise)",
    "Open source contributor (234 GitHub stars)",
    "Tier 1 company experience (Atlassian)",
    "Strong career progression (2 promotions in 6 years)",
    "Measurable impact (reduced MTTR by 67%)"
  ],
  "screening_decision": {
    "recommendation": "Advance to Technical Assessment",
    "confidence": "High (96% match)",
    "rationale": "Candidate has all required skills at advanced/expert level, strong career trajectory at Tier 1 companies, measurable impact on SRE metrics, and relevant certifications. No red flags identified."
  }
}

QUALITY CRITERIA:
✅ All required and preferred skills evaluated with evidence
✅ Proficiency levels justified with specific examples
✅ Career trajectory analyzed chronologically
✅ Red flags and green flags explicitly listed
✅ Screening decision includes confidence level and rationale
```

**Expected Output Size**: 180-220 lines JSON

---

### Subtask 2: Technical Skills Deep-Dive
**Agent**: Technical Interview Agent
**Goal**: Design technical assessment questions based on candidate's experience and role requirements
**Input Variables**: `subtask_1_output`, `role`, `candidate`
**Output Variables**: `technical_assessment`, `interview_questions`, `evaluation_rubric`

**Prompt**:
```
You are the Technical Interview agent designing a comprehensive technical assessment.

CONTEXT:
- Role: {{role.title}} ({{role.level}})
- Candidate: {{candidate.name}} ({{subtask_1_output.candidate_profile.current_role}})
- Skills Match: {{subtask_1_output.skills_match}}
- Experience: {{subtask_1_output.experience_analysis}}
- Screening Score: {{subtask_1_output.screening_score.percentage}}%

TASK:
Design multi-faceted technical assessment tailored to candidate's background:

1. **Technical Depth Questions** (30 minutes)
   Assess depth in core required skills:

   **Kubernetes (Expert level expected)**:
   - Architecture: "Explain Kubernetes control plane components and their responsibilities"
   - Troubleshooting: "A pod is in CrashLoopBackOff. Walk me through your diagnostic process."
   - Scaling: "Design a Kubernetes autoscaling strategy for a service with 10x traffic spikes"

   **Terraform (Advanced level expected)**:
   - State management: "How do you handle Terraform state in a team environment?"
   - Module design: "When would you create a Terraform module vs. inline resources?"
   - Drift detection: "How do you detect and remediate infrastructure drift?"

   **Python (Advanced level expected)**:
   - Automation: "Write a script to parse Prometheus metrics and alert on anomalies"
   - Concurrency: "Explain asyncio vs threading. When would you use each?"
   - Testing: "How do you test infrastructure automation code?"

   **Cloud (AWS Advanced, Azure missing)**:
   - AWS: "Design a highly available multi-region architecture for a web application"
   - Azure: "What are the key differences between AWS and Azure? (test learning agility)"

2. **Problem-Solving Scenarios** (30 minutes)
   Real-world SRE challenges:

   **Scenario 1: Production Outage**
   "It's 2am. You're on-call. Pagerduty alert: API error rate jumped from 0.1% to 15% in the last 5 minutes.
   What do you do? Walk me through your first 10 minutes."

   Expected answer structure:
   - Acknowledge alert, assess severity (SEV-1 or SEV-2?)
   - Check monitoring (Grafana, Datadog) for symptoms
   - Review recent changes (deployments, config changes)
   - Incident response (rollback vs. forward fix)
   - Communication (status page, stakeholders)

   **Scenario 2: Capacity Planning**
   "Your service currently handles 1,000 requests/second. Business expects 10x growth in 6 months.
   How do you prepare infrastructure? What metrics do you track?"

   Expected answer structure:
   - Load testing to understand current capacity headroom
   - Identify bottlenecks (database, compute, network)
   - Cost analysis (reserved instances, autoscaling)
   - Monitoring and alerting for capacity thresholds

   **Scenario 3: Observability Strategy**
   "You join a team with poor observability. Where do you start?
   What metrics, logs, and traces do you instrument first?"

   Expected answer structure:
   - Golden signals (latency, traffic, errors, saturation)
   - Distributed tracing for microservices
   - Log aggregation and structured logging
   - SLIs/SLOs definition

3. **System Design** (30 minutes)
   Design exercise at appropriate seniority level:

   **Senior (L5) Exercise**:
   "Design a CI/CD pipeline for a microservices application (10 services) with these requirements:
   - Automated testing (unit, integration, end-to-end)
   - Progressive deployment (canary rollout)
   - Automated rollback on high error rate
   - Multi-environment (dev, staging, production)

   Draw architecture diagram and explain trade-offs."

   **Staff (L6) Exercise**:
   "Design a multi-region disaster recovery strategy for a critical SaaS application (99.99% SLA).
   Consider: RTO/RPO, data replication, failover automation, cost optimization."

4. **Cultural Fit & Soft Skills** (15 minutes)
   Assess collaboration, communication, and leadership:

   **Collaboration**:
   - "Describe a time you disagreed with a teammate on a technical decision. How did you resolve it?"
   - "How do you balance SRE reliability goals with engineering velocity goals?"

   **Communication**:
   - "Explain Kubernetes networking to a non-technical product manager."
   - "You need to convince leadership to invest $100K in observability tooling. What's your pitch?"

   **Leadership** (for Senior+ roles):
   - "How do you mentor junior engineers?"
   - "Describe a time you improved team processes or culture."

5. **Questions for Interviewer** (10 minutes)
   Candidate's questions reveal priorities:
   - Strong signal: "What's your approach to on-call rotation and work-life balance?"
   - Strong signal: "What's the most challenging incident you've faced recently?"
   - Weak signal: "What's the salary range?" (should be HR question)
   - Red flag: No questions (lack of curiosity)

OUTPUT FORMAT (JSON):
{
  "technical_assessment": {
    "assessment_structure": {
      "technical_depth": "30 minutes",
      "problem_solving": "30 minutes",
      "system_design": "30 minutes",
      "cultural_fit": "15 minutes",
      "candidate_questions": "10 minutes",
      "total_duration": "115 minutes (2 hours)"
    },
    "difficulty_level": "Senior (L5) - Expect advanced proficiency in core skills"
  },
  "interview_questions": {
    "kubernetes_depth": [
      {
        "question": "Explain the role of etcd in a Kubernetes cluster. What happens if etcd becomes unavailable?",
        "expected_answer": "etcd is the distributed key-value store for cluster state. If unavailable, control plane can't make changes but existing pods continue running. Requires quorum for writes.",
        "scoring": "Expert: Mentions quorum, failure modes, backup strategies. Advanced: Correct explanation. Intermediate: Partial understanding."
      },
      {
        "question": "A pod is in CrashLoopBackOff. Walk me through your diagnostic process step-by-step.",
        "expected_answer": "1) kubectl describe pod to see events, 2) kubectl logs to see container output, 3) Check liveness/readiness probes, 4) Inspect resource limits, 5) Check ConfigMap/Secret mounts",
        "scoring": "Expert: Systematic approach with all steps. Advanced: Most steps covered. Intermediate: Basic troubleshooting only."
      }
    ],
    "terraform_depth": [
      {
        "question": "How do you handle Terraform state in a multi-team environment? What are the risks and mitigations?",
        "expected_answer": "Remote state (S3 + DynamoDB for locking), separate state files per environment, strict IAM policies, state file encryption. Risks: state corruption, concurrent modifications.",
        "scoring": "Advanced: Mentions locking, encryption, separation. Intermediate: Remote state only. Beginner: Local state."
      }
    ],
    "problem_solving_scenarios": [
      {
        "scenario": "Production Outage: API error rate jumped from 0.1% to 15% at 2am",
        "question": "Walk me through your first 10 minutes as the on-call engineer.",
        "expected_answer_steps": [
          "1. Acknowledge alert, assess severity (SEV-1 likely)",
          "2. Check monitoring (Grafana) for error patterns, latency, traffic",
          "3. Review recent changes (deployments in last 2 hours)",
          "4. Establish incident command (war room, notify manager)",
          "5. Immediate action: Rollback recent deployment if correlated",
          "6. Communication: Update status page, notify stakeholders",
          "7. Validate recovery: Monitor error rate drop, run smoke tests"
        ],
        "scoring_rubric": {
          "expert": "All 7 steps in logical order, mentions severity classification and communication",
          "advanced": "5-6 steps, correct prioritization",
          "intermediate": "3-4 steps, missing communication or rollback strategy"
        }
      },
      {
        "scenario": "Capacity Planning: 10x traffic growth expected in 6 months",
        "question": "How do you prepare infrastructure? What metrics do you track?",
        "expected_answer_steps": [
          "1. Load testing to establish current capacity ceiling",
          "2. Identify bottlenecks (database, compute, network, cost)",
          "3. Horizontal scaling strategy (autoscaling policies)",
          "4. Database scaling (read replicas, sharding if needed)",
          "5. Cost analysis (reserved instances for baseline, spot for bursts)",
          "6. Monitoring: CPU, memory, disk, network, database connections",
          "7. Capacity alerting: Trigger at 70% utilization to proactively scale"
        ],
        "scoring_rubric": {
          "expert": "Comprehensive plan with cost optimization and monitoring",
          "advanced": "Scaling strategy with load testing and bottleneck analysis",
          "intermediate": "Basic autoscaling suggestion, no cost or monitoring plan"
        }
      }
    ],
    "system_design_exercise": {
      "level": "Senior (L5)",
      "prompt": "Design a CI/CD pipeline for 10 microservices with automated testing, canary deployment, and automated rollback.",
      "evaluation_criteria": {
        "architecture": "Diagram includes: Git → CI (GitHub Actions/GitLab CI) → Build → Test stages → Artifact registry → CD (ArgoCD/Flux) → Kubernetes",
        "testing_strategy": "Unit tests (pre-merge), integration tests (staging), smoke tests (production post-deploy)",
        "progressive_deployment": "Canary rollout (10% → 50% → 100% with automated promotion based on error rate)",
        "automated_rollback": "Error rate >5% triggers automatic rollback to previous version",
        "multi_environment": "Separate pipelines or stages for dev/staging/production with approval gates"
      },
      "scoring": {
        "expert": "Complete architecture with trade-offs discussed (cost, complexity, reliability)",
        "advanced": "Solid design covering all requirements",
        "intermediate": "Basic CI/CD understanding, missing progressive deployment or rollback"
      }
    },
    "cultural_fit": [
      {
        "question": "Describe a time you disagreed with a teammate on a technical decision. How did you resolve it?",
        "evaluation_focus": "Collaboration, conflict resolution, ego management",
        "strong_answer": "Data-driven discussion, both sides presented, compromise or experiment to validate",
        "weak_answer": "I convinced them I was right | We agreed to disagree (no resolution)"
      },
      {
        "question": "Explain Kubernetes pod networking to a non-technical product manager in 2 minutes.",
        "evaluation_focus": "Communication, simplification without dumbing down",
        "strong_answer": "Uses analogy (pods = apartments, services = building address), explains connectivity simply",
        "weak_answer": "Technical jargon (CNI, iptables, kube-proxy) without context"
      }
    ]
  },
  "evaluation_rubric": {
    "technical_depth": {
      "weight": 40,
      "criteria": {
        "expert": "35-40 points - Deep understanding, real-world examples, handles edge cases",
        "advanced": "28-34 points - Solid understanding, some real-world experience",
        "intermediate": "20-27 points - Textbook knowledge, limited production experience",
        "beginner": "0-19 points - Surface-level understanding, no production experience"
      }
    },
    "problem_solving": {
      "weight": 30,
      "criteria": {
        "expert": "27-30 points - Systematic approach, considers trade-offs, realistic solutions",
        "advanced": "21-26 points - Logical approach, covers main points",
        "intermediate": "15-20 points - Some structure, misses key considerations",
        "beginner": "0-14 points - Unstructured, impractical solutions"
      }
    },
    "system_design": {
      "weight": 20,
      "criteria": {
        "expert": "18-20 points - Complete design, discusses trade-offs, scalable and cost-effective",
        "advanced": "14-17 points - Solid design, covers requirements",
        "intermediate": "10-13 points - Basic design, missing some requirements",
        "beginner": "0-9 points - Incomplete or impractical design"
      }
    },
    "cultural_fit": {
      "weight": 10,
      "criteria": {
        "strong": "9-10 points - Collaborative, curious, growth mindset, strong communicator",
        "good": "7-8 points - Collaborative, decent communication",
        "acceptable": "5-6 points - Some collaboration, room for improvement",
        "weak": "0-4 points - Poor communication, ego issues, lack of curiosity"
      }
    }
  }
}

QUALITY CRITERIA:
✅ Questions tailored to candidate's experience level (not generic)
✅ Scenarios are realistic SRE challenges (not whiteboard algorithms)
✅ Evaluation rubric objective with scoring criteria
✅ Mix of technical depth, problem-solving, and soft skills
✅ Expected answers provided for interviewer calibration
```

**Expected Output Size**: 300-350 lines JSON

---

### Subtask 3: Interview Recommendation & Hiring Decision
**Agent**: Recruitment & Hiring Specialist Agent
**Goal**: Synthesize screening and technical assessment, provide hiring recommendation
**Input Variables**: `subtask_1_output`, `subtask_2_output`, `role`, `candidate`
**Output Variables**: `interview_summary`, `hiring_recommendation`, `onboarding_plan`

**Prompt**:
```
You are the Recruitment & Hiring Specialist agent providing final hiring recommendation.

CONTEXT:
- Role: {{role.title}} ({{role.level}})
- Candidate: {{candidate.name}}
- Screening Score: {{subtask_1_output.screening_score.percentage}}%
- Technical Assessment: {{subtask_2_output}} (assume hypothetical strong performance: 85/100)
- Skills Match: {{subtask_1_output.skills_match.match_percentage}}%

TASK:
Synthesize all data and provide comprehensive hiring recommendation:

1. **Interview Performance Summary**
   Aggregate scores from screening + technical assessment:
   - Resume screening: {{subtask_1_output.screening_score.total}}/80 points
   - Technical depth: [Assume 35/40 based on strong performance]
   - Problem-solving: [Assume 26/30]
   - System design: [Assume 17/20]
   - Cultural fit: [Assume 9/10]

   **Total Score**: Calculate weighted average
   **Percentile**: Compare to historical candidate performance

2. **Strengths & Weaknesses Analysis**
   **Strengths**:
   - What does candidate excel at? (with evidence from interview)
   - What makes them stand out from other candidates?
   - Where will they add immediate value to the team?

   **Weaknesses/Growth Areas**:
   - What skills are missing or weak? (identify gaps)
   - Are gaps trainable or fundamental?
   - How significant are gaps for role success?

3. **Risk Assessment**
   Evaluate hiring risks:
   - **Technical risk**: Can they perform at required level? (Low/Medium/High)
   - **Team fit risk**: Will they collaborate effectively? (Low/Medium/High)
   - **Retention risk**: Flight risk indicators (compensation expectations, career goals)
   - **Ramp-up time**: How long to productivity? (30/60/90 days)

4. **Compensation Recommendation**
   Based on:
   - Market data for {{role.title}} in {{candidate.location}}
   - Candidate's current compensation (estimate from company/level)
   - Candidate's performance in interview
   - Internal equity (compare to existing team members at same level)

   Provide:
   - Base salary range: $XXX,XXX - $XXX,XXX AUD
   - Equity/Stock options: X,XXX options (if applicable)
   - Total compensation: $XXX,XXX AUD

5. **Hiring Decision Matrix**
   Use 4-quadrant framework:

   | Performance | Culture Fit | Decision |
   |-------------|-------------|----------|
   | High | High | **STRONG YES** - Extend offer immediately |
   | High | Low | **YES (with coaching)** - Hire, provide mentorship |
   | Low | High | **MAYBE** - Check for specific skill gaps, trainable? |
   | Low | Low | **NO** - Thank and close out |

6. **Onboarding Plan** (if hired)
   30-60-90 day plan:
   - **Day 1-30**: Ramp-up (codebase, tooling, team processes)
   - **Day 31-60**: Deliver first project (shadowing + independent work)
   - **Day 61-90**: Full productivity (on-call rotation, independent projects)

OUTPUT FORMAT (JSON):
{
  "interview_summary": {
    "candidate": "Jane Smith",
    "role": "Senior Site Reliability Engineer (L5)",
    "interview_date": "2025-10-11",
    "interviewers": ["Mike Rodriguez (SRE Lead)", "Sarah Chen (Engineering Manager)"],
    "overall_score": {
      "resume_screening": 77,
      "technical_depth": 35,
      "problem_solving": 26,
      "system_design": 17,
      "cultural_fit": 9,
      "total": 164,
      "max": 180,
      "percentage": 91.1,
      "percentile": "Top 10% of candidates (90th percentile)"
    }
  },
  "strengths": [
    {
      "area": "Kubernetes Expertise",
      "evidence": "Expert-level answers on control plane architecture, troubleshooting CrashLoopBackOff with systematic 7-step process, CKA certified",
      "impact": "Can immediately contribute to Kubernetes migration and mentor team"
    },
    {
      "area": "Incident Response",
      "evidence": "Demonstrated structured approach to production outage (SEV classification, war room, rollback strategy, communication). Reduced MTTR by 67% at Atlassian.",
      "impact": "Strengthens on-call rotation, brings SRE best practices"
    },
    {
      "area": "Communication",
      "evidence": "Explained pod networking to non-technical audience clearly using analogies, strong written communication (GitHub README quality)",
      "impact": "Can bridge technical-business gap, document effectively"
    }
  ],
  "weaknesses": [
    {
      "area": "Azure Experience",
      "gap": "No hands-on Azure experience (AWS only)",
      "severity": "Low",
      "trainable": "Yes - AWS skills transfer well, Azure fundamentals course + paired programming for 2 weeks",
      "mitigation": "Assign Azure-focused project in first 60 days with senior Azure engineer as mentor"
    },
    {
      "area": "Leadership Experience",
      "gap": "Limited formal mentorship experience (mentored 1 junior engineer)",
      "severity": "Low",
      "trainable": "Yes - natural fit for Senior role, can grow into Staff (L6) with mentorship coaching",
      "mitigation": "Assign 1-2 junior engineers to mentor, enroll in leadership training"
    }
  },
  "risk_assessment": {
    "technical_risk": {
      "level": "Low",
      "rationale": "91% interview score, expert Kubernetes/Python, strong problem-solving, proven production experience at scale"
    },
    "team_fit_risk": {
      "level": "Low",
      "rationale": "Collaborative in conflict resolution scenario, curious (asked 5 insightful questions), no ego issues"
    },
    "retention_risk": {
      "level": "Medium",
      "rationale": "Moved from REA to Atlassian after 3 years (seeking growth). Likely to stay 2-3 years if career growth visible (Staff L6 path).",
      "mitigation": "Clear promotion path to Staff within 18-24 months, interesting technical challenges (multi-region DR)"
    },
    "ramp_up_time": {
      "estimate": "45 days to full productivity",
      "rationale": "Strong foundation (Kubernetes, Terraform, Python), Azure learning curve = 2 weeks, domain knowledge (platform engineering) = 1 month"
    }
  },
  "compensation_recommendation": {
    "market_data": {
      "role": "Senior SRE (L5)",
      "location": "Melbourne, Australia",
      "market_range": "$140K - $170K AUD base salary",
      "source": "Levels.fyi, Seek.com.au, internal benchmarking"
    },
    "candidate_current_comp": {
      "estimate": "$150K AUD (Atlassian SRE II)",
      "increase_expectation": "10-20% for lateral move, 20-30% for promotion"
    },
    "offer_recommendation": {
      "base_salary": "$165,000 AUD",
      "rationale": "Top 10% candidate (91% score), +10% above midpoint to secure acceptance",
      "equity": "10,000 stock options (4-year vest, 1-year cliff)",
      "sign_on_bonus": "$10,000 AUD (to offset Atlassian equity loss)",
      "total_comp_year_1": "$180,000 AUD (base + bonus + equity value)",
      "benefits": "Standard package (health insurance, 4 weeks PTO, learning budget $5K)"
    },
    "internal_equity_check": {
      "comparable_employees": "2 existing Senior SREs at $155K-$160K",
      "equity_concern": "Low - offer is +3% above highest paid Senior SRE, justified by top 10% performance",
      "compression_risk": "Monitor - may need to adjust existing team members in next review cycle"
    }
  },
  "hiring_decision": {
    "recommendation": "✅ STRONG YES - Extend offer immediately",
    "confidence": "Very High (91% score, low risk, strong culture fit)",
    "decision_matrix": {
      "performance": "High (91%)",
      "culture_fit": "High (9/10)",
      "quadrant": "STRONG YES"
    },
    "rationale": "Jane is a top 10% candidate with expert Kubernetes skills, proven incident response experience at Atlassian (Tier 1 company), strong communication, and collaborative mindset. Minor Azure gap is easily trainable. At $165K base salary, she's a high-value hire who will immediately strengthen on-call rotation and mentor team. Low retention risk if clear promotion path to Staff (L6) within 18-24 months.",
    "approval_chain": [
      {"role": "Hiring Manager", "approver": "Sarah Chen", "status": "Pending"},
      {"role": "Engineering Director", "approver": "Alex Johnson", "status": "Pending"},
      {"role": "HR Comp Review", "approver": "HR Team", "status": "Pending"}
    ]
  },
  "onboarding_plan": {
    "day_1_30": {
      "focus": "Ramp-up and knowledge transfer",
      "activities": [
        "Week 1: Codebase walkthrough, dev environment setup, team intros",
        "Week 2: Shadow on-call engineer, review incident runbooks",
        "Week 3: Azure fundamentals training (paired with Azure expert)",
        "Week 4: Complete first small project (Terraform module for new service)"
      ],
      "success_criteria": "Can navigate codebase, understand on-call processes, basic Azure familiarity"
    },
    "day_31_60": {
      "focus": "Deliver first independent project",
      "activities": [
        "Project: Migrate 3 microservices to Kubernetes (with code review support)",
        "Join on-call rotation (secondary, shadowing primary)",
        "Azure hands-on: Deploy test environment in Azure (with mentor)",
        "Team contribution: Improve Grafana dashboards based on incident learnings"
      ],
      "success_criteria": "Completed Kubernetes migration, comfortable with on-call, can deploy Azure resources"
    },
    "day_61_90": {
      "focus": "Full productivity and ownership",
      "activities": [
        "Project: Design multi-region DR strategy (Staff L6 level work)",
        "Primary on-call rotation (independent)",
        "Mentorship: Assigned 1 junior engineer to mentor",
        "Team leadership: Lead incident post-mortem review sessions"
      ],
      "success_criteria": "Operating independently, on-call without escalations, mentoring others, contributing to team processes"
    }
  },
  "next_steps": {
    "immediate": [
      "Send offer letter within 24 hours (competitive market, prevent counter-offer risk)",
      "Schedule call with hiring manager to discuss role, team, and career path",
      "Prepare onboarding materials (codebase docs, team handbook, runbooks)"
    ],
    "if_offer_declined": [
      "Ask for feedback (compensation? role scope? company concerns?)",
      "Consider counter-offer if compensation issue and within budget ($5K flex)",
      "Add to talent pipeline for future opportunities"
    ]
  }
}

QUALITY CRITERIA:
✅ Interview summary aggregates all scores with percentile ranking
✅ Strengths and weaknesses evidence-based (not generic)
✅ Risk assessment quantified (Low/Medium/High) with mitigation
✅ Compensation recommendation backed by market data and internal equity
✅ Hiring decision follows objective matrix (not gut feel)
✅ Onboarding plan specific with 30/60/90 day milestones
```

**Expected Output Size**: 350-400 lines JSON

---

## Final Output Aggregation

After all subtasks complete, aggregate into comprehensive hiring recommendation:

```json
{
  "executive_summary": {
    "candidate": "Jane Smith",
    "role": "Senior Site Reliability Engineer (L5)",
    "recommendation": "✅ STRONG YES - Extend offer immediately",
    "overall_score": "91% (Top 10% of candidates)",
    "key_strengths": ["Expert Kubernetes", "Incident Response", "Strong Communication"],
    "compensation": "$165K base + $10K sign-on + 10K options = $180K total comp"
  },
  "screening_analysis": "{{subtask_1_output}}",
  "technical_assessment": "{{subtask_2_output}}",
  "hiring_recommendation": "{{subtask_3_output}}"
}
```

## Context Enrichment Flow

**Subtask 1** → **Subtask 2**:
- Skills match → Tailor interview questions to candidate's strengths/gaps
- Experience level → Adjust difficulty (Senior vs. Staff vs. Principal)

**Subtask 2** → **Subtask 3**:
- Technical performance → Hiring decision confidence
- Cultural fit assessment → Team fit risk evaluation

**Subtask 1 + 2 + 3** → **Final Report**:
- Comprehensive hiring packet for approvals
- Data-driven compensation recommendation
- Onboarding plan ready to execute

## Success Metrics

**Baseline (Before Prompt Chain)**:
- Candidate quality prediction: 60% accuracy
- Interview-to-hire conversion: 25%
- Time-to-hire: 45 days

**Target (With Prompt Chain)**:
- Candidate quality prediction: 90% accuracy (+50% improvement)
- Interview-to-hire conversion: 40% (+60% improvement due to better screening)
- Time-to-hire: 30 days (-33% reduction)

## Usage Example

```bash
python claude/tools/orchestration/prompt_chain_orchestrator.py \
  --chain-id candidate_screening_assessment_interview_chain \
  --workflow-file claude/workflows/prompt_chains/candidate_screening_assessment_interview_chain.md \
  --input '{
    "job_req_id": "JR-2025-089",
    "role": {
      "title": "Senior Site Reliability Engineer",
      "level": "Senior (L5)",
      "team": "Platform Engineering",
      "required_skills": ["Kubernetes", "Terraform", "Python", "Azure/AWS"],
      "preferred_skills": ["GitOps", "Prometheus", "Incident Response"],
      "years_experience": "5-8 years"
    },
    "candidate": {
      "name": "Jane Smith",
      "resume_url": "https://linkedin.com/in/janesmith",
      "linkedin_profile": "https://linkedin.com/in/janesmith",
      "github_profile": "https://github.com/janesmith",
      "current_company": "Atlassian",
      "current_title": "SRE II",
      "years_experience": 6
    }
  }'
```

## Notes

- **Subtask 1** provides structured resume screening to filter out weak candidates early
- **Subtask 2** designs tailored technical assessment (not generic whiteboard questions)
- **Subtask 3** provides data-driven hiring decision with compensation and onboarding plan
- All evaluations use objective rubrics to reduce bias
- Compensation recommendations consider market data and internal equity
- Onboarding plan ensures new hire ramps up effectively
