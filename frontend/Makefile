.PHONY: help init check format lint tests build clean install

# Variables
FRONTEND_DIR := .

help:
	@echo "Commandes frontend disponibles:"
	@echo "  make init          - Installe les dépendances frontend"
	@echo "  make check         - Execute l'ensemble des quality checks"
	@echo "  make format        - Formate le code avec Prettier"
	@echo "  make lint          - Vérifie le code avec ESLint"
	@echo "  make tests         - Execute les tests frontend"
	@echo "  make build         - Build le docker pour le frontend"
	@echo "  make clean         - Nettoie les fichiers générés"

# ============================================================================
# INITIALISATION
# ============================================================================

init: install
	@echo "✓ Frontend initialisé"

install:
	@echo "Installation des dépendances frontend..."
	@npm install
	@echo "✓ Dépendances frontend installées"

# ============================================================================
# QUALITY CHECKS
# ============================================================================

check: format lint
	@echo "✓ Qualité du code frontend vérifiée"

format:
	@echo "Formatage du code frontend avec Prettier..."
	@npm run format
	@echo "✓ Code frontend formaté"

lint:
	@echo "Vérification du code frontend avec ESLint..."
	@npm run lint || (echo "⚠ Erreurs de linting détectées" && exit 1)
	@echo "✓ Linting frontend terminé"

# ============================================================================
# TESTS
# ============================================================================

tests: install
	@echo "Exécution des tests frontend..."
	@npm test -- --run
	@echo "✓ Tests frontend terminés"

# ============================================================================
# BUILD
# ============================================================================

build: check tests
	@echo "Build du docker frontend..."
	@docker build -t eve-trade-frontend .
	@echo "✓ Docker frontend buildé"

# ============================================================================
# BUILD
# ============================================================================

run: install
	@echo "Lancement du frontend..."
	@npm run dev
	@echo "✓ Frontend lancé"

# ============================================================================
# NETTOYAGE
# ============================================================================

clean:
	@echo "Nettoyage des fichiers générés frontend..."
	@rm -rf node_modules dist build coverage .cache
	@echo "✓ Nettoyage frontend terminé"

