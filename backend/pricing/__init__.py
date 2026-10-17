"""定价与行情模块（纯 Python，不碰数据库、不碰用户余额）。

负责人：C

为什么放在 backend/ 里面而不是仓库根目录的 core_engine/：
后端在 Render 上的 Root Directory 是 `backend/`，构建产物只有 backend 目录。
放在外面的 `../core_engine/` 线上一定 import 失败（本地能跑、上线就炸）。

模块边界（必须守住）：
- 本模块只做"算"：输入比赛数据 -> 输出新价格和变化原因；
- 落库（price_history）由 B 的 app/api/prices.py 负责；
- 绝不在这里改用户余额或持仓。
"""
