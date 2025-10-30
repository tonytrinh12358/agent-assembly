#!/usr/bin/env python3
"""
Deploy CrewAI agent to Bedrock AgentCore
"""

import os
import sys
from bedrock_agentcore_starter_toolkit import Runtime
from boto3.session import Session
from utils import create_agentcore_role, save_agent_arn_to_parameter_store


def deploy_crewai_agent():
    """Deploy the CrewAI agent"""
    print("🚀 Deploying CrewAI agent...")
    
    region = os.environ.get("AWS_DEFAULT_REGION", "us-west-2")
    agent_name = "crewai_agent"
    
    # Create IAM role
    print(f"Creating IAM role for {agent_name}...")
    iam_role = create_agentcore_role(agent_name, region)
    
    # Change to agent directory
    original_dir = os.getcwd()
    os.chdir("crewai_agent")
    
    try:
        # Configure runtime
        print("Configuring AgentCore runtime...")
        boto_session = Session(region_name=region)
        runtime = Runtime()
        
        response = runtime.configure(
            entrypoint="crewai_agent.py",
            execution_role=iam_role['Role']['Arn'],
            auto_create_ecr=True,
            requirements_file="requirements.txt",
            region=region,
            agent_name=agent_name
        )
        
        print("Launching agent...")
        launch_result = runtime.launch()
        
        print(f"✅ Agent launched successfully!")
        print(f"Agent ARN: {launch_result.agent_arn}")
        
        # Save to Parameter Store
        save_agent_arn_to_parameter_store(agent_name, launch_result.agent_arn)
        
        return True
        
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        return False
        
    finally:
        os.chdir(original_dir)


if __name__ == "__main__":
    success = deploy_crewai_agent()
    sys.exit(0 if success else 1)

