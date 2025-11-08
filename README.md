# Eve Trade Helper

Application web pour analyser les opportunités de trading dans EVE Online, avec backend Python (FastAPI) et frontend Vue.js, orchestrée avec Docker Compose.

## 🚀 Installation et démarrage

### Prérequis

- Python 3.12+
- Node.js 18+
- Docker et Docker Compose (pour le mode production)
- Make (optionnel, pour simplifier les commandes)

### Installation

```bash
# Installer toutes les dépendances (backend + frontend)
make init
```

### Démarrage

#### Mode production (Docker)

```bash
docker-compose up --build
```

- Frontend : <http://localhost:8080>
- Backend API : <http://localhost:5001>

#### Mode développement

```bash
# Backend (dans un terminal)
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate     # Windows
python backend/app.py

# Frontend (dans un autre terminal)
cd frontend && npm run dev
```

## 📁 Architecture

L'application est composée de trois services principaux :

- **Frontend** : Application Vue.js 3 servant l'interface utilisateur
- **Backend** : API REST FastAPI (Python) fournissant les données et la logique métier
- **Redis** : Cache partagé pour optimiser les performances et réduire les appels API externes

**Pour plus de détails** :

- 📖 [Architecture Backend](backend/ARCHITECTURE.md)
- 📖 [Architecture Frontend](frontend/ARCHITECTURE.md)

## 🛠️ Commandes utiles

### Développement

```bash
make help              # Voir toutes les commandes disponibles
make check             # Vérifier la qualité du code (format, lint, typecheck)
make test              # Exécuter tous les tests
make test-unit         # Tests unitaires uniquement
make test-integration  # Tests d'intégration uniquement
make coverage          # Rapport de couverture
make all               # Tout exécuter (check, test, coverage)
```

### Docker

```bash
docker-compose up -d           # Démarrer en arrière-plan
docker-compose down            # Arrêter les services
docker-compose logs -f         # Voir les logs
docker-compose build --no-cache # Reconstruire les images
```

## 🐛 Débogage

Pour les détails sur le débogage :

- 📖 [Guide de débogage Backend](backend/DEBUG.md)
- 📖 [Guide de débogage Frontend](frontend/DEBUG.md)

## 📚 Documentation

- [CONTRIBUTING.md](CONTRIBUTING.md) - Guide pour les contributeurs
- [backend/ARCHITECTURE.md](backend/ARCHITECTURE.md) - Architecture détaillée du backend
- [frontend/ARCHITECTURE.md](frontend/ARCHITECTURE.md) - Architecture détaillée du frontend
