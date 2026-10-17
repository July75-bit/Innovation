"""定价与模拟比赛核心模块（纯 Python，不碰数据库、不碰用户余额）。

负责人：C

位置：`code/core_engine/`
- 课程要求的仓库结构把「定价」放在 `code/core_engine/`，与 `code/backend` 平级；
- 后端通过两种方式导入：① `code/backend/app/core/config.py` 把 `code/` 注入 `sys.path`
  （默认，本地/CI/Render 都生效）；② 可选 `pip install -e code/core_engine` 作为标准包；
- 代码里统一写 `from core_engine.pricing import update_price`。

模块边界（必须守住）：
- 本模块只做“算”：输入比赛数据 -> 输出新价格和变化原因；
- 落库（price_history）由 B 的 app/api/prices.py 负责；
- 绝不在这里改用户余额或持仓。
"""
