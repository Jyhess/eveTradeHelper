# Architecture du Frontend

Ce document décrit l'architecture détaillée du frontend Vue.js.

## Vue d'ensemble

Le frontend est une application Vue.js 3 avec Vue Router pour la navigation.

## Structure des modules

### Organisation des fichiers

```
frontend/
├── src/
│   ├── main.js              # Point d'entrée de l'application
│   ├── App.vue              # Composant racine
│   ├── components/          # Composants réutilisables
│   │   ├── Breadcrumb.vue
│   │   ├── Navigation.vue
│   │   ├── TreeNode.vue
│   │   ├── TreeSelect.vue
│   │   └── TreeSelectNode.vue
│   ├── views/               # Pages/Vues
│   │   ├── Regions.vue
│   │   ├── Constellations.vue
│   │   ├── Systems.vue
│   │   ├── SystemDetail.vue
│   │   ├── Market.vue
│   │   └── Deals.vue
│   ├── router/              # Configuration du routeur
│   │   └── index.js
│   ├── services/            # Services API
│   │   └── api.js
│   └── utils/               # Utilitaires
│       └── eventBus.js
├── public/
│   └── index.html           # Template HTML
└── vue.config.js            # Configuration Vue.js
```

## Composants principaux

### App.vue

Composant racine de l'application qui contient :
- La navigation principale
- Le router-view pour afficher les pages
- Le breadcrumb pour la navigation hiérarchique

### Composants réutilisables

#### Navigation.vue
Barre de navigation principale avec les liens vers les différentes sections.

#### Breadcrumb.vue
Fil d'Ariane pour la navigation hiérarchique (Régions > Constellations > Systèmes).

#### TreeNode.vue
Composant pour afficher un arbre de données (régions, constellations, systèmes).

#### TreeSelect.vue / TreeSelectNode.vue
Composants pour un sélecteur d'arbre interactif.

### Vues (Pages)

#### Regions.vue
Affiche la liste des régions avec leurs détails.

#### Constellations.vue
Affiche les constellations d'une région sélectionnée.

#### Systems.vue
Affiche les systèmes d'une constellation sélectionnée.

#### SystemDetail.vue
Affiche les détails d'un système (connexions, stations, etc.).

#### Market.vue
Affiche les informations de marché (catégories, groupes, types).

#### Deals.vue
Affiche les opportunités de trading (deals).

## Services

### api.js

Service centralisé pour les appels API vers le backend :

```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:5001',
  timeout: 10000
});

export default {
  getRegions() {
    return api.get('/api/v1/regions');
  },
  // ... autres méthodes
};
```

## Router

### Configuration du router

Le router est configuré dans `src/router/index.js` avec les routes suivantes :

- `/` - Page d'accueil (redirige vers `/regions`)
- `/regions` - Liste des régions
- `/regions/:regionId/constellations` - Constellations d'une région
- `/constellations/:constellationId/systems` - Systèmes d'une constellation
- `/systems/:systemId` - Détails d'un système
- `/market` - Informations de marché
- `/deals` - Opportunités de trading

## Communication avec le backend

### Configuration CORS

Le backend doit être configuré pour accepter les requêtes depuis le frontend. La configuration CORS est gérée dans le backend FastAPI.

### Base URL

Par défaut, le frontend fait des requêtes vers `http://localhost:5001`. Cette URL peut être configurée via les variables d'environnement.

## État de l'application

L'application utilise principalement l'état local des composants. Pour la communication entre composants non liés, un EventBus est utilisé (`utils/eventBus.js`).

## Build et déploiement

### Mode développement

```bash
npm run serve
```

Lance le serveur de développement avec hot-reload.

### Mode production

```bash
npm run build
```

Génère les fichiers statiques dans `dist/` qui peuvent être servis par un serveur web statique ou intégrés dans le backend.

## Configuration

### vue.config.js

Configuration Vue.js incluant :
- Source maps pour le débogage
- Configuration du proxy (si nécessaire)
- Options de build

## Évolutions futures

Cette architecture permet facilement :

- Ajout de nouvelles vues/pages
- Ajout de nouveaux composants réutilisables
- Intégration d'un state management (Vuex/Pinia) si nécessaire
- Ajout de nouvelles routes
- Amélioration de la gestion d'état globale

