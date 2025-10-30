#!/usr/bin/env python3
"""
Deploy Kitchen Analysis Agents to Bedrock AgentCore
"""

import os
import sys
import time
import boto3
from bedrock_agentcore_starter_toolkit import Runtime
from boto3.session import Session
from utils import (
    create_agentcore_role, 
    update_orchestrator_permissions, 
    save_agent_arn_to_parameter_store
)


def configure_runtime(agent_name, agentcore_iam_role, python_file_name, region="us-west-2"):
    """Configure AgentCore runtime for an agent"""
    boto_session = Session(region_name=region)
    
    agentcore_runtime = Runtime()
    
    response = agentcore_runtime.configure(
        entrypoint=python_file_name,
        execution_role=agentcore_iam_role['Role']['Arn'],
        auto_create_ecr=True,
        requirements_file="requirements.txt",
        region=region,
        agent_name=agent_name
    )
    return response, agentcore_runtime


def check_status(agent_runtime):
    """Check agent runtime status until ready"""
    status_response = agent_runtime.status()
    status = status_response.endpoint['status']
    end_status = ['READY', 'CREATE_FAILED', 'DELETE_FAILED', 'UPDATE_FAILED']
    
    print(f"Initial status: {status}")
    
    while status not in end_status:
        time.sleep(30)  # Wait 30 seconds between checks
        status_response = agent_runtime.status()
        status = status_response.endpoint['status']
        print(f"Status: {status}")
    
    return status


def deploy_agent(agent_name, agent_dir, python_file, region="us-west-2"):
    """Deploy a single agent to AgentCore"""
    print(f"\n🚀 Deploying {agent_name}...")
    
    # Create IAM role
    iam_role = create_agentcore_role(agent_name, region)
    
    # Change to agent directory
    original_dir = os.getcwd()
    os.chdir(agent_dir)
    
    try:
        # Configure runtime
        _, runtime = configure_runtime(agent_name, iam_role, python_file, region)
        
        # Launch agent
        launch_result = runtime.launch()
        agent_arn = launch_result.agent_arn
        
        print(f"✅ {agent_name} launched with ARN: {agent_arn}")
        
        # Save ARN to Parameter Store
        save_agent_arn_to_parameter_store(agent_name, agent_arn)
        
        # Check status
        status = check_status(runtime)
        
        if status == 'READY':
            print(f"✅ {agent_name} is ready!")
            return {
                'agent_name': agent_name,
                'agent_arn': agent_arn,
                'agent_id': launch_result.agent_id,
                'runtime': runtime,
                'iam_role': iam_role,
                'status': 'ready'
            }
        else:
            print(f"❌ {agent_name} failed to deploy. Status: {status}")
            return {
                'agent_name': agent_name,
                'status': 'failed',
                'error': f"Deployment failed with status: {status}"
            }
            
    finally:
        # Return to original directory
        os.chdir(original_dir)


def main():
    """Main deployment function"""
    print("🏠 Deploying Kitchen Analysis Agents to Bedrock AgentCore")
    print("=" * 60)
    
    # Set region
    region = os.environ.get("AWS_DEFAULT_REGION", "us-west-2")
    print(f"Using region: {region}")
    
    # Agent configurations
    agents_config = [
        {
            'name': 'langgraph_agent',
            'dir': 'langgraph_agent',
            'file': 'langgraph_agent.py'
        },
        {
            'name': 'crewai_agent', 
            'dir': 'crewai_agent',
            'file': 'crewai_agent.py'
        }
    ]
    
    deployed_agents = []
    
    # Deploy LangGraph and CrewAI agents first
    for config in agents_config:
        result = deploy_agent(
            config['name'],
            config['dir'], 
            config['file'],
            region
        )
        deployed_agents.append(result)
        
        if result['status'] != 'ready':
            print(f"❌ Failed to deploy {config['name']}, stopping deployment")
            return False
    
    # Deploy orchestrator agent with permissions to call sub-agents
    print(f"\n🚀 Deploying orchestrator_agent...")
    
    # Create orchestrator IAM role
    orchestrator_iam_role = create_agentcore_role("orchestrator_agent", region)
    
    # Get sub-agent ARNs for permissions
    ssm = boto3.client('ssm', region_name=region)
    
    sub_agent_arns = []
    sub_agent_parameter_arns = []
    
    for agent in deployed_agents:
        if agent['status'] == 'ready':
            sub_agent_arns.append(agent['agent_arn'])
            # Get parameter ARN
            param_response = ssm.get_parameter(Name=f"/agents/{agent['agent_name']}_arn")
            sub_agent_parameter_arns.append(param_response['Parameter']['ARN'])
    
    # Update orchestrator permissions
    update_orchestrator_permissions(
        sub_agent_arns, 
        sub_agent_parameter_arns, 
        orchestrator_iam_role['Role']['RoleName']
    )
    
    # Deploy orchestrator
    orchestrator_result = deploy_agent(
        "orchestrator_agent",
        "orchestrator_agent",
        "orchestrator_agent.py", 
        region
    )
    
    deployed_agents.append(orchestrator_result)
    
    # Summary
    print("\n📋 Deployment Summary")
    print("=" * 40)
    
    all_success = True
    for agent in deployed_agents:
        status_icon = "✅" if agent['status'] == 'ready' else "❌"
        print(f"{status_icon} {agent['agent_name']}: {agent['status']}")
        if agent['status'] != 'ready':
            all_success = False
            if 'error' in agent:
                print(f"   Error: {agent['error']}")
    
    if all_success:
        print("\n🎉 All agents deployed successfully!")
        print("\nAgent ARNs saved to Parameter Store:")
        for agent in deployed_agents:
            if agent['status'] == 'ready':
                print(f"  /agents/{agent['agent_name']}_arn")
        
        return True
    else:
        print("\n❌ Some agents failed to deploy")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

