# Frontend Tests

This directory contains tests for the frontend application.

## Test Structure

```
tests/
├── unit/              # Unit tests
│   ├── components/    # Component tests
│   ├── services/      # Service tests
│   └── utils/         # Utility function tests
└── integration/       # Integration tests (if needed)
```

## Running Tests

```bash
# Run all tests
npm test

# Run tests in watch mode
npm test:watch

# Run tests with coverage
npm test:coverage
```

## Test Guidelines

- Follow TDD principles: Write tests BEFORE implementation
- Test behavior, not implementation details
- Use descriptive test names
- Mock API calls in unit tests
- Keep tests isolated and independent
- Use `@vue/test-utils` for component testing

## Example Test Structure

```javascript
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import MyComponent from '@/components/MyComponent.vue'

describe('MyComponent', () => {
  it('should render correctly', () => {
    const wrapper = mount(MyComponent, {
      props: {
        // props
      }
    })
    expect(wrapper.text()).toContain('Expected text')
  })
})
```

