# Eve Trade Helper

Application web pour analyser les opportunités de trading dans EVE Online, avec backend Python (FastAPI) et frontend Vue.js, orchestrée avec Docker Compose.

## 🧪 Test-Driven Development (TDD)

Ce projet suit strictement la méthodologie **TDD** pour toutes les modifications de code. 

📖 **Consultez [TDD.md](TDD.md) pour le guide complet du processus TDD.**

**Cycle TDD** : 🔴 RED → 🟢 GREEN → 🔵 REFACTOR
1. Écrire le test qui échoue
2. Implémenter le minimum pour faire passer le test
3. Refactoriser le code

## Structure du projet

```
.
├── backend/
│   ├── app.py              # Application Flask (utilisée pour debug et production)
│   ├── requirements.txt    # Dépendances Python
│   └── Dockerfile          # Image Docker pour le backend
├── frontend/
│   ├── public/
│   │   └── index.html      # Template HTML
│   ├── src/
│   │   ├── App.vue         # Composant principal Vue.js
│   │   └── main.js         # Point d'entrée Vue.js
│   ├── package.json        # Dépendances Node.js
│   ├── vue.config.js       # Configuration Vue.js
│   └── Dockerfile          # Image Docker pour le frontend
├── .vscode/
│   ├── launch.json         # Configurations de debug pour Cursor/VS Code
│   ├── tasks.json          # Tâches (démarrage serveur Vue.js, etc.)
│   ├── settings.json       # Paramètres du workspace
│   └── extensions.json     # Extensions recommandées
├── backend/
│   ├── tests/              # Tests d'intégration
│   │   ├── reference/      # Données de référence pour comparaison
│   │   └── test_*.py       # Fichiers de tests
│   └── ...
├── .venv/                  # Environnement virtuel Python (créé localement)
├── setup_env.bat           # Script de configuration automatique (Windows)
├── setup_env.sh            # Script de configuration automatique (Linux/Mac)
├── .gitignore              # Fichiers à ignorer par Git
├── docker-compose.yml      # Configuration Docker Compose
└── README.md               # Ce fichier
```

## Démarrage

### Mode production avec Docker

1. **Démarrer les services** :

   ```bash
   docker-compose up --build
   ```

2. **Accéder à l'application** :
   - Frontend : http://localhost:8080
   - Backend API : http://localhost:5000/api/hello

### Mode développement avec debug (Cursor/VS Code)

#### Prérequis

1. **Installer les extensions recommandées** :

   - Python (ms-python.python)
   - Debugpy (ms-python.debugpy)
   - Vue Language Features (Vue.volar)
   - Prettier (esbenp.prettier-vscode)

   Les extensions sont listées dans `.vscode/extensions.json` et Cursor vous proposera de les installer automatiquement.

2. **Configurer l'environnement** (méthode automatique) :

   ```bash
   # Windows
   setup_env.bat

   # Linux/Mac
   chmod +x setup_env.sh
   ./setup_env.sh
   ```

   Ou **méthode manuelle** :

   ```bash
   # Créer et activer l'environnement virtuel Python
   # Windows
   python -m venv .venv
   .venv\Scripts\activate

   # Linux/Mac
   python3 -m venv .venv
   source .venv/bin/activate

   # Installer les dépendances
   # Backend (dans le venv activé)
   pip install -r backend/requirements.txt

   # Frontend
   cd frontend
   npm install
   cd ..
   ```

   **Note** : Cursor/VS Code détectera automatiquement l'environnement virtuel dans `.venv`. Assurez-vous que l'interpréteur Python sélectionné pointe vers `.venv/Scripts/python.exe` (Windows) ou `.venv/bin/python` (Linux/Mac).

#### Debug du Backend Python

1. **Ouvrir le panneau de debug** : `Ctrl+Shift+D` (ou `Cmd+Shift+D` sur Mac)
2. **Sélectionner la configuration** : "Python: Flask (Backend)"
3. **Appuyer sur F5** ou cliquer sur le bouton "Start Debugging"
4. Le serveur Flask démarre sur `http://localhost:5000` avec le débogueur actif
5. **Placer des breakpoints** dans `backend/app.py`

**Configurations disponibles** :

- `Python: Flask (Backend)` - Lance Flask avec debugpy intégré automatiquement
- `Python: Flask (Attach)` - Se connecte à un processus Flask déjà en cours (nécessite debugpy.listen() dans le code)

#### Debug du Frontend Vue.js

1. **Ouvrir le panneau de debug** : `Ctrl+Shift+D`
2. **Sélectionner la configuration** : "Vue.js: Chrome" ou "Vue.js: Edge"
3. **Appuyer sur F5** :
   - Le serveur de développement Vue.js (`npm run serve`) démarre automatiquement
   - Un navigateur s'ouvre avec le débogueur connecté une fois le serveur prêt
4. **Placer des breakpoints** dans vos fichiers `.vue` ou `.js`

**Note** :

- Le serveur Vue.js est lancé automatiquement via la tâche `preLaunchTask`
- Les source maps sont activées dans `vue.config.js` pour permettre le debug des fichiers source

#### Debug complet (Backend + Frontend simultanément)

1. **Ouvrir le panneau de debug**
2. **Sélectionner la configuration compound** : "Full Stack Debug"
3. **Appuyer sur F5**
4. Les deux débogueurs démarrent simultanément

## Commandes utiles

### Docker

- Démarrer en arrière-plan : `docker-compose up -d`
- Arrêter les services : `docker-compose down`
- Voir les logs : `docker-compose logs -f`
- Reconstruire les images : `docker-compose build --no-cache`

### Développement local

- **Activer l'environnement virtuel** :

  ```bash
  # Windows
  .venv\Scripts\activate

  # Linux/Mac
  source .venv/bin/activate
  ```

- Démarrer le backend : `python backend/app.py`
- Démarrer le frontend : `cd frontend && npm run serve`
- Build de production frontend : `cd frontend && npm run build`
- Désactiver le venv : `deactivate`

### Tests

Les tests d'intégration comparent les réponses de l'API ESI avec des données de référence.

```bash
# Installer les dépendances de test (si pas déjà fait)
pip install pytest pytest-cov

# Exécuter tous les tests
pytest backend/tests/

# Exécuter avec détails
pytest backend/tests/ -v

# Exécuter un fichier spécifique
pytest backend/tests/test_eve_api_client.py

# Générer un rapport de couverture
pytest backend/tests/ --cov=backend --cov-report=html
```

**Note** : Lors du premier lancement, les tests vont créer des fichiers de référence dans `backend/tests/reference/`. Ces fichiers seront utilisés pour comparer les résultats lors des exécutions suivantes.

## API Endpoints

### Régions

- `GET /api/v1/regions` : Liste toutes les régions avec leurs détails
- `GET /api/v1/regions/<region_id>/constellations` : Liste toutes les constellations d'une région avec leurs détails
- `GET /api/v1/constellations/<constellation_id>/systems` : Liste tous les systèmes d'une constellation avec leurs détails
- `GET /api/v1/systems/<system_id>/connections` : Liste tous les systèmes connectés à un système donné via les stargates

Exemple :
```bash
# Récupérer toutes les régions
curl http://localhost:5000/api/v1/regions

# Récupérer les constellations de la région 10000002 (The Forge)
curl http://localhost:5000/api/v1/regions/10000002/constellations

# Récupérer les systèmes d'une constellation (ex: 20000001)
curl http://localhost:5000/api/v1/constellations/20000001/systems

# Récupérer les systèmes connectés à un système (ex: 30000001 - Jita)
curl http://localhost:5000/api/v1/systems/30000001/connections
```

## Débogage

### Points d'arrêt (Breakpoints)

- **Backend Python** : Placez des breakpoints dans `backend/app.py`
- **Frontend Vue.js** : Placez des breakpoints dans `frontend/src/App.vue` ou `frontend/src/main.js`

### Variables et inspecteur

Une fois un point d'arrêt atteint, vous pouvez :

- Inspecter les variables dans le panneau "Variables"
- Évaluer des expressions dans la console de debug
- Naviguer dans la pile d'appels (Call Stack)
- Exécuter le code pas à pas (F10, F11, Shift+F11)

### Résolution de problèmes

- **Erreur "Port 5678 déjà utilisé" (WinError 10048)** :

  - **Solution 1** : Arrêter les processus utilisant le port :

    ```bash
    # Trouver le processus
    netstat -ano | findstr :5678

    # Tuer le processus (remplacer <PID> par l'ID trouvé)
    taskkill /PID <PID> /F
    ```

    Ou utilisez le script `kill_debug_port.bat`

  - **Solution 2** : Utiliser un port alternatif :

    - Dans Cursor, sélectionnez la configuration "Python: Flask (Backend - Port Alternatif)" qui utilise le port 5679
    - Ou définissez `DEBUGPY_PORT=5679` dans les variables d'environnement

  - **Solution 3** : Fermer toutes les sessions de debug précédentes dans Cursor/VS Code

- **Le débogueur Python ne se connecte pas** : Vérifiez que le port de debug n'est pas utilisé
- **Les breakpoints Vue.js ne fonctionnent pas** : Vérifiez que les source maps sont générées (`vue.config.js`)
- **Le frontend ne peut pas appeler le backend** : Vérifiez que les deux services sont démarrés et que CORS est activé
