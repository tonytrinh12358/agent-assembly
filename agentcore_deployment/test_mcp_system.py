#!/usr/bin/env python3
"""
Comprehensive testing suite for MCP-enabled multi-agent system
Tests agent communication, deployment status, and end-to-end workflows
"""

import asyncio
import json
import logging
import sys
import os
import argparse
from typing import Dict, Any, List
from datetime import datetime

# Add mcp_base to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'mcp_base'))

from mcp_base.mcp_client_utils import AgentCoreMCPClient, discover_available_agents
from mcp_base.auth_utils import get_bearer_token_for_agent
import boto3

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MCPSystemTester:
    """Comprehensive testing suite for MCP agents"""
    
    def __init__(self, region: str = "us-west-2"):
        self.region = region
        self.client = AgentCoreMCPClient(region)
        self.test_results = {
            "test_session_id": f"test_{int(datetime.now().timestamp())}",
            "timestamp": datetime.now().isoformat(),
            "region": region,
            "tests": {}
        }
    
    async def test_agent_discovery(self) -> Dict[str, Any]:
        """Test discovery of all agents in the ecosystem"""
        logger.info("🔍 Testing agent discovery...")
        
        try:
            ecosystem_info = await discover_available_agents(self.region)
            
            test_result = {
                "test_name": "agent_discovery",
                "status": "passed" if ecosystem_info else "failed",
                "discovered_agents": len(ecosystem_info),
                "agents": list(ecosystem_info.keys()),
                "details": ecosystem_info
            }
            
            if ecosystem_info:
                logger.info(f"✅ Discovery test passed - Found {len(ecosystem_info)} agents")
                for agent_name, tools in ecosystem_info.items():
                    tool_count = len(tools) if isinstance(tools, list) else 0
                    logger.info(f"  • {agent_name}: {tool_count} tools")
            else:
                logger.error("❌ Discovery test failed - No agents found")
            
            return test_result
            
        except Exception as e:
            logger.error(f"❌ Discovery test failed with exception: {e}")
            return {
                "test_name": "agent_discovery",
                "status": "error",
                "error": str(e)
            }
    
    async def test_individual_agent(self, agent_name: str) -> Dict[str, Any]:
        """Test individual agent functionality"""
        logger.info(f"🧪 Testing {agent_name}...")
        
        test_result = {
            "test_name": f"individual_agent_{agent_name}",
            "agent_name": agent_name,
            "subtests": {}
        }
        
        # Test 1: Health check
        try:
            health_result = await self.client.health_check_agent(agent_name)
            test_result["subtests"]["health_check"] = {
                "status": "passed" if "error" not in health_result else "failed",
                "result": health_result
            }
            logger.info(f"  ✅ Health check: {'passed' if 'error' not in health_result else 'failed'}")
        except Exception as e:
            test_result["subtests"]["health_check"] = {
                "status": "error",
                "error": str(e)
            }
            logger.error(f"  ❌ Health check failed: {e}")
        
        # Test 2: Tool listing
        try:
            tools = await self.client.list_agent_tools(agent_name)
            test_result["subtests"]["tool_listing"] = {
                "status": "passed" if tools and not any("error" in tool for tool in tools) else "failed",
                "tool_count": len(tools) if tools else 0,
                "tools": tools
            }
            logger.info(f"  ✅ Tool listing: {len(tools) if tools else 0} tools found")
        except Exception as e:
            test_result["subtests"]["tool_listing"] = {
                "status": "error", 
                "error": str(e)
            }
            logger.error(f"  ❌ Tool listing failed: {e}")
        
        # Test 3: Agent-specific functionality
        if agent_name == "langgraph_agent":
            await self._test_langgraph_specific(agent_name, test_result)
        elif agent_name == "crewai_agent":
            await self._test_crewai_specific(agent_name, test_result)
        elif agent_name == "orchestrator_agent":
            await self._test_orchestrator_specific(agent_name, test_result)
        
        # Overall status
        subtest_statuses = [subtest.get("status") for subtest in test_result["subtests"].values()]
        test_result["status"] = "passed" if all(status == "passed" for status in subtest_statuses) else "failed"
        
        return test_result
    
    async def _test_langgraph_specific(self, agent_name: str, test_result: Dict):
        """Test LangGraph agent specific functionality"""
        try:
            logger.info(f"  🏠 Testing LangGraph kitchen analysis...")
            result = await self.client.invoke_agent_tool(
                agent_name,
                "analyze_kitchen",
                prompt="Test kitchen analysis for renovation planning",
                image_path=None
            )
            
            test_result["subtests"]["kitchen_analysis"] = {
                "status": "passed" if "error" not in result else "failed",
                "result": result
            }
            logger.info(f"    ✅ Kitchen analysis: {'passed' if 'error' not in result else 'failed'}")
            
        except Exception as e:
            test_result["subtests"]["kitchen_analysis"] = {
                "status": "error",
                "error": str(e)
            }
            logger.error(f"    ❌ Kitchen analysis failed: {e}")
    
    async def _test_crewai_specific(self, agent_name: str, test_result: Dict):
        """Test CrewAI agent specific functionality"""
        try:
            logger.info(f"  💰 Testing CrewAI cost estimation...")
            
            # Test materials data
            test_materials = [
                {"material_type": "granite", "area_sqm": 8.0},
                {"material_type": "wood", "area_sqm": 15.0},
                {"material_type": "tile", "area_sqm": 12.0}
            ]
            
            result = await self.client.invoke_agent_tool(
                agent_name,
                "estimate_renovation_costs",
                materials_data=test_materials,
                cost_grade="standard"
            )
            
            test_result["subtests"]["cost_estimation"] = {
                "status": "passed" if "error" not in result else "failed",
                "result": result
            }
            logger.info(f"    ✅ Cost estimation: {'passed' if 'error' not in result else 'failed'}")
            
        except Exception as e:
            test_result["subtests"]["cost_estimation"] = {
                "status": "error",
                "error": str(e)
            }
            logger.error(f"    ❌ Cost estimation failed: {e}")
    
    async def _test_orchestrator_specific(self, agent_name: str, test_result: Dict):
        """Test Orchestrator agent specific functionality"""
        try:
            logger.info(f"  🎯 Testing Orchestrator workflow...")
            result = await self.client.invoke_agent_tool(
                agent_name,
                "orchestrate_full_workflow",
                query="Test kitchen renovation workflow",
                cost_grade="standard",
                image_path=None
            )
            
            test_result["subtests"]["workflow_orchestration"] = {
                "status": "passed" if "error" not in result else "failed",
                "result": result
            }
            logger.info(f"    ✅ Workflow orchestration: {'passed' if 'error' not in result else 'failed'}")
            
        except Exception as e:
            test_result["subtests"]["workflow_orchestration"] = {
                "status": "error",
                "error": str(e)
            }
            logger.error(f"    ❌ Workflow orchestration failed: {e}")
    
    async def test_end_to_end_workflow(self) -> Dict[str, Any]:
        """Test complete end-to-end workflow"""
        logger.info("🔄 Testing end-to-end workflow...")
        
        test_result = {
            "test_name": "end_to_end_workflow",
            "workflow_steps": []
        }
        
        try:
            # Step 1: Kitchen Analysis via LangGraph
            logger.info("  📊 Step 1: Kitchen Analysis...")
            kitchen_result = await self.client.invoke_agent_tool(
                "langgraph_agent",
                "analyze_kitchen",
                prompt="Analyze kitchen for renovation planning with standard grade materials",
                image_path=None
            )
            
            test_result["workflow_steps"].append({
                "step": 1,
                "name": "kitchen_analysis",
                "status": "passed" if "error" not in kitchen_result else "failed",
                "result": kitchen_result
            })
            
            # Extract materials for step 2
            materials_data = []
            if "error" not in kitchen_result and "data" in kitchen_result:
                materials_data = kitchen_result["data"].get("materials", [])
            
            if not materials_data:
                # Use default test materials
                materials_data = [
                    {"material_type": "granite", "area_sqm": 8.0},
                    {"material_type": "wood", "area_sqm": 15.0},
                    {"material_type": "tile", "area_sqm": 12.0}
                ]
            
            # Step 2: Cost Estimation via CrewAI
            logger.info("  💰 Step 2: Cost Estimation...")
            cost_result = await self.client.invoke_agent_tool(
                "crewai_agent",
                "estimate_renovation_costs",
                materials_data=materials_data,
                cost_grade="standard"
            )
            
            test_result["workflow_steps"].append({
                "step": 2,
                "name": "cost_estimation", 
                "status": "passed" if "error" not in cost_result else "failed",
                "result": cost_result
            })
            
            # Step 3: Full Orchestration
            logger.info("  🎯 Step 3: Full Orchestration...")
            orchestration_result = await self.client.invoke_agent_tool(
                "orchestrator_agent",
                "orchestrate_full_workflow",
                query="Complete kitchen renovation analysis workflow test",
                cost_grade="standard",
                image_path=None
            )
            
            test_result["workflow_steps"].append({
                "step": 3,
                "name": "orchestration",
                "status": "passed" if "error" not in orchestration_result else "failed", 
                "result": orchestration_result
            })
            
            # Overall status
            step_statuses = [step["status"] for step in test_result["workflow_steps"]]
            test_result["status"] = "passed" if all(status == "passed" for status in step_statuses) else "failed"
            
            logger.info(f"✅ End-to-end workflow: {'passed' if test_result['status'] == 'passed' else 'failed'}")
            
        except Exception as e:
            test_result["status"] = "error"
            test_result["error"] = str(e)
            logger.error(f"❌ End-to-end workflow failed: {e}")
        
        return test_result
    
    async def test_authentication(self) -> Dict[str, Any]:
        """Test Cognito authentication for agents"""
        logger.info("🔐 Testing authentication...")
        
        test_result = {
            "test_name": "authentication",
            "agent_auth_tests": {}
        }
        
        agent_names = ["langgraph_agent", "crewai_agent", "orchestrator_agent"]
        
        for agent_name in agent_names:
            try:
                # Try to get bearer token
                token = get_bearer_token_for_agent(agent_name, self.region)
                
                test_result["agent_auth_tests"][agent_name] = {
                    "status": "passed" if token else "failed",
                    "has_token": bool(token),
                    "token_length": len(token) if token else 0
                }
                
                logger.info(f"  • {agent_name}: {'✅ token available' if token else '❌ no token'}")
                
            except Exception as e:
                test_result["agent_auth_tests"][agent_name] = {
                    "status": "error",
                    "error": str(e)
                }
                logger.error(f"  • {agent_name}: ❌ auth error: {e}")
        
        # Overall auth status
        auth_statuses = [result["status"] for result in test_result["agent_auth_tests"].values()]
        test_result["status"] = "passed" if any(status == "passed" for status in auth_statuses) else "failed"
        
        return test_result
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests in the suite"""
        logger.info("🧪 Starting comprehensive MCP system test suite...")
        logger.info("=" * 60)
        
        # Run all tests
        tests = [
            self.test_agent_discovery(),
            self.test_individual_agent("langgraph_agent"),
            self.test_individual_agent("crewai_agent"), 
            self.test_individual_agent("orchestrator_agent"),
            self.test_authentication(),
            self.test_end_to_end_workflow()
        ]
        
        results = await asyncio.gather(*tests, return_exceptions=True)
        
        # Process results
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                test_name = f"test_{i}"
                self.test_results["tests"][test_name] = {
                    "status": "error",
                    "error": str(result)
                }
            else:
                test_name = result.get("test_name", f"test_{i}")
                self.test_results["tests"][test_name] = result
        
        # Generate summary
        self._generate_test_summary()
        
        return self.test_results
    
    def _generate_test_summary(self):
        """Generate test summary"""
        total_tests = len(self.test_results["tests"])
        passed_tests = sum(1 for test in self.test_results["tests"].values() if test.get("status") == "passed")
        failed_tests = sum(1 for test in self.test_results["tests"].values() if test.get("status") == "failed") 
        error_tests = sum(1 for test in self.test_results["tests"].values() if test.get("status") == "error")
        
        self.test_results["summary"] = {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "errors": error_tests,
            "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0
        }
        
        logger.info("=" * 60)
        logger.info("📊 TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"✅ Passed: {passed_tests}")
        logger.info(f"❌ Failed: {failed_tests}")
        logger.info(f"⚠️ Errors: {error_tests}")
        logger.info(f"🎯 Success Rate: {self.test_results['summary']['success_rate']:.1f}%")
        logger.info("=" * 60)


async def main():
    """Main test function"""
    parser = argparse.ArgumentParser(description="Test MCP multi-agent system")
    parser.add_argument("--region", default="us-west-2", help="AWS region")
    parser.add_argument("--agent", help="Test specific agent only")
    parser.add_argument("--test", help="Run specific test only (discovery, auth, e2e)")
    parser.add_argument("--output", help="Output file for test results JSON")
    
    args = parser.parse_args()
    
    tester = MCPSystemTester(args.region)
    
    try:
        if args.test == "discovery":
            result = await tester.test_agent_discovery()
        elif args.test == "auth":
            result = await tester.test_authentication()
        elif args.test == "e2e":
            result = await tester.test_end_to_end_workflow()
        elif args.agent:
            result = await tester.test_individual_agent(args.agent)
        else:
            result = await tester.run_all_tests()
        
        # Output results
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2)
            logger.info(f"📄 Test results saved to {args.output}")
        else:
            print(json.dumps(result, indent=2))
    
    except Exception as e:
        logger.error(f"❌ Test execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
