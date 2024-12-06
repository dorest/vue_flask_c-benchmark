class WebSocketService {
    constructor() {
        this.ws = null
        this.callbacks = new Set()
    }

    connect() {
        if (this.ws && this.ws.readyState !== WebSocket.CLOSED) {
            console.log('WebSocket already connected')
            return
        }

        console.log('Connecting to WebSocket...')
        this.ws = new WebSocket('ws://localhost:5000/ws/test-status')

        this.ws.onopen = () => {
            console.log('WebSocket connected successfully')
        }

        this.ws.onmessage = (event) => {
            console.log('Received message:', event.data)
            const data = JSON.parse(event.data)
            this.callbacks.forEach(callback => callback(data))
        }

        this.ws.onclose = (event) => {
            console.log('WebSocket connection closed:', event.code, event.reason)
            this.ws = null
            // 尝试重连
            setTimeout(() => this.connect(), 3000)
        }

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error)
        }
    }

    subscribe(callback) {
        this.callbacks.add(callback)
        if (!this.ws || this.ws.readyState === WebSocket.CLOSED) {
            this.connect()
        }
    }

    unsubscribe(callback) {
        this.callbacks.delete(callback)
    }
}

export default new WebSocketService() 