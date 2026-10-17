"""账户接口。

负责人：B

待实现：
- GET /api/account   当前用户虚拟币余额与总资产

参考响应：
    {
      "user_id": 1,
      "balance": 5000,
      "initial_balance": 5000,
      "total_asset": 5000,
      "position_value": 0
    }

规则来源：新用户初始 5000 虚拟币（settings.initial_balance），每日签到补给为加分项。
"""

from fastapi import APIRouter

router = APIRouter(prefix="/account", tags=["account"])

# TODO(B)：实现 GET /api/account
