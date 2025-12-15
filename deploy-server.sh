#!/bin/bash
# =============================================================================
# Medealis Server Deployment Script
# =============================================================================
# Deployment-Script für Server 10.190.140.10
# Führt alle notwendigen Schritte für Produktion-Deployment aus
# =============================================================================

set -e  # Exit bei Fehler

echo "🚀 Medealis Server Deployment Script"
echo "======================================"

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Konfiguration
DEPLOY_DIR="/opt/medealis"
DATA_DIR="/var/medealis"
SERVER_STORAGE_MOUNT="/mnt/medealis_server"
SERVER_STORAGE_UNC="//10.190.140.10/Allgemein/Qualitätsmanagement/QM_Medealis/03. Produkte/Chargenverwaltung/Produktionsunterlagen"

# 1. Voraussetzungen prüfen
echo ""
echo "📋 Schritt 1: Voraussetzungen prüfen..."
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker ist nicht installiert!${NC}"
    echo "Installiere Docker mit: sudo apt install docker.io docker-compose"
    exit 1
fi
echo -e "${GREEN}✅ Docker gefunden${NC}"

# 2. Verzeichnisse erstellen
echo ""
echo "📁 Schritt 2: Verzeichnisse erstellen..."
sudo mkdir -p "$DATA_DIR/postgres_data"
sudo mkdir -p "$DATA_DIR/user_data"
sudo mkdir -p "$DATA_DIR/logs"
sudo mkdir -p "$SERVER_STORAGE_MOUNT"
echo -e "${GREEN}✅ Verzeichnisse erstellt${NC}"

# 3. Server-Storage mounten (CIFS)
echo ""
echo "💾 Schritt 3: Server-Storage konfigurieren..."
echo -e "${YELLOW}Prüfe ob Server-Storage bereits gemountet ist...${NC}"

if mountpoint -q "$SERVER_STORAGE_MOUNT"; then
    echo -e "${GREEN}✅ Server-Storage bereits gemountet${NC}"
else
    echo -e "${YELLOW}⚠️  Server-Storage nicht gemountet${NC}"
    echo "Möchtest du CIFS-Mount einrichten? (j/n)"
    read -r SETUP_CIFS

    if [ "$SETUP_CIFS" = "j" ] || [ "$SETUP_CIFS" = "J" ]; then
        # CIFS-Utils installieren
        if ! command -v mount.cifs &> /dev/null; then
            echo "Installiere cifs-utils..."
            sudo apt update
            sudo apt install -y cifs-utils
        fi

        # Credentials abfragen
        echo "Benutzername für \\\\10.190.140.10\\Allgemein:"
        read -r SMB_USER
        echo "Passwort:"
        read -rs SMB_PASS
        echo "Domain (oder Enter für keinen):"
        read -r SMB_DOMAIN

        # Credentials-Datei erstellen
        sudo bash -c "cat > /root/.medealis_smb_credentials << EOF
username=$SMB_USER
password=$SMB_PASS
domain=${SMB_DOMAIN:-WORKGROUP}
EOF"
        sudo chmod 600 /root/.medealis_smb_credentials

        # Mounten
        echo "Mounte Server-Storage..."
        sudo mount -t cifs "$SERVER_STORAGE_UNC" "$SERVER_STORAGE_MOUNT" \
            -o credentials=/root/.medealis_smb_credentials,uid=1000,gid=1000,file_mode=0777,dir_mode=0777

        # Zu /etc/fstab hinzufügen für persistenten Mount
        if ! grep -q "$SERVER_STORAGE_MOUNT" /etc/fstab; then
            echo "Füge Mount zu /etc/fstab hinzu für Auto-Mount bei Reboot..."
            echo "$SERVER_STORAGE_UNC $SERVER_STORAGE_MOUNT cifs credentials=/root/.medealis_smb_credentials,uid=1000,gid=1000,file_mode=0777,dir_mode=0777 0 0" | sudo tee -a /etc/fstab
        fi

        echo -e "${GREEN}✅ Server-Storage gemountet${NC}"
    else
        echo -e "${YELLOW}⚠️  Server-Storage übersprungen - lokale Speicherung wird verwendet${NC}"
    fi
fi

# 4. .env Datei vorbereiten
echo ""
echo "⚙️  Schritt 4: Umgebungsvariablen konfigurieren..."
if [ ! -f "$DEPLOY_DIR/.env" ]; then
    if [ -f "$DEPLOY_DIR/.env.production" ]; then
        echo "Kopiere .env.production zu .env..."
        cp "$DEPLOY_DIR/.env.production" "$DEPLOY_DIR/.env"
        echo -e "${YELLOW}⚠️  WICHTIG: Bitte .env Datei bearbeiten und Passwörter ändern!${NC}"
        echo "Editor öffnen? (j/n)"
        read -r EDIT_ENV
        if [ "$EDIT_ENV" = "j" ] || [ "$EDIT_ENV" = "J" ]; then
            nano "$DEPLOY_DIR/.env"
        fi
    else
        echo -e "${RED}❌ Keine .env.production Vorlage gefunden!${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ .env Datei existiert bereits${NC}"
fi

# 5. Docker Images bauen
echo ""
echo "🏗️  Schritt 5: Docker Images bauen..."
cd "$DEPLOY_DIR"
docker-compose -f docker-compose.prod.yaml build --no-cache
echo -e "${GREEN}✅ Images gebaut${NC}"

# 6. Docker Container starten
echo ""
echo "🚀 Schritt 6: Container starten..."
docker-compose -f docker-compose.prod.yaml up -d
echo -e "${GREEN}✅ Container gestartet${NC}"

# 7. Status prüfen
echo ""
echo "📊 Schritt 7: Status prüfen..."
sleep 5  # Kurz warten
docker-compose -f docker-compose.prod.yaml ps

# 8. Logs anzeigen
echo ""
echo "📝 Logs (Ctrl+C zum Beenden):"
docker-compose -f docker-compose.prod.yaml logs -f --tail=50

# Fertig
echo ""
echo -e "${GREEN}✅ Deployment abgeschlossen!${NC}"
echo ""
echo "Zugriff auf die Anwendung:"
echo "  Admin-Interface: http://10.190.140.10:8501"
echo "  User-Interface:  http://10.190.140.10:8502"
echo ""
echo "Nützliche Befehle:"
echo "  Status anzeigen:    docker-compose -f docker-compose.prod.yaml ps"
echo "  Logs anzeigen:      docker-compose -f docker-compose.prod.yaml logs -f"
echo "  Stoppen:            docker-compose -f docker-compose.prod.yaml down"
echo "  Neu starten:        docker-compose -f docker-compose.prod.yaml restart"
