"""
Strands Orchestrator Agent for AgentCore Runtime
"""

import json
import boto3
import logging
from typing import Dict, Any, List
from datetime import datetime

from strands import Agent, tool
from strands.models import BedrockModel
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from invoke_agent_utils import invoke_agent_with_boto3, invoke_agent_with_materials_data

logger = logging.getLogger(__name__)
app = BedrockAgentCoreApp()


def get_agent_arn(agent_name: str) -> str:
    """
    Retrieve agent ARN from Parameter Store
    """
    try:
        ssm = boto3.client('ssm')
        response = ssm.get_parameter(
            Name=f'/agents/{agent_name}_arn'
        )
        return response['Parameter']['Value']
    except Exception as err:
        print(f"Error getting {agent_name} ARN: {err}")
        raise err


@tool
def analyze_kitchen_with_langgraph(image_path: str = None) -> Dict[str, Any]:
    """
    Analyze kitchen image using LangGraph agent with YOLO detection and Bedrock models.
    
    Args:
        image_path: Path to the kitchen image file (optional for AgentCore)
        
    Returns:
        Dictionary containing detected objects, materials, measurements, and Bedrock analysis
    """
    try:
        langgraph_agent_arn = get_agent_arn("langgraph_agent")
        
        prompt = f"Analyze kitchen image for renovation planning"
        if image_path:
            prompt += f" using image: {image_path}"
        
        result_json = invoke_agent_with_boto3(langgraph_agent_arn, prompt)
        
        # Parse JSON result
        result = json.loads(result_json)
        return result
        
    except Exception as e:
        return {"error": f"LangGraph analysis failed: {str(e)}"}


@tool  
def estimate_renovation_costs_with_crewai(materials_data: List[Dict], cost_grade: str = "standard") -> Dict[str, Any]:
    """
    Estimate kitchen renovation costs using CrewAI agents with Bedrock models.
    
    Args:
        materials_data: List of materials with type and area information
        cost_grade: Cost grade - economy, standard, or premium
        
    Returns:
        Dictionary containing detailed cost breakdown and estimates
    """
    try:
        crewai_agent_arn = get_agent_arn("crewai_agent")
        
        result_json = invoke_agent_with_materials_data(
            crewai_agent_arn, 
            materials_data, 
            cost_grade
        )
        
        # Parse JSON result
        result = json.loads(result_json)
        return result
        
    except Exception as e:
        return {"error": f"CrewAI cost estimation failed: {str(e)}"}


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
        # Analyze cost efficiency
        total_cost = cost_estimates.get("total_project_cost", 0)
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
    system_prompt="""You are an expert kitchen renovation consultant with access to advanced AI tools.

IMPORTANT: When a user asks about kitchen renovation, analysis, or cost estimates, you MUST use your tools:

1. ALWAYS start by calling analyze_kitchen_with_langgraph() to get kitchen analysis data
2. THEN call estimate_renovation_costs_with_crewai() using the materials from step 1
3. FINALLY call generate_renovation_recommendations() to provide personalized advice

Your tools work with mock data and don't require actual images. They will provide realistic analysis results.

Process:
1. Call analyze_kitchen_with_langgraph() - this returns detected objects, materials, and measurements
2. Extract the materials_data from the analysis results
3. Call estimate_renovation_costs_with_crewai(materials_data, "standard") for cost estimates
4. Call generate_renovation_recommendations(analysis_results, cost_results) for advice
5. Synthesize all results into a comprehensive renovation plan

Always provide costs in Australian dollars and measurements in square metres.
Focus on practical, actionable advice for homeowners.

CRITICAL FORMATTING RULES:
- NEVER include <thinking> tags in your response
- NEVER include [Executing:...] logs in your response  
- NEVER show internal reasoning or debugging information
- Provide ONLY the final, clean, professional analysis report
- Format your response as a well-structured renovation report with clear sections
- Use proper markdown formatting with headers, bullet points, and cost tables""",
    tools=[analyze_kitchen_with_langgraph, estimate_renovation_costs_with_crewai, generate_renovation_recommendations]
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
                return f"\n\n[Executing: {tool_info['name']}]\n\n"        

    return ""


@app.entrypoint
async def orchestrator_kitchen_analysis(payload):
    """
    AgentCore entrypoint for orchestrator with streaming capabilities
    """
    user_input = payload.get("prompt", "")
    image_path = payload.get("image_path", None)
    cost_grade = payload.get("cost_grade", "standard")
    include_labor = payload.get("include_labor", True)
    
    print(f"Orchestrator Agent received: {user_input}")
    
    # Construct comprehensive prompt
    analysis_prompt = f"""
    Please analyze this kitchen for renovation planning:
    
    Request: {user_input}
    Image path: {image_path or "No specific image provided"}
    Desired quality grade: {cost_grade}
    Include labor costs: {include_labor}
    
    I need:
    1. Complete object detection and material analysis using LangGraph
    2. Detailed cost estimation in Australian dollars using CrewAI agents
    3. Personalized renovation recommendations
    4. Summary with key insights and budget guidance
    
    Please use all your available tools to provide a comprehensive analysis.
    """
    
    try:
        # Stream each chunk as it becomes available
        async for event in orchestrator_agent.stream_async(analysis_prompt):
            text = parse_event(event)
            if text:  # Only return non-empty responses
                yield text
                
    except Exception as e:
        # Handle errors gracefully in streaming context
        error_response = f"❌ Orchestrator analysis failed: {str(e)}"
        print(error_response)
        yield error_response


if __name__ == "__main__":
    app.run()

