#!/data/data/com.termux/files/usr/bin/bash

echo "Install Playit-gg"

yes | pkg install tur-repo -y 
yes | pkg install playit -y

cat > ~/playit.sh <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash

cd "$HOME" || exit 1

command -v playitd >/dev/null 2>&1 || {
echo "Error: playitd command not found!"
exit 1
}

command -v playit-cli >/dev/null 2>&1 || {
echo "Error: playit-cli command not found!"
exit 1
}

nohup playitd >/dev/null 2>&1 </dev/null &
PLAYIT_PID=$!

echo "Playit daemon started (PID: $PLAYIT_PID)"
sleep 2

if ! kill -0 "$PLAYIT_PID" 2>/dev/null; then
echo "Error: playitd stopped unexpectedly!"
exit 1
fi

echo "Starting Playit CLI..."
exec playit-cli
EOF

chmod +x ~/playit.sh

clear

echo "Run playit-gg"
echo "playit.sh"
