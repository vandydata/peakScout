
## Build docker

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


