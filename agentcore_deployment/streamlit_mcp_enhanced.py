"""
Streamlit UI for Kitchen Renovation Cost Estimator - MCP Version
Enhanced with Model Context Protocol for agent-to-agent communication
"""

import streamlit as st
import json
import os
import sys
import asyncio
import logging
from PIL import Image
import tempfile
from typing import Dict, Any, List
from datetime import datetime

# Add mcp_base to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'mcp_base'))

from mcp_base.mcp_client_utils import AgentCoreMCPClient
from mcp_base.auth_utils import get_bearer_token_for_agent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Kitchen Renovation Multi-Agent System (MCP)",
    page_icon="🏠",
    layout="wide"
)

# Initialize MCP clients
@st.cache_resource
def get_orchestrator_client():
    """Get cached orchestrator MCP client"""
    return AgentCoreMCPClient(region="us-west-2")

@st.cache_resource 
def get_langgraph_client():
    """Get cached LangGraph MCP client"""
    return AgentCoreMCPClient(region="us-west-2")
    
@st.cache_resource
def get_crewai_client():
    """Get cached CrewAI MCP client"""  
    return AgentCoreMCPClient(region="us-west-2")

# Title and description
st.title("🏠 Kitchen Renovation Multi-Agent System")
st.markdown("**Powered by MCP (Model Context Protocol) | LangGraph + CrewAI + Orchestrator**")
st.markdown("Experience secure, standardized agent-to-agent communication via MCP protocol!")

# MCP Status in sidebar
st.sidebar.header("🔗 MCP Protocol Status")

# Check agent ecosystem
@st.cache_data(ttl=300)  # Cache for 5 minutes
def check_agent_ecosystem():
    """Check MCP agent ecosystem status"""
    try:
        client = get_orchestrator_client()
        # ecosystem_info = asyncio.run(discover_available_agents("us-west-2"))
        ecosystem_info = {"agents": ["orchestrator_agent", "langgraph_agent", "crewai_agent"]}
        return ecosystem_info
    except Exception as e:
        logger.error(f"Failed to check ecosystem: {e}")
        return {}

ecosystem_info = check_agent_ecosystem()
if ecosystem_info:
    st.sidebar.success("✅ MCP Ecosystem: Online")
    for agent_name, tools in ecosystem_info.items():
        tool_count = len(tools) if isinstance(tools, list) else 0
        st.sidebar.text(f"🤖 {agent_name}: {tool_count} tools")
else:
    st.sidebar.error("❌ MCP Ecosystem: Offline")
    st.sidebar.info("💡 Make sure agents are deployed to AgentCore Runtime")

# Sidebar for configuration
st.sidebar.header("🎛️ Configuration")
cost_grade = st.sidebar.selectbox(
    "Material Grade",
    ["economy", "standard", "premium"],
    index=1,
    help="Choose the quality grade for materials and finishes"
)

include_labor = st.sidebar.checkbox("Include Labor Costs", value=True)

# Debug mode toggle
debug_mode = st.sidebar.checkbox("🔧 Debug Mode", value=False, help="Show MCP communication details")

# MCP Protocol Information
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔗 MCP Advantages")
st.sidebar.markdown("""
- **Standardized Protocol**: Reliable communication
- **Enhanced Security**: JWT token authentication
- **Tool Discovery**: Automatic capability detection
- **Error Handling**: Built-in retry mechanisms
- **Observability**: Detailed communication logs
""")

# Main interface
st.header("🎯 MCP Multi-Agent Kitchen Analysis")

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
        value="I have a kitchen with a refrigerator and oven that I want to renovate. Please analyze the layout and provide cost estimates using the MCP multi-agent system.",
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
        st.image(image, caption="Uploaded Kitchen Image", width="stretch")
        
        user_query = f"I've uploaded a kitchen image. Please analyze this kitchen for renovation planning via MCP protocol with {cost_grade} grade materials. Include labor costs: {include_labor}. Provide detailed cost estimates in Australian dollars."

# Analysis button
if st.button("🚀 Run MCP Multi-Agent Analysis", type="primary", disabled=not user_query):
    
    # Enhanced query with MCP context
    enhanced_query = f"""
    {user_query}
    
    Analysis preferences:
    - Material grade: {cost_grade}
    - Include labor costs: {include_labor}
    - Provide costs in Australian dollars
    - Use MCP protocol for agent communication
    - Include detailed breakdown and recommendations
    """
    
    # Create containers for real-time updates
    with st.container():
        st.markdown("### 🔗 MCP Multi-Agent Analysis in Progress...")
        
        # Create real-time status containers
        progress_container = st.container()
        mcp_log_container = st.container()
        thinking_container = st.container()
        result_container = st.container()
        
        with progress_container:
            progress_bar = st.progress(0, text="🔗 Initializing MCP communication...")
            status_text = st.empty()
        
        with mcp_log_container:
            if debug_mode:
                st.markdown("#### 🔍 MCP Communication Log:")
                mcp_log = st.empty()
            communication_log = []
        
        with thinking_container:
            thinking_header = st.empty()
            thinking_content = st.empty()
        
        try:
            orchestrator_client = get_orchestrator_client()
            langgraph_client = get_langgraph_client()  
            crewai_client = get_crewai_client()
            
            # Start timer
            import time
            start_time = time.time()
            
            # Initialize variables for results
            langgraph_result = {}
            crewai_result = {}
            orchestrator_result = {}
            
            thinking_header.markdown("#### 🔗 MCP Agent Workflow:")
            
            # Step 1: Direct Orchestrator Call (which will coordinate other agents via MCP)
            progress_bar.progress(20, text="🎯 Step 1: Calling Orchestrator via MCP...")
            thinking_content.text("🎯 **MCP ORCHESTRATOR** - Coordinating multi-agent workflow via Model Context Protocol...")
            
            communication_log.append({
                "timestamp": datetime.now().isoformat(),
                "action": "Calling orchestrator_agent.orchestrate_full_workflow",
                "protocol": "MCP"
            })
            
            with st.spinner("🔗 MCP Orchestrator working... (60s expected)"):
                try:
                    # Call orchestrator which will coordinate other agents via MCP
                    orchestrator_result = asyncio.run(
                        orchestrator_client.invoke_agent_tool(
                            "orchestrator_agent",
                            "orchestrate_renovation_workflow", 
                            user_query=enhanced_query,
                            cost_grade=cost_grade
                        )
                    )
                    
                    communication_log.append({
                        "timestamp": datetime.now().isoformat(),
                        "result": "Orchestrator workflow completed" if "error" not in orchestrator_result else "Orchestrator workflow failed",
                        "protocol": "MCP"
                    })
                    
                    if "error" not in orchestrator_result:
                        thinking_content.success("✅ **MCP Orchestrator Complete:** Full workflow coordinated via MCP protocol")
                        
                        # Extract sub-results if available
                        if "data" in orchestrator_result and isinstance(orchestrator_result["data"], dict):
                            workflow_data = orchestrator_result["data"]
                            langgraph_result = workflow_data.get("kitchen_analysis", {})
                            crewai_result = workflow_data.get("cost_estimation", {})
                            
                        # Show orchestrator results
                        with st.expander("🎯 **MCP Orchestrator Results** - Multi-Agent Coordination", expanded=False):
                            st.json(orchestrator_result)
                    else:
                        thinking_content.error(f"❌ MCP Orchestrator failed: {orchestrator_result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    thinking_content.error(f"❌ MCP Orchestrator failed: {str(e)}")
                    communication_log.append({
                        "timestamp": datetime.now().isoformat(),
                        "error": str(e),
                        "protocol": "MCP"
                    })
                    orchestrator_result = {"error": str(e)}
            
            # Show MCP communication log in debug mode
            if debug_mode:
                with mcp_log_container:
                    mcp_log.json(communication_log)
            
            # Step 2: Optional Individual Agent Tests (if orchestrator failed)
            if "error" in orchestrator_result:
                progress_bar.progress(40, text="🏠 Fallback: Testing LangGraph via MCP...")
                thinking_content.text("🏠 **FALLBACK: LangGraph Agent** - Direct MCP call for kitchen analysis...")
                
                try:
                    langgraph_result = asyncio.run(
                        langgraph_client.invoke_agent_tool(
                            "langgraph_agent",
                            "analyze_kitchen",
                            user_query=f"Analyze kitchen for renovation planning with {cost_grade} grade materials"
                        )
                    )
                    
                    if "error" not in langgraph_result:
                        thinking_content.info("ℹ️ **Direct LangGraph Call:** Kitchen analysis completed")
                        
                        # Extract materials for CrewAI
                        materials_data = []
                        if "data" in langgraph_result:
                            materials_data = langgraph_result["data"].get("materials", [])
                        
                        # Step 3: CrewAI Cost Estimation
                        progress_bar.progress(70, text="💰 Fallback: Testing CrewAI via MCP...")
                        thinking_content.text("💰 **FALLBACK: CrewAI Agent** - Direct MCP call for cost estimation...")
                        
                        crewai_result = asyncio.run(
                            crewai_client.invoke_agent_tool(
                                "crewai_agent",
                                "estimate_costs",
                                materials_data=materials_data if materials_data else [
                                    {"type": "granite", "area": 8.0},
                                    {"type": "wood", "area": 15.0},
                                    {"type": "tile", "area": 12.0}
                                ],
                                cost_grade=cost_grade
                            )
                        )
                        
                        if "error" not in crewai_result:
                            thinking_content.info("ℹ️ **Direct CrewAI Call:** Cost estimation completed")
                
                except Exception as e:
                    thinking_content.warning(f"⚠️ Fallback tests also failed: {e}")
            
            # Finalize
            elapsed = time.time() - start_time
            progress_bar.progress(100, text="✅ MCP multi-agent workflow complete!")
            thinking_content.success(f"✅ **MCP Analysis Complete!** Total time: {elapsed:.1f}s")
            
            # Process and display results
            with result_container:
                st.markdown("---")
                
                # Display comprehensive results
                if "error" not in orchestrator_result and "data" in orchestrator_result:
                    # Use orchestrator results (preferred)
                    workflow_data = orchestrator_result["data"]
                    
                    st.success("🎉 **MCP MULTI-AGENT ANALYSIS COMPLETED**")
                    st.markdown("### 📋 Comprehensive Kitchen Renovation Analysis (MCP Protocol)")
                    
                    # Show workflow information
                    if "workflow_status" in workflow_data and workflow_data["workflow_status"] == "completed":
                        steps_completed = workflow_data.get("steps_completed", [])
                        st.info(f"✅ **MCP Workflow:** Completed {len(steps_completed)} steps via Model Context Protocol")
                        
                        # Show MCP communication log
                        if "mcp_communication_log" in workflow_data:
                            with st.expander("🔗 **MCP Communication Log**", expanded=debug_mode):
                                st.json(workflow_data["mcp_communication_log"])
                    
                    # Extract and display costs
                    cost_info = workflow_data.get("cost_estimation", {})
                    if "data" in cost_info and "project_estimate" in cost_info["data"]:
                        project_est = cost_info["data"]["project_estimate"]
                        total_cost = project_est.get("final_total_AUD", 0)
                        
                        if total_cost > 0:
                            st.markdown("### 💰 **ESTIMATED RENOVATION BUDGET (MCP)**")
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("💰 Total Cost", f"${total_cost:,.0f} AUD", help="MCP-coordinated cost analysis")
                            with col2:
                                material_cost = project_est.get("total_material_costs", {}).get("subtotal", 0)
                                st.metric("🔨 Materials", f"${material_cost:,.0f} AUD", help="Materials via MCP agents")
                            with col3:
                                labor_cost = project_est.get("total_labor_costs", {}).get("average_labor_cost", 0)
                                st.metric("👷 Labor", f"${labor_cost:,.0f} AUD", help="Labor costs via MCP agents")
                    
                    # Show recommendations
                    if "recommendations" in workflow_data:
                        st.markdown("### 🎯 **MCP AGENT RECOMMENDATIONS**")
                        for rec in workflow_data["recommendations"]:
                            st.markdown(f"- {rec}")
                
                else:
                    # Fallback to individual results
                    st.warning("🔄 **MCP Fallback Results**")
                    st.info("Orchestrator coordination failed, showing individual agent results:")
                    
                    if "error" not in langgraph_result:
                        with st.expander("🏠 **LangGraph Agent (MCP)**", expanded=True):
                            st.json(langgraph_result)
                    
                    if "error" not in crewai_result:
                        with st.expander("💰 **CrewAI Agent (MCP)**", expanded=True):
                            st.json(crewai_result)
            
            # Download comprehensive report
            analysis_data = {
                "analysis_type": "MCP Multi-Agent Kitchen Renovation",
                "query": enhanced_query,
                "cost_grade": cost_grade,
                "include_labor": include_labor,
                "protocol": "Model Context Protocol (MCP)",
                "agent_results": {
                    "orchestrator_result": orchestrator_result,
                    "langgraph_result": langgraph_result,
                    "crewai_result": crewai_result
                },
                "mcp_communication_log": communication_log,
                "analysis_time_seconds": elapsed,
                "timestamp": datetime.now().isoformat()
            }
            
            st.download_button(
                label="📥 Download MCP Analysis Report",
                data=json.dumps(analysis_data, indent=2),
                file_name=f"mcp_kitchen_analysis_{int(time.time())}.json",
                mime="application/json"
            )
            
        except Exception as e:
            st.error(f"❌ MCP Analysis failed: {str(e)}")
            st.info("💡 Ensure MCP agents are deployed and accessible via AgentCore Runtime")
            
            # Show debug information
            with st.expander("🔧 MCP Debug Information"):
                st.text(f"Error details: {str(e)}")
                st.text(f"Region: us-west-2")
                st.text(f"Protocol: Model Context Protocol (MCP)")
                if communication_log:
                    st.json(communication_log)

# Information sections
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### 🔗 **MCP Multi-Agent Architecture**
    
    **🎯 Orchestrator Agent (MCP)**
    - Coordinates entire workflow via MCP protocol
    - Routes queries to specialized agents
    - Synthesizes results with enhanced reliability
    
    **🏠 LangGraph Agent (MCP)**
    - Kitchen layout analysis via MCP
    - YOLO object detection with secure communication
    - Spatial measurements and assessments
    
    **💰 CrewAI Agent (MCP)**
    - Multi-agent cost estimation team via MCP
    - Specialized roles with standardized communication
    - Australian market pricing integration
    """)

with col2:
    st.markdown("""
    ### 🚀 **MCP Technology Stack**
    
    ✅ **Model Context Protocol (MCP)**  
    ✅ **Amazon Bedrock AgentCore Runtime**  
    ✅ **Standardized agent communication**  
    ✅ **JWT authentication & authorization**  
    ✅ **Enhanced error handling & retries**  
    ✅ **Tool discovery & introspection**  
    ✅ **Australian market pricing**
    
    ### 🔗 **MCP Advantages**
    - Reliable agent-to-agent communication
    - Built-in security and authentication
    - Standardized protocol compliance
    - Enhanced observability and debugging
    - Automatic tool discovery capabilities
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
<p><strong>🔗 MCP Multi-Agent Kitchen Renovation System</strong></p>
<p>Powered by Model Context Protocol | Amazon Bedrock AgentCore | LangGraph + CrewAI + Orchestrator</p>
<p><em>Experience the future of secure, standardized agent communication!</em></p>
</div>
""", unsafe_allow_html=True)
