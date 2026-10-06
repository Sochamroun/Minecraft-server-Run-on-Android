## Install playit-gg using Ubuntu server 
### Install Proot-Distro
```bash
yes | pkg install proot-distro -y
```
### Proot-Distro Install Ubuntu 
```bash
proot-distro install ubuntu
```
### login To Ubuntu Server 
```bash
proot-distro login ubuntu
```
### update and upgrade Ubuntu 
```bash
apt update && apt upgrade -y
```
### Install playit-linux-aarch64 v1.0.10
```bash
curl -#LO https://github.com/playit-cloud/playit-agent/releases/download/v1.0.10/playit-linux-aarch64 && chmod +x playit-linux-aarch64
```
### Install playit-cli-linux-aarch64 v1.0.10
```bash
curl -#LO https://github.com/playit-cloud/playit-agent/releases/download/v1.0.10/playit-cli-linux-aarch64 && chmod +x playit-cli-linux-aarch64
```
