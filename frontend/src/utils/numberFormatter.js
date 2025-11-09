/**
 * Gets the browser locale, falling back to 'en-US' if not available
 * @returns {string} Browser locale string
 */
function getBrowserLocale() {
  // eslint-disable-next-line no-undef
  if (typeof navigator !== 'undefined' && navigator.language) {
    // eslint-disable-next-line no-undef
    return navigator.language
  }
  return 'en-US'
}

/**
 * Formats a price value using browser locale
 * @param {number|null|undefined} price - The price to format
 * @returns {string} Formatted price string or 'N/A' for invalid values
 */
export function formatPrice(price) {
  if (!price && price !== 0) return 'N/A'
  if (price >= 1000) {
    // Replace narrow no-break space (U+202F) with standard non-breaking space (U+00A0) for visibility
    return Math.round(price)
      .toLocaleString(getBrowserLocale())
      .replace(/\u202F/g, '\u00A0')
  }
  return price.toFixed(2)
}

/**
 * Formats a volume value using browser locale
 * @param {number|null|undefined} volume - The volume to format
 * @returns {string} Formatted volume string or 'N/A' for invalid values
 */
export function formatVolume(volume) {
  if (!volume && volume !== 0) return 'N/A'
  // Format with 2 decimals for small volumes, rounded for large ones
  if (volume >= 1000) {
    // Replace narrow no-break space (U+202F) with standard non-breaking space (U+00A0) for visibility
    return Math.round(volume)
      .toLocaleString(getBrowserLocale())
      .replace(/\u202F/g, '\u00A0')
  }
  return volume.toFixed(2)
}

/**
 * Formats a number using browser locale
 * @param {number|null|undefined} number - The number to format
 * @returns {string} Formatted number string or 'N/A' for invalid values
 */
export function formatNumber(number) {
  if (number === null || number === undefined) return 'N/A'
  // Replace narrow no-break space (U+202F) with standard non-breaking space (U+00A0) for visibility
  return number.toLocaleString(getBrowserLocale()).replace(/\u202F/g, '\u00A0')
}

/**
 * Formats a numeric value for display in an input using browser locale
 * @param {number|string|null|undefined} value - The value to format
 * @returns {string} Formatted value string or empty string for invalid values
 */
export function formatNumberInput(value) {
  // Format a numeric value for display in an input with thousands separator
  if (value === null || value === undefined || value === '') {
    return ''
  }
  // Convert to number if necessary
  let numValue = value
  if (typeof value === 'string') {
    numValue = parseFloat(value.replace(/\s/g, '').replace(',', '.'))
  }
  if (isNaN(numValue) || numValue < 0) {
    return ''
  }
  // Format using browser locale
  // Replace narrow no-break space (U+202F) with standard non-breaking space (U+00A0) for visibility
  return numValue
    .toLocaleString(getBrowserLocale(), {
      minimumFractionDigits: 0,
      maximumFractionDigits: numValue % 1 === 0 ? 0 : 2, // No decimals if integer
      useGrouping: true
    })
    .replace(/\u202F/g, '\u00A0')
}

/**
 * Parses an input value to a number, removing all whitespace and grouping separators
 * @param {string|null|undefined} inputValue - The input value to parse
 * @returns {number|null} Parsed number or null for invalid values
 */
export function parseNumberInput(inputValue) {
  // Parse an input value to a number (removes all whitespace and grouping separators)
  if (!inputValue || inputValue === '') {
    return null
  }
  // Remove all whitespace (including non-breaking spaces) and grouping separators
  // Then normalize decimal separator to point
  const cleaned = inputValue
    .toString()
    .replace(/[\s\u00A0\u202F\u2009]/g, '') // Remove all types of spaces
    .replace(/[,\u00A0]/g, '.') // Replace comma and other separators with point
  const parsed = parseFloat(cleaned)
  return isNaN(parsed) ? null : parsed
}

