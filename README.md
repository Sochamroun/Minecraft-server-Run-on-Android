# 🌿 Minecraft Server Run on Android
* 📱 Requirements Android Device 
* 🛠️ Installation
* 🎮 Paper Server
* 🎮 Vanilla Server
* 🎮 Leaf Server 
* 🤖 Mineflayer Bot
* ⚡ Server Optimization
* 🌐 Tunnel / Playit.gg
* ❓ Troubleshooting
* 📞 Support Facebook/telegram
  
[![🇬🇧English](https://img.shields.io/badge/🇬🇧-English-blue?style=for-the-badge)](https://github.com/Sochamroun/Minecraft-server-Run-on-Android/blob/f6bcb8f840125d0814ecc4d295cdef3a724f44e8/README.md)
[![🇰🇭Cambodia](https://img.shields.io/badge/🇰🇭-Cambodia-blue?style=for-the-badge)](https://github.com/Sochamroun/Minecraft-server-Run-on-Android/blob/f6bcb8f840125d0814ecc4d295cdef3a724f44e8/KHMER.md)

[![✅ Termux](https://img.shields.io/badge/🥱-Termux_Download-blue?style=for-the-badge)](https://github.com/Sochamroun/Termux-EasySetup/releases/download/App/termux.apk)
## Update and upgrade Termux 
```bash
curl -sL https://raw.githubusercontent.com/Sochamroun/Minecraft-server-Run-on-Android/refs/heads/main/Install.sh | bash
```
---
## Download Script Install Server 
* Install Java 17 21 25
```bash
yes | pkg install openjdk-21 openjdk-17 openjdk-25 -y
```
* Paper Server 📃
```bash
curl -#LO https://raw.githubusercontent.com/Sochamroun/Minecraft-server-Run-on-Android/refs/heads/main/server/paper_mc.sh && chmod +x paper_mc.sh
```
* vanilla server 🫡
```bash
curl -#LO https://raw.githubusercontent.com/Sochamroun/Minecraft-server-Run-on-Android/refs/heads/main/server/vanilla_mc.sh && chmod +x vanilla_mc.sh
```
* leaf Server 🌿
```bash
curl -#LO https://raw.githubusercontent.com/Sochamroun/Minecraft-server-Run-on-Android/refs/heads/main/server/leaf_mc.sh && chmod +x leaf_mc.sh
```

[![🌿 Leaf](https://img.shields.io/badge/🌿-Leaf_Server_Download-green?style=for-the-badge)](https://www.leafmc.one/en/download/1.21.11)

---
## 🔌 plugins Server 
* paper 1.21.11
* note: cd folder 📁 server
* Normal Server 🌾
```bash
curl -#LO https://github.com/Sochamroun/Minecraft-server-Run-on-Android/releases/download/paper-1.21.11-plugins/normal.zip && unzip -o normal.zip && rm -f normal.zip
```
* RPG Server ⛰️
```bash
curl -#LO https://github.com/Sochamroun/Minecraft-server-Run-on-Android/releases/download/paper-1.21.11-plugins/RPG_0.1.0.zip && unzip -o RPG_0.1.0.zip && rm -f RPG_0.1.0.zip
```
* Login plugins
```bash
curl -#LO https://github.com/AuthMe/AuthMeReloaded/releases/download/6.0.1/AuthMe-6.0.1-Paper.jar
```
___
## Bot Join server Minecraft 
```bash
yes | pkg install nodejs -y
```
* Create folder 📁
```bash
mkdir bot && cd bot
```
* install mineflayer
```bash
npm init -y && npm install mineflayer
```
* Download bot.js
```bash
curl -#LO https://raw.githubusercontent.com/Sochamroun/Minecraft-server-Run-on-Android/refs/heads/main/bot.js
```
* run bot join server
```bash
node bot.js
```
* Edit bot.js
```bash
nano bot.sh
```
---
### note 
* Ctrl + x and y "save and exit"
* Ctrl + c "Close bot or stop bot Run"
---
### auto install script bot
```bash
curl -sL https://raw.githubusercontent.com/Sochamroun/Minecraft-server-Run-on-Android/refs/heads/main/NPC-MC.sh | bash
```
## Playit-gg tunnel Minecraft server 
* Free tunnel tcp server to public

[![playit-gg](https://img.shields.io/badge/🎲-Playit_gg_Download-orange?style=for-the-badge)](https://playit.gg/download/linux)

* playit-gg Plugins For papemc
* cd /$name && cd /plugins
```bash
curl -#LO https://github.com/playit-cloud/playit-minecraft-plugin/releases/latest/download/playit-minecraft-plugin.jar
```
---
## Minecraft Seed 
* -2382543636292059009 
---
## Python Check Server Online 🐍
```bash
curl -#LO https://raw.githubusercontent.com/Sochamroun/Termux-EasySetup/refs/heads/main/check-mc.py
```
---
## Nvim editor Code 
## 📦 Install Package / ដំឡើងកញ្ចប់
```bash
yes | pkg install neovim nodejs-lts ripgrep -y
```
## Git Clone AstroNvim Linux 
```bash
git clone --depth 1 https://github.com/AstroNvim/template ~/.config/nvim
rm -rf ~/.config/nvim/.git
nvim
```
## World challenge Free Download 🤫

[![📁 curseforge](https://img.shields.io/badge/📁-curseforge-orange?style=for-the-badge)](https://www.curseforge.com/minecraft/search?class=worlds&page=1&pageSize=20&sortBy=relevancy) 

* One Chunk challenge
```bash
curl -#LO https://github.com/Sochamroun/Minecraft-server-Run-on-Android/releases/download/One_Chunk_1.21%2B/one.block.1.21+.zip && unzip -o one.block.1.21+.zip && rm -f one.block.1.21+.zip
```
---
## How to use Termux 
| Command line | Description |
|--------------|-------------|
| cd | select folder 📁 |
| ls | show All folder and file |
| nano |Edit file script |
| mkdir |create folder |
| cp | copy file rename |
| du -sh * | show size file= MB |
| ifconfig | show ip |
| CTRL+X and Y | Save and exit |
| CTRL+C | Stop script or close |
| CTRL+D | Exit Termux App| 
| pkg install | packages | 

---

[![Facebook](https://img.shields.io/badge/📍-Facebook-blue?style=for-the-badge)](https://www.facebook.com/share/18q25LzNnc/)
[![telegram](https://img.shields.io/badge/🌐-Telegram-blue?style=for-the-badge)](https://t.me/Sochamroun123)
[![support](https://img.shields.io/badge/☕-Support_Me-blue?style=for-the-badge)](https://github.com/Sochamroun/Minecraft-server-Run-on-Android/blob/2a008aec64d1201f5eb29e3f72c59a22de74cb67/Buy_my_coffee.png)
---

<div align="center">
    <p><b> Prepared by Sochamroun </b></p>
    <p><b>If this project helps you, please give it a Stars ⭐</b></p>
    <p><b>*Last updated: 26-9-2026 </b></p>
</div>
