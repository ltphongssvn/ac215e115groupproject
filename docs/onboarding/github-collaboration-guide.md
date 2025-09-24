
# GitHub Collaboration Guide for AC215/E115 Team
<!-- Path: /docs/onboarding/github-collaboration-guide.md -->
<!-- Professional GitFlow-based workflow for Rice Market AI System microservices development -->

## Purpose of This Guide

This guide establishes our team's Git workflow based on industry-standard GitFlow practices, adapted for our microservices architecture. You'll learn how to contribute safely, review code effectively, and maintain a clean project history that documents our technical decisions.

## Table of Contents
1. [Understanding Our Branching Strategy](#understanding-our-branching-strategy)
2. [Branch Protection Rules](#branch-protection-rules)
3. [Environment Setup](#environment-setup)
4. [Daily Development Workflow](#daily-development-workflow)
5. [Feature Branch Management](#feature-branch-management)
6. [Pull Request Process](#pull-request-process)
7. [Code Review Guidelines](#code-review-guidelines)
8. [Commit Message Standards](#commit-message-standards)
9. [Release Management](#release-management)
10. [Finding Technical Decisions](#finding-technical-decisions)
11. [Troubleshooting](#troubleshooting)

## Understanding Our Branching Strategy

### Branch Types
- **main**: Production-ready code. Protected branch - no direct commits allowed, even for administrators
- **develop**: Integration branch for features. Protected branch - requires pull requests, allows admin override with warning
- **feature/**: Individual development branches (e.g., `feature/add-redis-cache`)
- **release/**: Preparation for production release (e.g., `release/1.2.0`)
- **hotfix/**: Emergency production fixes (e.g., `hotfix/auth-bypass`)

### Branch Flow Rules
```
feature/* → develop → release/* → main
hotfix/* → main + develop
```

### Protection Philosophy

Our repository implements a two-tier protection system that reflects the different purposes and stability requirements of each branch type. Think of this as creating security zones within your repository - some areas allow controlled flexibility for active development, while others maintain strict controls for production stability.

## Branch Protection Rules

### Main Branch (Production) - Maximum Protection

The main branch represents production-ready code and receives the highest level of protection. This branch only accepts changes through pull requests from the develop branch during planned releases or through hotfix branches for critical production fixes.

**Active Protection Settings:**
- Require a pull request before merging: **Enabled**
- Required number of approvals: **2**
- Dismiss stale pull request approvals when new commits are pushed: **Enabled**
- Require review from CODEOWNERS: **Enabled**
- Require status checks to pass before merging: **Enabled**
- Require conversation resolution before merging: **Enabled**
- Require linear history: **Enabled**
- Do not allow bypassing the above settings: **Enabled** (administrators cannot override)

**What This Means for You:**
When you attempt to push directly to main, you'll receive an error:
```bash
remote: error: GH006: Protected branch update failed for refs/heads/main.
remote: - Changes must be made through a pull request.
```

This protection ensures that production deployments always go through proper review channels. Even in emergencies, you must create a pull request - there are no shortcuts to production. This absolute protection prevents the common scenario where urgent "fixes" introduce new problems because they bypassed review.

### Develop Branch (Integration) - Balanced Protection

The develop branch serves as the integration point for all feature development. It maintains quality standards while allowing more flexibility than main, recognizing that this is where active development convergence happens.

**Active Protection Settings:**
- Require a pull request before merging: **Enabled**
- Required number of approvals: **1**
- Dismiss stale pull request approvals when new commits are pushed: **Enabled**
- Require review from CODEOWNERS: **Disabled**
- Require status checks to pass before merging: **Enabled**
- Require conversation resolution before merging: **Enabled**
- Require linear history: **Disabled** (allows merge commits)
- Do not allow bypassing the above settings: **Disabled** (administrators can override with warning)

**What This Means for You:**
Non-administrators must always use pull requests. Administrators can push directly in emergencies but will receive a warning:
```bash
remote: Bypassed rule violations for refs/heads/develop:
remote: - Changes must be made through a pull request.
```

This flexibility serves as an emergency valve for situations like CI/CD failures or urgent integration fixes. The warning reminds administrators that they're circumventing normal processes, encouraging them to use this power sparingly.

### Feature Branches - No Protection

Feature branches remain completely unprotected to give developers maximum flexibility during implementation. You can freely experiment, refactor, force-push, and rewrite history as needed while working on features. Protection only applies when attempting to merge these changes into develop.

## Environment Setup

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

# Verify branch protection (will fail as expected)
git checkout main
echo "test" > test.txt
git add test.txt
git commit -m "test"
git push origin main  # Should fail with GH006 error
git reset --hard origin/main  # Clean up
```

## Daily Development Workflow

### Start Your Day
```bash
# 1. Sync with team's work
git checkout develop
git pull origin develop

# 2. Check for dependency changes
git diff HEAD@{1} HEAD --name-only | grep requirements
# If changes found, update environment:
pip install -r requirements/base.txt

# 3. Create feature branch (unprotected for flexibility)
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

# Push regularly for backup (no restrictions on feature branches)
git push -u origin feature/your-branch
```

### End of Day
```bash
# Ensure all changes committed
git status

# Push to remote
git push origin feature/your-branch

# Create draft PR if not ready for review
# The PR will show required checks based on target branch
```

## Feature Branch Management

### Naming Conventions
```
feature/service-description
bugfix/issue-number-description
hotfix/critical-issue
```

Examples:
- `feature/nl-sql-query-optimization`
- `feature/rag-vector-search`
- `feature/ts-lstm-model`
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

# Force push to feature branch only (safe since unprotected)
git push --force-with-lease origin feature/your-branch
```

## Pull Request Process

### Understanding PR Requirements

When you create a pull request, GitHub automatically applies the protection rules of the target branch. The merge button will be disabled until all requirements are met:

**For PRs to develop:**
- 1 approval required
- All conversations must be resolved
- Status checks must pass (when configured)
- Can be merged with merge commit or squash

**For PRs to main:**
- 2 approvals required
- All conversations must be resolved
- Status checks must pass
- Must be merged with linear history (squash or rebase)
- CODEOWNERS review required (if configured)

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
- [ ] PR targets correct branch (develop for features, main for releases)
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

### PR Merge Requirements Dashboard

GitHub will show a status check at the bottom of your PR:
```
✓ 1 approval (or 2 for main)
✓ All conversations resolved
✓ Continuous integration checks passed
✓ No merge conflicts
```

## Code Review Guidelines

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
- Remember: Your approval is required for merging (1 for develop, 2 for main)

## Commit Message Standards

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
git commit -m "feat(nl-sql-agent): Add JWT refresh token rotation

- Implement 7-day refresh token expiry
- Add token rotation on each refresh
- Store tokens in Redis

Improves security by preventing token replay attacks
Resolves #45"

# Bug fix commit
git commit -m "fix(rag-orchestrator): Handle edge cases in confidence scoring

- Fix division by zero error
- Clamp scores to [0,1] range
- Validate NaN values

Fixes #89"
```

## Release Management

### Creating Release (Protected Workflow)
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

# Create PR to main (requires 2 approvals)
# After approval and merge:
git checkout main
git pull origin main
git tag -a v1.2.0 -m "Version 1.2.0"
git push origin v1.2.0

# Create PR from release back to develop (requires 1 approval)
# Clean up after merge
git push origin --delete release/1.2.0
```

### Hotfix Process (Emergency Production Fix)
```bash
# Start from main
git checkout main
git pull origin main
git checkout -b hotfix/critical-fix

# Make minimal fixes
# Test thoroughly
git commit -m "hotfix: Fix critical issue"

# Create PR to main (still requires 2 approvals - no exceptions)
# After merge, tag the hotfix
git checkout main
git pull origin main
git tag -a v1.2.1 -m "Hotfix 1.2.1"
git push origin v1.2.1

# Create PR to develop (requires 1 approval)
```

### Emergency Procedures

**For Develop Branch (Admin Only):**
In genuine emergencies affecting the develop branch, administrators can push directly, but will receive a warning:
```bash
# Not recommended but possible for administrators
git push origin develop
# Output: "Bypassed rule violations for refs/heads/develop"
# Warning serves as reminder that normal procedures are being bypassed
```

**For Main Branch:**
The main branch offers no emergency bypass option, even for administrators:
```bash
# This will always fail, even for administrators
git push origin main
# Output: "error: GH006: Protected branch update failed"
# Production changes must always go through proper review process
```

## Finding Technical Decisions

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
git log --oneline --follow -- services/nl-sql-agent/
```

### Creating Reports
```bash
# Dependency change history
git log --grep="build\|deps" --format="%ad %s" --date=short > deps-history.md

# List all hotfixes
git log --oneline --grep="^hotfix"
```

## Troubleshooting

### Common Protection-Related Issues

**"Protected branch update failed" when pushing to main**
This is expected behavior. The main branch requires all changes to go through pull requests with 2 approvals. Create a pull request from develop or a hotfix branch instead.

**"Changes must be made through a pull request" warning on develop**
For administrators, this is a warning that you're bypassing normal procedures. Consider whether this emergency override is truly necessary. For non-administrators, this will be an error - create a pull request from your feature branch.

**Pull request can't be merged despite approval**
Check that all requirements are met:
- Required number of approvals (1 for develop, 2 for main)
- All conversations resolved
- Status checks passing
- No merge conflicts

The merge button tooltip will show which requirements are still pending.

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

1. **No direct commits to main/develop** - Always use PRs (enforced by protection)
2. **One PR, one purpose** - Keep changes focused
3. **Review within 24 hours** - Don't block teammates
4. **Document in commits** - Explain why, not just what
5. **Test before pushing** - Catch issues early
6. **Communicate blockers** - Ask for help promptly
7. **Keep branches short-lived** - Merge within days
8. **Respect the protection** - Rules exist to protect production stability

## Rice Market AI System Specific Guidelines

### Service-Specific Branches
```bash
# Name includes service
git checkout -b feature/nl-sql-query-optimization
git checkout -b feature/rag-vector-indexing
git checkout -b feature/ts-prophet-integration

# Commit scope includes service
git commit -m "feat(nl-sql-agent): Add query caching"
git commit -m "feat(rag-orchestrator): Improve ranking"
git commit -m "feat(ts-forecasting): Add SHAP values"
```

### Cross-Service Changes
```bash
# Coordinate in single feature branch
git checkout -b feature/add-distributed-tracing

# Separate commits per service
git commit -m "feat(api-gateway): Add tracing headers"
git commit -m "feat(nl-sql-agent): Propagate trace context"
git commit -m "feat(rag-orchestrator): Add trace spans"
```

### Service Versioning
```
services/
  nl-sql-agent/VERSION         # 1.2.3
  rag-orchestrator/VERSION      # 2.1.0
  ts-forecasting/VERSION        # 1.0.5
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

### Protection Verification Commands
```bash
# Test develop protection (will warn for admins)
git checkout develop
echo "test" > test.txt && git add test.txt && git commit -m "test"
git push origin develop

# Test main protection (will fail for everyone)
git checkout main
echo "test" > test.txt && git add test.txt && git commit -m "test"
git push origin main  # Will fail with GH006
```

## Summary

This GitFlow workflow with branch protection creates a robust development environment that balances flexibility with safety. The two-tier protection system ensures that:

- **Feature branches** remain unprotected for maximum development flexibility
- **Develop branch** requires reviews but allows administrative override for emergencies
- **Main branch** is absolutely protected, ensuring production stability through mandatory review processes

Each protection level serves a specific purpose in maintaining code quality while enabling efficient development. The branch protection rules actively guide the team toward best practices by making the correct workflow the path of least resistance.

Remember: Good Git practices today save debugging hours tomorrow. The protection rules aren't obstacles - they're guardrails that help us deliver reliable software. When in doubt, ask for help before attempting fixes.

---
*Last updated: September 23, 2024*
*Branch Protection Configured: Main (strict), Develop (balanced)*
*Default Branch: develop*
*Maintainer: AC215/E115 Rice Market AI System Team*
*For questions about this guide or branch protection, post in the team chat*
```