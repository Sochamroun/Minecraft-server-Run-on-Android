# 🌿 Minecraft Server ដំណើរការលើ Android

  * 📱 តម្រូវការ៖ ឧបករណ៍ Android
  * 🛠️ ការដំឡើង
  * 🎮 Paper Server
  * 🎮 Vanilla Server
  * 🎮 Leaf Server
  * 🤖 Mineflayer Bot
  * ⚡ បង្កើនប្រសិទ្ធភាព Server
  * 🌐 Tunnel / Playit.gg
  * ❓ ដោះស្រាយបញ្ហា
  * 📞 Support 0883963489 🇰🇭

## ធ្វើបច្ចុប្បន្នភាព និង Upgrade Termux

```bash
curl -sL https://raw.githubusercontent.com/Sochamroun/Minecraft-server-Run-on-Android/refs/heads/main/Install.sh | bash
```

---

## ទាញយក Script សម្រាប់ដំឡើង Server

### ដំឡើង Java 17, 21 និង 25

```bash
yes | pkg install openjdk-21 openjdk-17 openjdk-25 -y
```

### Paper Server 📃

```bash
curl -#LO https://raw.githubusercontent.com/Sochamroun/Minecraft-server-Run-on-Android/refs/heads/main/server/paper_mc.sh && chmod +x paper_mc.sh
```

### Vanilla Server 🫡

```bash
curl -#LO https://raw.githubusercontent.com/Sochamroun/Minecraft-server-Run-on-Android/refs/heads/main/server/vanilla_mc.sh && chmod +x vanilla_mc.sh
```

### Leaf Server 🌿

```bash
curl -#LO https://raw.githubusercontent.com/Sochamroun/Minecraft-server-Run-on-Android/refs/heads/main/server/leaf_mc.sh && chmod +x leaf_mc.sh
```

---

## 🔌 Plugins សម្រាប់ Server

### Paper 1.21.11

> ចំណាំ៖ ចូលទៅកាន់ថត `server` មុន។

### Normal Server 🌾

```bash
curl -#LO https://github.com/Sochamroun/Minecraft-server-Run-on-Android/releases/download/paper-1.21.11-plugins/normal.zip && unzip -o normal.zip && rm -f normal.zip
```

### RPG Server ⛰️

```bash
curl -#LO https://github.com/Sochamroun/Minecraft-server-Run-on-Android/releases/download/paper-1.21.11-plugins/RPG_0.1.0.zip && unzip -o RPG_0.1.0.zip && rm -f RPG_0.1.0.zip
```

### Login Plugins

```bash
curl -#LO https://github.com/AuthMe/AuthMeReloaded/releases/download/6.0.1/AuthMe-6.0.1-Paper.jar
```

---

## 🤖 ឲ្យ Bot ចូល Minecraft Server

### ដំឡើង Node.js

```bash
yes | pkg install nodejs -y
```

### បង្កើតថត 📁

```bash
mkdir bot && cd bot
```

### ដំឡើង Mineflayer

```bash
npm init -y && npm install mineflayer
```

### ទាញយក `bot.js`

```bash
curl -#LO https://raw.githubusercontent.com/Sochamroun/Minecraft-server-Run-on-Android/refs/heads/main/bot.js
```

### ដំណើរការ Bot ឲ្យចូល Server

```bash
node bot.js
```

### កែប្រែ `bot.js`

```bash
nano bot.sh
```

---

### 📝 ចំណាំ

- `Ctrl + x` និង `y` — រក្សាទុក និងចាកចេញ
- `Ctrl + c` — បិទ Bot ឬបញ្ឈប់ Bot ដែលកំពុងដំណើរការ

---

## 🤖 Script ដំឡើង Bot ដោយស្វ័យប្រវត្តិ

```bash
curl -sL https://raw.githubusercontent.com/Sochamroun/Minecraft-server-Run-on-Android/refs/heads/main/NPC-MC.sh | bash
```

---

## 🌐 Playit-gg Tunnel សម្រាប់ Minecraft Server

- Tunnel TCP ឥតគិតថ្លៃ សម្រាប់បើក Server ឲ្យអាចចូលពីអ៊ីនធឺណិតបាន
- Playit-gg Plugin សម្រាប់ PaperMC
- ចូលទៅកាន់ថត Server និង `plugins`

```bash
cd /$name && cd /plugins
```

```bash
curl -#LO https://github.com/playit-cloud/playit-minecraft-plugin/releases/latest/download/playit-minecraft-plugin.jar
```

---

## 🌱 Minecraft Seed

```text
-2382543636292059009
```

---

## 🐍 Python សម្រាប់ពិនិត្យថា Server Online ឬអត់

```bash
curl -#LO https://raw.githubusercontent.com/Sochamroun/Termux-EasySetup/refs/heads/main/check-mc.py
```

---

## 📝 Nvim Editor សម្រាប់សរសេរ Code

### 📦 ដំឡើង Package

```bash
yes | pkg install neovim nodejs-lts ripgrep -y
```

### 🐧 Git Clone AstroNvim Linux

```bash
git clone --depth 1 https://github.com/AstroNvim/template ~/.config/nvim
rm -rf ~/.config/nvim/.git
nvim
```

---

## 🤫 World Challenge ទាញយកដោយឥតគិតថ្លៃ

### One Chunk Challenge

```bash
curl -#LO https://github.com/Sochamroun/Minecraft-server-Run-on-Android/releases/download/One_Chunk_1.21%2B/one.block.1.21+.zip && unzip -o one.block.1.21+.zip && rm -f one.block.1.21+.zip
```

---

## 📱 របៀបប្រើ Termux

| Command | អត្ថន័យ |
|---|---|
| `cd` | ជ្រើសរើសថត 📁 |
| `ls` | បង្ហាញថត និងឯកសារទាំងអស់ |
| `nano` | កែប្រែ Script ឬឯកសារ |
| `mkdir` | បង្កើតថតថ្មី |
| `cp` | ចម្លង ឬប្តូរឈ្មោះឯកសារ |
| `du -sh *` | បង្ហាញទំហំឯកសារ ជា MB |
| `ifconfig` | បង្ហាញ IP Address |
| `CTRL+X` និង `Y` | រក្សាទុក និងចាកចេញ |
| `CTRL+C` | បញ្ឈប់ Script ឬបិទដំណើរការ |
| `CTRL+D` | ចាកចេញពី Termux App |
| `pkg install` | ដំឡើង Package |

---

## 👨‍💻 រៀបចំដោយ Sochamroun

ប្រសិនបើ Project នេះមានប្រយោជន៍សម្រាប់អ្នក សូមផ្តល់ **Star ⭐** មួយ ដើម្បីគាំទ្រ Project នេះ។

**ធ្វើបច្ចុប្បន្នភាពចុងក្រោយ៖ 26-9-2026**
