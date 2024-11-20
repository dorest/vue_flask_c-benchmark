from flask import Blueprint, request, jsonify
from .models import TestCase, TestResult, ScheduledTask
from .services.perf_service import PerfService
from . import db, scheduler

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