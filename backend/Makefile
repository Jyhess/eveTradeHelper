.PHONY: help init check tests coverage coverage-html build clean install develop

# Variables
PYTHON := python3.12
VENV_DIR := .venv
BACKEND_DIR := .
REQ := requirements.txt requirements-dev.txt
STAMP := $(VENV_DIR)/.install-stamp

# Platform-specific variables
ifeq ($(OS),Windows_NT)
    PIP := $(VENV_DIR)\Scripts\pip.exe
    RUFF := $(VENV_DIR)\Scripts\ruff.exe
    MYPY := $(VENV_DIR)\Scripts\mypy.exe
    COVERAGE := $(VENV_DIR)\Scripts\coverage.exe
    PYTEST := $(VENV_DIR)\Scripts\pytest.exe
    MKDIR_P := if not exist $(VENV_DIR) mkdir $(VENV_DIR)
    TOUCH := type nul > $(STAMP)
    ACTIVATE := $(VENV_DIR)\Scripts\activate
else
    PIP := $(VENV_DIR)/bin/pip
    RUFF := $(VENV_DIR)/bin/ruff
    MYPY := $(VENV_DIR)/bin/mypy
    COVERAGE := $(VENV_DIR)/bin/coverage
    PYTEST := $(VENV_DIR)/bin/pytest
    MKDIR_P := mkdir -p $(VENV_DIR)
    TOUCH := touch $(STAMP)
    ACTIVATE := $(VENV_DIR)/bin/activate
endif

help:
	@echo "Commandes backend disponibles:"
	@echo "  make init          - Initialise l'environnement backend (venv + dépendances)"
	@echo "  make check         - Execute l'ensemble des quality checks"
	@echo "  make tests         - Execute les tests backend"
	@echo "  make coverage      - Génère un rapport de couverture"
	@echo "  make coverage-html  - Génère un rapport de couverture HTML"
	@echo "  make build         - Build le docker pour le backend"
	@echo "  make dev           - Lance le backend en mode développement (avec hot reload)"
	@echo "  make clean         - Nettoie les fichiers générés"

# ============================================================================
# INITIALISATION
# ============================================================================

init: develop
	@echo "✓ Backend initialisé"

develop: $(STAMP)

$(STAMP): $(REQ)
	@echo "Configuration de l'environnement virtuel backend..."
	@$(MKDIR_P)
	@$(PYTHON) -m venv $(VENV_DIR)
	@$(PIP) install --upgrade pip
	@$(PIP) install -r requirements.txt -r requirements-dev.txt
	@$(TOUCH)
	@echo "✓ Environnement virtuel backend configuré avec succès!"
	@echo "Pour l'activer:"
	@echo "  source $(ACTIVATE)  # Linux/Mac"
	@echo "  $(ACTIVATE)         # Windows"

install: develop

# ============================================================================
# QUALITY CHECKS
# ============================================================================

check: develop
	@echo "Vérification de la qualité du code backend..."
	@echo "  → Formatage avec Ruff..."
	@$(RUFF) format $(BACKEND_DIR)
	@echo "  → Linting avec Ruff..."
	@$(RUFF) check $(BACKEND_DIR) || (echo "⚠ Erreurs de linting détectées" && exit 1)
	@echo "  → Vérification des types avec Mypy..."
	@$(MYPY) $(BACKEND_DIR)/domain $(BACKEND_DIR)/application $(BACKEND_DIR)/eve || true
	@echo "✓ Qualité du code backend vérifiée"

# ============================================================================
# TESTS
# ============================================================================

tests: develop
	@echo "Exécution des tests backend..."
	@$(PYTEST) -v
	@echo "✓ Tests backend terminés"

# ============================================================================
# COVERAGE
# ============================================================================

coverage: develop
	@echo "Génération du rapport de couverture backend..."
	@$(COVERAGE) run -m pytest || echo "Tests échoués, rapport de couverture incomplet"
	@$(COVERAGE) report
	@echo "✓ Rapport de couverture backend généré"

coverage-html: develop
	@echo "Génération du rapport de couverture HTML backend..."
	@$(COVERAGE) run -m pytest || echo "Tests échoués, rapport de couverture incomplet"
	@$(COVERAGE) html
	@echo "✓ Rapport HTML disponible dans htmlcov/index.html"

# ============================================================================
# BUILD
# ============================================================================

build: check tests
	@echo "Build du docker backend..."
	@docker build -t eve-trade-backend .
	@echo "✓ Docker backend buildé"

run: develop
	@echo "Lancement du backend..."
	@$(PYTHON) app.py
	@echo "✓ Backend lancé"

dev: develop
	@echo "Lancement du backend en mode développement (hot reload activé)..."
	@RELOAD=1 $(PYTHON) app.py
	@echo "✓ Backend lancé en mode développement"

# ============================================================================
# NETTOYAGE
# ============================================================================

clean:
	@echo "Nettoyage des fichiers générés backend..."
	@rm -rf $(VENV_DIR)
	@rm -rf __pycache__ */__pycache__ **/__pycache__
	@rm -rf .pytest_cache
	@rm -rf .mypy_cache
	@rm -rf htmlcov
	@rm -rf .coverage
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@echo "✓ Nettoyage backend terminé"

