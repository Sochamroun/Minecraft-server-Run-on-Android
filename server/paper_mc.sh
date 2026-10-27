#!/data/data/com.termux/files/usr/bin/bash

clear

echo "==============================================="
echo " 📄 Minecraft Paper Server Install"
echo " 🌐 Termux Script Auto Setup by Sochamroun🤓"
echo "==============================================="

sleep 2

echo ""
echo "==============================================="
echo " 📁 Server Folder"
echo "==============================================="

echo ""
read -p "Enter server folder 📂 name: " SERVERNAME

mkdir -p ~/$SERVERNAME
cd ~/$SERVERNAME || exit

echo ""
echo "==============================================="
echo " 🎲 Minecraft Version"
echo "==============================================="

echo ""
echo "Example: 1.20.4 / 1.21.1"
echo ""

read -p "Version: " VERSION

API_URL="https://fill.papermc.io/v3/projects/paper/versions/${VERSION}/builds?channel=STABLE&limit=1"

BUILDS_JSON=$(curl -fsSL \
    -H "Accept: application/json" \
    "$API_URL") || {
    echo "❌ Failed to fetch PaperMC API!"
    exit 1
}

BUILD=$(printf '%s' "$BUILDS_JSON" |
    jq -er '.[0].id // empty') || {
    echo "❌ No stable build found!"
    exit 1
}

URL=$(printf '%s' "$BUILDS_JSON" |
    jq -er '.[0].downloads["server:default"].url // empty') || {
    echo "❌ Download URL not found!"
    exit 1
}

echo ""
echo "✅ Paper build found!"
echo "📦 Minecraft Version: $VERSION"
echo "🔢 Build: $BUILD"
echo "📂 Download URL: $URL"

echo ""
echo "==============================================="
echo " ⬇️ Downloading Paper"
echo "==============================================="

echo ""
echo "📥 Downloading server.jar..."

wget -O server.jar "$URL"
if [ $? -ne 0 ]; then
    echo "❌ Download failed!"
    rm -f server.jar
    exit 1
fi

if [ ! -s server.jar ]; then
    echo "❌ Downloaded file is empty or invalid."
    rm -f server.jar
    exit 1
fi

echo ""
echo "✅ paper Download complete!"
echo "📦 server.jar"

echo ""
echo "==============================================="
echo " 💾 Server RAM"
echo "==============================================="

echo ""
read -p "RAM (default 2048M = 2G): " RAM

RAM=${RAM:-2048M}

if [[ "$RAM" =~ ^[0-9]+$ ]]; then
    RAM="${RAM}M"
fi

echo ""
echo "✅ RAM: $RAM"

echo ""
echo "==============================================="
echo " 🕐 TimeZone"
echo "==============================================="

echo ""
echo "Search TimeZoneDB"

read -p "TIMEZONE (default=Asia/Phnom_Penh): " TIMEZONE

TIMEZONE=${TIMEZONE:-Asia/Phnom_Penh}

echo ""
echo "✅ TimeZone: $TIMEZONE"

echo "Select Java Runtime:"
echo "1) Java 21 1.20.5-1.21.11"
echo "2) Java 25 26.x"
read -rp "Choose [1-2]: " JAVA_CHOICE

case "$JAVA_CHOICE" in
    1) OPENJDK="java-21-openjdk" ;;
    2) OPENJDK="java-25-openjdk" ;;
    *)
        echo "Invalid choice!"
        exit 1
        ;;
esac

JAVA="$PREFIX/lib/jvm/$OPENJDK/bin/java"

if [ ! -x "$JAVA" ]; then
    echo "Java runtime not installed: $JAVA"
    exit 1
fi

cat > start.sh <<EOF
#!/data/data/com.termux/files/usr/bin/bash

export TZ="$TIMEZONE"

exec "$JAVA" -Xms$RAM -Xmx$RAM -jar server.jar nogui
EOF

chmod +x start.sh

echo ""
echo "✅ start.sh created"

echo ""
echo "📝 Running server..."
./start.sh

echo ""
echo "==============================================="
echo " 📜 EULA"
echo "==============================================="

echo ""
echo "Accepting EULA..."

if [ -f eula.txt ]; then
    sed -i 's/eula=false/eula=true/g' eula.txt
fi

echo "✅ EULA accepted"

echo ""
echo "==============================================="
echo " ⚙️ Server Settings"
echo "==============================================="

# Online Mode

echo ""
echo "🔐 Online Mode:"
echo "1) false (Offline/Cracked)"
echo "2) true (Premium)"

read -p "Choose (1-2): " ONLINE_CHOICE

case "$ONLINE_CHOICE" in
    1)
        ONLINE_MODE=false
        ;;
    2)
        ONLINE_MODE=true
        ;;
    *)
        echo "⚠️ Invalid choice!"
        echo "Using default: false"
        ONLINE_MODE=false
        ;;
esac

# View Distance

echo ""
read -p " View Distance (chunks, default 10): " VIEW_DISTANCE

VIEW_DISTANCE=${VIEW_DISTANCE:-10}

# Server Port

echo ""
read -p "🌐 Server Port (default 25565): " SERVER_PORT

SERVER_PORT=${SERVER_PORT:-25565}

# Max Players

echo ""
read -p "👥 Max Players (default 20): " MAX_PLAYERS

MAX_PLAYERS=${MAX_PLAYERS:-20}

# Level Seed

echo ""
read -p "🌱 Level Seed (leave blank for random): " LEVEL_SEED

# Hardcore

echo ""
echo "😠 Hardcore Mode:"
echo "1) false (Normal)"
echo "2) true (Hardcore)"

read -p "Choose (1-2): " HARDCORE_CHOICE

case "$HARDCORE_CHOICE" in
    1)
        HARDCORE=false
        ;;
    2)
        HARDCORE=true
        ;;
    *)
        echo "⚠️ Invalid choice!"
        echo "Defaulting to false"
        HARDCORE=false
        ;;
esac

echo ""
read -p "🌈 Enter MOTD: " MOTD

echo ""
echo "==============================================="
echo " ⚙️ Writing Server Properties"
echo "==============================================="

cat > server.properties <<EOF
online-mode=$ONLINE_MODE
view-distance=$VIEW_DISTANCE
server-port=$SERVER_PORT
max-players=$MAX_PLAYERS
hardcore=$HARDCORE
motd=$MOTD
EOF

if [ -n "$LEVEL_SEED" ]; then
    echo "level-seed=$LEVEL_SEED" >> server.properties
fi

echo ""
echo "✅ Settings saved!"

echo ""
echo "==============================================="
echo " 🔌 Plugins"
echo "==============================================="

mkdir -p plugins

echo ""
echo "✅ plugins folder created"

echo ""
echo "==============================================="
echo " ⚡ Server Shortcut"
echo "==============================================="

cat > "$HOME/$SERVERNAME.sh" <<EOF
#!/data/data/com.termux/files/usr/bin/bash

SERVER_PORT="$SERVER_PORT"
SERVER_DIR="\$HOME/$SERVERNAME"

# Detect local IPv4 using Python
ip_address=\$(python -c '
import socket

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
try:
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    if ip.startswith("127.") or ip == "0.0.0.0":
        print("IP_NOT_FOUND")
    else:
        print(ip)
except OSError:
    print("IP_NOT_FOUND")
finally:
    s.close()
' 2>/dev/null)

echo ""
echo "==============================================="
echo " 📜 Paper Minecraft Server"
echo "==============================================="

if [ -n "\$ip_address" ] && [ "\$ip_address" != "IP_NOT_FOUND" ]; then
    echo " Private IPv4 Server Minecraft: \$ip_address:\$SERVER_PORT"
else
    echo " ⚠️ Wi-Fi LAN IP not found"
    echo " Check Wi-Fi connection."
fi

echo "==============================================="

sleep 10

cd "\$SERVER_DIR" || exit 1

./start.sh
EOF

chmod +x "$HOME/$SERVERNAME.sh"

echo ""
echo "✅ Shortcut created"

echo ""
echo "==============================================="
echo " 🎉 Paper Server Installed Successfully"
echo "==============================================="

echo ""
echo "📁 Folder:"
echo "cd $SERVERNAME"

echo ""
echo "▶️ Start server:"
echo "bash $SERVERNAME.sh"

echo ""
echo "==============================================="
echo " 📊 Server Information"
echo "==============================================="

echo ""
echo "📦 Paper Version : $VERSION"
echo "💾 RAM           : $RAM"
echo "🌐 Port          : $SERVER_PORT"
echo "👥 Players       : $MAX_PLAYERS"
echo "🔐 Online-mode   : $ONLINE_MODE"
echo "😠 Hardcore      : $HARDCORE"
echo "🌈 MOTD          : $MOTD"
echo "🕐 TimeZone      : $TIMEZONE"

echo ""
echo "==============================================="
echo " ✅ READY!"
echo "==============================================="
