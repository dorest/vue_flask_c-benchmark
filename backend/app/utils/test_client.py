import socket
import json
import logging
import time

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestClient:
    def __init__(self, host='172.17.0.1', port=9999, timeout=5, max_retries=3):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.max_retries = max_retries
        logger.info(f"TestClient initialized with host={host}, port={port}")
    
    def execute_test(self, test_id, command):
        """执行测试用例"""
        logger.debug(f"Executing test {test_id} with command: {command}")
        return self._send_request({
            'action': 'execute_test',
            'test_id': test_id,
            'command': command
        })
    
    def get_logs(self, test_id):
        """获取测试日志"""
        logger.debug(f"Getting logs for test {test_id}")
        return self._send_request({
            'action': 'get_logs',
            'test_id': test_id
        })
    
    def check_connection(self):
        """检查与测试服务器的连接"""
        logger.debug(f"Checking connection to {self.host}:{self.port}")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        try:
            sock.connect((self.host, self.port))
            logger.info("Connection successful")
            return True
        except socket.timeout:
            logger.error(f"Connection timeout after {self.timeout} seconds")
            return False
        except ConnectionRefusedError:
            logger.error(f"Connection refused to {self.host}:{self.port}")
            return False
        except Exception as e:
            logger.error(f"Connection check failed: {str(e)}")
            return False
        finally:
            sock.close()
    
    def _send_request(self, request_data):
        """发送请求到测试服务器，支持重试"""
        retry_count = 0
        last_error = None
        
        while retry_count < self.max_retries:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            
            try:
                logger.debug(f"Attempt {retry_count + 1}/{self.max_retries} "
                           f"to connect to {self.host}:{self.port}")
                
                # 尝试连接
                sock.connect((self.host, self.port))
                logger.debug("Connection established")
                
                # 发送请求
                request_str = json.dumps(request_data)
                logger.debug(f"Sending request: {request_str}")
                sock.send(request_str.encode())
                
                # 接收响应
                response = sock.recv(4096).decode()
                logger.debug(f"Received response: {response}")
                
                return json.loads(response)
                
            except socket.timeout:
                last_error = f"Connection timeout after {self.timeout} seconds"
                logger.error(last_error)
            except ConnectionRefusedError:
                last_error = f"Connection refused to {self.host}:{self.port}"
                logger.error(last_error)
            except json.JSONDecodeError as e:
                last_error = f"Invalid JSON response: {str(e)}"
                logger.error(last_error)
            except Exception as e:
                last_error = str(e)
                logger.error(f"Unexpected error: {last_error}", exc_info=True)
            finally:
                sock.close()
            
            retry_count += 1
            if retry_count < self.max_retries:
                wait_time = retry_count * 2  # 指数退避
                logger.info(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
        
        return {
            'status': 'error',
            'error': f"Failed after {self.max_retries} attempts. Last error: {last_error}"
        }