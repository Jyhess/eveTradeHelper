# Frontend Architecture

This document describes the detailed Vue.js frontend architecture.

## Overview

The frontend is a Vue.js 3 application with Vue Router for navigation, following clean code principles and best practices.

**Important**: All code modifications must follow the rules defined in [DEVELOPMENT_RULES.md](./DEVELOPMENT_RULES.md).

## Module Structure

The frontend follows a clear separation of concerns:

```
src/
├── components/          # Reusable Vue components
├── views/              # Page-level components (routes)
├── services/           # API services and business logic
├── utils/             # Utility functions
├── constants.js       # Application constants
├── router/            # Vue Router configuration
└── main.js            # Application entry point
```

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

Centralized service for API calls to the backend. All API calls must go through services, never directly from components.

The service uses constants from `constants.js` for configuration:

```javascript
import axios from 'axios'
import { API_BASE_URL, API_TIMEOUT_MS } from '@/constants'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT_MS,
  headers: {
    'Content-Type': 'application/json'
  }
})

export const regionsApi = {
  async getRegions() {
    try {
      const response = await apiClient.get('/regions')
      return response.data
    } catch (error) {
      console.error('Error retrieving regions:', error)
      throw new Error(extractErrorMessage(error))
    }
  }
}
```

**Principles**:

- All API calls must be in services
- Services handle errors and transform data
- Components must not contain API logic
- Use async/await for asynchronous operations

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

The API base URL is configured in `src/constants.js` and can be overridden via environment variables (`VUE_APP_API_BASE_URL`).

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
- Path alias `@` for `src/` directory (e.g., `@/components/MyComponent.vue`)
- Proxy configuration (if necessary)
- Build options

### nginx.conf

Production nginx configuration following best practices:

**Security**:

- Security headers (X-Frame-Options, X-Content-Type-Options, X-XSS-Protection, Referrer-Policy)
- Hidden nginx version
- Denied access to hidden and backup files
- Optional Content Security Policy (CSP)
- Optional rate limiting

**Performance**:

- Gzip compression optimized for various file types
- Cache static assets (1 year) with immutable flag
- Cache HTML files (1 hour) with revalidation
- No cache for index.html to ensure updates
- Optimized timeouts and buffers

**SPA Routing**:

- Proper handling of Vue Router with `try_files`
- All routes serve `index.html` for client-side routing

**Monitoring**:

- Health check endpoint at `/health`
- Access and error logging configured

### Constants

All application constants are centralized in `src/constants.js`:

- API configuration (base URL, timeout)
- Default values (page size, debounce delay)
- Routes
- Error messages
- UI constants

**Rule**: Never use magic numbers or strings directly in code. Always use constants.

## Testing

Tests are organized in `tests/` directory:

```
tests/
├── unit/              # Unit tests
│   ├── components/    # Component tests
│   ├── services/      # Service tests
│   └── utils/         # Utility function tests
└── integration/       # Integration tests (if needed)
```

**Testing Principles**:

- Follow TDD: Write tests BEFORE implementation
- Test behavior, not implementation details
- Mock API calls in unit tests
- Use `@vue/test-utils` for component testing

See [tests/README.md](./tests/README.md) for more details.

## Code Quality

### Development Rules

All code must follow the rules defined in [DEVELOPMENT_RULES.md](./DEVELOPMENT_RULES.md):

- TDD (Test-Driven Development)
- No magic numbers/strings (use constants)
- Small functions and components
- Meaningful names
- DRY (Don't Repeat Yourself)
- Single Responsibility Principle
- Proper error handling
- Vue best practices

### Code Formatting

Code must be formatted according to project standards (ESLint/Prettier).

## Future Evolutions

This architecture easily allows:

- Adding new views/pages
- Adding new reusable components
- Integrating state management (Vuex/Pinia) if necessary
- Adding new routes
- Improving global state management
- Adding new services
- Extending test coverage
