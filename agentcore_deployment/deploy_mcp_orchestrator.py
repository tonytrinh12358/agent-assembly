#!/usr/bin/env python3
"""
Deploy MCP-Based Orchestrator Agent to Bedrock AgentCore
"""

import os
import sys
import boto3
import json
from bedrock_agentcore_starter_toolkit import Runtime
from boto3.session import Session
from utils import create_agentcore_role, save_agent_arn_to_parameter_store, get_agent_arn_from_parameter_store


def update_mcp_orchestrator_permissions(sub_agent_arns: list, sub_agent_parameter_arns: list, orchestrator_role_name: str):
    """Update orchestrator IAM role to allow MCP calls to sub-agents"""
    iam_client = boto3.client('iam')
    
    # Enhanced permissions for MCP protocol
    orchestrator_permissions = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "bedrock-agentcore:InvokeAgentRuntime",
                    "bedrock-agentcore:InvokeAgentRuntimeWithMCP"  # MCP-specific permission
                ],
                "Resource": [sub_agent_arn + "/runtime-endpoint/DEFAULT" for sub_agent_arn in sub_agent_arns] + [sub_agent_arn for sub_agent_arn in sub_agent_arns]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "ssm:GetParameter"
                ],
                "Resource": [sub_agent_parameter_arn for sub_agent_parameter_arn in sub_agent_parameter_arns]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "secretsmanager:GetSecretValue"
                ],
                "Resource": "arn:aws:secretsmanager:*:*:secret:agents/*/cognito_credentials*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "sts:GetSessionToken"
                ],
                "Resource": "*"
            }
        ]
    }
        
    rsp = iam_client.put_role_policy(
        RoleName=orchestrator_role_name,
        PolicyName="mcp_subagent_permissions",
        PolicyDocument=json.dumps(orchestrator_permissions)
    )
    return rsp


def deploy_mcp_orchestrator_agent():
    """Deploy the MCP-enhanced Orchestrator agent"""
    print("🚀 Deploying MCP-Enhanced Orchestrator agent...")
    
    region = os.environ.get("AWS_DEFAULT_REGION", "us-west-2")
    agent_name = "mcp_orchestrator_agent"
    
    # Get sub-agent ARNs that this orchestrator will communicate with via MCP
    try:
        sub_agent_names = ["langgraph_agent", "crewai_agent"]
        sub_agent_arns = []
        sub_agent_parameter_arns = []
        
        for sub_agent_name in sub_agent_names:
            try:
                arn = get_agent_arn_from_parameter_store(sub_agent_name)
                sub_agent_arns.append(arn)
                sub_agent_parameter_arns.append(f"arn:aws:ssm:{region}:*:parameter/agents/{sub_agent_name}_arn")
                print(f"✅ Found sub-agent: {sub_agent_name}")
            except Exception as e:
                print(f"⚠️  Warning: Could not find {sub_agent_name}: {e}")
        
        if not sub_agent_arns:
            print("❌ No sub-agents found. Please deploy LangGraph and CrewAI agents first.")
            return None
        
    except Exception as e:
        print(f"❌ Failed to retrieve sub-agent information: {e}")
        return None
    
    try:
        # Create IAM role with MCP permissions
        iam_role_name = f"AgentCore-{agent_name}-Role"
        iam_response = create_agentcore_role(agent_name, region)
        
        # Update permissions for MCP communication
        update_mcp_orchestrator_permissions(sub_agent_arns, sub_agent_parameter_arns, iam_role_name)
        print("✅ MCP permissions configured")
        
        # Change to agent directory and deploy using the pattern from working deployment
        original_dir = os.getcwd()
        os.chdir("orchestrator_agent")
        
        try:
            print("Configuring AgentCore runtime...")
            boto_session = Session(region_name=region)
            
            agentcore_runtime = Runtime()
            
            # Configure the agent with MCP requirements
            config_response = agentcore_runtime.configure(
                entrypoint="basic_mcp_orchestrator.py",  # Back to working orchestrator with agent communication
                execution_role=iam_response['Role']['Arn'],
                auto_create_ecr=True,
                requirements_file="requirements_basic.txt",  # Basic requirements
                region=region,
                agent_name=agent_name
            )
            
            print(f"✅ {agent_name} configured successfully!")
            
            # Launch the agent (this actually deploys it)
            print("Launching MCP agent...")
            launch_response = agentcore_runtime.launch()
            
            print(f"✅ {agent_name} launched successfully!")
            print(f"Launch response type: {type(launch_response)}")
            
            # Extract ARN
            if hasattr(launch_response, 'get'):
                agent_arn = launch_response.get('agent_arn') or launch_response.get('arn')
            else:
                # Try different ways to get ARN
                agent_arn = None
                if hasattr(launch_response, 'agent_arn'):
                    agent_arn = launch_response.agent_arn
                elif hasattr(launch_response, 'arn'):
                    agent_arn = launch_response.arn
                    
        finally:
            os.chdir(original_dir)
        
        if agent_arn:
            print(f"✅ {agent_name} deployed successfully!")
            print(f"Agent ARN: {agent_arn}")
            
            # Save ARN to Parameter Store
            save_agent_arn_to_parameter_store(agent_name, agent_arn)
            
            # Test MCP connectivity
            print("\n🧪 Testing MCP connectivity...")
            test_mcp_connectivity(agent_arn)
            
            return {
                'agent_name': agent_name,
                'agent_arn': agent_arn,
                'protocol': 'MCP',
                'sub_agents': sub_agent_names,
                'status': 'deployed'
            }
        else:
            print("❌ Failed to get agent ARN from deployment response")
            return None
            
    except Exception as e:
        print(f"❌ MCP Orchestrator deployment failed: {e}")
        raise


def test_mcp_connectivity(agent_arn: str):
    """Test MCP connectivity with the deployed orchestrator"""
    try:
        from mcp_client_utils import MCPAgentClient
        import asyncio
        
        async def test_connection():
            client = MCPAgentClient()
            
            # Test basic connectivity
            print("  🔍 Testing MCP protocol connectivity...")
            
            # Since we can't directly invoke the orchestrator via MCP from here,
            # we'll test the sub-agent connectivity instead
            test_agents = ["langgraph_agent", "crewai_agent"]
            
            for agent_name in test_agents:
                try:
                    tools = await client.list_agent_tools(agent_name)
                    print(f"  ✅ {agent_name}: Found {len(tools)} MCP tools")
                except Exception as e:
                    print(f"  ⚠️  {agent_name}: MCP connection issue - {e}")
        
        # Run async test
        asyncio.run(test_connection())
        print("✅ MCP connectivity test completed")
        
    except ImportError:
        print("⚠️  MCP libraries not available for testing - install requirements_mcp.txt")
    except Exception as e:
        print(f"⚠️  MCP connectivity test failed: {e}")


def main():
    """Main deployment function"""
    print("🎯 MCP-Enhanced Multi-Agent Kitchen Renovation System")
    print("=" * 60)
    
    try:
        deployment_result = deploy_mcp_orchestrator_agent()
        
        if deployment_result:
            print("\n🎉 MCP Orchestrator Deployment Summary:")
            print("=" * 40)
            print(f"Agent Name: {deployment_result['agent_name']}")
            print(f"Agent ARN: {deployment_result['agent_arn']}")
            print(f"Protocol: {deployment_result['protocol']}")
            print(f"Sub-Agents: {', '.join(deployment_result['sub_agents'])}")
            print(f"Status: {deployment_result['status']}")
            
            print("\n🔧 MCP Benefits:")
            print("- Standardized agent communication protocol")
            print("- Enhanced error handling and observability")
            print("- Tool discovery capabilities")
            print("- Better authentication and security")
            print("- Improved scalability and reliability")
            
            print(f"\n📋 Next Steps:")
            print("1. Test the MCP orchestrator in the AWS Console")
            print("2. Update your Streamlit app to use the MCP orchestrator")
            print("3. Monitor enhanced observability via CloudWatch and X-Ray")
            
        else:
            print("❌ Deployment failed - check logs above")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Deployment process failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
