#!/usr/bin/env python3
"""
Deploy Orchestrator agent to Bedrock AgentCore
"""

import os
import sys
import boto3
import json
from bedrock_agentcore_starter_toolkit import Runtime
from boto3.session import Session
from utils import create_agentcore_role, save_agent_arn_to_parameter_store, get_agent_arn_from_parameter_store


def update_orchestrator_permissions(sub_agent_arns: list, sub_agent_parameter_arns: list, orchestrator_role_name: str):
    """Update orchestrator IAM role to allow calling sub-agents"""
    iam_client = boto3.client('iam')
    orchestrator_permissions = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "bedrock-agentcore:InvokeAgentRuntime"
                ],
                "Resource": [sub_agent_arn + "/runtime-endpoint/DEFAULT" for sub_agent_arn in sub_agent_arns] + [sub_agent_arn for sub_agent_arn in sub_agent_arns]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "ssm:GetParameter"
                ],
                "Resource": [sub_agent_parameter_arn for sub_agent_parameter_arn in sub_agent_parameter_arns]
            }]
    }
        
    rsp = iam_client.put_role_policy(
        RoleName=orchestrator_role_name,
        PolicyName="subagent_permissions",
        PolicyDocument=json.dumps(orchestrator_permissions)
    )
    return rsp


def deploy_orchestrator_agent():
    """Deploy the Orchestrator agent"""
    print("🚀 Deploying Orchestrator agent...")
    
    region = os.environ.get("AWS_DEFAULT_REGION", "us-west-2")
    agent_name = "orchestrator_agent"
    
    # Get sub-agent ARNs from Parameter Store
    print("Getting sub-agent ARNs...")
    langgraph_agent_arn = get_agent_arn_from_parameter_store("langgraph_agent")
    crewai_agent_arn = get_agent_arn_from_parameter_store("crewai_agent")
    
    print(f"LangGraph Agent ARN: {langgraph_agent_arn}")
    print(f"CrewAI Agent ARN: {crewai_agent_arn}")
    
    # Create IAM role
    print(f"Creating IAM role for {agent_name}...")
    iam_role = create_agentcore_role(agent_name, region)
    
    # Update orchestrator permissions to call sub-agents
    print("Updating orchestrator permissions...")
    ssm = boto3.client('ssm')
    
    # Get parameter ARNs
    langgraph_param_response = ssm.get_parameter(Name='/agents/langgraph_agent_arn')
    crewai_param_response = ssm.get_parameter(Name='/agents/crewai_agent_arn')
    
    langgraph_param_arn = langgraph_param_response['Parameter']['ARN']
    crewai_param_arn = crewai_param_response['Parameter']['ARN']
    
    update_orchestrator_permissions(
        [langgraph_agent_arn, crewai_agent_arn],
        [langgraph_param_arn, crewai_param_arn],
        iam_role['Role']['RoleName']
    )
    
    # Change to agent directory
    original_dir = os.getcwd()
    os.chdir("orchestrator_agent")
    
    try:
        # Configure runtime
        print("Configuring AgentCore runtime...")
        boto_session = Session(region_name=region)
        
        agentcore_runtime = Runtime()
        
        # Configure the agent
        config_response = agentcore_runtime.configure(
            entrypoint="orchestrator_agent.py",
            execution_role=iam_role['Role']['Arn'],
            auto_create_ecr=True,
            requirements_file="requirements.txt",
            region=region,
            agent_name=agent_name
        )
        
        print(f"✅ {agent_name} configured successfully!")
        
        # Now launch the agent (this actually deploys it)
        print("Launching agent...")
        launch_response = agentcore_runtime.launch()
        
        print(f"✅ {agent_name} launched successfully!")
        print(f"Launch response type: {type(launch_response)}")
        print(f"Launch response: {launch_response}")
        
        # Extract agent ARN from launch response
        agent_arn = launch_response.agent_arn
        agent_id = launch_response.agent_id
        
        print(f"Agent ARN: {agent_arn}")
        print(f"Agent ID: {agent_id}")
        
        # Save ARN to Parameter Store
        save_agent_arn_to_parameter_store(agent_name, agent_arn)
        
        return agent_arn
        
    except Exception as e:
        print(f"❌ Failed to deploy {agent_name}: {e}")
        return None
        
    finally:
        os.chdir(original_dir)


if __name__ == "__main__":
    deploy_orchestrator_agent()
