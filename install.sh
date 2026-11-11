#!/bin/bash==========================================PsiMan Quantum - Interactive Installer==========================================GREEN='\033[1;32m'
CYAN='\033[1;36m'
YELLOW='\033[1;33m'
RED='\033[1;31m'
WHITE='\033[1;37m'
NC='\033[0m'clear
echo -e "${CYAN}╭──────────────────────────────────────────────────────╮${NC}"
echo -e "${CYAN}│          🐅 INSTALLING PSIMAN QUANTUM 🐅             │${NC}"
echo -e "${CYAN}╰──────────────────────────────────────────────────────╯${NC}"1. Check Rootif [ "$EUID" -ne 0 ]; then
echo -e "${RED}Please run as root! (sudo bash install.sh)${NC}"
exit 1
fi2. Interactive Configurationecho -e "\n${WHITE}⚙️  Panel Configuration${NC}"
echo -e "────────────────────────────────────────────────────────"Port (Optional - Default 8585)echo -ne "${CYAN}▶ Enter Web Panel Port ${YELLOW}[Default: 8585]:${NC}"
read INPUT_PORT
PORT=${INPUT_PORT:-8585}Username (Required - Cannot be empty)while true; do
echo -ne "${CYAN}▶ Enter Admin Username ${RED}[Required]:${NC}"
read PANEL_USER
if [ -n "$PANEL_USER" ]; then
break
else
echo -e "${RED}  ❌ Username cannot be empty! Please try again.${NC}"
fi
donePassword (Required - Cannot be empty)while true; do
echo -ne "${CYAN}▶ Enter Admin Password ${RED}[Required]:${NC}"
read PANEL_PASS
if [ -n "$PANEL_PASS" ]; then
break
else
echo -e "${RED}  ❌ Password cannot be empty! Please try again.${NC}"
fi
doneecho -e "────────────────────────────────────────────────────────\n"3. Update and Install Dependenciesecho -e "${GREEN}[1/5] Installing dependencies (Python, Flask, Waitress)...${NC}"
apt update -y > /dev/null 2>&1
apt install python3-flask python3-pip curl wget -y > /dev/null 2>&1
pip3 install waitress > /dev/null 2>&14. Download Psiphon Coreecho -e "${GREEN}[2/5] Downloading latest Psiphon Core engine...${NC}"
wget -qO /usr/local/bin/psiphon https://github.com/Psiphon-Labs/psiphon-tunnel-core-binaries/raw/master/linux/psiphon-tunnel-core-x86_64
chmod +x /usr/local/bin/psiphon5. Download Web Panelecho -e "${GREEN}[3/5] Fetching PsiMan Web Application...${NC}"⚠️ REPLACE THE URL BELOW WITH YOUR ACTUAL RAW GITHUB LINK FOR psiweb.py ⚠️wget -qO /opt/psiweb.py https://raw.githubusercontent.com/YOUR_GITHUB_USERNAME/PsiMan/main/psiweb.py6. Apply Custom Configurationsecho -e "${GREEN}[4/5] Applying your custom port and credentials...${NC}"
sed -i "s/port=8585/port=$PORT/g" /opt/psiweb.py
echo "{"username": "$PANEL_USER", "password": "$PANEL_PASS"}" > /opt/psi_config.json
chmod 600 /opt/psi_config.json7. Setup Systemd Serviceecho -e "${GREEN}[5/5] Setting up background service...${NC}"
cat < /etc/systemd/system/psiweb.service
[Unit]
Description=PsiMan Quantum Web Dashboard
After=network.target[Service]
Type=simple
User=root
ExecStart=/usr/bin/python3 /opt/psiweb.py
Restart=always[Install]
WantedBy=multi-user.target
EOFsystemctl daemon-reload
systemctl enable psiweb > /dev/null 2>&1
systemctl restart psiweb8. Done!SERVER_IP=$(curl -s https://api.ipify.org)
echo -e "\n${CYAN}╭──────────────────────────────────────────────────────╮${NC}"
echo -e "${CYAN}│ ✔ INSTALLATION COMPLETE!                             │${NC}"
echo -e "${CYAN}├──────────────────────────────────────────────────────┤${NC}"
echo -e "${CYAN}│ 🌍 URL      : ${WHITE}http://$SERVER_IP:$PORT${NC}"
echo -e "${CYAN}│ 👤 Username : ${WHITE}$PANEL_USER${NC}"
echo -e "${CYAN}│ 🔑 Password : ${WHITE}$PANEL_PASS${NC}"
echo -e "${CYAN}╰──────────────────────────────────────────────────────╯${NC}"
echo -e "${YELLOW}Enjoy your Enterprise Dashboard! 🚀${NC}\n"
