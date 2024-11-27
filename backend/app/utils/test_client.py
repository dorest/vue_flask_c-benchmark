import socket
import json

def test_connection():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # 连接到服务器
        sock.connect(('localhost', 9999))
        
        # 发送测试请求
        request = {
            'action': 'execute_test',
            'test_id': 1,
            'config': {
                'test': 'demo',
                'duration': 30
            }
        }
        
        print(f"Sending request: {request}")
        sock.send(json.dumps(request).encode())
        
        # 接收响应
        response = sock.recv(1024).decode()
        result = json.loads(response)
        print(f"Received response: {result}")
        
        return True
    except Exception as e:
        print(f"Error: {str(e)}")
        return False
    finally:
        sock.close()

if __name__ == '__main__':
    test_connection() 