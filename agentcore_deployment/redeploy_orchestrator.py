#!/usr/bin/env python3
"""
Redeploy the orchestrator agent with fixes
"""

import os
from bedrock_agentcore_starter_toolkit import Runtime
from boto3.session import Session


def redeploy_orchestrator():
    """Redeploy the orchestrator agent"""
    print("🔄 Redeploying Orchestrator agent with fixes...")
    
    region = os.environ.get("AWS_DEFAULT_REGION", "us-west-2")
    
    # Change to agent directory
    original_dir = os.getcwd()
    os.chdir("orchestrator_agent")
    
    try:
        # Configure runtime
        print("Configuring AgentCore runtime...")
        boto_session = Session(region_name=region)
        
        agentcore_runtime = Runtime()
        
        # Launch the agent (this will update the existing deployment)
        print("Launching updated agent...")
        launch_response = agentcore_runtime.launch()
        
        print(f"✅ orchestrator_agent redeployed successfully!")
        print(f"Agent ARN: {launch_response.agent_arn}")
        print(f"Agent ID: {launch_response.agent_id}")
        
        return launch_response.agent_arn
        
    except Exception as e:
        print(f"❌ Failed to redeploy orchestrator_agent: {e}")
        return None
        
    finally:
        os.chdir(original_dir)


if __name__ == "__main__":
    redeploy_orchestrator()





