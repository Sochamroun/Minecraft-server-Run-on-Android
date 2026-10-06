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
---
### How to Run 
* Step 1 login Ubuntu 
```bash
proot-distro login ubuntu
```
* step 2 Run playit-linux-aarch64
```bash
./playit-linux-aarch64
```
* step 3 Run playit-cli-linux-aarch64
```bash
./playit-cli-linux-aarch64
```
### Note 
* Claim Your key Agent Tunnel playit-gg
* Login account finish

<div align="center">
    <p><b> Prepared by Sochamroun </b></p>
    <p><b>If this project helps you, please give it a Stars ⭐</b></p>
    <p><b>*Last updated: 7 10 2026</b></p>
</div>
