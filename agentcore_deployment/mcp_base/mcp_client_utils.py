"""
MCP Client Utilities for Agent-to-Agent Communication
Provides standardized way to communicate between MCP servers on AgentCore Runtime.
"""

import asyncio
import boto3
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import timedelta
from boto3.session import Session

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

logger = logging.getLogger(__name__)


class AgentCoreMCPClient:
    """MCP client for invoking other AgentCore agents using Model Context Protocol"""
    
    def __init__(self, region: str = "us-west-2", timeout: int = 120):
        self.region = region
        self.timeout = timeout
        self.session = Session()
        self._cached_credentials = {}
        
    async def get_agent_credentials(self, agent_name: str) -> Dict[str, str]:
        """
        Retrieve agent ARN and authentication credentials from AWS
        
        Args:
            agent_name: Name of the target agent (e.g., 'langgraph_agent')
            
        Returns:
            Dictionary with agent_arn and bearer_token
        """
        if agent_name in self._cached_credentials:
            return self._cached_credentials[agent_name]
            
        try:
            # Get agent ARN from Parameter Store
            ssm_client = boto3.client('ssm', region_name=self.region)
            agent_arn_response = ssm_client.get_parameter(
                Name=f'/agents/{agent_name}_arn'
            )
            agent_arn = agent_arn_response['Parameter']['Value']
            
            # Skip authentication for development - since LangGraph is working with 200 OK
            bearer_token = ""
            logger.info(f"Using no-auth mode for {agent_name}")
            
            credentials = {
                'agent_arn': agent_arn,
                'bearer_token': bearer_token
            }
            
            # Cache for performance
            self._cached_credentials[agent_name] = credentials
            return credentials
            
        except Exception as e:
            logger.error(f"Failed to get credentials for agent {agent_name}: {e}")
            raise
    
    def _generate_temporary_token(self) -> str:
        """Generate temporary token using AWS credentials"""
        # For now, return empty string - in production, implement proper JWT generation
        logger.warning("Using empty bearer token - implement proper JWT generation for production")
        return ""
    
    async def invoke_agent_tool(self, agent_name: str, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        Invoke a specific tool on another agent via MCP using direct HTTP with correct headers
        
        Args:
            agent_name: Name of the target agent
            tool_name: Name of the tool to invoke
            **kwargs: Tool parameters
            
        Returns:
            Tool execution result
        """
        try:
            logger.info(f"🔄 Invoking {tool_name} on {agent_name} via MCP (Fixed Headers)...")
            
            # Get agent ARN
            credentials = await self.get_agent_credentials(agent_name)
            agent_arn = credentials['agent_arn']
            
            # Build MCP URL
            encoded_arn = agent_arn.replace(':', '%3A').replace('/', '%2F')
            mcp_url = f"https://bedrock-agentcore.{self.region}.amazonaws.com/runtimes/{encoded_arn}/invocations?qualifier=DEFAULT"
            
            # Create MCP request payload
            mcp_payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call", 
                "params": {
                    "name": tool_name,
                    "arguments": kwargs
                }
            }
            
            # KEY FIX: Use requests with AWS SigV4 + correct MCP headers
            import requests
            from botocore.auth import SigV4Auth
            from botocore.awsrequest import AWSRequest
            from botocore.session import Session as BotoSession
            
            # Create AWS request with correct headers
            headers = {
                "Content-Type": "application/json",  # MCP requirement
                "Accept": "application/json, text/event-stream"  # MCP requirement: both types
            }
            
            # Prepare request
            request = AWSRequest(
                method='POST',
                url=mcp_url,
                data=json.dumps(mcp_payload),
                headers=headers
            )
            
            # Sign with SigV4
            boto_session = BotoSession()
            credentials = boto_session.get_credentials()
            SigV4Auth(credentials, 'bedrock-agentcore', self.region).add_auth(request)
            
            # Make signed request
            prepped = request.prepare()
            response = requests.post(
                prepped.url,
                headers=dict(prepped.headers),
                data=prepped.body,
                timeout=self.timeout
            )
            
            # Handle response
            if response.status_code == 200:
                result_content = response.text
                try:
                    mcp_response = json.loads(result_content)
                    if 'result' in mcp_response:
                        logger.info(f"✅ Successfully invoked {tool_name} on {agent_name}")
                        return {
                            "result": mcp_response['result'],
                            "tool_name": tool_name,
                            "agent_name": agent_name,
                            "status": "success"
                        }
                    else:
                        logger.info(f"✅ Raw MCP response from {tool_name}")
                        return {
                            "result": mcp_response,
                            "tool_name": tool_name,
                            "agent_name": agent_name,
                            "status": "success"
                        }
                except json.JSONDecodeError:
                    logger.info(f"✅ Raw response from {tool_name}")
                    return {
                        "result": result_content,
                        "tool_name": tool_name,
                        "agent_name": agent_name,
                        "status": "success"
                    }
            else:
                logger.error(f"HTTP {response.status_code}: {response.text[:200]}")
                return {
                    "error": f"HTTP {response.status_code}: {response.text[:200]}",
                    "tool_name": tool_name,
                    "agent_name": agent_name,
                    "status": "failed"
                }
                    
        except Exception as e:
            error_msg = f"Failed to invoke {tool_name} on {agent_name}: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg, "agent_name": agent_name, "tool_name": tool_name}
    
    async def list_agent_tools(self, agent_name: str) -> List[Dict[str, Any]]:
        """
        List available tools on an agent via MCP
        
        Args:
            agent_name: Name of the target agent
            
        Returns:
            List of available tools with their descriptions
        """
        try:
            logger.info(f"🔍 Listing tools for {agent_name} via MCP...")
            
            credentials = await self.get_agent_credentials(agent_name)
            agent_arn = credentials['agent_arn']
            bearer_token = credentials['bearer_token']
            
            encoded_arn = agent_arn.replace(':', '%3A').replace('/', '%2F')
            mcp_url = f"https://bedrock-agentcore.{self.region}.amazonaws.com/runtimes/{encoded_arn}/invocations?qualifier=DEFAULT"
            
            headers = {"Content-Type": "application/json"}
            # Skip authorization header - using no-auth deployment mode
            
            async with streamablehttp_client(
                mcp_url, 
                headers, 
                timeout=timedelta(seconds=self.timeout),
                terminate_on_close=False
            ) as (read_stream, write_stream, _):
                
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    
                    # List tools
                    tool_result = await session.list_tools()
                    
                    tools = []
                    for tool in tool_result.tools:
                        tools.append({
                            "name": tool.name,
                            "description": tool.description,
                            "input_schema": getattr(tool, 'inputSchema', {})
                        })
                    
                    logger.info(f"✅ Found {len(tools)} tools on {agent_name}")
                    return tools
                    
        except Exception as e:
            error_msg = f"Failed to list tools for {agent_name}: {str(e)}"
            logger.error(error_msg)
            return [{"error": error_msg}]
    
    async def health_check_agent(self, agent_name: str) -> Dict[str, Any]:
        """
        Perform health check on an agent via MCP
        
        Args:
            agent_name: Name of the target agent
            
        Returns:
            Health check result
        """
        try:
            return await self.invoke_agent_tool(agent_name, "health_check")
        except Exception as e:
            return {
                "error": f"Health check failed for {agent_name}: {str(e)}",
                "status": "unhealthy"
            }


# Convenience functions for common operations
async def call_langgraph_agent(prompt: str, image_path: str = None, region: str = "us-west-2") -> Dict[str, Any]:
    """
    Convenience function to call LangGraph kitchen analysis agent
    
    Args:
        prompt: Analysis request prompt
        image_path: Optional path to kitchen image
        region: AWS region
        
    Returns:
        Kitchen analysis results
    """
    client = AgentCoreMCPClient(region=region)
    return await client.invoke_agent_tool(
        "langgraph_agent", 
        "analyze_kitchen", 
        prompt=prompt, 
        image_path=image_path
    )


async def call_crewai_agent(materials_data: List[Dict], cost_grade: str = "standard", region: str = "us-west-2") -> Dict[str, Any]:
    """
    Convenience function to call CrewAI cost estimation agent
    
    Args:
        materials_data: List of materials with area information
        cost_grade: Cost grade (economy, standard, premium)
        region: AWS region
        
    Returns:
        Cost estimation results
    """
    client = AgentCoreMCPClient(region=region)
    return await client.invoke_agent_tool(
        "crewai_agent", 
        "estimate_renovation_costs", 
        materials_data=materials_data, 
        cost_grade=cost_grade
    )


async def discover_available_agents(region: str = "us-west-2") -> Dict[str, List[Dict[str, Any]]]:
    """
    Discover all available agents and their tools in the system
    
    Args:
        region: AWS region
        
    Returns:
        Dictionary mapping agent names to their available tools
    """
    client = AgentCoreMCPClient(region=region)
    
    # Common agent names in the system
    agent_names = ["langgraph_agent", "crewai_agent", "orchestrator_agent"]
    
    agents_info = {}
    for agent_name in agent_names:
        try:
            tools = await client.list_agent_tools(agent_name)
            agents_info[agent_name] = tools
        except Exception as e:
            logger.warning(f"Could not discover tools for {agent_name}: {e}")
            agents_info[agent_name] = [{"error": str(e)}]
    
    return agents_info


# Example usage:
"""
# In your MCP server code:
import asyncio
from mcp_base.mcp_client_utils import call_langgraph_agent, call_crewai_agent

async def orchestrate_kitchen_analysis():
    # Call LangGraph for kitchen analysis
    analysis_result = await call_langgraph_agent(
        "Analyze kitchen for renovation planning",
        image_path="/path/to/image.jpg"
    )
    
    # Extract materials from analysis
    materials = analysis_result.get('data', {}).get('materials', [])
    
    # Call CrewAI for cost estimation
    cost_result = await call_crewai_agent(materials, "standard")
    
    return {
        "analysis": analysis_result,
        "costs": cost_result
    }

# Run the orchestration
result = asyncio.run(orchestrate_kitchen_analysis())
"""
