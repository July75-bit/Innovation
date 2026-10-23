# 数据库设计说明

> **负责人**：B ｜ **截止**：第 1 天出表结构，第 6 天定稿 ｜ **状态**：✅ 已填写（第 6 天附实际 schema）
> **对应课程指标**：#7 数据设计；分工文档 B6"整理 API 文档和数据库设计说明"
> 答辩必问："为什么要这几张表？并发下怎么保证不超卖？"

## 1. 实体关系图

```mermaid
erDiagram
    USERS ||--o{ POSITIONS : "持有"
    USERS ||--o{ TRADES : "产生"
    PLAYERS ||--o{ POSITIONS : "被持有"
    PLAYERS ||--o{ TRADES : "被交易"
    PLAYERS ||--o{ PRICE_HISTORY : "有价格历史"

    USERS {
        int user_id PK
        string nickname
        float balance
        float initial_balance
        datetime created_at
    }
    PLAYERS {
        int player_id PK
        string name
        string display_name
        string team
        float current_price
        float prev_price
        int rating
        string status
        datetime updated_at
    }
    POSITIONS {
        int position_id PK
        int user_id FK
        int player_id FK
        int quantity
        float avg_cost
        datetime updated_at
    }
    TRADES {
        int trade_id PK
        int user_id FK
        int player_id FK
        string side
        int quantity
        float price
        float amount
        float balance_after
        datetime created_at
    }
    PRICE_HISTORY {
        int price_id PK
        int player_id FK
        float price
        string reason
        datetime ts
    }
```

## 2. 表结构明细

### 2.1 `users` 账户

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `user_id` | INTEGER | PK, autoincrement | |
| `nickname` | VARCHAR(50) | NOT NULL | 演示账户可为 "demo" |
| `balance` | FLOAT | NOT NULL, default 5000 | 虚拟币余额，不可为负 |
| `initial_balance` | FLOAT | NOT NULL, default 5000 | 用于算收益率 |
| `created_at` | DATETIME | NOT NULL, default now | |

### 2.2 `players` 选手

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `player_id` | INTEGER | PK | |
| `name` | VARCHAR(50) | NOT NULL, UNIQUE | CS2 选手游戏内 ID（真实公开信息），如 ZywOo |
| `display_name` | VARCHAR(50) | | 展示名，真实选手暂无官方中文名时与 name 相同 |
| `team` | VARCHAR(50) | | 所属战队（真实公开信息），如 Vitality |
| `current_price` | FLOAT | NOT NULL, > 0 | 定价模块写入 |
| `prev_price` | FLOAT | NOT NULL | 用于算涨跌幅 |
| `role` | VARCHAR(20) | | 选手真实位置：AWPer / Entry / Rifler / IGL / Support / Lurker |
| `rating` | INTEGER | 0–100 | 本项目模拟综合表现分（C 维护），**不是 HLTV Rating 或任何官方统计** |
| `status` | VARCHAR(20) | NOT NULL, default 'trading' | `trading` / `suspended` |
| `updated_at` | DATETIME | NOT NULL | |

> 说明：`data/seed_players.json` 里的 `initial_price`（上市价）**不是本表字段**，落库时写成 `price_history` 的第一条记录（`reason = 初始价格`）。

### 2.2.1 实现说明（第 1 天补充）

- 金额字段（`balance` / `initial_balance` / `current_price` / `prev_price` / `price` / `amount` / `balance_after`）
  在 ORM 中用 `NUMERIC(12,2)`，`avg_cost` 用 `NUMERIC(12,4)`；SQLite 下仍按 REAL 存储，
  但应用层统一用 `Decimal` 计算，避免浮点误差。对外 JSON 仍是两位小数 `number`，契约不变。
- 种子数据会为每名选手写 `price_history` 第一条（`reason = 初始价格`）；若
  `current_price != initial_price`，再补一条当前价（`reason = 模拟比赛表现调整（种子数据…）`），
  保证前端折线图与 D 的 AI 输入都有可解释的历史点。

### 2.3 `positions` 持仓

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `position_id` | INTEGER | PK | |
| `user_id` | INTEGER | FK → users, NOT NULL | |
| `player_id` | INTEGER | FK → players, NOT NULL | |
| `quantity` | INTEGER | NOT NULL, ≥ 1 | 为 0 时删除行 |
| `avg_cost` | FLOAT | NOT NULL | 买入均价 |
| `updated_at` | DATETIME | NOT NULL | |

**唯一索引**：`UNIQUE(user_id, player_id)` —— 防止同一选手出现两行持仓。
**CHECK**：`quantity BETWEEN 1 AND 50`（与应用层校验双保险）。

### 2.4 `trades` 交易流水

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `trade_id` | INTEGER | PK | |
| `user_id` | INTEGER | FK → users, NOT NULL | |
| `player_id` | INTEGER | FK → players, NOT NULL | |
| `side` | VARCHAR(4) | NOT NULL, CHECK IN ('BUY','SELL') | |
| `quantity` | INTEGER | NOT NULL, ≥ 1 | |
| `price` | FLOAT | NOT NULL, > 0 | 成交时的价格快照 |
| `amount` | FLOAT | NOT NULL | `price × quantity` |
| `balance_after` | FLOAT | NOT NULL | 便于对账与回溯 |
| `created_at` | DATETIME | NOT NULL | |

**索引**：`INDEX(user_id, created_at DESC)` —— 流水页按时间倒序查询。

> 为什么存 `price` 快照？因为选手价格之后还会变，流水必须能独立追溯"当时多少钱成交的"。

### 2.5 `price_history` 价格历史

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `price_id` | INTEGER | PK | |
| `player_id` | INTEGER | FK → players, NOT NULL | |
| `price` | FLOAT | NOT NULL, > 0 | |
| `reason` | VARCHAR(200) | NOT NULL | 人类可读的涨跌原因（可解释性落点） |
| `ts` | DATETIME | NOT NULL | 升序查询 |

**索引**：`INDEX(player_id, ts)`。

## 3. 一致性规则（事务）

| 操作 | 必须同事务完成 | 失败处理 |
| --- | --- | --- |
| 买入 | 扣 `users.balance` + 更新/插入 `positions` + 插入 `trades` | 全回滚 |
| 卖出 | 加 `users.balance` + 减少/删除 `positions` + 插入 `trades` | 全回滚 |
| 价格更新 | 更新 `players.current_price/prev_price` + 插入 `price_history` | 全回滚 |

**C 的边界**：价格更新只写 `players` 和 `price_history`，**永不**碰 `users.balance` 与 `positions`。

## 4. 迁移与初始化

| 项 | 方案 |
| --- | --- |
| 建表 | 开发期 `Base.metadata.create_all()`（`app/core/database.py`） |
| 种子数据 | `python scripts/seed_db.py`（读 `data/seed_players.json`） |
| schema 迁移 | 6 天版不做 Alembic；若改表结构，删库重建 + 重新 seed，并在本文件记录 |
| 线上持久化 | 挂载 Persistent Disk 到 `/var/data`，`DATABASE_URL=sqlite:////var/data/playerstock.db` |

## 5. 变更记录

| 日期 | 变更 | 变更人 | 影响 |
| --- | --- | --- | --- |
| | 初版表结构 | B | A/C/D 确认字段名 |
| 第 1 天 | 按本文落成 ORM：5 张表 + `uq_positions_user_player` + `ck_positions_quantity_range` + 三条索引；金额改用 `NUMERIC(12,2)`（应用层 Decimal 计算，JSON 仍是两位小数）；SQLite 开启 `foreign_keys=ON` / WAL / `busy_timeout=5000` | B | 无接口字段变更；A/C/D 无需适配 |

## 6. TODO

- [x] B 第 1 天：按本文建 models，跑通 `init_db()`
- [x] B 第 1 天：补唯一索引与 CHECK 约束（提前于 D2 完成）
- [ ] B 第 6 天：把实际表结构（`sqlite3 .schema` 输出）贴到附录，证明与文档一致
      —— 第 1 天已先贴一版实测结果，见 §7，第 6 天只做复核

## 7. 附录 A：第 1 天实测 `.schema`（`code/backend/playerstock.db`）

生成方式：

```powershell
# 有 sqlite3 命令行时
sqlite3 code/backend/playerstock.db ".schema"

# 没有 sqlite3 时用 Python（本次实际采用）
python -c "import sqlite3;print('\n'.join(r[0] for r in sqlite3.connect('code/backend/playerstock.db').execute('select sql from sqlite_master where sql is not null')))"
```

```sql
-- table: players
CREATE TABLE players (
	player_id INTEGER NOT NULL, 
	name VARCHAR(50) NOT NULL, 
	display_name VARCHAR(50), 
	team VARCHAR(50), 
	current_price NUMERIC(12, 2) NOT NULL, 
	prev_price NUMERIC(12, 2) NOT NULL, 
	role VARCHAR(20), 
	rating INTEGER NOT NULL, 
	status VARCHAR(20) DEFAULT 'trading' NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (player_id), 
	CONSTRAINT ck_players_current_price_positive CHECK (current_price > 0), 
	CONSTRAINT ck_players_prev_price_positive CHECK (prev_price > 0), 
	CONSTRAINT ck_players_rating_range CHECK (rating >= 0 AND rating <= 100), 
	UNIQUE (name)
);

-- table: positions
CREATE TABLE positions (
	position_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	player_id INTEGER NOT NULL, 
	quantity INTEGER NOT NULL, 
	avg_cost NUMERIC(12, 4) NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (position_id), 
	CONSTRAINT uq_positions_user_player UNIQUE (user_id, player_id), 
	CONSTRAINT ck_positions_quantity_range CHECK (quantity >= 1 AND quantity <= 50), 
	CONSTRAINT ck_positions_avg_cost_non_negative CHECK (avg_cost >= 0), 
	FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE CASCADE, 
	FOREIGN KEY(player_id) REFERENCES players (player_id) ON DELETE CASCADE
);

-- table: price_history
CREATE TABLE price_history (
	price_id INTEGER NOT NULL, 
	player_id INTEGER NOT NULL, 
	price NUMERIC(12, 2) NOT NULL, 
	reason VARCHAR(200) NOT NULL, 
	ts DATETIME NOT NULL, 
	PRIMARY KEY (price_id), 
	CONSTRAINT ck_price_history_price_positive CHECK (price > 0), 
	FOREIGN KEY(player_id) REFERENCES players (player_id) ON DELETE CASCADE
);

-- table: trades
CREATE TABLE trades (
	trade_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	player_id INTEGER NOT NULL, 
	side VARCHAR(4) NOT NULL, 
	quantity INTEGER NOT NULL, 
	price NUMERIC(12, 2) NOT NULL, 
	amount NUMERIC(12, 2) NOT NULL, 
	balance_after NUMERIC(12, 2) NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (trade_id), 
	CONSTRAINT ck_trades_side CHECK (side IN ('BUY', 'SELL')), 
	CONSTRAINT ck_trades_quantity_positive CHECK (quantity > 0), 
	CONSTRAINT ck_trades_price_positive CHECK (price > 0), 
	CONSTRAINT ck_trades_amount_non_negative CHECK (amount >= 0), 
	FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE CASCADE, 
	FOREIGN KEY(player_id) REFERENCES players (player_id) ON DELETE CASCADE
);

-- table: users
CREATE TABLE users (
	user_id INTEGER NOT NULL, 
	nickname VARCHAR(50) NOT NULL, 
	balance NUMERIC(12, 2) NOT NULL, 
	initial_balance NUMERIC(12, 2) NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (user_id), 
	CONSTRAINT ck_users_balance_non_negative CHECK (balance >= 0), 
	CONSTRAINT ck_users_initial_balance_non_negative CHECK (initial_balance >= 0)
);

-- index: ix_positions_player_id
CREATE INDEX ix_positions_player_id ON positions (player_id);

-- index: ix_positions_user_id
CREATE INDEX ix_positions_user_id ON positions (user_id);

-- index: ix_price_history_player_ts
CREATE INDEX ix_price_history_player_ts ON price_history (player_id, ts);

-- index: ix_trades_user_created
CREATE INDEX ix_trades_user_created ON trades (user_id, created_at);
```

自查结果：`players=8`、`price_history=15`、`users=1`、`positions=0`、`trades=0`（seed 后的干净状态）。
`positions` 唯一约束与 `quantity 1–50` CHECK、`trades(user_id, created_at)` 索引、
`price_history(player_id, ts)` 索引均已实际生成。
