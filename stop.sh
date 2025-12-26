#!/bin/bash

# ============================================================================
# Script: stop.sh
# Description: Stops all data pipeline services
# Usage: ./stop.sh
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}  🛑 Data Pipeline - Stopping Services${NC}                       ${BLUE}║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_footer() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}  ✅ All services have been stopped successfully!${NC}            ${BLUE}║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null && ! command -v docker &> /dev/null; then
    log_error "Docker or Docker Compose is not installed"
    exit 1
fi

# Display header
print_header

# Check if we are in the correct directory
if [ ! -f "docker-compose.yml" ]; then
    log_error "docker-compose.yml not found in current directory"
    log_info "Please run this script from the project root directory"
    exit 1
fi

log_info "Stopping all containers..."

# Stop all containers
if docker-compose down 2>/dev/null; then
    log_success "Containers stopped successfully"
else
    log_warning "Some containers may not have been stopped correctly"
fi

# Display final status
log_info "Checking container status..."
RUNNING_CONTAINERS=$(docker-compose ps -q 2>/dev/null | wc -l)

if [ "$RUNNING_CONTAINERS" -eq 0 ]; then
    log_success "No containers are running"
else
    log_warning "$RUNNING_CONTAINERS container(s) are still running"
fi

# Display cleanup options
echo ""
log_info "Additional options:"
echo "  • To remove volumes (CAUTION: deletes data): docker-compose down -v"
echo "  • To remove images: docker-compose down --rmi all"
echo "  • To check logs: docker-compose logs"
echo ""

# Display footer
print_footer

log_info "To restart services, run: ./run.sh"
echo ""
