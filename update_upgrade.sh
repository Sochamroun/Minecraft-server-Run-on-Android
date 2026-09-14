#!/data/data/com.termux/files/usr/bin/bash

echo "Starting Termux Setup install software..."
# Server 
termux-change-repo
# update 
yes | pkg update && yes | pkg upgrade

# Install packages
yes | pkg install python git jq tmux wget iproute2 unzip fish nano nodejs nmap -y
yes | pkg install openjdk-21 openjdk-17 openjdk-25 -y
# pip install
pip install -U mcstatus dnspython

# Fix fish config folder (important)
mkdir -p ~/.config/fish

# Set fish shell (safe)
chsh -s fish || echo "⚠️ Cannot change shell (ignore if error)"

# Fix PATH
grep -qxF 'set -U fish_user_paths $fish_user_paths $HOME' ~/.config/fish/config.fish || \
echo 'set -U fish_user_paths $fish_user_paths $HOME' >> ~/.config/fish/config.fish

echo "THANK You"
