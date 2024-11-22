import axios from 'axios'

const API_BASE_URL = 'http://localhost:5000'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 5000
})
// 添加响应拦截器统一处理错误
api.interceptors.response.use(
  response => {
      return response
  },
  error => {
      if (error.response) {
          // 请求已发出，但服务器响应状态码不在 2xx 范围内
          console.error('API Error:', error.response.data)
          return Promise.resolve({ 
              data: {
                  code: error.response.status,
                  data: [],
                  message: error.response.data.message || '请求失败'
              }
          })
      } else {
          // 请求未发出就失败了
          return Promise.resolve({ 
              data: {
                  code: 500,
                  data: [],
                  message: '网络错误'
              }
          })
      }
  }
)

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
  },
  // 获取测试结果列表
  getTestResults(params) {
    return api.get('/test-results', { params })
        .then(response => {
            // 确保返回的数据格式一致
            return {
                data: response.data.data || [],
                message: response.data.message
            }
        })
  },
  getTestResultDetails(id) {
      return api.get(`/test-results/${id}/details`)
          .then(response => {
              return {
                  data: response.data.data || {},
                  message: response.data.message
              }
          })
  },
  // 导出测试报告
  exportTestReport(id) {
    return api.get(`/test-results/${id}/export`, {
      responseType: 'blob'
    })
  }
} 