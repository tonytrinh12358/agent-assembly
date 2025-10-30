"""
Utility functions for AgentCore deployment
"""
import boto3
from botocore.config import Config
import json
import time
from typing import Dict, Any


def create_agentcore_role(agent_name: str, region: str) -> Dict[str, Any]:
    """
    Create IAM role for AgentCore agent
    """
    iam_client = boto3.client('iam', region_name=region)
    
    # Trust policy for AgentCore
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "bedrock-agentcore.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    # Basic permissions policy
    permissions_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream"
                ],
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "ecr:GetAuthorizationToken",
                    "ecr:BatchGetImage",
                    "ecr:GetDownloadUrlForLayer"
                ],
                "Resource": "*"
            }
        ]
    }
    
    role_name = f"AgentCore-{agent_name}-Role"
    
    try:
        # Create role
        role_response = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description=f"IAM role for AgentCore agent {agent_name}"
        )
        
        # Attach basic permissions
        iam_client.put_role_policy(
            RoleName=role_name,
            PolicyName=f"{agent_name}-permissions",
            PolicyDocument=json.dumps(permissions_policy)
        )
        
        print(f"✅ Created IAM role: {role_name}")
        return role_response
        
    except iam_client.exceptions.EntityAlreadyExistsException:
        # Role already exists, get it
        role_response = iam_client.get_role(RoleName=role_name)
        print(f"ℹ️ IAM role already exists: {role_name}")
        return role_response


def update_orchestrator_permissions(sub_agent_arns: list, sub_agent_parameter_arns: list, orchestrator_role_name: str):
    """
    Update orchestrator role with permissions to invoke sub-agents
    """
    iam_client = boto3.client('iam')
    
    orchestrator_permissions = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "bedrock-agentcore:InvokeAgentRuntime"
                ],
                "Resource": [sub_agent_arn + "/runtime-endpoint/DEFAULT" for sub_agent_arn in sub_agent_arns] + sub_agent_arns
            },
            {
                "Effect": "Allow",
                "Action": [
                    "ssm:GetParameter"
                ],
                "Resource": sub_agent_parameter_arns
            }
        ]
    }
    
    try:
        iam_client.put_role_policy(
            RoleName=orchestrator_role_name,
            PolicyName="subagent_permissions",
            PolicyDocument=json.dumps(orchestrator_permissions)
        )
        print(f"✅ Updated orchestrator permissions for {orchestrator_role_name}")
    except Exception as e:
        print(f"❌ Failed to update orchestrator permissions: {e}")
        raise


def save_agent_arn_to_parameter_store(agent_name: str, agent_arn: str):
    """
    Save agent ARN to Parameter Store for lookup
    """
    ssm = boto3.client('ssm')
    try:
        ssm.put_parameter(
            Name=f'/agents/{agent_name}_arn',
            Value=agent_arn,
            Type='String',
            Overwrite=True
        )
        print(f"✅ Saved {agent_name} ARN to Parameter Store")
    except Exception as e:
        print(f"❌ Failed to save {agent_name} ARN: {e}")
        raise


def get_agent_arn_from_parameter_store(agent_name: str) -> str:
    """
    Retrieve agent ARN from Parameter Store
    """
    ssm = boto3.client('ssm')
    try:
        response = ssm.get_parameter(Name=f'/agents/{agent_name}_arn')
        return response['Parameter']['Value']
    except Exception as e:
        print(f"❌ Failed to get {agent_name} ARN: {e}")
        raise


def invoke_agent_with_boto3(agent_arn: str, user_query: str) -> str:
    """
    Invoke an AgentCore agent using boto3
    """
    client = boto3.client('bedrock-agentcore', region_name='us-west-2', 
                          config=Config(read_timeout=180, retries={'max_attempts': 5, 'mode': 'adaptive'}))
    
    try:
        import json
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
