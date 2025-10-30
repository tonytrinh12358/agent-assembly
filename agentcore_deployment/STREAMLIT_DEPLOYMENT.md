
# Streamlit App Deployment Guide

## Option 1: AWS App Runner (Recommended - Simplest)

1. **Prepare files:**
   ```bash
   # Files are already created by the deployment script
   ls requirements_streamlit.txt streamlit_orchestrator.py utils.py apprunner.yaml
   ```

2. **Create App Runner service:**
   ```bash
   aws apprunner create-service \
     --service-name "kitchen-renovation-app" \
     --source-configuration '{
       "ImageRepository": {
         "ImageIdentifier": "public.ecr.aws/docker/library/python:3.10-slim",
         "ImageConfiguration": {
           "Port": "8501"
         },
         "ImageRepositoryType": "ECR_PUBLIC"
       },
       "AutoDeploymentsEnabled": false
     }' \
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
