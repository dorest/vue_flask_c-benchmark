<template>
  <div class="test-results">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>测试结果</span>
          <div class="header-actions">
            <el-select v-model="selectedTestCase" placeholder="选择测试用例" clearable>
              <el-option
                v-for="item in testCases"
                :key="item.id"
                :label="item.name"
                :value="item.id"
              />
            </el-select>
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
            />
          </div>
        </div>
      </template>

      <el-table :data="testResults" style="width: 100%">
        <el-table-column prop="test_case_name" label="测试用例" />
        <el-table-column prop="start_time" label="开始时间" :formatter="formatTime" />
        <el-table-column prop="end_time" label="结束时间" :formatter="formatTime" />
        <el-table-column prop="status" label="状态">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">
              {{ scope.row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="scope">
            <el-button @click="showDetails(scope.row)">详情</el-button>
            <el-button type="danger" @click="deleteResult(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 详情对话框 -->
    <el-dialog 
      v-model="detailsVisible" 
      title="测试详情" 
      width="90%" 
      destroy-on-close
      @closed="handleDialogClose"
    >
      <el-tabs v-model="activeTab">
        <el-tab-pane label="性能图表" name="charts">
          <div class="performance-charts">
            <!-- CPU图表 -->
            <div class="chart-wrapper">
              <h3>CPU使用率</h3>
              <div class="chart-container">
                <v-chart 
                  class="chart"
                  ref="cpuChart"
                  :option="cpuChartOption" 
                  autoresize
                  @mounted="handleChartMounted('cpu')"
                />
              </div>
            </div>
            <!-- 内存图表 -->
            <div class="chart-wrapper">
              <h3>内存使用</h3>
              <div class="chart-container">
                <v-chart 
                  class="chart"
                  ref="memoryChart"
                  :option="memoryChartOption"
                  autoresize
                  @mounted="handleChartMounted('memory')"
                />
              </div>
            </div>
            <!-- 响应时间图表 -->
            <div class="chart-wrapper">
              <h3>响应时间分布</h3>
              <div class="chart-container">
                <v-chart 
                  class="chart"
                  ref="responseTimeChart"
                  :option="responseTimeChartOption"
                  autoresize
                  @mounted="handleChartMounted('responseTime')"
                />
              </div>
            </div>
          </div>
          
          <div class="benchmark-comparison">
            <h3>基准线比较</h3>
            <el-table :data="benchmarkData" border>
              <el-table-column prop="metric" label="指标" />
              <el-table-column prop="current" label="当前值" />
              <el-table-column prop="baseline" label="基准值" />
              <el-table-column prop="diff" label="差异">
                <template #default="scope">
                  <span :class="getDiffClass(scope.row.diff)">
                    {{ scope.row.diff }}%
                  </span>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="火焰图">
          <div class="flame-graph-container">
            <img :src="currentFlameGraphUrl" alt="Flame Graph" v-if="currentFlameGraphUrl" />
            <div v-else class="no-data">暂无火焰图数据</div>
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="控制台输出">
          <div class="console-output">
            <pre v-for="(log, index) in testLogs" :key="index" :class="getLogClass(log)">{{ log }}</pre>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-dialog>
  </div>
</template>

<script>
import { ref, onMounted, watch, onUnmounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api'
import WebSocketService from '../services/websocket'

export default {
  props: {
    id: {
      type: [String, Number],
      default: null
    }
  },
  setup(props) {
    const testResults = ref([])
    const testCases = ref([])
    const selectedTestCase = ref(null)
    const dateRange = ref([])
    const detailsVisible = ref(false)
    const flameGraphVisible = ref(false)
    const currentFlameGraphUrl = ref('')
    const benchmarkData = ref([])  // 添加这行
    const testLogs = ref([])
    const logPollingInterval = ref(null)
    const activeTab = ref('charts')
    const charts = ref({
      cpu: null,
      memory: null,
      responseTime: null
    })
    // 图表配置
    const cpuChartOption = ref({
      title: { 
        text: 'CPU使用率趋势',
        textStyle: {
          fontSize: 14
        }
      },
      tooltip: { 
        trigger: 'axis',
        formatter: function(params) {
          // 直接使用原始的 ISO 时间字符串进行格式化
          const date = new Date(params[0].data[0])
          return `${date.toLocaleString('zh-CN', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
          })}<br/>CPU: ${params[0].data[1].toFixed(2)}%`
        }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        top: '60px',
        containLabel: true
      },
      xAxis: { 
        type: 'time',
        axisLabel: {
          formatter: function(value) {
            const date = new Date(value)
            return date.toLocaleTimeString('zh-CN', {
              hour: '2-digit',
              minute: '2-digit',
              second: '2-digit',
              hour12: false
            })
          },
          hideOverlap: true
        }
      },
      yAxis: { 
        type: 'value',
        name: '使用率(%)',
        min: 0,
        max: 100,
        splitLine: {
          show: true
        }
      },
      series: [{
        name: 'CPU使用率',
        type: 'line',
        showSymbol: false,
        data: [],
        smooth: true,
        areaStyle: {
          opacity: 0.1
        }
      }]
    })

    const memoryChartOption = ref({
      title: { 
        text: '内存使用趋势',
        textStyle: {
          fontSize: 14
        }
      },
      tooltip: { 
        trigger: 'axis',
        formatter: function(params) {
          // 直接使用原始的 ISO 时间字符串进行格式化
          const date = new Date(params[0].data[0])
          return `${date.toLocaleString('zh-CN', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
          })}<br/>CPU: ${params[0].data[1].toFixed(2)}%`
        }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        top: '60px',
        containLabel: true
      },
      xAxis: { 
        type: 'time',
        axisLabel: {
          formatter: function(value) {
            const date = new Date(value)
            return date.toLocaleTimeString('zh-CN', {
              hour: '2-digit',
              minute: '2-digit',
              second: '2-digit',
              hour12: false
            })
          },
          hideOverlap: true
        }
      },
      yAxis: { 
        type: 'value',
        name: '使用率(%)',
        min: 0,
        max: 100,
        splitLine: {
          show: true
        }
      },
      series: [{
        name: '内存使用率',
        type: 'line',
        showSymbol: false,
        data: [],
        smooth: true,
        areaStyle: {
          opacity: 0.1
        }
      }]
    })


    const responseTimeChartOption = ref({
      title: { 
        text: '响应时间分布',
        textStyle: {
          fontSize: 14
        }
      },
      tooltip: { 
        trigger: 'axis',
        formatter: '{b}ms<br/>{a}: {c}次'
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: { 
        type: 'category',
        name: '响应时间(ms)'
      },
      yAxis: { 
        type: 'value',
        name: '次数'
      },
      series: [{
        name: '响应时间',
        type: 'bar',  // 改用柱状图更适合展示分布
        data: [],
        barWidth: '60%'
      }]
    })

    // 添加 watch 监听器
    watch([dateRange, selectedTestCase], () => {
      loadTestResults()
    })

    // 修改 loadTestResults 函数，增加日期格式化
    const loadTestResults = async () => {
      try {
        const params = {
          test_case_id: selectedTestCase.value,
          start_date: dateRange.value?.[0] ? new Date(dateRange.value[0]).toISOString() : null,
          end_date: dateRange.value?.[1] ? new Date(dateRange.value[1]).toISOString() : null
        }
        const response = await api.getTestResults(params)
        testResults.value = response.data
        
        if (testResults.value.length === 0) {
          ElMessage.info('暂无测试结果数据')
        }
      } catch (error) {
        console.error('加载测试结果失败:', error)
        ElMessage.error(`加载测试结果失败: ${error.message || '未知错误'}`)
      }
    }

    // 添加图表实例引用
    const chartRefs = ref({
      cpu: null,
      memory: null,
      responseTime: null
    })

    // 修改 showDetails 函数
    const showDetails = async (result) => {
      try {
        const response = await api.getTestResultDetails(result.id)
        updateCharts(response.data)
        currentFlameGraphUrl.value = response.data.flamegraph_path
        testLogs.value = response.data.logs || []
        activeTab.value = 'charts' // 重置为默认tab
        detailsVisible.value = true
        
        // 在下一个 tick 更新图表
        nextTick(() => {
          Object.values(charts.value).forEach(chart => {
            if (chart) {
              chart.resize()
            }
          })
        })

        if (result.status === 'running') {
          startLogPolling(result.id)
        } else {
          try {
            const logsResponse = await api.getTestLogs(result.id)
            if (logsResponse.data?.logs) {
              testLogs.value = logsResponse.data.logs
            }
          } catch (error) {
            console.error('获取完整日志失败:', error)
          }
        }
      } catch (error) {
        console.error('加载详情失败:', error)
        ElMessage.error('加载详情失败')
      }
    }

    // 更新图表数据
    const updateCharts = (data) => {
      const options = {
        cpu: cpuChartOption,
        memory: memoryChartOption,
        responseTime: responseTimeChartOption
      }

      Object.entries(options).forEach(([type, option]) => {
        // 获取原始数据
        const rawData = data[`${type}_data`] || []
        
        // 转换数据格式
        const formattedData = rawData.map(item => [
          // 将 ISO 时间字符串转换为时间戳
          item.timestamp,  // 保持原始 ISO 时间字符串
          item.value
        ])

        // 更新图表数据
        option.value.series[0].data = formattedData

        nextTick(() => {
          const chart = charts.value[type]
          if (chart) {
            chart.setOption(option.value)
            chart.resize()
          }
        })
      })

      benchmarkData.value = data.benchmark_data || []
    }

    // 显示火焰图
    const showFlameGraph = (result) => {
      currentFlameGraphUrl.value = result.flamegraph_path
      flameGraphVisible.value = true
    }

    // 导出报告
    const exportReport = async (result) => {
      try {
        await api.exportTestReport(result.id)
        ElMessage.success('报告导出成功')
      } catch (error) {
        ElMessage.error('报告导出失败')
      }
    }

    // 格式化时间
    const formatTime = (row, column) => {
      const date = new Date(row[column.property])
      return date.toLocaleString()
    }

    // 获取状态标签类型
    const getStatusType = (status) => {
      const types = {
        'success': 'success',
        'failed': 'danger',
        'running': 'warning'
      }
      return types[status] || 'info'
    }

    // 获取差异值样式
    const getDiffClass = (diff) => {
      return {
        'text-success': diff <= 0,
        'text-danger': diff > 0
      }
    }

    // 获取日志样式
    const getLogClass = (log) => {
      if (log.includes('[STDERR]')) {
        return 'log-error'
      }
      if (log.includes('Error:')) {
        return 'log-error'
      }
      if (log.includes('[STDOUT]')) {
        return 'log-output'
      }
      return 'log-info'
    }

    // 获取测试日志
    const fetchTestLogs = async (resultId) => {
      try {
        const response = await api.getTestLogs(resultId)
        if (response.data) {
          // 更新日志
          testLogs.value = response.data.logs || []
          
          // 更新测试状态
          const result = testResults.value.find(r => r.id === resultId)
          if (result) {
            const newStatus = response.data.status
            if (newStatus && newStatus !== result.status) {
              result.status = newStatus
              // 如果有结束时间，也更新它
              if (response.data.end_time) {
                result.end_time = response.data.end_time
              }
            }
            
            // 如果测试已完成，停止轮询并刷新数据
            if (newStatus && newStatus !== 'running') {
              stopLogPolling()
              await loadTestResults() // 重新加载列表以获取完整数据
            }
          }
        }
      } catch (error) {
        console.error('获取日志失败:', error)
        stopLogPolling() // 发生错误时停止轮询
      }
    }
        // 开始日志轮询
    const startLogPolling = (resultId) => {
      console.log('Starting polling for test:', resultId)
      stopLogPolling() // 确保先停止之前的轮询
      
      logPollingInterval.value = setInterval(async () => {
        await fetchTestLogs(resultId)
      }, 3000) // 每3秒轮询一次
    }

    const stopLogPolling = () => {
      if (logPollingInterval.value) {
        console.log('Stopping polling')
        clearInterval(logPollingInterval.value)
        logPollingInterval.value = null
      }
    }
        
    // 删除测试结果
    const deleteResult = async (result) => {
      try {
        await ElMessageBox.confirm('确定要删除该测试结果吗？', '提示', {
          type: 'warning'
        })
        
        await api.deleteTestResult(result.id)
        ElMessage.success('删除成功')
        loadTestResults()  // 重新加载列表
        
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('删除失败')
        }
      }
    }
    
    watch(detailsVisible, (newValue) => {
      if (!newValue) { // 当对话框关闭时
        stopLogPolling() // 停止轮询
      }
    })
    
    const handleWebSocketMessage = (data) => {
      const result = testResults.value.find(r => r.id === data.test_id)
      if (result) {
        result.status = data.status
        if (data.end_time) {
          result.end_time = data.end_time
        }
      }
    }

    onMounted(() => {
      // 订阅 WebSocket 消息
      WebSocketService.subscribe(handleWebSocketMessage)
      
      // 加载数据
      Promise.all([
        loadTestResults(),
        api.getTestCases().then(response => {
          testCases.value = response.data
        })
      ])
    })

    onUnmounted(() => {
      // 取消订阅 WebSocket 消息
      WebSocketService.unsubscribe(handleWebSocketMessage)
      stopLogPolling()
    })

    // 修改图表容器样式
    const chartStyle = {
      width: '100%',
      height: '300px'
    }

    // 处理图表挂载
    const handleChartMounted = (type) => {
      nextTick(() => {
        const chart = charts.value[type]
        if (chart) {
          chart.resize()
        }
      })
    }

    // 处理对话框关闭
    const handleDialogClose = () => {
      stopLogPolling()
      // 清理图表实例
      Object.values(charts.value).forEach(chart => {
        if (chart) {
          chart.dispose()
        }
      })
      charts.value = {
        cpu: null,
        memory: null,
        responseTime: null
      }
    }

    return {
      testResults,
      testCases,
      selectedTestCase,
      dateRange,
      detailsVisible,
      flameGraphVisible,
      currentFlameGraphUrl,
      cpuChartOption,
      memoryChartOption,
      responseTimeChartOption,
      benchmarkData, 
      showDetails,
      showFlameGraph,
      exportReport,
      formatTime,
      getStatusType,
      getDiffClass,
      chartStyle,
      chartRefs,
      testLogs,
      deleteResult,
      getLogClass,
      activeTab,
      handleChartMounted,
      handleDialogClose,
    }
  }
}
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 16px;
}

.performance-charts {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  margin-bottom: 20px;
}

.chart-wrapper {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.1);
}

.chart-container {
  height: 300px;
  width: 100%;
}

/* 确保图表正确渲染 */
:deep(.echarts) {
  width: 100% !important;
  height: 100% !important;
}

.benchmark-comparison {
  margin-top: 20px;
}

.text-success {
  color: #67C23A;
}

.text-danger {
  color: #F56C6C;
}

.flame-graph-container {
  width: 100%;
  overflow: auto;
}

.flame-graph-container img {
  width: 100%;
  height: auto;
}

/* 添加过渡效果 */
.el-dialog__body {
  transition: all 0.3s ease;
}

.console-output {
  height: 400px;
  overflow-y: auto;
  background: #1e1e1e;
  padding: 10px;
  border-radius: 4px;
  font-family: monospace;
}

.console-output pre {
  margin: 0;
  padding: 2px 0;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.log-error {
  color: #ff6b6b;
}

.log-output {
  color: #a8ff60;
}

.log-info {
  color: #d7d7d7;
}

.no-data {
  text-align: center;
  padding: 20px;
  color: #909399;
}
</style> 