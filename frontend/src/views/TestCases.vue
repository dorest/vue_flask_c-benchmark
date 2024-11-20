<template>
  <div class="test-cases">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>测试用例管理</span>
          <el-button type="primary" @click="showCreateDialog">新建测试</el-button>
        </div>
      </template>
      
      <el-table :data="testCases" @row-dblclick="handleRowDblClick">
        <el-table-column prop="name" label="名称" />
        <el-table-column prop="description" label="描述" />
        <el-table-column prop="command" label="命令" />
        <el-table-column label="操作" width="280">
          <template #default="scope">
            <el-button @click="runTest(scope.row)">运行</el-button>
            <el-button @click="showScheduleDialog(scope.row)">定时</el-button>
            <el-button 
              type="danger" 
              @click="handleDelete(scope.row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建测试用例对话框 -->
    <el-dialog v-model="createDialogVisible" :title="isEditing ? '编辑测试用例' : '新建测试用例'" >
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
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api'

export default {
  setup() {
    const testCases = ref([])
    const isEditing = ref(false)
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
        ElMessage.error('加载测试用例失败')
      }
    }

    const handleRowDblClick = (row) => {
      isEditing.value = true
      newTestCase.value = { ...row }
      createDialogVisible.value = true
    }

    const createTestCase = async () => {
      try {
        if (isEditing.value) {
          await api.updateTestCase(newTestCase.value.id, newTestCase.value)
          ElMessage.success('更新成功')
        } else {
          await api.createTestCase(newTestCase.value)
          ElMessage.success('创建成功')
        }
        createDialogVisible.value = false
        await fetchTestCases()
      } catch (error) {
        console.error('Failed to save test case:', error)
        ElMessage.error(isEditing.value ? '更新失败' : '创建失败')
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

    const resetCurrentTestCase = () => {
      newTestCase.value = {
        id: null,
        name: '',
        description: '',
        command: ''
      }
    }

    const showCreateDialog = () => {
      isEditing.value = false
      resetCurrentTestCase()
      createDialogVisible.value = true
    }
    const handleDelete = async (testCase) => {
      try {
        await ElMessageBox.confirm(
          '确定要删除这个测试用例吗？相关的测试结果和定时任务也会被删除。',
          '警告',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning',
          }
        )
        
        await api.deleteTestCase(testCase.id)
        ElMessage.success('删除成功')
        await fetchTestCases()  // 重新加载列表
      } catch (error) {
        if (error !== 'cancel') {
          console.error('Failed to delete test case:', error)
          ElMessage.error('删除失败')
        }
      }
    }

    onMounted(fetchTestCases)

    return {
      testCases,
      createDialogVisible,
      newTestCase,
      createTestCase,
      isEditing,
      runTest,
      handleDelete,
      handleRowDblClick,
      showCreateDialog
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

.el-button {
  margin-right: 8px;
}

.el-button:last-child {
  margin-right: 0;
}
</style> 