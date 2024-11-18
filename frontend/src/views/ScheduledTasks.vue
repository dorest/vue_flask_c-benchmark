<template>
  <div class="scheduled-tasks">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>定时任务</span>
          <el-button type="primary" @click="showCreateDialog">新建定时任务</el-button>
        </div>
      </template>

      <el-table :data="tasks">
        <el-table-column prop="test_case.name" label="测试用例" />
        <el-table-column prop="schedule_type" label="调度类型" />
        <el-table-column prop="cron_expression" label="Cron表达式" />
        <el-table-column prop="is_active" label="状态">
          <template #default="scope">
            <el-switch
              v-model="scope.row.is_active"
              @change="updateTaskStatus(scope.row)"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作">
          <template #default="scope">
            <el-button type="danger" @click="deleteTask(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建定时任务对话框 -->
    <el-dialog v-model="createDialogVisible" title="新建定时任务">
      <el-form :model="newTask" label-width="100px">
        <el-form-item label="测试用例">
          <el-select v-model="newTask.test_case_id">
            <el-option
              v-for="item in testCases"
              :key="item.id"
              :label="item.name"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="调度类型">
          <el-select v-model="newTask.schedule_type">
            <el-option label="每天" value="daily" />
            <el-option label="每周" value="weekly" />
            <el-option label="每月" value="monthly" />
          </el-select>
        </el-form-item>
        <el-form-item label="Cron表达式">
          <el-input v-model="newTask.cron_expression" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="createTask">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import api from '../api'

export default {
  setup() {
    const tasks = ref([])
    const testCases = ref([])
    const createDialogVisible = ref(false)
    const newTask = ref({
      test_case_id: null,
      schedule_type: 'daily',
      cron_expression: '0 0 * * *'
    })

    const fetchTasks = async () => {
      const response = await api.getScheduledTasks()
      tasks.value = response.data
    }

    const fetchTestCases = async () => {
      const response = await api.getTestCases()
      testCases.value = response.data
    }

    const createTask = async () => {
      await api.createScheduledTask(newTask.value)
      createDialogVisible.value = false
      await fetchTasks()
    }

    const updateTaskStatus = async (task) => {
      await api.updateScheduledTask(task.id, { is_active: task.is_active })
    }

    const deleteTask = async (task) => {
      await api.deleteScheduledTask(task.id)
      await fetchTasks()
    }

    onMounted(() => {
      fetchTasks()
      fetchTestCases()
    })

    return {
      tasks,
      testCases,
      createDialogVisible,
      newTask,
      createTask,
      updateTaskStatus,
      deleteTask
    }
  }
}
</script> 