## 这次改了什么

<!-- 一句话说明 -->

## 影响范围

- [ ] 前端（A）
- [ ] 后端 API / 交易规则（B）
- [ ] 定价算法 / 模拟数据（C）
- [ ] AI 智能体 / 部署 / 文档（D）

## 是否改动接口契约（`docs/software/api_contract.md`）

- [ ] 否，未改动字段
- [ ] 是，已同步更新 `api_contract.md`，并通知：
  - 对接人：@
  - 变更的字段/路径：
  - 前端是否需要同步改：

## 我怎么验证的

<!-- 贴命令 / 截图 / Swagger 结果。不允许只写"能跑" -->

```text
# 例：python -m pytest tests/unit/test_trades_rule.py -q
```

## 自查清单

- [ ] `python -m pytest` 通过（或说明为什么没跑）
- [ ] 没有提交 `.env`、真实密钥、`*.db`
- [ ] 没有提交 `frontend/node_modules`
- [ ] 新增的文档已在 `docs/` 对应目录落盘，不是只写在聊天里
- [ ] 如果改了 API 地址/启动命令，README 和 `docs/software/deployment.md` 已同步
