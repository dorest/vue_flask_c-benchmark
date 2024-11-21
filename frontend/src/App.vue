<template>
  <el-container>
    <el-aside width="200px">
      <div class="sidebar-header">
        <h3>C++性能测试平台</h3>
      </div>
      <el-menu
        router
        :default-active="$route.path"
        class="el-menu-vertical"
        background-color="#304156"
        text-color="#fff"
        active-text-color="#409EFF">
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
        <div class="header-content">
          <h2>欢迎使用性能测试平台</h2>
        </div>
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
  border-bottom: 1px solid #e6e6e6;
}

.header-content {
  display: flex;
  align-items: center;
  height: 100%;
}

.el-aside {
  background-color: #304156;
  color: #fff;
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 20px;
  color: #fff;
  border-bottom: 1px solid #1f2d3d;
}

.sidebar-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.el-menu {
  border-right: none;
  margin-top: 20px;
}

.el-menu-item {
  height: 56px;
  line-height: 56px;
  margin: 4px 0;
}

.el-menu-item:hover {
  background-color: #263445 !important;
}

.el-menu-item.is-active {
  background-color: #1f2d3d !important;
}

.el-icon {
  margin-right: 10px;
  font-size: 18px;
}
</style>
  