
## Build docker container

On local machine:

```
cd peakScout
docker build -t peakscout-lambda -f aws/Dockerfile .
```


### Test locally (optional)

```
# 1. Run the container
docker run -p 9000:8080 peakscout-lambda

# 2. In new terminal, test with curl in another terminal:
curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" \
  -H "Content-Type: application/json" \
  -d '{
    "command": "peak2gene",
    "parameters": {
      "peak_file": "test/test_MACS2.bed",
      "peak_type": "MACS2",
      "species": "test", 
      "k": 3,
      "ref_dir": "test/test-reference",
      "output_name": "test_MACS2",
      "output_dir": "test/results/",
      "output_type": "csv"
    }
  }'

# 3. In new terminal, check if test output is saved
docker ps # and get process ID
docker exec -it <container_id> /bin/bash # exec into running container (from step 1)
cat test/results/test_MACS2.csv # or whatever you expect
```

## EC2 instance (one time setup)


Had to create EC2 instance with IAM role that has ECR full access and S3 read access

```
Step 1: Create IAM Role for EC2

AWS Console → IAM → Roles → Create role
Trusted entity: AWS service → EC2
Permissions: Add AmazonEC2ContainerRegistryPowerUser
Role name: EC2-ECR-Push-Role
Create role

Step 2: Attach Role to EC2 Instance

AWS Console → EC2 → Instances
Select your instance → Actions → Security → Modify IAM role
Choose: EC2-ECR-Push-Role
Update IAM role

Then in EC2 instance, run the following commands:

rm -rf ~/.aws/credentials
rm -rf ~/.aws/config

# Verify the instance is using the IAM role
aws sts get-caller-identity
```

or restart instance.

## Export docker image to file and upload to S3

```
# On your local machine
docker build -t peakscout-lambda -f aws/Dockerfile .
docker save peakscout-lambda:latest -o peakscout-lambda.tar
gzip -f peakscout-lambda.tar
aws s3 cp peakscout-lambda.tar.gz s3://cds-peakscout-public/
```

## Load container into ECR repository - S3 to EC2 to ECR

In EC2 instance - https://us-east-1.console.aws.amazon.com/ec2/home?region=us-east-1#InstanceDetails:instanceId=i-03649dcd656f59fb6
* Docker installed
* aws role configured

Connect to it via https://us-east-1.console.aws.amazon.com/ec2/home?region=us-east-1#ConnectToInstance:instanceId=i-03649dcd656f59fb6, select `Connect using a Public IP` and click on `Connect` button.

Then run the following commands from the web-based terminal:

```
# Download container image from S3
aws s3 cp s3://cds-peakscout-public/peakscout-lambda.tar.gz ./

# Load image
docker load < peakscout-lambda.tar.gz

# Push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 802236546356.dkr.ecr.us-east-1.amazonaws.com
docker tag peakscout-lambda:latest 802236546356.dkr.ecr.us-east-1.amazonaws.com/peakscout-lambda:latest
docker push 802236546356.dkr.ecr.us-east-1.amazonaws.com/peakscout-lambda:latest

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


```
# this doesn't work, due to insufficient permissions
LAMBDA_FUNCTION="test2-peakscout-with-container"

aws lambda update-function-code \
    --function-name ${LAMBDA_FUNCTION} \
    --image-uri 802236546356.dkr.ecr.us-east-1.amazonaws.com/peakscout-lambda:latest
```


