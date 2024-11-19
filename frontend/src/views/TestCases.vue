<template>
  <div class="test-cases">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>测试用例管理</span>
          <el-button type="primary" @click="showCreateDialog">新建测试</el-button>
        </div>
      </template>
      
      <el-table :data="testCases">
        <el-table-column prop="name" label="名称" />
        <el-table-column prop="description" label="描述" />
        <el-table-column label="操作">
          <template #default="scope">
            <el-button @click="runTest(scope.row)">运行</el-button>
            <el-button @click="showScheduleDialog(scope.row)">定时</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建测试用例对话框 -->
    <el-dialog v-model="createDialogVisible" title="新建测试用例">
      <el-form :model="newTestCase">
        <el-form-item label="名称">
          <el-input v-model="newTestCase.name" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input type="textarea" v-model="newTestCase.description" />
        </el-form-item>
        <el-form-item label="命令">
          <el-input v-model="newTestCase.command" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="createTestCase">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import api from '../api'

export default {
  setup() {
    const testCases = ref([])
    const createDialogVisible = ref(false)
    const newTestCase = ref({
      name: '',
      description: '',
      command: ''
    })

    const fetchTestCases = async () => {
      try {
        const response = await api.getTestCases()
        testCases.value = response.data
      } catch (error) {
        console.error('Failed to fetch test cases:', error)
      }
    }

    const createTestCase = async () => {
      try {
        await api.createTestCase(newTestCase.value)
        createDialogVisible.value = false
        await fetchTestCases()
      } catch (error) {
        console.error('Failed to create test case:', error)
      }
    }

    const runTest = async (testCase) => {
      try {
        await api.runTestCase(testCase.id)
        ElMessage.success('测试启动成功')
      } catch (error) {
        ElMessage.error('测试启动失败')
      }
    }

    onMounted(fetchTestCases)

    return {
      testCases,
      createDialogVisible,
      newTestCase,
      createTestCase,
      runTest,
      showCreateDialog: () => createDialogVisible.value = true
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
</style> 