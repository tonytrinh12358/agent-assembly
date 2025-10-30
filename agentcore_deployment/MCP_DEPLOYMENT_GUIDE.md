# 🔗 MCP Multi-Agent System Deployment Guide

## Overview

This guide walks you through deploying and testing the MCP (Model Context Protocol) enhanced multi-agent system for kitchen renovation analysis. The system provides standardized, secure agent-to-agent communication with enhanced reliability and observability.

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    MCP Multi-Agent System                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌──────────────┐ │
│  │   LangGraph     │    │     CrewAI      │    │ Orchestrator │ │
│  │   MCP Server    │◄──►│   MCP Server    │◄──►│  MCP Server  │ │
│  │                 │    │                 │    │              │ │
│  │ • Kitchen       │    │ • Cost          │    │ • Workflow   │ │
│  │   Analysis      │    │   Estimation    │    │   Coordination│ │
│  │ • YOLO Detection│    │ • Multi-agent   │    │ • MCP Client │ │
│  │ • Materials ID  │    │   Team          │    │ • Synthesis  │ │
│  └─────────────────┘    └─────────────────┘    └──────────────┘ │
│           ▲                       ▲                      ▲      │
│           │                       │                      │      │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │            Model Context Protocol (MCP)                     │ │
│  │  • Standardized Communication  • JWT Authentication        │ │
│  │  • Tool Discovery             • Enhanced Error Handling   │ │
│  └─────────────────────────────────────────────────────────────┘ │
│           │                       │                      │      │
│           ▼                       ▼                      ▼      │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │           Amazon Bedrock AgentCore Runtime                  │ │
│  │         • MCP Protocol Support  • Cognito Auth             │ │
│  │         • Auto-scaling         • Observability            │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start Deployment

### Prerequisites

1. **AWS Account** with appropriate permissions
2. **Python 3.10+** installed
3. **AWS CLI** configured
4. **Docker** running (for AgentCore deployment)

### Step 1: Deploy All MCP Agents

```bash
# Deploy all agents with Cognito authentication
python deploy_mcp_agents.py

# Deploy specific agent only
python deploy_mcp_agents.py --agent langgraph

# Deploy without authentication (development)
python deploy_mcp_agents.py --no-auth
```

### Step 2: Verify Deployment

```bash
# Run comprehensive test suite
python test_mcp_system.py

# Test specific components
python test_mcp_system.py --test discovery
python test_mcp_system.py --test auth
python test_mcp_system.py --test e2e
```

### Step 3: Run Streamlit UI

```bash
# Start MCP-enhanced Streamlit UI
streamlit run streamlit_mcp_enhanced.py
```

## 📋 Detailed Deployment Steps

### 1. Setup Base Infrastructure

```bash
# Create mcp_base directory (should already exist)
cd TechSummit_2025/agentcore_deployment

# Install MCP dependencies
pip install -r mcp_base/requirements.txt
```

### 2. Deploy Individual Agents

#### LangGraph Agent (Kitchen Analysis)

```bash
# Deploy LangGraph MCP agent
python deploy_mcp_agents.py --agent langgraph
```

**Features:**
- Kitchen object detection via YOLO
- Material identification and measurement
- Bedrock AI-powered analysis
- MCP tools: `analyze_kitchen`, `detect_kitchen_objects`, `estimate_kitchen_materials`

#### CrewAI Agent (Cost Estimation)

```bash
# Deploy CrewAI MCP agent
python deploy_mcp_agents.py --agent crewai
```

**Features:**
- Multi-agent cost estimation team
- Australian market pricing
- Grade-based pricing (economy, standard, premium)
- MCP tools: `estimate_renovation_costs`, `get_material_pricing`, `compare_cost_grades`

#### Orchestrator Agent (Coordination)

```bash
# Deploy Orchestrator MCP agent
python deploy_mcp_agents.py --agent orchestrator
```

**Features:**
- Multi-agent workflow coordination
- MCP-based agent communication
- Comprehensive result synthesis
- MCP tools: `orchestrate_full_workflow`, `analyze_kitchen_mcp`, `estimate_costs_mcp`, `discover_agent_ecosystem`

### 3. Authentication Setup

The system uses AWS Cognito for JWT token authentication:

```bash
# Setup system-wide Cognito
python deploy_mcp_agents.py --setup-cognito
```

**What this creates:**
- Cognito User Pool for each agent
- App Client for JWT tokens
- Test users for authentication
- Secrets Manager storage for credentials
- Parameter Store entries for agent ARNs

### 4. Verification and Testing

#### Local Testing (Before Deployment)

```bash
# Test MCP servers locally
# Terminal 1: Start LangGraph server
cd langgraph_agent
python langgraph_mcp_server.py

# Terminal 2: Start CrewAI server  
cd crewai_agent
python crewai_mcp_server.py

# Terminal 3: Start Orchestrator server
cd orchestrator_agent
python orchestrator_mcp_server.py

# Terminal 4: Run local tests
python test_mcp_local.py
```

#### Remote Testing (After Deployment)

```bash
# Comprehensive system test
python test_mcp_system.py --output test_results.json

# Individual agent tests
python test_mcp_system.py --agent langgraph_agent
python test_mcp_system.py --agent crewai_agent
python test_mcp_system.py --agent orchestrator_agent

# Specific test types
python test_mcp_system.py --test discovery
python test_mcp_system.py --test auth
python test_mcp_system.py --test e2e
```

## 🔧 Configuration and Customization

### Environment Variables

```bash
export AWS_REGION=us-west-2
export MCP_TIMEOUT=120
export DEBUG_MODE=false
```

### Agent Configuration

Each agent can be customized via its respective files:

- **LangGraph**: `langgraph_agent/langgraph_mcp_server.py`
- **CrewAI**: `crewai_agent/crewai_mcp_server.py`
- **Orchestrator**: `orchestrator_agent/orchestrator_mcp_server.py`

### MCP Client Configuration

Modify `mcp_base/mcp_client_utils.py` for:
- Timeout settings
- Retry logic
- Authentication parameters
- Error handling behavior

## 🧪 Testing Scenarios

### 1. Basic Functionality Test

```python
# Test kitchen analysis
python test_mcp_system.py --agent langgraph_agent

# Expected: Kitchen objects detected, materials identified
```

### 2. Cost Estimation Test

```python
# Test cost estimation
python test_mcp_system.py --agent crewai_agent

# Expected: Australian dollar costs for materials and labor
```

### 3. End-to-End Workflow Test

```python
# Test complete workflow
python test_mcp_system.py --test e2e

# Expected: Kitchen analysis → Cost estimation → Recommendations
```

### 4. Authentication Test

```python
# Test Cognito authentication
python test_mcp_system.py --test auth

# Expected: JWT tokens available for all agents
```

### 5. Agent Discovery Test

```python
# Test MCP ecosystem discovery
python test_mcp_system.py --test discovery

# Expected: All agents discovered with their tools
```

## 🔍 Debugging and Troubleshooting

### Common Issues

#### 1. Agent Not Found
```
Error: Failed to get credentials for agent langgraph_agent
```
**Solution:**
- Check Parameter Store for agent ARN: `/agents/langgraph_agent_arn`
- Verify agent is deployed: `python deploy_mcp_agents.py --agent langgraph`

#### 2. Authentication Failure
```
Error: Bearer token not found
```
**Solution:**
- Check Secrets Manager: `agents/langgraph_agent/cognito_credentials`
- Refresh token: `python -c "from auth_utils import *; refresh_bearer_token('langgraph_agent')"`

#### 3. MCP Connection Timeout
```
Error: MCP connection timeout
```
**Solution:**
- Check agent status in AgentCore Console
- Increase timeout in `mcp_client_utils.py`
- Verify network connectivity

#### 4. Tool Discovery Failed
```
Error: No tools found for agent
```
**Solution:**
- Check agent logs in CloudWatch
- Verify MCP server is running correctly
- Test locally first with `test_mcp_local.py`

### Debug Mode

Enable debug mode in Streamlit UI or tests:

```python
# In Streamlit
debug_mode = st.sidebar.checkbox("🔧 Debug Mode", value=True)

# In tests
python test_mcp_system.py --output debug_results.json
```

### Log Analysis

Check CloudWatch logs for each agent:
- `/aws/bedrock-agentcore/langgraph_agent`
- `/aws/bedrock-agentcore/crewai_agent`
- `/aws/bedrock-agentcore/orchestrator_agent`

## 📊 Performance Monitoring

### Metrics to Monitor

1. **Response Times**
   - Kitchen analysis: ~15-30 seconds
   - Cost estimation: ~8-15 seconds
   - Full workflow: ~45-60 seconds

2. **Success Rates**
   - Individual agents: >95%
   - End-to-end workflow: >90%
   - Authentication: >99%

3. **Error Rates**
   - Connection timeouts: <5%
   - Authentication failures: <1%
   - Tool execution failures: <3%

### Performance Tuning

1. **Timeout Configuration**
```python
# In mcp_client_utils.py
AgentCoreMCPClient(region="us-west-2", timeout=180)  # 3 minutes
```

2. **Retry Logic**
```python
# Configure retries for failed requests
retries={'max_attempts': 5, 'mode': 'adaptive'}
```

3. **Caching**
```python
# Cache agent credentials
@st.cache_data(ttl=300)  # 5 minutes
```

## 🚀 Deployment to Production

### Production Checklist

- [ ] All agents deployed successfully
- [ ] Cognito authentication configured
- [ ] Test suite passes (>90% success rate)
- [ ] CloudWatch monitoring enabled
- [ ] Error alerts configured
- [ ] Documentation updated
- [ ] Performance benchmarks established

### Security Considerations

1. **JWT Token Security**
   - Tokens stored in AWS Secrets Manager
   - Regular token rotation
   - Minimal token permissions

2. **Network Security**
   - VPC configuration for AgentCore
   - Security groups properly configured
   - HTTPS/TLS for all communications

3. **Access Control**
   - IAM roles with least privilege
   - Cognito user pool restrictions
   - Resource-based permissions

### Scaling Considerations

1. **Auto-scaling Configuration**
   - AgentCore runtime auto-scaling
   - Load balancing for high traffic
   - Resource monitoring and alerts

2. **Cost Optimization**
   - Right-sizing agent resources
   - Monitoring usage patterns
   - Scheduled scaling policies

## 📈 Success Metrics

After deployment, you should see:

- ✅ **Agent Discovery**: All 3 agents discoverable via MCP
- ✅ **Authentication**: JWT tokens available for all agents
- ✅ **Kitchen Analysis**: YOLO detection working, materials identified
- ✅ **Cost Estimation**: Australian pricing, multiple grades supported
- ✅ **Workflow Orchestration**: End-to-end analysis completing
- ✅ **Streamlit UI**: MCP-enhanced interface functional
- ✅ **Performance**: Analysis completing within expected timeframes
- ✅ **Reliability**: >90% success rate on test suite

## 🎯 Next Steps

1. **Monitor Performance**: Use test suite regularly
2. **Expand Capabilities**: Add more MCP tools as needed  
3. **Optimize Costs**: Monitor usage and adjust resources
4. **Enhance Security**: Implement additional security measures
5. **Scale System**: Add more agents or capabilities via MCP

---

**🔗 MCP Multi-Agent System**: Experience the future of standardized, secure agent communication!

For support or questions, check the test results and CloudWatch logs for detailed debugging information.
