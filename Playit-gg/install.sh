#!/data/data/com.termux/files/usr/bin/bash

echo "Install Playit-gg"

yes | pkg install tur-repo -y 
yes | pkg install playit -y

cat > ~/playit.sh <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash

PLAYIT_PID=""

cleanup() {
    trap - INT TERM EXIT

    if [ -n "$PLAYIT_PID" ] && kill -0 "$PLAYIT_PID" 2>/dev/null; then
        kill "$PLAYIT_PID" 2>/dev/null
        wait "$PLAYIT_PID" 2>/dev/null
    fi
}

trap 'exit 130' INT
trap 'exit 143' TERM
trap cleanup EXIT

# Reuse an existing daemon if one is running
if pgrep -x playitd >/dev/null 2>&1; then
    echo "Playit daemon is already running."
else
    playitd &
    PLAYIT_PID=$!
    sleep 2

    if ! kill -0 "$PLAYIT_PID" 2>/dev/null; then
        echo "Error: playitd failed to start!"
        exit 1
    fi

    echo "Playit daemon started (PID: $PLAYIT_PID)"
fi

echo "Starting Playit CLI..."
playit-cli
EOF

chmod +x ~/playit.sh

clear

echo "Run playit-gg"
echo "playit.sh"
