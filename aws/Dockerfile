# Use AWS Lambda Python base image (optimized for Lambda)
FROM public.ecr.aws/lambda/python:3.11

# Lambda-specific dependencies
COPY aws/requirements.txt ${LAMBDA_TASK_ROOT}/requirements-lambda.txt
RUN pip install -r requirements-lambda.txt

# peakScout dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install -r requirements.txt

# Copy the peakScout source code
COPY src/ ${LAMBDA_TASK_ROOT}/

COPY aws/lambda_handler.py ${LAMBDA_TASK_ROOT}/

# Copy test files (useful for testing and validation)
COPY test/ ${LAMBDA_TASK_ROOT}/test/

# Make peakScout executable
RUN chmod +x ${LAMBDA_TASK_ROOT}/peakScout

# Set the handler
CMD ["lambda_handler.entrypoint"]
