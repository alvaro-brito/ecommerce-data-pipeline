FROM apache/airflow:2.7.3-python3.11

USER root

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    mysql-client \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Criar diretórios com permissões corretas ANTES de trocar de usuário
RUN mkdir -p /opt/airflow/logs \
    && mkdir -p /opt/airflow/dags \
    && mkdir -p /opt/airflow/plugins \
    && mkdir -p /opt/airflow/config \
    && chmod -R 777 /opt/airflow/logs \
    && chmod -R 777 /opt/airflow/dags \
    && chmod -R 777 /opt/airflow/plugins \
    && chmod -R 777 /opt/airflow/config

# Trocar para usuário airflow
USER airflow

# Instalar providers do Airflow
RUN pip install --no-cache-dir \
    apache-airflow-providers-postgres==5.10.0 \
    apache-airflow-providers-mysql==5.5.4 \
    apache-airflow-providers-http==4.7.0 \
    clickhouse-driver==0.2.10 \
    psycopg2-binary==2.9.9 \
    pymysql==1.1.0 \
    requests==2.31.0

# Definir variáveis de ambiente
ENV AIRFLOW_HOME=/opt/airflow \
    AIRFLOW__CORE__DAGS_FOLDER=/opt/airflow/dags \
    AIRFLOW__CORE__BASE_LOG_FOLDER=/opt/airflow/logs \
    AIRFLOW__CORE__DAG_DISCOVERY_SAFE_MODE=false \
    AIRFLOW__CORE__LOAD_EXAMPLES=false \
    AIRFLOW__CORE__UNIT_TEST_MODE=false \
    AIRFLOW__WEBSERVER__EXPOSE_CONFIG=true \
    AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION=false \
    AIRFLOW__CORE__LOAD_DEFAULT_CONNECTIONS=false

WORKDIR /opt/airflow

EXPOSE 8080

CMD ["bash", "-c", "airflow db upgrade && airflow users create --username admin --password admin --firstname Admin --lastname User --role Admin --email admin@example.com 2>/dev/null || true && airflow webserver"]
