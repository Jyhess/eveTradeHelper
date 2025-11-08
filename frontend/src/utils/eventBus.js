// Simple Event Bus pour Vue 3
class EventBus {
  constructor() {
    this.events = {}
  }

  on(event, callback) {
    if (!this.events[event]) {
      this.events[event] = []
    }
    this.events[event].push(callback)
  }

  off(event, callback) {
    if (!this.events[event]) return

    if (callback) {
      this.events[event] = this.events[event].filter(cb => cb !== callback)
    } else {
      delete this.events[event]
    }
  }

  emit(event, data) {
    if (!this.events[event]) return

    this.events[event].forEach(callback => {
      callback(data)
    })
  }
}

export default new EventBus()
