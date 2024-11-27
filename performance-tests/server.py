import socket
import json
import subprocess
import os
from datetime import datetime

class TestServer:
    def __init__(self):
        self.base_dir = '/root/flask-vue/performance-tests'
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(('localhost', 9999))
        self.sock.listen(1)
        
    def run(self):
        while True:
            conn, addr = self.sock.accept()
            try:
                data = conn.recv(1024).decode()
                request = json.loads(data)
                
                if request['action'] == 'execute_test':
                    result = self.execute_test(request['test_id'], request['config'])
                    conn.send(json.dumps(result).encode())
                    
            except Exception as e:
                conn.send(json.dumps({'error': str(e)}).encode())
            finally:
                conn.close()
    
    def execute_test(self, test_id, config):
        # 创建结果目录
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_dir = os.path.join(self.base_dir, 'results', f'{timestamp}_{test_id}')
        os.makedirs(result_dir, exist_ok=True)
        
        # 执行测试程序
        cmd = [
            os.path.join(self.base_dir, 'bin/test_program'),
            '--config', json.dumps(config),
            '--output', result_dir
        ]
        
        process = subprocess.Popen(cmd)
        
        return {
            'status': 'started',
            'result_dir': result_dir
        }

if __name__ == '__main__':
    server = TestServer()
    server.run()
