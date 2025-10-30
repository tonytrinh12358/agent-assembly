"""
CrewAI Cost Estimation Agent - MCP Server Implementation
Provides kitchen renovation cost estimation via Model Context Protocol.
"""

import sys
import os
import json
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum

# Add the mcp_base directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'mcp_base'))

from mcp_server_base import AgentCoreMCPServer, create_success_response, create_error_response
from crewai import Agent, Task, Crew, Process, LLM

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MaterialGrade(str, Enum):
    ECONOMY = "economy"
    STANDARD = "standard"
    PREMIUM = "premium"


class CostEstimate(BaseModel):
    material_type: str
    area_sqm: float
    unit_cost: float
    total_material_cost: float
    labor_cost: float
    total_cost: float
    grade: MaterialGrade


class CrewAICostMCPServer:
    """MCP Server implementation for CrewAI Cost Estimation Agent"""
    
    def __init__(self, region: str = "us-west-2"):
        self.region = region
        
        # Initialize the MCP server
        self.mcp_server = AgentCoreMCPServer(
            agent_name="CrewAI Cost Estimator",
            description="Multi-agent cost estimation team for kitchen renovation planning with Australian pricing"
        )
        
        # Initialize CrewAI components
        self._initialize_crewai()
        
        # Setup MCP tools
        self._setup_mcp_tools()
        
        logger.info("💰 CrewAI Cost Estimation MCP Server initialized")
    
    def _initialize_crewai(self):
        """Initialize CrewAI components - simplified for MCP demo"""
        try:
            logger.info("🔧 Initializing simplified CrewAI components for MCP demo")
            
            # Use None for complex components - we'll use mock data instead
            self.llm = None
            self.crew = None
            
            logger.info("✅ CrewAI components initialized (simplified mode)")
            
        except Exception as e:
            logger.error(f"Failed to initialize CrewAI: {e}")
            raise
    
    def _setup_crew(self):
        """Setup CrewAI agents with Bedrock models"""
        
        # Materials Expert Agent
        materials_expert = Agent(
            role='Materials Cost Expert',
            goal='Analyze kitchen materials and provide accurate Australian cost estimates per square metre',
            backstory='''You are an expert in Australian construction materials with 15+ years experience. 
            You know current market prices for kitchen materials in AUD per square metre.
            You specialize in wood, granite, tiles, and stainless steel pricing.''',
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
        
        # Labor Cost Analyst
        labor_analyst = Agent(
            role='Labor Cost Analyst', 
            goal='Calculate Australian labor costs for kitchen installation based on material complexity',
            backstory='''You are an experienced Australian contractor specializing in kitchen installations. 
            You know labor rates, installation complexity, and time requirements for different materials.
            You calculate costs in AUD and consider Australian trade rates.''',
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
        
        # Cost Synthesizer
        cost_synthesizer = Agent(
            role='Cost Synthesizer',
            goal='Combine material and labor costs into comprehensive Australian kitchen renovation estimates',
            backstory='''You are a financial analyst specializing in Australian construction project costs. 
            You synthesize material and labor estimates, add contingencies, and provide realistic budget ranges.''',
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
        
        return Crew(
            agents=[materials_expert, labor_analyst, cost_synthesizer],
            tasks=[],  # Tasks will be created dynamically
            process=Process.sequential,
            verbose=True
        )
    
    def _get_base_prices(self, grade: MaterialGrade) -> Dict[str, Dict[str, float]]:
        """Get base material prices for different grades"""
        base_prices = {
            MaterialGrade.ECONOMY: {
                "wood": {"unit_cost": 180, "labor_multiplier": 1.2},
                "granite": {"unit_cost": 350, "labor_multiplier": 1.5},
                "tile": {"unit_cost": 85, "labor_multiplier": 1.1},
                "stainless_steel": {"unit_cost": 120, "labor_multiplier": 1.3},
                "laminate": {"unit_cost": 65, "labor_multiplier": 1.0},
                "vinyl": {"unit_cost": 45, "labor_multiplier": 1.0}
            },
            MaterialGrade.STANDARD: {
                "wood": {"unit_cost": 280, "labor_multiplier": 1.3},
                "granite": {"unit_cost": 550, "labor_multiplier": 1.6},
                "tile": {"unit_cost": 125, "labor_multiplier": 1.2},
                "stainless_steel": {"unit_cost": 180, "labor_multiplier": 1.4},
                "laminate": {"unit_cost": 95, "labor_multiplier": 1.1},
                "vinyl": {"unit_cost": 75, "labor_multiplier": 1.1}
            },
            MaterialGrade.PREMIUM: {
                "wood": {"unit_cost": 450, "labor_multiplier": 1.5},
                "granite": {"unit_cost": 850, "labor_multiplier": 1.8},
                "tile": {"unit_cost": 185, "labor_multiplier": 1.4},
                "stainless_steel": {"unit_cost": 280, "labor_multiplier": 1.6},
                "laminate": {"unit_cost": 145, "labor_multiplier": 1.2},
                "vinyl": {"unit_cost": 115, "labor_multiplier": 1.2}
            }
        }
        
        return base_prices.get(grade, base_prices[MaterialGrade.STANDARD])
    
    def _estimate_material_costs(self, materials_data: List[Dict], grade: MaterialGrade) -> List[CostEstimate]:
        """Estimate costs for materials using CrewAI crew"""
        try:
            price_data = self._get_base_prices(grade)
            estimates = []
            
            for material in materials_data:
                material_type = material.get("material_type", "unknown")
                area = material.get("area_sqm", 0.0)
                
                # Get pricing info or use default
                pricing = price_data.get(material_type, {"unit_cost": 100, "labor_multiplier": 1.2})
                
                unit_cost = pricing["unit_cost"]
                total_material_cost = unit_cost * area
                labor_cost = total_material_cost * pricing["labor_multiplier"]
                total_cost = total_material_cost + labor_cost
                
                estimate = CostEstimate(
                    material_type=material_type,
                    area_sqm=area,
                    unit_cost=unit_cost,
                    total_material_cost=total_material_cost,
                    labor_cost=labor_cost,
                    total_cost=total_cost,
                    grade=grade
                )
                
                estimates.append(estimate)
            
            return estimates
            
        except Exception as e:
            logger.error(f"Cost estimation failed: {e}")
            raise
    
    def _extract_materials_from_analysis(self, kitchen_analysis: Dict) -> List[Dict]:
        """Extract materials data from kitchen analysis results"""
        # Default materials for kitchen renovation
        default_materials = [
            {"material_type": "granite", "area_sqm": 15.0, "location": "countertops"},
            {"material_type": "wood", "area_sqm": 25.0, "location": "cabinets"},
            {"material_type": "tile", "area_sqm": 20.0, "location": "backsplash"},
            {"material_type": "stainless_steel", "area_sqm": 2.0, "location": "appliances"}
        ]
        
        # If analysis has materials info, use it, otherwise use defaults
        if isinstance(kitchen_analysis, dict) and 'materials' in kitchen_analysis:
            return kitchen_analysis['materials']
        else:
            return default_materials
    
    def _setup_mcp_tools(self):
        """Setup MCP tools for cost estimation"""
        
        @self.mcp_server.mcp.tool()
        def estimate_renovation_costs(materials_data=None, cost_grade: str = "standard", renovation_goals: str = None, budget_range: str = None, kitchen_analysis=None):
            """Estimate costs - simplified for MCP demo"""
            return {
                "status": "success",
                "project_estimate": {
                    "final_total_AUD": 75000,
                    "total_material_costs": {"subtotal": 40000},
                    "total_labor_costs": {"average_labor_cost": 25000}
                },
                "recommendations": [
                    "Total project cost: $75,000 AUD",
                    "Material costs: $40,000 AUD", 
                    "Labor costs: $25,000 AUD"
                ]
            }
        
        @self.mcp_server.mcp.tool()
        def get_material_pricing(material_type: str, cost_grade: str = "standard") -> str:
            """
            Get pricing information for a specific material type
            
            Args:
                material_type: Type of material (wood, granite, tile, etc.)
                cost_grade: Cost grade - economy, standard, or premium
                
            Returns:
                JSON string with pricing information for the material
            """
            try:
                logger.info(f"💰 Getting pricing for {material_type} at {cost_grade} grade")
                
                grade = MaterialGrade(cost_grade.lower())
                price_data = self._get_base_prices(grade)
                
                if material_type in price_data:
                    pricing = price_data[material_type]
                    result = create_success_response({
                        "material_type": material_type,
                        "cost_grade": cost_grade,
                        "unit_cost_per_sqm_aud": pricing["unit_cost"],
                        "labor_multiplier": pricing["labor_multiplier"],
                        "estimated_labor_cost_per_sqm": pricing["unit_cost"] * pricing["labor_multiplier"]
                    })
                else:
                    available_materials = list(price_data.keys())
                    result = create_error_response(
                        f"Material '{material_type}' not found. Available: {available_materials}",
                        "MATERIAL_NOT_FOUND"
                    )
                
                return result
                
            except Exception as e:
                error_message = f"Pricing lookup failed: {str(e)}"
                logger.error(f"❌ Pricing lookup failed: {e}")
                return {"error": error_message, "status": "failed"}
        
        @self.mcp_server.mcp.tool()
        def compare_cost_grades(materials_data: List[Dict]) -> str:
            """
            Compare costs across all grade levels for given materials
            
            Args:
                materials_data: List of materials with type and area information
                
            Returns:
                JSON string with cost comparison across grades
            """
            try:
                logger.info(f"📊 Comparing costs across grades for {len(materials_data)} materials")
                
                comparison = {}
                
                for grade in MaterialGrade:
                    estimates = self._estimate_material_costs(materials_data, grade)
                    total_cost = sum(est.total_cost for est in estimates)
                    total_material = sum(est.total_material_cost for est in estimates)
                    total_labor = sum(est.labor_cost for est in estimates)
                    
                    # Add contingencies
                    contingency = total_cost * 0.10
                    project_mgmt = total_cost * 0.05
                    final_total = total_cost + contingency + project_mgmt
                    
                    comparison[grade.value] = {
                        "materials_cost": total_material,
                        "labor_cost": total_labor,
                        "subtotal": total_cost,
                        "contingency": contingency,
                        "project_management": project_mgmt,
                        "final_total": final_total
                    }
                
                result = create_success_response({
                    "cost_comparison": comparison,
                    "savings": {
                        "standard_vs_economy": comparison["economy"]["final_total"] - comparison["standard"]["final_total"],
                        "premium_vs_standard": comparison["premium"]["final_total"] - comparison["standard"]["final_total"],
                        "premium_vs_economy": comparison["premium"]["final_total"] - comparison["economy"]["final_total"]
                    },
                    "recommendations": [
                        f"Economy grade: ${comparison['economy']['final_total']:,.0f} AUD",
                        f"Standard grade: ${comparison['standard']['final_total']:,.0f} AUD", 
                        f"Premium grade: ${comparison['premium']['final_total']:,.0f} AUD",
                        "Standard grade offers the best value-to-quality ratio for most renovations"
                    ]
                })
                
                logger.info("✅ Cost comparison completed across all grades")
                return result
                
            except Exception as e:
                error_message = f"Cost comparison failed: {str(e)}"
                logger.error(f"❌ Cost comparison failed: {e}")
                return {"error": error_message, "status": "failed"}
    
    def run(self):
        """Run the MCP server"""
        logger.info("🚀 Starting CrewAI Cost Estimation MCP Server...")
        self.mcp_server.run()


# Create server instance
mcp_server = CrewAICostMCPServer()

if __name__ == "__main__":
    mcp_server.run()
