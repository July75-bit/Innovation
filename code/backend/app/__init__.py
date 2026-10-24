"""PlayerStock 后端应用包。

目录约定（与原 6 天手册的 code/backend/main.py 单文件写法有意不同）：
- app/api/      HTTP 路由
- app/models/   SQLAlchemy 模型
- app/schemas/  Pydantic 请求/响应模型
- app/core/     配置、数据库会话

启动命令：uvicorn app.main:app --reload --port 8000
"""

__version__ = "0.1.0"
