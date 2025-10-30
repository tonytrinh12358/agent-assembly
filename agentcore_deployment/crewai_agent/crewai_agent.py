"""
CrewAI Cost Estimation Agent for AgentCore Runtime
"""

from crewai import Agent, Task, Crew, Process, LLM
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import json
import os
from enum import Enum
from bedrock_agentcore.runtime import BedrockAgentCoreApp

app = BedrockAgentCoreApp()


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


class KitchenCostEstimator:
    def __init__(self, region: str = "us-west-2"):
        # Initialize CrewAI Bedrock LLM
        self.llm = LLM(
            model="bedrock/us.amazon.nova-premier-v1:0",
            aws_region_name=region
        )
        
        self.crew = self._setup_crew()
    
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
            process=Process.sequential,
            verbose=True
        )
    
    def estimate_costs(self, materials_data: List[Dict], grade: MaterialGrade = MaterialGrade.STANDARD) -> Dict[str, Any]:
        """Use actual CrewAI agents to estimate costs"""
        
        materials_context = json.dumps(materials_data, indent=2)
        
        # Task 1: Material Cost Analysis
        material_analysis_task = Task(
            description=f"""
            Analyze these kitchen materials and provide Australian cost estimates:
            {materials_context}
            
            For {grade.value} grade materials, provide cost per square metre in AUD:
            - Wood (cabinets): Consider Australian hardwood/engineered options
            - Granite (countertops): Consider Australian stone suppliers
            - Tile (flooring): Consider ceramic/porcelain options
            - Stainless steel (appliances): Consider commercial grade pricing
            
            Return costs in this format:
            - Material: $XXX AUD per sqm
            - Total for each material type
            """,
            agent=self.crew.agents[0],
            expected_output="Detailed material cost breakdown in AUD per square metre"
        )
        
        # Task 2: Labor Cost Analysis
        labor_analysis_task = Task(
            description=f"""
            Based on the material analysis, calculate Australian labor costs for installation:
            
            Consider:
            - Kitchen cabinet installation: $80-120 AUD per sqm
            - Granite countertop installation: $100-150 AUD per sqm  
            - Tile flooring installation: $60-90 AUD per sqm
            - Appliance installation: $200-300 AUD per unit
            
            Factor in complexity, access, and Australian trade rates.
            """,
            agent=self.crew.agents[1],
            expected_output="Labor cost calculations with Australian trade rates",
            context=[material_analysis_task]
        )
        
        # Task 3: Cost Synthesis
        synthesis_task = Task(
            description="""
            Synthesize the material and labor costs into a comprehensive estimate:
            
            Include:
            - Total material costs
            - Total labor costs  
            - 15% contingency
            - Final project total in AUD
            - Cost per square metre
            - Budget range (+/- 15%)
            
            Format as JSON with clear cost breakdown.
            """,
            agent=self.crew.agents[2],
            expected_output="Complete cost synthesis in JSON format with AUD totals",
            context=[material_analysis_task, labor_analysis_task]
        )
        
        # Execute the crew
        crew_with_tasks = Crew(
            agents=self.crew.agents,
            tasks=[material_analysis_task, labor_analysis_task, synthesis_task],
            process=Process.sequential,
            verbose=True
        )
        
        # Run the actual CrewAI workflow
        result = crew_with_tasks.kickoff()
        
        # Parse the result and format for our system
        return self._parse_crew_result(result, materials_data, grade)
    
    def _parse_crew_result(self, crew_result: str, materials_data: List[Dict], grade: MaterialGrade) -> Dict[str, Any]:
        """Parse CrewAI result and format for our system"""
        try:
            # Try to extract JSON from crew result
            import re
            json_match = re.search(r'\{.*\}', str(crew_result), re.DOTALL)
            if json_match:
                parsed_result = json.loads(json_match.group())
                return parsed_result
        except:
            pass
        
        # Fallback: Create structured result from crew output
        estimates = []
        total_cost = 0
        
        # Basic parsing of crew result for key costs
        base_costs = {
            "wood": 200.0,
            "granite": 900.0, 
            "tile": 85.0,
            "stainless_steel": 250.0
        }
        
        for material in materials_data:
            material_type = material["material_type"]
            area = material["area_sqm"]
            
            if material_type in base_costs:
                unit_cost = base_costs[material_type]
                material_cost = area * unit_cost
                labor_cost = material_cost * 0.6  # 60% labor rate
                total_item_cost = material_cost + labor_cost
                
                estimate = {
                    "material_type": material_type,
                    "area_sqm": area,
                    "unit_cost": unit_cost,
                    "total_material_cost": material_cost,
                    "labor_cost": labor_cost,
                    "total_cost": total_item_cost,
                    "grade": grade.value
                }
                
                estimates.append(estimate)
                total_cost += total_item_cost
        
        return {
            "estimates": estimates,
            "total_material_cost": sum(e["total_material_cost"] for e in estimates),
            "total_labor_cost": sum(e["labor_cost"] for e in estimates),
            "subtotal": total_cost,
            "contingency": total_cost * 0.15,
            "total_project_cost": total_cost * 1.15,
            "grade": grade.value,
            "crew_analysis": str(crew_result)
        }


# Initialize the estimator
estimator = KitchenCostEstimator()


@app.entrypoint
def crewai_cost_estimator(payload):
    """
    AgentCore entrypoint for CrewAI cost estimator
    """
    user_input = payload.get("prompt", "")
    materials_data = payload.get("materials_data", [])
    cost_grade = payload.get("cost_grade", "standard")
    
    print(f"CrewAI Agent received: {user_input}")
    print(f"Materials data: {len(materials_data)} items")
    
    try:
        # Parse materials if provided as JSON string
        if isinstance(materials_data, str):
            materials_data = json.loads(materials_data)
        
        # Default materials if none provided
        if not materials_data:
            materials_data = [
                {"material_type": "wood", "area_sqm": 14.0, "location": "cabinet"},
                {"material_type": "granite", "area_sqm": 7.5, "location": "countertop"},
                {"material_type": "tile", "area_sqm": 18.5, "location": "flooring"}
            ]
        
        # Convert grade
        grade = MaterialGrade(cost_grade.lower())
        
        # Run cost estimation
        result = estimator.estimate_costs(materials_data, grade)
        
        # Return JSON result
        return json.dumps(result, indent=2)
        
    except Exception as e:
        error_result = {
            "error": f"CrewAI cost estimation failed: {str(e)}",
            "status": "failed"
        }
        return json.dumps(error_result, indent=2)


if __name__ == "__main__":
    app.run()

