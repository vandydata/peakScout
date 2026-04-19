#!/bin/bash
# Build and tag peakScout Docker image for nf-core module

# Set your Docker Hub username here
DOCKER_USER="${DOCKER_USER:-yourusername}"
VERSION="1.0.0"

echo "Building peakScout Docker image..."
docker build -t peakscout:${VERSION} -f Dockerfile .

echo "Tagging image for Docker Hub..."
docker tag peakscout:${VERSION} ${DOCKER_USER}/peakscout:${VERSION}
docker tag peakscout:${VERSION} ${DOCKER_USER}/peakscout:latest

echo "To push to Docker Hub, run:"
echo "  docker login"
echo "  docker push ${DOCKER_USER}/peakscout:${VERSION}"
echo "  docker push ${DOCKER_USER}/peakscout:latest"
echo ""
echo "Then update the container path in:"
echo "  /mnt/d/data/nfcore-modules-peakscout/modules/nf-core/peakscout/main.nf"
echo "  Replace 'YOUR-DOCKER-USER' with '${DOCKER_USER}'"
