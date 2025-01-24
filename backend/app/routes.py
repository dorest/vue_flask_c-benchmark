from flask import Blueprint, request, jsonify, make_response
from .models import TestCase, TestResult, ScheduledTask
from .services.perf_service import PerfService
from . import db, scheduler
from .services.report_service import ReportService
from .utils.test_client import TestClient
from datetime import datetime, timedelta
from flask_cors import cross_origin
import os
from flask import current_app
from . import sock
import json

api_bp = Blueprint('api', __name__)

test_client = TestClient()

active_connections = set()

@sock.route('/ws/test-status')
def test_status_socket(ws):
    """WebSocket 连接处理"""
    active_connections.add(ws)
    try:
        while True:
            # 保持连接活跃
            ws.receive()
    except Exception:
        pass
    finally:
        active_connections.remove(ws)

def notify_clients(data):
    """向所有连接的客户端发送更新"""
    dead_connections = set()
    for ws in active_connections:
        try:
            current_app.logger.info(f"Sending data to client: {data}")
            ws.send(json.dumps(data))
        except Exception:
            dead_connections.add(ws)
    
    # 清理断开的连接
    active_connections.difference_update(dead_connections)

@api_bp.route('/test-cases', methods=['GET','POST'])
def create_test_case():
    if request.method == 'GET':
        cases = TestCase.query.all()
        return jsonify([{
            'id': case.id,
            'name': case.name,
            'description': case.description,
            'command': case.command,
            'parameters': case.parameters,
            'created_at': case.created_at.isoformat() if case.created_at else None,
            'enable_profiling': case.enable_profiling,
            'profiling_config': case.profiling_config
        } for case in cases])
        
    elif request.method == 'POST':
        data = request.json
        test_case = TestCase(
            name=data['name'],
            description=data.get('description'),
            command=data['command'],
            parameters=data.get('parameters', {}),
            enable_profiling=data.get('enable_profiling', False),
            profiling_config=data.get('profiling_config', {})
        )
        db.session.add(test_case)
        db.session.commit()
        return jsonify({
            'id': test_case.id,
            'name': test_case.name,
            'description': test_case.description,
            'command': test_case.command,
            'parameters': test_case.parameters,
            'created_at': test_case.created_at.isoformat(),
            'message': '创建成功',
            'enable_profiling': test_case.enable_profiling,
            'profiling_config': test_case.profiling_config
        }), 201


@api_bp.route('/test-cases/<int:id>', methods=['DELETE'])
def delete_test_case(id):
    test_case = TestCase.query.get_or_404(id)
    try:
        # 删除相关的定时任务
        scheduled_tasks = ScheduledTask.query.filter_by(test_case_id=id).all()
        for task in scheduled_tasks:
            try:
                scheduler.remove_job(f'task_{task.id}')
            except:
                pass  # 如果任务不存在，忽略错误
            db.session.delete(task)
        
        # 删除测试结果
        TestResult.query.filter_by(test_case_id=id).delete()
        
        # 删除测试用例
        db.session.delete(test_case)
        db.session.commit()
        
        return jsonify({
            'message': '删除成功',
            'id': id
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': str(e),
            'message': '删除失败'
        }), 500
        
@api_bp.route('/test-cases/<int:id>', methods=['PUT'])
def update_test_case(id):
    test_case = TestCase.query.get_or_404(id)
    data = request.json
    
    try:
        test_case.name = data.get('name', test_case.name)
        test_case.description = data.get('description', test_case.description)
        test_case.command = data.get('command', test_case.command)
        test_case.parameters = data.get('parameters', test_case.parameters)
        test_case.enable_profiling = data.get('enable_profiling', test_case.enable_profiling)
        test_case.profiling_config = data.get('profiling_config', test_case.profiling_config)
        
        db.session.commit()
        
        return jsonify({
            'id': test_case.id,
            'name': test_case.name,
            'description': test_case.description,
            'command': test_case.command,
            'parameters': test_case.parameters,
            'message': '更新成功',
            'enable_profiling': test_case.enable_profiling,
            'profiling_config': test_case.profiling_config
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': str(e),
            'message': '更新失败'
        }), 500


@api_bp.route('/test-results/<int:id>/export', methods=['GET'])
def export_test_report(id):
    result = TestResult.query.get_or_404(id)
    
    # 使用报告服务生成PDF
    report_data = ReportService.generate_test_report(result)
    
    response = make_response(report_data)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=test_report_{id}.pdf'
    
    return response

@api_bp.route('/test-results', methods=['GET'])
def get_test_results():
    try:
        test_case_id = request.args.get('test_case_id', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        query = TestResult.query
        
        if test_case_id:
            query = query.filter_by(test_case_id=test_case_id)
        if start_date:
            query = query.filter(TestResult.start_time >= start_date)
        if end_date:
            query = query.filter(TestResult.end_time <= end_date)
            
        results = query.order_by(TestResult.start_time.desc()).all()
        
        # 即使没有数据也返回空列表，而不是404
        return jsonify({
            'code': 200,
            'data': [{
                'id': result.id,
                'test_case_id': result.test_case_id,
                'test_case_name': result.test_case.name,
                'start_time': result.start_time.isoformat() if result.start_time else None,
                'end_time': result.end_time.isoformat() if result.end_time else None,
                'status': result.status,
                'flamegraph_path': result.flamegraph_path
            } for result in results],
            'message': '获取成功'
        })
    except Exception as e:
        print(f"Error fetching test results: {str(e)}")  # 添加日志
        return jsonify({
            'code': 500,
            'data': [],
            'message': str(e)
        }), 500

@api_bp.route('/test-results/<int:id>/details', methods=['GET'])
@cross_origin()
def get_test_result_details(id):
    try:
        result = TestResult.query.get_or_404(id)
        
        # 获取性能数据
        perf_data = result.perf_data or {}
        
        # 获取日志
        logs = []
        if result.result_dir:
            log_path = os.path.join(result.result_dir, 'output.log')
            if os.path.exists(log_path):
                with open(log_path, 'r') as f:
                    logs = f.read().splitlines()
        
        # 构造返回数据
        response_data = {
            'code': 200,
            'data': {
                'cpu_data': perf_data.get('cpu_data', []),
                'memory_data': perf_data.get('memory_data', []),

                'disk_io_data': perf_data.get('disk_io_data', []),
                'network_io_data': perf_data.get('network_io_data', []),
                'benchmark_data': [
                    {
                        'metric': 'CPU平均使用率',
                        'current': calculate_average(perf_data.get('cpu_data', [])),
                        'baseline': 50,
                        'diff': calculate_diff(calculate_average(perf_data.get('cpu_data', [])), 50)
                    },
                    {
                        'metric': '内存平均使用',
                        'current': calculate_average(perf_data.get('memory_data', [])),
                        'baseline': 500,
                        'diff': calculate_diff(calculate_average(perf_data.get('memory_data', [])), 500)
                    }

                ],
                'logs': logs,  # 添加日志到详情中
                'flamegraph_path': result.flamegraph_path
            },
            'message': '获取成功'
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Error fetching test result details: {str(e)}")
        return jsonify({
            'code': 500,
            'data': {
                'cpu_data': [],
                'memory_data': [],
                'disk_io_data': [],
                'network_io_data': [],
                'benchmark_data': [],
                'logs': [],
                'flamegraph_path': None
            },
            'message': str(e)
        }), 500

@api_bp.route('/test-cases/<int:id>/execute', methods=['POST'])
@cross_origin()
def execute_test_case(id):
    try:
        test_case = TestCase.query.get_or_404(id)
        
        # 通过 Socket 客户端执行测试
        
        response = test_client.execute_test(
            test_id=id,
            command=test_case.command,
            enable_profiling=test_case.enable_profiling,
            profiling_config=test_case.profiling_config
        )
        
        if 'error' in response:
            return jsonify({
                'code': 500,
                'message': response['error']
            }), 500
            
        # 创建测试结果记录
        result = TestResult(
            test_case_id=id,
            start_time=datetime.now(),
            status='running',
            result_dir=response['result_dir'],
            has_profile = test_case.enable_profiling
        )
        db.session.add(result)
        db.session.commit()
        
        notify_clients({
                'type': 'new_result',
                'test_id': result.id 
            })
        return jsonify({
            'code': 200,
            'message': '测试已启动',
            'data': {
                'result_id': result.id
            }
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': str(e)
        }), 500

@api_bp.route('/test-results/<int:id>/logs', methods=['GET'])
@cross_origin()
def get_test_logs(id):
    try:
        result = TestResult.query.get_or_404(id)
        
        # 从测试服务器获取日志
        response = test_client.get_logs(result.test_case_id, result.result_dir)
        
        # 如果测试已完成，更新状态
        if response.get('status') == 'completed':
            result.status = 'success' if response.get('success') else 'failed'
            result.end_time = datetime.now()
            db.session.commit()
        
        return jsonify({
            'code': 200,
            'data': {
                'logs': response.get('logs', []),
                'status': result.status,
                'end_time': result.end_time.isoformat() if result.end_time else None
            }
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': str(e)
        }), 500

@api_bp.route('/test-results/<int:id>', methods=['DELETE'])
@cross_origin()
def delete_test_result(id):
    try:
        result = TestResult.query.get_or_404(id)
        
        # 将宿主机路径转换为容器内路径
        container_path = result.result_dir.replace(
            '/root/flask-vue',
            '/usr/src/app'
        ) if result.result_dir else None
        
        # 删除结果目录（如果存在）
        if container_path and os.path.exists(container_path):
            import shutil
            shutil.rmtree(container_path)
        
        # 删除数据库记录
        db.session.delete(result)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '删除成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': str(e)
        }), 500

@api_bp.route('/test-results/update-status', methods=['POST'])
def update_test_status():
    try:
        data = request.get_json()
        test_case_id = data['test_case_id']
        start_timestamp = datetime.fromisoformat(data['start_timestamp'])
        perf_data = data.get('perf_data')  # 新增：获取性能数据
        
        current_app.logger.info(f"Received start_timestamp: {start_timestamp}")
        if perf_data:
            current_app.logger.info("Received performance data")
        
        # 查找对应时间戳的测试结果
        results = TestResult.query.filter(
            TestResult.test_case_id == test_case_id,
            TestResult.status == 'running'
        ).all()
        
        # 打印所有找到的运行中的测试结果
        for r in results:
            current_app.logger.info(
                f"Found running test - ID: {r.id}, "
                f"test_case_id: {r.test_case_id}, "
                f"start_time: {r.start_time}, "
                f"time_diff: {abs((r.start_time - start_timestamp).total_seconds())} seconds"
            )
        
        # 查找对应时间戳的测试结果
        result = TestResult.query.filter(
            TestResult.test_case_id == test_case_id,
            TestResult.start_time >= start_timestamp - timedelta(seconds=5),
            TestResult.start_time <= start_timestamp + timedelta(seconds=5),
            TestResult.status == 'running'
        ).order_by(TestResult.start_time.desc()).first()
        
        if result:
            current_app.logger.info(
                f"Updating test result - ID: {result.id}, "
                f"Previous status: {result.status}, "
                f"New status: {data['status']}"
            )
            result.status = data['status']
            if data.get('end_time'):
                result.end_time = datetime.fromisoformat(data['end_time'])
            if perf_data:  # 新增：更新性能数据
                result.perf_data = perf_data
                current_app.logger.info(f"Updated performance data for test {result.id}")
            
            db.session.commit()
            
            # 通知所有客户端状态更新，包含性能数据
            notify_data = {
                'type': 'update_status',
                'test_id': result.id,
                'status': result.status,
                'end_time': result.end_time.isoformat() if result.end_time else None
            }

            
            notify_clients(notify_data)
            
            return jsonify({
                'code': 200,
                'message': 'Status updated successfully'
            })
        else:
            return jsonify({
                'code': 404,
                'message': 'No matching test result found'
            }), 404
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating test status: {str(e)}")
        return jsonify({
            'code': 500,
            'message': str(e)
        }), 500
        
# 辅助函数：计算平均值
def calculate_average(data_list):
    if not data_list:
        return 0
    values = [item.get('value', 0) for item in data_list]
    return sum(values) / len(values)

# 辅助函数：计算差异百分比
def calculate_diff(current, baseline):
    if baseline == 0:
        return 0
    return ((current - baseline) / baseline) * 100

@api_bp.route('/test-results/<int:result_id>/profile', methods=['GET'])
def get_test_profile(result_id):
    """获取测试的性能分析数据"""
    try:
        result = TestResult.query.get_or_404(result_id)
        # 将宿主机路径转换为容器内路径
        # 从 /root/flask-vue/performance-tests/results/... 
        # 转换为 /usr/src/app/performance-tests/results/...
        container_path = result.result_dir.replace(
            '/root/flask-vue', 
            '/usr/src/app'
        )
        
        result_dir = os.path.join(container_path, 'profile')
        
        profile_data = {
            'result_dir': result_dir,
            'has_profile': result.has_profile,
            'profile_results': {}
        }
        current_app.logger.info(f"==========profiling_dir: {result_dir}===========")
        
        if result.has_profile and os.path.exists(result_dir):
            # 读取性能分析结果
            results_file = os.path.join(result_dir, 'profiling_results.json')
            if os.path.exists(results_file):
                with open(results_file, 'r') as f:
                    profile_data['profile_results'] = json.load(f)
        
        return jsonify(profile_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/api/scheduled-tasks', methods=['GET'])
def get_scheduled_tasks():
    tasks = ScheduledTask.query.all()
    return jsonify({
        'tasks': [{
            'id': task.id,
            'name': task.name,
            'test_case_id': task.test_case_id,
            'cron': task.cron,
            'enabled': task.enabled
        } for task in tasks]
    })

@api_bp.route('/api/scheduled-tasks', methods=['POST'])
def create_scheduled_task():
    data = request.get_json()
    task = ScheduledTask(
        name=data['name'],
        test_case_id=data['test_case_id'],
        cron=data['cron'],
        enabled=True
    )
    
    try:
        # 获取测试用例信息
        test_case = TestCase.query.get_or_404(data['test_case_id'])
        
        # 先发送到测试客户端
        result = test_client.handle_message({
            'action': 'add_schedule',
            'task_id': task.id,
            'test_id': test_case.id,
            'command': test_case.command,
            'enable_profiling': test_case.enable_profiling,
            'profiling_config': test_case.profiling_config,
            'cron': task.cron
        })
        
        if result['status'] == 'error':
            return jsonify({'message': result['message']}), 500
        
        # test_client 操作成功后再写入数据库
        db.session.add(task)
        db.session.commit()
        
        return jsonify({
            'message': '添加任务成功',
            'task': task.to_dict()
        })
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@api_bp.route('/api/scheduled-tasks/<int:id>/toggle', methods=['PUT'])
def toggle_scheduled_task(id):
    task = ScheduledTask.query.get_or_404(id)
    try:
        # 获取测试用例信息
        test_case = TestCase.query.get_or_404(task.test_case_id)
        
        # 发送到测试客户端
        result = test_client.handle_message({
            'action': 'toggle_schedule',
            'task_id': task.id,
            'enabled': not task.enabled,  # 先发送新状态
            'test_id': test_case.id,
            'command': test_case.command,
            'enable_profiling': test_case.enable_profiling,
            'profiling_config': test_case.profiling_config,
            'cron': task.cron
        })
        
        if result['status'] == 'error':
            return jsonify({'message': result['message']}), 500
            
        # 客户端操作成功后更新数据库
        task.enabled = not task.enabled
        db.session.commit()
        
        return jsonify({
            'message': f"任务已{'启用' if task.enabled else '禁用'}"
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 500

@api_bp.route('/api/scheduled-tasks/<int:id>', methods=['DELETE'])
def delete_scheduled_task(id):
    task = ScheduledTask.query.get_or_404(id)
    try:
        # 发送到测试客户端
        result = test_client.handle_message({
            'action': 'delete_schedule',
            'task_id': task.id
        })
        
        if result['status'] == 'error':
            return jsonify({'message': result['message']}), 500
            
        # 客户端操作成功后删除数据库记录
        db.session.delete(task)
        db.session.commit()
        
        return jsonify({'message': '删除任务成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 500

@api_bp.route('/api/scheduled-tasks/<int:id>', methods=['PUT'])
def update_scheduled_task(id):
    task = ScheduledTask.query.get_or_404(id)
    data = request.get_json()
    
    try:
        # 获取测试用例信息
        test_case = TestCase.query.get_or_404(data['test_case_id'])
        
        # 发送到测试客户端
        result = test_client.handle_message({
            'action': 'add_schedule',  # 使用 add_schedule 来更新现有任务
            'task_id': task.id,
            'test_id': test_case.id,
            'command': test_case.command,
            'enable_profiling': test_case.enable_profiling,
            'profiling_config': test_case.profiling_config,
            'cron': data['cron']  # 使用新的 cron 表达式
        })
        
        if result['status'] == 'error':
            return jsonify({'message': result['message']}), 500
            
        # 客户端操作成功后更新数据库
        task.name = data['name']
        task.test_case_id = data['test_case_id']
        task.cron = data['cron']
        task.enabled = data.get('enabled', task.enabled)
        task.updated_at = datetime.now()
        db.session.commit()
        
        return jsonify({
            'message': '更新任务成功',
            'task': task.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 500