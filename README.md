# Multi-Agent Kitchen Analysis Solution

## Overview

This is a complete multi-agent framework demonstration using **LangGraph**, **CrewAI**, and **Strands** agents with **Amazon Bedrock** integration for kitchen renovation analysis.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   LangGraph     │    │     CrewAI      │    │    Strands      │
│   Agent         │    │     Agent       │    │   Orchestrator  │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • YOLO Detection│    │ • Materials     │    │ • Coordinates   │
│ • Bedrock LLM   │    │   Expert        │    │   both agents   │
│ • Material ID   │    │ • Labor Analyst │    │ • Bedrock LLM   │
│ • Area Calc     │    │ • Cost Synth    │    │ • Final Report  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │ Amazon Bedrock  │
                    └─────────────────┘
```

## Components

### 1. LangGraph Agent (`langgraph_agent/`)
- **File**: `kitchen_analyzer_yolo.py`
- **Features**:
  - Real YOLO object detection
  - Tool-based architecture
  - Material identification
  - Area calculations

### 2. CrewAI Agent (`crewai_agent/`)
- **File**: `cost_estimator.py`
- **Features**:
  - Multi-agent workflow (3 agents)
  - Materials Cost Expert
  - Labor Cost Analyst
  - Cost Synthesizer
  - Australian pricing

### 3. Strands Orchestrator (`strands_agent/`)
- **File**: `kitchen_strands_agent.py`
- **Features**:
  - Orchestrates LangGraph + CrewAI
  - Comprehensive reporting
  - AI-powered recommendations
  - End-to-end workflow

## Setup

### 1. Install Dependencies
```bash
cd working_solution
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure AWS Bedrock
```bash
# Set AWS credentials
aws configure
# Or set environment variables
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
export AWS_DEFAULT_REGION=us-west-2
```

### 3. Enable Bedrock Models
- Go to AWS Console → Bedrock → Model Access

## Usage

### Test Individual Agents

#### LangGraph Agent
```bash
cd langgraph_agent
python kitchen_analyzer_yolo.py
```

#### CrewAI Agent
```bash
cd crewai_agent
python cost_estimator.py
```

#### Strands Orchestrator
```bash
cd strands_agent
python kitchen_strands_agent.py
```

### Test Complete Integration
```bash
python test_complete_solution.py
```

## Sample Results

### LangGraph Output
- **Objects Detected**: 2 kitchen items (refrigerator, oven)
- **Materials Found**: 5 materials (wood, granite, tile, stainless steel)
- **Kitchen Area**: 40.0 square metres
- **Bedrock Analysis**: Detailed renovation recommendations

### CrewAI Output
- **Total Project Cost**: $20,823.63 AUD
- **Materials Cost**: $12,262.50 AUD
- **Labor Cost**: $5,845.00 AUD
- **Multi-Agent Analysis**: 3 specialized agents with Bedrock reasoning

### Strands Output
- **Comprehensive Report**: Complete renovation analysis
- **Cost per Square Metre**: $520.59 AUD/sqm
- **AI Recommendations**: Layout optimization, material upgrades
- **Budget Range**: $17,700 - $23,947 AUD

## Key Features

✅ **Real YOLO Detection** - Actual computer vision object detection  
✅ **Bedrock Integration** - LLM calls  
✅ **Multi-Agent Workflows** - Specialized agents for different tasks  
✅ **Australian Pricing** - Real market pricing in AUD  
✅ **Tool Integration** - Proper @tool decorators and workflows  
✅ **End-to-End Pipeline** - Image → Analysis → Cost → Recommendations  

## File Structure

```
working_solution/
├── README.md                           # This file
├── requirements.txt                    # Dependencies
├── test_complete_solution.py          # Integration test
├── test_bedrock_simple.py            # Bedrock connectivity test
├── langgraph_agent/
│   ├── kitchen_analyzer_yolo.py       # LangGraph + YOLO + Bedrock
│   └── test_yolo_analyzer.py         # LangGraph tests
├── crewai_agent/
│   ├── cost_estimator.py             # CrewAI + Bedrock multi-agent
│   └── requirements.txt              # CrewAI dependencies
└── strands_agent/
    └── kitchen_strands_agent.py      # Strands orchestrator
```

## Technologies Used

- **LangGraph**: Workflow orchestration with tools
- **CrewAI**: Multi-agent collaboration
- **Strands**: Agent orchestration (simulated)
- **Amazon Bedrock**: Bedrock  LL
- **YOLO**: Object detection
- **PyTorch**: Deep learning framework
- **Pydantic**: Data validation
- **OpenCV**: Computer vision

## Cost Estimates

Based on real Australian market pricing:
- **Economy Grade**: $15,000 - $25,000 AUD
- **Standard Grade**: $20,000 - $35,000 AUD  
- **Premium Grade**: $35,000 - $50,000+ AUD

## Notes

- All pricing in Australian Dollars (AUD)
- Measurements in square metres
- Includes GST and labor costs
- Regional variations may apply
- Estimates valid as of 2023

## Support

For issues or questions about this multi-agent implementation, refer to the individual agent test files and ensure AWS Bedrock access is properly configured.
