FROM registry.cn-zhangjiakou.aliyuncs.com/fengzhihao/ubuntu:all.24.04

RUN mkdir -p /data/project/github/dify
ADD . /data/project/github/dify/
WORKDIR /data/project/github/dify/api
RUN poetry install

WORKDIR /data/project/github/dify/web
RUN pnpm install --registry=https://registry.npmmirror.com
RUN pnpm run build

# CMD [ "poetry run flask run --host 0.0.0.0 --port=5001 --debug" ]
# CMD [ " poetry run celery -A app.celery worker -P gevent -c 1 -Q dataset,generation,mail,ops_trace --loglevel INF" ]
# CMD [ "pnpm start" ]

# docker build -t registry.cn-zhangjiakou.aliyuncs.com/fengzhihao/ubuntu:all.24.04.dify .

# docker run -d --rm -p 3000:3000 -it --privileged=true --name dify registry.cn-shanghai.aliyuncs.com/fengzhihao/ubuntu:all.24.04.dify
# docker run --rm -v /data/project/github/dify:/data/project/github/dify -p 3000:3000 -p 5001:5001 -it --privileged=true --name dify registry.cn-zhangjiakou.aliyuncs.com/fengzhihao/ubuntu:all.24.04.dify /bin/bash


