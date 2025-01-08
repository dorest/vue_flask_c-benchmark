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
        <el-table-column label="性能分析" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.enable_profiling ? 'success' : 'info'">
              {{ scope.row.enable_profiling ? '已启用' : '未启用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="scope">
            <el-button @click="runTest(scope.row)">运行</el-button>
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
      <el-form :model="newTestCase" :rules="rules" ref="testCaseForm">
        <el-form-item label="名称" prop="name">
          <el-input v-model="newTestCase.name" />
        </el-form-item>
        
        <el-form-item label="描述" prop="description">
          <el-input type="textarea" v-model="newTestCase.description" />
        </el-form-item>
        
        <el-form-item label="命令" prop="command">
          <el-input 
            type="textarea" 
            v-model="newTestCase.command"
            :rows="5"
            placeholder="请输入测试命令，支持多行命令"
          />
        </el-form-item>

        <!-- 新增性能分析配置部分 -->
        <el-form-item label="性能分析">
          <el-switch v-model="newTestCase.enable_profiling" />
        </el-form-item>

        <el-form-item label="性能分析工具" v-if="newTestCase.enable_profiling">
          <el-radio-group v-model="newTestCase.profiling_tools">
            <el-radio label="perf">CPU 分析 (perf)</el-radio>
            <el-radio label="callgrind">调用关系分析 (callgrind)</el-radio>
            <el-radio label="valgrind">内存分析 (valgrind)</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item 
          label="采样频率" 
          v-if="newTestCase.enable_profiling && newTestCase.profiling_tools === 'perf'"
        >
          <el-input-number 
            v-model="newTestCase.perf_frequency" 
            :min="1" 
            :max="999"
            :step="1"
          />
          <span class="hint">Hz (每秒采样次数)</span>
        </el-form-item>

        <el-form-item 
          label="内存检查级别" 
          v-if="newTestCase.enable_profiling && newTestCase.profiling_tools === 'valgrind'"
        >
          <el-select v-model="newTestCase.valgrind_level">
            <el-option label="基础检查" value="basic" />
            <el-option label="完整检查" value="full" />
            <el-option label="详细检查" value="extra" />
          </el-select>
        </el-form-item>
          <!-- Callgrind 配置选项 -->
        <el-form-item 
          label="Callgrind 配置" 
          v-if="newTestCase.enable_profiling && newTestCase.profiling_tools === 'callgrind'"
        >
          <div class="callgrind-options">
            <el-checkbox v-model="newTestCase.callgrind_config.collect_jumps">
              收集跳转信息
              <el-tooltip content="记录条件跳转的执行情况" placement="top">
                <el-icon class="info-icon"><InfoFilled /></el-icon>
              </el-tooltip>
            </el-checkbox>
            
            <el-checkbox v-model="newTestCase.callgrind_config.collect_systime">
              收集系统调用时间
              <el-tooltip content="包含系统调用的执行时间" placement="top">
                <el-icon class="info-icon"><InfoFilled /></el-icon>
              </el-tooltip>
            </el-checkbox>
            
            <el-checkbox v-model="newTestCase.callgrind_config.cache_sim">
              模拟缓存行为
              <el-tooltip content="模拟 CPU 缓存命中/未命中情况" placement="top">
                <el-icon class="info-icon"><InfoFilled /></el-icon>
              </el-tooltip>
            </el-checkbox>
                </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="createTestCase">确定</el-button>
      </template>
    </el-dialog>

    <!-- 定时任务对话框 -->
    <el-dialog 
      title="设置定时任务" 
      v-model="scheduleDialogVisible"
    >
      <el-form :model="scheduleForm">
        <el-form-item label="执行周期">
          <el-select v-model="scheduleForm.schedule_type">
            <el-option label="每天" value="daily" />
            <el-option label="每周" value="weekly" />
            <el-option label="每月" value="monthly" />
          </el-select>
        </el-form-item>
        <el-form-item label="Cron表达式">
          <el-input v-model="scheduleForm.cron_expression" placeholder="例如: 0 2 * * *" />
          <span class="cron-hint">分 时 日 月 周</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="scheduleDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="createScheduledTask">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, onMounted, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api'
import { useRouter } from 'vue-router'  // 导入 useRouter

export default {
  setup() {
    const testCases = ref([])
    const isEditing = ref(false)
    const createDialogVisible = ref(false)
    const newTestCase = ref({
      name: '',
      description: '',
      command: '',
      enable_profiling: false,
      profiling_tools: 'perf',  // 默认选择 perf
      perf_frequency: 99,         // 默认采样频率
      valgrind_level: 'full',     // 默认内存检查级别
      callgrind_config: {         // 新增 callgrind 配置
        collect_jumps: false,     // 是否收集跳转信息
        collect_systime: false,   // 是否收集系统调用时间
        cache_sim: false,         // 是否模拟缓存行为
      }
    })
    const scheduleDialogVisible = ref(false)
    const scheduleForm = ref({
      test_case_id: null,
      schedule_type: 'daily',
      cron_expression: '0 2 * * *'
    })

    const executingStates = reactive(new Map())
    const router = useRouter()  // 使用 useRouter

    const rules = {
      name: [
        { required: true, message: '请输入测试用例名称', trigger: 'blur' },
        { min: 1, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
      ],
      command: [
        { required: true, message: '请输入测试命令', trigger: 'blur' }
      ]
    }

    const fetchTestCases = async () => {
      try {
        const response = await api.getTestCases()
        testCases.value = response.data
        testCases.value.forEach(testCase => {
          executingStates.set(testCase.id, false)
        })
      } catch (error) {
        console.error('Failed to fetch test cases:', error)
        ElMessage.error('加载测试用例失败')
      }
    }

    const handleRowDblClick = (row) => {
      isEditing.value = true
      newTestCase.value = {
        ...row,
        profiling_tools: row.profiling_config?.tools || 'perf',
        perf_frequency: row.profiling_config?.perf_frequency || 99,
        valgrind_level: row.profiling_config?.valgrind_level || 'full',
        callgrind_config: row.profiling_config?.callgrind_config || {
          collect_jumps: false,
          collect_systime: false,
          cache_sim: false,
        }
      }
      createDialogVisible.value = true
    }

    const createTestCase = async () => {
      try {
        const testCaseData = {
          ...newTestCase.value,
          profiling_config: {
            tools: newTestCase.value.profiling_tools,
            perf_frequency: newTestCase.value.perf_frequency,
            valgrind_level: newTestCase.value.valgrind_level,
            callgrind_config: newTestCase.value.callgrind_config
          }
        }

        if (isEditing.value) {
          await api.updateTestCase(testCaseData.id, testCaseData)
          ElMessage.success('更新成功')
        } else {
          await api.createTestCase(testCaseData)
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
        await ElMessageBox.confirm(
          '确定要立即运行这个测试用例吗？',
          '确认',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'info',
          }
        )
        
        executingStates.set(testCase.id, true)
        
        const response = await api.runTestCase(testCase.id)
        if (response.data.code === 200) {
          ElMessage.success('测试启动成功')
          // 跳转到结果页面
          router.push(`/results/${response.data.data.result_id}`)
        } else {
          ElMessage.error(response.data.message || '测试启动失败')
        }
      } catch (error) {
        if (error !== 'cancel') {
          console.error('Failed to run test:', error)
          ElMessage.error('测试启动失败')
        }
      } finally {
        executingStates.set(testCase.id, false)
      }
    }

    const resetCurrentTestCase = () => {
      newTestCase.value = {
        id: null,
        name: '',
        description: '',
        command: '',
        enable_profiling: false,
        profiling_tools: 'perf',
        perf_frequency: 99,
        valgrind_level: 'full',
        callgrind_config: {
          collect_jumps: false,
          collect_systime: false,
          cache_sim: false,
        }
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


    const createScheduledTask = async () => {
      try {
        await api.createScheduledTask(scheduleForm.value)
        ElMessage.success('定时任务创建成功')
        scheduleDialogVisible.value = false
      } catch (error) {
        console.error('Failed to create scheduled task:', error)
        ElMessage.error('定时任务创建失败')
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
      showCreateDialog,
      scheduleDialogVisible,
      scheduleForm,
      createScheduledTask,
      executingStates,
      rules,
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

.cron-hint {
  font-size: 12px;
  color: #909399;
  margin-left: 10px;
}

.hint {
  margin-left: 10px;
  color: #909399;
  font-size: 13px;
}

.el-checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.el-form-item {
  margin-bottom: 22px;
}
</style> 