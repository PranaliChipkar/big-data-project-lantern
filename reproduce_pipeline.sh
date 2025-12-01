#!/bin/bash
# Project LANTERN - Reproducibility Script
# This script reproduces the entire pipeline from scratch

echo "🚀 Project LANTERN Pipeline Reproduction"
echo "========================================"

# Step 1: Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Step 2: Initialize DVC
echo "📊 Setting up DVC..."
dvc init -f

# Step 3: Run the complete pipeline
echo "⚙️ Running pipeline..."
dvc repro

# Step 4: Show results
echo "📈 Pipeline Results:"
dvc metrics show

echo "✅ Pipeline reproduction complete!"
echo "Check data/parsed/ for all outputs"
