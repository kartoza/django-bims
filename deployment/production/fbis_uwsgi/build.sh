#!/usr/bin/env bash

if [ -z "$REPO_NAME" ]; then
	REPO_NAME=kartoza
fi

if [ -z "$IMAGE_NAME" ]; then
	IMAGE_NAME=freshwaterbiodiversity
fi

if [ -z "$TAG_NAME" ]; then
	TAG_NAME=v3.6
fi

if [ -z "$BUILD_ARGS" ]; then
	BUILD_ARGS="--pull --no-cache"
fi

# Build Args Environment

if [ -z "$HEALTHYRIVERS_BRANCH" ]; then
	HEALTHYRIVERS_BRANCH=3.0
fi

if [ -z "$BIMS_IMAGE_VERSION" ]; then
	BIMS_IMAGE_VERSION=latest
fi

echo "HEALTHYRIVERS_BRANCH=${HEALTHYRIVERS_BRANCH}"

echo "Build: $REPO_NAME/$IMAGE_NAME:$TAG_NAME"

docker build -t ${REPO_NAME}/${IMAGE_NAME} \
	--build-arg HEALTHYRIVERS_BRANCH=${HEALTHYRIVERS_BRANCH} --build-arg BIMS_IMAGE_VERSION=${BIMS_IMAGE_VERSION} \
	${BUILD_ARGS} .
docker tag ${REPO_NAME}/${IMAGE_NAME}:latest ${REPO_NAME}/${IMAGE_NAME}:${TAG_NAME}
docker push ${REPO_NAME}/${IMAGE_NAME}:${TAG_NAME}
