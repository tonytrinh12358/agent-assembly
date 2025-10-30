#!/usr/bin/env python3
"""
Deploy Streamlit app to AWS using the simplest method
"""

import os
import subprocess
import json

def create_requirements_file():
    """Create requirements.txt for Streamlit deployment"""
    requirements = """
streamlit==1.29.0
boto3==1.34.0
botocore==1.34.0
Pillow==10.0.0
pandas==2.1.0
numpy>=1.24.0,<2.0.0
"""
    
    with open("requirements_streamlit.txt", "w") as f:
        f.write(requirements.strip())
    
    print("✅ Created requirements_streamlit.txt")

def create_dockerfile():
    """Create Dockerfile for Streamlit app"""
    dockerfile_content = """
FROM python:3.10-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements_streamlit.txt .
RUN pip install --no-cache-dir -r requirements_streamlit.txt

# Copy application files
COPY streamlit_orchestrator.py .
COPY utils.py .

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Run streamlit
CMD ["streamlit", "run", "streamlit_orchestrator.py", "--server.port=8501", "--server.address=0.0.0.0"]
"""
    
    with open("Dockerfile.streamlit", "w") as f:
        f.write(dockerfile_content.strip())
    
    print("✅ Created Dockerfile.streamlit")

def create_apprunner_config():
    """Create App Runner configuration"""
    apprunner_config = {
        "version": 1.0,
        "runtime": "python3",
        "build": {
            "commands": {
                "build": [
                    "pip install -r requirements_streamlit.txt"
                ]
            }
        },
        "run": {
            "runtime-version": "3.10",
            "command": "streamlit run streamlit_orchestrator.py --server.port=8501 --server.address=0.0.0.0",
            "network": {
                "port": "8501",
                "env": "PORT"
            },
            "env": [
                {
                    "name": "AWS_DEFAULT_REGION",
                    "value": "us-west-2"
                }
            ]
        }
    }
    
    with open("apprunner.yaml", "w") as f:
        json.dump(apprunner_config, f, indent=2)
    
    print("✅ Created apprunner.yaml")

def create_deployment_guide():
    """Create deployment guide"""
    guide = """
# Streamlit App Deployment Guide

## Option 1: AWS App Runner (Recommended - Simplest)

1. **Prepare files:**
   ```bash
   # Files are already created by the deployment script
   ls requirements_streamlit.txt streamlit_orchestrator.py utils.py apprunner.yaml
   ```

2. **Create App Runner service:**
   ```bash
   aws apprunner create-service \\
     --service-name "kitchen-renovation-app" \\
     --source-configuration '{
       "ImageRepository": {
         "ImageIdentifier": "public.ecr.aws/docker/library/python:3.10-slim",
         "ImageConfiguration": {
           "Port": "8501"
         },
         "ImageRepositoryType": "ECR_PUBLIC"
       },
       "AutoDeploymentsEnabled": false
     }' \\
     --instance-configuration '{
       "Cpu": "0.25 vCPU",
       "Memory": "0.5 GB"
     }'
   ```

## Option 2: AWS ECS with Fargate

1. **Build and push Docker image:**
   ```bash
   # Build the image
   docker build -f Dockerfile.streamlit -t kitchen-renovation-streamlit .
   
   # Tag for ECR
   aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-west-2.amazonaws.com
   docker tag kitchen-renovation-streamlit:latest <account-id>.dkr.ecr.us-west-2.amazonaws.com/kitchen-renovation-streamlit:latest
   docker push <account-id>.dkr.ecr.us-west-2.amazonaws.com/kitchen-renovation-streamlit:latest
   ```

2. **Create ECS task definition and service**

## Option 3: AWS EC2 (Simple)

1. **Launch EC2 instance with appropriate IAM role**
2. **Install dependencies:**
   ```bash
   sudo yum update -y
   sudo yum install -y python3 python3-pip git
   pip3 install -r requirements_streamlit.txt
   ```

3. **Run the app:**
   ```bash
   export AWS_DEFAULT_REGION=us-west-2
   streamlit run streamlit_orchestrator.py --server.port=8501 --server.address=0.0.0.0
   ```

4. **Access via EC2 public IP on port 8501**

## Required IAM Permissions

The deployment needs these permissions:
- `ssm:GetParameter` (to read agent ARNs)
- `bedrock-agentcore:InvokeAgentRuntime` (to call agents)

## Environment Variables

- `AWS_DEFAULT_REGION=us-west-2`
- AWS credentials (via IAM role or environment variables)

## Testing

Once deployed, test the application by:
1. Opening the web interface
2. Entering a kitchen renovation query
3. Verifying the multi-agent analysis works
4. Checking that cost estimates are generated

## Monitoring

- Check CloudWatch logs for any errors
- Monitor agent invocation costs in AWS billing
- Set up CloudWatch alarms for high error rates
"""
    
    with open("STREAMLIT_DEPLOYMENT.md", "w") as f:
        f.write(guide)
    
    print("✅ Created STREAMLIT_DEPLOYMENT.md")

def main():
    """Main deployment preparation function"""
    print("🚀 Preparing Streamlit app for AWS deployment...")
    
    create_requirements_file()
    create_dockerfile()
    create_apprunner_config()
    create_deployment_guide()
    
    print("\n✅ Deployment files created successfully!")
    print("\n📋 Next steps:")
    print("1. Review STREAMLIT_DEPLOYMENT.md for deployment options")
    print("2. Choose your preferred deployment method (App Runner recommended)")
    print("3. Ensure IAM permissions are configured")
    print("4. Deploy and test the application")
    
    print(f"\n🌐 Current local app running at: http://localhost:8502")
    print("🎯 Ready to deploy the multi-agent kitchen renovation system!")

if __name__ == "__main__":
    main()





