"""
Simple Strands-like Orchestrator using LangGraph and CrewAI agents as tools
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from langchain_aws import ChatBedrock
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from pydantic import BaseModel
from typing import Dict, Any, List
import json
import asyncio
from datetime import datetime

# Import our agents
from langgraph_agent.kitchen_analyzer_yolo import KitchenAnalyzerYOLO
from crewai_agent.cost_estimator import KitchenCostEstimator, MaterialGrade


class KitchenAnalysisRequest(BaseModel):
    image_path: str
    cost_grade: str = "standard"
    include_labor: bool = True


class KitchenAnalysisResult(BaseModel):
    detection_results: Dict[str, Any]
    cost_estimates: Dict[str, Any]
    summary: Dict[str, Any]
    recommendations: List[str]
    timestamp: str


# Initialize agents as global instances
langgraph_agent = KitchenAnalyzerYOLO()
crewai_agent = KitchenCostEstimator()


@tool
def analyze_kitchen_with_yolo(image_path: str) -> str:
    """
    Analyze kitchen image using YOLO detection and LangGraph workflow with Bedrock models.
    
    Args:
        image_path: Path to the kitchen image file
        
    Returns:
        JSON string containing detected objects, materials, measurements, and Bedrock analysis
    """
    try:
        result = langgraph_agent.analyze_kitchen(image_path)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": f"LangGraph analysis failed: {str(e)}"})


@tool  
def estimate_renovation_costs(materials_json: str, cost_grade: str = "standard") -> str:
    """
    Estimate kitchen renovation costs using CrewAI agents with Bedrock models.
    
    Args:
        materials_json: JSON string of materials with type and area information
        cost_grade: Cost grade - economy, standard, or premium
        
    Returns:
        JSON string containing detailed cost breakdown and estimates
    """
    try:
        materials_data = json.loads(materials_json)
        grade = MaterialGrade(cost_grade.lower())
        result = crewai_agent.estimate_costs(materials_data, grade)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": f"CrewAI cost estimation failed: {str(e)}"})


@tool
def generate_renovation_recommendations(detection_json: str, cost_json: str) -> str:
    """
    Generate AI-powered renovation recommendations based on analysis results.
    
    Args:
        detection_json: JSON string of detection results
        cost_json: JSON string of cost estimates
        
    Returns:
        JSON string of renovation recommendations
    """
    try:
        detection_data = json.loads(detection_json)
        cost_data = json.loads(cost_json)
        
        recommendations = []
        
        # Analyze cost efficiency
        total_cost = cost_data.get("total_project_cost", 0)
        total_area = detection_data.get("measurements", {}).get("total_kitchen_area", 1)
        cost_per_sqm = total_cost / total_area if total_area > 0 else 0
        
        if cost_per_sqm > 1000:
            recommendations.append("Consider economy grade materials to reduce costs")
        elif cost_per_sqm < 500:
            recommendations.append("Budget allows for premium material upgrades")
        
        # Analyze material distribution
        materials = detection_data.get("materials", [])
        granite_area = sum(m.get("area_sqm", 0) for m in materials if m.get("material_type") == "granite")
        
        if granite_area > 10:
            recommendations.append("Large granite area detected - consider quartz alternatives for cost savings")
        
        # Analyze space efficiency
        cabinet_area = detection_data.get("measurements", {}).get("cabinet_area", 0)
        if cabinet_area < 10:
            recommendations.append("Consider additional storage solutions for better kitchen functionality")
        
        return json.dumps({"recommendations": recommendations})
        
    except Exception as e:
        return json.dumps({"error": f"Recommendation generation failed: {str(e)}"})


class KitchenRenovationOrchestrator:
    def __init__(self, region: str = "us-west-2"):
        # Initialize Bedrock LLM
        self.llm = ChatBedrock(
            model_id="us.amazon.nova-premier-v1:0",
            region_name=region,
            model_kwargs={
                "max_tokens": 4000,
                "temperature": 0.1
            }
        )
        
        # Create tools and bind to LLM
        self.tools = [analyze_kitchen_with_yolo, estimate_renovation_costs, generate_renovation_recommendations]
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
        # Build the graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the orchestration workflow"""
        
        # System message
        system_message = """You are a comprehensive kitchen renovation orchestrator with access to advanced AI tools.
        
        Your capabilities:
        1. Analyze kitchen images using YOLO detection and LangGraph workflows
        2. Estimate renovation costs using CrewAI multi-agent teams
        3. Generate personalized renovation recommendations
        
        When a user requests kitchen analysis:
        1. Use analyze_kitchen_with_yolo to detect objects and materials
        2. Extract materials data and use estimate_renovation_costs for detailed cost breakdowns
        3. Use generate_renovation_recommendations for personalized advice
        4. Synthesize all results into a comprehensive renovation plan
        
        Always provide costs in Australian dollars and measurements in square metres.
        Focus on practical, actionable advice for homeowners."""
        
        # Define the chatbot node
        def chatbot(state: MessagesState):
            messages = state["messages"]
            if not messages or not isinstance(messages[0], SystemMessage):
                messages = [SystemMessage(content=system_message)] + messages
            
            response = self.llm_with_tools.invoke(messages)
            return {"messages": [response]}
        
        # Create the graph
        graph_builder = StateGraph(MessagesState)
        
        # Add nodes
        graph_builder.add_node("chatbot", chatbot)
        graph_builder.add_node("tools", ToolNode(self.tools))
        
        # Add edges
        graph_builder.add_conditional_edges(
            "chatbot",
            tools_condition,
        )
        graph_builder.add_edge("tools", "chatbot")
        
        # Set entry point
        graph_builder.set_entry_point("chatbot")
        
        return graph_builder.compile()
    
    async def analyze_kitchen_comprehensive(self, request: KitchenAnalysisRequest) -> KitchenAnalysisResult:
        """
        Comprehensive kitchen analysis using orchestrated agents
        """
        
        user_message = f"""
        Please analyze this kitchen for renovation planning:
        
        Image: {request.image_path}
        Desired quality grade: {request.cost_grade}
        Include labor costs: {request.include_labor}
        
        I need:
        1. Complete object detection and material analysis using YOLO and LangGraph
        2. Detailed cost estimation in Australian dollars using CrewAI agents
        3. Personalized renovation recommendations
        4. Summary with key insights and budget guidance
        
        Please use all your available tools to provide a comprehensive analysis.
        """
        
        # Get orchestrator response
        response = self.graph.invoke({
            "messages": [HumanMessage(content=user_message)]
        })
        
        # Extract the final message content
        final_message = response["messages"][-1].content
        
        return KitchenAnalysisResult(
            detection_results={"orchestrator_analysis": "Completed via multi-agent orchestration"},
            cost_estimates={"orchestrator_analysis": "Completed via multi-agent orchestration"},
            summary={"orchestrator_response": final_message},
            recommendations=["Recommendations generated via orchestrated agents"],
            timestamp=datetime.now().isoformat()
        )


async def main():
    """Test the kitchen renovation orchestrator"""
    
    print("🏠 Kitchen Renovation Orchestrator")
    print("=" * 60)
    
    orchestrator = KitchenRenovationOrchestrator()
    
    request = KitchenAnalysisRequest(
        image_path="/home/ubuntu/workspace/TechSummit_2025/sample_images/img_1.jpg",
        cost_grade="standard",
        include_labor=True
    )
    
    try:
        print("🚀 Starting comprehensive kitchen analysis...")
        result = await orchestrator.analyze_kitchen_comprehensive(request)
        
        print("\n📋 Orchestrated Analysis Complete")
        print("=" * 60)
        print(f"Timestamp: {result.timestamp}")
        print(f"\nOrchestrator Response:\n{result.summary.get('orchestrator_response', 'No response')}")
        
        # Save results
        with open('orchestrated_kitchen_analysis.json', 'w') as f:
            json.dump(result.dict(), f, indent=2)
        
        print("\n💾 Results saved to orchestrated_kitchen_analysis.json")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
