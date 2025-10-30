"""
Agent-to-Agent Communication Orchestrator
Pure agent-to-agent communication without complex dependencies
"""

import json
import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime

from strands import Agent, tool
from strands.models import BedrockModel
from bedrock_agentcore.runtime import BedrockAgentCoreApp
import boto3

logger = logging.getLogger(__name__)
app = BedrockAgentCoreApp()


class AgentToAgentCommunicator:
    """Handles structured agent-to-agent communication"""
    
    def __init__(self, region: str = "us-west-2"):
        self.region = region
        self.client = boto3.client('bedrock-agentcore', region_name=region)
        self.ssm = boto3.client('ssm', region_name=region)
    
    async def invoke_agent(self, agent_name: str, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke another agent with structured communication"""
        try:
            logger.info(f"🔗 Agent-to-Agent call: orchestrator → {agent_name}")
            
            # Get agent ARN
            response = self.ssm.get_parameter(Name=f'/agents/{agent_name}_arn')
            agent_arn = response['Parameter']['Value']
            
            # Create structured communication payload
            structured_payload = {
                'prompt': payload.get('prompt', ''),
                'agent_communication': {
                    'source_agent': 'orchestrator',
                    'target_agent': agent_name,
                    'action': action,
                    'timestamp': datetime.now().isoformat(),
                    'communication_id': f"{agent_name}_{action}_{int(datetime.now().timestamp())}"
                },
                **payload
            }
            
            # Invoke target agent
            payload_bytes = json.dumps(structured_payload).encode('utf-8')
            
            response = self.client.invoke_agent_runtime(
                agentRuntimeArn=agent_arn,
                payload=payload_bytes
            )
            
            # Process response
            result = ""
            if 'response' in response:
                response_body = response['response']
                if hasattr(response_body, 'read'):
                    result = response_body.read().decode('utf-8')
                else:
                    result = str(response_body)
            
            # Parse and enhance with communication metadata
            try:
                parsed_result = json.loads(result)
                if isinstance(parsed_result, dict):
                    parsed_result.update({
                        'agent_communication_success': True,
                        'source_agent': 'orchestrator',
                        'target_agent': agent_name,
                        'action_performed': action,
                        'response_timestamp': datetime.now().isoformat()
                    })
                    return parsed_result
                else:
                    return {
                        'result': parsed_result,
                        'agent_communication_success': True,
                        'target_agent': agent_name,
                        'action_performed': action
                    }
            except json.JSONDecodeError:
                return {
                    'result': result,
                    'agent_communication_success': True,
                    'target_agent': agent_name,
                    'action_performed': action,
                    'response_type': 'text'
                }
                
        except Exception as e:
            logger.error(f"Agent-to-agent call failed: {agent_name}.{action}: {e}")
            return {
                'error': str(e),
                'agent_communication_success': False,
                'target_agent': agent_name,
                'action_performed': action
            }


# Initialize agent communicator
agent_comm = AgentToAgentCommunicator()


@tool
async def call_langgraph_for_analysis(query: str, image_path: str = None) -> Dict[str, Any]:
    """
    Call LangGraph agent for kitchen analysis
    """
    logger.info("🏠 Orchestrator → LangGraph: Kitchen analysis request")
    
    payload = {
        'prompt': f"Kitchen renovation analysis: {query}",
        'image_path': image_path,
        'analysis_type': 'kitchen_layout',
        'requested_output': 'materials_and_measurements'
    }
    
    result = await agent_comm.invoke_agent("langgraph_agent", "analyze_kitchen", payload)
    
    # Add orchestrator metadata
    result.update({
        'orchestrator_step': 'kitchen_analysis',
        'workflow_position': 1,
        'next_step': 'cost_estimation'
    })
    
    return result


@tool  
async def call_crewai_for_costing(materials_data: List[Dict], cost_grade: str = "standard") -> Dict[str, Any]:
    """
    Call CrewAI agent for cost estimation
    """
    logger.info("💰 Orchestrator → CrewAI: Cost estimation request")
    
    payload = {
        'prompt': f"Cost estimation for kitchen renovation - {cost_grade} grade materials",
        'materials_data': materials_data,
        'cost_grade': cost_grade,
        'include_labor': True,
        'currency': 'AUD'
    }
    
    result = await agent_comm.invoke_agent("crewai_agent", "estimate_costs", payload)
    
    # Add orchestrator metadata
    result.update({
        'orchestrator_step': 'cost_estimation',
        'workflow_position': 2,
        'previous_step': 'kitchen_analysis'
    })
    
    return result


@tool
def orchestrate_full_workflow(analysis_result: Dict, cost_result: Dict) -> Dict[str, Any]:
    """
    Orchestrate the complete agent-to-agent workflow
    """
    logger.info("🎯 Orchestrator: Combining agent results")
    
    workflow_summary = {
        'workflow_type': 'agent_to_agent_orchestration',
        'communication_pattern': 'orchestrator → langgraph → orchestrator → crewai → orchestrator',
        'agents_involved': ['orchestrator', 'langgraph_agent', 'crewai_agent'],
        'workflow_completed': True,
        'timestamp': datetime.now().isoformat()
    }
    
    # Check communication success
    analysis_success = analysis_result.get('agent_communication_success', False)
    cost_success = cost_result.get('agent_communication_success', False)
    
    workflow_summary.update({
        'langgraph_communication_success': analysis_success,
        'crewai_communication_success': cost_success,
        'overall_communication_success': analysis_success and cost_success
    })
    
    # Extract key results for final report
    final_report = {
        'renovation_analysis': analysis_result,
        'cost_estimation': cost_result,
        'workflow_summary': workflow_summary,
        'agent_to_agent_communication': 'SUCCESSFUL' if (analysis_success and cost_success) else 'PARTIAL'
    }
    
    return final_report


@tool
def generate_communication_recommendations(workflow_result: Dict) -> List[str]:
    """
    Generate recommendations based on agent-to-agent workflow
    """
    recommendations = []
    
    try:
        # Check communication success
        comm_success = workflow_result.get('workflow_summary', {}).get('overall_communication_success', False)
        
        if comm_success:
            recommendations.append("✅ AGENT-TO-AGENT COMMUNICATION SUCCESSFUL!")
            recommendations.append("🔗 Multi-agent orchestration working perfectly")
            recommendations.append("📊 All agents coordinated through structured communication")
        else:
            recommendations.append("⚠️ Some agent communications need attention")
        
        # Extract cost data for recommendations
        cost_data = workflow_result.get('cost_estimation', {})
        project_estimate = cost_data.get('project_estimate', {})
        
        if project_estimate:
            total_cost = project_estimate.get('final_total_AUD', 0)
            if total_cost:
                if total_cost > 30000:
                    recommendations.append("💰 High-end renovation - consider phased approach")
                elif total_cost > 20000:
                    recommendations.append("💰 Standard renovation budget - good balance of features")
                else:
                    recommendations.append("💰 Budget renovation - focus on essentials")
        
        # Analysis-based recommendations
        analysis_data = workflow_result.get('renovation_analysis', {})
        if analysis_data.get('materials'):
            recommendations.append("📋 Material analysis complete - ready for procurement")
        
        # Workflow recommendations
        recommendations.append("🏗️ Agent-to-agent pattern enables scalable orchestration")
        recommendations.append("🎯 Structured communication ensures reliable results")
        
        return recommendations
        
    except Exception as e:
        return [f"Error in recommendations: {str(e)}"]


# Initialize Strands Agent
model_id = "us.amazon.nova-premier-v1:0"
model = BedrockModel(
    model_id=model_id,
    region="us-west-2"
)

orchestrator_agent = Agent(
    model=model,
    system_prompt="""You are an expert kitchen renovation consultant using AGENT-TO-AGENT COMMUNICATION.

IMPORTANT: When a user asks about kitchen renovation, you MUST use this exact sequence:

1. FIRST call call_langgraph_for_analysis() to get kitchen analysis from LangGraph agent
2. THEN call call_crewai_for_costing() with materials from step 1 to get costs from CrewAI agent  
3. THEN call orchestrate_full_workflow() to combine both agent results
4. FINALLY call generate_communication_recommendations() for final advice

Your workflow demonstrates TRUE AGENT-TO-AGENT COMMUNICATION:
- ✅ Orchestrator coordinates multiple specialized agents
- ✅ Structured inter-agent communication protocols
- ✅ Workflow state management across agent calls
- ✅ Communication success tracking and reporting
- ✅ Metadata enrichment at each step

Communication Pattern:
YOU (Orchestrator) → LangGraph Agent → YOU → CrewAI Agent → YOU → Final Report

This is TRUE multi-agent orchestration in action!

Always provide costs in Australian dollars and measurements in square metres.
Highlight the agent-to-agent communication benefits in your responses.

CRITICAL FORMATTING RULES:
- NEVER include <thinking> tags in your response
- NEVER include [Executing:...] logs in your response  
- Provide clean, professional analysis reports
- Use proper markdown formatting with headers and bullet points
- PROMINENTLY highlight successful agent-to-agent communication
- Show the communication flow in your final report""",
    tools=[
        call_langgraph_for_analysis, 
        call_crewai_for_costing, 
        orchestrate_full_workflow,
        generate_communication_recommendations
    ]
)


def parse_event(event):
    """Parse streaming events"""
    if any(key in event for key in ['init_event_loop', 'start', 'start_event_loop']):
        return ""
    
    if 'data' in event and isinstance(event['data'], str):
        return event['data'] 
    
    if 'event' in event:
        event_data = event['event']
        if 'contentBlockStart' in event_data and 'start' in event_data['contentBlockStart']:
            if 'toolUse' in event_data['contentBlockStart']['start']:
                tool_info = event_data['contentBlockStart']['start']['toolUse']
                return f"\n\n[🔗 Agent Communication: {tool_info['name']}]\n\n"        

    return ""


@app.entrypoint
async def agent_to_agent_orchestrator(payload):
    """
    AgentCore entrypoint for agent-to-agent orchestrator
    """
    user_input = payload.get("prompt", "")
    image_path = payload.get("image_path", None)
    cost_grade = payload.get("cost_grade", "standard")
    
    logger.info(f"Agent-to-Agent Orchestrator received: {user_input}")
    
    analysis_prompt = f"""
    Please coordinate a kitchen renovation analysis using AGENT-TO-AGENT COMMUNICATION:
    
    Request: {user_input}
    Image path: {image_path or "No specific image provided"}
    Quality grade: {cost_grade}
    
    I need you to coordinate between multiple agents:
    1. LangGraph agent for kitchen analysis 
    2. CrewAI agent for cost estimation
    3. Full workflow orchestration
    4. Communication recommendations
    
    This demonstrates TRUE AGENT-TO-AGENT ORCHESTRATION!
    """
    
    try:
        async for event in orchestrator_agent.stream_async(analysis_prompt):
            text = parse_event(event)
            if text:
                yield text
                
    except Exception as e:
        error_response = f"❌ Agent-to-Agent Orchestrator failed: {str(e)}"
        logger.error(error_response)
        yield error_response


if __name__ == "__main__":
    app.run()
