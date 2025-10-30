# 🔗 MCP System Quick Command Reference

## 🚀 Quick Deployment

```bash
# Deploy all MCP agents
python deploy_mcp_agents.py

# Deploy specific agent
python deploy_mcp_agents.py --agent langgraph
python deploy_mcp_agents.py --agent crewai  
python deploy_mcp_agents.py --agent orchestrator

# Setup authentication only
python deploy_mcp_agents.py --setup-cognito

# Deploy without authentication (dev mode)
python deploy_mcp_agents.py --no-auth
```

## 🧪 Testing Commands

```bash
# Full test suite
python test_mcp_system.py

# Individual agent tests
python test_mcp_system.py --agent langgraph_agent
python test_mcp_system.py --agent crewai_agent
python test_mcp_system.py --agent orchestrator_agent

# Specific test types
python test_mcp_system.py --test discovery    # Test agent discovery
python test_mcp_system.py --test auth         # Test authentication
python test_mcp_system.py --test e2e          # Test end-to-end workflow

# Save test results
python test_mcp_system.py --output results.json

# Local testing (servers running locally)
python test_mcp_local.py
```

## 🖥️ Local Development

```bash
# Run MCP servers locally for testing
cd langgraph_agent && python langgraph_mcp_server.py     # Port 8000
cd crewai_agent && python crewai_mcp_server.py          # Port 8001  
cd orchestrator_agent && python orchestrator_mcp_server.py # Port 8002

# Test local servers
python test_mcp_local.py
```

## 🌐 Streamlit UI

```bash
# Original Streamlit (non-MCP)
streamlit run streamlit_orchestrator.py

# MCP-enhanced Streamlit
streamlit run streamlit_mcp_enhanced.py

# With specific port
streamlit run streamlit_mcp_enhanced.py --server.port 8501
```

## 🔧 Debugging Commands

```bash
# Check AWS resources
aws ssm get-parameter --name "/agents/langgraph_agent_arn"
aws secretsmanager get-secret-value --secret-id "agents/langgraph_agent/cognito_credentials"

# Check agent status via AWS CLI
aws bedrock-agentcore describe-runtime --agent-runtime-arn "arn:aws:bedrock-agentcore:..."

# Refresh authentication tokens
python -c "from mcp_base.auth_utils import CognitoAuthManager; auth = CognitoAuthManager(); auth.refresh_bearer_token('langgraph_agent')"
```

## 📊 Monitoring Commands

```bash
# View CloudWatch logs
aws logs describe-log-groups --log-group-name-prefix "/aws/bedrock-agentcore"
aws logs get-log-events --log-group-name "/aws/bedrock-agentcore/langgraph_agent" --log-stream-name "latest"

# Check agent health
python -c "
import asyncio
from mcp_base.mcp_client_utils import AgentCoreMCPClient
client = AgentCoreMCPClient()
print(asyncio.run(client.health_check_agent('langgraph_agent')))
"
```

## 🔄 Common Workflows

### Full Deployment + Test
```bash
python deploy_mcp_agents.py && python test_mcp_system.py --output results.json
```

### Redeploy Specific Agent
```bash
# Redeploy LangGraph agent
python deploy_mcp_agents.py --agent langgraph
python test_mcp_system.py --agent langgraph_agent
```

### Quick Health Check
```bash
python test_mcp_system.py --test discovery
```

### Debug Authentication Issues
```bash
python test_mcp_system.py --test auth
python deploy_mcp_agents.py --setup-cognito  # If needed
```

## 📁 File Structure

```
TechSummit_2025/agentcore_deployment/
├── mcp_base/                          # Base MCP infrastructure
│   ├── mcp_server_base.py            # Base MCP server class
│   ├── mcp_client_utils.py           # MCP client utilities  
│   ├── auth_utils.py                 # Cognito authentication
│   └── requirements.txt              # MCP dependencies
├── langgraph_agent/
│   ├── langgraph_mcp_server.py       # MCP version
│   ├── langgraph_agent.py            # Original version
│   └── requirements.txt              # Updated with MCP
├── crewai_agent/
│   ├── crewai_mcp_server.py          # MCP version
│   ├── crewai_agent.py               # Original version  
│   └── requirements.txt              # Updated with MCP
├── orchestrator_agent/
│   ├── orchestrator_mcp_server.py    # MCP version
│   ├── orchestrator_agent.py         # Original version
│   └── requirements.txt              # Updated with MCP
├── deploy_mcp_agents.py              # MCP deployment script
├── test_mcp_system.py                # Comprehensive test suite
├── test_mcp_local.py                 # Local testing script
├── streamlit_mcp_enhanced.py         # MCP-enabled UI
├── streamlit_orchestrator.py         # Original UI
├── MCP_DEPLOYMENT_GUIDE.md           # Full deployment guide
└── MCP_COMMANDS.md                   # This file
```

## 🎯 Success Indicators

After running commands, look for:
- ✅ `Agent deployed successfully` (deployment)
- ✅ `MCP session initialized` (testing)  
- ✅ `Test passed` (testing)
- ✅ `Workflow completed` (end-to-end)
- ✅ `Bearer token available` (authentication)

## ❌ Common Error Solutions

| Error | Solution |
|-------|----------|
| `Agent ARN not found` | Run `python deploy_mcp_agents.py --agent <name>` |
| `Bearer token not found` | Run `python deploy_mcp_agents.py --setup-cognito` |
| `MCP connection timeout` | Check agent status in AWS Console |
| `Tool not found` | Verify agent deployed with MCP protocol |
| `Permission denied` | Check IAM roles and policies |

## 📞 Quick Help

```bash
# Get help for any command
python deploy_mcp_agents.py --help
python test_mcp_system.py --help

# Check Python packages
pip list | grep mcp
pip list | grep bedrock-agentcore

# Verify AWS credentials
aws sts get-caller-identity
```
