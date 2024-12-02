import socket
import json
import subprocess
import os
from datetime import datetime
import threading

class TestServer:
    def __init__(self):
        self.base_dir = '/root/flask-vue/performance-tests'
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('0.0.0.0', 9999))
        self.sock.listen(1)
        print("Test server started on 0.0.0.0:9999")
        
    def execute_test(self, test_id, command):
        """执行测试命令并收集结果"""
        # 创建结果目录
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_dir = os.path.join(self.base_dir, 'results', f'{timestamp}_{test_id}')
        os.makedirs(result_dir, exist_ok=True)
        
        # 记录开始时间
        with open(f"{result_dir}/status.txt", 'w') as f:
            f.write(f"Test started at: {datetime.now()}\n")
            f.write(f"Commands to execute:\n{command}\n")
        
        try:
            # 分行执行命令
            commands = command.split('\n')
            for i, cmd in enumerate(commands, 1):
                cmd = cmd.strip()
                if not cmd:
                    continue
                    
                print(f"Executing command {i}: {cmd}")
                
                # 执行命令并收集输出
                process = subprocess.Popen(
                    cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=result_dir
                )
                
                stdout, stderr = process.communicate()
                
                # 记录命令输出
                with open(f"{result_dir}/output.log", 'a') as f:
                    f.write(f"\n=== Command {i}: {cmd} ===\n")
                    f.write("=== STDOUT ===\n")
                    f.write(stdout.decode())
                    f.write("\n=== STDERR ===\n")
                    f.write(stderr.decode())
                    f.write("\n")
                
                if process.returncode != 0:
                    raise Exception(f"Command failed with exit code {process.returncode}")
            
            # 记录成功状态
            with open(f"{result_dir}/status.txt", 'a') as f:
                f.write(f"\nTest completed successfully at: {datetime.now()}\n")
                
            return {
                'status': 'success',
                'result_dir': result_dir
            }
            
        except Exception as e:
            # 记录失败状态
            with open(f"{result_dir}/status.txt", 'a') as f:
                f.write(f"\nTest failed at: {datetime.now()}\n")
                f.write(f"Error: {str(e)}\n")
            
            return {
                'status': 'error',
                'error': str(e),
                'result_dir': result_dir
            }
    
    def run(self):
        while True:
            conn, addr = self.sock.accept()
            try:
                print(f"Connection from {addr}")
                data = conn.recv(1024).decode()
                request = json.loads(data)
                
                if request['action'] == 'execute_test':
                    # 在新线程中执行测试
                    thread = threading.Thread(
                        target=lambda: self.handle_test_request(request, conn)
                    )
                    thread.start()
                else:
                    conn.send(json.dumps({
                        'status': 'error',
                        'error': 'Unknown action'
                    }).encode())
            except Exception as e:
                print(f"Error handling request: {e}")
                try:
                    conn.send(json.dumps({
                        'status': 'error',
                        'error': str(e)
                    }).encode())
                except:
                    pass
            finally:
                conn.close()
    
    def handle_test_request(self, request, conn):
        try:
            result = self.execute_test(
                request['test_id'],
                request['command']
            )
            conn.send(json.dumps(result).encode())
        except Exception as e:
            conn.send(json.dumps({
                'status': 'error',
                'error': str(e)
            }).encode())

if __name__ == '__main__':
    server = TestServer()
    server.run()