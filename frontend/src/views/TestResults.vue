<template>
  <div class="test-results">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>测试结果</span>
          <el-select v-model="selectedTestCase" placeholder="选择测试用例" clearable>
            <el-option
              v-for="item in testCases"
              :key="item.id"
              :label="item.name"
              :value="item.id"
            />
          </el-select>
        </div>
      </template>

      <el-table :data="results" v-loading="loading">
        <el-table-column prop="test_case.name" label="测试用例" />
        <el-table-column prop="start_time" label="开始时间" />
        <el-table-column prop="status" label="状态">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">
              {{ scope.row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作">
          <template #default="scope">
            <el-button @click="showDetails(scope.row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 结果详情对话框 -->
    <el-dialog v-model="detailsVisible" title="测试结果详情" width="80%">
      <el-tabs>
        <el-tab-pane label="性能数据">
          <pre>{{ selectedResult?.perf_data }}</pre>
        </el-tab-pane>
        <el-tab-pane label="火焰图">
          <img :src="selectedResult?.flamegraph_path" v-if="selectedResult?.flamegraph_path">
        </el-tab-pane>
      </el-tabs>
    </el-dialog>
  </div>
</template>

<script>
import { ref, onMounted, watch } from 'vue'
import api from '../api'

export default {
  setup() {
    const results = ref([])
    const testCases = ref([])
    const selectedTestCase = ref(null)
    const loading = ref(false)
    const detailsVisible = ref(false)
    const selectedResult = ref(null)

    const fetchResults = async () => {
      loading.value = true
      try {
        const response = await api.getTestResults(selectedTestCase.value)
        results.value = response.data
      } finally {
        loading.value = false
      }
    }

    const fetchTestCases = async () => {
      const response = await api.getTestCases()
      testCases.value = response.data
    }

    const showDetails = (result) => {
      selectedResult.value = result
      detailsVisible.value = true
    }

    const getStatusType = (status) => {
      const types = {
        completed: 'success',
        running: 'warning',
        failed: 'danger',
        pending: 'info'
      }
      return types[status] || 'info'
    }

    onMounted(() => {
      fetchTestCases()
      fetchResults()
    })

    watch(selectedTestCase, fetchResults)

    return {
      results,
      testCases,
      selectedTestCase,
      loading,
      detailsVisible,
      selectedResult,
      showDetails,
      getStatusType
    }
  }
}
</script> 