import socket
import json
import logging
import time
from datetime import datetime  
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import sys
from pathlib import Path
sys.path.append(str(Path("performance-tests").resolve()))
import nameconfig

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestClient:
    def __init__(self, host='172.17.0.1', port=9999, timeout=5, max_retries=3):
        self.host = host #主机在docker容器中的ip地址，ifconfig docker0查看
        self.port = port
        self.timeout = timeout
        self.max_retries = max_retries
        self.api_url = f'http://{nameconfig.FLASK_APP_IP}:5000'  # 根据实际情况修改,docker inspect flask_app 查看下ip
        logger.info(f"TestClient initialized with host={host}, port={port}")
        
        # 添加调度器
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
    
    def execute_test(self, test_id, command, enable_profiling, profiling_config):
        """执行测试用例"""
        logger.debug(f"Executing test {test_id} with command: {command}")
        return self._send_request({
            'action': 'execute_test',
            'test_id': test_id,
            'command': command,
            'enable_profiling': enable_profiling,
            'profiling_config': profiling_config
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
            
    def handle_message(self, message):
        """处理接收到的消息"""
        try:
            action = message.get('action')
            if action == 'add_schedule':
                return self.add_schedule(message)
            elif action == 'toggle_schedule':
                return self.toggle_schedule(message)
            elif action == 'delete_schedule':
                return self.delete_schedule(message)
            else:
                return {
                    'status': 'error',
                    'message': f'Unknown action: {action}'
                }
            
        except Exception as e:
            print(f"Error handling message: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    def add_schedule(self, message):
        """添加定时任务"""
        try:
            task_id = message.get('task_id')
            test_id = message.get('test_id')
            command = message.get('command')
            enable_profiling = message.get('enable_profiling', False)
            profiling_config = message.get('profiling_config', {})
            cron = message.get('cron')

            self.scheduler.add_job(
                func=self.run_scheduled_test,
                trigger=CronTrigger.from_crontab(cron),
                id=f'task_{task_id}',
                args=[task_id, {
                    'id': test_id,
                    'command': command,
                    'enable_profiling': enable_profiling,
                    'profiling_config': profiling_config
                }],
                replace_existing=True
            )
            
            return {
                'status': 'success',
                'message': 'Schedule added successfully'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }

    def toggle_schedule(self, message):
        """切换定时任务状态"""
        try:
            task_id = message.get('task_id')
            enabled = message.get('enabled')
            job_id = f'task_{task_id}'

            # 查找并删除现有任务
            existing_job = self.scheduler.get_job(job_id)
            if existing_job:
                logger.info(f"Found existing job: {existing_job.id}")
                self.scheduler.remove_job(job_id)
                logger.info(f"Removed existing job: {job_id}")
            else:
                logger.info(f"No existing job found with ID: {job_id}")

            if enabled:
                test_id = message.get('test_id')
                command = message.get('command')
                enable_profiling = message.get('enable_profiling', False)
                profiling_config = message.get('profiling_config', {})
                cron = message.get('cron')

                self.scheduler.add_job(
                    func=self.run_scheduled_test,
                    trigger=CronTrigger.from_crontab(cron),
                    id=job_id,
                    args=[task_id, {
                        'id': test_id,
                        'command': command,
                        'enable_profiling': enable_profiling,
                        'profiling_config': profiling_config
                    }],
                    replace_existing=True
                )
                
                job = self.scheduler.get_job(job_id)
                if job:
                    logger.info(f"Job {job_id} successfully added, next run at: {job.next_run_time}")
                else:
                    logger.error(f"Failed to add job {job_id}")
                    
                logger.info(f"======all existing jobs: { self.scheduler.get_jobs()}")

            return {
                'status': 'success',
                'message': f"Task {'enabled' if enabled else 'disabled'} successfully"
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }

    def delete_schedule(self, message):
        """删除定时任务"""
        try:
            task_id = message.get('task_id')
            job_id = f'task_{task_id}'

            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)

            return {
                'status': 'success',
                'message': 'Schedule deleted successfully'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }

    # def run_scheduled_test(self, task_id, test_case):
    #     """执行定时任务"""
    #     try:
    #         # 使用现有的测试执行逻辑
    #         response = self.execute_test(
    #             test_id=test_case['id'],
    #             command=test_case['command'],
    #             enable_profiling=test_case['enable_profiling'],
    #             profiling_config=test_case['profiling_config']
    #         )
    #         if 'error' in response:
    #             return {
    #                 'code': 500,
    #                 'message': response['error']
    #             }
                
    #         # 创建测试结果记录
    #         result = TestResult(
    #             test_case_id=test_case['test_id'],
    #             start_time=datetime.now(),
    #             status='running',
    #             result_dir=response['result_dir'],
    #             has_profile=test_case['enable_profiling']
    #         )
    #         db.session.add(result)
    #         db.session.commit()
    #         return {
    #             'status': 'success',
    #             'message': 'Test executed successfully'
    #         }
    #     except Exception as e:
    #         return {
    #             'status': 'error',
    #             'message': str(e)
    #         }
    def run_scheduled_test(self, task_id, test_case):
        """执行定时任务"""
        try:
            # 使用现有的 execute_test_case 接口
            response = requests.post(
                f'{self.api_url}/test-cases/{test_case["id"]}/execute',
                proxies={'http': None, 'https': None},
                timeout=5
            )

            if response.status_code != 200:
                print(f"Error executing test: {response.text}")  # 添加日志
                return {
                    'status': 'error',
                    'message': response.json().get('message', '执行测试失败')
                }

            return {
                'status': 'success',
                'message': '测试已启动',
                'data': response.json().get('data')
            }

        except Exception as e:
            print(f"Exception in run_scheduled_test: {str(e)}")  # 添加日志
            return {
                'status': 'error',
                'message': str(e)
            }
            
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
