#!/bin/bash

# Script to run the enhanced Streamlit app with correct environment and region
echo "🚀 Starting Enhanced Kitchen Renovation Cost Estimator..."

# Activate the genai_bs conda environment (has all dependencies)
echo "📦 Activating genai_bs conda environment..."
source ~/miniconda3/etc/profile.d/conda.sh
conda activate genai_bs

# Set AWS region
echo "🌎 Setting AWS region to us-west-2..."
export AWS_DEFAULT_REGION=us-west-2

# Change to the correct directory
cd /home/ubuntu/workspace/TechSummit_2025/agentcore_deployment

# Run Streamlit
echo "🎯 Launching Streamlit Enhanced app..."
echo "📋 App features:"
echo "   ✅ Direct Bedrock Nova Premier LLM analysis"
echo "   ✅ Australian market pricing"
echo "   ✅ Clean, readable cost breakdowns"
echo "   ✅ No tokenization issues"
echo ""
echo "🌐 Access the app at: http://localhost:8501"
echo ""

streamlit run streamlit_enhanced.py --server.port 8501
