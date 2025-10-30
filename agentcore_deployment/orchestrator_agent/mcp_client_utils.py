"""
MCP Client Utilities for Agent-to-Agent Communication
Uses Model Context Protocol to invoke other agents
"""

import asyncio
import boto3
import json
import logging
from typing import Dict, Any, List, Optional
from boto3.session import Session
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

logger = logging.getLogger(__name__)


class MCPAgentClient:
    """MCP client for invoking AgentCore agents using Model Context Protocol"""
    
    def __init__(self, region: str = "us-west-2", timeout: int = 120):
        self.region = region
        self.timeout = timeout
        self.session = Session()
        
    async def get_agent_credentials(self, agent_name: str) -> Dict[str, str]:
        """Retrieve agent ARN and authentication credentials"""
        try:
            # Get agent ARN from Parameter Store
            ssm_client = boto3.client('ssm', region_name=self.region)
            agent_arn_response = ssm_client.get_parameter(
                Name=f'/agents/{agent_name}_arn'
            )
            agent_arn = agent_arn_response['Parameter']['Value']
            
            # Get bearer token from Secrets Manager (if available)
            # For now, we'll use temporary credentials or fall back to direct invocation
            try:
                secrets_client = boto3.client('secretsmanager', region_name=self.region)
                response = secrets_client.get_secret_value(
                    SecretId=f'agents/{agent_name}/cognito_credentials'
                )
                secret_value = response['SecretString']
                parsed_secret = json.loads(secret_value)
                bearer_token = parsed_secret.get('bearer_token', '')
            except Exception:
                # Fall back to using AWS credentials for authentication
                bearer_token = self._generate_temporary_token()
            
            return {
                'agent_arn': agent_arn,
                'bearer_token': bearer_token
            }
            
        except Exception as e:
            logger.error(f"Failed to retrieve credentials for {agent_name}: {e}")
            raise
    
    def _generate_temporary_token(self) -> str:
        """Generate temporary bearer token using AWS STS (simplified approach)"""
        try:
            sts_client = boto3.client('sts', region_name=self.region)
            token_response = sts_client.get_session_token(DurationSeconds=3600)
            # For simplicity, we'll encode the credentials as a token
            # In production, this should use proper Cognito authentication
            credentials = token_response['Credentials']
            token_data = {
                'AccessKeyId': credentials['AccessKeyId'],
                'SecretAccessKey': credentials['SecretAccessKey'],
                'SessionToken': credentials['SessionToken']
            }
            return json.dumps(token_data)
        except Exception as e:
            logger.warning(f"Failed to generate temporary token: {e}")
            return ""
    
    async def invoke_agent_via_mcp(self, agent_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Invoke an agent's tool via MCP protocol
        
        Args:
            agent_name: Name of the target agent (e.g., 'langgraph_agent')
            tool_name: Name of the tool to invoke (e.g., 'analyze_kitchen')
            arguments: Arguments to pass to the tool
            
        Returns:
            Tool execution result
        """
        try:
            # Get agent credentials
            credentials = await self.get_agent_credentials(agent_name)
            agent_arn = credentials['agent_arn']
            bearer_token = credentials['bearer_token']
            
            # Construct MCP URL
            encoded_arn = agent_arn.replace(':', '%3A').replace('/', '%2F')
            mcp_url = f"https://bedrock-agentcore.{self.region}.amazonaws.com/runtimes/{encoded_arn}/invocations?qualifier=DEFAULT"
            
            headers = {
                "authorization": f"Bearer {bearer_token}",
                "Content-Type": "application/json"
            }
            
            logger.info(f"Invoking {agent_name}.{tool_name} via MCP: {mcp_url}")
            
            async with streamablehttp_client(mcp_url, headers, timeout=self.timeout, terminate_on_close=False) as (
                read_stream,
                write_stream,
                _,
            ):
                async with ClientSession(read_stream, write_stream) as session:
                    # Initialize MCP session
                    await session.initialize()
                    logger.debug(f"MCP session initialized for {agent_name}")
                    
                    # Call the tool
                    result = await session.call_tool(
                        name=tool_name,
                        arguments=arguments
                    )
                    
                    # Extract result content
                    if result.content and len(result.content) > 0:
                        if hasattr(result.content[0], 'text'):
                            response_text = result.content[0].text
                            try:
                                # Try to parse as JSON
                                return json.loads(response_text)
                            except json.JSONDecodeError:
                                # Return as plain text
                                return {"result": response_text}
                        else:
                            return {"result": str(result.content[0])}
                    else:
                        return {"result": "No content returned"}
                        
        except Exception as e:
            logger.error(f"MCP invocation failed for {agent_name}.{tool_name}: {e}")
            return {"error": f"MCP invocation failed: {str(e)}"}
    
    async def list_agent_tools(self, agent_name: str) -> List[Dict[str, Any]]:
        """List available tools for a specific agent"""
        try:
            credentials = await self.get_agent_credentials(agent_name)
            agent_arn = credentials['agent_arn']
            bearer_token = credentials['bearer_token']
            
            encoded_arn = agent_arn.replace(':', '%3A').replace('/', '%2F')
            mcp_url = f"https://bedrock-agentcore.{self.region}.amazonaws.com/runtimes/{encoded_arn}/invocations?qualifier=DEFAULT"
            
            headers = {
                "authorization": f"Bearer {bearer_token}",
                "Content-Type": "application/json"
            }
            
            async with streamablehttp_client(mcp_url, headers, timeout=self.timeout, terminate_on_close=False) as (
                read_stream,
                write_stream,
                _,
            ):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    
                    tool_result = await session.list_tools()
                    
                    tools = []
                    for tool in tool_result.tools:
                        tools.append({
                            'name': tool.name,
                            'description': tool.description,
                            'input_schema': getattr(tool, 'inputSchema', None)
                        })
                    
                    return tools
                    
        except Exception as e:
            logger.error(f"Failed to list tools for {agent_name}: {e}")
            return []


# Backward compatibility functions
async def invoke_langgraph_agent_mcp(query: str, image_path: Optional[str] = None) -> Dict[str, Any]:
    """Invoke LangGraph agent via MCP for kitchen analysis"""
    client = MCPAgentClient()
    arguments = {
        "prompt": f"Analyze kitchen for renovation planning: {query}",
        "image_path": image_path
    }
    return await client.invoke_agent_via_mcp("langgraph_agent", "analyze_kitchen", arguments)


async def invoke_crewai_agent_mcp(materials_data: List[Dict], cost_grade: str = "standard") -> Dict[str, Any]:
    """Invoke CrewAI agent via MCP for cost estimation"""
    client = MCPAgentClient()
    arguments = {
        "prompt": f"Estimate costs for kitchen renovation with {cost_grade} grade materials",
        "materials_data": materials_data,
        "cost_grade": cost_grade
    }
    return await client.invoke_agent_via_mcp("crewai_agent", "estimate_costs", arguments)


# Utility function for testing
async def test_mcp_agent_communication():
    """Test MCP communication with all agents"""
    client = MCPAgentClient()
    
    print("🧪 Testing MCP Agent Communication")
    print("=" * 60)
    
    # Test agents
    test_agents = ["langgraph_agent", "crewai_agent"]
    
    for agent_name in test_agents:
        try:
            print(f"\n🔍 Testing {agent_name}...")
            
            # List tools
            tools = await client.list_agent_tools(agent_name)
            print(f"  ✅ Found {len(tools)} tools:")
            for tool in tools:
                print(f"     🔧 {tool['name']}: {tool['description']}")
            
            # Test basic connectivity
            test_result = await client.invoke_agent_via_mcp(
                agent_name, 
                "ping" if "ping" in [t['name'] for t in tools] else tools[0]['name'] if tools else "default",
                {"test": True}
            )
            
            if "error" not in test_result:
                print(f"  ✅ {agent_name} communication successful!")
            else:
                print(f"  ⚠️  {agent_name} returned error: {test_result['error']}")
                
        except Exception as e:
            print(f"  ❌ {agent_name} communication failed: {e}")


if __name__ == "__main__":
    # Run test
    asyncio.run(test_mcp_agent_communication())
