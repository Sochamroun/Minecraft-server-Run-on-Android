#!/data/data/com.termux/files/usr/bin/bash

echo "Install Playit-gg"

yes | pkg install playit -y

cat > ~/playit.sh <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash

pgrep -x playitd >/dev/null || playitd &
sleep 2
exec playit-cli
EOF

chmod +x ~/playit.sh

echo "Run playit-gg"
echo "playit.sh"
