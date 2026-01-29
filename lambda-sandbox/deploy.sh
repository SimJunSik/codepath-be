#!/bin/bash
# Deploy Lambda sandbox function to AWS

set -e

AWS_PROFILE=${AWS_PROFILE:-codepath}
AWS_REGION=${AWS_REGION:-ap-northeast-2}
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --profile $AWS_PROFILE --query Account --output text)
ECR_REPO="codepath-sandbox-lambda"
LAMBDA_FUNCTION_NAME="codepath-code-executor"
IMAGE_TAG="latest"

echo "=== CodePath Lambda Sandbox Deployment ==="
echo "AWS Account: $AWS_ACCOUNT_ID"
echo "Region: $AWS_REGION"
echo ""

# 1. Create ECR repository if not exists
echo "[1/5] Creating ECR repository..."
aws ecr describe-repositories --repository-names $ECR_REPO --profile $AWS_PROFILE --region $AWS_REGION 2>/dev/null || \
    aws ecr create-repository --repository-name $ECR_REPO --profile $AWS_PROFILE --region $AWS_REGION

# 2. Login to ECR
echo "[2/5] Logging in to ECR..."
aws ecr get-login-password --profile $AWS_PROFILE --region $AWS_REGION | \
    docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# 3. Build image
echo "[3/5] Building Docker image..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
docker build --platform linux/amd64 -t $ECR_REPO:$IMAGE_TAG $SCRIPT_DIR

# 4. Tag and push image
echo "[4/5] Pushing image to ECR..."
docker tag $ECR_REPO:$IMAGE_TAG $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:$IMAGE_TAG
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:$IMAGE_TAG

# 5. Create or update Lambda function
echo "[5/5] Creating/Updating Lambda function..."

# Check if function exists
if aws lambda get-function --function-name $LAMBDA_FUNCTION_NAME --profile $AWS_PROFILE --region $AWS_REGION 2>/dev/null; then
    echo "Updating existing Lambda function..."
    aws lambda update-function-code \
        --function-name $LAMBDA_FUNCTION_NAME \
        --image-uri $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:$IMAGE_TAG \
        --profile $AWS_PROFILE \
        --region $AWS_REGION
else
    echo "Creating new Lambda function..."

    # Create IAM role for Lambda if not exists
    ROLE_NAME="codepath-lambda-executor-role"
    ROLE_ARN="arn:aws:iam::$AWS_ACCOUNT_ID:role/$ROLE_NAME"

    if ! aws iam get-role --role-name $ROLE_NAME --profile $AWS_PROFILE 2>/dev/null; then
        echo "Creating IAM role..."
        aws iam create-role \
            --role-name $ROLE_NAME \
            --assume-role-policy-document '{
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Principal": {"Service": "lambda.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }]
            }' \
            --profile $AWS_PROFILE

        # Attach basic execution policy
        aws iam attach-role-policy \
            --role-name $ROLE_NAME \
            --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole \
            --profile $AWS_PROFILE

        echo "Waiting for role to propagate..."
        sleep 10
    fi

    # Create Lambda function
    aws lambda create-function \
        --function-name $LAMBDA_FUNCTION_NAME \
        --package-type Image \
        --code ImageUri=$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:$IMAGE_TAG \
        --role $ROLE_ARN \
        --timeout 10 \
        --memory-size 256 \
        --profile $AWS_PROFILE \
        --region $AWS_REGION
fi

# Wait for function to be active
echo "Waiting for Lambda function to be active..."
aws lambda wait function-active --function-name $LAMBDA_FUNCTION_NAME --profile $AWS_PROFILE --region $AWS_REGION

echo ""
echo "=== Deployment Complete ==="
echo "Lambda Function: $LAMBDA_FUNCTION_NAME"
echo "Lambda ARN: arn:aws:lambda:$AWS_REGION:$AWS_ACCOUNT_ID:function:$LAMBDA_FUNCTION_NAME"
echo ""
echo "Test with:"
echo "  aws lambda invoke --function-name $LAMBDA_FUNCTION_NAME --payload '{\"code\": \"def solution(x): return x*2\", \"test_cases\": [{\"input\": {\"x\": 5}, \"expected_output\": 10}]}' --cli-binary-format raw-in-base64-out output.json --profile $AWS_PROFILE --region $AWS_REGION && cat output.json"
