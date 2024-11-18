<template>
  <el-container>
    <el-aside width="200px">
      <el-menu
        router
        :default-active="$route.path"
        class="el-menu-vertical">
        <el-menu-item index="/test-cases">
          <el-icon><Document /></el-icon>
          <span>测试用例</span>
        </el-menu-item>
        <el-menu-item index="/results">
          <el-icon><DataLine /></el-icon>
          <span>测试结果</span>
        </el-menu-item>
        <el-menu-item index="/schedules">
          <el-icon><Timer /></el-icon>
          <span>定时任务</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    
    <el-container>
      <el-header>
        <h2>C++性能测试平台</h2>
      </el-header>
      <el-main>
        <router-view></router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.el-header {
  background-color: #f5f7fa;
  line-height: 60px;
  padding: 0 20px;
}

.el-aside {
  background-color: #304156;
  color: #fff;
  height: 100vh;
}

.el-menu {
  border-right: none;
}
</style>
  