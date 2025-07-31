#!/bin/bash

# Backend Deployment Script
echo "🚀 Deploying Backend Changes from Debug to Dev Branch..."

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Error: Not in a git repository"
    exit 1
fi

# Get current branch
CURRENT_BRANCH=$(git branch --show-current)

if [ "$CURRENT_BRANCH" != "debug" ]; then
    echo "⚠️  Warning: You're not on the debug branch. Current branch: $CURRENT_BRANCH"
    read -p "Do you want to continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Deployment cancelled"
        exit 1
    fi
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo "📝 You have uncommitted changes. Please commit them first:"
    git status --porcelain
    read -p "Do you want to commit them now? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "💬 Enter commit message:"
        read -r COMMIT_MSG
        git add .
        git commit -m "$COMMIT_MSG"
    else
        echo "❌ Please commit your changes before deploying"
        exit 1
    fi
fi

# Switch to dev branch
echo "🔄 Switching to dev branch..."
git checkout dev

if [ $? -ne 0 ]; then
    echo "❌ Failed to switch to dev branch"
    exit 1
fi

# Pull latest changes from remote dev
echo "📥 Pulling latest changes from remote dev..."
git pull origin dev

# Merge debug branch into dev
echo "🔀 Merging debug branch into dev..."
git merge debug

if [ $? -ne 0 ]; then
    echo "❌ Merge conflict detected. Please resolve conflicts and run:"
    echo "   git add ."
    echo "   git commit"
    echo "   git push origin dev"
    exit 1
fi

# Push to remote dev branch
echo "📤 Pushing changes to remote dev branch..."
git push origin dev

if [ $? -ne 0 ]; then
    echo "❌ Failed to push to remote dev branch"
    exit 1
fi

echo "✅ Backend deployment successful!"
echo "🔙 Switching back to debug branch..."
git checkout debug

echo "🎉 Deployment complete! Your changes are now live on the dev branch."
