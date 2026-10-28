
#!/data/data/com.termux/files/usr/bin/bash

cd "$HOME" || exit 1

# Check files
if [ ! -x ./playit-linux-aarch64 ]; then
    echo "Error: playit-linux-aarch64 not found!"
    exit 1
fi

if [ ! -x ./playit-cli-linux-aarch64 ]; then
    echo "Error: playit-cli-linux-aarch64 not found!"
    exit 1
fi

# Start playit daemon in background (hidden)
nohup ./playit-linux-aarch64 \
    >/dev/null 2>&1 </dev/null &

PLAYIT_PID=$!

echo "Playit background started (PID: $PLAYIT_PID)"
sleep 2

# Start CLI in foreground (visible)
echo "Starting Playit CLI..."
exec ./playit-cli-linux-aarch64
