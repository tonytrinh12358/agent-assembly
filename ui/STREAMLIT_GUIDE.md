# 🏠 Kitchen Renovation Cost Estimator - Streamlit UI

## Quick Start

### 1. Setup Environment
```bash
cd working_solution
source ../kitchen_analysis/venv/bin/activate  # Use existing venv
pip install streamlit  # Already installed
```

### 2. Configure AWS Bedrock
```bash
# Ensure AWS credentials are configured
aws configure
# Or set environment variables
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
export AWS_DEFAULT_REGION=us-west-2
```

### 3. Launch Streamlit UI
```bash
streamlit run streamlit_app.py
```

### 4. Access the Application
- **Local URL**: http://localhost:8501
- **Network URL**: http://your-ip:8501

## Features

### 🖼️ **Image Upload**
- Drag & drop or browse for kitchen images
- Supports PNG, JPG, JPEG formats
- Real-time image preview

### ⚙️ **Configuration Options**
- **Material Grade**: Economy, Standard, Premium
- **Labor Costs**: Include/exclude labor estimation
- **Real-time Settings**: Changes apply immediately

### 🤖 **AI Analysis Pipeline**
1. **LangGraph Agent**: YOLO object detection + Bedrock analysis
2. **CrewAI Agent**: Multi-agent cost estimation (3 specialized agents)
3. **Strands Orchestrator**: Comprehensive report generation

### 📊 **Results Display**
- **Key Metrics**: Total project cost, cost per sqm
- **Full Report**: Comprehensive analysis with recommendations
- **Download**: JSON export of complete analysis
- **Australian Pricing**: All costs in AUD

## Usage Flow

1. **Upload Image** → Kitchen photo (clear, well-lit)
2. **Configure Settings** → Material grade & labor options
3. **Click Analyze** → Multi-agent AI processing
4. **View Results** → Cost estimates & recommendations
5. **Download Report** → JSON export for records

## Sample Results

### Expected Output
- **Objects Detected**: 2-6 kitchen items
- **Materials Found**: 3-5 material types
- **Total Cost**: $15,000 - $45,000 AUD
- **Analysis Time**: 30-60 seconds

### Cost Breakdown
- **Materials**: 60-70% of total cost
- **Labor**: 30-40% of total cost
- **Contingency**: 15% buffer included

## Troubleshooting

### Common Issues
- **AWS Access**: Ensure Bedrock model access is enabled
- **Image Upload**: Use clear, uncluttered kitchen photos
- **Analysis Timeout**: Large images may take longer to process
- **Cost Display**: Refresh if metrics don't appear

### Error Messages
- `❌ Analysis failed`: Check AWS credentials and Bedrock access
- `🔍 No objects detected`: Try a clearer kitchen image
- `💰 Cost calculation error`: Verify material detection results

## Technical Details

### Architecture
```
Streamlit UI → Strands Agent → LangGraph (YOLO) + CrewAI (Cost) → Bedrock LLM → Results
```

### Dependencies
- **Streamlit**: Web UI framework
- **Multi-Agent**: LangGraph, CrewAI, Strands
- **Computer Vision**: YOLO, OpenCV, PyTorch
- **Cloud AI**: Amazon Bedrock Bedrock 

### Performance
- **Image Processing**: 5-10 seconds
- **AI Analysis**: 20-40 seconds
- **Total Time**: 30-60 seconds per analysis

## Production Deployment

### Docker Deployment
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "streamlit_app.py", "--server.headless", "true"]
```

### Environment Variables
```bash
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
export AWS_DEFAULT_REGION=us-west-2
export STREAMLIT_SERVER_PORT=8501
```

This Streamlit UI provides a complete end-to-end experience for kitchen renovation cost estimation using multi-agent AI!
