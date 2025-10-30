"""
Kitchen Visual Analysis with Real YOLO Detection, LangGraph, and Bedrock Integration
"""

from langgraph.graph import StateGraph, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_aws import ChatBedrock
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import json
from enum import Enum
import torch
from ultralytics import YOLO


class MaterialType(str, Enum):
    WOOD = "wood"
    GRANITE = "granite" 
    TILE = "tile"
    STAINLESS_STEEL = "stainless_steel"
    VINYL = "vinyl"
    LAMINATE = "laminate"
    UNKNOWN = "unknown"


class DetectedObject(BaseModel):
    name: str
    confidence: float
    bbox: List[int]  # [x, y, w, h]


class MaterialInfo(BaseModel):
    material_type: MaterialType
    area_sqm: float
    location: str


@tool
def analyze_kitchen_objects(objects_json: str) -> str:
    """
    Analyze detected kitchen objects and provide renovation insights.
    
    Args:
        objects_json: JSON string of detected objects with confidence and bbox
        
    Returns:
        Analysis of kitchen layout and renovation recommendations
    """
    try:
        objects = json.loads(objects_json)
        
        analysis = []
        analysis.append("🏠 Kitchen Analysis Results:")
        
        # Analyze object types
        object_types = [obj.get('name', 'unknown') for obj in objects]
        analysis.append(f"📊 Detected {len(objects)} objects: {', '.join(set(object_types))}")
        
        # Check for essential kitchen elements
        essentials = ['refrigerator', 'oven', 'sink']
        found_essentials = [item for item in essentials if item in object_types]
        missing_essentials = [item for item in essentials if item not in object_types]
        
        if found_essentials:
            analysis.append(f"✅ Essential appliances found: {', '.join(found_essentials)}")
        if missing_essentials:
            analysis.append(f"⚠️ Missing essentials: {', '.join(missing_essentials)}")
            
        # Renovation recommendations
        analysis.append("\n💡 Renovation Recommendations:")
        if 'refrigerator' in object_types and 'oven' in object_types:
            analysis.append("- Good appliance layout detected")
            analysis.append("- Consider cabinet upgrades for storage")
            analysis.append("- Granite countertops would enhance the space")
        
        return "\n".join(analysis)
        
    except Exception as e:
        return f"Error analyzing objects: {str(e)}"


class KitchenAnalyzerYOLO:
    def __init__(self, region: str = "us-west-2"):
        # Initialize Bedrock LLM
        self.llm = ChatBedrock(
            model_id="us.amazon.nova-premier-v1:0",
            region_name=region,
            model_kwargs={
                "max_tokens": 4000,
                "temperature": 0.1
            }
        )
        
        # Create tools and bind to LLM
        self.tools = [analyze_kitchen_objects]
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
        # Build the graph
        self.graph = self._build_graph()
        
        # Load YOLO model using modern ultralytics API
        try:
            self.yolo_model = YOLO('yolov5s.pt')  # Uses modern ultralytics API
            print("✅ YOLO model loaded successfully")
        except Exception as e:
            print(f"⚠️ YOLO model loading failed: {e}")
            self.yolo_model = None
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        
        # System message
        system_message = """You are a kitchen renovation expert with computer vision capabilities. 
        You can analyze kitchen images, detect objects, and provide renovation recommendations.
        Use the analyze_kitchen_objects tool to provide detailed insights."""
        
        # Define the chatbot node
        def chatbot(state: MessagesState):
            messages = state["messages"]
            if not messages or not isinstance(messages[0], SystemMessage):
                messages = [SystemMessage(content=system_message)] + messages
            
            response = self.llm_with_tools.invoke(messages)
            return {"messages": [response]}
        
        # Create the graph
        graph_builder = StateGraph(MessagesState)
        
        # Add nodes
        graph_builder.add_node("chatbot", chatbot)
        graph_builder.add_node("tools", ToolNode(self.tools))
        
        # Add edges
        graph_builder.add_conditional_edges(
            "chatbot",
            tools_condition,
        )
        graph_builder.add_edge("tools", "chatbot")
        
        # Set entry point
        graph_builder.set_entry_point("chatbot")
        
        return graph_builder.compile()
    
    def _detect_objects_yolo(self, image_path: str) -> List[DetectedObject]:
        """Run YOLO detection on image"""
        if not self.yolo_model:
            return []
            
        try:
            # Load and process image using modern ultralytics API
            results = self.yolo_model(image_path)
            detected_objects = []
            
            # Filter for kitchen-relevant objects
            kitchen_objects = {'refrigerator', 'oven', 'microwave', 'sink', 'dining table'}
            
            # Modern ultralytics API format
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Get box coordinates, confidence, and class
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        conf = box.conf[0].cpu().numpy()
                        cls = box.cls[0].cpu().numpy()
                        
                        class_name = self.yolo_model.names[int(cls)]
                        if class_name in kitchen_objects and conf > 0.5:
                            detected_objects.append(DetectedObject(
                                name=class_name,
                                confidence=float(conf),
                                bbox=[int(x1), int(y1), int(x2-x1), int(y2-y1)]  # [x, y, w, h]
                            ))
            
            return detected_objects
            
        except Exception as e:
            print(f"YOLO detection error: {e}")
            return []
    
    def analyze_kitchen(self, image_path: str) -> Dict[str, Any]:
        """Analyze kitchen image using LangGraph + Bedrock"""
        print("🔍 Running kitchen analysis with LangGraph + Bedrock...")
        
        # Step 1: YOLO Detection
        detected_objects = self._detect_objects_yolo(image_path)
        print(f"📊 Detected {len(detected_objects)} kitchen objects")
        
        # Step 2: Prepare objects for analysis
        objects_data = [obj.model_dump() for obj in detected_objects]
        objects_json = json.dumps(objects_data, indent=2)
        
        # Step 3: LangGraph Analysis with Bedrock
        user_prompt = f"""
        Analyze this kitchen image. I've detected these objects using YOLO:
        
        {objects_json}
        
        Please provide:
        1. Kitchen layout assessment
        2. Renovation recommendations  
        3. Material suggestions
        4. Cost considerations for Australian market
        
        Use the analyze_kitchen_objects tool for detailed analysis.
        """
        
        # Invoke the graph
        response = self.graph.invoke({
            "messages": [HumanMessage(content=user_prompt)]
        })
        
        # Extract analysis
        final_message = response["messages"][-1].content
        
        # Calculate areas and materials
        materials = self._infer_materials(detected_objects)
        measurements = self._calculate_measurements(detected_objects)
        
        return {
            "image_path": image_path,
            "detected_objects": [obj.model_dump() for obj in detected_objects],
            "materials": [mat.model_dump() for mat in materials],
            "measurements": measurements,
            "bedrock_analysis": final_message,
            "status": "completed"
        }
    
    def _infer_materials(self, detected_objects: List[DetectedObject]) -> List[MaterialInfo]:
        """Infer materials from detected objects"""
        materials = []
        
        # Material mapping
        material_map = {
            "cabinet": MaterialType.WOOD,
            "countertop": MaterialType.GRANITE,
            "refrigerator": MaterialType.STAINLESS_STEEL,
            "sink": MaterialType.STAINLESS_STEEL,
            "oven": MaterialType.STAINLESS_STEEL,
            "microwave": MaterialType.STAINLESS_STEEL,
            "dining table": MaterialType.WOOD,
            "flooring": MaterialType.TILE
        }
        
        # Add detected object materials
        for obj in detected_objects:
            if obj.name in material_map:
                area_sqm = (obj.bbox[2] * obj.bbox[3]) / 10764  # Convert pixels to sq m
                materials.append(MaterialInfo(
                    material_type=material_map[obj.name],
                    area_sqm=area_sqm,
                    location=obj.name
                ))
        
        # Add inferred materials if kitchen detected
        if detected_objects:
            materials.extend([
                MaterialInfo(material_type=MaterialType.WOOD, area_sqm=14.0, location="cabinet"),
                MaterialInfo(material_type=MaterialType.GRANITE, area_sqm=7.5, location="countertop"),
                MaterialInfo(material_type=MaterialType.TILE, area_sqm=18.5, location="flooring")
            ])
        
        return materials
    
    def _calculate_measurements(self, detected_objects: List[DetectedObject]) -> Dict[str, float]:
        """Calculate kitchen measurements"""
        total_area = sum((obj.bbox[2] * obj.bbox[3]) / 10764 for obj in detected_objects)
        
        return {
            "total_kitchen_area": max(total_area, 40.0),  # Minimum realistic kitchen size
            "cabinet_area": 14.0,
            "countertop_area": 7.5,
            "flooring_area": 18.5,
            "appliance_count": len([obj for obj in detected_objects if obj.name in ['refrigerator', 'oven', 'microwave']])
        }


def main():
    """Test the kitchen analyzer"""
    analyzer = KitchenAnalyzerYOLO()
    
    # Test with kitchen image
    result = analyzer.analyze_kitchen("/home/ubuntu/workspace/TechSummit_2025/sample_images/img_1.jpg")
    
    print("\n🏠 Kitchen Analysis Results:")
    print("=" * 50)
    print(f"Objects detected: {len(result['detected_objects'])}")
    print(f"Materials found: {len(result['materials'])}")
    print(f"Total area: {result['measurements']['total_kitchen_area']:.1f} sq m")
    print(f"\nBedrock Analysis:\n{result['bedrock_analysis']}")


if __name__ == "__main__":
    main()
