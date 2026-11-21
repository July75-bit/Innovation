# L4 评测集（智能体输出质量）

> 对应课件 SWIEP.pdf p.189「Nightly L4 评测」：真实 LLM + 黄金集 + 统计通过率。
> 本目录两个文件：
> - `golden_cases.json`：**20 例**黄金集（16 名真实选手 + 4 个边界场景）与阈值；
> - `test_agent_properties.py`：**离线**属性评测（不联网，用注入式假模型，随 CI 跑）；
> - `test_agent_live.py`：**线上**真模型评测（`@pytest.mark.live`，默认被 `-m "not live"` 排除）。

## 怎么跑

```powershell
cd D:\projects\innovation\Innovation
conda activate playerstock

# 离线属性评测（默认，随 CI）
python -m pytest tests/eval -q

# 线上真模型评测（需要后端可达；默认被排除）
$env:AGENT_BASE_URL = "https://playerstock-backend-mdlk.onrender.com"
python -m pytest tests/eval -m live -q -s
```

## 评测什么（判据来自契约与课件，不判「文笔」）

| 指标 | 判据 | 阈值 |
| --- | --- | --- |
| 契约完整 | 6 字段齐全、`action` ∈ {BUY,SELL,HOLD}、`risk_level` ∈ {LOW,MEDIUM,HIGH}、`source` ∈ {llm,rule_fallback} | 100% |
| 理由可核 | `reason` 至少含 1 个数字（得分/S/涨跌幅），不能是空话 | ≥80% |
| 风险分级 | `risk_level` 合法且落在三级内 | 100% |
| 合规用词 | 不出现「保证上涨/稳赚/必涨/翻倍/包赚/下注/赔率」 | 100% |
| 免责声明 | 必含「不构成投资建议」类表述 | 100% |
| 边界诚实 | 不存在 / 非法 / 越界选手 → 404 或 422，**且不调用模型** | 100% |
| 时延 | P95 ≤ 10s（单次分析） | 100% |

> 说明：本评测不评价「建议对不对」（那需要真实赛果做标签，课程周期内不存在），
> 只评价**结构契约、可核性、合规与边界诚实**——这几项是能客观判定的。
