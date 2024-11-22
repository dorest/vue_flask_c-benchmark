from flask import Blueprint, request, jsonify, make_response
from .models import TestCase, TestResult, ScheduledTask
from .services.perf_service import PerfService
from . import db, scheduler
from .services.report_service import ReportService

api_bp = Blueprint('api', __name__)

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
            'created_at': case.created_at.isoformat() if case.created_at else None
        } for case in cases])
        
    elif request.method == 'POST':
        data = request.json
        test_case = TestCase(
            name=data['name'],
            description=data.get('description'),
            command=data['command'],
            parameters=data.get('parameters', {})
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
            'message': '创建成功'
        }), 201


@api_bp.route('/test-cases/<int:id>/run', methods=['POST'])
def run_test_case(id):
    test_case = TestCase.query.get_or_404(id)
    parameters = request.json.get('parameters', {})
    
    # 执行测试
    result = PerfService.run_perf_test(test_case, parameters)
    
    # 保存结果
    test_result = TestResult(
        test_case_id=test_case.id,
        start_time=result['start_time'],
        end_time=result['end_time'],
        status=result['status'],
        perf_data=result['perf_data'],
        benchmark_data=result.get('benchmark_data'),
        flamegraph_path=result.get('flamegraph_path')
    )
    db.session.add(test_result)
    db.session.commit()
    
    return jsonify(result)

@api_bp.route('/scheduled-tasks', methods=['POST'])
def create_scheduled_task():
    data = request.json
    task = ScheduledTask(
        test_case_id=data['test_case_id'],
        schedule_type=data['schedule_type'],
        cron_expression=data['cron_expression'],
        is_active=True
    )
    db.session.add(task)
    db.session.commit()
    
    # 添加定时任务
    scheduler.add_job(
        func=PerfService.run_perf_test,
        trigger='cron',
        args=[TestCase.query.get(task.test_case_id), {}],
        id=f'task_{task.id}',
        **dict(zip(['minute', 'hour', 'day', 'month', 'day_of_week'],
                   task.cron_expression.split()))
    )
    
    return jsonify({'id': task.id}), 201

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
        
        db.session.commit()
        
        return jsonify({
            'id': test_case.id,
            'name': test_case.name,
            'description': test_case.description,
            'command': test_case.command,
            'parameters': test_case.parameters,
            'message': '更新成功'
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
def get_test_result_details(id):
    try:
        result = TestResult.query.get_or_404(id)
        
        # 获取性能数据
        perf_data = result.perf_data or {}
        
        # 构造返回数据
        response_data = {
            'code': 200,
            'data': {
                'cpu_data': perf_data.get('cpu_data', []),
                'memory_data': perf_data.get('memory_data', []),
                'response_time_data': perf_data.get('response_time_data', []),
                'benchmark_data': [
                    {
                        'metric': 'CPU平均使用率',
                        'current': calculate_average(perf_data.get('cpu_data', [])),
                        'baseline': 50,  # 示例基准值
                        'diff': calculate_diff(calculate_average(perf_data.get('cpu_data', [])), 50)
                    },
                    {
                        'metric': '内存平均使用',
                        'current': calculate_average(perf_data.get('memory_data', [])),
                        'baseline': 500,  # 示例基准值
                        'diff': calculate_diff(calculate_average(perf_data.get('memory_data', [])), 500)
                    },
                    {
                        'metric': '平均响应时间',
                        'current': calculate_average(perf_data.get('response_time_data', [])),
                        'baseline': 100,  # 示例基准值
                        'diff': calculate_diff(calculate_average(perf_data.get('response_time_data', [])), 100)
                    }
                ]
            },
            'message': '获取成功'
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Error fetching test result details: {str(e)}")  # 添加日志
        return jsonify({
            'code': 500,
            'data': {
                'cpu_data': [],
                'memory_data': [],
                'response_time_data': [],
                'benchmark_data': []
            },
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
