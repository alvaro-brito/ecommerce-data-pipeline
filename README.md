# E-commerce Data Pipeline

A complete data pipeline for e-commerce analytics, implementing Modern Data Stack architecture with Extract, Load, and Transform (ELT).

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   PostgreSQL    │     │  Apache Airflow │     │   ClickHouse    │
│   (OLTP Source) │────▶│  (Orchestration)│────▶│ (Data Warehouse)│
│     :5432       │     │     :8080       │     │   :8123/:9000   │
└─────────────────┘     └────────┬────────┘     └────────┬────────┘
                                 │                       │
                                 ▼                       │
                        ┌─────────────────┐              │
                        │ Webhook Server  │              │
                        │ (dbt Trigger)   │              │
                        │     :5001       │              │
                        └────────┬────────┘              │
                                 │                       │
                                 ▼                       ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │      dbt        │     │ Apache Superset │
                        │ (Transformation)│────▶│ (Visualization) │
                        └─────────────────┘     │     :8088       │
                                                └─────────────────┘
```

## Technologies

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| OLTP Database | PostgreSQL | 15-alpine | Source transactional system |
| Data Warehouse | ClickHouse | latest | Columnar analytical database |
| Orchestration | Apache Airflow | 2.7.3 | DAG scheduling and execution |
| Transformation | dbt-core | 1.7.0 | SQL transformations and modeling |
| Visualization | Apache Superset | 3.1.0 | Dashboards and BI |
| Automation | Flask/Python | 3.11 | Webhook server for triggers |

## Prerequisites

- **Docker** >= 20.10
- **Docker Compose** >= 2.0
- **RAM** >= 8GB (recommended)
- **Disk Space** >= 10GB
- **Available Ports**: 5432, 5433, 8080, 8088, 8123, 9000, 5001

### Check Prerequisites

```bash
# Docker
docker --version

# Docker Compose
docker-compose --version

# Check ports in use (macOS/Linux)
lsof -i :5432,5433,8080,8088,8123,9000,5001
```

## Quick Start

### 1. Clone and Start

```bash
# Start all services
./run.sh

# Wait ~2 minutes for complete initialization
```

### 2. Check Status

```bash
# View container status
docker-compose ps

# Check logs for a specific service
docker logs <container-name>
```

### 3. Access Interfaces

| Service | URL | Username | Password |
|---------|-----|----------|----------|
| Airflow | http://localhost:8080 | admin | admin |
| Superset | http://localhost:8088 | admin | admin |
| ClickHouse | http://localhost:8123 | default | clickhouse123 |

### 4. Stop Services

```bash
./stop.sh
```

## Project Structure

```
ecommerce-data-pipeline/
├── docker-compose.yml          # All service definitions
├── run.sh                      # Script to start the project
├── stop.sh                     # Script to stop the project
├── check_all_works.sh          # Verification script
├── README.md                   # This file
│
├── postgres/                   # PostgreSQL (OLTP source)
│   └── init/
│       ├── 01-init-schema.sql  # Table creation
│       └── 02-seed-data.sql    # Sample data
│
├── clickhouse/                 # ClickHouse (Data Warehouse)
│   └── init/
│       └── 01-init-tables.sql  # Warehouse structure
│
├── airflow/                    # Apache Airflow
│   ├── Dockerfile              # Custom image
│   ├── dags/
│   │   └── elt_pipeline.py     # Main pipeline DAG
│   ├── logs/                   # Execution logs
│   └── plugins/                # Custom plugins
│
├── dbt/                        # dbt (transformations)
│   ├── dbt_project.yml         # Project configuration
│   ├── profiles.yml            # ClickHouse connection
│   └── models/
│       ├── staging/            # Staging layer (views)
│       │   ├── stg_customers.sql
│       │   ├── stg_products.sql
│       │   ├── stg_orders.sql
│       │   └── stg_order_items.sql
│       └── marts/              # Marts layer (tables)
│           ├── fact_sales.sql
│           └── agg_sales_by_state.sql
│
├── superset/                   # Apache Superset
│   └── config/
│       └── superset_config.py  # Configuration
│
└── scripts/                    # Utility scripts
    └── webhook_server.py       # Flask server for triggers
```

## Components

### PostgreSQL (OLTP Source)

Transactional database that simulates an e-commerce system.

**Schema:**

```sql
-- Customers
customers (customer_id, first_name, last_name, email, phone, state, city, created_at)

-- Products
products (product_id, product_name, category, price, cost, created_at)

-- Orders
orders (order_id, customer_id, order_date, status, total_amount)

-- Order Items
order_items (order_item_id, order_id, product_id, quantity, unit_price, subtotal)
```

**Sample Data:**
- 10 customers
- 15 products (5 categories)
- 100 orders
- ~294 order items

**Connection:**
```
Host: localhost
Port: 5432
Database: ecommerce_db
User: ecommerce
Password: ecommerce123
```

### ClickHouse (Data Warehouse)

Columnar database optimized for analytical queries.

**Schemas:**
- `raw` - Raw data extracted from PostgreSQL
- `analytics` - Data transformed by dbt

**Connection:**
```
HTTP: http://localhost:8123
Native: localhost:9000
User: default
Password: clickhouse123
```

### Apache Airflow (Orchestration)

Manages the ELT pipeline through DAGs (Directed Acyclic Graphs).

**Main DAG: `elt_pipeline`**

```
create_clickhouse_databases
           │
           ▼
    ┌──────┴──────────┐
    │  TaskGroup      │
    │  load_data      │
    ├─────────────────┤
    │ load_customers ─┐
    │ load_products ──┼─► Parallel execution
    │ load_orders ────┤
    │ load_order_items┘
    └──────┬──────────┘
           │
           ▼
run_dbt_transformations (webhook)
```

**Configuration:**
- Schedule: `@daily`
- Start Date: 2025-01-01
- Retries: 2
- Retry Delay: 5 minutes

**Important Files:**
- `airflow/dags/elt_pipeline.py` - DAG definition
- `airflow/Dockerfile` - Image with additional providers

### dbt (Transformation)

Performs SQL transformations on data in ClickHouse.

**Layers:**

| Layer | Materialization | Prefix | Description |
|-------|-----------------|--------|-------------|
| Staging | view | `stg_` | Cleaning and standardization |
| Marts | table | `fact_`, `agg_` | Business models |

**Models:**

```
models/
├── staging/
│   ├── stg_customers.sql    # Customer dimension
│   ├── stg_products.sql     # Product dimension (+ profit_margin)
│   ├── stg_orders.sql       # Order fact (+ date fields)
│   └── stg_order_items.sql  # Order items
│
└── marts/
    ├── fact_sales.sql          # Denormalized sales fact
    └── agg_sales_by_state.sql  # Aggregation by state
```

**Run dbt manually:**

```bash
# Enter the container
docker exec -it dbt bash

# Run models
dbt run

# Run tests
dbt test

# Generate documentation
dbt docs generate
```

### Webhook Server (Automation)

Flask server that receives webhooks from Airflow and executes dbt.

**Endpoints:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/webhook/manual` | Airflow trigger |
| POST | `/webhook` | External trigger |
| GET | `/health` | Health check |
| GET | `/status` | Service status |

**Test manually:**

```bash
# Health check
curl http://localhost:5001/health

# Trigger dbt
curl -X POST http://localhost:5001/webhook/manual
```

### Apache Superset (Visualization)

BI platform for creating dashboards.

**Connect to ClickHouse:**

1. Access http://localhost:8088
2. Login: admin / admin
3. Settings → Database Connections → + Database
4. Select "ClickHouse"
5. SQLAlchemy URI: `clickhouse+native://default:clickhouse123@clickhouse-server:9000/analytics`

## Data Flow

### 1. Extraction (PostgreSQL → ClickHouse)

Airflow executes queries on PostgreSQL and inserts data into the `raw` schema in ClickHouse.

```python
# DAG example
SELECT * FROM customers;
# → INSERT INTO raw.customers
```

### 2. Transformation (dbt)

dbt transforms data from the `raw` schema to `analytics`.

```sql
-- Example: stg_orders.sql
SELECT
    order_id,
    customer_id,
    order_date,
    toYear(order_date) as order_year,
    toMonth(order_date) as order_month,
    toQuarter(order_date) as order_quarter,
    status,
    total_amount
FROM raw.orders
```

### 3. Aggregation (Marts)

Final models ready for consumption.

```sql
-- fact_sales: Denormalized sales
-- agg_sales_by_state: Metrics by state
```

## Maintenance

### Add a New Table to the Pipeline

1. **PostgreSQL** - Create table in `postgres/init/01-init-schema.sql`

2. **ClickHouse** - Create raw table in `clickhouse/init/01-init-tables.sql`

3. **Airflow** - Add extraction task in `airflow/dags/elt_pipeline.py`:

```python
@task
def load_new_table():
    # Extract from PostgreSQL
    pg_hook = PostgresHook(postgres_conn_id='postgres_source')
    data = pg_hook.get_records("SELECT * FROM new_table")

    # Insert into ClickHouse
    # ...
```

4. **dbt** - Create staging model in `dbt/models/staging/stg_new_table.sql`:

```sql
{{ config(materialized='view') }}

SELECT *
FROM raw.new_table
```

5. Update source in `dbt/models/sources.yml`

### Add a New dbt Model

1. Create SQL file in `dbt/models/staging/` or `dbt/models/marts/`

2. Define configuration:

```sql
{{ config(
    materialized='table',  -- or 'view'
    engine='MergeTree()',
    order_by='sort_field'
) }}

SELECT ...
FROM {{ ref('previous_model') }}
```

3. Execute:

```bash
docker exec -it dbt dbt run --select model_name
```

### Modify Airflow Schedule

Edit `airflow/dags/elt_pipeline.py`:

```python
@dag(
    schedule_interval='0 2 * * *',  # Run at 2 AM daily
    # or '@hourly', '@daily', '@weekly'
)
```

### Add a New Airflow Provider

Edit `airflow/Dockerfile`:

```dockerfile
RUN pip install --no-cache-dir \
    apache-airflow-providers-new-provider==X.Y.Z
```

Rebuild:

```bash
docker-compose build airflow-webserver airflow-scheduler
docker-compose up -d
```

## Troubleshooting

### Container Won't Start

```bash
# View container logs
docker logs <container-name>

# Check if port is in use
lsof -i :<port>

# Recreate container
docker-compose up -d --force-recreate <service>
```

### Airflow DAG Not Showing

```bash
# Check for syntax errors
docker exec -it airflow-webserver airflow dags list

# View scheduler logs
docker logs airflow-scheduler
```

### dbt Execution Fails

```bash
# Enter the container
docker exec -it dbt bash

# Test connection
dbt debug

# View detailed logs
dbt run --debug
```

### ClickHouse Won't Accept Connection

```bash
# Check if it's running
docker exec -it clickhouse-server clickhouse-client --password clickhouse123

# Test via HTTP
curl http://localhost:8123/ping
```

### Superset Won't Connect to ClickHouse

1. Check if driver is installed:
```bash
docker exec -it superset pip list | grep clickhouse
```

2. Use container hostname (not localhost):
```
clickhouse+native://default:clickhouse123@clickhouse-server:9000/analytics
```

### Webhook Server Not Responding

```bash
# Check logs
docker logs webhook-server

# Test health
curl http://localhost:5001/health
```

### Clean Everything and Start Over

```bash
# Stop and remove volumes
docker-compose down -v

# Remove custom images
docker rmi ecommerce-pipeline-airflow-webserver
docker rmi ecommerce-pipeline-airflow-scheduler

# Start from scratch
./run.sh
```

## Environment Variables

### PostgreSQL Source

| Variable | Value | Description |
|----------|-------|-------------|
| POSTGRES_USER | ecommerce | Database user |
| POSTGRES_PASSWORD | ecommerce123 | Password |
| POSTGRES_DB | ecommerce_db | Database name |

### ClickHouse

| Variable | Value | Description |
|----------|-------|-------------|
| CLICKHOUSE_DB | ecommerce | Default database |
| CLICKHOUSE_USER | default | User |
| CLICKHOUSE_PASSWORD | clickhouse123 | Password |

### Airflow

| Variable | Value |
|----------|-------|
| AIRFLOW__CORE__EXECUTOR | LocalExecutor |
| AIRFLOW__CORE__SQL_ALCHEMY_CONN | postgresql+psycopg2://airflow:airflow@airflow-db:5432/airflow |
| AIRFLOW__CORE__LOAD_EXAMPLES | false |

### Superset

| Variable | Value |
|----------|-------|
| SUPERSET_SECRET_KEY | your-secret-key-change-this |
| SUPERSET_ADMIN_USERNAME | admin |
| SUPERSET_ADMIN_PASSWORD | admin |

## Volumes

| Volume | Container | Path | Description |
|--------|-----------|------|-------------|
| postgres_data | postgres-source | /var/lib/postgresql/data | PostgreSQL data |
| clickhouse_data | clickhouse-server | /var/lib/clickhouse | ClickHouse data |
| clickhouse_logs | clickhouse-server | /var/log/clickhouse-server | ClickHouse logs |
| airflow_db_data | airflow-db | /var/lib/postgresql/data | Airflow metadata |
| superset_data | superset | /var/lib/superset | Superset data |

## Network

All containers share the `ecommerce-pipeline` network (bridge).

**Inter-container Communication:**
- Use container name as hostname
- Example: `clickhouse-server:9000` (not `localhost:9000`)

## Ports

| Host Port | Container Port | Service |
|-----------|----------------|---------|
| 5432 | 5432 | PostgreSQL Source |
| 5433 | 5432 | PostgreSQL Airflow |
| 8080 | 8080 | Airflow Webserver |
| 8088 | 8088 | Superset |
| 8123 | 8123 | ClickHouse HTTP |
| 9000 | 9000 | ClickHouse Native |
| 5001 | 5000 | Webhook Server |

