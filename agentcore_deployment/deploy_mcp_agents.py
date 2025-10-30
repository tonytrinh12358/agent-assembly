#!/usr/bin/env python3
"""
Deploy MCP-enabled agents to Amazon Bedrock AgentCore Runtime
Supports MCP protocol with Cognito authentication
"""

import os
import sys
import json
import logging
import argparse
from typing import Dict, Any, Optional
from pathlib import Path

# Add mcp_base to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'mcp_base'))

from bedrock_agentcore_starter_toolkit import Runtime
from boto3.session import Session
from auth_utils import CognitoAuthManager
import boto3
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MCPAgentDeployer:
    """Deploys MCP-enabled agents to AgentCore Runtime with Cognito authentication"""
    
    def __init__(self, region: str = "us-west-2"):
        self.region = region
        self.session = Session()
        self.auth_manager = CognitoAuthManager(region)
        self.ssm_client = boto3.client('ssm', region_name=region)
        
    def deploy_mcp_agent(
        self, 
        agent_name: str, 
        agent_dir: str, 
        entrypoint: str,
        description: str = "",
        setup_cognito: bool = True
    ) -> Dict[str, Any]:
        """
        Deploy a single MCP agent to AgentCore Runtime
        
        Args:
            agent_name: Name of the agent (e.g., 'langgraph_agent')
            agent_dir: Directory containing agent code
            entrypoint: Python entrypoint file (e.g., 'langgraph_mcp_server.py')
            description: Description of the agent
            setup_cognito: Whether to setup Cognito authentication
            
        Returns:
            Deployment result with ARN and configuration
        """
        try:
            logger.info(f"🚀 Deploying MCP agent: {agent_name}")
            logger.info(f"📁 Agent directory: {agent_dir}")
            logger.info(f"🐍 Entrypoint: {entrypoint}")
            
            # Validate files exist
            agent_path = Path(agent_dir)
            if not agent_path.exists():
                raise FileNotFoundError(f"Agent directory not found: {agent_dir}")
            
            entrypoint_path = agent_path / entrypoint
            if not entrypoint_path.exists():
                raise FileNotFoundError(f"Entrypoint file not found: {entrypoint_path}")
            
            requirements_path = agent_path / "requirements.txt"
            if not requirements_path.exists():
                raise FileNotFoundError(f"Requirements file not found: {requirements_path}")
            
            # Setup Cognito authentication if requested
            auth_config = {}
            if setup_cognito:
                try:
                    logger.info(f"🔐 Setting up Cognito authentication for {agent_name}...")
                    cognito_config = self.auth_manager.setup_cognito_for_agent(agent_name)
                    
                    auth_config = {
                        "customJWTAuthorizer": {
                            "allowedClients": [cognito_config['client_id']],
                            "discoveryUrl": cognito_config['discovery_url'],
                        }
                    }
                    logger.info(f"✅ Cognito setup completed for {agent_name}")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Cognito setup failed for {agent_name}: {e}")
                    logger.info("🔄 Proceeding without authentication (development mode)")
            
            # Change to agent directory
            original_dir = os.getcwd()
            os.chdir(agent_dir)
            
            try:
                # Initialize AgentCore Runtime
                runtime = Runtime()
                
                # Configure the runtime
                logger.info(f"⚙️ Configuring AgentCore Runtime for {agent_name}...")
                config_params = {
                    "entrypoint": entrypoint,
                    "auto_create_execution_role": True,
                    "auto_create_ecr": True,
                    "requirements_file": "requirements.txt",
                    "region": self.region,
                    "protocol": "MCP",  # Enable MCP protocol
                    "agent_name": f"{agent_name}_mcp"
                }
                
                if auth_config:
                    config_params["authorizer_configuration"] = auth_config
                
                configure_response = runtime.configure(**config_params)
                logger.info("✅ Configuration completed")
                
                # Launch the agent
                logger.info(f"🚀 Launching {agent_name} to AgentCore Runtime...")
                logger.info("⏰ This may take several minutes...")
                
                launch_result = runtime.launch()
                
                logger.info("✅ Launch initiated successfully")
                logger.info(f"🎯 Agent ARN: {launch_result.agent_arn}")
                logger.info(f"🆔 Agent ID: {launch_result.agent_id}")
                
                # Store Agent ARN in Parameter Store
                try:
                    self.ssm_client.put_parameter(
                        Name=f'/agents/{agent_name}_arn',
                        Value=launch_result.agent_arn,
                        Type='String',
                        Description=f'MCP Agent ARN for {agent_name}',
                        Overwrite=True
                    )
                    logger.info(f"✅ Agent ARN stored in Parameter Store: /agents/{agent_name}_arn")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to store ARN in Parameter Store: {e}")
                
                # Wait for deployment to complete
                logger.info("⏳ Waiting for deployment to complete...")
                deployment_status = self._wait_for_deployment(runtime)
                
                result = {
                    "agent_name": agent_name,
                    "agent_arn": launch_result.agent_arn,
                    "agent_id": launch_result.agent_id,
                    "status": deployment_status,
                    "protocol": "MCP",
                    "region": self.region,
                    "authentication": "Cognito JWT" if auth_config else "None",
                    "deployment_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                
                if deployment_status == "READY":
                    logger.info(f"🎉 {agent_name} deployed successfully!")
                else:
                    logger.warning(f"⚠️ {agent_name} deployment status: {deployment_status}")
                
                return result
                
            finally:
                # Always change back to original directory
                os.chdir(original_dir)
                
        except Exception as e:
            logger.error(f"❌ Failed to deploy {agent_name}: {e}")
            raise
    
    def _wait_for_deployment(self, runtime: Runtime, max_wait_minutes: int = 15) -> str:
        """Wait for deployment to complete"""
        try:
            end_status = ['READY', 'CREATE_FAILED', 'DELETE_FAILED', 'UPDATE_FAILED']
            wait_seconds = 0
            max_wait_seconds = max_wait_minutes * 60
            
            while wait_seconds < max_wait_seconds:
                status_response = runtime.status()
                status = status_response.endpoint['status']
                
                if status in end_status:
                    return status
                
                logger.info(f"⏳ Status: {status} - waiting... ({wait_seconds//60}m {wait_seconds%60}s)")
                time.sleep(30)
                wait_seconds += 30
            
            logger.warning(f"⚠️ Timeout waiting for deployment after {max_wait_minutes} minutes")
            return "TIMEOUT"
            
        except Exception as e:
            logger.error(f"❌ Error checking deployment status: {e}")
            return "ERROR"
    
    def deploy_all_mcp_agents(self) -> Dict[str, Any]:
        """Deploy all MCP agents in the system"""
        logger.info("🚀 Starting deployment of all MCP agents...")
        
        agents = [
            {
                "name": "langgraph_agent",
                "dir": "langgraph_agent",
                "entrypoint": "langgraph_mcp_server.py",
                "description": "Kitchen analysis with YOLO detection via MCP"
            },
            {
                "name": "crewai_agent", 
                "dir": "crewai_agent",
                "entrypoint": "crewai_mcp_server.py",
                "description": "Multi-agent cost estimation via MCP"
            },
            {
                "name": "orchestrator_agent",
                "dir": "orchestrator_agent", 
                "entrypoint": "orchestrator_mcp_server.py",
                "description": "Multi-agent coordinator via MCP"
            }
        ]
        
        deployment_results = {}
        
        for agent_config in agents:
            try:
                logger.info(f"🎯 Deploying {agent_config['name']}...")
                result = self.deploy_mcp_agent(
                    agent_config["name"],
                    agent_config["dir"],
                    agent_config["entrypoint"],
                    agent_config["description"]
                )
                deployment_results[agent_config["name"]] = result
                
                # Brief pause between deployments
                time.sleep(10)
                
            except Exception as e:
                logger.error(f"❌ Failed to deploy {agent_config['name']}: {e}")
                deployment_results[agent_config["name"]] = {
                    "status": "FAILED",
                    "error": str(e)
                }
        
        # Summary
        successful = sum(1 for result in deployment_results.values() if result.get("status") == "READY")
        total = len(agents)
        
        logger.info(f"📊 Deployment Summary: {successful}/{total} agents deployed successfully")
        
        for agent_name, result in deployment_results.items():
            status = result.get("status", "UNKNOWN")
            logger.info(f"  • {agent_name}: {status}")
        
        return {
            "summary": {
                "total_agents": total,
                "successful_deployments": successful,
                "failed_deployments": total - successful
            },
            "agents": deployment_results,
            "deployment_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def setup_system_cognito(self) -> Dict[str, Any]:
        """Setup system-wide Cognito configuration"""
        logger.info("🔐 Setting up system-wide Cognito configuration...")
        
        try:
            # Setup general MCP system config
            system_config = self.auth_manager.setup_cognito_for_agent(
                "mcp_system", 
                "multi-agent-mcp-system"
            )
            
            logger.info("✅ System-wide Cognito configuration completed")
            return system_config
            
        except Exception as e:
            logger.error(f"❌ Failed to setup system Cognito: {e}")
            raise


def main():
    """Main deployment function"""
    parser = argparse.ArgumentParser(description="Deploy MCP agents to AgentCore Runtime")
    parser.add_argument("--region", default="us-west-2", help="AWS region")
    parser.add_argument("--agent", help="Deploy specific agent only")
    parser.add_argument("--no-auth", action="store_true", help="Skip Cognito authentication setup")
    parser.add_argument("--setup-cognito", action="store_true", help="Setup system-wide Cognito only")
    
    args = parser.parse_args()
    
    deployer = MCPAgentDeployer(args.region)
    
    try:
        if args.setup_cognito:
            # Just setup Cognito configuration
            result = deployer.setup_system_cognito()
            print(json.dumps(result, indent=2))
            return
        
        if args.agent:
            # Deploy specific agent
            agent_configs = {
                "langgraph": ("langgraph_agent", "langgraph_agent", "langgraph_mcp_server.py"),
                "crewai": ("crewai_agent", "crewai_agent", "crewai_mcp_server.py"),
                "orchestrator": ("orchestrator_agent", "orchestrator_agent", "orchestrator_mcp_server.py")
            }
            
            if args.agent in agent_configs:
                name, dir_name, entrypoint = agent_configs[args.agent]
                result = deployer.deploy_mcp_agent(
                    name, dir_name, entrypoint, 
                    setup_cognito=not args.no_auth
                )
                print(json.dumps(result, indent=2))
            else:
                logger.error(f"Unknown agent: {args.agent}")
                logger.info(f"Available agents: {list(agent_configs.keys())}")
                sys.exit(1)
        else:
            # Deploy all agents
            results = deployer.deploy_all_mcp_agents()
            print(json.dumps(results, indent=2))
    
    except Exception as e:
        logger.error(f"❌ Deployment failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
