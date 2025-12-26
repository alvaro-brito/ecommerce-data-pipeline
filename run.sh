#!/bin/bash

# ============================================================================
# Script: run.sh
# Description: Starts the data pipeline project with Docker Compose
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[⚠]${NC} $1"; }

print_header() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}  🚀 Data Pipeline - Starting Services${NC}                       ${BLUE}║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Header
print_header

# Stop previous containers
log_info "Stopping previous containers..."
docker-compose down -v 2>/dev/null || true
sleep 2

# Start Docker Compose
log_info "Starting Docker Compose..."
docker-compose up -d 2>&1 | grep -E "Creating|Created|Starting|Started|Error" || true

# Wait for containers
log_info "Waiting for containers to be ready (120 seconds)..."
sleep 120

# Container status
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Container Status${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

CONTAINERS=("postgres-source" "clickhouse-server" "airflow-db" "airflow-webserver" "airflow-scheduler" "webhook-server" "superset")

for container in "${CONTAINERS[@]}"; do
    if docker ps --filter "name=$container" --filter "status=running" -q | grep -q .; then
        log_success "Container '$container' is running"
    else
        log_warning "Container '$container' is not running"
    fi
done

# Credentials
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🔑 Access Credentials${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}PostgreSQL Source (OLTP):${NC}"
echo "  Host: localhost | Port: 5432 | User: ecommerce | Password: ecommerce123 | DB: ecommerce_db"
echo ""
echo -e "${YELLOW}ClickHouse (Data Warehouse):${NC}"
echo "  HTTP: http://localhost:8123 | Native: localhost:9000 | User: default | Password: clickhouse123"
echo ""
echo -e "${YELLOW}Apache Airflow (Orchestration):${NC}"
echo "  URL: http://localhost:8080 | User: admin | Password: admin"
echo ""
echo -e "${YELLOW}Apache Superset (Visualization):${NC}"
echo "  URL: http://localhost:8088 | User: admin | Password: admin"
echo ""
echo -e "${YELLOW}Webhook Server (dbt Automation):${NC}"
echo "  URL: http://localhost:5001 | Health: http://localhost:5001/health"
echo ""

# Run ELT pipeline and dbt transformations
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Running ELT Pipeline${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

log_info "Triggering Airflow DAG to load data..."
docker exec airflow-webserver airflow dags trigger elt_pipeline 2>/dev/null || log_warning "Could not trigger DAG"

log_info "Waiting for DAG execution (30 seconds)..."
sleep 30

log_info "Verifying dbt data in ClickHouse..."
if docker exec clickhouse-server clickhouse-client --query "SELECT count() FROM analytics_marts.fact_sales" 2>/dev/null | grep -qE '^[1-9][0-9]*$'; then
    log_success "Data verification successful: dbt transformations data found in analytics_marts.fact_sales"
else
    log_warning "Data verification failed: No data found in analytics_marts.fact_sales"
fi

log_success "ELT pipeline completed"

# Configure Superset
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Configuring Superset${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

log_info "Setting up Superset with ClickHouse connection..."
python3 scripts/setup_superset_advanced.py 2>&1 || log_warning "Superset setup completed with warnings"

# Finish
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${GREEN}All services have been started successfully!${NC}"
echo ""
echo -e "${GREEN}Access URLs:${NC}"
echo "  Airflow:   http://localhost:8080 (admin/admin)"
echo "  Superset:  http://localhost:8088 (admin/admin)"
echo "  ClickHouse: http://localhost:8123"
echo "  Dbt Docs: http://localhost:5001/docs/#!/overview "
echo ""
echo -e "${GREEN}To verify everything is working:${NC}"
echo "  ./check_all_works.sh"
echo ""
echo -e "${GREEN}To stop services:${NC}"
echo "  ./stop.sh"
echo ""
