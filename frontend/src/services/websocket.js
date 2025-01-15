class WebSocketService {
    constructor() {
        this.ws = null
        this.callbacks = new Set()
        this.pendingMessages = []  // 添加消息队列
    }

    connect() {
        if (this.ws && this.ws.readyState !== WebSocket.CLOSED) {
            console.log('WebSocket already connected')
            return
        }

        console.log('Connecting to WebSocket...')
        this.ws = new WebSocket(process.env.VUE_APP_WS_BASE_URL)

        this.ws.onopen = () => {
            console.log('WebSocket connected successfully')
        }

        this.ws.onmessage = (event) => {
            console.log('Received message:', event.data)
            console.log('callbacks:', this.callbacks)
            const data = JSON.parse(event.data)
            if (this.callbacks.size === 0) {
                // 如果没有回调注册，将消息存入队列
                console.log('No callbacks registered, queueing message')
                this.pendingMessages.push(data)
            } else {
                // 有回调时直接处理
                this.callbacks.forEach(callback => callback(data))
            }
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
        console.log('subscribe:', callback)
        this.callbacks.add(callback)

        // 处理之前队列中的消息
        if (this.pendingMessages.length > 0) {
            console.log('Processing pending messages:', this.pendingMessages.length)
            this.pendingMessages.forEach(data => callback(data))
            this.pendingMessages = []  // 清空队列
        }

        if (!this.ws || this.ws.readyState === WebSocket.CLOSED) {
            this.connect()
        }
    }

    unsubscribe(callback) {
        this.callbacks.delete(callback)
    }
}

export default new WebSocketService() 