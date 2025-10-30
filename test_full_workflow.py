#!/usr/bin/env python3
"""
Test the complete Streamlit UI workflow
"""

import asyncio
import sys
import os
import re
import json
from datetime import datetime

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our Strands agent
from strands_agent.kitchen_strands_agent import (
    analyze_kitchen_comprehensive, 
    KitchenAnalysisRequest
)

async def test_full_workflow():
    """Test the complete workflow that Streamlit UI uses"""
    
    print("🏠 Testing Complete Kitchen Analysis Workflow")
    print("=" * 60)
    
    # Step 1: Create analysis request (like Streamlit UI does)
    print("📋 Step 1: Creating analysis request...")
    request = KitchenAnalysisRequest(
        image_path="/home/ubuntu/workspace/TechSummit_2025/sample_images/img_1.jpg",
        cost_grade="standard",
        include_labor=True
    )
    print(f"✅ Request created: {request.cost_grade} grade, labor included: {request.include_labor}")
    
    # Step 2: Run Strands agent analysis
    print("\n🤖 Step 2: Running Strands agent analysis...")
    try:
        result = await analyze_kitchen_comprehensive(request)
        print("✅ Strands agent analysis completed successfully")
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return
    
    # Step 3: Extract response content (like Streamlit UI does)
    print("\n📊 Step 3: Extracting response content...")
    response_content = result.summary.get('strands_response', '')
    
    if not response_content:
        print("❌ No response content found")
        return
    
    print(f"✅ Response content extracted ({len(response_content)} characters)")
    
    # Step 4: Parse cost data (using same logic as Streamlit UI)
    print("\n💰 Step 4: Parsing cost data...")
    total_cost = 0.00
    material_cost = 0.00
    labor_cost = 0.00
    
    # Look for embedded JSON cost data
    cost_json_match = re.search(r'COST_DATA_JSON: (\{[^}]+\})', response_content)
    if cost_json_match:
        try:
            cost_data = json.loads(cost_json_match.group(1))
            total_cost = cost_data.get('total_cost', 0)
            material_cost = cost_data.get('material_cost', 0)
            labor_cost = cost_data.get('labor_cost', 0)
            print("✅ Successfully parsed embedded JSON cost data")
        except json.JSONDecodeError:
            print("⚠️ JSON parsing failed, trying regex fallback...")
    
    # Fallback to regex patterns if JSON parsing fails
    if total_cost == 0:
        cost_match = re.search(r'Total Project Cost: \$([0-9,]+\.?\d*)', response_content)
        if cost_match:
            total_cost = float(cost_match.group(1).replace(',', ''))
        
        material_match = re.search(r'Material Costs: \$([0-9,]+\.?\d*)', response_content)
        if material_match:
            material_cost = float(material_match.group(1).replace(',', ''))
        
        labor_match = re.search(r'Labor Costs: \$([0-9,]+\.?\d*)', response_content)
        if labor_match:
            labor_cost = float(labor_match.group(1).replace(',', ''))
    
    # Step 5: Display results (like Streamlit UI would)
    print("\n🎯 Step 5: Final Results")
    print("=" * 40)
    print(f"💰 Total Cost: ${total_cost:,.2f} AUD")
    print(f"🔨 Material Cost: ${material_cost:,.2f} AUD")
    print(f"👷 Labor Cost: ${labor_cost:,.2f} AUD")
    
    if total_cost > 0:
        print(f"\n📊 Cost Breakdown:")
        print(f"   Materials: {(material_cost/total_cost)*100:.1f}%")
        print(f"   Labor: {(labor_cost/total_cost)*100:.1f}%")
        print(f"   Contingency: {((total_cost-material_cost-labor_cost)/total_cost)*100:.1f}%")
    
    # Step 6: Clean response for display
    print("\n📝 Step 6: Cleaning response for display...")
    clean_content = re.sub(r'\n\nCOST_DATA_JSON: \{[^}]+\}', '', response_content)
    print(f"✅ Response cleaned (removed embedded JSON)")
    
    # Step 7: Verify workflow success
    print("\n🏆 Step 7: Workflow Verification")
    print("=" * 40)
    
    success_checks = [
        ("Strands agent execution", result is not None),
        ("Response content extraction", len(response_content) > 0),
        ("Cost data parsing", total_cost > 0),
        ("Material cost parsing", material_cost > 0),
        ("Labor cost parsing", labor_cost > 0),
        ("Response cleaning", len(clean_content) > 0)
    ]
    
    all_passed = True
    for check_name, passed in success_checks:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {check_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 SUCCESS: Complete workflow is working perfectly!")
        print("The Streamlit UI should display proper cost metrics.")
        print(f"🌐 Access the UI at: http://localhost:8501")
    else:
        print("❌ FAILURE: Some workflow steps failed.")
        print("Check the individual steps above for issues.")
    
    return all_passed

if __name__ == "__main__":
    success = asyncio.run(test_full_workflow())
    sys.exit(0 if success else 1)
