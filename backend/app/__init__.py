import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
import pytz
from flask_sock import Sock
os.environ['TZ'] = 'Asia/Shanghai'  # 设置环境变量
import time
time.tzset()  # 重新加载时区设置

db = SQLAlchemy()
migrate = Migrate()
scheduler = BackgroundScheduler(timezone=pytz.timezone('Asia/Shanghai'))
sock = Sock()

def create_app():
    app = Flask(__name__)
    CORS(app)
    CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:8080"],  # 只允许前端域名
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # 允许的方法
        "allow_headers": ["Content-Type"]  # 允许的请求头
        }
    })
    
    # 配置
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://root:zxyoright@postgres_db:5432/zxy'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    sock.init_app(app)
    
    # 注册蓝图
    from .routes import api_bp
    app.register_blueprint(api_bp)
    
    # 启动调度器
    scheduler.start()
    
    return app