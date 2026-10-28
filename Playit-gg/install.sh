#!/data/data/com.termux/files/usr/bin/bash

echo "Install Playit-gg"

yes | pkg install tur-repo -y 
yes | pkg install playit -y

cat > ~/playit.sh <<'EOF'

#!/data/data/com.termux/files/usr/bin/bash

cd "$HOME" || exit 1

# Start playit daemon in background (hidden)
nohup ./playitd \
    >/dev/null 2>&1 </dev/null &

PLAYIT_PID=$!

echo "Playit background started (PID: $PLAYIT_PID)"
sleep 2

# Start CLI in foreground (visible)
echo "Starting Playit CLI..."
exec ./playit-cli
EOF

chmod +x ~/playit.sh

echo "Run playit-gg"
echo "playit.sh"
