#!/bin/bash

# ============================================================================
# Script: check_all_works.sh
# Description: Verifies if all project components are working correctly
# ============================================================================

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Control variables
CHECKS_PASSED=0
CHECKS_FAILED=0
CHECKS_WARNING=0

# Functions
log_success() { echo -e "${GREEN}[✓]${NC} $1"; ((CHECKS_PASSED++)); }
log_error() { echo -e "${RED}[✗]${NC} $1"; ((CHECKS_FAILED++)); }
log_warning() { echo -e "${YELLOW}[⚠]${NC} $1"; ((CHECKS_WARNING++)); }
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }

print_header() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}  🔍 Data Pipeline - Complete Verification${NC}                   ${BLUE}║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_section() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_footer() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}  Verification Summary${NC}"
    echo -e "${BLUE}╠════════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${BLUE}║${NC}  ${GREEN}✓ Passed: $CHECKS_PASSED${NC}"
    echo -e "${BLUE}║${NC}  ${YELLOW}⚠ Warnings: $CHECKS_WARNING${NC}"
    echo -e "${BLUE}║${NC}  ${RED}✗ Failed: $CHECKS_FAILED${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Header
print_header

# ============================================================================
# 1. Check Docker Compose
# ============================================================================
print_section "1. Checking Docker Compose"

if [ -f "docker-compose.yml" ]; then
    log_success "docker-compose.yml found"
else
    log_error "docker-compose.yml not found"
    exit 1
fi

# ============================================================================
# 2. Check Container Status
# ============================================================================
print_section "2. Checking Container Status"

CONTAINERS=("postgres-source" "clickhouse-server" "airflow-db" "airflow-webserver" "airflow-scheduler" "webhook-server" "superset")

for container in "${CONTAINERS[@]}"; do
    if docker ps --filter "name=$container" --filter "status=running" -q | grep -q .; then
        log_success "Container '$container' is running"
    else
        log_warning "Container '$container' is not running"
    fi
done

# ============================================================================
# 3. Check Service Connectivity
# ============================================================================
print_section "3. Checking Service Connectivity"

# PostgreSQL Source
if bash -c "echo > /dev/tcp/localhost/5432" 2>/dev/null; then
    log_success "PostgreSQL Source (port 5432) is accessible"
else
    log_warning "PostgreSQL Source (port 5432) is not accessible"
fi

# ClickHouse HTTP
if bash -c "echo > /dev/tcp/localhost/8123" 2>/dev/null; then
    log_success "ClickHouse HTTP (port 8123) is accessible"
else
    log_warning "ClickHouse HTTP (port 8123) is not accessible"
fi

# ClickHouse Native
if bash -c "echo > /dev/tcp/localhost/9000" 2>/dev/null; then
    log_success "ClickHouse Native (port 9000) is accessible"
else
    log_warning "ClickHouse Native (port 9000) is not accessible"
fi

# Airflow
if bash -c "echo > /dev/tcp/localhost/8080" 2>/dev/null; then
    log_success "Apache Airflow (port 8080) is accessible"
else
    log_warning "Apache Airflow (port 8080) is not accessible"
fi

# Superset
if bash -c "echo > /dev/tcp/localhost/8088" 2>/dev/null; then
    log_success "Apache Superset (port 8088) is accessible"
else
    log_warning "Apache Superset (port 8088) is not accessible"
fi

# Webhook Server
if bash -c "echo > /dev/tcp/localhost/5001" 2>/dev/null; then
    log_success "Webhook Server (port 5001) is accessible"
else
    log_warning "Webhook Server (port 5001) is not accessible"
fi

# ============================================================================
# 4. Check PostgreSQL Source Data
# ============================================================================
print_section "4. Checking PostgreSQL Source Data"

# Check if tables exist
TABLES=$(docker exec postgres-source psql -U ecommerce -d ecommerce_db -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_name IN ('customers', 'orders', 'order_items', 'products');" 2>/dev/null | xargs)

if [ "$TABLES" -eq 4 ]; then
    log_success "All 4 tables exist in PostgreSQL Source"

    # Count records
    CUSTOMERS=$(docker exec postgres-source psql -U ecommerce -d ecommerce_db -t -c "SELECT COUNT(*) FROM customers;" 2>/dev/null | xargs)
    ORDERS=$(docker exec postgres-source psql -U ecommerce -d ecommerce_db -t -c "SELECT COUNT(*) FROM orders;" 2>/dev/null | xargs)
    ORDER_ITEMS=$(docker exec postgres-source psql -U ecommerce -d ecommerce_db -t -c "SELECT COUNT(*) FROM order_items;" 2>/dev/null | xargs)
    PRODUCTS=$(docker exec postgres-source psql -U ecommerce -d ecommerce_db -t -c "SELECT COUNT(*) FROM products;" 2>/dev/null | xargs)

    log_success "Customers: $CUSTOMERS records"
    log_success "Orders: $ORDERS records"
    log_success "Order Items: $ORDER_ITEMS records"
    log_success "Products: $PRODUCTS records"
else
    log_warning "Not all tables were found in PostgreSQL Source"
fi

# ============================================================================
# 5. Check ClickHouse
# ============================================================================
print_section "5. Checking ClickHouse"

if curl -s http://localhost:8123/ping &>/dev/null; then
    log_success "ClickHouse is responding"
else
    log_warning "ClickHouse is not responding to ping"
fi

# ============================================================================
# 6. Check Airflow
# ============================================================================
print_section "6. Checking Apache Airflow"

if curl -s http://localhost:8080/health &>/dev/null; then
    log_success "Apache Airflow is responding"
else
    log_warning "Apache Airflow is not responding"
fi

# ============================================================================
# 7. Check Webhook Server
# ============================================================================
print_section "7. Checking Webhook Server"

if curl -s http://localhost:5001/health &>/dev/null; then
    log_success "Webhook Server is responding"
else
    log_warning "Webhook Server is not responding"
fi

# ============================================================================
# 8. Check Apache Superset
# ============================================================================
print_section "8. Checking Apache Superset"

if curl -s http://localhost:8088 &>/dev/null; then
    log_success "Apache Superset is responding"
else
    log_warning "Apache Superset is not responding"
fi

# ============================================================================
# 9. Access Credentials
# ============================================================================
print_section "9. Access Credentials"

echo -e "${YELLOW}PostgreSQL Source:${NC}"
echo "  Host: localhost | Port: 5432 | User: ecommerce | Password: ecommerce123 | DB: ecommerce_db"
echo ""
echo -e "${YELLOW}ClickHouse:${NC}"
echo "  HTTP: http://localhost:8123 | Native: localhost:9000 | User: default | Password: clickhouse123"
echo ""
echo -e "${YELLOW}Apache Airflow:${NC}"
echo "  URL: http://localhost:8080 | User: admin | Password: admin"
echo ""
echo -e "${YELLOW}Apache Superset:${NC}"
echo "  URL: http://localhost:8088 | User: admin | Password: admin"
echo ""
echo -e "${YELLOW}Webhook Server:${NC}"
echo "  URL: http://localhost:5001 | Health: http://localhost:5001/health"

# Footer
print_footer

# Status
if [ $CHECKS_FAILED -eq 0 ]; then
    exit 0
else
    exit 1
fi
