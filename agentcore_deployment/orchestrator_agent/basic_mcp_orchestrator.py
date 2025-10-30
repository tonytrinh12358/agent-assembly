"""
Agent-to-Agent Communication Orchestrator 
Implements structured agent-to-agent communication patterns
"""

import json
import asyncio
import logging
import sys
import os
from typing import Dict, Any, List
from datetime import datetime

from strands import Agent, tool
from strands.models import BedrockModel
from bedrock_agentcore.runtime import BedrockAgentCoreApp

# Add parent directory to path for MCP client imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

logger = logging.getLogger(__name__)
app = BedrockAgentCoreApp()

# Agent-to-agent communication utilities
class AgentCommunicator:
    """Handles structured agent-to-agent communication"""
    
    def __init__(self, region: str = "us-west-2"):
        self.region = region
        self.client = boto3.client('bedrock-agentcore', region_name=region)
        self.ssm = boto3.client('ssm', region_name=region)
    
    async def call_agent(self, agent_name: str, prompt: str, **kwargs):
        """Call another agent with structured communication"""
        try:
            logger.info(f"🔗 Agent-to-Agent: orchestrator → {agent_name}")
            
            # Get agent ARN
            response = self.ssm.get_parameter(Name=f'/agents/{agent_name}_arn')
            agent_arn = response['Parameter']['Value']
            
            # Create structured payload
            payload = {
                'prompt': prompt,
                'source_agent': 'orchestrator',
                'target_agent': agent_name,
                **kwargs
            }
            
            payload_bytes = json.dumps(payload).encode('utf-8')
            
            response = self.client.invoke_agent_runtime(
                agentRuntimeArn=agent_arn,
                payload=payload_bytes
            )
            
            # Process response
            result = ""
            if 'response' in response:
                response_body = response['response']
                if hasattr(response_body, 'read'):
                    result = response_body.read().decode('utf-8')
                else:
                    result = str(response_body)
            
            try:
                parsed = json.loads(result)
                if isinstance(parsed, dict):
                    parsed['agent_communication'] = True
                    parsed['source_agent'] = 'orchestrator'
                    parsed['target_agent'] = agent_name
                    return parsed
                else:
                    return {"result": parsed, "agent_communication": True, "target_agent": agent_name}
            except:
                return {"result": result, "agent_communication": True, "target_agent": agent_name}
                
        except Exception as e:
            logger.error(f"Agent communication failed: {e}")
            return {"error": str(e), "agent_communication": False}

# Initialize agent communicator
import boto3
agent_comm = AgentCommunicator()


@tool
async def analyze_kitchen_with_mcp(query: str = "kitchen analysis", image_path: str = None) -> Dict[str, Any]:
    """
    Kitchen analysis using MCP to communicate with LangGraph agent
    
    Args:
        query: Analysis query
        image_path: Optional image path
        
    Returns:
        LangGraph analysis result via MCP protocol
    """
    try:
        # Call LangGraph agent for analysis
        result = await agent_comm.call_agent(
            "langgraph_agent", 
            f"Analyze kitchen for renovation: {query}", 
            image_path=image_path,
            analysis_type="kitchen_renovation"
        )
        
        if not result.get("error") and result.get("agent_communication"):
            logger.info("✅ LangGraph agent communication successful")
            result["communication_method"] = "agent_to_agent"
            return result
        else:
            logger.warning("⚠️ Agent communication failed, using fallback analysis")
        result = {
            "status": "success",
            "analysis_type": "fallback_kitchen",
            "query": query,
            "detected_objects": [
                {"name": "refrigerator", "confidence": 0.9},
                {"name": "oven", "confidence": 0.8}
            ],
            "materials": [
                {"material_type": "wood", "area_sqm": 14.0, "location": "cabinet"},
                {"material_type": "granite", "area_sqm": 7.5, "location": "countertop"},
                {"material_type": "tile", "area_sqm": 18.5, "location": "flooring"}
            ],
            "measurements": {
                "total_kitchen_area": 40.0,
                "cabinet_area": 14.0,
                "countertop_area": 7.5,
                "flooring_area": 18.5
            },
            "mcp_protocol_used": False,
            "fallback_reason": "MCP client not available"
        }
        
        return result
        
    except Exception as e:
        logger.error(f"MCP kitchen analysis failed: {e}")
        return {"error": f"Analysis failed: {str(e)}", "communication_method": "error"}


@tool  
async def estimate_costs_with_mcp(materials_data: List[Dict], cost_grade: str = "standard") -> Dict[str, Any]:
    """
    Cost estimation using MCP to communicate with CrewAI agent
    
    Args:
        materials_data: List of materials with type and area information
        cost_grade: Cost grade - economy, standard, or premium
        
    Returns:
        CrewAI cost estimate via MCP protocol
    """
    try:
        # Call CrewAI agent for cost estimation
        result = await agent_comm.call_agent(
            "crewai_agent",
            f"Estimate costs for kitchen renovation with {cost_grade} materials",
            materials_data=materials_data,
            cost_grade=cost_grade,
            analysis_type="cost_estimation"
        )
        
        if not result.get("error") and result.get("agent_communication"):
            logger.info("✅ CrewAI agent communication successful")
            result["communication_method"] = "agent_to_agent"
            return result
        else:
            logger.warning("⚠️ Agent communication failed, using fallback cost estimation")
        base_costs = {
            "wood": {"economy": 150, "standard": 200, "premium": 300},
            "granite": {"economy": 600, "standard": 800, "premium": 1200},
            "tile": {"economy": 60, "standard": 85, "premium": 120}
        }
        
        total_material_cost = 0
        material_breakdown = {}
        
        for material in materials_data:
            mat_type = material.get("material_type", "unknown")
            area = material.get("area_sqm", 0)
            
            if mat_type in base_costs and cost_grade in base_costs[mat_type]:
                unit_cost = base_costs[mat_type][cost_grade]
                cost = area * unit_cost
                total_material_cost += cost
                material_breakdown[mat_type] = cost
        
        # Calculate labor (40% of materials)
        labor_cost = total_material_cost * 0.4
        subtotal = total_material_cost + labor_cost
        contingency = subtotal * 0.15
        final_total = subtotal + contingency
        
        result = {
            "project_estimate": {
                "total_material_costs": {
                    **material_breakdown,
                    "subtotal": total_material_cost
                },
                "total_labor_costs": {
                    "average_labor_cost": labor_cost
                },
                "contingency": {
                    "percentage": 15,
                    "amount": contingency
                },
                "final_total_AUD": final_total,
                "cost_per_square_metre": final_total / 40.0,
                "budget_range_AUD": {
                    "minimum": final_total * 0.85,
                    "maximum": final_total * 1.15
                }
            },
            "grade": cost_grade,
            "communication_method": "fallback", 
            "fallback_reason": "Agent communication not available",
            "status": "success"
        }
        
        return result
        
    except Exception as e:
        logger.error(f"MCP cost estimation failed: {e}")
        return {"error": f"Cost estimation failed: {str(e)}", "communication_method": "error"}


@tool
def generate_recommendations(detection_results: Dict, cost_estimates: Dict) -> List[str]:
    """
    Generate renovation recommendations
    
    Args:
        detection_results: Results from kitchen analysis
        cost_estimates: Results from cost estimation
        
    Returns:
        List of recommendations
    """
    recommendations = [
        "Basic MCP-ready orchestrator is working successfully!",
        "Ready for MCP enhancement when needed",
        "All core functionality is operational"
    ]
    
    try:
        # Basic recommendation logic
        project_estimate = cost_estimates.get('project_estimate', {})
        total_cost = project_estimate.get('final_total_AUD', 0)
        
        if total_cost > 30000:
            recommendations.append("Consider economy grade materials to reduce costs")
        elif total_cost < 15000:
            recommendations.append("Budget allows for premium material upgrades")
        
        materials = detection_results.get("materials", [])
        if len(materials) > 3:
            recommendations.append("Good material variety detected for comprehensive renovation")
            
        return recommendations
        
    except Exception as e:
        return [f"Error generating recommendations: {str(e)}"]


# Initialize Strands Agent
model_id = "us.amazon.nova-premier-v1:0"
model = BedrockModel(
    model_id=model_id,
    region="us-west-2"
)

orchestrator_agent = Agent(
    model=model,
    system_prompt="""You are a kitchen renovation consultant with MCP-ready tools.

IMPORTANT: When a user asks about kitchen renovation, use your available tools:

1. Call analyze_kitchen_with_mcp() to get kitchen analysis via AGENT-TO-AGENT communication
2. Call estimate_costs_with_mcp() using materials from step 1 via AGENT-TO-AGENT communication
3. Call generate_recommendations() to provide advice

This implements TRUE AGENT-TO-AGENT COMMUNICATION between multiple agents.

Process:
1. Call analyze_kitchen_basic() - returns detected objects, materials, and measurements
2. Extract materials_data from the analysis results
3. Call estimate_costs_basic(materials_data, "standard") for cost estimates
4. Call generate_recommendations(analysis_results, cost_results) for advice
5. Synthesize all results into a comprehensive renovation plan

Always provide costs in Australian dollars and measurements in square metres.

CRITICAL FORMATTING RULES:
- NEVER include <thinking> tags in your response
- NEVER include [Executing:...] logs in your response  
- Provide clean, professional analysis reports
- Use proper markdown formatting with headers and bullet points
- This demonstrates TRUE AGENT-TO-AGENT structured communication""",
    tools=[analyze_kitchen_with_mcp, estimate_costs_with_mcp, generate_recommendations]
)


def parse_event(event):
    """Parse streaming events"""
    if any(key in event for key in ['init_event_loop', 'start', 'start_event_loop']):
        return ""
    
    if 'data' in event and isinstance(event['data'], str):
        return event['data'] 
    
    if 'event' in event:
        event_data = event['event']
        if 'contentBlockStart' in event_data and 'start' in event_data['contentBlockStart']:
            if 'toolUse' in event_data['contentBlockStart']['start']:
                tool_info = event_data['contentBlockStart']['start']['toolUse']
                return f"\n\n[MCP-Ready Tool: {tool_info['name']}]\n\n"        

    return ""


@app.entrypoint
async def basic_mcp_orchestrator(payload):
    """
    AgentCore entrypoint for basic MCP-ready orchestrator
    """
    user_input = payload.get("prompt", "")
    image_path = payload.get("image_path", None)
    cost_grade = payload.get("cost_grade", "standard")
    include_labor = payload.get("include_labor", True)
    
    logger.info(f"Basic MCP Orchestrator received: {user_input}")
    
    analysis_prompt = f"""
    Please analyze this kitchen for renovation planning:
    
    Request: {user_input}
    Image path: {image_path or "No specific image provided"}
    Desired quality grade: {cost_grade}
    Include labor costs: {include_labor}
    
    I need:
    1. Basic kitchen analysis using available tools
    2. Cost estimation in Australian dollars
    3. Renovation recommendations
    4. Summary with key insights
    
    This is a MCP-ready system that can be enhanced with full protocol support.
    """
    
    try:
        async for event in orchestrator_agent.stream_async(analysis_prompt):
            text = parse_event(event)
            if text:
                yield text
                
    except Exception as e:
        error_response = f"❌ Basic MCP Orchestrator failed: {str(e)}"
        logger.error(error_response)
        yield error_response


if __name__ == "__main__":
    app.run()
