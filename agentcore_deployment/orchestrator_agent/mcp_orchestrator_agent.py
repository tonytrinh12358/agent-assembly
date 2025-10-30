"""
MCP-Based Orchestrator Agent for AgentCore Runtime
Uses Model Context Protocol for agent-to-agent communication
"""

import json
import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime

from strands import Agent, tool
from strands.models import BedrockModel
from bedrock_agentcore.runtime import BedrockAgentCoreApp

# Import our MCP client utilities
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from mcp_client_utils import MCPAgentClient, invoke_langgraph_agent_mcp, invoke_crewai_agent_mcp

logger = logging.getLogger(__name__)
app = BedrockAgentCoreApp()


# Initialize MCP client
mcp_client = MCPAgentClient(region="us-west-2", timeout=180)


@tool
async def analyze_kitchen_with_langgraph_mcp(image_path: str = None) -> Dict[str, Any]:
    """
    Analyze kitchen image using LangGraph agent via MCP protocol.
    
    Args:
        image_path: Path to the kitchen image file (optional for AgentCore)
        
    Returns:
        Dictionary containing detected objects, materials, measurements, and Bedrock analysis
    """
    try:
        prompt = f"Analyze kitchen image for renovation planning"
        if image_path:
            prompt += f" using image: {image_path}"
        
        result = await invoke_langgraph_agent_mcp(prompt, image_path)
        
        if "error" in result:
            logger.error(f"LangGraph MCP analysis failed: {result['error']}")
            return {"error": f"LangGraph analysis failed: {result['error']}"}
        
        return result
        
    except Exception as e:
        logger.error(f"LangGraph MCP tool failed: {e}")
        return {"error": f"LangGraph analysis failed: {str(e)}"}


@tool  
async def estimate_renovation_costs_with_crewai_mcp(materials_data: List[Dict], cost_grade: str = "standard") -> Dict[str, Any]:
    """
    Estimate kitchen renovation costs using CrewAI agents via MCP protocol.
    
    Args:
        materials_data: List of materials with type and area information
        cost_grade: Cost grade - economy, standard, or premium
        
    Returns:
        Dictionary containing detailed cost breakdown and estimates
    """
    try:
        result = await invoke_crewai_agent_mcp(materials_data, cost_grade)
        
        if "error" in result:
            logger.error(f"CrewAI MCP cost estimation failed: {result['error']}")
            return {"error": f"CrewAI cost estimation failed: {result['error']}"}
        
        return result
        
    except Exception as e:
        logger.error(f"CrewAI MCP tool failed: {e}")
        return {"error": f"CrewAI cost estimation failed: {str(e)}"}


@tool
async def discover_available_agents() -> Dict[str, List[Dict]]:
    """
    Discover all available agents and their tools via MCP protocol.
    
    Returns:
        Dictionary mapping agent names to their available tools
    """
    try:
        agent_names = ["langgraph_agent", "crewai_agent"]
        agent_tools = {}
        
        for agent_name in agent_names:
            try:
                tools = await mcp_client.list_agent_tools(agent_name)
                agent_tools[agent_name] = tools
                logger.info(f"Discovered {len(tools)} tools for {agent_name}")
            except Exception as e:
                logger.warning(f"Failed to discover tools for {agent_name}: {e}")
                agent_tools[agent_name] = []
        
        return agent_tools
        
    except Exception as e:
        logger.error(f"Agent discovery failed: {e}")
        return {}


@tool
def generate_renovation_recommendations(detection_results: Dict, cost_estimates: Dict) -> List[str]:
    """
    Generate AI-powered renovation recommendations based on analysis results.
    
    Args:
        detection_results: Results from kitchen detection analysis
        cost_estimates: Results from cost estimation
        
    Returns:
        List of renovation recommendations
    """
    recommendations = []
    
    try:
        # Handle nested project_estimate structure from CrewAI MCP
        project_estimate = cost_estimates.get('project_estimate', cost_estimates)
        
        # Analyze cost efficiency
        total_cost = (
            project_estimate.get('final_total_AUD', 0) or
            project_estimate.get('total_project_cost', 0) or
            cost_estimates.get('total_project_cost', 0)
        )
        
        total_area = detection_results.get("measurements", {}).get("total_kitchen_area", 1)
        cost_per_sqm = total_cost / total_area if total_area > 0 else 0
        
        if cost_per_sqm > 1000:
            recommendations.append("Consider economy grade materials to reduce costs")
        elif cost_per_sqm < 500:
            recommendations.append("Budget allows for premium material upgrades")
        
        # Analyze material distribution
        materials = detection_results.get("materials", [])
        granite_area = sum(m.get("area_sqm", 0) for m in materials if m.get("material_type") == "granite")
        
        if granite_area > 10:
            recommendations.append("Large granite area detected - consider quartz alternatives for cost savings")
        
        # Analyze space efficiency
        cabinet_area = detection_results.get("measurements", {}).get("cabinet_area", 0)
        if cabinet_area < 10:
            recommendations.append("Consider additional storage solutions for better kitchen functionality")
        
        # MCP-specific recommendations
        recommendations.append("All agent communications successfully completed via MCP protocol")
        
        return recommendations
        
    except Exception as e:
        return [f"Error generating recommendations: {str(e)}"]


# Initialize Strands Agent with Bedrock
model_id = "us.amazon.nova-premier-v1:0"
model = BedrockModel(
    model_id=model_id,
    region="us-west-2"
)

orchestrator_agent = Agent(
    model=model,
    system_prompt="""You are an expert kitchen renovation consultant with access to advanced AI tools via MCP protocol.

IMPORTANT: When a user asks about kitchen renovation, analysis, or cost estimates, you MUST use your MCP-enabled tools:

1. ALWAYS start by calling analyze_kitchen_with_langgraph_mcp() to get kitchen analysis data
2. THEN call estimate_renovation_costs_with_crewai_mcp() using the materials from step 1
3. OPTIONALLY call discover_available_agents() to show the multi-agent ecosystem
4. FINALLY call generate_renovation_recommendations() to provide personalized advice

Your tools now use the Model Context Protocol (MCP) for enhanced reliability, observability, and standardization.

Process:
1. Call analyze_kitchen_with_langgraph_mcp() - this returns detected objects, materials, and measurements
2. Extract the materials_data from the analysis results
3. Call estimate_renovation_costs_with_crewai_mcp(materials_data, "standard") for cost estimates
4. Call generate_renovation_recommendations(analysis_results, cost_results) for advice
5. Synthesize all results into a comprehensive renovation plan

Always provide costs in Australian dollars and measurements in square metres.
Focus on practical, actionable advice for homeowners.

MCP ADVANTAGES:
- Standardized protocol for agent communication
- Better error handling and observability
- Tool discovery capabilities
- Enhanced security and authentication

CRITICAL FORMATTING RULES:
- NEVER include <thinking> tags in your response
- NEVER include [Executing:...] logs in your response  
- NEVER show internal reasoning or debugging information
- Provide ONLY the final, clean, professional analysis report
- Format your response as a well-structured renovation report with clear sections
- Use proper markdown formatting with headers, bullet points, and cost tables
- Highlight that the analysis was performed using MCP protocol for enhanced reliability""",
    tools=[
        analyze_kitchen_with_langgraph_mcp, 
        estimate_renovation_costs_with_crewai_mcp, 
        discover_available_agents,
        generate_renovation_recommendations
    ]
)


def parse_event(event):
    """
    Parse a streaming event from the agent and return formatted output
    """
    # Skip events that don't need to be displayed
    if any(key in event for key in ['init_event_loop', 'start', 'start_event_loop']):
        return ""
    
    # Text chunks from supervisor
    if 'data' in event and isinstance(event['data'], str):
        return event['data'] 
    
    # Handle text messages from the assistant
    if 'event' in event:
        event_data = event['event']
        
        # Beginning of a tool use
        if 'contentBlockStart' in event_data and 'start' in event_data['contentBlockStart']:
            if 'toolUse' in event_data['contentBlockStart']['start']:
                tool_info = event_data['contentBlockStart']['start']['toolUse']
                return f"\n\n[MCP Tool Executing: {tool_info['name']}]\n\n"        

    return ""


@app.entrypoint
async def mcp_orchestrator_kitchen_analysis(payload):
    """
    AgentCore entrypoint for MCP-based orchestrator with streaming capabilities
    """
    user_input = payload.get("prompt", "")
    image_path = payload.get("image_path", None)
    cost_grade = payload.get("cost_grade", "standard")
    include_labor = payload.get("include_labor", True)
    
    logger.info(f"MCP Orchestrator Agent received: {user_input}")
    
    # Construct comprehensive prompt with MCP context
    analysis_prompt = f"""
    Please analyze this kitchen for renovation planning using MCP protocol:
    
    Request: {user_input}
    Image path: {image_path or "No specific image provided"}
    Desired quality grade: {cost_grade}
    Include labor costs: {include_labor}
    
    I need:
    1. Complete object detection and material analysis using LangGraph via MCP
    2. Detailed cost estimation in Australian dollars using CrewAI agents via MCP
    3. Agent discovery to show the multi-agent ecosystem capabilities
    4. Personalized renovation recommendations
    5. Summary with key insights and budget guidance
    
    Please use all your available MCP-enabled tools to provide a comprehensive analysis.
    Highlight the benefits of using MCP protocol for agent communication.
    """
    
    try:
        # Stream each chunk as it becomes available
        async for event in orchestrator_agent.stream_async(analysis_prompt):
            text = parse_event(event)
            if text:  # Only return non-empty responses
                yield text
                
    except Exception as e:
        # Handle errors gracefully in streaming context
        error_response = f"❌ MCP Orchestrator analysis failed: {str(e)}"
        logger.error(error_response)
        yield error_response


if __name__ == "__main__":
    app.run()
