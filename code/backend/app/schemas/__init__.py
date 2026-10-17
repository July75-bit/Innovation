"""Pydantic 请求 / 响应模型。

负责人：B

建议至少定义：

请求：
- TradeRequest：player_id: int, quantity: int（ge=1，正整数校验放这里）

响应：
- TradeResponse：success: bool, message: str, balance: float, player_id: int, quantity: int
- PlayerSummary：player_id, name, display_name, team, role, current_price, prev_price,
  change_pct, rating, hltv_rating, kast, adr, status
- PlayerDetail：PlayerSummary + reason（最近一次价格变化原因）
- AccountResponse：user_id, balance, initial_balance, total_asset, position_value
- PositionItem：player_id, name, quantity, avg_cost, current_price, market_value, profit, profit_pct
- PricePoint：ts, price, reason
- PriceHistoryResponse：player_id, points: list[PricePoint]
- AnalysisResponse：player_id, action(Literal["BUY","SELL","HOLD"]), reason, risk_level, source, disclaimer

注意：
- `player_id` 这个字段名是四方约定的关键，不要写成 `id`；
- action / risk_level 用 Literal 约束，避免 AI 返回 "buy" 或 "建议买入" 时前端解析失败；
- 响应模型一旦发布就当作契约，改字段必须走 PR 模板的"接口变更"勾选。
"""
