"""
Real YOLO inference script for SageMaker endpoint
"""

import json
import base64
import io
import torch
from PIL import Image
import numpy as np
from ultralytics import YOLO


def model_fn(model_dir):
    """Load real YOLO model"""
    # Load YOLOv5 model using modern ultralytics API
    model = YOLO('yolov5s.pt')
    return model


def input_fn(request_body, request_content_type):
    """Parse input data"""
    if request_content_type == 'application/json':
        input_data = json.loads(request_body)
        image_data = input_data['instances'][0]['data']
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))
        return image
    else:
        raise ValueError(f"Unsupported content type: {request_content_type}")


def predict_fn(input_data, model):
    """Run real YOLO prediction"""
    results = model(input_data)
    
    boxes = []
    scores = []
    classes = []
    
    # Parse results using modern ultralytics API
    for result in results:
        if result.boxes is not None:
            for box in result.boxes:
                # Get box coordinates, confidence, and class
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = box.conf[0].cpu().numpy()
                cls = box.cls[0].cpu().numpy()
                
                boxes.append([float(x1), float(y1), float(x2-x1), float(y2-y1)])
                scores.append(float(conf))
                classes.append(int(cls))
    
    return {
        'boxes': boxes,
        'scores': scores,
        'classes': classes
    }


def output_fn(prediction, content_type):
    """Format output"""
    if content_type == 'application/json':
        return json.dumps({'predictions': [prediction]})
    else:
        raise ValueError(f"Unsupported content type: {content_type}")
