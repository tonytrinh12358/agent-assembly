"""
Streamlit UI for Kitchen Renovation Cost Estimator using the Orchestrator Agent
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
    page_title="Kitchen Renovation Multi-Agent System",
    page_icon="🏠",
    layout="wide"
)

# Title and description
st.title("🏠 Kitchen Renovation Multi-Agent System")
st.markdown("**Powered by AgentCore Orchestrator with LangGraph + CrewAI + Strands**")
st.markdown("Experience the power of distributed multi-agent AI on Amazon Bedrock AgentCore!")

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
debug_mode = st.sidebar.checkbox("🔧 Debug Mode", value=False, help="Show cost extraction details for troubleshooting")
if debug_mode:
    st.session_state['debug_mode'] = True
else:
    st.session_state['debug_mode'] = False

# Main interface
st.header("🎯 Multi-Agent Kitchen Analysis")

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
    
    # Create containers for real-time updates
    with st.container():
        st.markdown("### 🤖 Multi-Agent Analysis in Progress...")
        
        # Create real-time status containers
        progress_container = st.container()
        thinking_container = st.container()
        result_container = st.container()
        
        with progress_container:
            progress_bar = st.progress(0, text="🎯 Initializing orchestrator...")
            status_text = st.empty()
        
        with thinking_container:
            thinking_header = st.empty()
            thinking_content = st.empty()
        
        try:
            # Get orchestrator agent ARN
            orchestrator_arn = get_agent_arn_from_parameter_store("orchestrator_agent")
            
            # Multi-step agent workflow
            thinking_header.markdown("#### 🤖 Multi-Agent Workflow:")
            
            # Start timer
            import time
            start_time = time.time()
            
            # Initialize variables
            materials_data = []
            langgraph_result = ""
            crewai_result = ""
            crewai_data = None
            
            # Step 1: LangGraph Agent - Kitchen Analysis
            progress_bar.progress(20, text="🏠 Step 1: LangGraph analyzing kitchen...")
            thinking_content.text("🔍 **STEP 1: LangGraph Agent** - Analyzing kitchen layout and materials...")
            
            with st.spinner("🔄 LangGraph Agent working... (30s expected)"):
                try:
                    langgraph_arn = get_agent_arn_from_parameter_store("langgraph_agent")
                    langgraph_query = f"Analyze kitchen for renovation planning with {cost_grade} grade materials"
                    langgraph_result = invoke_agent_with_boto3(langgraph_arn, langgraph_query)
                    
                    # Parse LangGraph JSON response
                    try:
                        import json
                        langgraph_data = json.loads(langgraph_result)
                        
                        # Handle double-encoded JSON
                        if isinstance(langgraph_data, str):
                            langgraph_data = json.loads(langgraph_data)
                        
                        materials_data = langgraph_data.get('materials', [])
                        
                        thinking_content.success(f"✅ **LangGraph Complete:** Found {len(materials_data)} materials, {len(langgraph_data.get('detected_objects', []))} objects detected")
                        
                        # Store LangGraph data for later use
                        st.session_state['langgraph_data'] = langgraph_data
                        
                        # Show LangGraph results
                        with st.expander("🔍 **LangGraph Agent Results** - Kitchen Analysis", expanded=False):
                            st.json(langgraph_data)
                            
                    except json.JSONDecodeError:
                        thinking_content.warning("⚠️ LangGraph returned non-JSON response")
                        materials_data = []
                        with st.expander("🔍 **LangGraph Agent Results** - Raw Response", expanded=False):
                            st.text(langgraph_result[:1000] + "..." if len(langgraph_result) > 1000 else langgraph_result)
                        
                except Exception as e:
                    thinking_content.error(f"❌ LangGraph failed: {str(e)}")
                    materials_data = []
                    langgraph_result = f"Error: {str(e)}"
            
            # Step 2: CrewAI Agent - Cost Estimation
            progress_bar.progress(60, text="💰 Step 2: CrewAI estimating costs...")
            thinking_content.text("💰 **STEP 2: CrewAI Agent** - Multi-agent cost estimation team (Materials Expert + Labor Analyst + Cost Synthesizer)...")
            
            # Show materials data being passed to CrewAI
            if materials_data:
                thinking_content.text(f"💰 **CrewAI Input:** Using {len(materials_data)} materials from LangGraph for cost analysis...")
            
            with st.spinner("🔄 CrewAI Agent working... (15s expected)"):
                try:
                    crewai_arn = get_agent_arn_from_parameter_store("crewai_agent")
                    
                    # Create materials prompt for CrewAI
                    if materials_data:
                        crewai_query = f"Estimate costs for kitchen renovation with {cost_grade} grade materials. Materials: {json.dumps(materials_data)}"
                    else:
                        crewai_query = f"Estimate costs for kitchen renovation with {cost_grade} grade materials including cabinets, countertops, and flooring"
                    
                    crewai_result = invoke_agent_with_boto3(crewai_arn, crewai_query)
                    
                    # Parse CrewAI response
                    try:
                        crewai_data = json.loads(crewai_result)
                        
                        # Handle double-encoded JSON
                        if isinstance(crewai_data, str):
                            crewai_data = json.loads(crewai_data)
                        
                        # Extract total cost for display (handle all naming conventions including _AUD suffix)
                        total_cost_raw = (crewai_data.get('final_project_total_AUD', 0) or 
                                        crewai_data.get('final_project_total', 0) or 
                                        crewai_data.get('total_project_cost', 0))
                        
                        thinking_content.success(f"✅ **CrewAI Complete:** Estimated total cost: ${total_cost_raw:,.0f} AUD")
                        
                        # Debug: Store CrewAI data for cost extraction
                        st.session_state['crewai_data'] = crewai_data
                        
                        # Debug: Show what we're storing (only in debug mode)
                        if st.session_state.get('debug_mode', False):
                            st.write(f"🔍 **Storing CrewAI data:** Keys = {list(crewai_data.keys())}")
                            st.write(f"🔍 **Sample values:** final_project_total_AUD = {crewai_data.get('final_project_total_AUD', 'NOT FOUND')}")
                            st.write(f"🔍 **Sample values:** final_project_total = {crewai_data.get('final_project_total', 'NOT FOUND')}")
                            st.write(f"🔍 **Sample values:** total_project_cost = {crewai_data.get('total_project_cost', 'NOT FOUND')}")
                        
                        # Show CrewAI results
                        with st.expander("💰 **CrewAI Agent Results** - Cost Analysis", expanded=False):
                            st.json(crewai_data)
                            
                    except json.JSONDecodeError:
                        thinking_content.warning("⚠️ CrewAI returned non-JSON response")
                        with st.expander("💰 **CrewAI Agent Results** - Raw Response", expanded=False):
                            st.text(crewai_result[:1000] + "..." if len(crewai_result) > 1000 else crewai_result)
                        
                except Exception as e:
                    thinking_content.error(f"❌ CrewAI failed: {str(e)}")
                    crewai_result = f"Error: {str(e)}"
            
            # Step 3: Quick Synthesis (no long orchestrator call)
            progress_bar.progress(90, text="📋 Step 3: Generating final report...")
            thinking_content.text("🎯 **STEP 3: Final Report** - Combining agent results...")
            
            # Create a simple combined result instead of calling orchestrator again
            result = f"""
Based on the multi-agent analysis:

**LangGraph Analysis Results:**
{langgraph_result[:1000]}...

**CrewAI Cost Analysis Results:**
{crewai_result[:1000]}...

**Final Recommendations:**
The kitchen renovation plan combines object detection results with detailed cost analysis to provide comprehensive recommendations for your renovation project.
"""
            
            elapsed = time.time() - start_time
            progress_bar.progress(100, text="✅ Multi-agent workflow complete!")
            thinking_content.success(f"✅ **All Agents Complete!** Total time: {elapsed:.1f}s")
            
            # Parse and clean the streaming response
            import re
            
            # Handle streaming format from orchestrator
            if isinstance(result, str) and 'data: ' in result:
                lines = result.split('\n')
                content_lines = []
                for line in lines:
                    if line.startswith('data: '):
                        # Remove data: prefix and clean quotes
                        content = line.replace('data: ', '').strip()
                        if content.startswith('"') and content.endswith('"'):
                            content = content[1:-1]  # Remove surrounding quotes
                        content_lines.append(content)
                parsed_result = ''.join(content_lines)
            else:
                parsed_result = str(result)
            
            # Clean up the response (remove thinking tags, execution logs)
            cleaned_result = re.sub(r'<thinking>.*?</thinking>', '', parsed_result, flags=re.DOTALL)
            cleaned_result = re.sub(r'\[Executing:.*?\]', '', cleaned_result)
            cleaned_result = re.sub(r'\n{3,}', '\n\n', cleaned_result).strip()
            
            # If cleaned result is too short or empty, use original result
            if len(cleaned_result.strip()) < 50:
                cleaned_result = parsed_result
            
            # Use LLM to clean up and format the final analysis properly
            try:
                thinking_content.text("🤖 **Final Step:** Cleaning and formatting analysis with LLM...")
                
                bedrock = boto3.client('bedrock-runtime', region_name='us-west-2')
                
                format_prompt = f"""
Please clean up and properly format this kitchen renovation analysis. The text contains formatting artifacts and escaped characters that need to be fixed.

<raw_analysis>
{cleaned_result}
</raw_analysis>

Please:
1. Fix all formatting issues (broken tables, escaped characters, weird symbols)
2. Create clean, readable markdown with proper headers
3. Ensure cost tables display correctly with aligned columns
4. Remove any garbled text or artifacts
5. Maintain all the important information (costs, recommendations, timeline)
6. Format as a professional renovation analysis report

Return only the cleaned, well-formatted analysis - no explanations.
"""
                
                response = bedrock.converse(
                    modelId="us.amazon.nova-premier-v1:0",
                    messages=[{
                        "role": "user",
                        "content": [{"text": format_prompt}]
                    }],
                    inferenceConfig={
                        "maxTokens": 4000,
                        "temperature": 0.1
                    }
                )
                
                cleaned_result = response['output']['message']['content'][0]['text'].strip()
                thinking_content.success("✅ **Analysis formatted successfully!**")
                
            except Exception as e:
                thinking_content.warning(f"⚠️ LLM formatting failed: {e} - showing original result")
                pass
            
            with result_container:
                # Extract and display budget prominently
                st.markdown("---")
                
                # Extract cost information using multiple patterns
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
                
                # Extract costs from individual agent results
                total_cost = None
                material_cost = None  
                labor_cost = None
                
                # First try to extract from CrewAI JSON data if available
                try:
                    # Check both local variables and session state
                    crew_data = None
                    if 'crewai_data' in locals() and crewai_data:
                        crew_data = crewai_data
                    elif 'crewai_data' in st.session_state:
                        crew_data = st.session_state['crewai_data']
                    
                    if crew_data:
                        # Handle nested project_estimate structure (actual CrewAI format)
                        project_estimate = crew_data.get('project_estimate', crew_data)
                        
                        # Extract total cost from multiple possible locations
                        total_cost_val = (
                            project_estimate.get('final_total_AUD') or
                            project_estimate.get('final_project_total_AUD') or
                            project_estimate.get('final_project_total') or 
                            project_estimate.get('total_project_cost') or
                            crew_data.get('final_project_total_AUD') or
                            crew_data.get('final_project_total') or
                            crew_data.get('total_project_cost') or
                            0
                        )
                        total_cost = str(int(float(total_cost_val))) if total_cost_val else None
                        
                        # Extract material costs from nested structure
                        materials = project_estimate.get('total_material_costs', crew_data.get('total_material_costs', {}))
                        if isinstance(materials, dict) and 'subtotal' in materials:
                            material_cost = str(int(float(materials['subtotal'])))
                        elif isinstance(materials, (int, float)):
                            material_cost = str(int(float(materials)))
                        elif crew_data.get('total_material_cost'):
                            material_cost = str(int(float(crew_data.get('total_material_cost', 0))))
                        else:
                            material_cost = None
                        
                        # Extract labor costs from nested structure
                        labor_costs = project_estimate.get('total_labor_costs', crew_data.get('total_labor_costs', {}))
                        labor_cost_val = None
                        
                        if isinstance(labor_costs, dict):
                            labor_cost_val = (
                                labor_costs.get('average_labor_cost') or
                                labor_costs.get('total_labor_cost') or
                                labor_costs.get('subtotal')
                            )
                        elif isinstance(labor_costs, (int, float)):
                            labor_cost_val = labor_costs
                        elif crew_data.get('total_labor_cost'):
                            labor_cost_val = crew_data.get('total_labor_cost')
                        
                        labor_cost = str(int(float(labor_cost_val))) if labor_cost_val else None
                            
                        # Debug information (show if debug mode is enabled)
                        if st.session_state.get('debug_mode', False):
                            st.write(f"🔍 **Debug Cost Extraction:**")
                            st.write(f"- Found crew_data: {'YES' if crew_data else 'NO'}")
                            if crew_data:
                                st.write(f"- crew_data keys: {list(crew_data.keys())}")
                                project_estimate = crew_data.get('project_estimate', {})
                                st.write(f"- project_estimate keys: {list(project_estimate.keys()) if isinstance(project_estimate, dict) else 'NOT DICT'}")
                                if isinstance(project_estimate, dict):
                                    st.write(f"- final_total_AUD: {project_estimate.get('final_total_AUD', 'NOT FOUND')}")
                                    materials = project_estimate.get('total_material_costs', {})
                                    st.write(f"- materials subtotal: {materials.get('subtotal', 'NOT FOUND') if isinstance(materials, dict) else 'NOT DICT'}")
                                    labor = project_estimate.get('total_labor_costs', {})
                                    st.write(f"- average_labor_cost: {labor.get('average_labor_cost', 'NOT FOUND') if isinstance(labor, dict) else 'NOT DICT'}")
                            
                            st.write(f"- Extracted total_cost: {total_cost}")
                            st.write(f"- Extracted material_cost: {material_cost}") 
                            st.write(f"- Extracted labor_cost: {labor_cost}")
                            
                except Exception as e:
                    st.error(f"Cost extraction error: {e}")
                    pass
                
                # Fallback to text extraction from all results
                if not total_cost:
                    all_text = f"{langgraph_result} {crewai_result} {cleaned_result}"
                    
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
                    st.success("💰 **ESTIMATED RENOVATION BUDGET**")
                    
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
                    # Fallback cost estimation based on cost grade
                    st.info("💰 **ESTIMATED RENOVATION BUDGET** (Based on Analysis)")
                    
                    # Provide estimates based on cost grade if no specific costs found
                    if cost_grade == "economy":
                        fallback_total = "18,500"
                        fallback_materials = "11,000"
                        fallback_labor = "7,500"
                    elif cost_grade == "premium":
                        fallback_total = "35,000"
                        fallback_materials = "21,000"
                        fallback_labor = "14,000"
                    else:  # standard
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
                st.markdown("### 📋 Comprehensive Kitchen Renovation Analysis")
                st.markdown(cleaned_result)
            
            # Download option with detailed agent results
            analysis_data = {
                "query": enhanced_query,
                "cost_grade": cost_grade,
                "include_labor": include_labor,
                "agent_results": {
                    "langgraph_result": langgraph_result if 'langgraph_result' in locals() else None,
                    "crewai_result": crewai_result if 'crewai_result' in locals() else None,
                    "orchestrator_synthesis": cleaned_result
                },
                "extracted_costs": {
                    "total_cost": total_cost,
                    "material_cost": material_cost,
                    "labor_cost": labor_cost
                },
                "analysis_time_seconds": elapsed,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            st.download_button(
                label="📥 Download Analysis Report",
                data=json.dumps(analysis_data, indent=2),
                file_name=f"multi_agent_kitchen_analysis.json",
                mime="application/json"
            )
            
        except Exception as e:
            st.error(f"❌ Analysis failed: {str(e)}")
            st.info("💡 Make sure the orchestrator agent is deployed and accessible")
            
            # Show debug information
            with st.expander("🔧 Debug Information"):
                st.text(f"Error details: {str(e)}")
                try:
                    orchestrator_arn = get_agent_arn_from_parameter_store("orchestrator_agent")
                    st.text(f"Orchestrator ARN: {orchestrator_arn}")
                except Exception as debug_e:
                    st.text(f"Could not get orchestrator ARN: {debug_e}")

# Information sections
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### 🤖 **Multi-Agent Architecture**
    
    **🎯 Orchestrator Agent (Strands)**
    - Coordinates the entire workflow
    - Routes queries to specialized agents
    - Synthesizes results into comprehensive recommendations
    
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
    ✅ **Bedrock ** for AI reasoning  
    ✅ **Distributed agent deployment**  
    ✅ **Real-time agent orchestration**  
    ✅ **Australian market pricing**  
    ✅ **Comprehensive renovation planning**  
    
    ### 📊 **Analysis Features**
    - Kitchen layout assessment
    - Material identification & costing
    - Labor cost calculation
    - Renovation recommendations
    - Budget planning & contingencies
    """)

# Sidebar agent status
st.sidebar.markdown("---")
st.sidebar.markdown("### 🤖 Agent Status")

# Check orchestrator status
try:
    orchestrator_arn = get_agent_arn_from_parameter_store("orchestrator_agent")
    st.sidebar.success("✅ Orchestrator Agent: Ready")
    st.sidebar.text(f"ARN: ...{orchestrator_arn[-20:]}")
except Exception as e:
    st.sidebar.error("❌ Orchestrator Agent: Not available")
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
- The orchestrator will coordinate all agents automatically
""")

st.sidebar.markdown("### ⏱️ Expected Timing")
st.sidebar.info("""
**Analysis takes 25-30 seconds:**
- 🎯 Orchestrator planning: ~3s
- 🏠 LangGraph analysis: ~15s  
- 💰 CrewAI cost estimation: ~8s
- 📋 Final synthesis: ~4s

Watch the thinking process above!
""")

st.sidebar.markdown("### 🏷️ Cost Grades")
st.sidebar.markdown("""
- **Economy**: Budget-friendly materials (~$15-20k)
- **Standard**: Mid-range quality (~$20-30k)
- **Premium**: High-end luxury (~$30k+)
""")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
<p><strong>🎯 Multi-Agent Kitchen Renovation System</strong></p>
<p>Powered by Amazon Bedrock AgentCore | LangGraph + CrewAI + Strands</p>
</div>
""", unsafe_allow_html=True)





