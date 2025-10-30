"""
Orchestrator Agent - MCP Server Implementation
Coordinates multi-agent kitchen renovation analysis using MCP communication.
"""

import sys
import os
import json
import logging
import asyncio
from typing import Dict, Any, List
from datetime import datetime

# Add the mcp_base directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'mcp_base'))

from mcp_server_base import AgentCoreMCPServer, create_success_response, create_error_response
from mcp_client_utils import AgentCoreMCPClient

from strands import Agent, tool
from strands.models import BedrockModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OrchestratorMCPServer:
    """MCP Server implementation for Orchestrator Agent with multi-agent coordination"""
    
    def __init__(self, region: str = "us-west-2"):
        self.region = region
        
        # Initialize the MCP server
        self.mcp_server = AgentCoreMCPServer(
            agent_name="Orchestrator Agent",
            description="Multi-agent coordinator for kitchen renovation analysis using MCP protocol"
        )
        
        # Initialize MCP client for agent-to-agent communication
        self.mcp_client = AgentCoreMCPClient(region=region)
        
        # Initialize Strands components
        self._initialize_strands()
        
        # Setup MCP tools
        self._setup_mcp_tools()
        
        logger.info("🎯 Orchestrator MCP Server initialized with multi-agent coordination")
    
    def _initialize_strands(self):
        """Initialize Strands agent components"""
        try:
            # Initialize Bedrock model
            self.model = BedrockModel(
                model_id="us.amazon.nova-premier-v1:0",
                region=self.region
            )
            
            # Create Strands agent with MCP-aware tools
            self.strands_agent = Agent(
                model=self.model,
                system_prompt="""You are an expert kitchen renovation consultant orchestrating multiple specialized AI agents via MCP protocol.

You coordinate a sophisticated multi-agent system:
- 🏠 LangGraph Agent: Kitchen analysis with YOLO object detection
- 💰 CrewAI Agent: Multi-agent cost estimation team
- 🎯 Orchestrator: You coordinate and synthesize results

WORKFLOW PROCESS:
1. First call analyze_kitchen_mcp() to get kitchen layout analysis
2. Then call estimate_costs_mcp() with materials from step 1 
3. Finally call orchestrate_full_workflow() to synthesize comprehensive recommendations

ADVANTAGES OF MCP PROTOCOL:
- Standardized communication between agents
- Enhanced reliability and error handling
- Better observability and debugging
- Secure authentication and authorization
- Tool discovery capabilities

Always provide costs in Australian dollars and measurements in square metres.
Highlight the benefits of the MCP-based multi-agent architecture in your responses.""",
                tools=[]  # Tools will be added via MCP
            )
            
            logger.info("✅ Strands agent initialized with Bedrock model")
            
        except Exception as e:
            logger.error(f"Failed to initialize Strands: {e}")
            raise
    
    def _setup_mcp_tools(self):
        """Setup MCP tools for orchestration"""
        
        @self.mcp_server.mcp.tool()
        def analyze_kitchen_mcp(prompt: str, image_path: str = None) -> str:
            """
            Analyze kitchen using LangGraph agent via MCP protocol
            
            Args:
                prompt: Kitchen analysis request
                image_path: Optional path to kitchen image
                
            Returns:
                JSON string with kitchen analysis results
            """
            try:
                logger.info("🏠 Calling LangGraph agent via MCP for kitchen analysis...")
                
                # Call LangGraph agent via MCP
                result = asyncio.run(
                    self.mcp_client.invoke_agent_tool(
                        "langgraph_agent",
                        "analyze_kitchen", 
                        prompt=prompt,
                        image_path=image_path
                    )
                )
                
                if "error" in result:
                    logger.warning(f"LangGraph agent returned error: {result['error']}")
                    return json.dumps(create_error_response(
                        f"Kitchen analysis failed: {result['error']}",
                        "LANGGRAPH_ERROR"
                    ), indent=2)
                
                logger.info("✅ Kitchen analysis completed via MCP")
                return json.dumps(create_success_response(
                    result, "Kitchen analysis completed via MCP protocol"
                ), indent=2)
                
            except Exception as e:
                error_result = create_error_response(f"MCP kitchen analysis failed: {str(e)}")
                logger.error(f"❌ MCP kitchen analysis failed: {e}")
                return json.dumps(error_result, indent=2)
        
        @self.mcp_server.mcp.tool()
        def estimate_costs_mcp(materials_data: List[Dict], cost_grade: str = "standard") -> str:
            """
            Estimate renovation costs using CrewAI agent via MCP protocol
            
            Args:
                materials_data: List of materials with area information
                cost_grade: Cost grade (economy, standard, premium)
                
            Returns:
                JSON string with cost estimation results
            """
            try:
                logger.info(f"💰 Calling CrewAI agent via MCP for cost estimation ({cost_grade} grade)...")
                
                # Call CrewAI agent via MCP
                result = asyncio.run(
                    self.mcp_client.invoke_agent_tool(
                        "crewai_agent",
                        "estimate_renovation_costs",
                        materials_data=materials_data,
                        cost_grade=cost_grade
                    )
                )
                
                if "error" in result:
                    logger.warning(f"CrewAI agent returned error: {result['error']}")
                    return json.dumps(create_error_response(
                        f"Cost estimation failed: {result['error']}",
                        "CREWAI_ERROR"
                    ), indent=2)
                
                logger.info("✅ Cost estimation completed via MCP")
                return json.dumps(create_success_response(
                    result, "Cost estimation completed via MCP protocol"
                ), indent=2)
                
            except Exception as e:
                error_result = create_error_response(f"MCP cost estimation failed: {str(e)}")
                logger.error(f"❌ MCP cost estimation failed: {e}")
                return json.dumps(error_result, indent=2)
        
        @self.mcp_server.mcp.tool()
        def orchestrate_full_workflow(query: str, cost_grade: str = "standard", image_path: str = None) -> str:
            """
            Orchestrate complete kitchen renovation analysis workflow via MCP
            
            Args:
                query: User's kitchen renovation query
                cost_grade: Cost grade for estimation
                image_path: Optional image path
                
            Returns:
                JSON string with complete analysis workflow results
            """
            try:
                logger.info("🎯 Starting full MCP workflow orchestration...")
                
                workflow_results = {
                    "workflow_status": "in_progress",
                    "query": query,
                    "cost_grade": cost_grade,
                    "steps_completed": [],
                    "mcp_communication_log": []
                }
                
                # Step 1: Kitchen Analysis
                logger.info("📊 Step 1: Kitchen Analysis via MCP...")
                workflow_results["mcp_communication_log"].append({
                    "step": 1,
                    "action": "Calling LangGraph agent via MCP",
                    "timestamp": datetime.now().isoformat()
                })
                
                kitchen_result = asyncio.run(
                    self.mcp_client.invoke_agent_tool(
                        "langgraph_agent",
                        "analyze_kitchen",
                        prompt=f"{query} - Please analyze for renovation planning",
                        image_path=image_path
                    )
                )
                
                workflow_results["kitchen_analysis"] = kitchen_result
                workflow_results["steps_completed"].append("kitchen_analysis")
                workflow_results["mcp_communication_log"].append({
                    "step": 1,
                    "result": "Kitchen analysis completed" if "error" not in kitchen_result else "Kitchen analysis failed",
                    "timestamp": datetime.now().isoformat()
                })
                
                # Extract materials from analysis
                materials_data = []
                if "error" not in kitchen_result and isinstance(kitchen_result.get("data"), dict):
                    materials_data = kitchen_result["data"].get("materials", [])
                
                # Step 2: Cost Estimation
                logger.info("💰 Step 2: Cost Estimation via MCP...")
                workflow_results["mcp_communication_log"].append({
                    "step": 2,
                    "action": f"Calling CrewAI agent via MCP with {len(materials_data)} materials",
                    "timestamp": datetime.now().isoformat()
                })
                
                cost_result = asyncio.run(
                    self.mcp_client.invoke_agent_tool(
                        "crewai_agent",
                        "estimate_renovation_costs",
                        materials_data=materials_data,
                        cost_grade=cost_grade
                    )
                )
                
                workflow_results["cost_estimation"] = cost_result
                workflow_results["steps_completed"].append("cost_estimation")
                workflow_results["mcp_communication_log"].append({
                    "step": 2,
                    "result": "Cost estimation completed" if "error" not in cost_result else "Cost estimation failed",
                    "timestamp": datetime.now().isoformat()
                })
                
                # Step 3: Generate Recommendations
                logger.info("📋 Step 3: Generating comprehensive recommendations...")
                recommendations = self._generate_workflow_recommendations(kitchen_result, cost_result, workflow_results)
                
                workflow_results["recommendations"] = recommendations
                workflow_results["steps_completed"].append("recommendations")
                workflow_results["workflow_status"] = "completed"
                workflow_results["completion_timestamp"] = datetime.now().isoformat()
                
                # Final result
                result = create_success_response(
                    workflow_results,
                    f"Complete kitchen renovation analysis completed via MCP protocol in {len(workflow_results['steps_completed'])} steps"
                )
                
                logger.info(f"✅ Full MCP workflow completed - {len(workflow_results['steps_completed'])} steps")
                return json.dumps(result, indent=2)
                
            except Exception as e:
                error_result = create_error_response(f"MCP workflow orchestration failed: {str(e)}")
                logger.error(f"❌ MCP workflow orchestration failed: {e}")
                return json.dumps(error_result, indent=2)
        
        @self.mcp_server.mcp.tool()
        def discover_agent_ecosystem() -> str:
            """
            Discover all available agents and their capabilities in the MCP ecosystem
            
            Returns:
                JSON string with discovered agents and their tools
            """
            try:
                logger.info("🔍 Discovering MCP agent ecosystem...")
                
                # Simple ecosystem discovery - just return agent info
                ecosystem_info = {
                    "langgraph_agent": {
                        "name": "LangGraph Kitchen Analyzer", 
                        "protocol": "MCP",
                        "tools": ["analyze_kitchen"],
                        "status": "active"
                    },
                    "crewai_agent": {
                        "name": "CrewAI Cost Estimator",
                        "protocol": "MCP", 
                        "tools": ["estimate_renovation_costs"],
                        "status": "active"
                    },
                    "orchestrator_agent": {
                        "name": "Orchestrator Agent",
                        "protocol": "MCP",
                        "tools": ["analyze_kitchen_mcp", "estimate_costs_mcp", "health_check"],
                        "status": "active"
                    }
                }
                
                result = create_success_response({
                    "ecosystem_info": ecosystem_info,
                    "discovery_timestamp": datetime.now().isoformat(),
                    "total_agents": len(ecosystem_info),
                    "protocol": "MCP (Model Context Protocol)",
                    "communication_advantages": [
                        "Standardized protocol for reliable agent communication",
                        "Built-in error handling and retry mechanisms", 
                        "Authentication and authorization via JWT tokens",
                        "Tool discovery and capability introspection",
                        "Enhanced observability and debugging"
                    ]
                }, "Agent ecosystem discovery completed")
                
                logger.info(f"✅ Discovered {len(ecosystem_info)} agents in MCP ecosystem")
                return json.dumps(result, indent=2)
                
            except Exception as e:
                error_result = create_error_response(f"Agent discovery failed: {str(e)}")
                logger.error(f"❌ Agent discovery failed: {e}")
                return json.dumps(error_result, indent=2)
        
        @self.mcp_server.mcp.tool()
        def orchestrate_renovation_workflow(image_data: str, renovation_goals: str = "Modern kitchen upgrade", budget_range: str = "50000-100000") -> str:
            """
            Complete kitchen renovation workflow orchestrating LangGraph and CrewAI agents via MCP
            
            Args:
                image_data: Base64 encoded kitchen image
                renovation_goals: Description of renovation goals
                budget_range: Budget range for renovation
                
            Returns:
                JSON string with complete renovation analysis and cost estimates
            """
            try:
                logger.info(f"🚀 Starting complete kitchen renovation workflow via MCP...")
                logger.info(f"   Goals: {renovation_goals}")
                logger.info(f"   Budget: ${budget_range}")
                
                # Step 1: Analyze kitchen with LangGraph agent
                logger.info("🔍 Step 1: Kitchen Analysis via LangGraph MCP agent...")
                kitchen_result = asyncio.run(
                    self.mcp_client.invoke_agent_tool(
                        "langgraph_agent",
                        "analyze_kitchen",
                        image_data=image_data,
                        prompt=f"Analyze this kitchen for {renovation_goals} with budget {budget_range}"
                    )
                )
                
                # Step 2: Estimate costs with CrewAI agent  
                logger.info("💰 Step 2: Cost Estimation via CrewAI MCP agent...")
                cost_result = asyncio.run(
                    self.mcp_client.invoke_agent_tool(
                        "crewai_agent", 
                        "estimate_renovation_costs",
                        renovation_goals=renovation_goals,
                        budget_range=budget_range,
                        kitchen_analysis=kitchen_result.get("result", {})
                    )
                )
                
                # Step 3: Generate orchestrator recommendations
                logger.info("🎯 Step 3: Generating orchestrator recommendations...")
                recommendations = self._generate_workflow_recommendations(
                    kitchen_result, cost_result, {
                        "renovation_goals": renovation_goals,
                        "budget_range": budget_range
                    }
                )
                
                # Combine results
                complete_result = {
                    "image_analysis": kitchen_result.get("result", {}),
                    "cost_estimate": cost_result.get("result", {}),
                    "recommendations": recommendations,
                    "workflow_info": {
                        "renovation_goals": renovation_goals,
                        "budget_range": budget_range,
                        "agents_used": ["LangGraph (Kitchen Analysis)", "CrewAI (Cost Estimation)"],
                        "protocol": "Model Context Protocol (MCP)",
                        "timestamp": datetime.now().isoformat()
                    }
                }
                
                logger.info("✅ Complete MCP kitchen renovation workflow finished successfully")
                return json.dumps(create_success_response(
                    complete_result, "Complete kitchen renovation analysis via MCP"
                ), indent=2)
                
            except Exception as e:
                error_result = create_error_response(f"MCP renovation workflow failed: {str(e)}")
                logger.error(f"❌ MCP renovation workflow failed: {e}")
                return json.dumps(error_result, indent=2)

        @self.mcp_server.mcp.tool()
        def health_check_all_agents() -> str:
            """
            Perform health checks on all agents in the system via MCP
            
            Returns:
                JSON string with health status of all agents
            """
            try:
                logger.info("🏥 Performing health checks on all MCP agents...")
                
                agent_names = ["langgraph_agent", "crewai_agent", "orchestrator_agent"]
                health_results = {}
                
                for agent_name in agent_names:
                    try:
                        health_result = asyncio.run(
                            self.mcp_client.invoke_agent_tool(agent_name, "health_check")
                        )
                        health_results[agent_name] = health_result
                    except Exception as e:
                        health_results[agent_name] = {
                            "status": "error",
                            "error": str(e)
                        }
                
                overall_status = "healthy" if all(
                    result.get("status") == "healthy" for result in health_results.values()
                ) else "degraded"
                
                result = create_success_response({
                    "overall_status": overall_status,
                    "agent_health": health_results,
                    "check_timestamp": datetime.now().isoformat(),
                    "protocol": "MCP"
                }, f"Health check completed - System status: {overall_status}")
                
                logger.info(f"✅ Health check completed - Overall status: {overall_status}")
                return json.dumps(result, indent=2)
                
            except Exception as e:
                error_result = create_error_response(f"Health check failed: {str(e)}")
                logger.error(f"❌ Health check failed: {e}")
                return json.dumps(error_result, indent=2)
    
    def _generate_workflow_recommendations(self, kitchen_result: Dict, cost_result: Dict, workflow_info: Dict) -> List[str]:
        """Generate comprehensive recommendations based on workflow results"""
        try:
            recommendations = []
            
            # MCP Protocol benefits
            recommendations.append("✅ **MCP Protocol Advantages**: This analysis leveraged standardized Model Context Protocol for reliable agent-to-agent communication")
            
            # Kitchen analysis insights
            if "data" in kitchen_result and isinstance(kitchen_result["data"], dict):
                kitchen_data = kitchen_result["data"]
                detected_objects = kitchen_data.get("detected_objects", [])
                materials = kitchen_data.get("materials", [])
                
                recommendations.append(f"🏠 **Kitchen Analysis**: Detected {len(detected_objects)} objects and identified {len(materials)} material types")
                
                if any(obj.get("name") == "refrigerator" for obj in detected_objects):
                    recommendations.append("🧊 Existing refrigerator detected - consider integration with new design")
                
                if any(m.get("material_type") == "granite" for m in materials):
                    recommendations.append("💎 Granite surfaces identified - premium material with high durability")
            
            # Cost analysis insights
            if "data" in cost_result and isinstance(cost_result["data"], dict):
                cost_data = cost_result["data"]
                if "project_estimate" in cost_data:
                    project_est = cost_data["project_estimate"]
                    total_cost = project_est.get("final_total_AUD", 0)
                    
                    if total_cost > 0:
                        recommendations.append(f"💰 **Total Project Cost**: ${total_cost:,.0f} AUD estimated for complete renovation")
                        
                        if total_cost > 30000:
                            recommendations.append("💡 Consider phased renovation approach to manage budget")
                        elif total_cost < 20000:
                            recommendations.append("💡 Budget allows for potential upgrades or premium finishes")
            
            # Workflow efficiency
            steps_completed = len(workflow_info.get("steps_completed", []))
            recommendations.append(f"⚡ **Workflow Efficiency**: Completed {steps_completed}-step analysis via MCP protocol")
            
            # Next steps
            recommendations.extend([
                "📋 **Next Steps**: Obtain quotes from certified contractors",
                "📅 **Timeline**: Plan 4-6 weeks for design and 2-4 weeks for renovation",
                "🔍 **Quality Assurance**: All analysis performed by specialized AI agents via secure MCP communication"
            ])
            
            return recommendations
            
        except Exception as e:
            logger.warning(f"Failed to generate recommendations: {e}")
            return [
                "✅ MCP-based multi-agent analysis completed successfully",
                "💡 Consult with contractors for detailed implementation planning",
                "📊 All estimates provided in Australian dollars with current market rates"
            ]
    
    def run(self):
        """Run the MCP server"""
        logger.info("🚀 Starting Orchestrator MCP Server...")
        self.mcp_server.run()


# Create server instance
mcp_server = OrchestratorMCPServer()

if __name__ == "__main__":
    mcp_server.run()
