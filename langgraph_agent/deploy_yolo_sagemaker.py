"""
Deploy YOLO model to SageMaker endpoint for kitchen object detection
"""

import boto3
import json
import time
from datetime import datetime


class YOLOSageMakerDeployer:
    def __init__(self, region='us-west-2'):
        self.sagemaker = boto3.client('sagemaker', region_name=region)
        self.iam = boto3.client('iam', region_name=region)
        self.region = region
        
    def create_execution_role(self, role_name='YOLOSageMakerRole'):
        """Create IAM role for SageMaker"""
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "sagemaker.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        try:
            response = self.iam.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description='Role for YOLO SageMaker endpoint'
            )
            
            # Attach required policies
            self.iam.attach_role_policy(
                RoleName=role_name,
                PolicyArn='arn:aws:iam::aws:policy/AmazonSageMakerFullAccess'
            )
            
            role_arn = response['Role']['Arn']
            print(f"✓ Created IAM role: {role_arn}")
            return role_arn
            
        except self.iam.exceptions.EntityAlreadyExistsException:
            response = self.iam.get_role(RoleName=role_name)
            role_arn = response['Role']['Arn']
            print(f"✓ Using existing IAM role: {role_arn}")
            return role_arn
    
    def create_model(self, model_name, role_arn):
        """Create SageMaker model"""
        # Using pre-built PyTorch inference container with YOLO
        container_uri = f"763104351884.dkr.ecr.{self.region}.amazonaws.com/pytorch-inference:1.12.0-gpu-py38"
        
        model_config = {
            'ModelName': model_name,
            'ExecutionRoleArn': role_arn,
            'PrimaryContainer': {
                'Image': container_uri,
                'ModelDataUrl': 's3://sagemaker-sample-files/datasets/image/YOLO/model.tar.gz',  # Placeholder
                'Environment': {
                    'SAGEMAKER_PROGRAM': 'inference.py',
                    'SAGEMAKER_SUBMIT_DIRECTORY': '/opt/ml/code'
                }
            }
        }
        
        try:
            self.sagemaker.create_model(**model_config)
            print(f"✓ Created model: {model_name}")
        except self.sagemaker.exceptions.ValidationException as e:
            if "already exists" in str(e):
                print(f"✓ Model {model_name} already exists")
            else:
                raise e
    
    def create_endpoint_config(self, config_name, model_name):
        """Create endpoint configuration"""
        config = {
            'EndpointConfigName': config_name,
            'ProductionVariants': [
                {
                    'VariantName': 'primary',
                    'ModelName': model_name,
                    'InitialInstanceCount': 1,
                    'InstanceType': 'ml.m5.large',  # Use GPU for better performance: ml.g4dn.xlarge
                    'InitialVariantWeight': 1.0
                }
            ]
        }
        
        try:
            self.sagemaker.create_endpoint_config(**config)
            print(f"✓ Created endpoint config: {config_name}")
        except self.sagemaker.exceptions.ValidationException as e:
            if "already exists" in str(e):
                print(f"✓ Endpoint config {config_name} already exists")
            else:
                raise e
    
    def create_endpoint(self, endpoint_name, config_name):
        """Create and deploy endpoint"""
        try:
            self.sagemaker.create_endpoint(
                EndpointName=endpoint_name,
                EndpointConfigName=config_name
            )
            print(f"✓ Creating endpoint: {endpoint_name}")
            
            # Wait for endpoint to be in service
            print("⏳ Waiting for endpoint to be in service...")
            waiter = self.sagemaker.get_waiter('endpoint_in_service')
            waiter.wait(
                EndpointName=endpoint_name,
                WaiterConfig={'Delay': 30, 'MaxAttempts': 20}
            )
            
            print(f"🎉 Endpoint {endpoint_name} is ready!")
            return endpoint_name
            
        except self.sagemaker.exceptions.ValidationException as e:
            if "already exists" in str(e):
                print(f"✓ Endpoint {endpoint_name} already exists")
                return endpoint_name
            else:
                raise e
    
    def deploy_yolo_endpoint(self, endpoint_name=None):
        """Deploy complete YOLO endpoint"""
        if not endpoint_name:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            endpoint_name = f"yolo-kitchen-detection-{timestamp}"
        
        model_name = f"{endpoint_name}-model"
        config_name = f"{endpoint_name}-config"
        
        print("🚀 Deploying YOLO model to SageMaker")
        print("=" * 50)
        
        # Step 1: Create IAM role
        role_arn = self.create_execution_role()
        
        # Step 2: Create model
        self.create_model(model_name, role_arn)
        
        # Step 3: Create endpoint config
        self.create_endpoint_config(config_name, model_name)
        
        # Step 4: Create endpoint
        endpoint_name = self.create_endpoint(endpoint_name, config_name)
        
        print(f"\n✅ Deployment complete!")
        print(f"Endpoint name: {endpoint_name}")
        print(f"Region: {self.region}")
        
        return endpoint_name


def main():
    """Deploy YOLO endpoint"""
    deployer = YOLOSageMakerDeployer()
    
    try:
        endpoint_name = deployer.deploy_yolo_endpoint()
        
        # Save endpoint name for use in kitchen analyzer
        with open('endpoint_config.json', 'w') as f:
            json.dump({
                'endpoint_name': endpoint_name,
                'region': deployer.region,
                'deployed_at': datetime.now().isoformat()
            }, f, indent=2)
        
        print(f"\n📝 Endpoint configuration saved to endpoint_config.json")
        print(f"💡 Set environment variable: export SAGEMAKER_ENDPOINT_NAME={endpoint_name}")
        
    except Exception as e:
        print(f"❌ Deployment failed: {e}")


if __name__ == "__main__":
    main()
