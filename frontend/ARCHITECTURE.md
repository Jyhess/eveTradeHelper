# Frontend Architecture

This document describes the detailed Vue.js frontend architecture.

## Overview

The frontend is a Vue.js 3 application with Vue Router for navigation.

## Module Structure

## Main Components

### App.vue

Root component of the application containing:

- Main navigation
- Router-view to display pages
- Breadcrumb for hierarchical navigation

### Reusable Components

#### Navigation.vue

Main navigation bar with links to different sections.

#### Breadcrumb.vue

Breadcrumb trail for hierarchical navigation (Regions > Constellations > Systems).

#### TreeNode.vue

Component to display a data tree (regions, constellations, systems).

#### TreeSelect.vue / TreeSelectNode.vue

Components for an interactive tree selector.

### Views (Pages)

#### Regions.vue

Displays the list of regions with their details.

#### Constellations.vue

Displays constellations of a selected region.

#### Systems.vue

Displays systems of a selected constellation.

#### SystemDetail.vue

Displays details of a system (connections, stations, etc.).

#### Market.vue

Displays market information (categories, groups, types).

#### Deals.vue

Displays trading opportunities (deals).

## Services

### api.js

Centralized service for API calls to the backend:

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
  // ... other methods
};
```

## Router

### Router Configuration

The router is configured in `src/router/index.js` with the following routes:

- `/` - Home page (redirects to `/regions`)
- `/regions` - List of regions
- `/regions/:regionId/constellations` - Constellations of a region
- `/constellations/:constellationId/systems` - Systems of a constellation
- `/systems/:systemId` - System details
- `/market` - Market information
- `/deals` - Trading opportunities

## Backend Communication

### CORS Configuration

The backend must be configured to accept requests from the frontend. CORS configuration is handled in the FastAPI backend.

### Base URL

By default, the frontend makes requests to `http://localhost:5001`. This URL can be configured via environment variables.

## Application State

The application mainly uses local component state. For communication between unrelated components, an EventBus is used (`utils/eventBus.js`).

## Build and Deployment

### Development Mode

```bash
npm run dev
```

Launches the development server with hot-reload.

### Production Mode

```bash
npm run build
```

Generates static files in `dist/` that can be served by a static web server or integrated into the backend.

## Configuration

### vue.config.js

Vue.js configuration including:

- Source maps for debugging
- Proxy configuration (if necessary)
- Build options

## Future Evolutions

This architecture easily allows:

- Adding new views/pages
- Adding new reusable components
- Integrating state management (Vuex/Pinia) if necessary
- Adding new routes
- Improving global state management
