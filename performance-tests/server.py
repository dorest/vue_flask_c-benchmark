import socket
import json
import subprocess
import os
from datetime import datetime
import threading
import queue
import requests  # 新增
import logging
from logging.handlers import RotatingFileHandler
import psutil
import time

class TestServer:
    def __init__(self):
        self.base_dir = '/root/flask-vue/performance-tests'
        self.log_dir = os.path.join(self.base_dir, 'logs')
        os.makedirs(self.log_dir, exist_ok=True)
        self.setup_logging()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('0.0.0.0', 9999))
        self.sock.listen(1)
        print("Test server started on 0.0.0.0:9999")
        # 存储每个测试的日志队列和状态
        self.test_logs = {}
        self.test_status = {}
        self.api_url = 'http://172.18.0.2:5000'  # 根据实际情况修改,docker inspect flask_app 查看下ip
        self.test_timestamps = {}  # 存储 test_case_id 对应的启动时间
        # 禁用代理设置
        os.environ['NO_PROXY'] = '*'
        os.environ['no_proxy'] = '*'
        self.perf_data = {}  # 新增：存储性能数据
        
    def setup_logging(self):
        """配置日志记录器"""
        self.logger = logging.getLogger('TestServer')
        self.logger.setLevel(logging.DEBUG)
        
        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - [%(threadName)s] - %(message)s'
        )
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        # 文件处理器（带轮转）
        file_handler = RotatingFileHandler(
            os.path.join(self.log_dir, 'server.log'),
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        
        # 添加处理器
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
    
    def update_test_status(self, test_case_id, start_timestamp, status, end_time=None, perf_data=None):
        """通过 HTTP 更新测试状态"""
        try:
            data = {
                'test_case_id': test_case_id,
                'start_timestamp': start_timestamp.isoformat(),
                'status': status,
                'end_time': end_time.isoformat() if end_time else None
            }
            
            # 添加性能数据
            if perf_data:
                data['perf_data'] = perf_data
            
            self.logger.info(f"Updating status for test case {test_case_id}")
            
            response = requests.post(
                f'{self.api_url}/test-results/update-status',
                json=data,
                proxies={'http': None, 'https': None},
                timeout=5
            )
            
            if response.status_code != 200:
                self.logger.error(f"Error updating status: {response.text}")
            else:
                self.logger.info(f"Successfully updated test case {test_case_id} status to {status}")
                
        except Exception as e:
            self.logger.error(f"Error calling API: {e}", exc_info=True)
            
    def execute_test(self, test_id, command):
        """执行测试命令并收集结果"""
        timestamp = datetime.now()
        self.logger.info(f"Starting test execution for test case: {test_id} at {timestamp}")
        
        result_dir = os.path.join(self.base_dir, 'results', 
                                 f"{timestamp.strftime('%Y%m%d_%H%M%S')}_{test_id}")
        os.makedirs(result_dir, exist_ok=True)

        
        # 创建日志队列
        log_queue = queue.Queue()
        self.test_logs[test_id] = log_queue
        self.test_status[test_id] = 'running'
        
        def log_message(msg):
            """记录日志到文件和队列"""
            log_queue.put(msg)
            with open(f"{result_dir}/output.log", 'a') as f:
                f.write(f"{msg}\n")
        
        def run_test():
            try:
                # 启动性能监控线程
                monitor_thread = threading.Thread(
                    target=self.collect_performance_metrics,
                    args=(test_id, result_dir)
                )
                monitor_thread.daemon = True
                monitor_thread.start()
                
                log_message(f"Test started at: {datetime.now()}")
                log_message(f"Commands to execute:\n{command}")
                
                commands = command.split('\n')
                for i, cmd in enumerate(commands, 1):
                    cmd = cmd.strip()
                    if not cmd:
                        continue
                        
                    log_message(f"\nExecuting command {i}: {cmd}")
                    
                    process = subprocess.Popen(
                        cmd,
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        cwd=result_dir,
                        bufsize=1,
                        universal_newlines=True
                    )
                    
                    # 实时读取输出
                    while True:
                        stdout_line = process.stdout.readline()
                        stderr_line = process.stderr.readline()
                        
                        if not stdout_line and not stderr_line and process.poll() is not None:
                            break
                            
                        if stdout_line:
                            log_message(f"[STDOUT] {stdout_line.strip()}")
                        if stderr_line:
                            log_message(f"[STDERR] {stderr_line.strip()}")
                    
                    if process.returncode != 0:
                        raise Exception(f"Command failed with exit code {process.returncode}")
                
                log_message(f"\nTest completed successfully at: {datetime.now()}")
                self.test_status[test_id] = 'success'
                
                # 等待性能监控线程结束
                monitor_thread.join(timeout=5)
                self.update_test_status(test_id, timestamp, 'success', datetime.now(), self.perf_data.get(test_id))
                
            except Exception as e:
                error_msg = str(e)
                log_message(f"\nTest failed at: {datetime.now()}")
                log_message(f"Error: {error_msg}")
                self.test_status[test_id] = 'failed'
                self.update_test_status(test_id, timestamp, 'failed', datetime.now(), self.perf_data.get(test_id))
            finally:
                # 测试完成后清理日志队列
                if test_id in self.test_logs:
                    del self.test_logs[test_id] 
        
        # 启动测试线程
        thread = threading.Thread(target=run_test)
        thread.daemon = True
        thread.start()
        
        # 返回初始响应
        return {
            'status': 'running',
            'result_dir': result_dir,
            'timestamp': timestamp.isoformat()
        }
    
    def get_test_logs(self, test_id):
        """获取测试日志"""
        logs = []
        status = self.test_status.get(test_id, 'unknown')
        
        print(f"获取测试日志self.test_logs：{self.test_logs}")
        
        if test_id not in self.test_logs:
            # 如果没有实时日志，尝试从文件读取
            result_dir = self.find_result_dir(test_id)
            if result_dir and os.path.exists(f"{result_dir}/output.log"):
                with open(f"{result_dir}/output.log", 'r') as f:
                    logs = f.read().splitlines()
        else:
            # 从队列获取所有可用日志
            queue = self.test_logs[test_id]
            while not queue.empty():
                logs.append(queue.get_nowait())
        
        return {
            'status': status,
            'logs': logs
        }
    
    def find_result_dir(self, test_id):
        """查找最新的结果目录"""
        results_dir = os.path.join(self.base_dir, 'results')
        if not os.path.exists(results_dir):
            return None
            
        matching_dirs = [d for d in os.listdir(results_dir) if d.endswith(f"_{test_id}")]
        if not matching_dirs:
            return None
            
        # 返回最新的目录
        latest_dir = sorted(matching_dirs)[-1]
        return os.path.join(results_dir, latest_dir)
    
    def collect_performance_metrics(self, test_id, result_dir):
        """收集性能指标"""
        perf_data = {
            'cpu_data': [],
            'memory_data': [],
            'disk_io_data': [],  # 新增：磁盘 I/O 数据
            'network_io_data': []  # 新增：网络 I/O 数据
        }
        
        perf_file = os.path.join(result_dir, 'performance.json')
        
        # 初始化 I/O 计数器
        disk_io_start = psutil.disk_io_counters()
        net_io_start = psutil.net_io_counters()
        
        while self.test_status.get(test_id) == 'running':
            timestamp = datetime.now().isoformat()
            
            # 收集 CPU 使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            perf_data['cpu_data'].append({
                'timestamp': timestamp,
                'value': cpu_percent
            })
            
            # 收集内存使用情况
            memory = psutil.virtual_memory()
            perf_data['memory_data'].append({
                'timestamp': timestamp,
                'value': memory.percent
            })
            
            # 收集磁盘 I/O 使用情况
            disk_io = psutil.disk_io_counters()
            perf_data['disk_io_data'].append({
                'timestamp': timestamp,
                'read_bytes': disk_io.read_bytes - disk_io_start.read_bytes,
                'write_bytes': disk_io.write_bytes - disk_io_start.write_bytes
            })
            
            # 收集网络 I/O 使用情况
            net_io = psutil.net_io_counters()
            perf_data['network_io_data'].append({
                'timestamp': timestamp,
                'bytes_sent': net_io.bytes_sent - net_io_start.bytes_sent,
                'bytes_recv': net_io.bytes_recv - net_io_start.bytes_recv
            })
            
            # 实时保存性能数据到文件
            with open(perf_file, 'w') as f:
                json.dump(perf_data, f)
            
            time.sleep(1)
        
        self.perf_data[test_id] = perf_data
        return perf_data
    
    def run(self):
        while True:
            try:
                print("Waiting for connection...")
                conn, addr = self.sock.accept()
                print(f"Connection from {addr}")
                
                try:
                    data = conn.recv(1024).decode()
                    request = json.loads(data)
                    
                    if request['action'] == 'execute_test':
                        # 执行测试
                        result = self.execute_test(
                            request['test_id'],
                            request['command']
                        )
                        conn.sendall(json.dumps(result).encode())
                        
                    elif request['action'] == 'get_logs':
                        # 获取日志
                        result = self.get_test_logs(request['test_id'])
                        conn.sendall(json.dumps(result).encode())
                        
                    else:
                        conn.sendall(json.dumps({
                            'status': 'error',
                            'error': 'Unknown action'
                        }).encode())
                        
                except Exception as e:
                    print(f"Error handling request: {e}")
                    try:
                        conn.sendall(json.dumps({
                            'status': 'error',
                            'error': str(e)
                        }).encode())
                    except:
                        pass
                finally:
                    conn.close()
                    
            except Exception as e:
                print(f"Error accepting connection: {e}")

if __name__ == '__main__':
    server = TestServer()
    server.run()