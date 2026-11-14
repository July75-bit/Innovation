# 智能体 L4 评测报告（真模型 · 黄金集）

> **对应课件**：SWIEP.pdf p.189「Nightly L4 评测：真实 LLM + 黄金集 / 统计通过率」。
> **评测对象**：`GET /api/analysis/{player_id}`（线上 Render 后端，DeepSeek 官方 API）。
> **最近一次**：**2026-11-14 10:11**（`tests/eval/last_live_run.json` 为原始结果）。
> **执行**：D 王泽棠

## 1. 评测集设计（20 例）

| 类型 | 例数 | 说明 |
| --- | ---: | --- |
| 真实选手 | 16 | 覆盖 16 名选手（不同位置：AWPer / Rifler / IGL / Lurker），价格趋势上涨/横盘/回落都有 |
| 暂停交易 | 1 | sh1ro（`suspended`），验证规则版与模型版都给建议但不影响交易 |
| 边界：不存在 | 1 | `player_id=999` → 期望 4xx |
| 边界：非法 | 1 | `player_id=0` → 期望 4xx |
| 边界：负数 | 1 | `player_id=-1` → 期望 4xx |
| 边界：越界 | 1 | `player_id=100000` → 期望 4xx |

定义文件：`tests/eval/golden_cases.json`；跑法见 `tests/eval/README.md`。

## 2. 实测结果（2026-11-14 10:11，线上）

| 指标 | 阈值 | 实测 | 判定 |
| --- | --- | --- | --- |
| 契约完整率（6 字段 + 枚举 + 来源） | 100% | **16/16 = 100%** | ✅ |
| 走真模型（`source=llm`） | — | **16/16 = 100%** | ✅ |
| 理由可核率（含数字） | ≥80% | **16/16 = 100%** | ✅ |
| 风险分级合法（LOW/MEDIUM/HIGH） | 100% | **16/16 = 100%**（实测出现 HIGH / MEDIUM 两档，非恒定值） | ✅ |
| 合规用词（无"保证上涨/稳赚/必涨…"） | 100% | **16/16 = 100%** | ✅ |
| 免责声明 | 100% | **16/16 = 100%** | ✅ |
| 边界诚实（4 例均 4xx 且不含 AI 字段） | 100% | **4/4 = 100%**（全部 404） | ✅ |
| 时延 | P95 ≤ 10s | 中位 **2016ms** / P95 **3393ms** / 最大 4752ms | ✅ |

样例（可复核，取自结果文件）：

```
E01 ZywOo  HOLD risk=HIGH   src=llm  3091ms
    reason: 当前价格108.75，较前一日126.27单日下跌13.88%，原因是本轮表现下滑（得分81.3，S=-0.92）；
            但表现评分仍有88，且买入均价108.75与……（含可核对数字）
E03 m0NESY BUY  risk=HIGH   src=llm  4752ms
    reason: 当前价 85.08 已从 11-14 低点 77.95 反弹，本轮上涨 8.27%，本轮得分 90.2（S=+0.55）……
```

> 观察：模型对同一批数据给出**不同结论**（HOLD / BUY 都有，风险 HIGH / MEDIUM 都出现），
> 说明它不是在"背模板"——这是"模型是独立建议者"的现场证据（`qa.md` 已收录）。

## 3. 离线版（每次 CI 都跑）

真模型评测要联网、要密钥、单例 2–3 秒，不适合每次提交。因此同一套黄金集另有一份**离线属性评测**：

```powershell
python -m pytest tests/eval -q          # 33 passed, 6 deselected（live 默认排除）
```

它用统一 `fake_llm` 夹具（`tests/conftest.py`）注入假模型，验证的是**确定性的那一半**：
字段集合、枚举、来源、免责、脏输出清洗、边界回落。真模型的"质量"由本报告的线上数据承担。

## 4. 局限（如实交代）

1. **没有"建议对不对"的标签**：判断建议是否正确需要真实赛果，课程周期内不存在；
   因此本评测只评「契约 / 可核性 / 合规 / 边界诚实」，不评"预测准确率"。
2. **样本量 20**：够验证契约与稳定性，不足以做统计显著的模型对比（如换 provider 的 A/B）。
3. **非 nightly**：靠人工手动触发（`-m live`），没有定时任务——课程环境无 CI 定时授权。
4. **单账户视角**：上下文只含当前账户持仓，不覆盖多用户并发对模型的影响（那是交易层的测试范围）。

## 5. 复跑

```powershell
cd D:\projects\innovation\Innovation
conda activate playerstock

# 离线（随 CI）
python -m pytest tests/eval -q

# 线上真模型
$env:AGENT_BASE_URL = "https://playerstock-backend-mdlk.onrender.com"
python -m pytest tests/eval -m live -q
```

结果会写到 `tests/eval/last_live_run.json`（已入库，便于评委核对本次数字）。
