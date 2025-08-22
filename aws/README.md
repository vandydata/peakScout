
# AWS, Lambda, Docker
## Build docker container

On local machine:

```
cd peakScout
docker build -t peakscout-lambda -f aws/Dockerfile .
```
### Test locally

```sh
# 1. Run the container
docker run -p 9000:8080 peakscout-lambda
 
# with S3 access
docker run -p 9000:8080 \
  -e AWS_ACCESS_KEY_ID=$(aws configure get aws_access_key_id) \
  -e AWS_SECRET_ACCESS_KEY=$(aws configure get aws_secret_access_key) \
  -e AWS_DEFAULT_REGION=us-east-1 \
  peakscout-lambda:latest

# 2. In new terminal, test with curl in another terminal:
# Test data
curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" \
  -H "Content-Type: application/json" \
  -d '{
    "command": "peak2gene",
    "args": [
      "--peak_file", "test/test_MACS2.bed",
      "--peak_type", "MACS2", 
      "--species", "test",
      "--k", "3",
      "--ref_dir", "test/test-reference",
      "--output_name", "test_MACS2",
      "--o", "test/results/",
      "--output_type", "csv"
    ],
    "return_files": true,
    "debug": true
  }'

# Real ref data
curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" \
  -H "Content-Type: application/json" \
  -d '{
    "command": "peak2gene",
    "args": [
      "--peak_file", "test/test_MACS2.bed",
      "--peak_type", "MACS2",
      "--species", "mm10",
      "--k", "3",
      "--ref_dir", "test/test-reference",
      "--output_name", "test_MACS2",
      "--o", "test/results/",
      "--output_type", "csv"
    ],
    "return_files": true,
    "debug": true
  }'

# Real input data, real ref data
# 202-403-Cha_J__MAFB_WT_R1.macs2_peaks.xls

curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" \
  -H "Content-Type: application/json" \
  -d '{
    "command": "peak2gene",
    "args": [
      "--peak_file", "test/2025-403-Cha_J__MAFB_WT_R1.macs2_peaks.narrowPeak",
      "--peak_type", "MACS2",
      "--species", "hg38",
      "--k", "1",
      "--ref_dir", "test/test-reference",
      "--output_name", "test_MACS2",
      "--o", "test/results/",
      "--output_type", "csv"
    ],
    "return_files": true,
    "debug": false
  }'


# 3. In new terminal, check if test output is saved
docker ps # and get process ID
docker exec -it <container_id> /bin/bash # exec into running container (from step 1)
cat test/results/test_MACS2.csv # or whatever you expect
```


## Push container to ECR repository - local to ECR (preferred)

From local machine to ECR, directly. Required a ` AmazonEC2ContainerRegistryPowerUser` permissions policy be attached to the IAM user by admin.

Execute
```sh
bash aws/02-push-docker-to-ECR.sh
```
or run the following commands manually:

```sh
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $(aws sts get-caller-identity --query Account --output text).dkr.ecr.us-east-1.amazonaws.com

docker tag peakscout-lambda:latest $(aws sts get-caller-identity --query Account --output text).dkr.ecr.us-east-1.amazonaws.com/peakscout-lambda:latest

docker push $(aws sts get-caller-identity --query Account --output text).dkr.ecr.us-east-1.amazonaws.com/peakscout-lambda:latest
## EC2 instance (one time setup)
```

## Push container to ECR repository - S3 to EC2 to ECR (not preferred, this is a workaround)

This is for when you cannot push directly from local machine to ECR due to network restrictions or permission issues..

Had to create EC2 instance with IAM role that has ECR full access and S3 read access

Step 1: Create IAM Role for EC2

* AWS Console → IAM → Roles → Create role
* Trusted entity: AWS service → EC2
* Permissions: Add AmazonEC2ContainerRegistryPowerUser
* Role name: EC2-ECR-Push-Role
* Create role

Step 2: Attach Role to EC2 Instance

* AWS Console → EC2 → Instances
* Select your instance → Actions → Security → Modify IAM role
* Choose: EC2-ECR-Push-Role
* Update IAM role

Then in EC2 instance, run the following commands:
```sh
rm -rf ~/.aws/credentials
rm -rf ~/.aws/config


# Verify the instance is using the IAM role
aws sts get-caller-identity
```

or restart instance.

## Export docker image to file and upload to S3

```sh
# On your local machine
docker build -t peakscout-lambda -f aws/Dockerfile .
docker save peakscout-lambda:latest -o peakscout-lambda.tar
gzip -f peakscout-lambda.tar
aws s3 cp peakscout-lambda.tar.gz s3://cds-peakscout-public/
```

In EC2 instance - https://us-east-1.console.aws.amazon.com/ec2/home?region=us-east-1#InstanceDetails:instanceId=i-03649dcd656f59fb6
* Docker installed
* aws role configured

Connect to it via https://us-east-1.console.aws.amazon.com/ec2/home?region=us-east-1#ConnectToInstance:instanceId=i-03649dcd656f59fb6, select `Connect using a Public IP` and click on `Connect` button.

Then run the following commands from the web-based terminal:

```sh
# Download container image from S3
aws s3 cp s3://cds-peakscout-public/peakscout-lambda.tar.gz ./

# Load image
docker load < peakscout-lambda.tar.gz

# Push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 802236546356.dkr.ecr.us-east-1.amazonaws.com
docker tag peakscout-lambda:latest 802236546356.dkr.ecr.us-east-1.amazonaws.com/peakscout-lambda:latest
docker push 802236546356.dkr.ecr.us-east-1.amazonaws.com/peakscout-lambda:latest

# go to lambda console > Image tab > Deploy new image > Browse > select newest/latest and deploy
# test lambda function in aws console
```




## Create or update Lambda function

### Create new function

via AWS Console, function from container
* Container image: 802236546356.dkr.ecr.us-east-1.amazonaws.com/peakscout-lambda:latest
* Memory: 3008 MB
* Timeout: 15 min
* CORS: Enable CORS
* access: public

### Update existing function after docker update

* AWS Console → Lambda → Your function
* Go to "Image" tab
* Click "Deploy new image"
* Click "Deploy" (it will pull the latest image)
* Wait for "Update successful" message


```sh
# this doesn't work, due to insufficient permissions
LAMBDA_FUNCTION="test2-peakscout-with-container"

aws lambda update-function-code \
    --function-name ${LAMBDA_FUNCTION} \
    --image-uri 802236546356.dkr.ecr.us-east-1.amazonaws.com/peakscout-lambda:latest
```


