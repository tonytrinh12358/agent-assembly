#!/usr/bin/env python3
"""
Test the orchestrator agent calling sub-agents
"""

import os
from utils import invoke_agent_with_boto3, get_agent_arn_from_parameter_store


def test_orchestrator_agent():
    """Test the orchestrator agent with a complex query that should trigger both sub-agents"""
    
    try:
        # Set region
        os.environ["AWS_DEFAULT_REGION"] = "us-west-2"
        
        # Get orchestrator ARN
        orchestrator_arn = get_agent_arn_from_parameter_store("orchestrator_agent")
        print(f"Testing orchestrator: {orchestrator_arn}")
        
        # Test query that should trigger both agents
        test_query = """
        I need help with my kitchen renovation project. I want to:
        1. Analyze my kitchen layout and get renovation recommendations
        2. Get cost estimates for the materials and work needed
        
        Please help me with both aspects of this project.
        """
        
        print("🚀 Testing orchestrator with complex query...")
        print(f"Query: {test_query}")
        print("\n" + "="*80 + "\n")
        
        # Invoke the orchestrator
        result = invoke_agent_with_boto3(orchestrator_arn, test_query)
        
        print("✅ Orchestrator response:")
        print(result)
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to test orchestrator: {e}")
        return False


def test_individual_agents():
    """Test each individual agent to make sure they still work"""
    
    print("\n" + "="*80)
    print("🧪 Testing individual agents...")
    print("="*80 + "\n")
    
    try:
        # Test LangGraph agent
        print("1. Testing LangGraph Agent...")
        langgraph_arn = get_agent_arn_from_parameter_store("langgraph_agent")
        langgraph_result = invoke_agent_with_boto3(langgraph_arn, "Analyze a kitchen for renovation planning")
        print(f"✅ LangGraph response length: {len(str(langgraph_result))} characters")
        print(f"Preview: {str(langgraph_result)[:200]}...")
        
        print("\n" + "-"*40 + "\n")
        
        # Test CrewAI agent
        print("2. Testing CrewAI Agent...")
        crewai_arn = get_agent_arn_from_parameter_store("crewai_agent")
        crewai_result = invoke_agent_with_boto3(crewai_arn, "Estimate costs for kitchen renovation materials")
        print(f"✅ CrewAI response length: {len(str(crewai_result))} characters")
        print(f"Preview: {str(crewai_result)[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to test individual agents: {e}")
        return False


if __name__ == "__main__":
    print("🔬 Testing Multi-Agent System on Bedrock AgentCore")
    print("="*80)
    
    # Test individual agents first
    individual_success = test_individual_agents()
    
    if individual_success:
        print("\n" + "="*80)
        print("🎯 Testing Orchestrator (Multi-Agent Workflow)")
        print("="*80)
        
        # Test orchestrator
        orchestrator_success = test_orchestrator_agent()
        
        if orchestrator_success:
            print("\n🎉 All tests completed successfully!")
            print("✅ Multi-agent system is working on Bedrock AgentCore!")
        else:
            print("\n❌ Orchestrator test failed")
    else:
        print("\n❌ Individual agent tests failed")





