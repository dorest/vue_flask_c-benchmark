from . import db
from datetime import datetime

class TestCase(db.Model):
    __tablename__ = 'test_cases'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    command = db.Column(db.Text, nullable=False)
    parameters = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    results = db.relationship('TestResult', backref='test_case', lazy=True)

class TestResult(db.Model):
    __tablename__ = 'test_results'
    
    id = db.Column(db.Integer, primary_key=True)
    test_case_id = db.Column(db.Integer, db.ForeignKey('test_cases.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='pending')
    perf_data = db.Column(db.JSON)
    benchmark_data = db.Column(db.JSON)
    flamegraph_path = db.Column(db.Text)
    result_dir = db.Column(db.Text)

class ScheduledTask(db.Model):
    __tablename__ = 'scheduled_tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    test_case_id = db.Column(db.Integer, db.ForeignKey('test_cases.id'), nullable=False)
    schedule_type = db.Column(db.String(20), nullable=False)
    cron_expression = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)