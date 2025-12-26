#!/usr/bin/env python3
"""
Advanced script to automatically configure Superset with:
- Connection to ClickHouse
- Datasets from dbt transformed tables
- Dashboard with charts
"""

import subprocess
import time
import sys
import requests

# Configuration
SUPERSET_URL = "http://localhost:8088"
CLICKHOUSE_HOST = "clickhouse-server"
CLICKHOUSE_PORT = 8123
CLICKHOUSE_USER = "default"
CLICKHOUSE_PASSWORD = "clickhouse123"
CLICKHOUSE_DB = "analytics_marts"

# Colors for output
GREEN = '\033[92m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
RED = '\033[91m'
END = '\033[0m'


def log_info(msg):
    print(f"{BLUE}[INFO]{END} {msg}")


def log_success(msg):
    print(f"{GREEN}[SUCCESS]{END} {msg}")


def log_warning(msg):
    print(f"{YELLOW}[WARNING]{END} {msg}")


def log_error(msg):
    print(f"{RED}[ERROR]{END} {msg}")


def wait_for_superset(max_retries=60):
    """Wait for Superset to be available"""
    log_info("Waiting for Superset to be available...")
    for i in range(max_retries):
        try:
            response = requests.get(f"{SUPERSET_URL}/health", timeout=5)
            if response.status_code == 200:
                log_success("Superset is available!")
                return True
        except:
            pass
        if i < max_retries - 1:
            time.sleep(2)
    log_error("Superset did not become available in time")
    return False


def run_docker_command(command):
    """Execute command inside superset container"""
    full_cmd = f'docker exec superset {command}'
    result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
    return result.returncode == 0, result.stdout, result.stderr


def run_python_in_container(script):
    """Execute Python script inside superset container using stdin pipe"""
    cmd = ['docker', 'exec', '-i', 'superset', 'python']
    result = subprocess.run(cmd, input=script, capture_output=True, text=True)
    return result.returncode == 0, result.stdout, result.stderr


def setup_database():
    """Create ClickHouse database connection in Superset"""
    log_info("Setting up ClickHouse database connection...")

    # Create Python script to run inside container
    script = f'''
import sys
import os
sys.path.insert(0, '/app')
os.chdir('/app')

from superset.app import create_app
app = create_app()

with app.app_context():
    from superset.extensions import db
    from superset.models.core import Database

    # Check if database exists
    existing = db.session.query(Database).filter_by(database_name="ClickHouse DW").first()
    if existing:
        print(f"Database already exists with ID: {{existing.id}}")
    else:
        # Create new database
        new_db = Database(
            database_name="ClickHouse DW",
            sqlalchemy_uri="clickhousedb+connect://{CLICKHOUSE_USER}:{CLICKHOUSE_PASSWORD}@{CLICKHOUSE_HOST}:{CLICKHOUSE_PORT}/{CLICKHOUSE_DB}",
            expose_in_sqllab=True,
            allow_ctas=False,
            allow_cvas=False,
            allow_dml=False,
            allow_run_async=True
        )
        db.session.add(new_db)
        db.session.commit()
        print(f"Database created with ID: {{new_db.id}}")
'''

    # Execute inside container using stdin pipe
    success, stdout, stderr = run_python_in_container(script)

    if success or "already exists" in stdout:
        log_success("Database connection configured!")
        return True
    else:
        log_warning(f"Database setup issue: {stderr}")
        return True  # Continue anyway


def setup_datasets():
    """Create datasets from ClickHouse tables"""
    log_info("Setting up datasets...")

    tables = ["fact_sales", "agg_sales_by_state"]

    for table in tables:
        script = f'''
import sys
import os
import traceback
sys.path.insert(0, '/app')
os.chdir('/app')

from superset.app import create_app
app = create_app()

with app.app_context():
        try:
            from superset.extensions import db
            from superset.models.core import Database
            from superset.connectors.sqla.models import SqlaTable, SqlMetric

            # Get database
            database = db.session.query(Database).filter_by(database_name="ClickHouse DW").first()
            if not database:
                print("Database not found")
                sys.exit(1)

            # Check if dataset exists
            table_obj = db.session.query(SqlaTable).filter_by(table_name="{table}", database_id=database.id).first()
            if not table_obj:
                # Create dataset
                table_obj = SqlaTable(
                    table_name="{table}",
                    database_id=database.id,
                    schema="{CLICKHOUSE_DB}"
                )
                db.session.add(table_obj)
                db.session.flush() # Get ID
                print(f"Dataset {table} created with ID: {{table_obj.id}}")
            else:
                print(f"Dataset {table} already exists with ID: {{table_obj.id}}")

            # Fetch metadata to populate columns
            try:
                print(f"Fetching metadata for {table}...")
                table_obj.fetch_metadata()
                db.session.commit()
            except Exception as e:
                print(f"Error fetching metadata: {{e}}")

            # Define metrics to ensure they exist
            metrics_defs = []
            if "{table}" == "agg_sales_by_state":
                metrics_defs = [
                    {{"metric_name": "sum_total_revenue", "expression": "SUM(total_revenue)", "verbose_name": "Total Revenue", "metric_type": "sum"}},
                    {{"metric_name": "sum_total_orders", "expression": "SUM(total_orders)", "verbose_name": "Total Orders", "metric_type": "sum"}},
                    {{"metric_name": "sum_total_profit", "expression": "SUM(total_profit)", "verbose_name": "Total Profit", "metric_type": "sum"}},
                    {{"metric_name": "avg_profit_margin", "expression": "AVG(profit_margin_pct)", "verbose_name": "Profit Margin %", "metric_type": "avg"}},
                ]
            elif "{table}" == "fact_sales":
                 metrics_defs = [
                    {{"metric_name": "count_rows", "expression": "COUNT(*)", "verbose_name": "Count", "metric_type": "count"}},
                    {{"metric_name": "sum_revenue", "expression": "SUM(revenue)", "verbose_name": "Total Revenue", "metric_type": "sum"}},
                ]

            for m_def in metrics_defs:
                # Check if metric exists in this table
                # We need to query SqlMetric directly or check table_obj.metrics
                # But table_obj.metrics is a list.
                
                # Re-query table to ensure relationships are loaded if it was just created
                # table_obj = db.session.query(SqlaTable).get(table_obj.id)
                
                existing_metric = next((m for m in table_obj.metrics if m.metric_name == m_def["metric_name"]), None)
                
                if not existing_metric:
                    print(f"Adding metric {{m_def['metric_name']}} to {table}")
                    new_metric = SqlMetric(
                        metric_name=m_def["metric_name"],
                        verbose_name=m_def["verbose_name"],
                        metric_type=m_def["metric_type"],
                        expression=m_def["expression"],
                        table_id=table_obj.id
                    )
                    db.session.add(new_metric)
                    # table_obj.metrics.append(new_metric) 
                else:
                    print(f"Metric {{m_def['metric_name']}} already exists in {table}")
                    
            db.session.commit()
        
        except Exception as e:
            print("EXCEPTION_OCCURRED")
            traceback.print_exc()
            sys.exit(1)
'''

        success, stdout, stderr = run_python_in_container(script)

        if success:
            log_success(f"Dataset '{table}' configured!")
        else:
            log_warning(f"Dataset '{table}' issue: {stdout} {stderr}")


def setup_dashboard():
    """Create dashboard"""
    log_info("Setting up dashboard...")

    script = '''
import sys
import os
sys.path.insert(0, '/app')
os.chdir('/app')

from superset.app import create_app
app = create_app()

with app.app_context():
    from superset.extensions import db
    from superset.models.dashboard import Dashboard
    from flask_appbuilder.security.sqla.models import User

    # Check if dashboard exists
    existing = db.session.query(Dashboard).filter_by(slug="ecommerce-analytics").first()
    if existing:
        print(f"Dashboard already exists with ID: {existing.id}")
    else:
        # Get admin user
        admin = db.session.query(User).filter_by(username="admin").first()

        # Create dashboard
        new_dash = Dashboard(
            dashboard_title="E-commerce Analytics",
            slug="ecommerce-analytics",
            published=True,
            json_metadata='{"chart_configuration": {}, "global_chart_configuration": {"scope": {"rootPath": ["ROOT_ID"], "excluded": []}, "chartsInScope": []}, "color_scheme": "", "refresh_frequency": 0, "shared_label_colors": {}, "cross_filters_enabled": true, "default_filters": "{}"}'
        )
        if admin:
            new_dash.owners = [admin]
        db.session.add(new_dash)
        db.session.commit()
        print(f"Dashboard created with ID: {new_dash.id}")
'''

    success, stdout, stderr = run_python_in_container(script)

    if success or "already exists" in stdout:
        log_success("Dashboard configured!")
        return True
    else:
        log_warning(f"Dashboard issue: {stderr[:200]}")
        return True


def setup_charts():
    """Create charts"""
    log_info("Setting up charts...")

    charts = [
        ("Revenue by State", "dist_bar", "agg_sales_by_state", '{"groupby": ["state"], "metrics": ["sum_total_revenue"], "viz_type": "dist_bar", "row_limit": 50, "time_range": "No filter", "color_scheme": "d3Category10", "show_legend": true, "show_bar_value": true, "order_desc": true, "rich_tooltip": true, "y_axis_format": "SMART_NUMBER", "adhoc_filters": []}'),
        ("Orders by State", "dist_bar", "agg_sales_by_state", '{"groupby": ["state"], "metrics": ["sum_total_orders"], "viz_type": "dist_bar", "row_limit": 50, "time_range": "No filter", "color_scheme": "d3Category10", "show_legend": true, "show_bar_value": true, "order_desc": true, "rich_tooltip": true, "y_axis_format": "SMART_NUMBER", "adhoc_filters": []}'),
        ("Sales Distribution", "pie", "agg_sales_by_state", '{"groupby": ["state"], "metric": "sum_total_revenue", "viz_type": "pie", "row_limit": 50, "time_range": "No filter", "color_scheme": "d3Category10", "show_labels": true, "show_legend": true, "adhoc_filters": [], "donut": false}'),
    ]

    for chart_name, viz_type, table_name, params in charts:
        # Escape single quotes in params for Python string
        params_escaped = params.replace("'", "\\'")

        script = f'''
import sys
import os
import traceback
sys.path.insert(0, '/app')
os.chdir('/app')

from superset.app import create_app
app = create_app()

with app.app_context():
    try:
        from superset.extensions import db
        from superset.models.slice import Slice
        from superset.connectors.sqla.models import SqlaTable
        from superset.models.dashboard import Dashboard
        from flask_appbuilder.security.sqla.models import User

        # Check if chart exists
        existing = db.session.query(Slice).filter_by(slice_name="{chart_name}").first()
        if existing:
            print(f"Chart already exists with ID: {{existing.id}} - Updating params")
            existing.params = '{params_escaped}'
            db.session.commit()
        else:
            # Get dataset
            dataset = db.session.query(SqlaTable).filter_by(table_name="{table_name}").first()
            if not dataset:
                print("Dataset not found")
                sys.exit(1)

            # Get admin user
            admin = db.session.query(User).filter_by(username="admin").first()

            # Get dashboard
            dashboard = db.session.query(Dashboard).filter_by(slug="ecommerce-analytics").first()

            # Create chart
            new_chart = Slice(
                slice_name="{chart_name}",
                viz_type="{viz_type}",
                datasource_type="table",
                datasource_id=dataset.id,
                params='{params_escaped}'
            )
            if admin:
                new_chart.owners = [admin]
            
            db.session.add(new_chart)
            db.session.flush()
            
            if dashboard:
                new_chart.dashboards.append(dashboard)
                
            db.session.commit()
            print(f"Chart created with ID: {{new_chart.id}}")
            
    except Exception as e:
        print("EXCEPTION_OCCURRED")
        traceback.print_exc()
        sys.exit(1)
'''

        success, stdout, stderr = run_python_in_container(script)

        if success or "already exists" in stdout:
            log_success(f"Chart '{chart_name}' configured!")
        else:
            log_warning(f"Chart '{chart_name}' issue: {stdout} {stderr}")


def update_dashboard_layout():
    """Update dashboard layout to show charts"""
    log_info("Updating dashboard layout...")
    
    script = '''
import sys
import os
import json
import uuid
import traceback

sys.path.insert(0, '/app')
os.chdir('/app')

from superset.app import create_app
app = create_app()

with app.app_context():
    try:
        from superset.extensions import db
        from superset.models.dashboard import Dashboard
        
        dashboard = db.session.query(Dashboard).filter_by(slug="ecommerce-analytics").first()
        if not dashboard:
            print("Dashboard not found")
            sys.exit(1)
            
        charts = dashboard.slices
        print(f"Found {len(charts)} charts for dashboard")
        
        if not charts:
            print("No charts to layout")
            sys.exit(0)

        # Map charts by name
        chart_map = {c.slice_name: c for c in charts}
        
        revenue_chart = chart_map.get("Revenue by State")
        orders_chart = chart_map.get("Orders by State")
        dist_chart = chart_map.get("Sales Distribution")

        # Create Layout IDs
        root_id = "ROOT_ID"
        grid_id = "GRID_ID"
        header_id = "HEADER_ID"
        row1_id = f"ROW-{uuid.uuid4()}"
        row2_id = f"ROW-{uuid.uuid4()}"
        
        # Chart IDs
        rev_id = f"CHART-{uuid.uuid4()}"
        ord_id = f"CHART-{uuid.uuid4()}"
        dist_id = f"CHART-{uuid.uuid4()}"

        positions = {
            "DASHBOARD_VERSION_KEY": "v2",
            root_id: {
                "type": "ROOT", 
                "id": root_id, 
                "children": [grid_id]
            },
            grid_id: {
                "type": "GRID", 
                "id": grid_id, 
                "children": [header_id, row1_id, row2_id], 
                "parents": [root_id]
            },
            header_id: {
                "type": "HEADER",
                "id": header_id,
                "meta": {"text": "E-commerce Analytics"},
                "parents": [root_id, grid_id]
            },
            row1_id: {
                "type": "ROW", 
                "id": row1_id, 
                "children": [], 
                "parents": [root_id, grid_id],
                "meta": {"background": "BACKGROUND_TRANSPARENT"}
            },
            row2_id: {
                "type": "ROW", 
                "id": row2_id, 
                "children": [], 
                "parents": [root_id, grid_id],
                "meta": {"background": "BACKGROUND_TRANSPARENT"}
            }
        }
        
        # Add charts to positions if they exist
        if revenue_chart:
            positions[rev_id] = {
                "type": "CHART",
                "id": rev_id,
                "children": [],
                "parents": [root_id, grid_id, row1_id],
                "meta": {
                    "chartId": revenue_chart.id,
                    "sliceName": revenue_chart.slice_name,
                    "width": 6, 
                    "height": 50,
                    "uuid": str(uuid.uuid4())
                }
            }
            positions[row1_id]["children"].append(rev_id)

        if orders_chart:
            positions[ord_id] = {
                "type": "CHART",
                "id": ord_id,
                "children": [],
                "parents": [root_id, grid_id, row1_id],
                "meta": {
                    "chartId": orders_chart.id,
                    "sliceName": orders_chart.slice_name,
                    "width": 6, 
                    "height": 50,
                    "uuid": str(uuid.uuid4())
                }
            }
            positions[row1_id]["children"].append(ord_id)

        if dist_chart:
            positions[dist_id] = {
                "type": "CHART",
                "id": dist_id,
                "children": [],
                "parents": [root_id, grid_id, row2_id],
                "meta": {
                    "chartId": dist_chart.id,
                    "sliceName": dist_chart.slice_name,
                    "width": 12, 
                    "height": 63,
                    "uuid": str(uuid.uuid4())
                }
            }
            positions[row2_id]["children"].append(dist_id)

        # Update metadata to include charts in scope
        chart_ids = [c.id for c in charts]
        meta = json.loads(dashboard.json_metadata) if dashboard.json_metadata else {}
        if "global_chart_configuration" in meta:
             meta["global_chart_configuration"]["chartsInScope"] = chart_ids
        
        dashboard.json_metadata = json.dumps(meta)
        dashboard.position_json = json.dumps(positions)
        db.session.commit()
        print("Dashboard layout updated successfully")

    except Exception as e:
        print("EXCEPTION_OCCURRED")
        traceback.print_exc()
        sys.exit(1)
'''
    success, stdout, stderr = run_python_in_container(script)

    if success and "updated successfully" in stdout:
        log_success("Dashboard layout updated!")
    else:
        log_warning(f"Dashboard layout issue: {stdout} {stderr}")


def cleanup_resources():
    """Delete existing dashboard, charts, and datasets"""
    log_info("Cleaning up existing resources...")

    script = '''
import sys
import os
sys.path.insert(0, '/app')
os.chdir('/app')

from superset.app import create_app
app = create_app()

with app.app_context():
    try:
        from superset.extensions import db
        from superset.models.dashboard import Dashboard
        from superset.models.slice import Slice
        from superset.connectors.sqla.models import SqlaTable
        
        # Delete Dashboard
        dash = db.session.query(Dashboard).filter_by(slug="ecommerce-analytics").first()
        if dash:
            print(f"Deleting dashboard: {dash.dashboard_title}")
            db.session.delete(dash)
            
        # Delete Charts
        charts = ["Revenue by State", "Orders by State", "Sales Distribution"]
        for c_name in charts:
            chart = db.session.query(Slice).filter_by(slice_name=c_name).first()
            if chart:
                print(f"Deleting chart: {c_name}")
                db.session.delete(chart)
                
        # Delete Datasets
        datasets = ["fact_sales", "agg_sales_by_state"]
        for d_name in datasets:
            dataset = db.session.query(SqlaTable).filter_by(table_name=d_name).first()
            if dataset:
                print(f"Deleting dataset: {d_name}")
                db.session.delete(dataset)
                
        db.session.commit()
        print("Cleanup successful")
        
    except Exception as e:
        print(f"Error during cleanup: {e}")
        import traceback
        traceback.print_exc()
'''
    success, stdout, stderr = run_python_in_container(script)
    if success:
        log_success("Cleanup completed!")
    else:
        log_warning(f"Cleanup failed: {stdout} {stderr}")


def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] == "--clean":
        if not wait_for_superset():
             sys.exit(1)
        cleanup_resources()
        time.sleep(2)
    
    log_info("Starting Superset configuration with ClickHouse...")

    if not wait_for_superset():
        sys.exit(1)

    setup_database()
    setup_datasets()
    setup_dashboard()
    setup_charts()
    update_dashboard_layout()

    log_success("\nConfiguration completed!")
    print(f"\n{BLUE}{'='*60}{END}")
    print(f"{GREEN}Access Superset at: {SUPERSET_URL}{END}")
    print(f"{GREEN}Dashboard: {SUPERSET_URL}/superset/dashboard/ecommerce-analytics/{END}")
    print(f"{YELLOW}Username: admin{END}")
    print(f"{YELLOW}Password: admin{END}")
    print(f"{BLUE}{'='*60}{END}\n")


if __name__ == "__main__":
    main()
