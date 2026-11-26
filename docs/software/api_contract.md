# 接口契约

> 负责人 B ｜ 第 1 天锁定字段，之后只加不改；改字段需通知 A/C/D 并同步前端。

## 1. 通用约定

| 项 | 约定 |
| --- | --- |
| Base URL | 本地 `http://127.0.0.1:8000`；线上由前端 `VITE_API_BASE_URL` 注入 |
| 路径 | 业务接口统一 `/api` 前缀 |
| 编码 | `application/json; charset=utf-8` |
| 命名 | snake_case；主键叫 `player_id` / `user_id`，不用 `id` |
| 金额 | number，2 位小数；前端不再二次截断 |
| 时间 | ISO 8601 UTC，如 `2026-01-01T10:05:00Z` |
| 布尔 | true / false |

> 交易是否成功以**后端数据库**为准，前端不允许只改页面数字。

## 2. 错误格式

```json
{ "success": false, "message": "余额不足，当前余额 50.00，需要 100.00", "code": "INSUFFICIENT_BALANCE" }
```

| HTTP | code | 场景 |
| --- | --- | --- |
| 400 | INSUFFICIENT_BALANCE | 余额不足 |
| 400 | INSUFFICIENT_POSITION | 持仓不足 |
| 400 | POSITION_LIMIT_EXCEEDED | 超过单选手 50 股 |
| 400 | PLAYER_TRADING_SUSPENDED | 选手暂停交易 / 本轮有比赛 |
| 400 | INVALID_QUANTITY | 数量非正整数 |
| 404 | PLAYER_NOT_FOUND | 选手不存在 |
| 422 | VALIDATION_ERROR | Pydantic 校验失败 |
| 500 | INTERNAL_ERROR | 未预期异常 |

`message` 必须是可以直接展示的中文，前端不做映射。

## 3. 接口清单

| # | 方法 | 路径 | 功能 |
| --- | --- | --- | --- |
| 1 | GET | /api/health | 健康检查 |
| 2 | GET | /api/players | 市场选手列表 |
| 3 | GET | /api/players/{player_id} | 单个选手详情 |
| 4 | GET | /api/players/{player_id}/prices | 价格历史（按 ts 升序） |
| 5 | GET | /api/account | 账户余额与资产 |
| 5.1 | GET | /api/account/history | 资产曲线与交易统计（个人页） |
| 6 | GET | /api/positions | 当前持仓 |
| 7 | POST | /api/trades/buy | 买入 |
| 8 | POST | /api/trades/sell | 卖出 |
| 9 | GET | /api/trades | 交易流水（倒序） |
| 10 | GET | /api/analysis/{player_id} | AI 建议（6 字段） |
| 11 | POST | /api/prices/recalc | 赛后结算（运维接口，前端不调用；需 `?token=<RESEED_TOKEN>`，未配置口令时 403 `OPS_TOKEN_UNSET`） |
| 12 | GET | /api/debug/db | 只读数据库自检（DEBUG_ENDPOINTS=0 时 404） |
| 13 | POST | /api/auth/register | 注册私人账号，成功即登录 |
| 14 | POST | /api/auth/login | 登录，签发新令牌 |
| 15 | GET | /api/auth/me | 当前身份 |
| 16 | POST | /api/auth/logout | 退出（撤销令牌，幂等） |
| 17 | DELETE | /api/auth/account | 删除账号（口令二次确认，级联清理） |
| 18 | GET | /api/debug/logs | 运行日志自检（?lines=100&level=WARNING） |

## 4. 关键示例

### 买入 / 卖出

请求：`{ "player_id": 1, "quantity": 2 }`

响应：

```json
{ "success": true, "message": "买入成功", "balance": 4748.00, "player_id": 1, "quantity": 2 }
```

卖出返回结构相同；余额、持仓、流水在同一事务里更新。

### AI 建议（6 字段）

```json
{
  "player_id": 1,
  "action": "BUY",
  "reason": "近期表现高于均值，当前价格低于 11 个历史点的中位数",
  "risk_level": "medium",
  "source": "llm",
  "disclaimer": "仅课程模拟建议，不构成投资建议"
}
```

- `source` 为 `llm` 或 `rule_fallback`；任何失败都返回 200 + rule_fallback。
- AI 只读，不写余额、不下单。

### 认证

登录/注册返回 `access_token` 与 `user`；后续请求带 `Authorization: Bearer <token>`。
令牌 30 天有效，退出即撤销。

## 5. 变更流程

1. 先改本文档并标注日期与影响接口；
2. PR 勾「接口变更」，通知 A/B/C/D；
3. 前端同步改类型与调用，后端补测试；
4. 合并后在 PR 里贴新旧响应示例。
