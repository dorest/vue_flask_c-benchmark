class Config:
    # PostgreSQL连接URI格式：postgresql://用户名:密码@主机:端口/数据库名
    SQLALCHEMY_DATABASE_URI = 'postgresql://root:zxyoright@localhost:5432/zxy'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'your-secret-key'