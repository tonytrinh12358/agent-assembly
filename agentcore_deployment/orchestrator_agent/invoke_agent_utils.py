"""
Utility functions for invoking AgentCore agents
"""
import boto3
import json
from typing import Dict, Any


def invoke_agent_with_boto3(agent_arn: str, user_query: str) -> str:
    """
    Invoke an AgentCore agent using boto3
    """
    client = boto3.client('bedrock-agentcore', region_name='us-west-2')
    
    try:
        payload_dict = {'prompt': user_query}
        payload_bytes = json.dumps(payload_dict).encode('utf-8')
        
        response = client.invoke_agent_runtime(
            agentRuntimeArn=agent_arn,
            payload=payload_bytes
        )
        
        # Handle streaming response from AgentCore
        result = ""
        if 'response' in response:
            response_body = response['response']
            # Check if it's a StreamingBody object
            if hasattr(response_body, 'read'):
                # Read the entire stream
                result = response_body.read().decode('utf-8')
            else:
                # Handle as direct string
                result = str(response_body)
        
        return result
        
    except Exception as e:
        print(f"❌ Failed to invoke agent {agent_arn}: {e}")
        return f"Error: {str(e)}"


def invoke_agent_with_materials_data(agent_arn: str, materials_data: list, cost_grade: str = "standard") -> str:
    """
    Invoke CrewAI agent with materials data
    """
    client = boto3.client('bedrock-agentcore', region_name='us-west-2')
    
    try:
        payload_dict = {
            'prompt': f"Estimate costs for kitchen renovation with {cost_grade} grade materials",
            'materials_data': materials_data,
            'cost_grade': cost_grade
        }
        payload_bytes = json.dumps(payload_dict).encode('utf-8')
        
        response = client.invoke_agent_runtime(
            agentRuntimeArn=agent_arn,
            payload=payload_bytes
        )
        
        # Handle streaming response from AgentCore
        result = ""
        if 'response' in response:
            response_body = response['response']
            # Check if it's a StreamingBody object
            if hasattr(response_body, 'read'):
                # Read the entire stream
                result = response_body.read().decode('utf-8')
            else:
                # Handle as direct string
                result = str(response_body)
        
        return result
        
    except Exception as e:
        print(f"❌ Failed to invoke agent {agent_arn}: {e}")
        return f"Error: {str(e)}"

