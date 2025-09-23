# GitHub Collaboration Guide for AC215/E115 Team
# Professional GitFlow-based workflow for microservices development

## Purpose of This Guide

This guide establishes our team's Git workflow based on industry-standard GitFlow practices, adapted for our microservices architecture. You'll learn how to contribute safely, review code effectively, and maintain a clean project history that documents our technical decisions.

## Table of Contents
1. [Understanding Our Branching Strategy](#branching-strategy)
2. [Environment Setup](#environment-setup)
3. [Daily Development Workflow](#daily-workflow)
4. [Feature Branch Management](#feature-branches)
5. [Pull Request Process](#pull-requests)
6. [Code Review Guidelines](#code-review)
7. [Commit Message Standards](#commit-standards)
8. [Release Management](#releases)
9. [Finding Technical Decisions](#finding-decisions)
10. [Troubleshooting](#troubleshooting)

## Understanding Our Branching Strategy {#branching-strategy}

### Branch Types
- **main**: Production-ready code. Protected branch - no direct commits
- **develop**: Integration branch for features. Always in working state
- **feature/**: Individual development branches (e.g., `feature/add-redis-cache`)
- **release/**: Preparation for production release (e.g., `release/1.2.0`)
- **hotfix/**: Emergency production fixes (e.g., `hotfix/auth-bypass`)

### Branch Flow Rules
```
feature/* → develop → release/* → main
hotfix/* → main + develop
```

## Environment Setup {#environment-setup}

### Initial Configuration
```bash
# Set your identity
git config --global user.name "Your Full Name"
git config --global user.email "your.email@harvard.edu"

# Enable commit signing (recommended)
git config --global commit.gpgsign true

# Configure aliases for efficiency
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.st status
git config --global alias.lg "log --graph --pretty=format:'%Cred%h%Creset -%C(yellow)%d%Creset %s %Cgreen(%cr) %C(bold blue)<%an>%Creset' --abbrev-commit"

# Enable automatic rebase for cleaner history
git config --global pull.rebase true

# Better merge conflict display
git config --global merge.conflictstyle diff3
```

### Repository Setup
```bash
# Clone repository
git clone https://github.com/ltphongssvn/ac215e115groupproject.git
cd ac215e115groupproject

# Set up develop branch tracking
git checkout -b develop origin/develop

# Install pre-commit hooks
pip install pre-commit
pre-commit install
```

## Daily Development Workflow {#daily-workflow}

### Start Your Day
```bash
# 1. Sync with team's work
git checkout develop
git pull origin develop

# 2. Check for dependency changes
git diff HEAD@{1} HEAD --name-only | grep requirements
# If changes found, update environment:
pip install -r requirements/base.txt

# 3. Create feature branch
git checkout -b feature/descriptive-name
```

### During Development
```bash
# Check status frequently
git status

# Stage changes selectively
git add -p  # Interactive staging

# Commit with meaningful messages
git commit -m "feat(component): Add specific functionality

- Detailed change item 1
- Detailed change item 2

Resolves #issue-number"

# Push regularly for backup
git push -u origin feature/your-branch
```

### End of Day
```bash
# Ensure all changes committed
git status

# Push to remote
git push origin feature/your-branch

# Create draft PR if not ready for review
```

## Feature Branch Management {#feature-branches}

### Naming Conventions
```
feature/service-description
bugfix/issue-number-description
hotfix/critical-issue
```

Examples:
- `feature/api-gateway-jwt-auth`
- `bugfix/67-numpy-compatibility`
- `hotfix/database-connection-leak`

### Creating Feature Branch
```bash
# Always start from updated develop
git checkout develop
git pull origin develop
git checkout -b feature/your-feature

# Push to establish remote tracking
git push -u origin feature/your-feature
```

### Keeping Branch Updated
```bash
# Fetch latest changes
git fetch origin

# Rebase on develop
git checkout feature/your-branch
git rebase origin/develop

# Resolve conflicts if any
git add <resolved-files>
git rebase --continue

# Force push to feature branch only
git push --force-with-lease origin feature/your-branch
```

## Pull Request Process {#pull-requests}

### PR Template
```markdown
## Summary
Brief description of changes and motivation

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings
```

### Before Creating PR
```bash
# Update branch
git rebase origin/develop

# Run tests
pytest tests/
pre-commit run --all-files

# Review changes
git diff origin/develop...HEAD

# Clean commit history if needed
git rebase -i origin/develop
```

## Code Review Guidelines {#code-review}

### Review Focus Areas
1. **Correctness**: Logic and functionality
2. **Security**: Input validation, authentication
3. **Performance**: Efficiency, caching
4. **Maintainability**: Readability, documentation
5. **Testing**: Coverage, edge cases

### Review Etiquette
- Provide constructive feedback with examples
- Explain the "why" behind suggestions
- Approve promptly or request changes clearly
- Use "nit:" prefix for minor issues
- Suggest, don't demand

## Commit Message Standards {#commit-standards}

### Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code restructuring
- `perf`: Performance improvement
- `test`: Test changes
- `build`: Build/dependency changes
- `ci`: CI configuration
- `chore`: Maintenance

### Examples
```bash
# Feature commit
git commit -m "feat(api-gateway): Add JWT refresh token rotation

- Implement 7-day refresh token expiry
- Add token rotation on each refresh
- Store tokens in Redis

Improves security by preventing token replay attacks
Resolves #45"

# Bug fix commit
git commit -m "fix(ml-service): Handle edge cases in confidence scoring

- Fix division by zero error
- Clamp scores to [0,1] range
- Validate NaN values

Fixes #89"
```

## Release Management {#releases}

### Creating Release
```bash
# Start from develop
git checkout develop
git pull origin develop

# Create release branch
git checkout -b release/1.2.0

# Update versions and changelog
# Run full test suite
# Commit changes
git commit -m "chore(release): Prepare v1.2.0"

# After approval, merge to main
git checkout main
git merge --no-ff release/1.2.0
git tag -a v1.2.0 -m "Version 1.2.0"

# Merge back to develop
git checkout develop
git merge --no-ff release/1.2.0

# Clean up
git branch -d release/1.2.0
git push origin --delete release/1.2.0
```

### Hotfix Process
```bash
# Start from main
git checkout main
git checkout -b hotfix/critical-fix

# Make minimal fixes
# Test thoroughly
git commit -m "hotfix: Fix critical issue"

# Merge to both main and develop
git checkout main
git merge --no-ff hotfix/critical-fix
git tag -a v1.2.1 -m "Hotfix 1.2.1"

git checkout develop
git merge --no-ff hotfix/critical-fix
```

## Finding Technical Decisions {#finding-decisions}

### Search Commands
```bash
# Find package decisions
git log --all --grep="numpy\|pandas" -i

# Find by date range
git log --since="2024-09-01" --until="2024-09-30"

# Find file history
git log --follow -p -- requirements/base.txt

# Find by author and topic
git log --author="Thanh" --grep="compatibility"

# Find breaking changes
git log --grep="BREAKING CHANGE"

# Architecture evolution
git log --oneline --follow -- services/api-gateway/
```

### Creating Reports
```bash
# Dependency change history
git log --grep="build\|deps" --format="%ad %s" --date=short > deps-history.md

# List all hotfixes
git log --oneline --grep="^hotfix"
```

## Troubleshooting {#troubleshooting}

### Merge Conflicts in Requirements
```bash
# View conflict
cat requirements/base.txt

# Resolution strategy:
# 1. Keep both packages unless version conflict
# 2. Use newer version if compatible
# 3. Document choice in commit message

git add requirements/base.txt
git commit -m "fix(deps): Resolve requirements conflict"
```

### Wrong Branch Commits
```bash
# If committed to develop instead of feature
git branch feature/your-feature
git checkout develop
git reset --hard origin/develop
git checkout feature/your-feature
```

### Undo Pushed Commit
```bash
# On feature branch (can rewrite)
git revert HEAD
git push origin feature/branch

# On main/develop (never rewrite)
git revert <commit-hash>
git push origin main
```

### Large Files
```bash
# Remove from history before push
git reset --soft HEAD~1
git reset HEAD large-file
git commit -c ORIG_HEAD

# Add to gitignore
echo "large-file" >> .gitignore
git add .gitignore
git commit -m "chore: Update gitignore"
```

## Team Principles

1. **No direct commits to main/develop** - Always use PRs
2. **One PR, one purpose** - Keep changes focused
3. **Review within 24 hours** - Don't block teammates
4. **Document in commits** - Explain why, not just what
5. **Test before pushing** - Catch issues early
6. **Communicate blockers** - Ask for help promptly
7. **Keep branches short-lived** - Merge within days

## Microservices Considerations

### Service-Specific Branches
```bash
# Name includes service
git checkout -b feature/api-gateway-rate-limiting

# Commit scope includes service
git commit -m "feat(api-gateway): Add rate limiting"
```

### Cross-Service Changes
```bash
# Coordinate in single feature branch
git checkout -b feature/add-tracing

# Separate commits per service
git commit -m "feat(api-gateway): Add tracing"
git commit -m "feat(ml-service): Add tracing"
```

### Service Versioning
```
services/
  api-gateway/VERSION    # 1.2.3
  ml-service/VERSION      # 2.1.0
  data-service/VERSION    # 1.0.5
```

## Quick Reference

### Daily Commands
```bash
git status                     # Current state
git pull origin develop        # Get latest
git checkout -b feature/name   # New feature
git add -p                     # Stage interactively
git commit -m "message"        # Commit
git push origin feature/name   # Push branch
```

### Investigation Commands
```bash
git log -5                     # Recent commits
git log --grep="keyword"       # Search commits
git diff origin/develop        # Compare changes
git blame file.py              # Who changed what
```

### Emergency Commands
```bash
git stash                      # Save work temporarily
git reset --hard HEAD          # Discard all changes
git checkout -- file.py        # Discard file changes
git reflog                     # Recovery options
```

## Summary

This GitFlow workflow protects our production code while enabling rapid development. Each branch type serves a specific purpose, and our commit messages document technical decisions for future reference. Following these practices ensures code quality, facilitates collaboration, and maintains a valuable project history.

Remember: Good Git practices today save debugging hours tomorrow. When in doubt, ask for help before attempting fixes.

---
*Last updated: September 22, 2024*  
*Maintainer: AC215/E115 Team*  
*For questions about this guide, post in the team chat*