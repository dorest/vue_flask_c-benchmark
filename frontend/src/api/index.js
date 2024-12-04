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
  runTestCase(id) {
    return api.post(`/test-cases/${id}/execute`)
      .then(response => {
        return {
          data: {
            code: response.data.code || 200,
            data: {
              result_id: response.data.data?.result_id,
              result_dir: response.data.data?.result_dir
            },
            message: response.data.message
          }
        }
      })
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
  },
  // 添加获取测试执行结果的方法
  getTestResult(id) {
    return api.get(`/test-results/${id}`)
      .then(response => {
        return {
          data: {
            code: response.data.code || 200,
            data: {
              id: response.data.data?.id,
              test_case_name: response.data.data?.test_case_name,
              start_time: response.data.data?.start_time,
              status: response.data.data?.status,
              result_dir: response.data.data?.result_dir,
              output: response.data.data?.output
            },
            message: response.data.message
          }
        }
      })
  },
  // 添加获取测试输出的方法
  getTestOutput(resultDir) {
    return api.get(`/test-results/output`, {
      params: { result_dir: resultDir }
    })
      .then(response => {
        return {
          data: {
            code: response.data.code || 200,
            data: response.data.data || '',
            message: response.data.message
          }
        }
      })
  }
} 