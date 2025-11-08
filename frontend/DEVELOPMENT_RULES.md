# DEVELOPMENT RULES - TO BE SYSTEMATICALLY FOLLOWED

⚠️ **IMPORTANT**: These rules are MANDATORY. The AI must ALWAYS respect them when making any code modifications.

## Test-Driven Development (TDD)

**ALL** code modifications on the frontend must follow the TDD Red-Green-Refactor cycle:

### 1. 🔴 RED - Write the failing test

**MANDATORY STEP**: Write the test BEFORE implementing the feature.

- The test must fail for the right reason (no missing imports, etc.)
- The test must be specific and test one thing
- **DO NOT** implement code without writing the test first

### 2. 🟢 GREEN - Implement the minimum to make the test pass

**MANDATORY STEP**: Implement only the minimum necessary.

- Implement only what is necessary for the test to pass
- **DO NOT** add additional features
- Code can be "dirty" as long as the test passes

### 3. 🔵 REFACTOR - Improve the code

**MANDATORY STEP**: Refactor after the test passes.

- Once the test is green, refactor the code
- Improve readability, performance, maintainability
- Ensure all tests still pass after refactoring
- Apply all clean code rules below

## Project-specific rules

### Language

**ABSOLUTE RULE**: **ALWAYS** write in English.

**MANDATORY ACTION**:

- All code, comments, JSDoc, documentation, and messages must be in English
- Variable names, function names, component names must be in English
- Error messages, log messages, and user-facing text must be in English
- Documentation files (README, ARCHITECTURE, etc.) must be in English
- Test names and test descriptions must be in English

**VIOLATION EXAMPLE**:

```javascript
// ❌ BAD
function calculerTotal() {
  // Récupérer les données
  return items.reduce((sum, item) => sum + item.prix, 0)
}

// ✅ GOOD
function calculateTotal() {
  // Retrieve data
  return items.reduce((sum, item) => sum + item.price, 0)
}
```

### Tests

- Unit tests use Jest/Vitest with Vue Test Utils
- Component tests should test behavior, not implementation details
- Use `@vue/test-utils` for component testing
- Mock API calls in unit tests
- Integration tests can use real API calls (if needed)
- Use `describe` and `it` blocks for test organization
- Use descriptive test names that explain what is being tested

### Code

- Use ES6+ features (const/let, arrow functions, destructuring, etc.)
- Use explicit variable and function names
- Prefer composition over inheritance
- Use Vue 3 Composition API when appropriate (for complex components)

## CLEAN CODE RULES - TO BE SYSTEMATICALLY APPLIED

**ALL** code modifications must respect the following clean code principles. The AI must verify each rule before proposing code.

### 1. Elimination of magic numbers and strings

**ABSOLUTE RULE**: **NEVER** use magic numbers or strings directly in code.

**MANDATORY ACTION**:

- Create named constants in `src/constants.js`
- Examples: `API_TIMEOUT = 10000`, `DEFAULT_PAGE_SIZE = 50`, `ROUTES = { REGIONS: '/regions' }`
- Constants must be explicit and documented
- Use constants for API endpoints, timeouts, default values, etc.

**VIOLATION EXAMPLE**:

```javascript
// ❌ BAD
setTimeout(() => {
  // ...
}, 5000)

// ✅ GOOD
import { DEBOUNCE_DELAY_MS } from '@/constants'
setTimeout(() => {
  // ...
}, DEBOUNCE_DELAY_MS)
```

### 2. Small Functions and Components

**ABSOLUTE RULE**: A function or component must do **one thing** (Single Responsibility Principle).

**MANDATORY ACTION**:

- If a function exceeds 50 lines, **DIVIDE IT** into sub-functions
- If a component exceeds 200 lines, **DIVIDE IT** into smaller components
- Functions and components must be individually testable
- Prefer several small functions/components over one large one
- Extract computed properties and methods when logic becomes complex

**VIOLATION EXAMPLE**:

```javascript
// ❌ BAD: 60-line function
function processData(data) {
  // 60 lines of code...
}

// ✅ GOOD: divided into sub-functions
function processData(data) {
  const validated = validateData(data)
  const cleaned = cleanData(validated)
  return transformData(cleaned)
}
```

### 3. Meaningful Names

- Variable, function, and component names must be **self-explanatory**
- Avoid abbreviations unless they are universal (e.g., `id`, `api`, `url`)
- Use verbs for functions: `calculateTotal()`, `fetchRegions()`, `formatDate()`
- Use nouns for components: `RegionCard`, `NavigationBar`, `LoadingSpinner`
- Use domain business names when appropriate
- Use camelCase for variables and functions
- Use PascalCase for components

### 4. DRY (Don't Repeat Yourself)

**ABSOLUTE RULE**: **NEVER** duplicate code.

**MANDATORY ACTION**:

- Extract common logic into utility functions
- Create helpers in `src/utils/` when necessary
- Reuse existing functions rather than rewriting logic
- If code is repeated 2 times or more, extract it into a function
- Create reusable components for repeated UI patterns
- Use mixins or composables (Vue 3) for shared component logic

### 4.1. Prefer named functions over comments

- **NEVER** use a comment to explain what a complex line of code does
- Extract logic into an explicit named function
- Example: replace `// Filter valid results` + `const valid = results.filter(r => r && r.isValid)` with `const valid = filterValidResults(results)`
- Named functions are self-documented and reusable
- If a line of code requires a comment, it's a sign it should be extracted into a function

### 5. Single Responsibility Principle (SRP)

- Each component/function must have **one reason to change**
- Separate concerns: data fetching, formatting, rendering, etc.
- Extract complex logic into computed properties or methods
- Use composables (Vue 3) or mixins to share behavior

### 6. Component Structure

**MANDATORY ACTION**:

- Follow Vue component structure: `<template>`, `<script>`, `<style>`
- Organize script section: props, data, computed, methods, lifecycle hooks
- Use single-file components (`.vue` files)
- Keep template logic minimal - move complex logic to computed properties or methods
- Use scoped styles when possible to avoid style conflicts

**COMPONENT STRUCTURE EXAMPLE**:

```vue
<template>
  <!-- Template content -->
</template>

<script>
export default {
  name: 'ComponentName',
  props: {
    // Props definition
  },
  data() {
    return {
      // Local state
    }
  },
  computed: {
    // Computed properties
  },
  methods: {
    // Methods
  },
  mounted() {
    // Lifecycle hooks
  }
}
</script>

<style scoped>
/* Component styles */
</style>
```

### 7. Documentation and Expressiveness

- Add **JSDoc** comments only when necessary:
  - **ALWAYS** for public API functions in services
  - **AVOID** redundant JSDoc in components if the name and parameters are clear
- Use comments to explain the **why**, not the **how**
- Code must be self-documented through good naming
- A JSDoc comment is useless if it simply repeats the function name and its parameters
- Document complex business logic or non-obvious decisions

**JSDOC EXAMPLE**:

```javascript
/**
 * Fetches regions from the API with optional filtering
 * @param {Object} filters - Filter options (limit, search, etc.)
 * @returns {Promise<Array>} Array of region objects
 * @throws {Error} If API request fails
 */
async function fetchRegions(filters = {}) {
  // Implementation
}
```

### 8. Separation of Concerns

- Separate constants in `src/constants.js`
- Separate utilities in `src/utils/` when module-specific
- Business logic must be in services (`src/services/`), not in components
- Components should focus on presentation and user interaction
- API calls must be in services, not in components
- Each module must have a clear responsibility

### 9. Appropriate Abstraction

- Use the **right level of abstraction** for each function
- Create reusable utility functions instead of inline logic
- Avoid mixed abstraction levels in the same function
- Use composables (Vue 3) for shared reactive logic

### 10. Maintainability

- Code must be **easy to modify** without breaking other parts
- Centralize constants to facilitate changes
- Structure code in a modular way
- Prefer composition over duplication
- Use Vue Router for navigation, not manual URL manipulation

### 11. Import Management

**ABSOLUTE RULE**: **NEVER** import inside functions or conditionally.

**MANDATORY ACTION**:

- All imports must be **AT THE TOP OF THE FILE** only
- Group imports: standard library, third-party, local
- Use absolute imports with `@/` alias for `src/` directory
- Use relative imports only for same-directory files

**VIOLATION EXAMPLE**:

```javascript
// ❌ BAD
export default {
  methods: {
    async fetchData() {
      const api = await import('@/services/api') // ❌ Import inside function
      return api.regions.getRegions()
    }
  }
}

// ✅ GOOD
import api from '@/services/api' // ✅ Import at top of file

export default {
  methods: {
    async fetchData() {
      return api.regions.getRegions()
    }
  }
}
```

### 12. Error Handling

- Avoid generic `catch (error)` when possible
- Log errors with appropriate context
- Use specific error handling for different error types
- Do not hide errors without logging them
- Display user-friendly error messages
- Use try-catch blocks for async operations

**ERROR HANDLING EXAMPLE**:

```javascript
// ❌ BAD
async fetchRegions() {
  try {
    const data = await api.regions.getRegions()
    this.regions = data.regions
  } catch (error) {
    // Generic error handling
  }
}

// ✅ GOOD
async fetchRegions() {
  try {
    const data = await api.regions.getRegions()
    this.regions = data.regions || []
  } catch (error) {
    console.error('Error retrieving regions:', error)
    this.error = error.response?.data?.detail || error.message || 'An error occurred'
    // Show user-friendly error message
  }
}
```

### 13. Vue-Specific Best Practices

**MANDATORY ACTION**:

- Use `v-if` for conditional rendering (not `v-show` unless performance is critical)
- Use `:key` for `v-for` loops with unique identifiers
- Use computed properties for derived state (not methods)
- Use methods for event handlers and actions
- Avoid direct DOM manipulation - use Vue's reactivity system
- Use props for parent-to-child communication
- Use events (`$emit`) for child-to-parent communication
- Use Vuex/Pinia or provide/inject for global state (if needed)
- Use `scoped` styles to avoid CSS conflicts
- Prefer template refs over direct DOM queries

**VIOLATION EXAMPLE**:

```vue
<!-- ❌ BAD -->
<template>
  <div v-for="item in items">
    {{ item.name }}
  </div>
</template>

<!-- ✅ GOOD -->
<template>
  <div v-for="item in items" :key="item.id">
    {{ item.name }}
  </div>
</template>
```

### 14. API Service Pattern

**MANDATORY ACTION**:

- All API calls must go through services in `src/services/`
- Services must handle errors and transform data
- Components must not contain API logic
- Use async/await for asynchronous operations
- Handle loading and error states in components

**SERVICE EXAMPLE**:

```javascript
// src/services/api.js
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

### 15. State Management

- Use component local state (`data()`) for component-specific state
- Use Vuex/Pinia for global application state (if needed)
- Avoid prop drilling - use provide/inject or state management
- Keep state as close to where it's used as possible

## MANDATORY CHECKLIST BEFORE ANY CODE MODIFICATION

**THE AI MUST verify this checklist before proposing code**:

- [ ] **TDD respected**: Test written BEFORE implementation (RED → GREEN → REFACTOR)
- [ ] **No magic numbers/strings**: Use constants from `src/constants.js`
- [ ] **Small functions/components**: No function exceeds 50 lines, no component exceeds 200 lines
- [ ] **Explicit names**: Self-explanatory variables, functions, and components
- [ ] **No duplication**: Code reused via helper functions or components
- [ ] **Named functions**: No explanatory comments, extract into functions
- [ ] **SRP respected**: Single responsibility per function/component
- [ ] **Component structure**: Proper Vue component organization
- [ ] **JSDoc**: Only in services (public APIs) and if really necessary
- [ ] **Imports at top**: All imports at top of file only
- [ ] **Business logic**: In services, not in components
- [ ] **Error handling**: Specific error handling, no generic catch
- [ ] **Vue best practices**: Proper use of v-if, :key, computed, methods, etc.
- [ ] **API calls**: Through services only, not in components
- [ ] **English language**: All code, comments, JSDoc, and documentation in English
- [ ] **ESLint/Prettier**: Code formatted according to project standards

## INSTRUCTIONS FOR THE AI

**BEFORE proposing code, THE AI MUST**:

1. **Read this complete checklist**
2. **Verify each point** before generating code
3. **Systematically apply** all rules
4. **Write everything in English** (code, comments, JSDoc, documentation)
5. **Refuse** to generate code that violates these rules
6. **Propose corrections** if existing code violates the rules

**AFTER modifying code in the frontend, THE AI MUST**:

1. **Automatically execute ESLint/Prettier** on all modified JavaScript/Vue files
2. **Command to execute**: `npm run lint -- --fix <file1> <file2> ...` for each modified file in `frontend/src/`
3. **Verify** that formatting is applied before finalizing modifications
4. **Never** propose code not formatted according to project standards

**If the user requests something that violates these rules, THE AI MUST**:

- Explain why the request violates the rules
- Propose an alternative that complies with the rules
- Not generate non-compliant code

## File Organization

```
frontend/src/
├── components/          # Reusable Vue components
│   ├── Navigation.vue
│   ├── Breadcrumb.vue
│   └── ...
├── views/              # Page-level components (routes)
│   ├── Regions.vue
│   ├── Deals.vue
│   └── ...
├── services/           # API services and business logic
│   └── api.js
├── utils/             # Utility functions
│   └── eventBus.js
├── constants.js       # Application constants
├── router/            # Vue Router configuration
│   └── index.js
└── main.js            # Application entry point
```

## Testing Structure

```
frontend/tests/
├── unit/              # Unit tests for components and utilities
│   ├── components/
│   ├── services/
│   └── utils/
└── integration/       # Integration tests (if needed)
```

## References

- [Vue.js Style Guide](https://vuejs.org/style-guide/)
- [Vue Test Utils](https://test-utils.vuejs.org/)
- [Clean Code JavaScript](https://github.com/ryanmcdermott/clean-code-javascript)
- [JavaScript Best Practices](https://www.w3schools.com/js/js_best_practices.asp)
