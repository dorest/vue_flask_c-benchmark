<template>
    <div id="app">
      <h1>Vue + Flask</h1>
      <p>{{ message }}</p>
    </div>
  </template>
  
  <script>
  export default {
    data() {
      return {
        message: ""  // 用来存储从 Flask API 获取的消息
      };
    },
    mounted() {
      // 当组件挂载完成后，发起 API 请求
      fetch("http://localhost:5000/api/data")  // Flask 后端 API 地址
        .then(response => response.json())  // 解析返回的 JSON 数据
        .then(data => {
          this.message = data.message;  // 将获取到的 message 显示到页面上
        })
        .catch(error => {
          console.error("Error fetching data:", error);
        });
    }
  };
  </script>
  
  <style scoped>
  /* 样式代码可以根据需要添加 */
  #app {
    font-family: Avenir, Helvetica, Arial, sans-serif;
    text-align: center;
    color: #2c3e50;
  }
  </style>
  