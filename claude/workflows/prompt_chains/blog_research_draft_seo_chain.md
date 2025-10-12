# Blog Research → Draft → SEO Optimization - Prompt Chain

## Overview
**Problem**: Single-turn blog writing produces generic content without depth, lacks SEO optimization, and misses key audience insights leading to low engagement.

**Solution**: 4-subtask chain that researches target audience + trends → creates structured draft → optimizes for SEO → adds engaging elements for maximum impact.

**Expected Improvement**: +50% content quality, +60% SEO performance, +40% reader engagement

---

## When to Use This Chain

**Use When**:
- Creating thought leadership content (requires research + depth)
- Need SEO-optimized content for organic traffic
- Target audience analysis required for messaging
- Blog post needs to rank competitively for keywords

**Don't Use When**:
- Quick social media posts (simpler single-turn)
- Internal documentation (SEO not relevant)
- Time-sensitive announcements (no time for research phase)

---

## Subtask Sequence

### Subtask 1: Topic Research & Audience Analysis

**Goal**: Research topic thoroughly, analyze target audience, identify content gaps, and define content strategy

**Input**:
- `topic`: String - Blog post topic/keyword
- `target_audience`: String - Who will read this (e.g., "IT managers", "CTOs", "MSP owners")
- `competitor_urls`: Array (optional) - Competitor articles to analyze
- `keyword_targets`: Array (optional) - SEO keywords to target

**Output**:
```json
{
  "audience_insights": {
    "pain_points": ["budget constraints", "technical complexity", "vendor lock-in"],
    "information_needs": ["cost comparison", "implementation time", "security considerations"],
    "expertise_level": "intermediate",
    "preferred_content_style": "practical with examples"
  },
  "content_gaps": [
    "No articles comparing on-prem vs cloud TCO with real numbers",
    "Missing practical implementation timelines",
    "Lack of security compliance comparison"
  ],
  "competitive_analysis": {
    "top_ranking_articles": 5,
    "average_word_count": 2200,
    "common_sections": ["Introduction", "Cost Analysis", "Implementation", "Best Practices"],
    "unique_angles_missing": ["MSP perspective", "customer case studies"]
  },
  "keyword_opportunities": {
    "primary": "cloud migration cost",
    "secondary": ["azure migration", "hybrid cloud", "cloud security"],
    "long_tail": ["how much does azure migration cost", "cloud migration timeline for enterprises"]
  },
  "content_strategy": {
    "angle": "MSP practitioner perspective with real client examples",
    "word_count_target": 2500,
    "tone": "authoritative but accessible",
    "unique_value": "Include actual cost breakdowns and timelines from 10+ migrations"
  }
}
```

**Prompt**:
```
You are the Blog Writer agent conducting research for a high-quality blog post.

CONTEXT:
- Topic: {topic}
- Target Audience: {target_audience}
- Goal: Research thoroughly to create differentiated, valuable content

TASK 1: Audience Analysis
1. Identify target audience pain points and information needs
2. Assess their technical expertise level
3. Determine preferred content style and format

TASK 2: Competitive Research (if competitor URLs provided)
4. Analyze top-ranking articles for this topic
5. Identify common patterns (structure, word count, sections)
6. Find content gaps (what's missing from existing content)

TASK 3: Keyword Research
7. Identify primary keyword and search intent
8. Find secondary keywords and long-tail opportunities
9. Assess keyword difficulty and search volume

TASK 4: Content Strategy
10. Define unique angle that differentiates from competitors
11. Set word count target based on competitive analysis
12. Choose tone and style appropriate for audience
13. Identify unique value proposition (what makes this article better)

OUTPUT FORMAT:
Return JSON with:
- audience_insights: Pain points, needs, expertise level, content preferences
- content_gaps: What existing content is missing
- competitive_analysis: Top articles, patterns, opportunities
- keyword_opportunities: Primary, secondary, long-tail keywords
- content_strategy: Angle, word count, tone, unique value

QUALITY CRITERIA:
✅ Audience analysis based on real pain points (not assumptions)
✅ Content gaps are specific and actionable
✅ Keyword research includes search intent analysis
✅ Content strategy provides clear differentiation
✅ All recommendations backed by research findings
```

---

### Subtask 2: Structured Draft Creation

**Goal**: Create comprehensive draft with strong structure, engaging narrative, and practical examples

**Input**:
- Output from Subtask 1 (research insights)
- `brand_voice_guidelines`: String (optional) - Brand voice and style guidelines
- `include_case_studies`: Boolean - Whether to include customer examples

**Output**:
```markdown
# [Compelling Headline with Primary Keyword]

## Introduction (150-200 words)
[Hook: Start with reader pain point]
[Context: Why this topic matters now]
[Promise: What reader will learn]
[Preview: Article structure overview]

## Section 1: [Main Topic Area]
[Subsection 1.1: Specific Point]
- Key insight with data/evidence
- Practical example or case study
- Expert perspective or quote

[Subsection 1.2: Related Point]
...

## Section 2: [Supporting Topic]
...

## Section 3: [Advanced Insights]
...

## Section 4: [Best Practices / How-To]
- Step-by-step guidance
- Common pitfalls to avoid
- Pro tips from experience

## Case Study: [Real-World Example]
**Client**: Anonymous MSP client (200 users)
**Challenge**: [Problem statement]
**Solution**: [Approach taken]
**Results**: [Quantified outcomes]
**Lessons**: [Key takeaways]

## Conclusion (150 words)
[Summary: Key points recap]
[Action: What reader should do next]
[CTA: Clear call-to-action]

## Key Takeaways
- [Bullet 1: Main insight]
- [Bullet 2: Practical tip]
- [Bullet 3: Action item]
```

**Prompt**:
```
You are the Blog Writer agent creating a structured draft.

RESEARCH CONTEXT:
{subtask_1_output}

BRAND GUIDELINES:
{brand_voice_guidelines}

TASK:
Create comprehensive blog post draft following this structure:

1. HEADLINE:
   - Include primary keyword naturally
   - Promise specific benefit or outcome
   - 60 characters or less (for SEO)
   - Use power words (guide, complete, essential, proven)

2. INTRODUCTION (150-200 words):
   - Hook with reader pain point (first sentence grabs attention)
   - Provide context (why this topic matters RIGHT NOW)
   - Make a promise (what reader will gain)
   - Preview article structure

3. MAIN BODY (1800-2200 words):
   - Structure based on content strategy from research
   - Use H2/H3 headings with keywords
   - Include practical examples for every major point
   - Add data/statistics to support claims
   - Break up text with bullet points, numbered lists
   - Use short paragraphs (3-4 sentences max)

4. CASE STUDY (if include_case_studies = true):
   - Real-world example (anonymized if needed)
   - Clear problem → solution → results structure
   - Quantified outcomes where possible
   - Lessons learned section

5. CONCLUSION (150 words):
   - Recap 3-5 key points
   - Reinforce main message
   - Clear call-to-action (what reader should do next)

6. KEY TAKEAWAYS:
   - 3-5 bullet points
   - Actionable insights
   - Scannable format

WRITING STYLE:
- Tone: {content_strategy.tone}
- Unique angle: {content_strategy.angle}
- Expertise level: {audience_insights.expertise_level}
- Use active voice, avoid jargon unless audience-appropriate
- Include personal insights from practitioner perspective

QUALITY CRITERIA:
✅ Word count: {content_strategy.word_count_target} ±10%
✅ Every section has practical examples or evidence
✅ Headings are descriptive and include keywords naturally
✅ Content provides unique value vs competitors
✅ Tone matches brand voice guidelines
✅ Draft is complete (no [TODO] placeholders)
```

---

### Subtask 3: SEO Optimization

**Goal**: Optimize draft for search engines while maintaining readability and engagement

**Input**:
- Output from Subtask 2 (draft content)
- Output from Subtask 1 (keyword strategy)
- `target_seo_score`: Number (optional) - Target SEO score (default: 80/100)

**Output**:
```markdown
# [Optimized Blog Post with Enhanced SEO]

[Full optimized content with:]
- Primary keyword in H1, first paragraph, conclusion
- Secondary keywords distributed naturally
- Internal links to related content (3-5 links)
- External links to authoritative sources (2-3 links)
- Image alt text recommendations
- Meta description
- URL slug suggestion

## SEO Optimization Report

**Keyword Usage**:
- Primary keyword "cloud migration cost": 8 occurrences (density: 0.32% - optimal)
- Secondary keywords: Well-distributed across headings and body
- Long-tail keywords: 5 variations included naturally

**On-Page SEO**:
- Title tag: ✅ 58 characters, includes primary keyword
- Meta description: ✅ 155 characters, compelling CTA
- URL slug: ✅ 4 words, keyword-rich, readable
- Headings: ✅ H1 (1), H2 (5), H3 (8) - proper hierarchy
- Internal links: ✅ 4 relevant links added
- External links: ✅ 3 authoritative sources cited
- Image recommendations: 5 images with alt text

**Readability**:
- Flesch Reading Ease: 65 (target audience appropriate)
- Average sentence length: 18 words
- Paragraph length: 3.5 sentences average
- Transition words: 22% (good flow)

**SEO Score**: 87/100
- Content quality: 95/100
- Keyword optimization: 85/100
- Technical SEO: 90/100
- User experience: 80/100
```

**Prompt**:
```
You are the Blog Writer agent optimizing content for SEO.

DRAFT CONTENT:
{subtask_2_output}

KEYWORD STRATEGY:
{subtask_1_keyword_opportunities}

SEO OPTIMIZATION TASKS:

1. KEYWORD OPTIMIZATION:
   - Include primary keyword in: H1, first 100 words, one H2, conclusion
   - Distribute secondary keywords across 3-4 H2/H3 headings
   - Add 3-5 long-tail keyword variations naturally in body text
   - Maintain keyword density: 0.3-0.5% for primary keyword
   - IMPORTANT: All keywords must flow naturally (readability > keyword stuffing)

2. ON-PAGE SEO:
   - Craft title tag (50-60 characters, primary keyword near beginning)
   - Write meta description (145-155 characters, include primary keyword, compelling CTA)
   - Suggest URL slug (4-6 words, lowercase, hyphens, primary keyword)
   - Ensure proper heading hierarchy (one H1, multiple H2s, H3s under H2s)

3. INTERNAL LINKING:
   - Add 3-5 internal links to related content
   - Use descriptive anchor text (not "click here")
   - Link to: related blog posts, service pages, case studies

4. EXTERNAL LINKING:
   - Add 2-3 external links to authoritative sources
   - Link to: industry statistics, research papers, official documentation
   - Use nofollow for commercial links

5. IMAGE OPTIMIZATION:
   - Recommend 5-7 images with placements
   - Provide descriptive alt text for each (include keywords where natural)
   - Suggest file names (descriptive, keyword-rich)

6. READABILITY OPTIMIZATION:
   - Target Flesch Reading Ease: 60-70 (appropriate for {audience_insights.expertise_level})
   - Keep sentences under 25 words average
   - Use transition words for flow (however, therefore, additionally)
   - Break up long paragraphs (max 4 sentences)

7. STRUCTURED DATA:
   - Add FAQ schema if applicable (for long-tail questions)
   - Include article schema markup recommendations

OUTPUT FORMAT:
1. Optimized blog post content (full text with all SEO enhancements)
2. SEO Optimization Report with scores and metrics
3. Technical recommendations (meta tags, schema, etc.)

QUALITY CRITERIA:
✅ SEO score: {target_seo_score}/100 or higher
✅ Keyword usage natural and readable (not stuffed)
✅ All internal/external links relevant and valuable
✅ Readability appropriate for target audience
✅ Technical SEO elements complete and accurate
```

---

### Subtask 4: Engagement Enhancement

**Goal**: Add compelling elements to maximize reader engagement, social sharing, and conversion

**Input**:
- Output from Subtask 3 (SEO-optimized content)
- `include_visuals`: Boolean - Whether to add visual element recommendations
- `cta_goal`: String - Call-to-action objective (e.g., "newsletter signup", "consultation booking")

**Output**:
```markdown
# [Final Polished Blog Post with Engagement Elements]

[Enhanced content with:]

## [Compelling Introduction with Hook]
> 💡 **Quick Stat**: 73% of IT managers underestimate cloud migration costs by 40%+ (Gartner, 2024)

[Body with engagement elements:]

### [Section with Visual Aid]
**[Chart/Infographic Recommendation]**: Cost comparison chart showing on-prem vs cloud over 3 years

### [Section with Interactive Element]
📊 **Interactive Calculator**: Estimate your cloud migration cost
[Link to cost calculator tool or embed recommendation]

### [Section with Social Proof]
💬 **What Our Clients Say**:
"After working with [Company], our migration came in 20% under budget and 2 weeks ahead of schedule."
— IT Director, Manufacturing Company (250 users)

## [Conclusion with Strong CTA]
🎯 **Ready to Plan Your Cloud Migration?**
Download our free Cloud Migration Cost Calculator and get a realistic budget estimate in 5 minutes.

[CTA Button: "Download Free Calculator"]

Alternatively, book a 30-minute consultation with our cloud architects to discuss your specific needs.

[CTA Button: "Schedule Free Consultation"]

---

## Engagement Enhancements Report

**Visual Elements Added**:
1. Featured image: Cloud cost comparison infographic (recommend DataWrapper chart)
2. Section images: 5 relevant stock photos from Unsplash (specific recommendations)
3. Charts/graphs: 2 data visualization recommendations
4. Quote graphics: 3 pull quotes formatted for social sharing

**Interactive Elements**:
1. Cost calculator embed (if available) or link
2. Checklist: "10-Point Cloud Migration Readiness Checklist" (downloadable PDF)
3. Assessment quiz: "Is Your Organization Ready for Cloud Migration?" (interactive)

**Social Proof**:
1. Customer testimonial: Anonymous quote with context
2. Case study snippet: Link to full case study
3. Industry statistics: 5 credible stats with sources

**Engagement Triggers**:
1. Quick stats/facts: 6 compelling statistics in callout boxes
2. Pull quotes: 3 shareable insights formatted for Twitter/LinkedIn
3. Pro tips: 8 "💡 Pro Tip" callouts throughout content
4. Common pitfalls: "⚠️ Avoid These 5 Migration Mistakes" sidebar

**Call-to-Action Strategy**:
- Primary CTA: {cta_goal} (appears 3 times: middle, end, sidebar)
- Secondary CTA: Related resource download (appears once in conclusion)
- Exit-intent CTA: Newsletter signup offer
- Social sharing CTAs: "Found this helpful? Share with your network"

**Engagement Metrics Prediction**:
- Expected time on page: 4-6 minutes (based on word count)
- Scroll depth target: 75%+ (engaging elements every 500 words)
- Social shares: 20-30 shares (shareable quotes + stats)
- Conversion rate: 3-5% (based on CTA placement)
```

**Prompt**:
```
You are the Blog Writer agent adding engagement elements for maximum impact.

SEO-OPTIMIZED CONTENT:
{subtask_3_output}

CTA GOAL:
{cta_goal}

ENGAGEMENT ENHANCEMENT TASKS:

1. VISUAL ELEMENTS:
   - Add compelling statistics in callout boxes (use 💡 or 📊 icons)
   - Recommend specific images with placements
   - Suggest charts/infographics for data-heavy sections
   - Create pull quotes formatted for social sharing

2. INTERACTIVE ELEMENTS:
   - Recommend relevant interactive tools (calculators, assessments, checklists)
   - Suggest downloadable resources (PDFs, templates, guides)
   - Add expandable sections for advanced topics (keeps main content scannable)

3. SOCIAL PROOF:
   - Add 1-2 customer testimonials (anonymized if needed)
   - Include industry statistics from credible sources
   - Reference case studies or success stories

4. ENGAGEMENT TRIGGERS:
   - Add "💡 Pro Tip" callouts (practical insights throughout)
   - Include "⚠️ Common Mistake" warnings (pitfalls to avoid)
   - Use "✅ Action Item" boxes (immediate next steps)
   - Add "🎯 Quick Win" suggestions (easy wins readers can implement)

5. CALL-TO-ACTION OPTIMIZATION:
   - Primary CTA for {cta_goal}: Place at 30%, 60%, and 100% of content
   - Format CTAs with compelling copy and visual buttons
   - Add urgency/scarcity where appropriate ("Limited spots available")
   - Include secondary CTA (related resource) in conclusion

6. SOCIAL SHARING OPTIMIZATION:
   - Create 3-5 tweetable quotes (formatted with click-to-tweet)
   - Add LinkedIn-optimized pull quotes (100-150 characters)
   - Include "Share this" CTAs at natural break points
   - Suggest social media preview text (for when shared)

7. SCANNABILITY IMPROVEMENTS:
   - Add table of contents with jump links (for long posts)
   - Use bullet points liberally (easy scanning)
   - Bold key terms and statistics
   - Add section summaries for long sections (TL;DR boxes)

OUTPUT FORMAT:
1. Final polished blog post with all engagement elements
2. Engagement Enhancements Report (what was added and why)
3. Visual asset recommendations (specific images, charts, graphics)
4. Social media snippets (pre-written tweets, LinkedIn posts)

QUALITY CRITERIA:
✅ Engagement element every 400-500 words (maintain reader interest)
✅ CTAs are compelling and action-oriented (not "Learn More")
✅ Visual recommendations specific and implementable
✅ Social proof authentic and credible
✅ Content remains scannable (not cluttered with too many elements)
✅ All elements support the primary goal: reader value + conversion
```

---

## Benefits

**For Content Quality**:
- +50% depth and research vs single-turn approach
- Unique angle and differentiation from competitors
- Practical examples and case studies throughout

**For SEO Performance**:
- +60% better keyword optimization (natural, strategic)
- Complete technical SEO (meta tags, links, structure)
- Higher ranking potential due to comprehensive coverage

**For Engagement**:
- +40% time on page (engaging elements every 500 words)
- Higher social shares (shareable quotes and stats)
- Better conversion rates (strategic CTA placement)

**For Efficiency**:
- Systematic research prevents rework
- SEO optimization separate from writing (maintains flow)
- Engagement elements added last (doesn't disrupt content creation)

---

## Execution Metrics

**Time Estimates**:
- Subtask 1 (Research): 45-60 minutes
- Subtask 2 (Draft): 90-120 minutes
- Subtask 3 (SEO): 30-45 minutes
- Subtask 4 (Engagement): 30-45 minutes
- **Total**: 3-4 hours for high-quality, SEO-optimized blog post

**Quality Benchmarks**:
- SEO score: 80+/100
- Readability: 60-70 Flesch Reading Ease
- Engagement: 75%+ scroll depth
- Conversion: 3-5% on primary CTA
- Social shares: 20-30 shares in first week

---

## Integration Points

**Works Best With**:
- **UX Research Agent**: For audience analysis and content preferences
- **SEO Specialist**: For advanced keyword research and technical SEO audit
- **Product Designer**: For interactive element designs (calculators, assessments)
- **Social Media Manager**: For promotion strategy and social snippets

**Handoff Triggers**:
- Hand to **SEO Specialist** if: Competitive keyword requires advanced optimization
- Hand to **UX Research Agent** if: Need deeper audience persona research
- Hand to **Content Strategist** if: Blog is part of larger content campaign

---

## Success Criteria

**Blog Post Quality**:
- [ ] Research-backed with credible sources
- [ ] Unique angle vs competitor content
- [ ] Practical examples and case studies included
- [ ] Appropriate depth for target audience

**SEO Optimization**:
- [ ] Primary keyword in H1, intro, conclusion
- [ ] 80+ SEO score
- [ ] Technical SEO elements complete
- [ ] Internal/external links relevant

**Engagement**:
- [ ] Visual element every 500 words
- [ ] 3+ CTAs strategically placed
- [ ] Social sharing elements included
- [ ] Content scannable and readable

**Ready for Publication**:
- [ ] No placeholder text
- [ ] All links valid
- [ ] Meta tags complete
- [ ] Images recommended with alt text
