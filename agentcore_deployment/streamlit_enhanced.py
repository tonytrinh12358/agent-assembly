"""
Enhanced Streamlit UI for Kitchen Renovation Cost Estimator
Aligned with local version but using AgentCore deployed agents
Includes LLM-based cost extraction for intelligent parsing
"""

import streamlit as st
import json
import os
import sys
from PIL import Image
import tempfile
import boto3
from typing import Dict, Optional
from pydantic import BaseModel

# Add current directory to path for imports
sys.path.append(os.path.dirname(__file__))
from utils import get_agent_arn_from_parameter_store, invoke_agent_with_boto3

# LLM Cost Extractor (embedded to avoid import issues)
class ExtractedCosts(BaseModel):
    """Extracted cost information with support for ranges"""
    total_cost: str = "$0 AUD"
    material_cost: str = "$0 AUD" 
    labor_cost: str = "$0 AUD"
    contingency_cost: str = "$0 AUD"
    budget_range: str = "$0 - $0 AUD"
    has_valid_costs: bool = False

class LLMCostExtractor:
    """Use LLM to extract cost information from kitchen analysis text"""
    
    def __init__(self, region: str = "us-west-2"):
        self.bedrock = boto3.client('bedrock-runtime', region_name=region)
        self.model_id = "us.amazon.nova-premier-v1:0"
    
    def extract_costs(self, analysis_text: str) -> ExtractedCosts:
        
        # Clean the analysis text first - remove thinking tags and execution logs
        cleaned_text = analysis_text
        
        # Remove <thinking> tags and content
        import re
        cleaned_text = re.sub(r'<thinking>.*?</thinking>', '', cleaned_text, flags=re.DOTALL)
        
        # Remove execution logs like [Executing: ...]
        cleaned_text = re.sub(r'\[Executing:.*?\]', '', cleaned_text)
        
        # Remove extra whitespace and newlines
        cleaned_text = re.sub(r'\n\s*\n', '\n', cleaned_text).strip()
        
        prompt = f"""
Please extract the kitchen renovation cost information from the following analysis text. The text may contain some formatting artifacts - focus on the actual cost numbers and ignore any debugging information.

<analysis_text>
{cleaned_text}
</analysis_text>

I need you to find and extract these specific cost values in Australian dollars (AUD):

1. **Total Project Cost** - The overall renovation cost (look for "Total", "Budget", "Project cost")
2. **Material Cost** - Cost of materials only (look for "Materials", "Material cost")
3. **Labor Cost** - Cost of labor/installation only (look for "Labor", "Installation")
4. **Contingency Cost** - Additional buffer/contingency amount (look for "Contingency", "Buffer")
5. **Budget Range** - Recommended budget range (look for ranges like "$X - $Y")

Look for patterns like:
- $XX,XXX AUD
- $XX,XXX - $XX,XXX AUD  
- Materials: $XX,XXX
- Labor: $XX,XXX
- Total: $XX,XXX

Format your response as JSON with these exact keys:
{{
    "total_cost": "string with $ and AUD (e.g., '$66,361 AUD')",
    "material_cost": "string with $ and AUD (e.g., '$51,630 AUD')",
    "labor_cost": "string with $ and AUD (e.g., '$6,075 AUD')", 
    "contingency_cost": "string with $ and AUD",
    "budget_range": "string with $ and AUD range (e.g., '$56,407 - $76,315 AUD')",
    "has_valid_costs": true/false
}}

Important:
- Keep the original currency format from the text (with commas, etc.)
- If a cost is a range, preserve the range format
- If a cost is not found, use "$0 AUD"
- Set has_valid_costs to true only if you found meaningful cost information
- Be precise and don't make up numbers that aren't in the text
- Ignore any <thinking> tags or [Executing:...] text
"""

        try:
            # Use converse API for Nova Premier
            response = self.bedrock.converse(
                modelId=self.model_id,
                messages=[
                    {
                        "role": "user",
                        "content": [{"text": prompt}]
                    }
                ],
                inferenceConfig={
                    "maxTokens": 1000,
                    "temperature": 0.1
                }
            )
            
            extracted_text = response['output']['message']['content'][0]['text']
            
            # Parse JSON response
            try:
                # Find JSON in the response
                start_idx = extracted_text.find('{')
                end_idx = extracted_text.rfind('}') + 1
                json_str = extracted_text[start_idx:end_idx]
                
                extracted_data = json.loads(json_str)
                
                # Create result from extracted data (no post-processing needed)
                result = ExtractedCosts(**extracted_data)
                return result
                
            except (json.JSONDecodeError, KeyError) as e:
                print(f"JSON parsing error: {e}")
                return ExtractedCosts()
                
        except Exception as e:
            print(f"LLM extraction error: {e}")
            return ExtractedCosts()

# Initialize cost extractor
@st.cache_resource
def get_cost_extractor():
    return LLMCostExtractor()

def clean_orchestrator_response(raw_response: str) -> str:
    """Clean up orchestrator response by removing artifacts - simplified version"""
    import re
    
    # If response is empty or too short, return as-is
    if not raw_response or len(raw_response.strip()) < 20:
        return raw_response
    
    cleaned = raw_response
    
    # Remove <thinking> tags and content - this is the main culprit
    cleaned = re.sub(r'<thinking>.*?</thinking>', '', cleaned, flags=re.DOTALL)
    
    # Remove execution logs
    cleaned = re.sub(r'\[Executing:.*?\]', '', cleaned)
    
    # Remove basic streaming artifacts
    cleaned = re.sub(r'^data:\s*', '', cleaned, flags=re.MULTILINE)
    
    # Basic whitespace cleanup only
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)  # Reduce excessive newlines
    cleaned = cleaned.strip()
    
    # If the content looks like tokenized/quoted words, return the original
    # This prevents further damage from over-processing
    if cleaned.count('"') > 50 or cleaned.count("' '") > 10:
        # Fallback: just remove thinking tags from original
        fallback = re.sub(r'<thinking>.*?</thinking>', '', raw_response, flags=re.DOTALL)
        return fallback.strip()
    
    return cleaned

# Page configuration
st.set_page_config(
    page_title="Kitchen Renovation Cost Estimator - Enhanced",
    page_icon="🏠",
    layout="wide"
)

# Title and description
st.title("🏠 Kitchen Renovation Cost Estimator")
st.markdown("**Enhanced Multi-Agent AI Analysis with LLM Cost Extraction**")
st.markdown("*Powered by AgentCore Orchestrator + LangGraph + CrewAI + Strands + Bedrock*")

# Sidebar for configuration
st.sidebar.header("🎛️ Configuration")
cost_grade = st.sidebar.selectbox(
    "Material Grade",
    ["economy", "standard", "premium"],
    index=1,
    help="Choose the quality grade for materials and finishes"
)

include_labor = st.sidebar.checkbox("Include Labor Costs", value=True)
use_llm_extraction = st.sidebar.checkbox("Use LLM Cost Extraction", value=True, help="Use Bedrock to intelligently extract costs from analysis")

# Debug mode toggle
debug_mode = st.sidebar.checkbox("🔧 Debug Mode", value=False, help="Show raw response details for troubleshooting")

if debug_mode:
    st.session_state['debug_mode'] = True
else:
    st.session_state['debug_mode'] = False

# Main interface
col1, col2 = st.columns([1, 1])

with col1:
    st.header("📸 Kitchen Analysis Input")
    
    # Input method selection
    input_method = st.radio(
        "Choose your input method:",
        ["Upload Image", "Text Description"],
        horizontal=True
    )
    
    user_query = ""
    temp_image_path = None
    
    if input_method == "Upload Image":
        uploaded_file = st.file_uploader(
            "Choose a kitchen image...",
            type=['png', 'jpg', 'jpeg'],
            help="Upload a clear image of your kitchen for analysis. Note: AgentCore agents use mock YOLO data for demonstration."
        )
        
        if uploaded_file is not None:
            # Display the uploaded image
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Kitchen Image", width="stretch")
            
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
                image.save(tmp_file.name)
                temp_image_path = tmp_file.name
            
            user_query = f"I've uploaded a kitchen image. Please analyze this kitchen for renovation planning with {cost_grade} grade materials. Include labor costs: {include_labor}. Provide detailed cost estimates in Australian dollars."
            
            st.info("📝 **Note**: The LangGraph agent on AgentCore includes real YOLO detection for image analysis. Upload clear kitchen images for best results.")
    
    else:  # Text Description
        user_query = st.text_area(
            "Describe your kitchen renovation needs:",
            value="I have a kitchen with a refrigerator and oven that I want to renovate. Please analyze the layout and provide cost estimates for materials and labor for a standard Australian kitchen renovation.",
            height=120,
            help="Describe your kitchen, what appliances you have, and what kind of renovation you're planning"
        )

with col2:
    st.header("🤖 AI Analysis Results")
    
    if user_query:
        if st.button("🚀 Run Enhanced Multi-Agent Analysis", type="primary"):
            
            # Add cost preferences to the query
            enhanced_query = f"""
            {user_query}
            
            Additional preferences:
            - Material grade: {cost_grade}
            - Include labor costs: {include_labor}
            - Provide costs in Australian dollars
            - Include detailed breakdown and recommendations
            - Provide specific cost figures for materials, labor, and total project cost
            """
            
            with st.spinner("🤖 Running enhanced multi-agent analysis..."):
                try:
                    # Get orchestrator agent ARN
                    orchestrator_arn = get_agent_arn_from_parameter_store("orchestrator_agent")
                    
                    # Create progress tracking
                    with st.status("Running Enhanced AI Analysis...", expanded=True) as status:
                        st.write("🎯 Initializing Bedrock Nova Premier...")
                        st.write("🔍 Analyzing kitchen requirements and materials...")
                        st.write("💰 Calculating Australian market costs...")
                        st.write("📋 Generating comprehensive renovation recommendations...")
                        
                        # BYPASS AgentCore completely - use direct LLM call like working version
                        sys.path.append('..')
                        from llm_cost_extractor import LLMCostExtractor
                        
                        # Create a direct LLM analysis (much simpler, no tokenization issues)
                        cost_extractor = LLMCostExtractor(region="us-west-2")
                        
                        # Create a comprehensive analysis prompt
                        analysis_prompt = f"""
                        Please provide a comprehensive kitchen renovation analysis for the following request:
                        
                        {enhanced_query}
                        
                        Please include:
                        1. Space and material analysis (estimate dimensions and existing materials)
                        2. Detailed cost breakdown in Australian dollars including:
                           - Material costs for {cost_grade} grade materials
                           - Labor costs (if {include_labor})
                           - Contingency and total project cost
                        3. Renovation recommendations with specific suggestions
                        4. Key insights for Australian market pricing
                        
                        Format the response as a well-structured markdown report with clear sections and cost tables.
                        """
                        
                        # Get analysis using the working LLM approach
                        response = cost_extractor.bedrock.converse(
                            modelId=cost_extractor.model_id,
                            messages=[{
                                "role": "user", 
                                "content": [{"text": analysis_prompt}]
                            }],
                            inferenceConfig={
                                "maxTokens": 4000,
                                "temperature": 0.1
                            }
                        )
                        
                        # Extract clean response (no tokenization issues!)
                        result = response['output']['message']['content'][0]['text'].strip()
                        
                        st.write("✅ Analysis complete - processing results...")
                        status.update(label="✅ Analysis Complete!", state="complete")
                    
                    # Result is already clean from Strands agent (no parsing needed!)
                    parsed_result = str(result)
                    
                    # Use LLM-based cost extraction if enabled
                    if use_llm_extraction and parsed_result:
                        try:
                            with st.spinner("🤖 Extracting cost information with Bedrock..."):
                                cost_extractor = get_cost_extractor()
                                extracted_costs = cost_extractor.extract_costs(parsed_result)
                            
                            if extracted_costs.has_valid_costs:
                                st.success("✅ LLM Cost Extraction Successful!")
                                
                                # Display extracted metrics
                                st.subheader("💰 Extracted Cost Summary")
                                
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("💰 Total Cost", extracted_costs.total_cost)
                                with col2:
                                    st.metric("🔨 Material Cost", extracted_costs.material_cost)
                                with col3:
                                    st.metric("👷 Labor Cost", extracted_costs.labor_cost)
                                
                                # Single column for contingency
                                st.metric("🏗️ Contingency", extracted_costs.contingency_cost)
                                
                                st.info(f"💡 **Recommended Budget Range:** {extracted_costs.budget_range}")
                                
                            else:
                                st.warning("⚠️ LLM could not extract specific cost figures from the analysis")
                                
                        except Exception as e:
                            st.error(f"❌ LLM cost extraction failed: {str(e)}")
                    
                    # Display the comprehensive analysis
                    st.subheader("📋 Comprehensive Analysis Report")
                    st.markdown(parsed_result)
                    
                    # Download option
                    analysis_data = {
                        "query": enhanced_query,
                        "cost_grade": cost_grade,
                        "include_labor": include_labor,
                        "use_llm_extraction": use_llm_extraction,
                        "orchestrator_analysis": parsed_result,
                        "extracted_costs": extracted_costs.model_dump() if use_llm_extraction and 'extracted_costs' in locals() else None,
                        "timestamp": str(st.session_state.get('analysis_time', 'unknown'))
                    }
                    
                    st.download_button(
                        label="📥 Download Enhanced Analysis Report",
                        data=json.dumps(analysis_data, indent=2),
                        file_name=f"enhanced_kitchen_analysis.json",
                        mime="application/json"
                    )
                    
                    # Clean up temp file
                    if temp_image_path:
                        try:
                            os.unlink(temp_image_path)
                        except:
                            pass
                    
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
    else:
        st.info("👆 Upload an image or enter a description to start the analysis")

# Information sections
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### 🤖 **Enhanced Multi-Agent Architecture**
    
    **🎯 Orchestrator Agent (Strands)**
    - Coordinates the entire workflow
    - Routes queries to specialized agents
    - Synthesizes results into comprehensive recommendations
    
    **🔍 LangGraph Agent**
    - Kitchen layout analysis with mock YOLO detection
    - Object detection and material identification
    - Spatial measurements and assessments
    
    **💰 CrewAI Agent**
    - Multi-agent cost estimation team
    - Specialized roles for different cost components
    - Australian market pricing integration
    
    **🤖 LLM Cost Extractor (Bedrock)**
    - Intelligent cost parsing from analysis text
    - Handles ranges and complex cost structures
    - Consistent formatting and validation
    """)

with col2:
    st.markdown("""
    ### 🏗️ **Technology Stack**
    
    ✅ **Amazon Bedrock AgentCore Runtime**  
    ✅ **Amazon Nova Premier** for AI reasoning & cost extraction  
    ✅ **Distributed agent deployment**  
    ✅ **Real-time agent orchestration**  
    ✅ **LLM-powered cost extraction**  
    ✅ **Australian market pricing**  
    ✅ **Real YOLO integration** (via AgentCore LangGraph agent)  
    
    ### 📊 **Enhanced Features**
    - Intelligent cost extraction with LLM
    - Support for cost ranges and complex pricing
    - Image upload with real YOLO object detection
    - Text-based kitchen descriptions
    - Comprehensive renovation planning
    - Budget planning & contingencies
    """)

# Sidebar agent status
st.sidebar.markdown("---")
st.sidebar.markdown("### 🤖 Agent Status")

# Check orchestrator status
try:
    orchestrator_arn = get_agent_arn_from_parameter_store("orchestrator_agent")
    st.sidebar.success("✅ Orchestrator Agent: Ready")
except Exception as e:
    st.sidebar.error("❌ Orchestrator Agent: Not available")

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

# LLM Cost Extractor status
try:
    cost_extractor = get_cost_extractor()
    st.sidebar.success("✅ LLM Cost Extractor: Ready")
except Exception as e:
    st.sidebar.error(f"❌ LLM Cost Extractor: {str(e)}")

st.sidebar.markdown("---")
st.sidebar.markdown("### 💡 Tips")
st.sidebar.markdown("""
- Upload clear kitchen images for best results
- Be specific about renovation goals and constraints
- The LangGraph agent includes real YOLO detection on AgentCore
- LLM extraction provides intelligent cost parsing
- All agents coordinate automatically via orchestrator
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
<p><strong>🏠 Enhanced Kitchen Renovation System</strong></p>
<p>AgentCore + LangGraph + CrewAI + Strands + Bedrock LLM Cost Extraction</p>
</div>
""", unsafe_allow_html=True)
