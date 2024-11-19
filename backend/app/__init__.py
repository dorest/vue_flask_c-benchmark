from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler

db = SQLAlchemy()
migrate = Migrate()
scheduler = BackgroundScheduler()

def create_app():
    app = Flask(__name__)
    CORS(app)
    
    # 配置
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://root:zxyoright@postgres_db:5432/zxy'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    
    # 注册蓝图
    from .routes import api_bp
    app.register_blueprint(api_bp)
    
    # 启动调度器
    scheduler.start()
    
    return app