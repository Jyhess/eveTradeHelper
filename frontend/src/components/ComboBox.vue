<template>
  <div ref="comboBoxRef" class="combo-box">
    <input
      :id="inputId"
      ref="inputRef"
      v-model="searchText"
      type="text"
      class="combo-input"
      :placeholder="placeholder"
      :disabled="disabled"
      :class="{ 'has-value': modelValue !== null && modelValue !== '' }"
      @focus="handleFocus"
      @blur="handleBlur"
      @keydown="handleKeydown"
      @input="handleInput"
    />
    <div v-if="showDropdown && filteredOptions.length > 0" class="combo-dropdown">
      <div
        v-for="(option, index) in filteredOptions"
        :key="getOptionValue(option) || index"
        class="combo-option"
        :class="{ 'highlighted': index === highlightedIndex }"
        @mousedown.prevent="handleOptionMousedown(option)"
        @mouseenter="highlightedIndex = index"
      >
        {{ getOptionLabel(option) }}
      </div>
    </div>
    <div v-else-if="showDropdown && filteredOptions.length === 0 && searchText" class="combo-dropdown">
      <div class="combo-no-results">No results found</div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ComboBox',
  props: {
    modelValue: {
      type: [String, Number, null],
      default: null
    },
    options: {
      type: Array,
      required: true
    },
    placeholder: {
      type: String,
      default: 'Select an option...'
    },
    disabled: {
      type: Boolean,
      default: false
    },
    inputId: {
      type: String,
      default: ''
    },
    optionLabel: {
      type: String,
      default: 'label'
    },
    optionValue: {
      type: String,
      default: 'value'
    }
  },
  emits: ['update:modelValue', 'change', 'next'],
  expose: ['focus'],
  data() {
    return {
      searchText: '',
      showDropdown: false,
      highlightedIndex: -1,
      blurTimeout: null
    }
  },
  computed: {
    filteredOptions() {
      if (!this.options || this.options.length === 0) {
        return []
      }
      if (!this.searchText) {
        return this.options
      }
      const searchLower = this.searchText.toLowerCase()
      return this.options.filter(option => {
        if (!option) {
          return false
        }
        const label = this.getOptionLabel(option).toLowerCase()
        return label.includes(searchLower)
      })
    }
  },
  watch: {
    modelValue(newValue) {
      if (newValue !== null && newValue !== '') {
        const selectedOption = this.options.find(
          opt => this.getOptionValue(opt) === newValue
        )
        if (selectedOption) {
          this.searchText = this.getOptionLabel(selectedOption)
        }
      } else {
        this.searchText = ''
      }
    }
  },
  mounted() {
    this.updateSearchTextFromValue()
  },
  methods: {
    getOptionLabel(option) {
      if (!option) {
        return ''
      }
      if (typeof option === 'string') {
        return option
      }
      return option[this.optionLabel] || option.label || option.name || String(option)
    },
    getOptionValue(option) {
      if (!option) {
        return null
      }
      if (typeof option === 'string') {
        return option
      }
      return option[this.optionValue] || option.value || option.id || option
    },
    updateSearchTextFromValue() {
      if (this.modelValue !== null && this.modelValue !== '') {
        const selectedOption = this.options.find(
          opt => this.getOptionValue(opt) === this.modelValue
        )
        if (selectedOption) {
          this.searchText = this.getOptionLabel(selectedOption)
        }
      }
    },
    handleFocus() {
      if (this.blurTimeout) {
        // eslint-disable-next-line no-undef
        clearTimeout(this.blurTimeout)
        this.blurTimeout = null
      }
      this.showDropdown = true
      this.highlightedIndex = -1
      // Select all text on focus if there's a value
      if (this.searchText) {
        this.$nextTick(() => {
          if (this.$refs.inputRef) {
            this.$refs.inputRef.select()
          }
        })
      }
    },
    handleBlur() {
      // Delay hiding dropdown to allow click events
      // eslint-disable-next-line no-undef
      this.blurTimeout = setTimeout(() => {
        this.showDropdown = false
        this.highlightedIndex = -1
        this.updateSearchTextFromValue()
      }, 200)
    },
    handleInput() {
      this.showDropdown = true
      this.highlightedIndex = -1
    },
    handleKeydown(event) {
      if (this.disabled) return

      switch (event.key) {
        case 'ArrowDown':
          event.preventDefault()
          if (!this.showDropdown) {
            this.showDropdown = true
          }
          if (this.filteredOptions.length === 0) {
            this.highlightedIndex = -1
          } else if (this.highlightedIndex < this.filteredOptions.length - 1) {
            this.highlightedIndex++
          } else {
            this.highlightedIndex = 0
          }
          break

        case 'ArrowUp':
          event.preventDefault()
          if (!this.showDropdown) {
            this.showDropdown = true
          }
          if (this.filteredOptions.length === 0) {
            this.highlightedIndex = -1
          } else if (this.highlightedIndex > 0) {
            this.highlightedIndex--
          } else {
            this.highlightedIndex = this.filteredOptions.length - 1
          }
          break

        case 'Enter':
          event.preventDefault()
          if (this.showDropdown && this.highlightedIndex >= 0 && this.highlightedIndex < this.filteredOptions.length) {
            const option = this.filteredOptions[this.highlightedIndex]
            if (option) {
              const value = this.getOptionValue(option)
              const isSameValue = this.modelValue === value
              this.selectOption(option)
              // Only move to next if a different value was selected
              if (!isSameValue) {
                // Remove focus immediately
                if (this.$refs.inputRef) {
                  this.$refs.inputRef.blur()
                }
                // Emit next event - the parent will handle focusing the next element
                // For region/constellation changes, the focus will be handled after async loading
                this.$emit('next')
              }
            }
          } else if (this.filteredOptions.length === 1) {
            // If only one option matches, select it
            const option = this.filteredOptions[0]
            if (option) {
              const value = this.getOptionValue(option)
              const isSameValue = this.modelValue === value
              this.selectOption(option)
              // Only move to next if a different value was selected
              if (!isSameValue) {
                // Remove focus immediately
                if (this.$refs.inputRef) {
                  this.$refs.inputRef.blur()
                }
                // Emit next event - the parent will handle focusing the next element
                // For region/constellation changes, the focus will be handled after async loading
                this.$emit('next')
              }
            }
          }
          break

        case 'Escape':
          event.preventDefault()
          this.showDropdown = false
          this.highlightedIndex = -1
          this.updateSearchTextFromValue()
          this.$refs.inputRef?.blur()
          break

        case 'Tab':
          if (this.showDropdown && this.highlightedIndex >= 0 && this.highlightedIndex < this.filteredOptions.length) {
            event.preventDefault()
            const option = this.filteredOptions[this.highlightedIndex]
            if (option) {
              this.selectOption(option)
            }
          }
          break
      }
    },
    handleOptionMousedown(option) {
      // Prevent default to avoid input losing focus before selection
      if (!option) {
        return
      }
      const value = this.getOptionValue(option)
      const isSameValue = this.modelValue === value
      this.selectOption(option)
      // Only move to next if a different value was selected
      if (!isSameValue) {
        // Remove focus immediately
        if (this.$refs.inputRef) {
          this.$refs.inputRef.blur()
        }
        // Emit next event - the parent will handle focusing the next element
        // For region/constellation changes, the focus will be handled after async loading
        this.$emit('next')
      }
    },
    selectOption(option) {
      if (!option) {
        return
      }
      const value = this.getOptionValue(option)
      const label = this.getOptionLabel(option)

      this.searchText = label
      this.showDropdown = false
      this.highlightedIndex = -1

      this.$emit('update:modelValue', value)
      this.$emit('change', value, option)
    },
    focus() {
      this.$refs.inputRef?.focus()
    }
  }
}
</script>

<style scoped>
.combo-box {
  position: relative;
  width: 100%;
}

.combo-input {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 1em;
  background: white;
  cursor: text;
}

.combo-input:hover {
  border-color: #667eea;
}

.combo-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.combo-input:disabled {
  background: #f5f5f5;
  cursor: not-allowed;
}

.combo-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  margin-top: 4px;
  background: white;
  border: 1px solid #ddd;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  max-height: 300px;
  overflow-y: auto;
  z-index: 1000;
}

.combo-option {
  padding: 10px 15px;
  cursor: pointer;
  transition: background 0.2s;
}

.combo-option:hover,
.combo-option.highlighted {
  background: #f0f0f0;
}

.combo-option:first-child {
  border-top-left-radius: 6px;
  border-top-right-radius: 6px;
}

.combo-option:last-child {
  border-bottom-left-radius: 6px;
  border-bottom-right-radius: 6px;
}

.combo-no-results {
  padding: 15px;
  text-align: center;
  color: #999;
  font-style: italic;
}
</style>

