"""
Actual Strands Kitchen Analysis Agent with Bedrock Integration
Uses LangGraph and CrewAI agents as tools
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import json
import asyncio
from datetime import datetime

# Import actual strands framework
from strands import Agent, tool
from strands.models import BedrockModel

# Import our working agents
from langgraph_agent.kitchen_analyzer_cv import KitchenAnalyzerYOLO
from crewai_agent.cost_estimator import KitchenCostEstimator, MaterialGrade

# Initialize working agents as global instances
langgraph_agent = KitchenAnalyzerYOLO()
crewai_agent = KitchenCostEstimator()


class KitchenAnalysisRequest(BaseModel):
    image_path: str = Field(description="Path to kitchen image for analysis")
    cost_grade: str = Field(default="standard", description="Cost grade: economy, standard, or premium")
    include_labor: bool = Field(default=True, description="Include labor costs in estimation")


class KitchenAnalysisResult(BaseModel):
    detection_results: Dict[str, Any] = Field(description="LangGraph detection and material analysis results")
    cost_estimates: Dict[str, Any] = Field(description="CrewAI cost estimation results")
    summary: Dict[str, Any] = Field(description="Strands agent synthesized analysis")
    recommendations: List[str] = Field(description="AI-generated recommendations")
    timestamp: str = Field(description="Analysis timestamp")


# Initialize working agents as global instances
langgraph_agent = KitchenAnalyzerYOLO()
crewai_agent = KitchenCostEstimator()


@tool
def analyze_kitchen_with_yolo(image_path: str) -> Dict[str, Any]:
    """
    Analyze kitchen image using YOLO detection and LangGraph workflow with Bedrock models.
    
    Args:
        image_path: Path to the kitchen image file
        
    Returns:
        Dictionary containing detected objects, materials, measurements, and Bedrock analysis
    """
    try:
        result = langgraph_agent.analyze_kitchen(image_path)
        return result
    except Exception as e:
        return {"error": f"LangGraph analysis failed: {str(e)}"}


@tool  
def estimate_renovation_costs(materials_data: List[Dict], cost_grade: str = "standard") -> Dict[str, Any]:
    """
    Estimate kitchen renovation costs using CrewAI agents with Bedrock models.
    
    Args:
        materials_data: List of materials with type and area information
        cost_grade: Cost grade - economy, standard, or premium
        
    Returns:
        Dictionary containing detailed cost breakdown and estimates
    """
    try:
        grade = MaterialGrade(cost_grade.lower())
        result = crewai_agent.estimate_costs(materials_data, grade)
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


# Initialize Strands Agent with Bedrock
kitchen_agent = Agent(
    model=BedrockModel(
        model_id="us.amazon.nova-premier-v1:0",
        region="us-west-2"
    ),
    tools=[analyze_kitchen_with_yolo, estimate_renovation_costs, generate_renovation_recommendations],
    system_prompt="""You are an expert kitchen renovation consultant with access to advanced AI tools.
    
Your capabilities:
1. Analyze kitchen images using YOLO detection and LangGraph workflows
2. Estimate renovation costs using CrewAI multi-agent teams
3. Generate personalized renovation recommendations

When a user requests kitchen analysis:
1. Use analyze_kitchen_with_yolo to detect objects and materials
2. Use estimate_renovation_costs to get detailed cost breakdowns
3. Use generate_renovation_recommendations for personalized advice
4. Synthesize all results into a comprehensive renovation plan

Always provide costs in Australian dollars and measurements in square metres.
Focus on practical, actionable advice for homeowners."""
)


async def analyze_kitchen_comprehensive(request: KitchenAnalysisRequest) -> KitchenAnalysisResult:
    """
    Comprehensive kitchen analysis using Strands agent orchestration
    """
    
    user_message = f"""
    Please analyze this kitchen for renovation planning:
    
    Image: {request.image_path}
    Desired quality grade: {request.cost_grade}
    Include labor costs: {request.include_labor}
    
    I need:
    1. Complete object detection and material analysis
    2. Detailed cost estimation in Australian dollars
    3. Personalized renovation recommendations
    4. Summary with key insights and budget guidance
    
    Please use all your available tools to provide a comprehensive analysis.
    """
    
    # Get Strands agent response
    response = kitchen_agent(user_message)
    response_text = response.message['content'][0]['text']
    
    # Extract structured data from tool calls if available
    detection_results = {}
    cost_estimates = {}
    
    # Check if response contains tool call results
    if hasattr(response, 'tool_calls') and response.tool_calls:
        for tool_call in response.tool_calls:
            if tool_call.get('function', {}).get('name') == 'analyze_kitchen_with_yolo':
                detection_results = tool_call.get('result', {})
            elif tool_call.get('function', {}).get('name') == 'estimate_renovation_costs':
                cost_estimates = tool_call.get('result', {})
    
    # Try to extract JSON cost data from the response text as fallback
    import re
    json_matches = re.finditer(r'```json\s*([\s\S]*?)\s*```', response_text, re.IGNORECASE)
    for match in json_matches:
        try:
            json_data = json.loads(match.group(1))
            if 'cost_breakdown' in json_data:
                cost_estimates = json_data
                break
            elif 'final_project_total' in json_data:
                cost_estimates = {"cost_breakdown": json_data}
                break
        except json.JSONDecodeError:
            continue
    
    # If we still don't have cost estimates, try extracting from the full response text
    if not cost_estimates:
        # Look for the final output from CrewAI that appears in logs
        final_output_match = re.search(r'Final Output:\s*```json\s*([\s\S]*?)\s*```', response_text, re.IGNORECASE)
        if final_output_match:
            try:
                json_data = json.loads(final_output_match.group(1))
                if 'cost_breakdown' in json_data:
                    cost_estimates = json_data
                elif 'final_project_total' in json_data:
                    cost_estimates = {"cost_breakdown": json_data}
            except json.JSONDecodeError:
                pass
    
    # Embed structured cost data in the response text for UI parsing
    if cost_estimates:
        # Ensure the cost data is embedded in a format the UI can parse
        cost_json = json.dumps(cost_estimates, indent=2)
        if 'cost_breakdown' in cost_estimates:
            cb = cost_estimates['cost_breakdown']
            if 'final_project_total' in cb:
                response_text += f"\n\nCOST_DATA_JSON: ```json\n{cost_json}\n```"
    
    # Parse the response and structure the result
    return KitchenAnalysisResult(
        detection_results=detection_results or {"strands_analysis": "Completed via Strands agent"},
        cost_estimates=cost_estimates or {"strands_analysis": "Completed via Strands agent"},
        summary={"strands_response": response_text},
        recommendations=["Recommendations generated via Strands agent"],
        timestamp=datetime.now().isoformat()
    )


async def main():
    """Test the Strands kitchen analysis agent"""
    
    print("🏠 Strands Kitchen Analysis Agent")
    print("=" * 50)
    
    request = KitchenAnalysisRequest(
        image_path="/home/ubuntu/workspace/TechSummit_2025/sample_images/img_1.jpg",
        cost_grade="standard",
        include_labor=True
    )
    
    try:
        result = await analyze_kitchen_comprehensive(request)
        
        print("\n📋 Strands Agent Analysis Complete")
        print("=" * 50)
        print(f"Timestamp: {result.timestamp}")
        print(f"Response:\n{result.summary.get('strands_response', 'No response')}")
        
        # Save results
        with open('strands_kitchen_analysis.json', 'w') as f:
            json.dump(result.dict(), f, indent=2)
        
        print("\n💾 Results saved to strands_kitchen_analysis.json")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
