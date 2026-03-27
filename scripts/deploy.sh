#!/usr/bin/env bash
#
# deploy.sh - IT-BCP-ITSCM-System deployment script
#
# Usage: ./scripts/deploy.sh <environment> <region>
#   environment: staging | production
#   region:      east | west | both
#
set -euo pipefail

ENVIRONMENT="${1:-}"
REGION="${2:-}"

if [[ -z "$ENVIRONMENT" || -z "$REGION" ]]; then
  echo "Usage: $0 <environment> <region>"
  echo "  environment: staging | production"
  echo "  region:      east | west | both"
  exit 1
fi

if [[ "$ENVIRONMENT" != "staging" && "$ENVIRONMENT" != "production" ]]; then
  echo "Error: environment must be 'staging' or 'production'"
  exit 1
fi

if [[ "$REGION" != "east" && "$REGION" != "west" && "$REGION" != "both" ]]; then
  echo "Error: region must be 'east', 'west', or 'both'"
  exit 1
fi

IMAGE_TAG="${IMAGE_TAG:-latest}"
RESOURCE_GROUP="${AZURE_RESOURCE_GROUP:-bcp-itscm-rg}"
BACKEND_IMAGE="${BACKEND_IMAGE:-ghcr.io/org/bcp-backend:$IMAGE_TAG}"
FRONTEND_IMAGE="${FRONTEND_IMAGE:-ghcr.io/org/bcp-frontend:$IMAGE_TAG}"

echo "============================================"
echo " IT-BCP-ITSCM-System Deployment"
echo " Environment: $ENVIRONMENT"
echo " Region:      $REGION"
echo " Image Tag:   $IMAGE_TAG"
echo "============================================"

deploy_region() {
  local region_suffix="$1"
  local health_url="$2"

  echo ""
  echo ">>> Deploying to $region_suffix ..."

  az containerapp update \
    --name "bcp-backend-${ENVIRONMENT}-${region_suffix}" \
    --resource-group "$RESOURCE_GROUP" \
    --image "$BACKEND_IMAGE"

  az containerapp update \
    --name "bcp-frontend-${ENVIRONMENT}-${region_suffix}" \
    --resource-group "$RESOURCE_GROUP" \
    --image "$FRONTEND_IMAGE"

  echo ">>> Waiting 30s for deployment to settle..."
  sleep 30

  echo ">>> Running health check: $health_url"
  HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$health_url" || echo "000")
  if [[ "$HTTP_STATUS" == "200" ]]; then
    echo ">>> Health check PASSED (HTTP $HTTP_STATUS)"
  else
    echo ">>> Health check FAILED (HTTP $HTTP_STATUS)"
    echo ""
    echo "=== ROLLBACK INSTRUCTIONS ==="
    echo "To rollback, run:"
    echo "  az containerapp revision list \\"
    echo "    --name bcp-backend-${ENVIRONMENT}-${region_suffix} \\"
    echo "    --resource-group $RESOURCE_GROUP \\"
    echo "    --output table"
    echo ""
    echo "  az containerapp revision activate \\"
    echo "    --name bcp-backend-${ENVIRONMENT}-${region_suffix} \\"
    echo "    --resource-group $RESOURCE_GROUP \\"
    echo "    --revision <previous-revision-name>"
    echo "=========================="
    exit 1
  fi
}

if [[ "$ENVIRONMENT" == "staging" ]]; then
  HEALTH_URL="${STAGING_BACKEND_URL:-https://bcp-backend-staging.example.com}/api/health"
  deploy_region "staging" "$HEALTH_URL"
else
  # Production
  if [[ "$REGION" == "east" || "$REGION" == "both" ]]; then
    EAST_HEALTH="${PROD_EAST_BACKEND_URL:-https://bcp-backend-prod-east.example.com}/api/health"
    deploy_region "east" "$EAST_HEALTH"
  fi

  if [[ "$REGION" == "west" || "$REGION" == "both" ]]; then
    WEST_HEALTH="${PROD_WEST_BACKEND_URL:-https://bcp-backend-prod-west.example.com}/api/health"
    deploy_region "west" "$WEST_HEALTH"
  fi
fi

echo ""
echo "============================================"
echo " Deployment completed successfully!"
echo "============================================"
echo ""
echo "=== ROLLBACK INSTRUCTIONS ==="
echo "If issues are found after deployment:"
echo "1. List revisions:"
echo "   az containerapp revision list --name <app-name> --resource-group $RESOURCE_GROUP --output table"
echo "2. Activate previous revision:"
echo "   az containerapp revision activate --name <app-name> --resource-group $RESOURCE_GROUP --revision <rev>"
echo "=========================="
