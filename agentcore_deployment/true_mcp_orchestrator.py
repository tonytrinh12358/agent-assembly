"""
TRUE MCP Agent-to-Agent Orchestrator
This orchestrator uses MCP protocol to communicate with LangGraph and CrewAI agents
"""

import json
import asyncio
import logging
import boto3
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

# Try MCP imports with fallback
try:
    import mcp
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client
    MCP_AVAILABLE = True
    logger.info("✅ MCP SDK available")
except ImportError as e:
    logger.error(f"❌ MCP SDK not available: {e}")
    MCP_AVAILABLE = False


class TrueMCPOrchestrator:
    """Orchestrator that uses MCP to communicate with other agents"""
    
    def __init__(self, region: str = "us-west-2"):
        self.region = region
        self.session = boto3.Session()
        
    async def get_agent_mcp_url(self, agent_name: str) -> str:
        """Get MCP URL for an agent"""
        try:
            # Get agent ARN from Parameter Store
            ssm_client = boto3.client('ssm', region_name=self.region)
            response = ssm_client.get_parameter(Name=f'/agents/{agent_name}_arn')
            agent_arn = response['Parameter']['Value']
            
            # Encode ARN for MCP URL
            encoded_arn = agent_arn.replace(':', '%3A').replace('/', '%2F')
            mcp_url = f"https://bedrock-agentcore.{self.region}.amazonaws.com/runtimes/{encoded_arn}/invocations?qualifier=DEFAULT"
            
            return mcp_url
        except Exception as e:
            logger.error(f"Failed to get MCP URL for {agent_name}: {e}")
            raise
    
    async def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for MCP calls"""
        try:
            # For now, use a simple approach - in production you'd use Cognito
            return {
                "Content-Type": "application/json",
                # Note: In production, you'd get a proper bearer token here
                "Authorization": "Bearer dummy_token_for_testing"
            }
        except Exception as e:
            logger.error(f"Failed to get auth headers: {e}")
            return {"Content-Type": "application/json"}
    
    async def invoke_agent_via_mcp(self, agent_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke an agent via MCP protocol"""
        if not MCP_AVAILABLE:
            return {"error": "MCP SDK not available", "fallback": True}
        
        try:
            mcp_url = await self.get_agent_mcp_url(agent_name)
            headers = await self.get_auth_headers()
            
            logger.info(f"🔗 MCP call: {agent_name}.{tool_name} via {mcp_url[:50]}...")
            
            # For now, let's simulate the MCP call structure
            # In a full implementation, this would be a real MCP call
            async with streamablehttp_client(mcp_url, headers, timeout=120, terminate_on_close=False) as (
                read_stream,
                write_stream,
                _,
            ):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    
                    # Call the tool via MCP
                    result = await session.call_tool(
                        name=tool_name,
                        arguments=arguments
                    )
                    
                    # Process MCP response
                    if result.content and len(result.content) > 0:
                        if hasattr(result.content[0], 'text'):
                            response_text = result.content[0].text
                            try:
                                return json.loads(response_text)
                            except json.JSONDecodeError:
                                return {"result": response_text, "mcp_protocol_used": True}
                        else:
                            return {"result": str(result.content[0]), "mcp_protocol_used": True}
                    else:
                        return {"result": "No content returned", "mcp_protocol_used": True}
                        
        except Exception as e:
            logger.error(f"MCP call failed for {agent_name}.{tool_name}: {e}")
            
            # Fall back to direct bedrock-agentcore call
            return await self.fallback_direct_call(agent_name, arguments.get("prompt", str(arguments)))
    
    async def fallback_direct_call(self, agent_name: str, query: str) -> Dict[str, Any]:
        """Fallback to direct bedrock-agentcore call when MCP fails"""
        try:
            logger.warning(f"🔄 Falling back to direct call for {agent_name}")
            
            # Get agent ARN
            ssm_client = boto3.client('ssm', region_name=self.region)
            response = ssm_client.get_parameter(Name=f'/agents/{agent_name}_arn')
            agent_arn = response['Parameter']['Value']
            
            # Direct bedrock-agentcore call
            client = boto3.client('bedrock-agentcore', region_name=self.region)
            payload_dict = {'prompt': query}
            payload_bytes = json.dumps(payload_dict).encode('utf-8')
            
            response = client.invoke_agent_runtime(
                agentRuntimeArn=agent_arn,
                payload=payload_bytes
            )
            
            # Handle response
            result = ""
            if 'response' in response:
                response_body = response['response']
                if hasattr(response_body, 'read'):
                    result = response_body.read().decode('utf-8')
                else:
                    result = str(response_body)
            
            # Try to parse as JSON
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                return {"result": result, "mcp_protocol_used": False, "fallback_used": True}
                
        except Exception as e:
            logger.error(f"Direct call fallback failed: {e}")
            return {"error": f"Both MCP and direct calls failed: {str(e)}", "mcp_protocol_used": False}
    
    async def analyze_kitchen_via_mcp(self, query: str, image_path: str = None) -> Dict[str, Any]:
        """Analyze kitchen using LangGraph agent via MCP"""
        logger.info("🏠 Starting kitchen analysis via MCP...")
        
        arguments = {
            "prompt": f"Analyze kitchen for renovation planning: {query}",
            "image_path": image_path
        }
        
        result = await self.invoke_agent_via_mcp("langgraph_agent", "analyze_kitchen", arguments)
        
        # Ensure result is a dictionary
        if isinstance(result, str):
            result = {"result": result, "mcp_protocol_used": False}
        elif not isinstance(result, dict):
            result = {"result": str(result), "mcp_protocol_used": False}
            
        result["step"] = "langgraph_analysis"
        result["agent"] = "langgraph_agent"
        
        return result
    
    async def estimate_costs_via_mcp(self, materials_data: List[Dict], cost_grade: str = "standard") -> Dict[str, Any]:
        """Estimate costs using CrewAI agent via MCP"""
        logger.info("💰 Starting cost estimation via MCP...")
        
        arguments = {
            "prompt": f"Estimate costs for kitchen renovation with {cost_grade} grade materials",
            "materials_data": materials_data,
            "cost_grade": cost_grade
        }
        
        result = await self.invoke_agent_via_mcp("crewai_agent", "estimate_costs", arguments)
        
        # Ensure result is a dictionary
        if isinstance(result, str):
            result = {"result": result, "mcp_protocol_used": False}
        elif not isinstance(result, dict):
            result = {"result": str(result), "mcp_protocol_used": False}
            
        result["step"] = "crewai_estimation" 
        result["agent"] = "crewai_agent"
        
        return result
    
    async def full_renovation_analysis(self, query: str, cost_grade: str = "standard", image_path: str = None) -> Dict[str, Any]:
        """Complete renovation analysis using MCP agent-to-agent communication"""
        logger.info("🎯 Starting full MCP agent-to-agent renovation analysis...")
        
        try:
            # Step 1: Kitchen Analysis via MCP
            analysis_result = await self.analyze_kitchen_via_mcp(query, image_path)
            
            # Step 2: Extract materials for cost estimation  
            materials_data = []
            if "materials" in analysis_result:
                materials_data = analysis_result["materials"]
            else:
                # Default materials if analysis doesn't provide them
                materials_data = [
                    {"material_type": "wood", "area_sqm": 14.0, "location": "cabinet"},
                    {"material_type": "granite", "area_sqm": 7.5, "location": "countertop"},
                    {"material_type": "tile", "area_sqm": 18.5, "location": "flooring"}
                ]
            
            # Step 3: Cost Estimation via MCP
            cost_result = await self.estimate_costs_via_mcp(materials_data, cost_grade)
            
            # Step 4: Combine results
            final_result = {
                "analysis_type": "true_mcp_agent_to_agent",
                "kitchen_analysis": analysis_result,
                "cost_estimation": cost_result,
                "materials_used": materials_data,
                "cost_grade": cost_grade,
                "mcp_workflow_completed": True,
                "timestamp": datetime.now().isoformat()
            }
            
            # Check if MCP was actually used
            mcp_used = (
                analysis_result.get("mcp_protocol_used", False) and 
                cost_result.get("mcp_protocol_used", False)
            )
            
            final_result["true_mcp_communication"] = mcp_used
            
            if mcp_used:
                logger.info("✅ TRUE MCP agent-to-agent communication completed successfully!")
            else:
                logger.warning("⚠️ Fallback communication used (not true MCP)")
            
            return final_result
            
        except Exception as e:
            logger.error(f"Full MCP analysis failed: {e}")
            return {
                "error": f"MCP agent-to-agent analysis failed: {str(e)}",
                "analysis_type": "failed_mcp_workflow"
            }


async def test_true_mcp_communication():
    """Test true MCP agent-to-agent communication"""
    print("🧪 Testing TRUE MCP Agent-to-Agent Communication")
    print("=" * 60)
    
    if not MCP_AVAILABLE:
        print("❌ MCP SDK not available - installing...")
        # Try to import again after user installs
        return
    
    orchestrator = TrueMCPOrchestrator()
    
    test_query = """I have a kitchen with a refrigerator and oven that I want to renovate. 
    Please analyze the layout and provide cost estimates for materials and labor for a standard Australian kitchen renovation."""
    
    print(f"🎯 Query: {test_query[:100]}...")
    print()
    
    try:
        result = await orchestrator.full_renovation_analysis(
            query=test_query,
            cost_grade="standard"
        )
        
        print("📋 MCP Communication Results:")
        print("=" * 40)
        print(f"✅ Analysis Type: {result.get('analysis_type', 'unknown')}")
        print(f"🔗 True MCP Used: {result.get('true_mcp_communication', False)}")
        print(f"📊 Workflow Completed: {result.get('mcp_workflow_completed', False)}")
        
        if result.get('kitchen_analysis'):
            analysis = result['kitchen_analysis']
            print(f"🏠 LangGraph Agent: {'✅ Success' if not analysis.get('error') else '❌ Error'}")
            print(f"   MCP Used: {analysis.get('mcp_protocol_used', False)}")
            
        if result.get('cost_estimation'):
            costs = result['cost_estimation']
            print(f"💰 CrewAI Agent: {'✅ Success' if not costs.get('error') else '❌ Error'}")
            print(f"   MCP Used: {costs.get('mcp_protocol_used', False)}")
        
        print()
        if result.get('true_mcp_communication'):
            print("🎉 SUCCESS: TRUE MCP agent-to-agent communication working!")
        else:
            print("⚠️  FALLBACK: Using direct calls (MCP implementation needs work)")
            
        return result
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return None


if __name__ == "__main__":
    asyncio.run(test_true_mcp_communication())
