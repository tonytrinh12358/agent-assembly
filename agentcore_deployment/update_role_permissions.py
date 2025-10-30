#!/usr/bin/env python3
"""
Update existing IAM role with ECR permissions
"""

import boto3
import json


def update_role_permissions():
    """Update the existing IAM role with ECR permissions"""
    iam_client = boto3.client('iam')
    role_name = "AgentCore-langgraph_agent-Role"
    
    # Updated permissions policy with ECR access
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
    
    try:
        # Update the role policy
        iam_client.put_role_policy(
            RoleName=role_name,
            PolicyName="langgraph_agent-permissions",
            PolicyDocument=json.dumps(permissions_policy)
        )
        print(f"✅ Updated permissions for role: {role_name}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to update role permissions: {e}")
        return False


if __name__ == "__main__":
    update_role_permissions()

