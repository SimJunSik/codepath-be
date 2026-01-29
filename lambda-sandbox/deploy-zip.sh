#!/bin/bash
# Deploy Lambda sandbox function using ZIP file

set -e

AWS_PROFILE=${AWS_PROFILE:-codepath}
AWS_REGION=${AWS_REGION:-ap-northeast-2}
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --profile $AWS_PROFILE --query Account --output text)
LAMBDA_FUNCTION_NAME="codepath-code-executor"
ROLE_NAME="codepath-lambda-executor-role"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ZIP_FILE="$SCRIPT_DIR/function.zip"

echo "=== CodePath Lambda Sandbox Deployment (ZIP) ==="
echo "AWS Account: $AWS_ACCOUNT_ID"
echo "Region: $AWS_REGION"
echo ""

# 1. Create ZIP file
echo "[1/3] Creating ZIP package..."
cd "$SCRIPT_DIR"
zip -j "$ZIP_FILE" handler.py
echo "Created: $ZIP_FILE"

# 2. Create IAM role if not exists
echo "[2/3] Checking IAM role..."
ROLE_ARN="arn:aws:iam::$AWS_ACCOUNT_ID:role/$ROLE_NAME"

if ! aws iam get-role --role-name $ROLE_NAME --profile $AWS_PROFILE 2>/dev/null; then
    echo "Creating IAM role: $ROLE_NAME"
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

    aws iam attach-role-policy \
        --role-name $ROLE_NAME \
        --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole \
        --profile $AWS_PROFILE

    echo "Waiting for role to propagate..."
    sleep 10
else
    echo "IAM role already exists: $ROLE_NAME"
fi

# 3. Create or update Lambda function
echo "[3/3] Deploying Lambda function..."

if aws lambda get-function --function-name $LAMBDA_FUNCTION_NAME --profile $AWS_PROFILE --region $AWS_REGION 2>/dev/null; then
    echo "Updating existing Lambda function..."
    aws lambda update-function-code \
        --function-name $LAMBDA_FUNCTION_NAME \
        --zip-file fileb://$ZIP_FILE \
        --profile $AWS_PROFILE \
        --region $AWS_REGION
else
    echo "Creating new Lambda function..."
    aws lambda create-function \
        --function-name $LAMBDA_FUNCTION_NAME \
        --runtime python3.12 \
        --role $ROLE_ARN \
        --handler handler.lambda_handler \
        --zip-file fileb://$ZIP_FILE \
        --timeout 10 \
        --memory-size 256 \
        --profile $AWS_PROFILE \
        --region $AWS_REGION
fi

# Wait for function to be active
echo "Waiting for Lambda function to be ready..."
aws lambda wait function-active --function-name $LAMBDA_FUNCTION_NAME --profile $AWS_PROFILE --region $AWS_REGION 2>/dev/null || sleep 5

# Clean up
rm -f "$ZIP_FILE"

echo ""
echo "=== Deployment Complete ==="
echo "Lambda Function: $LAMBDA_FUNCTION_NAME"
echo "Lambda ARN: arn:aws:lambda:$AWS_REGION:$AWS_ACCOUNT_ID:function:$LAMBDA_FUNCTION_NAME"
echo ""
echo "Test with:"
echo "  aws lambda invoke --function-name $LAMBDA_FUNCTION_NAME --payload '{\"code\": \"def solution(x): return x*2\", \"test_cases\": [{\"input\": {\"x\": 5}, \"expected_output\": 10}]}' --cli-binary-format raw-in-base64-out /dev/stdout --profile $AWS_PROFILE --region $AWS_REGION"
