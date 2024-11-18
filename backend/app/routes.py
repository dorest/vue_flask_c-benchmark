from flask import Blueprint, request, jsonify
from .models import TestCase, TestResult, ScheduledTask
from .services.perf_service import PerfService
from . import db, scheduler

api_bp = Blueprint('api', __name__)

@api_bp.route('/test-cases', methods=['POST'])
def create_test_case():
    data = request.json
    test_case = TestCase(
        name=data['name'],
        description=data.get('description'),
        command=data['command'],
        parameters=data.get('parameters', {})
    )
    db.session.add(test_case)
    db.session.commit()
    return jsonify({'id': test_case.id}), 201

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