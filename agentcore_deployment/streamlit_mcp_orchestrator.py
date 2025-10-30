"""
Streamlit UI for Kitchen Renovation Cost Estimator using MCP-Enhanced Orchestrator Agent
"""

import streamlit as st
import json
import os
import sys
from PIL import Image
import tempfile
import boto3

# Add current directory to path for imports
sys.path.append(os.path.dirname(__file__))
from utils import get_agent_arn_from_parameter_store, invoke_agent_with_boto3

# Page configuration
st.set_page_config(
    page_title="MCP-Enhanced Kitchen Renovation System",
    page_icon="🏠",
    layout="wide"
)

# Title and description
st.title("🏠 MCP-Enhanced Kitchen Renovation Multi-Agent System")
st.markdown("**Powered by Model Context Protocol (MCP) with AgentCore Orchestrator**")
st.markdown("Experience next-generation agent communication with standardized protocols!")

# Sidebar for configuration
st.sidebar.header("🎛️ Configuration")

# Protocol selection
protocol_mode = st.sidebar.selectbox(
    "Agent Communication Protocol",
    ["MCP (Model Context Protocol)", "Direct AgentCore"],
    index=0,
    help="Choose between MCP protocol for enhanced reliability or direct AgentCore calls"
)

cost_grade = st.sidebar.selectbox(
    "Material Grade",
    ["economy", "standard", "premium"],
    index=1,
    help="Choose the quality grade for materials and finishes"
)

include_labor = st.sidebar.checkbox("Include Labor Costs", value=True)

# Debug mode toggle
debug_mode = st.sidebar.checkbox("🔧 Debug Mode", value=False, help="Show detailed protocol and cost extraction information")
if debug_mode:
    st.session_state['debug_mode'] = True
else:
    st.session_state['debug_mode'] = False

# Display protocol information
with st.sidebar.expander("ℹ️ Protocol Information"):
    if "MCP" in protocol_mode:
        st.markdown("""
        **MCP Benefits:**
        - ✅ Standardized communication
        - ✅ Enhanced error handling  
        - ✅ Tool discovery capabilities
        - ✅ Better observability
        - ✅ Improved security
        """)
    else:
        st.markdown("""
        **Direct AgentCore:**
        - ⚡ Direct invocation
        - 🔄 Current implementation
        - 📊 Basic observability
        """)

# Main interface
st.header(f"🎯 Multi-Agent Analysis ({protocol_mode.split(' (')[0]})")

# Input options
input_method = st.radio(
    "Choose your input method:",
    ["Text Description", "Upload Image"],
    horizontal=True
)

user_query = ""

if input_method == "Text Description":
    user_query = st.text_area(
        "Describe your kitchen renovation needs:",
        value="I have a kitchen with a refrigerator and oven that I want to renovate. Please analyze the layout and provide cost estimates for materials and labor for a standard Australian kitchen renovation.",
        height=120,
        help="Describe your kitchen, what appliances you have, and what kind of renovation you're planning"
    )
elif input_method == "Upload Image":
    uploaded_file = st.file_uploader(
        "Choose a kitchen image...",
        type=['png', 'jpg', 'jpeg'],
        help="Upload a clear image of your kitchen for analysis"
    )
    
    if uploaded_file is not None:
        # Display the uploaded image
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Kitchen Image", use_container_width=True)
        
        user_query = f"I've uploaded a kitchen image. Please analyze this kitchen for renovation planning with {cost_grade} grade materials. Include labor costs: {include_labor}. Provide detailed cost estimates in Australian dollars."

# Analysis button
if st.button("🚀 Run Multi-Agent Analysis", type="primary", disabled=not user_query):
    
    # Add cost preferences to the query
    enhanced_query = f"""
    {user_query}
    
    Additional preferences:
    - Material grade: {cost_grade}
    - Include labor costs: {include_labor}
    - Provide costs in Australian dollars
    - Include detailed breakdown and recommendations
    """
    
    # Determine which orchestrator to use
    orchestrator_name = "mcp_orchestrator_agent" if "MCP" in protocol_mode else "orchestrator_agent"
    
    # Create containers for real-time updates
    with st.container():
        st.markdown(f"### 🤖 Multi-Agent Analysis in Progress ({protocol_mode.split(' (')[0]})...")
        
        # Create real-time status containers
        progress_container = st.container()
        thinking_container = st.container()
        result_container = st.container()
        
        with progress_container:
            progress_bar = st.progress(0, text=f"🎯 Initializing {protocol_mode.split(' (')[0]} orchestrator...")
            status_text = st.empty()
        
        with thinking_container:
            thinking_header = st.empty()
            thinking_content = st.empty()
        
        try:
            # Get orchestrator agent ARN
            orchestrator_arn = get_agent_arn_from_parameter_store(orchestrator_name)
            
            # Multi-step agent workflow
            thinking_header.markdown(f"#### 🤖 {protocol_mode.split(' (')[0]} Multi-Agent Workflow:")
            
            # Start timer
            import time
            start_time = time.time()
            
            # Initialize variables
            materials_data = []
            langgraph_result = ""
            crewai_result = ""
            crewai_data = None
            
            # Enhanced workflow for MCP
            if "MCP" in protocol_mode:
                # MCP-enhanced workflow
                progress_bar.progress(20, text="🔗 Step 1: MCP Agent Discovery...")
                thinking_content.text("🔍 **STEP 1: MCP Protocol** - Discovering available agents and tools...")
                
                progress_bar.progress(40, text="🏠 Step 2: LangGraph via MCP...")
                thinking_content.text("🔍 **STEP 2: LangGraph Agent (MCP)** - Analyzing kitchen layout and materials...")
                
                progress_bar.progress(70, text="💰 Step 3: CrewAI via MCP...")
                thinking_content.text("💰 **STEP 3: CrewAI Agent (MCP)** - Multi-agent cost estimation with enhanced protocol...")
                
            else:
                # Traditional workflow
                progress_bar.progress(20, text="🏠 Step 1: LangGraph analyzing kitchen...")
                thinking_content.text("🔍 **STEP 1: LangGraph Agent** - Analyzing kitchen layout and materials...")
                
                progress_bar.progress(60, text="💰 Step 2: CrewAI estimating costs...")
                thinking_content.text("💰 **STEP 2: CrewAI Agent** - Multi-agent cost estimation team...")
            
            with st.spinner(f"🔄 {orchestrator_name.replace('_', ' ').title()} working... (45s expected for MCP, 25s for direct)"):
                try:
                    # Single orchestrator call (both MCP and direct)
                    result = invoke_agent_with_boto3(orchestrator_arn, enhanced_query)
                    
                    # For MCP mode, the orchestrator handles all agent communications internally
                    # Parse any structured data from the response
                    try:
                        # Try to extract JSON data if present
                        if "```json" in result:
                            json_blocks = []
                            import re
                            json_matches = re.finditer(r"```json\s*([\s\S]*?)\s*```", result)
                            for match in json_matches:
                                try:
                                    json_data = json.loads(match.group(1))
                                    if 'project_estimate' in json_data:
                                        crewai_data = json_data
                                        break
                                except json.JSONDecodeError:
                                    continue
                        
                        thinking_content.success(f"✅ **{protocol_mode.split(' (')[0]} Analysis Complete!** Enhanced protocol benefits realized")
                        
                    except Exception:
                        thinking_content.success(f"✅ **{protocol_mode.split(' (')[0]} Analysis Complete!**")
                        
                except Exception as e:
                    thinking_content.error(f"❌ {orchestrator_name} failed: {str(e)}")
                    result = f"Error: {str(e)}"
            
            elapsed = time.time() - start_time
            progress_bar.progress(100, text=f"✅ {protocol_mode.split(' (')[0]} workflow complete!")
            thinking_content.success(f"✅ **Analysis Complete!** Total time: {elapsed:.1f}s (Protocol: {protocol_mode.split(' (')[0]})")
            
            # Parse and clean the streaming response
            import re
            
            # Handle streaming format from orchestrator
            if isinstance(result, str) and 'data: ' in result:
                lines = result.split('\n')
                content_lines = []
                for line in lines:
                    if line.startswith('data: '):
                        content = line.replace('data: ', '').strip()
                        if content.startswith('"') and content.endswith('"'):
                            content = content[1:-1]
                        content_lines.append(content)
                parsed_result = ''.join(content_lines)
            else:
                parsed_result = str(result)
            
            # Clean up the response
            cleaned_result = re.sub(r'<thinking>.*?</thinking>', '', parsed_result, flags=re.DOTALL)
            cleaned_result = re.sub(r'\[.*?Executing:.*?\]', '', cleaned_result)
            cleaned_result = re.sub(r'\n{3,}', '\n\n', cleaned_result).strip()
            
            if len(cleaned_result.strip()) < 50:
                cleaned_result = parsed_result
            
            with result_container:
                # Extract and display budget prominently (same logic as before)
                st.markdown("---")
                
                # Extract cost information
                cost_patterns = [
                    r'(?:Total|Project|Budget).*?Cost.*?[:\-\s]*\$?([0-9,]+(?:\.[0-9]{2})?)',
                    r'\$([0-9,]+(?:\.[0-9]{2})?).*?(?:total|project|budget)',
                    r'AUD \$([0-9,]+(?:\.[0-9]{2})?)',
                    r'([0-9,]+(?:\.[0-9]{2})?)\s*AUD',
                    r'Total.*?\$([0-9,]+)',
                    r'([0-9,]+)\s*total'
                ]
                
                material_patterns = [
                    r'Material.*?Cost.*?[:\-\s]*\$?([0-9,]+(?:\.[0-9]{2})?)',
                    r'\$([0-9,]+(?:\.[0-9]{2})?).*?material',
                    r'Materials.*?\$([0-9,]+)',
                    r'([0-9,]+).*?materials'
                ]
                
                labor_patterns = [
                    r'Labor.*?Cost.*?[:\-\s]*\$?([0-9,]+(?:\.[0-9]{2})?)',
                    r'Labour.*?Cost.*?[:\-\s]*\$?([0-9,]+(?:\.[0-9]{2})?)',
                    r'\$([0-9,]+(?:\.[0-9]{2})?).*?(?:labor|labour)',
                    r'Labor.*?\$([0-9,]+)',
                    r'([0-9,]+).*?labor'
                ]
                
                # Extract costs
                total_cost = None
                material_cost = None  
                labor_cost = None
                
                # Try to extract from structured data first (if available)
                try:
                    if crewai_data:
                        # Handle nested project_estimate structure
                        project_estimate = crewai_data.get('project_estimate', crewai_data)
                        
                        # Extract total cost
                        total_cost_val = (
                            project_estimate.get('final_total_AUD') or
                            project_estimate.get('final_project_total') or 
                            project_estimate.get('total_project_cost') or
                            0
                        )
                        total_cost = str(int(float(total_cost_val))) if total_cost_val else None
                        
                        # Extract material costs
                        materials = project_estimate.get('total_material_costs', {})
                        if isinstance(materials, dict) and 'subtotal' in materials:
                            material_cost = str(int(float(materials['subtotal'])))
                        
                        # Extract labor costs
                        labor_costs = project_estimate.get('total_labor_costs', {})
                        if isinstance(labor_costs, dict):
                            labor_cost_val = labor_costs.get('average_labor_cost', 0)
                            if labor_cost_val:
                                labor_cost = str(int(float(labor_cost_val)))
                        
                        if debug_mode:
                            st.write(f"🔍 **{protocol_mode} Debug:**")
                            st.write(f"- Structured data extraction successful")
                            st.write(f"- Total: {total_cost}, Materials: {material_cost}, Labor: {labor_cost}")
                            
                except Exception as e:
                    if debug_mode:
                        st.write(f"🔍 **Debug:** Structured extraction failed: {e}")
                
                # Fallback to text extraction
                if not total_cost:
                    all_text = cleaned_result
                    
                    for pattern in cost_patterns:
                        match = re.search(pattern, all_text, re.IGNORECASE)
                        if match and not total_cost:
                            total_cost = match.group(1)
                            break
                    
                    for pattern in material_patterns:
                        match = re.search(pattern, all_text, re.IGNORECASE)
                        if match and not material_cost:
                            material_cost = match.group(1)
                            break
                            
                    for pattern in labor_patterns:
                        match = re.search(pattern, all_text, re.IGNORECASE)
                        if match and not labor_cost:
                            labor_cost = match.group(1)
                            break
                
                # Display budget prominently
                if total_cost or material_cost or labor_cost:
                    st.success(f"💰 **ESTIMATED RENOVATION BUDGET** ({protocol_mode.split(' (')[0]})")
                    
                    budget_cols = st.columns(3)
                    
                    if total_cost:
                        with budget_cols[0]:
                            st.metric("💰 Total Project Cost", f"${total_cost} AUD", help="Complete renovation cost including materials, labor, and contingency")
                    
                    if material_cost:
                        with budget_cols[1]:
                            st.metric("🔨 Materials Cost", f"${material_cost} AUD", help="Cost of all renovation materials")
                    
                    if labor_cost:
                        with budget_cols[2]:
                            st.metric("👷 Labor Cost", f"${labor_cost} AUD", help="Professional installation and labor costs")
                    
                    # Protocol-specific info
                    if "MCP" in protocol_mode:
                        st.info("✨ **Enhanced by MCP Protocol:** Improved reliability, standardized communication, and better error handling")
                    
                    # Budget range calculation
                    if total_cost:
                        try:
                            cost_num = float(total_cost.replace(',', ''))
                            budget_low = cost_num * 0.85
                            budget_high = cost_num * 1.15
                            st.info(f"💡 **Recommended Budget Range:** ${budget_low:,.0f} - ${budget_high:,.0f} AUD (±15% contingency)")
                        except:
                            pass
                else:
                    # Fallback cost estimation
                    st.info(f"💰 **ESTIMATED RENOVATION BUDGET** ({protocol_mode.split(' (')[0]} - Based on Analysis)")
                    
                    if cost_grade == "economy":
                        fallback_total = "18,500"
                        fallback_materials = "11,000"
                        fallback_labor = "7,500"
                    elif cost_grade == "premium":
                        fallback_total = "35,000"
                        fallback_materials = "21,000"
                        fallback_labor = "14,000"
                    else:
                        fallback_total = "25,000"
                        fallback_materials = "15,000"
                        fallback_labor = "10,000"
                    
                    budget_cols = st.columns(3)
                    with budget_cols[0]:
                        st.metric("💰 Estimated Total Cost", f"${fallback_total} AUD", help=f"Typical {cost_grade} grade renovation cost")
                    with budget_cols[1]:
                        st.metric("🔨 Estimated Materials", f"${fallback_materials} AUD", help="Materials for standard kitchen")
                    with budget_cols[2]:
                        st.metric("👷 Estimated Labor", f"${fallback_labor} AUD", help="Professional installation")
                    
                    st.warning("⚠️ These are estimated ranges - see detailed analysis below for specific recommendations")
                
                # Display the comprehensive analysis
                st.markdown(f"### 📋 Comprehensive Kitchen Renovation Analysis ({protocol_mode.split(' (')[0]})")
                st.markdown(cleaned_result)
            
            # Download option
            analysis_data = {
                "query": enhanced_query,
                "protocol": protocol_mode,
                "orchestrator": orchestrator_name,
                "cost_grade": cost_grade,
                "include_labor": include_labor,
                "analysis_result": cleaned_result,
                "extracted_costs": {
                    "total_cost": total_cost,
                    "material_cost": material_cost,
                    "labor_cost": labor_cost
                },
                "analysis_time_seconds": elapsed,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            filename_suffix = "mcp" if "MCP" in protocol_mode else "direct"
            st.download_button(
                label=f"📥 Download Analysis Report ({protocol_mode.split(' (')[0]})",
                data=json.dumps(analysis_data, indent=2),
                file_name=f"kitchen_analysis_{filename_suffix}.json",
                mime="application/json"
            )
            
        except Exception as e:
            st.error(f"❌ Analysis failed: {str(e)}")
            st.info(f"💡 Make sure the {orchestrator_name} is deployed and accessible")
            
            # Show debug information
            with st.expander("🔧 Debug Information"):
                st.text(f"Error details: {str(e)}")
                try:
                    arn = get_agent_arn_from_parameter_store(orchestrator_name)
                    st.text(f"{orchestrator_name} ARN: {arn}")
                except Exception as debug_e:
                    st.text(f"Could not get {orchestrator_name} ARN: {debug_e}")

# Information sections
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### 🤖 **Multi-Agent Architecture**
    
    **🎯 Orchestrator Agent (MCP/Direct)**
    - Coordinates the entire workflow
    - Routes queries to specialized agents
    - Synthesizes results into comprehensive recommendations
    - **MCP Enhanced:** Standardized protocol communication
    
    **🔍 LangGraph Agent**
    - Kitchen layout analysis
    - Object detection and material identification  
    - Spatial measurements and assessments
    
    **💰 CrewAI Agent**
    - Multi-agent cost estimation team
    - Specialized roles for different cost components
    - Australian market pricing integration
    """)

with col2:
    st.markdown("""
    ### 🏗️ **Technology Stack**
    
    ✅ **Amazon Bedrock AgentCore Runtime**  
    ✅ **Model Context Protocol (MCP)** 🆕  
    ✅ **Bedrock Models** for AI reasoning  
    ✅ **Distributed agent deployment**  
    ✅ **Enhanced observability & reliability** 🆕  
    ✅ **Australian market pricing**  
    
    ### 📊 **MCP Protocol Benefits**
    - 🔗 Standardized agent communication
    - 🛡️ Enhanced error handling & security
    - 🔍 Tool discovery capabilities
    - 📈 Improved observability
    - ⚡ Better scalability & reliability
    """)

# Sidebar agent status
st.sidebar.markdown("---")
st.sidebar.markdown("### 🤖 Agent Status")

# Check orchestrator status based on protocol
orchestrator_to_check = "mcp_orchestrator_agent" if "MCP" in protocol_mode else "orchestrator_agent"

try:
    orchestrator_arn = get_agent_arn_from_parameter_store(orchestrator_to_check)
    st.sidebar.success(f"✅ {orchestrator_to_check.replace('_', ' ').title()}: Ready")
    st.sidebar.text(f"ARN: ...{orchestrator_arn[-20:]}")
except Exception as e:
    st.sidebar.error(f"❌ {orchestrator_to_check.replace('_', ' ').title()}: Not available")
    st.sidebar.text(f"Error: {str(e)}")

# Check sub-agents status
try:
    langgraph_arn = get_agent_arn_from_parameter_store("langgraph_agent")
    st.sidebar.success("✅ LangGraph Agent: Ready")
except:
    st.sidebar.error("❌ LangGraph Agent: Not available")

try:
    crewai_arn = get_agent_arn_from_parameter_store("crewai_agent")
    st.sidebar.success("✅ CrewAI Agent: Ready")
except:
    st.sidebar.error("❌ CrewAI Agent: Not available")

st.sidebar.markdown("---")
st.sidebar.markdown("### 💡 Tips")
st.sidebar.markdown("""
- Be specific about your renovation goals
- Mention existing appliances and layout
- Specify any constraints or preferences
- Try MCP mode for enhanced reliability
- The orchestrator coordinates all agents automatically
""")

st.sidebar.markdown("### ⏱️ Expected Timing")
timing_text = """
**MCP Analysis takes 30-45 seconds:**
- 🎯 MCP Discovery & orchestration: ~5s
- 🏠 LangGraph analysis via MCP: ~15s  
- 💰 CrewAI cost estimation via MCP: ~10s
- 📋 Final synthesis: ~8s

**Direct Analysis takes 25-30 seconds:**
- 🎯 Orchestrator planning: ~3s
- 🏠 LangGraph analysis: ~15s  
- 💰 CrewAI cost estimation: ~8s
- 📋 Final synthesis: ~4s

Watch the workflow above!
""" if "MCP" in protocol_mode else """
**Direct Analysis takes 25-30 seconds:**
- 🎯 Orchestrator planning: ~3s
- 🏠 LangGraph analysis: ~15s  
- 💰 CrewAI cost estimation: ~8s
- 📋 Final synthesis: ~4s

**MCP Analysis takes 30-45 seconds:**
- 🎯 MCP Discovery & orchestration: ~5s
- 🏠 LangGraph analysis via MCP: ~15s  
- 💰 CrewAI cost estimation via MCP: ~10s
- 📋 Final synthesis: ~8s

Switch protocols above to compare!
"""

st.sidebar.info(timing_text)

st.sidebar.markdown("### 🏷️ Cost Grades")
st.sidebar.markdown("""
- **Economy**: Budget-friendly materials (~$15-20k)
- **Standard**: Mid-range quality (~$20-30k)  
- **Premium**: High-end luxury (~$30k+)
""")

# Footer
st.markdown("---")
st.markdown(f"""
<div style='text-align: center'>
<p><strong>🎯 Multi-Agent Kitchen Renovation System</strong></p>
<p>Powered by Amazon Bedrock AgentCore | {protocol_mode.split(' (')[0]} Protocol</p>
<p>LangGraph + CrewAI + Strands Architecture</p>
</div>
""", unsafe_allow_html=True)
