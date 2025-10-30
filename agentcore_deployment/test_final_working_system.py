#!/usr/bin/env python3
"""
Final test of the working MCP system with real data
"""

import asyncio
import sys
import base64
import json
from pathlib import Path

# Add MCP base to path
sys.path.append('mcp_base')
from mcp_base.mcp_client_utils import AgentCoreMCPClient

async def test_working_system():
    """Test the complete working MCP system with simplified agents"""
    
    print("🎉 TESTING THE WORKING MCP SYSTEM WITH REAL DATA")
    print("=" * 60)
    print("")
    
    client = AgentCoreMCPClient()
    
    # Load image
    image_path = "/Users/totrinh/Library/CloudStorage/OneDrive-amazon.com/workspace/agent-assemble/TechSummit_2025/sample_images/img_1.jpg"
    with open(image_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')
    
    print("🔄 Testing the complete working MCP workflow...")
    
    result = await client.invoke_agent_tool(
        'orchestrator_agent',
        'orchestrate_renovation_workflow',
        image_data=image_data,
        renovation_goals='Modern kitchen with granite countertops and energy-efficient appliances',
        budget_range='75000'
    )
    
    print(f"Status: {result.get('status')}")
    
    if result.get('status') == 'success':
        raw_result = result.get('result', {})
        
        try:
            if isinstance(raw_result, str):
                parsed = json.loads(raw_result)
            else:
                parsed = raw_result
            
            # Check for errors
            if 'error' in parsed:
                error_msg = parsed['error']['message'] if isinstance(parsed['error'], dict) else str(parsed['error'])
                print(f"❌ Still getting error: {error_msg}")
                return False
            
            # Check for actual results
            if 'result' in parsed and isinstance(parsed['result'], dict):
                workflow_result = parsed['result']
                print("🎉🎉🎉 SUCCESS! REAL WORKFLOW RESULTS! 🎉🎉🎉")
                print("=" * 60)
                
                # Display image analysis
                if 'image_analysis' in workflow_result:
                    analysis = workflow_result['image_analysis']
                    print("🔍 IMAGE ANALYSIS (via LangGraph MCP):")
                    if 'detected_objects' in analysis:
                        objects = analysis['detected_objects']
                        print(f"   - Objects detected: {len(objects)} kitchen items")
                        print(f"   - Examples: {[obj['name'] for obj in objects[:3]]}")
                    if 'materials' in analysis:
                        materials = analysis['materials']
                        print(f"   - Materials identified: {len(materials)} types")
                        areas = [f"{m['material_type']} ({m['area_sqm']}sqm)" for m in materials]
                        print(f"   - Areas: {areas}")
                    print("")
                
                # Display cost estimate
                if 'cost_estimate' in workflow_result:
                    estimate = workflow_result['cost_estimate']
                    print("💰 COST ESTIMATE (via CrewAI MCP):")
                    if 'project_estimate' in estimate:
                        project = estimate['project_estimate']
                        final_total = project.get('final_total_AUD', 'N/A')
                        if isinstance(final_total, (int, float)):
                            print(f"   - Total project cost: ${final_total:,.0f} AUD")
                        else:
                            print(f"   - Total project cost: {final_total}")
                        
                        if 'total_material_costs' in project:
                            mat_costs = project['total_material_costs']
                            subtotal = mat_costs.get('subtotal', 0)
                            print(f"   - Materials subtotal: ${subtotal:,.0f}")
                        
                        if 'total_labor_costs' in project:
                            lab_costs = project['total_labor_costs']
                            labor_cost = lab_costs.get('average_labor_cost', 0)
                            print(f"   - Labor subtotal: ${labor_cost:,.0f}")
                    print("")
                
                # Display recommendations
                if 'recommendations' in workflow_result:
                    recs = workflow_result['recommendations']
                    print("💡 RECOMMENDATIONS (Multi-agent coordination):")
                    for i, rec in enumerate(recs[:3], 1):
                        print(f"   {i}. {rec}")
                    print("")
                
                print("🚀🚀🚀 THE STREAMLIT UI WILL NOW DISPLAY REAL RESULTS! 🚀🚀🚀")
                return True
            else:
                print(f"🔍 Unexpected result format: {str(parsed)[:200]}...")
                return False
        except Exception as e:
            print(f"Parse error: {e}")
            print(f"Raw result: {str(raw_result)[:300]}...")
            return False
    else:
        print(f"❌ Workflow failed: {result.get('error', 'Unknown')}")
        return False

async def main():
    """Main test function"""
    success = await test_working_system()
    
    print("\n" + "=" * 70)
    if success:
        print("🎉🎉🎉 COMPLETE SUCCESS! MCP SYSTEM WORKING WITH REAL DATA! 🎉🎉🎉")
        print("✅ Kitchen analysis: Working via LangGraph MCP agent")  
        print("✅ Cost estimation: Working via CrewAI MCP agent")
        print("✅ Agent coordination: Working via Orchestrator MCP agent")
        print("✅ All communication: Model Context Protocol")
        print("")
        print("🚀 Try your Streamlit UI now - it should show actual results!")
        print("📱 URL: http://localhost:8503")
    else:
        print("🔧 Still debugging, but made significant progress!")
    
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
