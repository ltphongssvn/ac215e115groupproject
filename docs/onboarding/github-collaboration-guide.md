# /home/lenovo/code/ltphongssvn/ac215e115groupproject/docs/onboarding/github-collaboration-guide.md
# GitHub Collaboration Guide for AC215/E115 Team
# Complete guide for team members at all technical levels to effectively use GitHub

## Purpose of This Guide

This guide teaches you how to use GitHub effectively for our microservices project, regardless of your prior Git experience. You'll learn how to find important technical decisions in our commit history, understand why specific packages and versions were chosen, and contribute to the project without getting lost in Git complexities.

## Table of Contents
1. [Essential Concepts You Need to Know](#essential-concepts)
2. [Setting Up Your Environment](#setting-up)
3. [Daily Workflow Commands](#daily-workflow)
4. [Finding Technical Decisions in History](#finding-decisions)
5. [Understanding Our Commit Messages](#understanding-commits)
6. [Common Problems and Solutions](#troubleshooting)

## Essential Concepts You Need to Know {#essential-concepts}

Before diving into commands, let's understand what GitHub does for our team:

**Repository (Repo)**: Think of this as our project's shared folder that keeps track of every change ever made. Everyone has their own copy to work on, and GitHub stores the master copy that we all sync with.

**Commit**: A snapshot of changes with a description. Like saving a document with a note about what you changed. Each commit has a unique ID (called a hash) that looks like `343e189`.

**Branch**: A parallel version of the project. We work on the `main` branch, but you might create feature branches for big changes.

**Push/Pull**: Push sends your commits to GitHub, Pull gets other people's commits from GitHub to your computer.

## Setting Up Your Environment {#setting-up}

### First-Time Setup (Do This Once)

Configure Git with your identity so your commits are properly attributed:

```bash
# Tell Git who you are (use your actual name and email)
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Set up helpful aliases to make Git easier to use
git config --global alias.lg "log --oneline --graph --all --decorate"
git config --global alias.st "status"
```

### Cloning the Project (First Time Only)

```bash
# Navigate to where you want the project folder
cd ~/code

# Clone our repository
git clone https://github.com/ltphongssvn/ac215e115groupproject.git

# Enter the project directory
cd ac215e115groupproject
```

## Daily Workflow Commands {#daily-workflow}

These are the commands you'll use every day. Follow this sequence to stay synchronized with the team:

### Start of Each Work Session

```bash
# 1. Check what branch you're on and if you have any uncommitted changes
git status

# 2. Get the latest changes from GitHub
git pull origin main

# 3. Check if requirements have changed (important!)
# If you see changes to any requirements/*.txt files, reinstall:
conda activate test_ac215
pip install -r requirements/base.txt
pip install -r requirements/api-gateway.txt  # if working on API gateway
```

### After Making Changes

```bash
# 1. See what files you've changed
git status

# 2. Review your actual changes (press 'q' to exit the view)
git diff

# 3. Add your changes to staging
git add .  # adds everything, OR
git add specific_file.py  # add specific files only

# 4. Commit with a descriptive message
git commit -m "Clear description of what you changed and why"

# 5. Push to GitHub
git push origin main
```

## Finding Technical Decisions in History {#finding-decisions}

Our commit messages contain important technical decisions. Here's how to find them:

### View Recent Commits with Full Messages

```bash
# See the last 5 commits with full messages
git log -5

# Example output shows WHO made changes, WHEN, and WHY:
# commit 343e189... (you'll see a long hash)
# Author: Team Member <email@example.com>
# Date:   Mon Sep 16 2024
#
#     Add API gateway security requirements
#     
#     - Added dedicated requirements file for API gateway security packages
#     - Includes Redis (5.0.1) for caching and session management
#     - Includes PyJWT (2.8.0) and passlib (1.7.4) for authentication
#     ...
```

### Search for Specific Decisions

```bash
# Find all commits about numpy (to understand version choice)
git log --grep="numpy" --all

# Find all commits about requirements changes
git log --grep="requirements" --all

# Find commits that changed a specific file
git log -- requirements/base.txt

# See what changed in a specific commit (use the hash from git log)
git show 343e189
```

### Understanding Why We Use Specific Package Versions

To understand why we use specific versions (like numpy 1.26.4 instead of 2.0):

```bash
# Find the commit that set the numpy version
git log -p -- requirements/base.txt | grep -B5 -A5 "numpy"

# Read the commit message for that change
git log --grep="numpy" --grep="compatibility" --all
```

You'll find detailed explanations like:
- "Downgraded numpy from 2.0.2 to 1.26.4 to resolve LangChain incompatibility"
- This tells you there's a technical constraint, not an arbitrary choice

## Understanding Our Commit Messages {#understanding-commits}

Our team uses structured commit messages. Here's how to read them:

### Structure of Our Commit Messages

```
Short summary line (what was done)

- Bullet point with specific change
- Another specific change
- Version numbers and packages included

Paragraph explaining WHY these changes matter and 
what problem they solve for the team.
```

### Real Example from Our Project

```
Fix critical dependency conflicts: numpy 1.26.4 for LangChain compatibility

- Downgraded numpy from 2.0.2 to 1.26.4 to resolve LangChain incompatibility
- Fixed incorrect package name from scikit-learn-onnx to skl2onnx
- Updated documentation with troubleshooting notes

These changes resolve installation failures that would block team members 
from setting up the development environment.
```

### How to Write Good Commit Messages

When you make changes, write messages that help future teammates:

```bash
# Good commit message
git commit -m "Add Redis connection pooling to API gateway

- Configured connection pool with max_connections=50
- Added retry logic with exponential backoff
- Set timeout to 5 seconds as per performance requirements

This improves API gateway resilience under high load and prevents
connection exhaustion issues we discussed in meeting on Sept 15."

# Bad commit message (don't do this)
git commit -m "fixed stuff"  # No one knows what was fixed or why
```

## Common Problems and Solutions {#troubleshooting}

### Problem: "Your branch is behind origin/main"

This means others have pushed changes you don't have yet.

```bash
# Solution: Pull the latest changes
git pull origin main
```

### Problem: "Merge conflict" when pulling

This happens when you and someone else changed the same file.

```bash
# See which files have conflicts
git status

# Open the conflicted file in your editor
# Look for sections like this:
<<<<<<< HEAD
your changes
=======
their changes
>>>>>>> origin/main

# Edit the file to keep the right changes, remove the markers
# Then:
git add the_fixed_file.py
git commit -m "Resolved merge conflict in filename"
git push origin main
```

### Problem: "I committed the wrong thing"

If you haven't pushed yet:

```bash
# Undo the last commit but keep your changes
git reset --soft HEAD~1

# Now you can fix and recommit
```

If you already pushed:

```bash
# Create a new commit that undoes the problematic one
git revert HEAD
git push origin main
```

### Problem: "I don't know what changed in requirements"

When you pull and see requirements files changed:

```bash
# See what packages changed
git diff HEAD~1 requirements/base.txt

# Read why they changed
git log -1 -- requirements/base.txt
```

## Quick Reference Card

Print this section and keep it handy:

### Every Day Commands
- `git status` - What's my current situation?
- `git pull origin main` - Get latest from team
- `git add .` - Stage all my changes
- `git commit -m "message"` - Save changes with description
- `git push origin main` - Share with team

### Investigation Commands
- `git log -5` - See recent commits
- `git log --grep="keyword"` - Search commit messages
- `git show <hash>` - See specific commit details
- `git diff` - What did I change?

### Getting Help
- `git status` - Always start here when confused
- `git log --oneline -10` - Quick view of recent history
- `git help <command>` - Detailed help for any command

## Team Collaboration Rules

1. **Always pull before starting work** - Get the latest changes first
2. **Commit frequently with clear messages** - Small, focused commits are better
3. **Push at least once per day** - Don't let changes accumulate locally
4. **Read commit messages** - They contain important technical context
5. **Update documentation** - If you discover something important, document it

## Getting Additional Help

If you're stuck:

1. Run `git status` and copy the output
2. Post in our team chat with:
   - The command you tried
   - The error message
   - Output of `git status`
3. Don't worry about "messing up" - Git keeps history of everything

## Advanced: Reviewing Package Decision History

For understanding architectural decisions about packages:

```bash
# See all commits that changed requirements files
git log --oneline -- requirements/

# Find when a specific package was added
git log -p -- requirements/ | grep -B5 "package_name"

# See who added a package and why
git blame requirements/base.txt | grep "redis"
# Then look up the commit hash shown to read the full message
```

## Summary

GitHub is our team's shared memory for the project. Every technical decision, every package choice, and every bug fix is documented in our commit history. By following this guide, you can:

- Stay synchronized with the team's work
- Understand why specific technical choices were made
- Contribute your changes effectively
- Find answers to technical questions in our project's history

Remember: Good commit messages today save hours of confusion tomorrow. When in doubt, over-communicate in your commit messages - future teammates (including future you) will thank you.

---
*Last updated: September 2024*  
*Maintainer: AC215/E115 Team*  
*For questions about this guide, post in the team chat*