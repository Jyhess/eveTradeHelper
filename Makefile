.PHONY: help init back front check tests build clean

# Variables
BACKEND_DIR := backend
FRONTEND_DIR := frontend

help:
	@echo "Commandes disponibles:"
	@echo ""
	@echo "Initialisation:"
	@echo "  make init          - Initialise front et back (dépendances + environnement)"
	@echo "  make back          - Initialise, lance les tests et build le docker pour le back"
	@echo "  make front         - Initialise, lance les tests et build le docker pour le front"
	@echo "  make all           - Initialise, teste et build le docker pour back et front"
	@echo ""
	@echo "Quality checks:"
	@echo "  make check         - Execute l'ensemble des quality checks (back + front)"
	@echo ""
	@echo "Tests:"
	@echo "  make tests         - Execute les tests pour back et front"
	@echo ""
	@echo "Build:"
	@echo "  make build         - Build le docker pour back et front (nécessite init avant)"
	@echo ""
	@echo "Nettoyage:"
	@echo "  make clean         - Nettoie tous les fichiers générés (back + front)"

init:
	@$(MAKE) -C $(BACKEND_DIR) init
	@$(MAKE) -C $(FRONTEND_DIR) init
	@echo "✓ Initialisation complète terminée (back + front)"

back:
	@$(MAKE) -C $(BACKEND_DIR) init
	@$(MAKE) -C $(BACKEND_DIR) build
	@echo "✓ Backend: initialisation, tests et build terminés"

front:
	@$(MAKE) -C $(FRONTEND_DIR) init
	@$(MAKE) -C $(FRONTEND_DIR) build
	@echo "✓ Frontend: initialisation, tests et build terminés"

all: back front
	@echo "✓ Toutes les tâches terminées (back + front)"

check:
	@$(MAKE) -C $(BACKEND_DIR) check
	@$(MAKE) -C $(FRONTEND_DIR) check
	@echo "✓ Tous les quality checks terminés (back + front)"

tests:
	@$(MAKE) -C $(BACKEND_DIR) tests
	@$(MAKE) -C $(FRONTEND_DIR) tests
	@echo "✓ Tous les tests terminés (back + front)"

build: back front
	@echo "✓ Build complet terminé (back + front)"

run:
	docker compose up --build
	@echo "✓ Lancement complet terminé (back + front)"

clean:
	@$(MAKE) -C $(BACKEND_DIR) clean
	@$(MAKE) -C $(FRONTEND_DIR) clean
	@echo "✓ Nettoyage complet terminé (back + front)"
