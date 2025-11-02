#!/bin/bash

echo "===================================="
echo "Configuration de l'environnement"
echo "===================================="
echo ""

echo "[1/3] Création de l'environnement virtuel Python..."
python3 -m venv .venv
if [ $? -ne 0 ]; then
    echo "ERREUR: Impossible de créer l'environnement virtuel"
    exit 1
fi

echo ""
echo "[2/3] Activation de l'environnement virtuel..."
source .venv/bin/activate

echo ""
echo "[3/3] Installation des dépendances Python..."
pip install --upgrade pip
pip install -r backend/requirements.txt
if [ $? -ne 0 ]; then
    echo "ERREUR: Impossible d'installer les dépendances"
    exit 1
fi

echo ""
echo "[4/4] Installation des dépendances Node.js..."
cd frontend
npm install
if [ $? -ne 0 ]; then
    echo "ERREUR: Impossible d'installer les dépendances Node.js"
    exit 1
fi
cd ..

echo ""
echo "===================================="
echo "Configuration terminée avec succès!"
echo "===================================="
echo ""
echo "Pour activer l'environnement virtuel:"
echo "  source .venv/bin/activate"
echo ""

