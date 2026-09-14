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

# ddos Server
cat > ~/mcbot/npc.js << 'EOF'
const mineflayer = require('mineflayer');

const HOST = '192.168.x.x';
const PORT = 25565;

const MAX_BOTS = 20;
const JOIN_DELAY = 5000;

const bots = new Set();
let stopped = false;
let joined = 0;

function randomName() {
  const letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz';
  const numbers = '2345678';

  let name = '';

  for (let i = 0; i < 6; i++) {
    name += letters[Math.floor(Math.random() * letters.length)];
  }

  for (let i = 0; i < 2; i++) {
    name += numbers[Math.floor(Math.random() * numbers.length)];
  }

  return name;
}

function createBot() {
  if (stopped || joined >= MAX_BOTS) return;

  const username = randomName();

  const bot = mineflayer.createBot({
    host: HOST,
    port: PORT,
    username,
    version: '1.21.1'
  });

  bots.add(bot);
  joined++;

  console.log(`🤖 [${joined}/${MAX_BOTS}] Joining: ${username}`);

  bot.once('spawn', () => {
    console.log(`✅ Online: ${username}`);
  });

  bot.on('kicked', reason => {
    console.log(`⚠️ Kicked: ${username} - ${reason}`);
  });

  bot.on('error', err => {
    console.log(`❌ Error ${username}: ${err.message}`);
  });

  bot.on('end', () => {
    bots.delete(bot);
    console.log(`🔴 Offline: ${username}`);
  });

  if (joined < MAX_BOTS && !stopped) {
    setTimeout(createBot, JOIN_DELAY);
  } else {
    console.log(`🎉 Finished. ${MAX_BOTS} bots attempted.`);
  }
}

// Ctrl+C
process.on('SIGINT', () => {
  if (stopped) return;

  stopped = true;
  console.log('\n🛑 Stopping all bots...');

  for (const bot of bots) {
    try {
      bot.quit('Load test stopped');
    } catch {}
  }

  setTimeout(() => {
    console.log('👋 All bots stopped.');
    process.exit(0);
  }, 1000);
});

console.log(`🎮 Minecraft Load Test`);
console.log(`📡 ${HOST}:${PORT}`);
console.log(`🤖 Bots: ${MAX_BOTS}`);
console.log(`⏱️ Join delay: ${JOIN_DELAY / 1000}s`);
console.log('');

createBot();
EOF

chmod +x ~/mcbot/bot.js
chmod +x ~/mcbot/npc.js

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
