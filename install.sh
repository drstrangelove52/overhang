#!/bin/bash
set -e

REPO_URL="https://github.com/drstrangelove52/overhang.git"
INSTALL_DIR="/opt/overhang"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()    { echo -e "[overhang] $1"; }
warn()    { echo -e "[overhang] $1"; }
error()   { echo -e "[overhang] $1"; exit 1; }

# --- Check dependencies ---
command -v docker  >/dev/null 2>&1 || error "Docker nicht gefunden. Bitte installieren: https://docs.docker.com/engine/install/"
command -v openssl >/dev/null 2>&1 || error "openssl nicht gefunden (apt install openssl)"
docker compose version >/dev/null 2>&1 || error "Docker Compose Plugin nicht gefunden"

info "Overhang Installer"
echo "================================================"

# --- Clone or update repo ---
if [ -d "$INSTALL_DIR/.git" ]; then
    info "Vorhandene Installation gefunden — aktualisiere..."
    git -C "$INSTALL_DIR" pull
else
    info "Klone Repository nach $INSTALL_DIR ..."
    git clone "$REPO_URL" "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"

# --- .env setup ---
if [ ! -f .env ]; then
    info "Erstelle .env aus Vorlage..."
    cp .env.example .env
    # Auto-generate secrets
    DB_PASS=$(openssl rand -hex 20)
    SECRET=$(openssl rand -hex 32)
    sed -i "s/MYSQL_ROOT_PASSWORD=changeme/MYSQL_ROOT_PASSWORD=$(openssl rand -hex 20)/" .env
    sed -i "s/MYSQL_PASSWORD=changeme/MYSQL_PASSWORD=$DB_PASS/" .env
    sed -i "s|mysql+aiomysql://overhang:changeme|mysql+aiomysql://overhang:$DB_PASS|" .env
    sed -i "s/SECRET_KEY=change-this-to-a-random-secret/SECRET_KEY=$SECRET/" .env
    info ".env erstellt mit zufälligen Passwörtern"
else
    warn ".env existiert bereits — wird nicht überschrieben"
fi

# --- TLS certificate ---
CERT_DIR="$INSTALL_DIR/certs"
mkdir -p "$CERT_DIR"

if [ ! -f "$CERT_DIR/cert.pem" ]; then
    info "Generiere selbstsigniertes TLS-Zertifikat (10 Jahre)..."
    HOSTNAME=$(hostname -f 2>/dev/null || hostname)
    openssl req -x509 -nodes -newkey rsa:2048         -keyout "$CERT_DIR/key.pem"         -out "$CERT_DIR/cert.pem"         -days 3650         -subj "/CN=$HOSTNAME/O=Overhang/C=CH"         -addext "subjectAltName=IP:127.0.0.1,DNS:$HOSTNAME,DNS:localhost"
    chmod 600 "$CERT_DIR/key.pem"
    info "Zertifikat erstellt für: $HOSTNAME"
else
    warn "TLS-Zertifikat existiert bereits — wird nicht überschrieben"
fi

# --- Build & start ---
info "Baue und starte Container..."
docker compose pull --ignore-buildable
docker compose up --build -d

# --- Wait for health ---
info "Warte auf Dienste..."
sleep 15

if curl -sk https://localhost/api/health | grep -q '"ok"'; then
    echo ""
    echo -e "${GREEN}================================================${NC}"
    echo -e "${GREEN}  Overhang läuft! ${NC}"
    echo -e "${GREEN}  https://$(hostname -f 2>/dev/null || hostname)${NC}"
    echo -e "${GREEN}  https://$(hostname -I | awk '{print $1}')${NC}"
    echo -e "${GREEN}================================================${NC}"
    echo ""
    warn "Hinweis: Browser-Warnung beim ersten Aufruf wegen self-signed Zertifikat"
    warn "        einfach mit 'Trotzdem fortfahren' bestätigen"
else
    warn "Dienste noch nicht bereit. Status prüfen mit: docker compose -f $INSTALL_DIR ps"
fi
