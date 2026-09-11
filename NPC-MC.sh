#!/data/data/com.termux/files/usr/bin/bash

clear
echo "===================================="
echo " 📁 Bot Join Minecraft Server"
echo " 🌐 Chill Chill "
echo "===================================="

sleep 2

echo "Install Nodejs"

yes | pkg install nodejs -y

sleep 2

mkdir mcbot && cd mcbot

npm init -y
npm install mineflayer

cat > ~/mcbot/bot.js << 'EOF'
const mineflayer = require('mineflayer');
const readline = require('readline');

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

function ask(question) {
  return new Promise(resolve => rl.question(question, resolve));
}

let host;
let port;
let bot;

function createBot() {
  console.log(`🚀 Connecting to ${host}:${port} | Version: 1.21.1...`);

  bot = mineflayer.createBot({
    host: host,
    port: port,
    username: 'ZinProMaxBOT',
    version: '1.21.1',
    auth: 'offline'
  });

  bot.once('spawn', () => {
    console.log('✅ Bot Joined Server!');
    console.log('🎮 Minecraft Version: 1.21.1');
    console.log('💬 Type chat below:');
  });

  // Server chat → console
  bot.on('message', (message) => {
    console.log(`📨 ${message.toString()}`);
  });

  bot.on('error', (err) => {
    console.log(`❌ Error: ${err.message}`);
  });

  bot.on('kicked', (reason) => {
    console.log(`⚠️ Kicked: ${reason}`);
  });

  bot.on('end', () => {
    console.log('🔄 Disconnected! Reconnecting in 5 seconds...');

    setTimeout(() => {
      createBot();
    }, 5000);
  });
}

// Terminal → Minecraft chat
rl.on('line', (message) => {
  message = message.trim();

  if (!message) return;

  if (bot && bot.player) {
    bot.chat(message);
    console.log(`💬 Bot: ${message}`);
  } else {
    console.log('⏳ Bot is not connected yet...');
  }
});

async function main() {
  console.log('====================================');
  console.log('   Minecraft Bot');
  console.log('   Thank You ');
  console.log('====================================');

  host = (await ask('🌐 Server IP: ')).trim();

  const portInput = (await ask('🔌 Server Port [25565]: ')).trim();
  port = portInput === '' ? 25565 : parseInt(portInput, 10);

  if (!host) {
    console.log('❌ Server IP is required!');
    rl.close();
    return;
  }

  if (isNaN(port) || port < 1 || port > 65535) {
    console.log('❌ Invalid port!');
    rl.close();
    return;
  }

  createBot();
}

main();
EOF

chmod +x ~/mcbot/bot.js

cd 
cat > ~/bot.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
cd ~/mcbot && node bot.js
EOF

chmod +x bot.sh

clear 
echo "Run : bash bot.sh"
echo "" 
echo "Run : cd mcbot && node bot.js"
echo ""
echo -e "\033[93mThanks You\033[0m"
