#!/usr/bin/env bash
set -euo pipefail

RESOURCE_GROUP="${RESOURCE_GROUP:?RESOURCE_GROUP is required}"
CONTAINERAPPS_ENV="${CONTAINERAPPS_ENV:?CONTAINERAPPS_ENV is required}"
REGISTRY_SERVER="${REGISTRY_SERVER:?REGISTRY_SERVER is required}"
API_IMAGE="${API_IMAGE:?API_IMAGE is required}"
WEB_IMAGE="${WEB_IMAGE:?WEB_IMAGE is required}"

az containerapp create \
  --resource-group "$RESOURCE_GROUP" \
  --environment "$CONTAINERAPPS_ENV" \
  --yaml infra/azure/container-apps/api.containerapp.yaml \
  --image "$REGISTRY_SERVER/$API_IMAGE"

az containerapp create \
  --resource-group "$RESOURCE_GROUP" \
  --environment "$CONTAINERAPPS_ENV" \
  --yaml infra/azure/container-apps/web.containerapp.yaml \
  --image "$REGISTRY_SERVER/$WEB_IMAGE"
