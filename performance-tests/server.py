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
import xml.etree.ElementTree as ET

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
        self.api_url = 'http://172.18.0.3:5000'  # 根据实际情况修改,docker inspect flask_app 查看下ip
        self.test_timestamps = {}  # 存储 test_case_id 对应的启动时间
        # 禁用代理设置
        os.environ['NO_PROXY'] = '*'
        os.environ['no_proxy'] = '*'
        self.perf_data = {}  # 新增：存储性能数据
        # 新增性能分析相关配置
        self.profiling_enabled = False  # 是否启用性能分析
        self.profiling_tools = {
            'perf': True,      # CPU性能分析
            'valgrind': True,  # 内存分析
            'callgrind': True  # 调用图分析
        }
        
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
            
    def execute_test(self, test_id, command, enable_profiling=False, profiling_config=None):
        """扩展执行测试函数，添加性能分析支持"""
        self.profiling_enabled = enable_profiling
        self.profiling_tools['perf'] = 'perf' == profiling_config['tools']
        self.profiling_tools['valgrind'] = 'valgrind' == profiling_config['tools']
        self.profiling_tools['callgrind'] = 'callgrind' == profiling_config['tools']
        timestamp = datetime.now()
        self.logger.info(f"Starting test execution for test case: {test_id} at {timestamp}")
        
        result_dir = os.path.join(self.base_dir, 'results', 
                                 f"{timestamp.strftime('%Y%m%d_%H%M%S')}_{test_id}")
        os.makedirs(result_dir, exist_ok=True)
        
        # 创建性能分析目录
        profile_dir = os.path.join(result_dir, 'profile')
        os.makedirs(profile_dir, exist_ok=True)

        # 保持原有的日志队列设置
        log_queue = queue.Queue()
        self.test_logs[test_id] = log_queue
        self.test_status[test_id] = 'running'

        def log_message(msg):
            """保持原有的日志记录功能"""
            log_queue.put(msg)
            with open(f"{result_dir}/output.log", 'a') as f:
                f.write(f"{msg}\n")

        def xml_to_text(xml_file, text_file):
            """将 valgrind XML 转换为可读的文本格式"""
            import xml.etree.ElementTree as ET
            
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()
                
                with open(text_file, 'w') as f:
                    # 写入头部信息
                    for line in root.findall('.//preamble/line'):
                        if line.text:
                            f.write(f"{line.text}\n")
                    f.write("\n")
                    
                    # 写入命令信息
                    cmd = root.find('.//args/argv/exe')
                    args = root.findall('.//args/argv/arg')
                    if cmd is not None and cmd.text:
                        cmd_str = cmd.text
                        for arg in args:
                            if arg.text:
                                cmd_str += f" {arg.text}"
                        f.write(f"Command: {cmd_str}\n\n")
                    
                    # 写入运行状态
                    final_status = root.findall('.//status')[-1]
                    if final_status is not None:
                        state = final_status.find('state')
                        time = final_status.find('time')
                        if state is not None and time is not None:
                            f.write(f"Status: {state.text} in {time.text}\n\n")
                    
                    # 写入错误信息
                    for error in root.findall('.//error'):
                        # 获取错误类型和描述
                        kind = error.find('kind')
                        xwhat = error.find('xwhat/text')
                        
                        if kind is not None and kind.text:
                            f.write(f"\n==ERROR== {kind.text}\n")
                        if xwhat is not None and xwhat.text:
                            f.write(f"==ERROR== {xwhat.text}\n")
                        
                        # 写入调用栈
                        stack = error.find('stack')
                        if stack is not None:
                            f.write("==ERROR== Stack trace:\n")
                            for frame in stack.findall('frame'):
                                fn = frame.find('fn')
                                file = frame.find('file')
                                line = frame.find('line')
                                
                                if fn is not None and fn.text:
                                    frame_info = f"==ERROR==    at {fn.text}"
                                    if file is not None and file.text:
                                        frame_info += f" ({file.text}"
                                        if line is not None and line.text:
                                            frame_info += f":{line.text}"
                                        frame_info += ")"
                                    f.write(f"{frame_info}\n")
                        
                        f.write("\n")
                    
                    # 如果没有错误信息
                    if not root.findall('.//error'):
                        f.write("No memory leaks or errors detected.\n")
                        
                return True
            except Exception as e:
                print(f"Error converting XML to text: {e}")
                return False
        def generate_memory_svg(xml_file, svg_file):
            """将 valgrind XML 输出转换为内存泄漏可视化图"""
            import xml.etree.ElementTree as ET
            import graphviz
            
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()
                
                # 检查是否有错误信息
                errors = root.findall('.//error')
                if not errors:
                    print("No memory leaks detected, skipping SVG generation")
                    return False
                    
                # 创建有向图
                dot = graphviz.Digraph(comment='Memory Leak Analysis')
                dot.attr(rankdir='TB')  # 从上到下的布局
                
                has_valid_error = False  # 跟踪是否有有效的错误信息
                
                # 遍历所有错误
                for error in errors:
                    kind = error.find('kind')
                    xwhat = error.find('xwhat/text')
                    
                    if kind is not None and xwhat is not None and kind.text and xwhat.text:
                        has_valid_error = True
                        # 创建错误节点
                        error_id = f"error_{error.find('unique').text}"
                        error_label = f"{kind.text}\n{xwhat.text}"
                        dot.node(error_id, error_label, 
                                shape='box', 
                                style='filled', 
                                fillcolor='red',
                                fontcolor='white')
                        
                        # 处理调用栈
                        stack = error.find('stack')
                        if stack is not None:
                            prev_node = error_id
                            for i, frame in enumerate(stack.findall('frame')):
                                fn = frame.find('fn')
                                file = frame.find('file')
                                line = frame.find('line')
                                
                                if fn is not None and fn.text:
                                    frame_id = f"{error_id}_frame_{i}"
                                    
                                    # 构建帧标签
                                    frame_label = fn.text
                                    if file is not None and file.text:
                                        frame_label += f"\n{file.text}"
                                        if line is not None and line.text:
                                            frame_label += f":{line.text}"
                                    
                                    # 添加帧节点
                                    dot.node(frame_id, frame_label, 
                                        shape='box',
                                        style='filled',
                                        fillcolor='lightblue')
                                    
                                    # 连接节点
                                    dot.edge(prev_node, frame_id)
                                    prev_node = frame_id
                
                # 只在有有效错误信息时生成 SVG
                if has_valid_error:
                    dot.render(svg_file, format='svg', cleanup=True)
                    return True
                else:
                    print("No valid memory leak information found, skipping SVG generation")
                    return False
                
            except Exception as e:
                print(f"Error generating memory SVG: {e}")
                return False

        def run_profiling(cmd):
            """执行性能分析"""
            profiling_results = {}
            
            if enable_profiling:
                try:
                    # 1. perf 分析
                    if self.profiling_tools['perf']:
                        perf_data = os.path.join(profile_dir, 'perf.data')
                        perf_cmd = f"perf record -F 99 -g -o {perf_data} -- {cmd}"
                        subprocess.run(perf_cmd, shell=True, check=True)
                        
                        # 生成火焰图
                        subprocess.run(f"perf script -i {perf_data} > {profile_dir}/perf.script", shell=True)
                        subprocess.run(f"/root/FlameGraph/stackcollapse-perf.pl {profile_dir}/perf.script > {profile_dir}/perf.folded", shell=True)
                        subprocess.run(f"/root/FlameGraph/flamegraph.pl {profile_dir}/perf.folded > {profile_dir}/flamegraph.svg", shell=True)
                        
                        # 生成 perf report 输出
                        subprocess.run(f"perf report -i {perf_data} > {profile_dir}/perf_report.txt", shell=True)
                        
                        # 生成 perf annotate 输出
                        subprocess.run(f"perf annotate -i {perf_data} > {profile_dir}/perf_annotate.txt", shell=True)
                        
                        # 收集所有性能分析结果的路径
                        profiling_results['perf'] = {
                            'flamegraph': f"{profile_dir}/flamegraph.svg",
                            'report': f"{profile_dir}/perf_report.txt",
                            'annotate': f"{profile_dir}/perf_annotate.txt",
                            'raw_data': perf_data,
                            'script': f"{profile_dir}/perf.script",
                            'folded': f"{profile_dir}/perf.folded"
                        }

                    # 2. Valgrind 内存分析
                    if self.profiling_tools['valgrind']:
                        valgrind_log = os.path.join(profile_dir, 'valgrind.log')
                        valgrind_xml = os.path.join(profile_dir, 'valgrind.xml')
                        
                        # 只生成 XML 输出
                        valgrind_cmd = f"valgrind --tool=memcheck --leak-check=full --show-leak-kinds=all --xml=yes --xml-file={valgrind_xml} {cmd}"
                        subprocess.run(valgrind_cmd, shell=True, check=True)
                        
                        # 从 XML 生成文本日志
                        if xml_to_text(valgrind_xml, valgrind_log):
                            profiling_results['valgrind'] = valgrind_log
                        
                        # 生成内存分析图
                        heap_svg = os.path.join(profile_dir, 'heap')
                        if generate_memory_svg(valgrind_xml, heap_svg):
                            profiling_results['heap'] = heap_svg + '.svg'

                    # 3. Callgrind 调用图分析
                    if self.profiling_tools['callgrind']:
                        callgrind_out = os.path.join(profile_dir, 'callgrind.out')
                        callgrind_cmd = f"valgrind --tool=callgrind --callgrind-out-file={callgrind_out} {cmd}"
                        subprocess.run(callgrind_cmd, shell=True, check=True)
                        
                        # 生成调用图可视化
                        subprocess.run(f"gprof2dot -f callgrind {callgrind_out} | dot -Tsvg -o {profile_dir}/callgrind.svg", shell=True)
                        profiling_results['callgrind'] = f"{profile_dir}/callgrind.svg"

                except Exception as e:
                    log_message(f"Profiling error: {str(e)}")
                    
            return profiling_results

        def run_test():
            try:
                # 保持原有的性能监控线程
                monitor_thread = threading.Thread(
                    target=self.collect_performance_metrics,
                    args=(test_id, result_dir)
                )
                monitor_thread.daemon = True
                monitor_thread.start()

                log_message(f"Test started at: {datetime.now()}")
                log_message(f"Commands to execute:\n{command}")

                commands = command.split('\n')
                profiling_results = {}

                for i, cmd in enumerate(commands, 1):
                    cmd = cmd.strip()
                    if not cmd:
                        continue

                    log_message(f"\nExecuting command {i}: {cmd}")
                    
                    # 执行性能分析
                    if enable_profiling:
                        prof_results = run_profiling(cmd)
                        profiling_results['tools'] = self.profiling_tools
                        profiling_results[f"command_{i}"] = prof_results
                    
                    # 保持原有的命令执行逻辑
                    process = subprocess.Popen(
                        cmd,
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        cwd=result_dir,
                        bufsize=1,
                        universal_newlines=True
                    )
                    
                    # 保持原有的输出处理逻辑
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

                # 保存性能分析结果
                if profiling_results:
                    with open(os.path.join(profile_dir, 'profiling_results.json'), 'w') as f:
                        json.dump(profiling_results, f)

                log_message(f"\nTest completed successfully at: {datetime.now()}")
                self.test_status[test_id] = 'success'
                
                # 等待性能监控线程结束
                monitor_thread.join(timeout=5)
                
                # 更新测试状态时包含性能分析结果
                perf_data = self.perf_data.get(test_id, {})
                if profiling_results:
                    perf_data['profiling'] = profiling_results
                print(f"=============perf_data: {perf_data}==============")
                self.update_test_status(test_id, timestamp, 'success', datetime.now(), perf_data)
                
            except Exception as e:
                error_msg = str(e)
                log_message(f"\nTest failed at: {datetime.now()}")
                log_message(f"Error: {error_msg}")
                self.test_status[test_id] = 'failed'
                self.update_test_status(test_id, timestamp, 'failed', datetime.now(), self.perf_data.get(test_id))
            finally:
                if test_id in self.test_logs:
                    del self.test_logs[test_id]

        # 启动测试线程
        thread = threading.Thread(target=run_test)
        thread.daemon = True
        thread.start()
        
        return {
            'status': 'running',
            'result_dir': result_dir,
            'timestamp': timestamp.isoformat(),
            'profiling_enabled': enable_profiling
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
                            request['command'],
                            request['enable_profiling'],
                            request['profiling_config']
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