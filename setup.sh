#!/data/data/com.termux/files/usr/bin/bash

curl -sL https://raw.githubusercontent.com/Sochamroun/Minecraft-server-Run-on-Android/refs/heads/main/Install.sh | bash

yes | pkg install openjdk-21 openjdk-25 -y

curl -#LO https://raw.githubusercontent.com/Sochamroun/Minecraft-server-Run-on-Android/refs/heads/main/server/paper_mc.sh && chmod +x paper_mc.sh

curl -#LO https://raw.githubusercontent.com/Sochamroun/Minecraft-server-Run-on-Android/refs/heads/main/server/vanilla_mc.sh && chmod +x vanilla_mc.sh

curl -#LO https://raw.githubusercontent.com/Sochamroun/Minecraft-server-Run-on-Android/refs/heads/main/server/leaf_mc.sh && chmod +x leaf_mc.sh

curl -#LO https://raw.githubusercontent.com/Sochamroun/Minecraft-server-Run-on-Android/refs/heads/main/server/Java_Runime.sh && chmod +x Java_Runime.sh

curl -#LO https://raw.githubusercontent.com/Sochamroun/Minecraft-server-Run-on-Android/refs/heads/main/server/panel.py

echo " All in One "

echo "" 
echo "============================"
echo "Command Line to Start Script"
echo "============================"
echo "./paper_mc.sh = 📜 Paper Server Install"
echo "./vanilla_mc.sh = 🥱 vanilla server install"
echo "./leaf_mc.sh = 🌿 Leaf Server Install"
echo "./Java_Runime.sh = ⛓️ Change Java Runtime"
echo "python panel.py = Panel Start Server On Webpage"
