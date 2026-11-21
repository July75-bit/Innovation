# Render 启用真模型配置指南（给 B · 约 10 分钟）

> **状态（2026-11-07 晚）**：✅ **已上线并验证通过**。Zen 免费档因额度 429 走不通，
> 最终改用 **DeepSeek 官方 API**：`source=llm`、5/5 选手、中位 **2461ms**（见 `test_report.md` §8.3）。
> 本文保留两条路线，新环境照 §1B（官方 API）配即可。
>
> **目标**：把线上 `/api/analysis/{id}` 从 `rule_fallback` 切到真 LLM。
> **前提**：`develop` 已包含 UA 修复 `897aa3e`、URL 归一化 `8a26a19`、引号清理 `2684e1b`。
> **负责人**：B（Render 控制台操作）｜ 验证：D 复核线上接口｜ 时间：今天彩排前。

## 0. 你要拿到的三样东西

| 项 | 值 | 来源 |
| --- | --- | --- |
| Key | `oc_sk_` 开头完整串 | D 私发（**不要发到群里/截图**） |
| URL | `https://opencode.ai/inference/openai/v1/chat/completions` | 固定值，**必须带 `/chat/completions` 全路径**，我们代码要的是完整 URL 而不是 base |
| 模型名 | `deepseek-v4.1-flash-free` | Zen 公开清单实测存在（备选 `glm-5.3-flash-free` / `big-pickle`） |

### 0.1 路线 B（推荐，2026-11-07 实测可用）：DeepSeek 官方 API

Zen 免费档会返回 `429 FreeUsageLimitError`（免费额度是账号级限制，换模型无效），官方 API 直接可用：

| 项 | 值 |
| --- | --- |
| `LLM_API_KEY` | `sk-` 开头的 DeepSeek 平台 key（预充值，10 元够用很久） |
| `LLM_BASE_URL` | `https://api.deepseek.com/v1`（只填 base 即可，代码自动补 `/chat/completions`） |
| `LLM_MODEL` | **`deepseek-flash`** |

> **模型名别搞混**：官方现名 `deepseek-flash`（= `DeepSeek-V4.1-Flash-1017`）；旧名 `deepseek-v4-flash` 仍接受；
> `deepseek-chat` 是 V3 时代老名，文档已不再列；Zen 网关那边叫 `deepseek-v4.1-flash-free`/`-flash`。
> 成本：单次约 684 输入 + 200 输出 tokens ≈ **¥0.003/次**（高峰价），演示十次以内可忽略。

## 1. 配置步骤（Render 控制台）

1. 打开 `dashboard.render.com` → 服务 **`playerstock-backend`**；
2. 左侧 **Environment** 标签 → 逐条 Add Key / Value（三个一起加，**少一个都不生效**）：

   ```
   LLM_API_KEY  = oc_sk_…（完整值）
   LLM_BASE_URL = https://opencode.ai/inference/openai/v1/chat/completions
   LLM_MODEL    = deepseek-v4.1-flash-free
   ```

3. 点 **Save Changes** → Render 自动重新部署（旧进程不会热加载环境变量，别手动重启凑合）；
4. 等状态回到 **Live**（免费实例约 1–2 分钟）。

> 已存在同名变量就编辑值，别加重复项；`LLM_TIMEOUT_SECONDS` 不用配（默认 20s）。

## 2. 验证（按顺序，两条都绿才算完成）

**① 命令行**（仓库根目录）：

```powershell
python scripts/check_llm.py --base
```

期望：`source = llm`（不再是 `rule_fallback`）、`action/risk_level/reason` 齐全。

**② 浏览器**：打开 `https://playerstock-backend-mdlk.onrender.com/api/analysis/1`，看 JSON 里的 `"source"`；再开前端详情页 `/players/1`，AI 卡的「依据来源」不应再显示「规则兜底（AI 暂不可用）」。

## 3. 如果 source 还是 rule_fallback：看日志一眼定位

Render → `playerstock-backend` → **Logs**，搜 `LLM 输出不可用`，后面的异常类型直接对应病因：

| 日志里的错误 | 原因 | 处置 |
| --- | --- | --- |
| `HTTP Error 403`（1010） | 部署的代码不含 UA 修复 | 确认 `develop` 已推到 `897aa3e` 之后，重新触发部署 |
| `HTTP Error 401` | key 复制不完整/多了空格 | 重贴 key |
| `HTTP Error 404` / 400 说 model 不存在 | 模型名写错 | 用 `deepseek-v4.1-flash-free`，或换备选 |
| `HTTP Error 429` | 出口 IP 或 free 档限流 | 换模型名再试；持续 429 就保持规则兜底（不算事故，见 §5） |
| `timeout` | 20s 内没回 | 换更快的 flash 档模型，或调大 `LLM_TIMEOUT_SECONDS` |

**无论哪种，接口仍返回 200 + 规则版结果，页面不报错、交易不受影响**——这是设计好的降级，放心操作。

## 4. 想撤掉（随时，无损）

Environment 里删掉 `LLM_API_KEY`（或留空）→ Save → 自动部署 → 回到规则兜底。其他不用动。

## 5. 答辩注意（给全员）

- **演示别连点多个选手的 AI 分析**：free 档限流按分钟窗口，现场演示只点 1–2 次；
- 万一点出「规则兜底」：**顺势讲降级设计**（"无密钥/超时/脏输出一律回落，6 字段不变，AI 故障不阻塞交易"），话术在 `qa.md`，这反而是加分项；
- **key 已在本项目聊天记录出现过，答辩结束后请吊销/轮换**（OpenCode 后台操作，1 分钟）。

> 依据：`code/backend/ai/llm_agent.py`（UA 修复 `897aa3e`）、`code/backend/app/core/config.py`（四个 `llm_*` 字段）、`docs/software/deployment.md` §2 环境变量表、`scripts/check_llm.py`（B 写的验证脚本，注意其 `--direct` 也是裸 UA，本机直测会 403，用 `--base` 验线上即可）。
