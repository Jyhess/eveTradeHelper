# Hello World - Vue.js + Python

Application web simple avec backend Python (Flask) et frontend Vue.js, orchestrée avec Docker Compose.

## Structure du projet

```
.
├── backend/
│   ├── app.py              # Application Flask
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
├── docker-compose.yml      # Configuration Docker Compose
└── README.md               # Ce fichier
```

## Démarrage

1. **Démarrer les services** :
   ```bash
   docker-compose up --build
   ```

2. **Accéder à l'application** :
   - Frontend : http://localhost:8080
   - Backend API : http://localhost:5000/api/hello

## Commandes utiles

- Démarrer en arrière-plan : `docker-compose up -d`
- Arrêter les services : `docker-compose down`
- Voir les logs : `docker-compose logs -f`
- Reconstruire les images : `docker-compose build --no-cache`

