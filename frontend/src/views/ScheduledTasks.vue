<template>
  <div class="scheduled">
    <el-row :gutter="20">
      <el-col :span="24">
        <el-card class="box-card">
          <div class="clearfix">
            <span>定时任务列表</span>
            <el-button style="float: right; padding: 3px 0" type="text" @click="handleAdd">添加任务</el-button>
          </div>
          <el-table :data="tableData" style="width: 100%" @row-dblclick="handleEdit">
            <el-table-column prop="name" label="任务名称" />
            <el-table-column label="测试用例">
              <template #default="{ row }">
                {{ getTestCaseName(row.test_case_id) }}
              </template>
            </el-table-column>
            <el-table-column prop="cron" label="执行时间" />
            <el-table-column label="状态">
              <template #default="{ row }">
                <el-tag :type="row.enabled ? 'success' : 'info'">
                  {{ row.enabled ? '启用' : '禁用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200">
              <template #default="{ row }">
                <el-button
                  size="small"
                  :type="row.enabled ? 'warning' : 'success'"
                  @click="handleToggle(row)"
                >{{ row.enabled ? '禁用' : '启用' }}</el-button>
                <el-button
                  size="small"
                  type="danger"
                  @click="handleDelete(row)"
                >删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑定时任务' : '添加定时任务'" 
      width="500px"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
      >
        <el-form-item label="任务名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="测试用例" prop="test_case_id">
          <el-select
            v-model="form.test_case_id"
            placeholder="请选择测试用例"
            style="width: 100%"
          >
            <el-option
              v-for="item in testCases"
              :key="item.id"
              :label="item.name"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="执行时间" prop="cron">
          <el-input 
            v-model="form.cron"
            placeholder="例如: 0 * * * * (每小时执行)"
          >
            <template #append>
              <el-popover
                placement="top-start"
                :width="400"
                trigger="hover"
              >
                <template #default>
                  <div>
                    <p>Cron 表达式格式：分 时 日 月 星期</p>
                    <p>每个字段可以使用：</p>
                    <ul>
                      <li>* - 表示任意值</li>
                      <li>数字 - 具体值</li>
                      <li>*/n - 每隔n个单位</li>
                    </ul>
                    <p>示例：</p>
                    <ul>
                      <li>0 * * * * - 每小时执行</li>
                      <li>0 0 * * * - 每天零点执行</li>
                      <li>0 0 * * 0 - 每周日零点执行</li>
                      <li>*/15 * * * * - 每15分钟执行</li>
                    </ul>
                  </div>
                </template>
                <template #reference>
                  <el-icon><QuestionFilled /></el-icon>
                </template>
              </el-popover>
            </template>
          </el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取 消</el-button>
          <el-button type="primary" @click="submitForm">确 定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { QuestionFilled } from '@element-plus/icons-vue'
import api from '../api'

export default {
  name: 'ScheduledTasks',
  components: {
    QuestionFilled
  },
  setup() {
    // 数据定义
    const tableData = ref([])
    const testCases = ref([])
    const dialogVisible = ref(false)
    const formRef = ref(null)
    const isEditing = ref(false)
    const form = ref({
      name: '',
      test_case_id: '',
      cron: '',
      enabled: true
    })

    // 表单验证规则
    const rules = ref({
      name: [
        { required: true, message: '请输入任务名称', trigger: 'blur' }
      ],
      test_case_id: [
        { required: true, message: '请选择测试用例', trigger: 'change' }
      ],
      cron: [
        { required: true, message: '请输入执行时间', trigger: 'blur' },
        { 
          validator: (rule, value, callback) => {
            // 去除首尾空格
            const trimmedValue = value.trim()
            
            // 检查是否包含5个部分
            const parts = trimmedValue.split(/\s+/)
            if (parts.length !== 5) {
              callback(new Error('Cron 表达式必须包含5个部分'))
              return
            }

            // 验证每个部分的格式
            const patterns = {
              minute: /^(\*|[0-5]?[0-9])(\/[0-9]+)?$/,
              hour: /^(\*|1?[0-9]|2[0-3])(\/[0-9]+)?$/,
              day: /^(\*|[1-9]|[12][0-9]|3[01])(\/[0-9]+)?$/,
              month: /^(\*|[1-9]|1[0-2])(\/[0-9]+)?$/,
              weekday: /^(\*|[0-6])(\/[0-9]+)?$/
            }

            const [minute, hour, day, month, weekday] = parts

            if (!patterns.minute.test(minute)) {
              callback(new Error('分钟格式不正确 (0-59)'))
              return
            }
            if (!patterns.hour.test(hour)) {
              callback(new Error('小时格式不正确 (0-23)'))
              return
            }
            if (!patterns.day.test(day)) {
              callback(new Error('日期格式不正确 (1-31)'))
              return
            }
            if (!patterns.month.test(month)) {
              callback(new Error('月份格式不正确 (1-12)'))
              return
            }
            if (!patterns.weekday.test(weekday)) {
              callback(new Error('星期格式不正确 (0-6)'))
              return
            }

            callback()
          },
          trigger: 'blur'
        }
      ]
    })

    // 获取表格数据
    const getTableData = async () => {
      try {
        const response = await api.getScheduledTasks()
        tableData.value = response.data.tasks
      } catch (error) {
        ElMessage.error('获取任务列表失败')
      }
    }

    // 获取测试用例列表
    const getTestCases = async () => {
      try {
        const response = await api.getTestCases()
        testCases.value = response.data
      } catch (error) {
        ElMessage.error('获取测试用例列表失败')
      }
    }

    // 获取测试用例名称
    const getTestCaseName = (id) => {
      const testCase = testCases.value.find(tc => tc.id === id)
      return testCase ? testCase.name : '未知测试用例'
    }

    // 显示添加对话框
    const handleAdd = () => {
      isEditing.value = false
      dialogVisible.value = true
      form.value = {
        name: '',
        test_case_id: '',
        cron: '',
        enabled: true
      }
    }
          // 处理编辑
    const handleEdit = (row) => {
      isEditing.value = true
      dialogVisible.value = true
      form.value = {
        id: row.id,
        name: row.name,
        test_case_id: row.test_case_id,
        cron: row.cron,
        enabled: row.enabled
      }
    }


    // 提交表单
    const submitForm = async () => {
      if (!formRef.value) return
      
      try {
        await formRef.value.validate()
        
        if (isEditing.value) {
          await api.updateScheduledTask(form.value.id, form.value)
          ElMessage.success('更新任务成功')
        } else {
          await api.createScheduledTask(form.value)
          ElMessage.success('添加任务成功')
        }
        
        dialogVisible.value = false
        getTableData()
      } catch (error) {
        if (error?.message) {
          ElMessage.error(error.message)
        } else {
          ElMessage.error(isEditing.value ? '更新任务失败' : '添加任务失败')
        }
      }
    }

    // 切换任务状态
    const handleToggle = async (row) => {
      try {
        await api.toggleScheduledTask(row.id)
        ElMessage.success(`${row.enabled ? '禁用' : '启用'}任务成功`)
        getTableData()
      } catch (error) {
        ElMessage.error(`${row.enabled ? '禁用' : '启用'}任务失败`)
      }
    }

    // 删除任务
    const handleDelete = async (row) => {
      try {
        await ElMessageBox.confirm('确认删除该任务吗？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        
        await api.deleteScheduledTask(row.id)
        ElMessage.success('删除任务成功')
        getTableData()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('删除任务失败')
        }
      }
    }

    // 生命周期钩子
    onMounted(() => {
      Promise.all([
        getTableData(),
        getTestCases()
      ])
    })

    return {
      // 数据
      formRef, 
      tableData,
      testCases,
      dialogVisible,
      form,
      rules,
      isEditing,

      // 方法
      getTestCaseName,
      handleAdd,
      handleEdit,
      submitForm,
      handleToggle,
      handleDelete
    }
  }
}
</script>

<style scoped>
.scheduled {
  padding: 20px;
}
</style> 