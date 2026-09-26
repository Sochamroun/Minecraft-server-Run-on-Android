#!/data/data/com.termux/files/usr/bin/bash

clear

echo "==============================================="
echo " 🍃 Minecraft Leaf Server Install"
echo " 🌐 Termux Script Auto Setup by Sochamroun🤓"
echo "==============================================="

sleep 2

echo ""
echo "==============================================="
echo " 📁 Server Folder"
echo "==============================================="

echo ""
read -p "Enter server folder 📂 name: " SERVERNAME

mkdir -p ~/"$SERVERNAME"
cd ~/"$SERVERNAME" || exit 1

echo ""
echo "==============================================="
echo " 🎲 Minecraft Version"
echo "==============================================="
echo ""
echo "Example: 1.21.11"
echo ""

read -p "Version: " VERSION

if [ -z "$VERSION" ]; then
    echo "❌ Version cannot be empty!"
    exit 1
fi

echo ""
echo "🍃 Searching Leaf release..."
echo "Minecraft: $VERSION"

API_URL="https://api.github.com/repos/Winds-Studio/Leaf/releases/tags/ver-$VERSION"

RELEASE_JSON=$(curl -fsSL \
    -H "Accept: application/vnd.github+json" \
    "$API_URL")

if [ -z "$RELEASE_JSON" ]; then
    echo "❌ Cannot connect to Leaf GitHub API!"
    exit 1
fi

URL=$(echo "$RELEASE_JSON" | jq -r '
    .assets[]
    | select(.name | test("\\.jar$"))
    | .browser_download_url
' | head -n 1)

JAR_NAME=$(echo "$RELEASE_JSON" | jq -r '
    .assets[]
    | select(.name | test("\\.jar$"))
    | .name
' | head -n 1)

if [ -z "$URL" ] || [ "$URL" = "null" ]; then
    echo ""
    echo "❌ Leaf version not found!"
    echo ""
    echo "Available versions:"
    curl -fsSL \
        -H "Accept: application/vnd.github+json" \
        "https://api.github.com/repos/Winds-Studio/Leaf/releases?per_page=30" |
        jq -r '.[].tag_name' |
        sed 's/^ver-//'
    exit 1
fi

echo ""
echo "✅ Leaf found!"
echo "📦 JAR: $JAR_NAME"
echo "⬇️ Downloading..."

wget -O server.jar "$URL"

if [ $? -ne 0 ]; then
    echo "❌ Download failed!"
    rm -f server.jar
    exit 1
fi

echo ""
echo "✅ Leaf download complete!"
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
read -p "TIMEZONE (default=Asia/Phnom_Penh): " TIMEZONE

TIMEZONE=${TIMEZONE:-Asia/Phnom_Penh}


echo ""
echo "Creating start.sh..."

cat > start.sh <<EOF
#!/data/data/com.termux/files/usr/bin/bash

export TZ="$TIMEZONE"

java -Xms$RAM -Xmx$RAM -jar server.jar nogui
EOF

chmod +x start.sh

echo ""
echo "RAM=$RAM"
echo "TIMEZONE=$TIMEZONE"

sleep 2

echo ""
echo "==============================================="
echo " 🍃 Starting Leaf first time..."
echo "==============================================="

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

cat > ~/$SERVERNAME.sh <<EOF
#!/data/data/com.termux/files/usr/bin/bash

ip_address=\$(ip -4 addr show wlan0 | grep -oP 'inet \K[\d.]+')

echo "==============================================="
echo " 🍃 Paper Minecraft Server"
echo "IPv4 Server Minecraft ✅: \$ip_address:$SERVER_PORT"
echo "==============================================="

sleep 10

cd ~/$SERVERNAME || exit

./start.sh
EOF

chmod +x ~/$SERVERNAME.sh

echo ""
echo "✅ Shortcut created"

echo ""
echo "==============================================="
echo " 🎉 Paper Server Installed Successfully"
echo "==============================================="

echo ""
echo "📁 Folder:"
echo ""
echo "✅ Download complete!"
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

echo ""
echo "==============================================="
echo " ▶️ Creating Start Script"
echo "==============================================="

cat > start.sh <<EOF
#!/data/data/com.termux/files/usr/bin/bash

export TZ=$TIMEZONE

java -Xms$RAM -Xmx$RAM -jar server.jar nogui
EOF

chmod +x start.sh

echo ""
echo "✅ start.sh created"

echo ""
echo "==============================================="
echo " 🚀 Starting Paper First Time"
echo "==============================================="

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

cat > ~/$SERVERNAME.sh <<EOF
#!/data/data/com.termux/files/usr/bin/bash

ip_address=\$(ip -4 addr show wlan0 | grep -oP 'inet \K[\d.]+')

echo "==============================================="
echo " 🍃 Paper Minecraft Server"
echo "IPv4 Server Minecraft ✅: \$ip_address:$SERVER_PORT"
echo "==============================================="

sleep 10

cd ~/$SERVERNAME || exit

./start.sh
EOF

chmod +x ~/$SERVERNAME.sh

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
