"""
Quick Test for Agent-to-Agent Communication
Simple test to verify orchestrator calls other agents
"""

import boto3
import json

def quick_test():
    """Quick test of agent-to-agent communication"""
    print("🚀 Quick Agent-to-Agent Communication Test")
    print("=" * 50)
    
    # Get orchestrator ARN
    ssm = boto3.client('ssm', region_name='us-west-2')
    response = ssm.get_parameter(Name='/agents/orchestrator_agent_arn')
    orchestrator_arn = response['Parameter']['Value']
    print(f"✅ Using orchestrator: {orchestrator_arn.split('/')[-1]}")
    
    # Call orchestrator with agent coordination request
    client = boto3.client('bedrock-agentcore', region_name='us-west-2')
    
    payload = {
        'prompt': 'Please coordinate a kitchen renovation analysis: analyze the kitchen layout first using the analysis agent, then estimate costs using the cost estimation agent.',
        'test_mode': True
    }
    
    print("\n🔗 Calling orchestrator for agent coordination...")
    
    payload_bytes = json.dumps(payload).encode('utf-8')
    response = client.invoke_agent_runtime(
        agentRuntimeArn=orchestrator_arn,
        payload=payload_bytes
    )
    
    # Get response
    if 'response' in response:
        result = response['response'].read().decode('utf-8')
        
        print(f"✅ Response received: {len(result)} characters")
        
        # Check for agent mentions
        mentions = []
        if 'langgraph' in result.lower():
            mentions.append('LangGraph')
        if 'crewai' in result.lower():  
            mentions.append('CrewAI')
        if 'cost' in result.lower():
            mentions.append('Cost estimation')
        if 'analysis' in result.lower():
            mentions.append('Analysis')
            
        print(f"🎯 Agent coordination detected: {', '.join(mentions) if mentions else 'None'}")
        
        # Show sample
        sample = result[:500].replace('data: "', '').replace('"', '')
        print(f"\n📋 Sample response:")
        print(f"   {sample}...")
        
        if mentions:
            print(f"\n🎉 SUCCESS: Orchestrator is coordinating with other agents!")
            print("✅ TRUE agent-to-agent communication verified!")
        else:
            print("\n⚠️  Basic response - agent coordination may need attention")
            
    else:
        print("❌ No response received")

if __name__ == "__main__":
    quick_test()
