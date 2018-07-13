#!/usr/bin/env bash

export COMPOSE_PROJECT_NAME=bims
export COMPOSE_FILE=deployment/docker-compose.yml:deployment/docker-compose.override.yml
