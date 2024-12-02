import socket
import json

class TestClient:
    def __init__(self, host='localhost', port=9999):
        self.host = host
        self.port = port
    
    def execute_test(self, test_id, command):
        """执行测试用例"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((self.host, self.port))
            request = {
                'action': 'execute_test',
                'test_id': test_id,
                'command': command
            }
            
            # 发送请求
            sock.send(json.dumps(request).encode())
            
            # 接收响应
            response = sock.recv(1024).decode()
            return json.loads(response)
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
        finally:
            sock.close()
    
    def check_connection(self):
        """检查与测试服务器的连接"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((self.host, self.port))
            return True
        except:
            return False
        finally:
            sock.close()