"""
Test script for YOLO Kitchen Analyzer
"""

from kitchen_analyzer_yolo import KitchenAnalyzerYOLO, AnalysisState, DetectedObject, MaterialInfo, MaterialType


def test_yolo_analyzer():
    """Test YOLO analyzer without SageMaker endpoint"""
    print("🧪 Testing YOLO Kitchen Analyzer")
    print("=" * 40)
    
    # Test without SageMaker endpoint (uses local detection)
    analyzer = KitchenAnalyzerYOLO()
    
    # Test initialization
    assert analyzer.graph is not None
    print("✓ Analyzer initialization test passed")
    
    # Test full workflow
    result = analyzer.analyze_kitchen("/home/ubuntu/workspace/TechSummit_2025/sample_images/img_1.jpg")
    
    assert result["status"] == "complete"
    assert len(result["detected_objects"]) > 0
    assert len(result["materials"]) > 0
    assert "total_kitchen_area" in result["measurements"]
    
    print("✓ Full YOLO workflow test passed")
    print("✓ Local YOLO detection working")
    
    # Test with mock SageMaker endpoint
    analyzer_sm = KitchenAnalyzerYOLO(sagemaker_endpoint="mock-endpoint")
    assert analyzer_sm.yolo_client is not None
    print("✓ SageMaker client initialization test passed")
    
    print("\n🎉 All YOLO tests passed!")


if __name__ == "__main__":
    test_yolo_analyzer()
