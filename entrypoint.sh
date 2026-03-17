#!/bin/bash
set -e

echo "Starting FinOps Platform..."
echo "Initializing services..."

# Execute supervisord in the foreground
exec /usr/bin/supervisord -n -c /etc/supervisor/conf.d/supervisord.conf
