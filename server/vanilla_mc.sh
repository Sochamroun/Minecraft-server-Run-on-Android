#!/data/data/com.termux/files/usr/bin/bash

clear
echo "==============================================="
echo " 📁 Minecraft vanilla Server Install"
echo " 🌐 Termux Script Auto Setup by Sochamroun 🤓"
echo "==============================================="

sleep 5

echo ""
echo "Enter server folder 📂 name:"
read SERVERNAME

mkdir -p ~/$SERVERNAME
cd ~/$SERVERNAME || exit

echo ""
echo "Enter Minecraft version 🎲"
echo "Example: 1.20.4 / 1.21.1"
read VERSION

MANIFEST="https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"

echo ""
echo "Getting version info..."

VERSION_URL=$(curl -fsSL "$MANIFEST" | \
jq -r --arg VERSION "$VERSION" \
'.versions[] | select(.id == $VERSION) | .url')

if [ -z "$VERSION_URL" ] || [ "$VERSION_URL" = "null" ]; then
    echo "❌ Version not found!"
    exit 1
fi

DOWNLOAD_URL=$(curl -fsSL "$VERSION_URL" | jq -r '.downloads.server.url')

echo "⬇️ Downloading Vanilla Server..."
wget -O server.jar "$DOWNLOAD_URL"

if [ $? -ne 0 ]; then
    echo "❌ Download failed!"
    exit 1
fi

echo "✅ Vanilla Minecraft Server downloaded!"

# Ram Server
read -p "RAM (default 2024M = 2G) (note M=MB ; G=GB ): " RAM
RAM=${RAM:-2024M}

# TimeZone
echo "Search TimeZoneDB"
read -p "TIMEZONE (default=Asia/Phnom_Penh): " TIMEZONE
TIMEZONE=${TIMEZONE:-Asia/Phnom_Penh}

echo ""
echo "Creating start.sh..."

cat > start.sh <<EOF
#!/data/data/com.termux/files/usr/bin/bash
export TZ=$TIMEZONE
java -Xms$RAM -Xmx$RAM -jar server.jar nogui
EOF

chmod +x start.sh

echo "RAM=$RAM"
echo "TIMEZONE=$TIMEZONE"
sleep 2

chmod +x start.sh

echo ""
echo "Running server first time... 📝"
./start.sh

echo ""
echo "Accepting EULA... 🗂️"
if [ -f eula.txt ]; then
sed -i 's/eula=false/eula=true/g' eula.txt
fi

echo ""
echo "===== Server Settings ====="

# Online Mode
echo "Online Mode:"
echo "1) false (Offline/Cracked)"
echo "2) true (Premium)"
read -p "Choose (1-2): " ONLINE_CHOICE

case "$ONLINE_CHOICE" in
    1) ONLINE_MODE=false ;;
    2) ONLINE_MODE=true ;;
    *)
        echo "Invalid choice! Using default: false (Offline/Cracked)"
        ONLINE_MODE=false
        ;;
esac

# View Distance
read -p "View Distance (chunks, default 10): " VIEW_DISTANCE
VIEW_DISTANCE=${VIEW_DISTANCE:-10}

# Server Port
read -p "Server Port (default 25565): " SERVER_PORT
SERVER_PORT=${SERVER_PORT:-25565}

# Max Players
read -p "Max Players (default 20): " MAX_PLAYERS
MAX_PLAYERS=${MAX_PLAYERS:-20}

# Level Seed
read -p "Level Seed (leave blank for random): " LEVEL_SEED

# Hardcore
echo ""
echo "Hardcore Mode:"
echo "1) false (Normal)"
echo "2) true (Hardcore)"
read -p "Choose (1-2): " HARDCORE_CHOICE

case "$HARDCORE_CHOICE" in
    1) HARDCORE=false ;;
    2) HARDCORE=true ;;
    *)
        echo "Invalid choice! Defaulting to false (Normal)"
        HARDCORE=false
        ;;
esac

# MOTD
echo ""
read -p "Enter MOTD: " MOTD

echo ""
echo "Writing server.properties..."

cat > server.properties <<EOF
online-mode=$ONLINE_MODE
view-distance=$VIEW_DISTANCE
server-port=$SERVER_PORT
max-players=$MAX_PLAYERS
hardcore=$HARDCORE
motd=$MOTD
EOF

# Add level-seed only if user entered one
if [ -n "$LEVEL_SEED" ]; then
    echo "level-seed=$LEVEL_SEED" >> server.properties
fi

echo ""
echo "✅ Settings saved!"

echo ""
echo "Creating shortcut script..."

cat > ~/$SERVERNAME.sh <<EOF
#!/data/data/com.termux/files/usr/bin/bash

ip_address=\$(ip -4 addr show wlan0 | grep -oP 'inet \K[\d.]+')

echo "IP Server Minecraft✅: \$ip_address"
echo "Please Wait Server Run 😎"
sleep 10

cd ~/$SERVERNAME || exit
./start.sh
EOF

chmod +x ~/$SERVERNAME.sh

echo ""
echo "===================================="
echo " ✅ Server Installed Successfully"
echo "===================================="

echo ""
echo "📁 Folder:"
echo "cd ~/$SERVERNAME"

echo ""
echo "▶ Start server:"
echo "bash ~/$SERVERNAME.sh"

echo ""
echo "🔓 Server Enabled 🧐"

echo "Wait Check"
sleep 5

echo "true = Premium ✅"
echo "false = Offline/Cracked 🤫" 
echo " 🍎 Online-mode=$ONLINE_MODE"
echo " 😠 Hardcore=$HARDCORE"
echo " 😎 Player=$MAX_PLAYERS"
echo " 🌈 MOTD set: $MOTD"

