# Lambda container image for secure Python code execution
FROM public.ecr.aws/lambda/python:3.12

# Copy handler code
COPY handler.py ${LAMBDA_TASK_ROOT}/

# Set the handler
CMD ["handler.lambda_handler"]
