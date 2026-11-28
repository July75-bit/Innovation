# Render 启用真模型配置指南（DeepSeek 官方 API · 约 10 分钟）

> **状态**：✅ 线上已启用（2026-11-07 起），`/api/analysis/{id}` 返回 `source=llm`，中位耗时约 2.5 秒（见 `test_report.md` §8）。
> 最早试过 OpenCode Zen 免费档，被 Cloudflare 拦截（403/1010）又遇到额度限制（429），已经放弃；本文只保留 DeepSeek 一条路线。
> **负责人**：B（Render 控制台操作）｜ 验证：D 复核线上接口。

## 0. 需要的三项配置

| 环境变量 | 值 | 说明 |
| --- | --- | --- |
| `LLM_API_KEY` | `sk-` 开头的 DeepSeek 平台 key | 只在 Render 控制台填写，**不要发到群里、不要截图** |
| `LLM_BASE_URL` | `https://api.deepseek.com/v1` | 只填 base 即可，代码会自动补 `/chat/completions` |
| `LLM_MODEL` | `deepseek-flash` | 与 `render.yaml`、`.env.example` 一致 |

> `render.yaml` 已写好 `LLM_BASE_URL` 和 `LLM_MODEL`，用 Blueprint 同步时只需手填 `LLM_API_KEY`。
> 成本：单次约 700 输入 + 200 输出 tokens，演示用量可以忽略。

## 1. 配置步骤（Render 控制台）

1. 打开 `dashboard.render.com` → 服务 **`playerstock-backend`**；
2. 左侧 **Environment** → 按上表添加或编辑三个变量（已存在就改值，别加重复项）；
3. 点 **Save Changes**，Render 会自动重新部署；
4. 等状态回到 **Live**（免费实例约 1–2 分钟）。

> `LLM_TIMEOUT_SECONDS` 不用配，默认 20 秒。

## 2. 验证（两条都通过才算完成）

**① 命令行**（仓库根目录）：

```powershell
python scripts/check_llm.py --base https://playerstock-backend-mdlk.onrender.com
```

期望：`source = llm`，`action / risk_level / reason` 齐全。

**② 浏览器**：打开 `https://playerstock-backend-mdlk.onrender.com/api/analysis/1`，看 JSON 里的 `"source"`；再打开前端详情页，AI 卡的来源不应显示「规则兜底」。

## 3. source 仍是 rule_fallback 时怎么查

Render → `playerstock-backend` → **Logs**，搜 `LLM 输出不可用`，看后面的异常：

| 日志里的错误 | 原因 | 处置 |
| --- | --- | --- |
| `HTTP Error 401` | key 复制不完整或多了空格 / 引号 | 重新粘贴 key |
| `HTTP Error 404` / 400 提示 model 不存在 | 模型名或 base URL 写错 | 按 §0 表格核对 |
| `HTTP Error 402` / 429 | 账户余额不足或限流 | 去 DeepSeek 平台充值，或稍后再试 |
| `timeout` | 20 秒内没返回 | 调大 `LLM_TIMEOUT_SECONDS`，或接受规则兜底 |

**无论哪种，接口都返回 200 + 规则版结果，页面不报错、交易不受影响**——这是设计好的降级。

## 4. 想关掉真模型

Environment 里删除 `LLM_API_KEY`（或留空）→ Save → 自动部署 → 回到规则版。其他不用改。

## 5. 答辩注意

- 演示时只点 1–2 个选手的 AI 分析，避免现场等待；
- 如果出现「规则兜底」：正好讲降级设计（无密钥 / 超时 / 输出不合规一律回落，6 个字段不变），话术见 `qa.md`；
- key 曾在聊天记录中出现过，**答辩结束后在 DeepSeek 平台吊销并换新**。

> 依据：`code/backend/ai/llm_agent.py`（端点归一化、引号清理、20 秒超时）、`code/backend/app/core/config.py`（`llm_*` 字段）、`render.yaml`、`docs/software/deployment.md` 环境变量表、`scripts/check_llm.py`。
