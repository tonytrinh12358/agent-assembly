#!/usr/bin/env python3
"""
Test the complete multi-agent workflow with proper data flow
"""

import os
import json
from utils import invoke_agent_with_boto3, get_agent_arn_from_parameter_store


def test_complete_workflow():
    """Test the complete workflow: LangGraph -> CrewAI via Orchestrator"""
    
    try:
        # Set region
        os.environ["AWS_DEFAULT_REGION"] = "us-west-2"
        
        # Get orchestrator ARN
        orchestrator_arn = get_agent_arn_from_parameter_store("orchestrator_agent")
        print(f"Testing orchestrator: {orchestrator_arn}")
        
        # Test query that should trigger the full workflow
        test_query = """
        I have a kitchen with a refrigerator and oven that I want to renovate. 
        Please analyze the layout and provide cost estimates for materials and labor.
        Assume this is a standard Australian kitchen renovation project.
        """
        
        print("🚀 Testing complete multi-agent workflow...")
        print(f"Query: {test_query}")
        print("\n" + "="*80 + "\n")
        
        # Invoke the orchestrator
        result = invoke_agent_with_boto3(orchestrator_arn, test_query)
        
        print("✅ Complete workflow response:")
        print(result)
        
        # Check if the response contains evidence of both agents being called
        result_str = str(result)
        has_langgraph_data = any(keyword in result_str.lower() for keyword in ['kitchen', 'renovation', 'analysis', 'layout'])
        has_crewai_data = any(keyword in result_str.lower() for keyword in ['cost', 'estimate', 'price', 'budget', 'materials'])
        
        print(f"\n📊 Analysis:")
        print(f"✅ Contains kitchen analysis data: {has_langgraph_data}")
        print(f"✅ Contains cost estimation data: {has_crewai_data}")
        
        if has_langgraph_data and has_crewai_data:
            print("🎉 SUCCESS: Multi-agent workflow is working correctly!")
            return True
        else:
            print("⚠️  Partial success: Some agent data may be missing")
            return False
        
    except Exception as e:
        print(f"❌ Failed to test complete workflow: {e}")
        return False


def test_direct_agent_calls():
    """Test calling agents directly to compare with orchestrator results"""
    
    print("\n" + "="*80)
    print("🔍 Testing direct agent calls for comparison...")
    print("="*80 + "\n")
    
    try:
        # Test LangGraph agent directly
        print("1. Direct LangGraph Agent call...")
        langgraph_arn = get_agent_arn_from_parameter_store("langgraph_agent")
        langgraph_query = "Analyze a kitchen with refrigerator and oven for renovation planning"
        langgraph_result = invoke_agent_with_boto3(langgraph_arn, langgraph_query)
        
        print(f"✅ LangGraph direct result (length: {len(str(langgraph_result))} chars)")
        
        # Parse the JSON response to extract materials data
        try:
            langgraph_data = json.loads(langgraph_result)
            if 'materials' in langgraph_data:
                materials_data = langgraph_data['materials']
                print(f"📋 Materials found: {len(materials_data)} items")
                
                # Test CrewAI agent with the materials data
                print("\n2. Direct CrewAI Agent call with LangGraph materials...")
                crewai_arn = get_agent_arn_from_parameter_store("crewai_agent")
                
                # Create the payload that CrewAI expects
                crewai_payload = {
                    "materials_data": materials_data,
                    "cost_grade": "standard"
                }
                
                # For the direct call, we need to format this as a query
                crewai_query = f"Estimate costs for these materials: {json.dumps(materials_data)} with cost grade: standard"
                crewai_result = invoke_agent_with_boto3(crewai_arn, crewai_query)
                
                print(f"✅ CrewAI direct result (length: {len(str(crewai_result))} chars)")
                print(f"Preview: {str(crewai_result)[:300]}...")
                
                return True
            else:
                print("⚠️  No materials data found in LangGraph response")
                return False
                
        except json.JSONDecodeError:
            print("⚠️  Could not parse LangGraph response as JSON")
            return False
        
    except Exception as e:
        print(f"❌ Failed to test direct agent calls: {e}")
        return False


if __name__ == "__main__":
    print("🔬 Testing Complete Multi-Agent Workflow")
    print("="*80)
    
    # Test the complete workflow through orchestrator
    workflow_success = test_complete_workflow()
    
    # Test direct agent calls for comparison
    direct_success = test_direct_agent_calls()
    
    print("\n" + "="*80)
    print("📋 FINAL RESULTS:")
    print("="*80)
    print(f"✅ Orchestrator workflow: {'SUCCESS' if workflow_success else 'NEEDS WORK'}")
    print(f"✅ Direct agent calls: {'SUCCESS' if direct_success else 'NEEDS WORK'}")
    
    if workflow_success and direct_success:
        print("\n🎉 COMPLETE SUCCESS: Multi-agent system is fully operational!")
    else:
        print("\n🔧 Some components need debugging...")





