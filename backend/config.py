class Config:
    # 在 Docker 环境中，主机名应该是 PostgreSQL 容器的服务名
    SQLALCHEMY_DATABASE_URI = 'postgresql://root:zxyoright@postgres_db:5432/zxy'
    SQLALCHEMY_TRACK_MODIFICATIONS = False