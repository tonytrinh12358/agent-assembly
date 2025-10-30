"""
Authentication utilities for MCP agents on AgentCore Runtime
Handles Cognito JWT token generation and management.
"""

import boto3
import json
import logging
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class CognitoAuthManager:
    """Manages Cognito authentication for MCP agents"""
    
    def __init__(self, region: str = "us-west-2"):
        self.region = region
        self.cognito_client = boto3.client('cognito-idp', region_name=region)
        self.secrets_client = boto3.client('secretsmanager', region_name=region)
        self.ssm_client = boto3.client('ssm', region_name=region)
    
    def setup_cognito_for_agent(self, agent_name: str, user_pool_name: str = None) -> Dict[str, Any]:
        """
        Setup Cognito User Pool and App Client for an agent
        
        Args:
            agent_name: Name of the agent
            user_pool_name: Optional custom user pool name
            
        Returns:
            Cognito configuration including user pool ID, client ID, etc.
        """
        try:
            if not user_pool_name:
                user_pool_name = f"{agent_name}-mcp-pool"
            
            logger.info(f"🔐 Setting up Cognito for {agent_name}...")
            
            # Create User Pool
            user_pool_response = self.cognito_client.create_user_pool(
                PoolName=user_pool_name,
                Policies={
                    'PasswordPolicy': {
                        'MinimumLength': 8,
                        'RequireUppercase': False,
                        'RequireLowercase': False,
                        'RequireNumbers': False,
                        'RequireSymbols': False
                    }
                },
                AutoVerifiedAttributes=['email'],
                UsernameAttributes=['email'],
                Schema=[
                    {
                        'Name': 'email',
                        'AttributeDataType': 'String',
                        'Required': True,
                        'Mutable': True
                    }
                ]
            )
            
            user_pool_id = user_pool_response['UserPool']['Id']
            logger.info(f"✅ Created User Pool: {user_pool_id}")
            
            # Create User Pool Client
            client_response = self.cognito_client.create_user_pool_client(
                UserPoolId=user_pool_id,
                ClientName=f"{agent_name}-mcp-client",
                GenerateSecret=False,  # Required for JWT token flow
                ExplicitAuthFlows=[
                    'ADMIN_NO_SRP_AUTH'
                ],
                TokenValidityUnits={
                    'AccessToken': 'hours',
                    'IdToken': 'hours',
                    'RefreshToken': 'days'
                },
                AccessTokenValidity=24,
                IdTokenValidity=24,
                RefreshTokenValidity=30
            )
            
            client_id = client_response['UserPoolClient']['ClientId']
            logger.info(f"✅ Created App Client: {client_id}")
            
            # Create User Pool Domain
            domain_name = f"{agent_name}-mcp-{user_pool_id.lower()}"
            try:
                domain_response = self.cognito_client.create_user_pool_domain(
                    Domain=domain_name,
                    UserPoolId=user_pool_id
                )
                logger.info(f"✅ Created domain: {domain_name}")
            except ClientError as e:
                if 'InvalidParameterException' in str(e):
                    logger.warning(f"Domain already exists or invalid: {domain_name}")
                    domain_name = f"{agent_name}-mcp-alt-{user_pool_id.lower()[-8:]}"
                    try:
                        domain_response = self.cognito_client.create_user_pool_domain(
                            Domain=domain_name,
                            UserPoolId=user_pool_id
                        )
                        logger.info(f"✅ Created alternate domain: {domain_name}")
                    except Exception as e2:
                        logger.warning(f"Could not create domain: {e2}")
                        domain_name = None
                else:
                    raise
            
            # Create a test user for the agent
            username = f"{agent_name}@example.com"
            password = f"TempPass123!{agent_name}"
            
            try:
                self.cognito_client.admin_create_user(
                    UserPoolId=user_pool_id,
                    Username=username,
                    TemporaryPassword=password,
                    MessageAction='SUPPRESS',
                    UserAttributes=[
                        {
                            'Name': 'email',
                            'Value': username
                        },
                        {
                            'Name': 'email_verified',
                            'Value': 'true'
                        }
                    ]
                )
                
                # Set permanent password
                self.cognito_client.admin_set_user_password(
                    UserPoolId=user_pool_id,
                    Username=username,
                    Password=password,
                    Permanent=True
                )
                
                logger.info(f"✅ Created test user: {username}")
                
            except ClientError as e:
                if 'UsernameExistsException' in str(e):
                    logger.info(f"User {username} already exists")
                else:
                    raise
            
            # Generate discovery URL (OpenID configuration, not JWKS)
            discovery_url = f"https://cognito-idp.{self.region}.amazonaws.com/{user_pool_id}/.well-known/openid-configuration"
            
            # Generate and store bearer token
            bearer_token = self._generate_bearer_token(user_pool_id, client_id, username, password)
            
            # Store configuration
            config = {
                'user_pool_id': user_pool_id,
                'client_id': client_id,
                'discovery_url': discovery_url,
                'domain': domain_name,
                'test_username': username,
                'test_password': password,
                'bearer_token': bearer_token,
                'region': self.region
            }
            
            # Store in Secrets Manager
            self._store_cognito_config(agent_name, config)
            
            logger.info(f"🎉 Cognito setup complete for {agent_name}")
            return config
            
        except Exception as e:
            logger.error(f"❌ Failed to setup Cognito for {agent_name}: {e}")
            raise
    
    def _generate_bearer_token(self, user_pool_id: str, client_id: str, username: str, password: str) -> str:
        """Generate bearer token using username/password authentication"""
        try:
            auth_response = self.cognito_client.admin_initiate_auth(
                UserPoolId=user_pool_id,
                ClientId=client_id,
                AuthFlow='ADMIN_NO_SRP_AUTH',
                AuthParameters={
                    'USERNAME': username,
                    'PASSWORD': password
                }
            )
            
            return auth_response['AuthenticationResult']['AccessToken']
            
        except Exception as e:
            logger.error(f"Failed to generate bearer token: {e}")
            return ""
    
    def _store_cognito_config(self, agent_name: str, config: Dict[str, Any]):
        """Store Cognito configuration in Secrets Manager"""
        try:
            secret_name = f'agents/{agent_name}/cognito_credentials'
            
            try:
                # Try to create new secret
                self.secrets_client.create_secret(
                    Name=secret_name,
                    Description=f'Cognito credentials for {agent_name} MCP agent',
                    SecretString=json.dumps(config, indent=2)
                )
                logger.info(f"✅ Stored Cognito config in Secrets Manager: {secret_name}")
                
            except ClientError as e:
                if 'ResourceExistsException' in str(e):
                    # Update existing secret
                    self.secrets_client.update_secret(
                        SecretId=secret_name,
                        SecretString=json.dumps(config, indent=2)
                    )
                    logger.info(f"✅ Updated Cognito config in Secrets Manager: {secret_name}")
                else:
                    raise
                    
        except Exception as e:
            logger.error(f"Failed to store Cognito config: {e}")
            raise
    
    def get_cognito_config(self, agent_name: str) -> Dict[str, Any]:
        """Retrieve Cognito configuration from Secrets Manager"""
        try:
            secret_name = f'agents/{agent_name}/cognito_credentials'
            response = self.secrets_client.get_secret_value(SecretId=secret_name)
            
            return json.loads(response['SecretString'])
            
        except Exception as e:
            logger.error(f"Failed to get Cognito config for {agent_name}: {e}")
            raise
    
    def refresh_bearer_token(self, agent_name: str) -> str:
        """Refresh bearer token for an agent"""
        try:
            config = self.get_cognito_config(agent_name)
            
            new_token = self._generate_bearer_token(
                config['user_pool_id'],
                config['client_id'],
                config['test_username'],
                config['test_password']
            )
            
            # Update stored config
            config['bearer_token'] = new_token
            self._store_cognito_config(agent_name, config)
            
            logger.info(f"✅ Refreshed bearer token for {agent_name}")
            return new_token
            
        except Exception as e:
            logger.error(f"Failed to refresh token for {agent_name}: {e}")
            raise


def setup_cognito_user_pool() -> Dict[str, Any]:
    """
    Setup Cognito User Pool for the MCP system (compatibility function)
    This function maintains compatibility with existing code patterns.
    """
    auth_manager = CognitoAuthManager()
    return auth_manager.setup_cognito_for_agent("mcp_system", "mcp-multi-agent-pool")


def get_bearer_token_for_agent(agent_name: str, region: str = "us-west-2") -> str:
    """
    Get valid bearer token for an agent - using AWS STS fallback
    
    Args:
        agent_name: Name of the agent
        region: AWS region
        
    Returns:
        Valid bearer token
    """
    auth_manager = CognitoAuthManager(region)
    try:
        config = auth_manager.get_cognito_config(agent_name)
        return config.get('bearer_token', '')
    except:
        # Fallback to AWS STS temporary token
        try:
            import boto3
            sts_client = boto3.client('sts', region_name=region)
            
            # Get temporary credentials
            response = sts_client.get_session_token(DurationSeconds=3600)
            
            # Create a simple bearer token from session token
            session_token = response['Credentials']['SessionToken']
            logger.info(f"Generated temporary STS token for {agent_name}")
            return session_token
            
        except Exception as e:
            logger.warning(f"Could not get bearer token for {agent_name}: {e}")
            return ""


# Example usage:
"""
# Setup authentication for all agents
auth_manager = CognitoAuthManager()

# Setup for each agent
langgraph_config = auth_manager.setup_cognito_for_agent("langgraph_agent")
crewai_config = auth_manager.setup_cognito_for_agent("crewai_agent")
orchestrator_config = auth_manager.setup_cognito_for_agent("orchestrator_agent")

# Later, get bearer tokens
langgraph_token = get_bearer_token_for_agent("langgraph_agent")
"""
