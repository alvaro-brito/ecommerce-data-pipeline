import os

# Superset configuration
SECRET_KEY = os.environ.get('SUPERSET_SECRET_KEY', 'ThisIsASecretKey')

# PostgreSQL for Superset metadata
SQLALCHEMY_DATABASE_URI = 'postgresql://ecommerce:ecommerce123@postgres-source:5432/ecommerce_db'

# Feature flags
FEATURE_FLAGS = {
    'ENABLE_TEMPLATE_PROCESSING': True,
    'ALLOW_DASHBOARD_EDITING': True,
}

# Cache configuration
CACHE_CONFIG = {
    'CACHE_TYPE': 'SimpleCache',
    'CACHE_DEFAULT_TIMEOUT': 300
}

# Allow CSV Upload
ALLOW_FILE_UPLOAD = True

# Max Upload Size (100MB)
MAX_UPLOAD_SIZE = 104857600

# API Configuration - Disable CSRF for API endpoints
WTF_CSRF_ENABLED = False

# Enable public API access
FAB_API_SWAGGER_UI = True
ENABLE_PROXY_FIX = True

# CORS settings for API access
ENABLE_CORS = True
CORS_OPTIONS = {
    'supports_credentials': True,
    'allow_headers': ['*'],
    'resources': ['*'],
    'origins': ['*']
}

# Security settings
TALISMAN_ENABLED = False
PUBLIC_ROLE_LIKE = 'Gamma'
