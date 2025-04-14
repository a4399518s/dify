```
docker compose down
docker compose up -d
docker compose up -d --no-deps --build api
-x "http://crash:202412231431@192.168.1.220:65534"
export HTTPS_PROXY="http://crash:202412231431@192.168.1.220:65534"
export HTTP_PROXY="http://crash:202412231431@192.168.1.220:65534"
export http_proxy="http://crash:202412231431@192.168.1.220:65534"
export https_proxy="http://crash:202412231431@192.168.1.220:65534"
unset HTTPS_PROXY
unset HTTP_PROXY
unset http_proxy
unset https_proxy
```
rm -rf /usr/share/keyrings/kubernetes-archive-keyring.gpg
 curl  -x "http://crash:202412231431@192.168.1.220:65534" -fsSLo /usr/share/keyrings/kubernetes-archive-keyring.gpg https://packages.cloud.google.com/apt/doc/apt-key.gpg
rm -rf /etc/apt/sources.list.d/kubernetes.list
echo "deb [signed-by=/usr/share/keyrings/kubernetes-archive-keyring.gpg] https://apt.kubernetes.io/ kubernetes-xenial main" | \
sudo tee /etc/apt/sources.list.d/kubernetes.list

sudo mkdir -p /etc/systemd/system/docker.service.d
sudo vim /etc/systemd/system/docker.service.d/http-proxy.conf
[Service]
Environment="HTTP_PROXY=http://crash:202412231431@192.168.1.220:65534"
Environment="HTTPS_PROXY=http://crash:202412231431@192.168.1.220:65534"
sudo systemctl daemon-reload
sudo systemctl restart docker

docker pull registry.k8s.io/pause:3.10
vim /usr/lib/systemd/system/cri-docker.service


ExecStart=/usr/bin/cri-dockerd --container-runtime-endpoint fd:// --network-plugin=cni --cni-bin-dir=/opt/cni/bin --cni-cache-dir=/var/lib/cni/cache --cni-conf-dir=/etc/cni/net.d
systemctl daemon-reload 
systemctl restart cri-docker

kubeadm reset --cri-socket unix:///run/cri-dockerd.sock

kubeadm config images pull --cri-socket unix:///var/run/cri-dockerd.sock --image-repository="registry.aliyuncs.com/google_containers" 

kubeadm init \
    --image-repository="registry.aliyuncs.com/google_containers" \
    --control-plane-endpoint="kubeapi.hctalent.cn" \
    --kubernetes-version=v1.17.17 \
    --pod-network-cidr=10.1.0.0/16 \
    --service-cidr=10.2.0.0/16 \
    --token-ttl=0 \
    --upload-certs

kubeadm join kubeapi.hctalent.cn:6443 --token 88sfrt.9v8j36zvax03rg47 \
    --cri-socket unix:///run/cri-dockerd.sock \
    --discovery-token-ca-cert-hash sha256:91b21ed5fee3275ecfd5b21554c1da750793a02f3c99bb42a1d396f2edc156e7 \
    --control-plane --certificate-key c7df8b86018df79e34f7604ce080792f44af5ac021992dff5c54e33cc4881dd8

kubectl describe pod -n kube-flannel kube-flannel-ds-rjf8x
http://192.168.31.213/chat/pEFDPVLjBuoUwCds