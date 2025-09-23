# Rice Market AI System - Documentation Index
# Path: /docs/DOCUMENTATION_INDEX.md
# Centralized guide to all project documentation for quick team onboarding

## Quick Start for New Team Members

### Essential Reading Order
1. **Project Overview**: `/README.md` - Start here for project vision and structure
2. **Statement of Work**: `/docs/milestones/ms1/Statement of Work- Rice Market AI System_Rev.04.pdf` - Detailed project scope and objectives
3. **GitHub Workflow**: `/docs/onboarding/github-collaboration-guide.md` - How we work together
4. **Development Setup**: `/docs/onboarding/python-setup-guide.md` - Environment configuration

## Documentation by Category

### 🎯 Project Planning & Milestones
- **Statement of Work**: `docs/milestones/ms1/Statement of Work- Rice Market AI System_Rev.04.pdf`
- **Milestone 1**: `docs/milestones/ms1/Milestone 1 _ AC215.pdf` - Project Proposal & Team Formation
- **Milestone 2**: `docs/milestones/ms2/Milestone 2 _ AC215.pdf` - MLOps Infrastructure
- **Milestone 3**: `docs/milestones/ms3/Milestone 3 _ AC215.pdf` - Midterm Presentation
- **Milestone 4**: `docs/milestones/ms4/Milestone 4 _ AC215.pdf` - Full-Stack Development
- **Milestone 5**: `docs/milestones/ms5/Milestone 5 _ AC215.pdf` - Deployment & Scaling

### 🚀 Onboarding Guides
- **GitHub Collaboration**: `docs/onboarding/github-collaboration-guide.md` - GitFlow workflow and best practices
- **Python Setup**: `docs/onboarding/python-setup-guide.md` - Python environment configuration
- **Python Verification**: `docs/onboarding/python-verification-guide.md` - Verify your Python installation
- **Requirements Management**: `docs/onboarding/python-requirements-setup.md` - Managing dependencies
- **Docker Setup**: `docs/onboarding/docker-containerization-guide.md` - Container development
- **Docker Test Service**: `docs/onboarding/docker-test-service-files.md` - Testing with Docker
- **FastAPI Setup**: `docs/onboarding/fastapi-environment-setup.md` - API development setup

### 🏗️ Architecture & Design
- **Good vs Bad Ideas**: `docs/Ideation/Guide_ Good vs Bad Idea for AC215.pdf` - Design principles and best practices

### 💻 Service Documentation
- **NL+SQL Agent**: `services/nl-sql-agent/README.md` - Natural Language to SQL service
- **RAG Orchestrator**: `services/rag-orchestrator/README.md` - Document processing service
- **Time-Series Forecasting**: `services/ts-forecasting/README.md` - Price prediction service

### 📊 Data Management
- **Data Overview**: `data/data-readme.md` - Data directory structure and guidelines
- **Company Excel Files**: `data/raw/company_excel_files/README.md` - Handling sensitive company data

### 👥 Team Collaboration
- **Feature Branches Guide**: `docs/team/feature-branches-guide.md` - Current active branches and workflow

## Quick Links by Role

### For Backend Developers
1. `/docs/onboarding/fastapi-environment-setup.md`
2. Service READMEs in `/services/*/README.md`
3. `/docs/onboarding/docker-containerization-guide.md`

### For ML Engineers
1. `/docs/milestones/ms2/Milestone 2 _ AC215.pdf` - MLOps setup
2. `/services/ts-forecasting/README.md` - Forecasting service
3. `/docs/onboarding/python-setup-guide.md` - Python environment

### For Data Engineers
1. `/data/data-readme.md` - Data structure overview
2. `/data/raw/company_excel_files/README.md` - Data privacy requirements
3. Service-specific data requirements in each service README

### For DevOps/Platform Engineers
1. `/docs/onboarding/docker-containerization-guide.md`
2. `/docs/onboarding/github-collaboration-guide.md`
3. All milestone PDFs for deployment requirements

## Documentation Standards

### When Creating New Documentation
1. **Location**: Place in appropriate directory (docs/, services/, data/)
2. **Naming**: Use descriptive names with hyphens (not spaces)
3. **Header**: Always include path comment at top of file
4. **Format**: Prefer Markdown (.md) for text documentation
5. **Updates**: Update this index when adding new documentation

### Documentation Review Schedule
- **Weekly**: Service READMEs should be updated with any API changes
- **Per Milestone**: Review and update onboarding guides
- **As Needed**: Update data documentation when schemas change

## Getting Help

If you can't find what you need:
1. Check this index first
2. Search the repository: `find . -name "*keyword*"`
3. Ask in the team chat
4. Contact the documentation maintainer

---
*Last Updated: September 23, 2024*
*Maintainer: AC215/E115 Rice Market AI System Team*  
*This is a living document - please update when adding new documentation*
