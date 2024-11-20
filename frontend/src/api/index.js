import axios from 'axios'

const API_BASE_URL = 'http://localhost:5000'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 5000
})

export default {
  // 测试用例相关
  getTestCases() {
    return api.get('/test-cases')
  },
  createTestCase(data) {
    return api.post('/test-cases', data)
  },
  runTestCase(id, parameters = {}) {
    return api.post(`/test-cases/${id}/run`, { parameters })
  },
  // 添加删除方法
  deleteTestCase(id) {
    return api.delete(`/test-cases/${id}`)
  },
  // 添加更新方法
  updateTestCase(id, data) {
    return api.put(`/test-cases/${id}`, data)
  }
} 