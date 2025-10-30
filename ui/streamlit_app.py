"""
Streamlit UI for Kitchen Renovation Cost Estimator
Multi-Agent Analysis with LangGraph, CrewAI, and Strands
"""

import streamlit as st
import asyncio
import json
import re
import os
import sys
from PIL import Image
import tempfile

# Add current directory and project root to path for imports
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import our Strands agent
from strands_agent.kitchen_strands_agent import (
    analyze_kitchen_comprehensive, 
    KitchenAnalysisRequest,
    kitchen_agent
)

# Page configuration
st.set_page_config(
    page_title="Kitchen Renovation Cost Estimator",
    page_icon="🏠",
    layout="wide"
)

# Title and description
st.title("🏠 Kitchen Renovation Cost Estimator")
st.markdown("**Multi-Agent AI Analysis using LangGraph, CrewAI & Strands with Amazon Bedrock**")

# Sidebar for configuration
st.sidebar.header("Configuration")
cost_grade = st.sidebar.selectbox(
    "Material Grade",
    ["economy", "standard", "premium"],
    index=1
)

include_labor = st.sidebar.checkbox("Include Labor Costs", value=True)

# Main interface
col1, col2 = st.columns([1, 1])

with col1:
    st.header("📸 Upload Kitchen Image")
    
    uploaded_file = st.file_uploader(
        "Choose a kitchen image...",
        type=['png', 'jpg', 'jpeg'],
        help="Upload a clear image of your kitchen for analysis"
    )
    
    if uploaded_file is not None:
        # Display the uploaded image
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Kitchen Image", use_container_width=True)
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
            image.save(tmp_file.name)
            temp_image_path = tmp_file.name

with col2:
    st.header("🤖 AI Analysis Results")
    
    if uploaded_file is not None:
        if st.button("🚀 Analyze Kitchen & Estimate Costs", type="primary"):
            
            with st.spinner("🔍 Running multi-agent analysis..."):
                try:
                    # Create analysis request
                    request = KitchenAnalysisRequest(
                        image_path=temp_image_path,
                        cost_grade=cost_grade,
                        include_labor=include_labor
                    )
                    
                    # Run the Strands agent analysis
                    with st.status("Running AI Analysis...", expanded=True) as status:
                        st.write("🔍 LangGraph: YOLO detection + Bedrock analysis...")
                        st.write("💰 CrewAI: Multi-agent cost estimation...")
                        st.write("🎯 Strands: Orchestrating comprehensive analysis...")
                        
                        # Run async analysis
                        result = asyncio.run(analyze_kitchen_comprehensive(request))
                        
                        status.update(label="✅ Analysis Complete!", state="complete")
                    
                    # Display results
                    st.success("🎉 Analysis Complete!")
                    
                    # Extract response content
                    response_content = result.summary.get('strands_response', '')
                    
                    # Use LLM-based cost extraction for robust parsing
                    try:
                        # Import the LLM cost extractor
                        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
                        from llm_cost_extractor import extract_costs_with_llm
                        
                        # Combine all available text for LLM analysis
                        combined_analysis = response_content or ""
                        try:
                            # Include structured data if available
                            if hasattr(result, 'cost_estimates'):
                                combined_analysis += f"\n\nStructured Data: {json.dumps(result.cost_estimates, indent=2)}"
                            combined_analysis += f"\n\nFull Analysis: {json.dumps(result.dict(), indent=2)}"
                        except Exception:
                            pass
                        
                        # Use LLM to extract costs
                        with st.spinner("🤖 Extracting cost information with AI..."):
                            extracted_costs = extract_costs_with_llm(combined_analysis)
                        
                        # Get cost strings (supporting ranges)
                        total_cost_str = extracted_costs.total_cost
                        material_cost_str = extracted_costs.material_cost  
                        labor_cost_str = extracted_costs.labor_cost
                        contingency_cost_str = extracted_costs.contingency_cost
                        cost_per_sqm_str = extracted_costs.cost_per_sqm
                        budget_range_str = extracted_costs.budget_range
                        has_valid_costs = extracted_costs.has_valid_costs
                        
                    except Exception as e:
                        # Fallback to basic display
                        st.warning(f"⚠️ LLM cost extraction failed: {str(e)}")
                        total_cost_str = "$0 AUD"
                        material_cost_str = "$0 AUD" 
                        labor_cost_str = "$0 AUD"
                        contingency_cost_str = "$0 AUD"
                        cost_per_sqm_str = "$0 AUD"
                        budget_range_str = "$0 - $0 AUD"
                        has_valid_costs = False
                    
                    # Debug information for troubleshooting
                    with st.sidebar:
                        with st.expander("🔍 Debug Cost Extraction", expanded=False):
                            st.write(f"**LLM Extracted Costs:**")
                            st.write(f"- Total: {total_cost_str}")
                            st.write(f"- Material: {material_cost_str}")
                            st.write(f"- Labor: {labor_cost_str}")
                            st.write(f"- Contingency: {contingency_cost_str}")
                            st.write(f"- Cost per m²: {cost_per_sqm_str}")
                            st.write(f"- Budget Range: {budget_range_str}")
                            st.write(f"**Has Valid Costs:** {has_valid_costs}")
                            st.write(f"**Response Length:** {len(response_content) if response_content else 0} chars")
                            if response_content:
                                # Show snippet for debugging
                                snippet = response_content[:1000] + "..." if len(response_content) > 1000 else response_content
                                st.text_area("Response snippet:", snippet, height=100)
                    
                    # Display metrics with string-based costs (supporting ranges)
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("💰 Total Cost", total_cost_str)
                    with col2:
                        st.metric("🔨 Material Cost", material_cost_str)
                    with col3:
                        st.metric("👷 Labor Cost", labor_cost_str)
                    
                    # Additional metrics row
                    col4, col5 = st.columns(2)
                    with col4:
                        st.metric("🏗️ Contingency", contingency_cost_str)
                    with col5:
                        st.metric("📐 Cost per m²", cost_per_sqm_str)
                    
                    # Budget range as a prominent callout
                    if budget_range_str and budget_range_str != "$0 - $0 AUD":
                        st.info(f"💡 **Recommended Budget Range:** {budget_range_str}")
                    
                    # Show success message with key metrics
                    if has_valid_costs:
                        st.success(f"✅ Analysis Complete! Total renovation cost: {total_cost_str}")
                    else:
                        st.warning("⚠️ Cost data not found in response. Check analysis below.")
                    
                    # Display full analysis (clean version without embedded JSON)
                    st.subheader("📋 Comprehensive Analysis Report")
                    if response_content:
                        # Remove the embedded JSON from display
                        clean_content = re.sub(r'\n\nCOST_DATA_JSON: \{[^}]+\}', '', response_content)
                        st.text_area(
                            "Full Analysis",
                            clean_content,
                            height=400,
                            help="Complete multi-agent analysis report"
                        )
                    else:
                        st.error("❌ No analysis content received")
                    
                    # Download option
                    st.download_button(
                        label="📥 Download Analysis Report",
                        data=json.dumps(result.dict(), indent=2),
                        file_name=f"kitchen_analysis_{result.timestamp}.json",
                        mime="application/json"
                    )
                    
                    # Clean up temp file
                    os.unlink(temp_image_path)
                    
                except Exception as e:
                    st.error(f"❌ Analysis failed: {str(e)}")
                    st.info("💡 Make sure AWS Bedrock is configured and accessible")
    else:
        st.info("👆 Upload a kitchen image to start the analysis")

# Footer with information
st.markdown("---")
st.markdown("""
### 🔧 **Technology Stack**
- **LangGraph**: YOLO object detection + Bedrock AI analysis
- **CrewAI**: Multi-agent cost estimation (Materials Expert, Labor Analyst, Cost Synthesizer)  
- **Strands**: Agent orchestration and comprehensive reporting
- **Amazon Bedrock**: Bedrock  for AI reasoning
- **Australian Pricing**: Real market rates in AUD per square metre

### 📊 **Analysis Features**
✅ Real computer vision object detection  
✅ Multi-agent AI reasoning with Bedrock  
✅ Australian market pricing  
✅ Material identification and area calculation  
✅ Labor cost estimation  
✅ Comprehensive renovation recommendations  
""")

# Sidebar information
st.sidebar.markdown("---")
st.sidebar.markdown("### 💡 Tips")
st.sidebar.markdown("""
- Use clear, well-lit kitchen photos
- Include cabinets, countertops, and appliances
- Avoid cluttered or partial views
- Standard grade provides balanced cost/quality
""")

st.sidebar.markdown("### 🏷️ Cost Grades")
st.sidebar.markdown("""
- **Economy**: Budget-friendly materials
- **Standard**: Mid-range quality (recommended)
- **Premium**: High-end luxury materials
""")
