"""AI 智能体模块。

负责人：D

为什么放在 backend/ 里面：
1. 手册 D2 要求"在后端封装分析函数，避免把 API 密钥暴露到前端" —— 只有后端进程内
   才能安全读 settings.llm_api_key；
2. Render 上后端 Root Directory 是 backend/，放在目录外线上 import 不到。

设计原则：
- AI 只产出建议（BUY / SELL / HOLD + 理由 + 风险等级），不直接改余额或执行交易；
- 模型不可用（无密钥 / 超时 / 返回非法 JSON）时，必须回落到 fallback 规则版，
  返回同样结构的建议，保证交易、定价、行情不受影响。
"""
