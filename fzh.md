```
docker compose down
docker compose up -d
docker compose -f docker-compose.test.yaml up -d
docker compose -f docker-compose.test.yaml up -d --no-deps --build api
docker compose up -d --no-deps --build web
-x "http://crash:202412231431@192.168.1.220:65534"
cd /opt/project/github/dify/docker
export HTTPS_PROXY="http://crash:202412231431@192.168.1.220:65534"
export HTTP_PROXY="http://crash:202412231431@192.168.1.220:65534"
export http_proxy="http://crash:202412231431@192.168.1.220:65534"
export https_proxy="http://crash:202412231431@192.168.1.220:65534"


export HTTPS_PROXY="http://crash:202412231431@192.168.1.220:65534"
export HTTP_PROXY="http://crash:202412231431@192.168.1.220:65534"
export http_proxy="http://crash:202412231431@192.168.1.220:65534"
export https_proxy="http://crash:202412231431@192.168.1.220:65534"

unset HTTPS_PROXY
unset HTTP_PROXY
unset http_proxy
unset https_proxy

git pull

docker exec -it docker-web-1 /bin/bash
pnpm run build

docker restart docker-web-1
docker restart docker-api-1
docker restart docker-worker-1

```
