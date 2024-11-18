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
  
  // 测试结果相关
  getTestResults(testCaseId = null) {
    return api.get('/test-results', {
      params: { test_case_id: testCaseId }
    })
  },
  getTestResult(id) {
    return api.get(`/test-results/${id}`)
  },
  
  // 定时任务相关
  getScheduledTasks() {
    return api.get('/scheduled-tasks')
  },
  createScheduledTask(data) {
    return api.post('/scheduled-tasks', data)
  },
  updateScheduledTask(id, data) {
    return api.put(`/scheduled-tasks/${id}`, data)
  },
  deleteScheduledTask(id) {
    return api.delete(`/scheduled-tasks/${id}`)
  }
} 