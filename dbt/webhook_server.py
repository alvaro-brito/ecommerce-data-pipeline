#!/usr/bin/env python3
"""
Webhook Server to execute dbt when Airbyte finishes ELT
Listens on http://localhost:5001/webhook
"""

from flask import Flask, request, jsonify, send_from_directory
import subprocess
import logging
import os
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# dbt directory
DBT_DIR = '/usr/app'
DOCS_DIR = os.path.join(DBT_DIR, 'target')

@app.route('/docs/')
def serve_docs_index():
    """Serve dbt documentation index"""
    return send_from_directory(DOCS_DIR, 'index.html')

@app.route('/docs/<path:path>')
def serve_docs_files(path):
    """Serve dbt documentation files"""
    return send_from_directory(DOCS_DIR, path)


def run_dbt_command(command):
    """Executes dbt command and returns result"""
    try:
        logger.info(f"Executing: {command}")
        
        result = subprocess.run(
            command,
            shell=True,
            cwd=DBT_DIR,
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes timeout
        )
        
        logger.info(f"Output: {result.stdout}")
        
        if result.returncode != 0:
            logger.error(f"Error: {result.stderr}")
            return False, result.stderr
        
        return True, result.stdout
    
    except subprocess.TimeoutExpired:
        error_msg = "dbt command timed out after 10 minutes"
        logger.error(error_msg)
        return False, error_msg
    
    except Exception as e:
        error_msg = f"Error executing dbt: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    }), 200


@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Webhook endpoint called by Airbyte after finishing ELT
    
    Expected payload:
    {
        "type": "job.success",
        "job_id": "123",
        "connection_id": "abc",
        "sync_id": "def"
    }
    """
    try:
        data = request.get_json() or {}
        
        logger.info(f"Webhook received: {data}")
        
        # Validate event type
        event_type = data.get('type', '')
        
        if 'success' not in event_type.lower():
            logger.warning(f"Ignoring event: {event_type}")
            return jsonify({
                'status': 'ignored',
                'message': f'Event type {event_type} not processed'
            }), 200
        
        # Execute dbt run
        logger.info("Starting dbt run...")
        success, output = run_dbt_command('dbt run')
        
        if not success:
            return jsonify({
                'status': 'error',
                'message': 'dbt run failed',
                'details': output
            }), 500
        
        # Execute dbt test
        logger.info("Starting dbt test...")
        success, output = run_dbt_command('dbt test')
        
        if not success:
            logger.warning(f"dbt test had issues: {output}")
            # Do not fail completely if tests fail
        
        # Execute dbt docs generate
        logger.info("Generating dbt documentation...")
        success, output = run_dbt_command('dbt docs generate')
        
        if not success:
            logger.warning(f"Error generating docs: {output}")
        
        return jsonify({
            'status': 'success',
            'message': 'dbt pipeline executed successfully',
            'timestamp': datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        logger.error(f"Error in webhook: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/webhook/manual', methods=['POST'])
def webhook_manual():
    """
    Endpoint to execute dbt manually (without event type validation)
    Useful for testing
    """
    try:
        logger.info("Executing dbt manually...")
        
        # Execute dbt run
        success, output = run_dbt_command('dbt run')
        
        if not success:
            return jsonify({
                'status': 'error',
                'message': 'dbt run failed',
                'details': output
            }), 500
        
        # Execute dbt test
        success, output = run_dbt_command('dbt test')
        
        if not success:
            logger.warning(f"dbt test had issues: {output}")

        # Execute dbt docs generate
        logger.info("Generating dbt documentation...")
        success, output = run_dbt_command('dbt docs generate')
        
        if not success:
            logger.warning(f"Error generating docs: {output}")
        
        return jsonify({
            'status': 'success',
            'message': 'dbt pipeline executed successfully',
            'timestamp': datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        logger.error(f"Error in manual webhook: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/status', methods=['GET'])
def status():
    """Returns webhook server status"""
    return jsonify({
        'status': 'running',
        'service': 'dbt-webhook-server',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat(),
        'endpoints': {
            'health': 'GET /health',
            'webhook': 'POST /webhook',
            'webhook_manual': 'POST /webhook/manual',
            'status': 'GET /status'
        }
    }), 200


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting webhook server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False)
