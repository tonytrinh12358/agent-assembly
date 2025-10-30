#!/usr/bin/env python3
"""
Simple test of the orchestrator agent
"""

import os
from utils import invoke_agent_with_boto3, get_agent_arn_from_parameter_store


def test_orchestrator_simple():
    """Simple test of the orchestrator"""
    
    try:
        # Set region
        os.environ["AWS_DEFAULT_REGION"] = "us-west-2"
        
        # Get orchestrator ARN
        orchestrator_arn = get_agent_arn_from_parameter_store("orchestrator_agent")
        print(f"Testing orchestrator: {orchestrator_arn}")
        
        # Simple test query
        test_query = "I want to renovate my kitchen. Please analyze it and give me cost estimates."
        
        print("🚀 Testing orchestrator...")
        print(f"Query: {test_query}")
        print("\n" + "="*80 + "\n")
        
        # Invoke the orchestrator
        result = invoke_agent_with_boto3(orchestrator_arn, test_query)
        
        print("✅ Orchestrator response:")
        print(result)
        
        # Check for evidence of tool usage
        result_str = str(result)
        has_tool_execution = "[Executing:" in result_str
        has_analysis_data = any(keyword in result_str.lower() for keyword in ['kitchen', 'analysis', 'materials', 'cost'])
        
        print(f"\n📊 Analysis:")
        print(f"✅ Tool execution detected: {has_tool_execution}")
        print(f"✅ Contains analysis data: {has_analysis_data}")
        
        if has_tool_execution:
            print("🎉 SUCCESS: Orchestrator is calling sub-agents as tools!")
            return True
        else:
            print("⚠️  Orchestrator is not using tools properly")
            return False
        
    except Exception as e:
        print(f"❌ Failed to test orchestrator: {e}")
        return False


if __name__ == "__main__":
    print("🔬 Simple Orchestrator Test")
    print("="*80)
    
    success = test_orchestrator_simple()
    
    print("\n" + "="*80)
    if success:
        print("🎉 ORCHESTRATOR IS WORKING!")
        print("✅ Multi-agent system successfully deployed to Bedrock AgentCore!")
    else:
        print("🔧 Orchestrator needs more debugging...")





