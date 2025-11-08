.PHONY: help init develop check format lint typecheck test test-unit test-integration coverage coverage-html all clean install-frontend

PYTHON := python3.12
VENV_DIR := .venv
BACKEND_DIR := backend
REQ := $(BACKEND_DIR)/requirements.txt $(BACKEND_DIR)/requirements-dev.txt
STAMP := $(VENV_DIR)/.install-stamp

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
	@echo "Commandes disponibles:"
	@echo "  make init             - Installer toutes les dépendances (backend + frontend)"
	@echo "  make develop          - Créer et configurer l'environnement virtuel"
	@echo "  make check            - Vérifier la qualité du code (format, lint, typecheck)"
	@echo "  make format           - Formater le code avec Ruff"
	@echo "  make lint             - Vérifier le code avec Ruff (sans formater)"
	@echo "  make typecheck        - Vérifier les types avec Mypy"
	@echo "  make test             - Exécuter tous les tests"
	@echo "  make test-unit        - Exécuter uniquement les tests unitaires"
	@echo "  make test-integration - Exécuter uniquement les tests d'intégration"
	@echo "  make coverage         - Générer un rapport de couverture"
	@echo "  make coverage-html   - Générer un rapport de couverture HTML"
	@echo "  make all              - Vérifier la qualité, exécuter les tests et générer la couverture"
	@echo "  make install-frontend - Installer les dépendances frontend"
	@echo "  make clean             - Nettoyer les fichiers générés"

init: develop install-frontend
	@echo "✓ Installation complète terminée"

$(STAMP): $(REQ)
	@echo "Configuration de l'environnement virtuel..."
	@$(MKDIR_P)
	@$(PYTHON) -m venv $(VENV_DIR)
	@$(PIP) install --upgrade pip
	@$(PIP) install -r $(BACKEND_DIR)/requirements.txt -r $(BACKEND_DIR)/requirements-dev.txt
	@$(TOUCH)
	@echo "Environnement virtuel configuré avec succès!"
	@echo "Pour l'activer:"
	@echo "  source $(ACTIVATE)  # Linux/Mac"
	@echo "  $(ACTIVATE)         # Windows"

develop: $(STAMP)

check: develop
	@echo "Vérification de la qualité du code..."
	@echo "  → Formatage avec Ruff..."
	@$(RUFF) format $(BACKEND_DIR)
	@echo "  → Linting avec Ruff..."
	@$(RUFF) check $(BACKEND_DIR)
	@echo "  → Vérification des types avec Mypy..."
	@$(MYPY) $(BACKEND_DIR)/domain $(BACKEND_DIR)/application $(BACKEND_DIR)/eve
	@echo "✓ Qualité du code vérifiée"

format: develop
	@echo "Formatage du code avec Ruff..."
	@$(RUFF) format $(BACKEND_DIR)

lint: develop
	@echo "Vérification du code avec Ruff (sans formater)..."
	@$(RUFF) check $(BACKEND_DIR)
	@$(RUFF) format --check $(BACKEND_DIR)

typecheck: develop
	@echo "Vérification des types avec Mypy..."
	@$(MYPY) $(BACKEND_DIR)/domain $(BACKEND_DIR)/application $(BACKEND_DIR)/eve

test: develop
	@echo "Exécution de tous les tests..."
	@cd $(BACKEND_DIR) && $(PYTHON) -m pytest -v

test-unit: develop
	@echo "Exécution des tests unitaires..."
	@cd $(BACKEND_DIR) && $(PYTHON) -m pytest unit_tests/ -m unit -v

test-integration: develop
	@echo "Exécution des tests d'intégration..."
	@cd $(BACKEND_DIR) && $(PYTHON) -m pytest integration_tests/ -m integration -v

coverage: develop
	@echo "Génération du rapport de couverture..."
	@cd $(BACKEND_DIR) && $(COVERAGE) run -m pytest || echo "Tests échoués, rapport de couverture incomplet"
	@cd $(BACKEND_DIR) && $(COVERAGE) report

coverage-html: develop
	@echo "Génération du rapport de couverture HTML..."
	@cd $(BACKEND_DIR) && $(COVERAGE) run -m pytest || echo "Tests échoués, rapport de couverture incomplet"
	@cd $(BACKEND_DIR) && $(COVERAGE) html
	@echo "Rapport HTML disponible dans $(BACKEND_DIR)/htmlcov/index.html"

install-frontend:
	@echo "Installation des dépendances frontend..."
	@cd frontend && npm install

all: check test coverage

clean:
	@echo "Nettoyage des fichiers générés..."
	@rm -rf $(VENV_DIR)
	@rm -rf $(BACKEND_DIR)/__pycache__ $(BACKEND_DIR)/**/__pycache__
	@rm -rf $(BACKEND_DIR)/.pytest_cache
	@rm -rf $(BACKEND_DIR)/.mypy_cache
	@rm -rf $(BACKEND_DIR)/htmlcov
	@rm -rf $(BACKEND_DIR)/.coverage
	@find $(BACKEND_DIR) -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@echo "Nettoyage terminé"
