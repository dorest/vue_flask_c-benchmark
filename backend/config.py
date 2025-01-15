import sys
from pathlib import Path
sys.path.append(str(Path("performance-tests").resolve()))
import nameconfig
class Config:
    # 在 Docker 环境中，主机名应该是 PostgreSQL 容器的服务名
    SQLALCHEMY_DATABASE_URI = f'postgresql://root:zxyoright@{nameconfig.DB_CONTAINER_NAME}:5432/zxy'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TEST_ROOT_DIR = '/root/flask-vue/performance-tests'