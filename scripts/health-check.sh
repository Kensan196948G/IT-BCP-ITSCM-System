#!/usr/bin/env bash
# health-check.sh - Check health of all docker-compose services
# Exit code: 0 = all OK, 1 = one or more failures

set -euo pipefail

BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:3000}"
TIMEOUT=5

# Colours (disabled when not a terminal)
if [ -t 1 ]; then
    GREEN='\033[0;32m'
    RED='\033[0;31m'
    YELLOW='\033[0;33m'
    NC='\033[0m'
else
    GREEN='' RED='' YELLOW='' NC=''
fi

overall_exit=0

declare -a SERVICE_NAMES=()
declare -a SERVICE_URLS=()
declare -a SERVICE_STATUSES=()
declare -a SERVICE_CODES=()

check_service() {
    local name="$1"
    local url="$2"
    local expected_code="${3:-200}"

    local http_code
    http_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time "$TIMEOUT" "$url" 2>/dev/null || echo "000")

    SERVICE_NAMES+=("$name")
    SERVICE_URLS+=("$url")
    SERVICE_CODES+=("$http_code")

    if [ "$http_code" = "$expected_code" ]; then
        SERVICE_STATUSES+=("OK")
    else
        SERVICE_STATUSES+=("FAIL")
        overall_exit=1
    fi
}

echo ""
echo "IT-BCP-ITSCM-System Health Check"
echo "================================="
echo ""

# Check services
check_service "Backend API" "${BACKEND_URL}/api/health" "200"
check_service "Frontend"    "${FRONTEND_URL}/"           "200"

# Print table
printf "%-20s %-35s %-10s %-10s\n" "SERVICE" "URL" "HTTP" "STATUS"
printf "%-20s %-35s %-10s %-10s\n" "-------" "---" "----" "------"

for i in "${!SERVICE_NAMES[@]}"; do
    status="${SERVICE_STATUSES[$i]}"
    if [ "$status" = "OK" ]; then
        color="$GREEN"
    else
        color="$RED"
    fi
    printf "%-20s %-35s %-10s ${color}%-10s${NC}\n" \
        "${SERVICE_NAMES[$i]}" \
        "${SERVICE_URLS[$i]}" \
        "${SERVICE_CODES[$i]}" \
        "$status"
done

echo ""
if [ "$overall_exit" -eq 0 ]; then
    echo -e "${GREEN}All services are healthy.${NC}"
else
    echo -e "${RED}One or more services are unhealthy.${NC}"
fi

exit "$overall_exit"
