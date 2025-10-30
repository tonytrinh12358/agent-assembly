# Deployment Guide - Multi-Agent Kitchen Analysis

## Quick Start

### 1. Prerequisites
- Python 3.10+
- AWS Account with Bedrock access
- AWS CLI configured

### 2. Setup
```bash
cd working_solution
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. AWS Configuration
```bash
# Configure AWS credentials
aws configure

# Test Bedrock access
python test_bedrock_simple.py
```

### 4. Test Individual Components
```bash
# Test LangGraph Agent
cd langgraph_agent && python kitchen_analyzer_yolo.py

# Test CrewAI Agent  
cd ../crewai_agent && python cost_estimator.py

# Test Strands Orchestrator
cd ../strands_agent && python kitchen_strands_agent.py
```

### 5. Run Complete Solution
```bash
cd ..
python test_complete_solution.py
```

## Expected Output

### ✅ Success Indicators
- YOLO model loads successfully
- Bedrock connections established
- All agents execute without errors
- Cost estimates generated in AUD
- Comprehensive reports created

### ❌ Common Issues
- **Bedrock Access**: Ensure model access is enabled in AWS Console
- **Credentials**: Check AWS CLI configuration
- **Dependencies**: Install all requirements
- **Region**: Use us-west-2 (recommended)

## Production Deployment

### Docker Deployment
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "strands_agent/kitchen_strands_agent.py"]
```

### Environment Variables
```bash
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
export AWS_DEFAULT_REGION=us-west-2
```

## Architecture Overview

```
User Request → Strands Agent → LangGraph (YOLO + Bedrock) → CrewAI (Multi-Agent) → Final Report
```

This solution demonstrates real multi-agent collaboration with Bedrock LLM integration across three different agentic frameworks.
