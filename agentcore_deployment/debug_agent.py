#!/usr/bin/env python3
"""
Debug agent connectivity with detailed error messages
"""

import boto3
import json
from botocore.exceptions import ClientError
from utils import get_agent_arn_from_parameter_store

def debug_agent_call(name, arn):
    print(f'\n🔍 Debugging {name}')
    print(f'ARN: {arn}')
    print('-' * 60)
    
    try:
        # Try bedrock-agentcore client first
        print('📞 Trying bedrock-agentcore client...')
        client = boto3.client('bedrock-agentcore', region_name='us-west-2')
        payload = json.dumps({'prompt': 'test'}).encode('utf-8')
        
        response = client.invoke_agent_runtime(
            agentRuntimeArn=arn,
            payload=payload
        )
        
        print(f'✅ {name}: SUCCESS with bedrock-agentcore!')
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_msg = e.response['Error']['Message']
        print(f'❌ ClientError: {error_code} - {error_msg}')
        
        if 'not found' in error_msg.lower() or 'does not exist' in error_msg.lower():
            print('💡 DIAGNOSIS: Agent was deleted or never deployed')
        elif 'access denied' in error_msg.lower():
            print('💡 DIAGNOSIS: Permission issue - check IAM roles')
        elif 'invalid' in error_msg.lower():
            print('💡 DIAGNOSIS: Invalid ARN format or service')
        else:
            print(f'💡 DIAGNOSIS: Unknown error - {error_msg}')
            
        return False
        
    except Exception as e:
        error_msg = str(e)
        print(f'❌ Exception: {error_msg}')
        
        if 'bedrock-agentcore' in error_msg and 'not found' in error_msg:
            print('💡 DIAGNOSIS: bedrock-agentcore service not available')
        elif 'timeout' in error_msg.lower():
            print('💡 DIAGNOSIS: Network timeout')
        else:
            print(f'💡 DIAGNOSIS: {error_msg}')
            
        return False

def main():
    print('🚨 DEBUGGING AGENT CONNECTIVITY ISSUES')
    print('=' * 70)
    
    try:
        # Check each agent
        agents = [
            ('LangGraph', get_agent_arn_from_parameter_store('langgraph_agent')),
            ('CrewAI', get_agent_arn_from_parameter_store('crewai_agent')),
            ('Orchestrator', get_agent_arn_from_parameter_store('orchestrator_agent'))
        ]
        
        working_count = 0
        for name, arn in agents:
            result = debug_agent_call(name, arn)
            if result:
                working_count += 1
        
        print('\n' + '=' * 70)
        print(f'📊 SUMMARY: {working_count}/3 agents working')
        
        if working_count == 0:
            print('\n🚨 CRITICAL: No agents responding!')
            print('\n💡 SOLUTIONS:')
            print('1. Redeploy all agents: python deploy_agents.py')
            print('2. Check if AgentCore service is available in your account')
            print('3. Verify AWS credentials and region')
            
        return working_count > 0
        
    except Exception as e:
        print(f'❌ Debug setup failed: {e}')
        return False

if __name__ == "__main__":
    main()
