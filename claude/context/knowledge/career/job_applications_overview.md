# Job Applications Repository

This repository contains materials and workflows for managing job applications, CV customization, and career development.

## CV Creation Methods

This repository supports two CV creation approaches:

### Full CV (Detailed)
- **Purpose**: Direct applications, senior roles, detailed competency demonstration
- **Format**: 2-3 line bullets with comprehensive Action-Result framework
- **Process**: See `/methodology/cv-creation-process.md`
- **Keywords**: Maximum ATS coverage with detailed storytelling

### Brief CV (Ultra-concise) 
- **Purpose**: Quick-screening applications, recruiter-driven roles, multiple applications
- **Format**: 10-20 word bullets with bold-first outcomes using symbols (→, ~, —)
- **Process**: See `/methodology/au_cv_prompt_naythan_style.md`  
- **Keywords**: High keyword density through concise format

### Database Updates (August 2025)
- Added comprehensive certifications database in `personal_profile.json`
- Corrected Windows 10/2000-device metrics in OneAdvanced experiences
- Enhanced validation steps to prevent terminology drift from source data

## Structure

```
├── source-files/           # Core source materials
│   ├── **EMPLOYER-SPECIFIC DATABASES** (use for CV creation):
│   │   ├── experiences_zetta.json         # 5 experiences (5 bullets)
│   │   ├── experiences_telstra.json       # 17 experiences (7 bullets)
│   │   ├── experiences_oneadvanced.json   # 26 experiences (7 bullets)
│   │   ├── experiences_viadex.json        # 4 experiences (2 bullets)
│   │   └── experiences_halsion.json       # 8 experiences (2 bullets)
│   ├── feedback_database.json         # Professional testimonials & endorsements
│   ├── usp_database.json              # Unique selling points & positioning
│   ├── JSON-USAGE-GUIDE.md            # Guide for querying databases
│   ├── migration-validation.md         # Database validation report
│   ├── experiences_markdown.md         # Legacy: Complete professional experience
│   ├── detailed-star.md                # STAR method examples
│   ├── action_result_examples_markdown.md  # Action-result bullet points
│   └── Naythan Dawe - CV - *.md        # Role-specific CV templates
├── methodology/            # Application frameworks and methods
│   ├── cv-creation-process.md        # Systematic CV creation workflow
│   ├── cv-bullet-point-framework.md  # Action-Result CV bullet framework
│   └── naythan-unique-selling-points.md  # Legacy: USPs (use usp_database.json instead)
├── scripts/               # Conversion and automation tools
│   ├── convert-cv-libreoffice.sh     # Recommended conversion method
│   ├── convert-cv-*.sh               # Alternative conversion methods
│   ├── setup-pandoc.sh               # First-time setup
│   └── reference.docx                # Formatting reference for pandoc
├── applications/          # Job-specific applications
│   ├── microsoft/ats/                # Microsoft Account Technology Strategist
│   ├── pwc/                          # PwC Senior BRM application
│   └── deloitte/                     # Deloitte consultant roles
├── collateral/            # Reference documents
└── examples/              # Reference examples (legacy)
```

## Key Resources

### CV Bullet Point Framework
Located in `methodology/cv-bullet-point-framework.md` - this is the core methodology for creating impactful CV content using the Action-Result method.

**Formula: [POWER VERB] + [SCOPE/CONTEXT] + [METHOD] + [QUANTIFIED RESULT]**

### Professional Background Summary
- 12+ years senior technical consulting experience
- Expertise in customer success, cloud migrations, enterprise architecture
- Proven track record with C-level stakeholders and complex technical projects
- Cross-cultural experience (Australia, UK, Timor-Leste)
- Quantified achievements in revenue generation, cost savings, and process improvement

### Available CV Templates
- **AWS TAM** - Technical Account Manager focus
- **CSM** - Customer Success Manager emphasis  
- **MS ATS** - Microsoft-focused solutions

## Usage

This repository supports rapid, high-quality job application creation through:

### **1. Job Analysis & CV Creation**
- **Quick Start**: Say "we are going to update/create a CV" to trigger systematic process
- **Process Guide**: Follow `/methodology/cv-creation-process.md` for complete workflow
- **Database Query**: Use employer-specific JSON files (experiences_*.json)
- **USP Positioning**: Query `source-files/usp_database.json`
- **Testimonials**: Query `source-files/feedback_database.json`
- Create customized CVs using Action-Result framework
- Apply role-specific templates (TAM, CSM, Solutions Architect)

### **2. CV Conversion Workflow**
```bash
# Recommended: LibreOffice conversion (best formatting)
cd scripts
./convert-cv-libreoffice.sh input.md output.docx

# Alternative: Pandoc with reference document
./convert-cv-final.sh input.md output.docx
```

### **3. Quality Assurance**
- All bullet points follow Action-Result framework
- Every achievement backed by detailed STAR examples
- Consistent messaging across all materials

### **4. Writing Rules**
- Australian English throughout
- 14-word sentences (max 20 words)
- Sentence case only
- Bold only at sentence start for emphasis
- Never merge experiences across roles