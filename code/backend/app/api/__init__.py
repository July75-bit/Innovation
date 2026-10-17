"""HTTP 路由集合。

每个模块对外暴露一个 `router: APIRouter`，由 app/main.py 统一挂到 /api 前缀下。

| 模块 | 文件 | 负责人 |
| --- | --- | --- |
| 健康检查 | health.py | B |
| 市场 / 选手 | players.py | B |
| 账户余额 | account.py | B |
| 买卖与流水 | trades.py | B |
| 持仓 | positions.py | B |
| 价格历史 | prices.py | B（数据来自 C） |
| AI 分析 | ai.py | B（逻辑来自 D） |
"""
