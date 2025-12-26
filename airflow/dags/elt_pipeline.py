"""
DAG: ELT Pipeline - PostgreSQL → ClickHouse → dbt
Descrição: Extrai dados do PostgreSQL, carrega em ClickHouse e executa transformações com dbt
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.task_group import TaskGroup
import psycopg2
from clickhouse_driver import Client
import logging

# Logger
logger = logging.getLogger(__name__)

# Configurações
POSTGRES_CONN = {
    'host': 'postgres-source',
    'port': 5432,
    'user': 'ecommerce',
    'password': 'ecommerce123',
    'database': 'ecommerce_db'
}

CLICKHOUSE_CONN = {
    'host': 'clickhouse-server',
    'port': 9000,
    'user': 'default',
    'password': 'clickhouse123'
}

# Argumentos padrão
default_args = {
    'owner': 'data-pipeline',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2025, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
}

# DAG
dag = DAG(
    'elt_pipeline',
    default_args=default_args,
    description='ELT Pipeline: PostgreSQL → ClickHouse → dbt',
    schedule_interval='@daily',
    catchup=False,
    tags=['elt', 'ecommerce', 'clickhouse'],
)

def create_clickhouse_databases():
    """Cria databases no ClickHouse"""
    logger.info("Criando databases no ClickHouse...")
    try:
        client = Client(CLICKHOUSE_CONN['host'], port=CLICKHOUSE_CONN['port'], user=CLICKHOUSE_CONN['user'], password=CLICKHOUSE_CONN['password'])
        client.execute("CREATE DATABASE IF NOT EXISTS raw")
        client.execute("CREATE DATABASE IF NOT EXISTS analytics")
        logger.info("✓ Databases criados com sucesso")
    except Exception as e:
        logger.error(f"Erro ao criar databases: {str(e)}")
        raise

def extract_and_load_table(table_name: str):
    """Extrai dados do PostgreSQL e carrega em ClickHouse"""
    logger.info(f"Iniciando ELT para tabela: {table_name}")
    
    try:
        # Conectar ao PostgreSQL
        pg_conn = psycopg2.connect(**POSTGRES_CONN)
        pg_cursor = pg_conn.cursor()
        
        # Buscar dados
        pg_cursor.execute(f"SELECT * FROM {table_name}")
        columns = [desc[0] for desc in pg_cursor.description]
        rows = pg_cursor.fetchall()
        
        logger.info(f"Extraídos {len(rows)} registros de {table_name}")
        
        # Conectar ao ClickHouse
        ch_client = Client(CLICKHOUSE_CONN['host'], port=CLICKHOUSE_CONN['port'], user=CLICKHOUSE_CONN['user'], password=CLICKHOUSE_CONN['password'])
        
        # Recriar tabela para garantir schema correto
        ch_client.execute(f"DROP TABLE IF EXISTS raw.{table_name}")
        
        # Criar tabela em ClickHouse
        if table_name == 'customers':
            ch_client.execute(f"""
                CREATE TABLE raw.{table_name} (
                    customer_id Int32,
                    first_name String,
                    last_name String,
                    email String,
                    phone Nullable(String),
                    state String,
                    city String,
                    created_at DateTime
                ) ENGINE = MergeTree() ORDER BY customer_id
            """)
        elif table_name == 'products':
            ch_client.execute(f"""
                CREATE TABLE raw.{table_name} (
                    product_id Int32,
                    product_name String,
                    category String,
                    price Float64,
                    cost Float64,
                    created_at DateTime
                ) ENGINE = MergeTree() ORDER BY product_id
            """)
        elif table_name == 'orders':
            ch_client.execute(f"""
                CREATE TABLE raw.{table_name} (
                    order_id Int32,
                    customer_id Nullable(Int32),
                    order_date DateTime,
                    status String,
                    total_amount Float64
                ) ENGINE = MergeTree() ORDER BY order_id
            """)
        elif table_name == 'order_items':
            ch_client.execute(f"""
                CREATE TABLE raw.{table_name} (
                    order_item_id Int32,
                    order_id Nullable(Int32),
                    product_id Nullable(Int32),
                    quantity Int32,
                    unit_price Float64,
                    subtotal Float64
                ) ENGINE = MergeTree() ORDER BY order_item_id
            """)
        
        # Inserir dados
        if rows:
            ch_client.execute(
                f"INSERT INTO raw.{table_name} VALUES",
                rows
            )
            logger.info(f"Carregados {len(rows)} registros em raw.{table_name}")
        
        pg_cursor.close()
        pg_conn.close()
        
        logger.info(f"✓ ELT concluído para tabela: {table_name}")
        
    except Exception as e:
        logger.error(f"Erro ao processar {table_name}: {str(e)}")
        raise

# Tasks
create_db_task = PythonOperator(
    task_id='create_clickhouse_databases',
    python_callable=create_clickhouse_databases,
    dag=dag,
)

with TaskGroup("extract_load", dag=dag) as extract_load_group:
    for table in ['customers', 'products', 'orders', 'order_items']:
        PythonOperator(
            task_id=f"load_{table}",
            python_callable=extract_and_load_table,
            op_kwargs={'table_name': table},
            dag=dag,
        )

# Task: Executar dbt
dbt_task = BashOperator(
    task_id='run_dbt_transformations',
    bash_command='curl -X POST http://webhook-server:5000/webhook/manual || echo "Webhook não disponível"',
    dag=dag,
)

# Dependências
create_db_task >> extract_load_group >> dbt_task

if __name__ == "__main__":
    dag.cli()
