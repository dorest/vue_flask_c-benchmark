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
    enable_profiling = db.Column(db.Boolean, default=False)
    profiling_config = db.Column(db.JSON)
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
    has_profile = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            'id': self.id,
            'test_case_id': self.test_case_id,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'status': self.status,
            'perf_data': self.perf_data,
            'benchmark_data': self.benchmark_data,
            'flamegraph_path': self.flamegraph_path,
            'result_dir': self.result_dir
        }

class ScheduledTask(db.Model):
    __tablename__ = 'scheduled_tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    test_case_id = db.Column(db.Integer, db.ForeignKey('test_cases.id'), nullable=False)
    cron = db.Column(db.String(100), nullable=False)
    enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    test_case = db.relationship('TestCase', backref=db.backref('scheduled_tasks', lazy=True))
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'test_case_id': self.test_case_id,
            'cron': self.cron,
            'enabled': self.enabled,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }