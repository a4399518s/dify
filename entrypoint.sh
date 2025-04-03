#!/bin/bash
set -e

# 在此添加初始化代码，例如：
# echo "Initializing application..."
cd /data/project/github/dify/api
nohup poetry run flask run --host 0.0.0.0 --port=5001 --debug > /var/log/dify.api.log 2>&1 &
nohup poetry run celery -A app.celery worker -P gevent -c 1 -Q dataset,generation,mail,ops_trace --loglevel INFO > /var/log/dify.celery.log 2>&1 &

cd /data/project/github/dify/web
nohup  pnpm start > /var/log/dify.web.log 2>&1 &

# 执行传入的命令
exec "$@"
