#!/usr/bin/env python3
"""
Test deployed agent
"""

import boto3
import json
from utils import invoke_agent_with_boto3, get_agent_arn_from_parameter_store


def test_langgraph_agent():
    """Test the deployed LangGraph agent"""
    
    try:
        # Get agent ARN from Parameter Store
        agent_arn = get_agent_arn_from_parameter_store("langgraph_agent")
        print(f"Testing agent: {agent_arn}")
        
        # Test the agent using our fixed utility function
        result = invoke_agent_with_boto3(agent_arn, "Analyze a kitchen for renovation planning")
        
        print("✅ Agent response:")
        print(result)
        return True
        
    except Exception as e:
        print(f"❌ Failed to test agent: {e}")
        return False


if __name__ == "__main__":
    test_langgraph_agent()
