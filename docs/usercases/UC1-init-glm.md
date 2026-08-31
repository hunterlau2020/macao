# UC-1 初始化 MACAO 项目配置（`macao init --agteam <team>`）

- **设计日期**：2026-08-31
- **设计人**：glm
- **状态**：用例设计稿（待实现；实现前须过 Schema/测试对账）
- **关联**：吸收并统一现行 `macao init`（模板写入）与 `macao setup`（探测向导）；对齐 PRD v2.4 §17 agmsg 映射、FAQ Q9 静态规范 / 动态运行时、`macao_config.schema.json` 既有字段（`team.name`、`agmsg_member_id`）；回应 codex 3c5ed32 轮 P1-5（无条件覆盖配置）验收标准。
- **agmsg 集成约束**：对 agmsg 的一切读取**只经官方脚本**（`~/.agents/skills/agmsg/scripts/` 下的 `team.sh` / `history.sh` / `identities.sh` / `whoami.sh` / `join.sh`），**禁止直读 `db/`（messages.db）、`teams/`、`run/actas.*`**。探活禁用 `inbox.sh` / `check-inbox.sh`（会 mark-read）。

---

## 1. 前置条件

| #   | 条件                                                    | 不满足时的行为 |
| --- | ----------------------------------------------------- | ------- |
| P1  | 当前目录为 Git 仓库（或用户确认 `--no-git` 裸模式）                    | E1      |
| P2  | agmsg 已安装且 `~/.agents/skills/agmsg/scripts/` 可用       | E2      |
| P3  | `--agteam <team>` 指名的团队存在于 agmsg（`team.sh <team>` 非空） | E3      |
| P4  | 本机至少安装 1 款受支持 CLI（`probe_available_clis` 非空）          | E4      |
| P5  | `macao.yaml` 不存在，或用户显式 `--force`                      | E5（防覆盖） |

## 2. 主成功场景（细化 a–i）

### a. 用户进入 `~/projectX`

记录 `project_root = $(pwd)`；读取 Git 上下文（分支/remote，复用 `detect_git_context`）。

### b. 用户输入 `macao init --agteam stockdb`

### c. 系统读取 agmsg 团队画像（只经脚本）

- **c1** `team.sh stockdb` → 名册 `[{name, type, project}]`（成员数 N、名称、CLI 类型）
- **c2** 对每名成员 `history.sh stockdb <name>` → 通信语料（条数、时间跨度、消息样本）
- **c3 角色启发式推断**（输出必须带置信度，仅供 d 步建议，绝不直接落盘）：

| 信号                                                        | 推断              | 置信度 |
| --------------------------------------------------------- | --------------- | --- |
| 消息中高频出现 diff/commit/修复类内容；或该成员 == `whoami.sh` 当前身份（发起者本人） | Executor 候选     | 高   |
| 常收到"请审查/REVIEW/意见"类消息、回复中含评审语义                            | Reviewer 候选     | 高   |
| 仅偶发闲聊/通知                                                  | 未定 → 交用户指定      | 低   |
| 历史为空（N 条 ≈ 0）                                             | 全部未定 → 走 d 步纯交互 | —   |

### d. 系统生成交互式配置建议（名册 ∩ 本机 CLI 探测 = 可用矩阵）

- **d1 CLI↔成员绑定建议**：成员 `type` 映射 CLI（`codex→codex`、`claude-code→claude`…）；本机未装的成员标 `MISSING`，装了但不在团队的 CLI 标 `EXTRA`（可选纳入）
- **d2 角色建议**：1 名 Executor（默认 c3 最高置信者）+ ≥2 名 Reviewer（其余成员）
- **d3 模型建议**：按 CLI 给默认模型表（opencode→`Qwen3.8 max`、claude-code→`claude-3-7-sonnet`、agy→`gemini-2.0-pro`…），允许逐项改写
- **d4 输出建议表**：`成员 | agmsg_member_id | cli | adapter | 角色 | model | 置信度`，逐行 `[Y/n/编辑]`

### e. 用户逐项确认/修改

空回车 = 接受建议；支持 `--yes` 全默认跳过交互。

### f. 落盘静态配置

- **f1** 组装 `macao.yaml`：`team.name=stockdb`；executor/reviewers 各含 `agmsg_member_id`（schema 已支持；`generate_smart_config` 扩展）
- **f2** 写前 Schema 校验（`validate_config`），失败即中止不落盘
- **f3** 存在旧配置且 `--force`：先 `macao.yaml.bak.<ts>` 原子备份再写；无 `--force` → E5
- **f4** 注入 `.gitignore` 隔离（幂等，复用 `ensure_gitignore_isolation` 8 规则）
- **f5** 非交互修正：若本会话 agent 尚未加入该 agmsg 团队（`identities.sh` 无此项目记录），提示执行 `join.sh stockdb <macao> <type> "$(pwd)"`（MACAO 自身作为编排者入队，PRD §11.6 agmsg 网桥前置条件）

### g. 项目进展判定（信号按优先级）

| 判定        | 信号（任一命中即为"已开始"）                                                                                                 | 后续动作                                                       |
| --------- | --------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- |

| **已开始运行** | ① `.macao/state.db` 存在且含活跃任务；② agmsg 历史含 workflow 形态消息（REVIEW_REQUEST / vote / 任务派发样本文本）；③ `.macao/archive/` 非空 | 提示运行 `macao doctor` + `macao daemon --once` 对账，**不自动改状态库** |
| **新项目**   | 以上全无                                                                                                            | 提示下一步 `macao task create`；建议首个微任务走 `live-run` 演练           |

### h. 项目各个角色状态探测

在 f 已落盘**静态意图**、g 已判定进展之后，对 e 步确认的每个席位做**只读**运行态画像。产出占用矩阵供 i 步落盘。本步**不改角色分配、不推进 FSM、不消费收件箱、不清理 worktree**。

- **h1 探测对象**：`team.executor` + `team.reviewers`（含 e 步纳入的 EXTRA；d1 标 `MISSING` 的席位仍探测，结果必为 `NOT_READY`）。编排者入队仍走 f5，不占席位行。
- **h2 每席位四轨并行**（单轨超时短；失败记 `DEGRADED`/`NOT_READY`，不中止其余席位）：

| 轨 | 唯一合法来源 | 读取 | 硬禁止 |
|---|---|---|---|
| 本机 CLI | 对应 Adapter.`preflight()` + `capabilities()` | `installed` / `version`（探测失败标 `unknown`，禁止默认版本冒充）/ `auth_valid` / `in_matrix` / `can_execute`·`can_review` / `execution_mode` / `supports_worktree` | 拉起长会话、写厂商配置、把 `auth_valid=True` 写成常量 |
| agmsg 身份 | `identities.sh "$(pwd)" <type>`；`whoami.sh "$(pwd)" <type>` 仅描述**当前进程** | 该 `agmsg_member_id` 是否已为本项目注册；type 与 d1 CLI 映射一致 | `inbox.sh` / `check-inbox.sh`（会 mark-read）；直读 `teams/`、`messages.db`、`run/actas.*` |
| 通信近况 | `history.sh <team> <name>`（只读，可与 c2 缓存共用） | 最近消息时戳、是否含未闭环 workflow 样本（REVIEW_REQUEST / vote / 派发）——只作标注 | 把启发式当事实落盘；为探活而 `send.sh` |
| 本地残留 | `.macao/worktrees/<agent_id>/`、`git worktree list`、`.macao/.reviews/<id>.review.yml` | 孤儿 worktree、未归档票面 | `git worktree remove`（清理属 daemon / live-run / reconcile，init 只报告） |

- **h3 会话锁（诚实降级）**：现行官方脚本集无 lock-status；v1 **不**直读 `~/.agents/skills/agmsg/run/actas.*`（越权）。占用综合信号 = 孤儿 worktree ∨ 近实时 history → 标 `BUSY_SUSPECTED`（非确定 `OCCUPIED`）。确定性锁待官方脚本后再升格。
- **h4 存量绑定**（仅 g = 已开始）：只读 `.macao/state.db` 活跃任务，将 `task_id` / `state` / `review_round` / `checkpoint_ref` 挂到对应 `reviewer_id`（优先 `artifacts.reviewer_id`，其次 worktree 路径 `.macao/worktrees/<agent_id>/<task_id>/r<round>`）。**禁止** `update_task_state` / `create_task` / 改 `vote_result.json`。
- **h5 综合判定**（fail-closed，只标状态不改席位）：

| 综合 | 条件（同时满足） |
|---|---|
| **READY** | `preflight.is_ok` ∧ 身份已入队 ∧（Executor 须 `can_execute`；Reviewer 须 `can_review` ∧ `execution_mode ∈ {read_only, sandboxed}` ∧ `supports_worktree=true`）∧ 无 `BUSY_SUSPECTED` |
| **DEGRADED** | 已入队，但 auth/version/capabilities 不完整，或 `BUSY_SUSPECTED`，或存量绑定与静态席位不一致 |
| **NOT_READY** | CLI 未装 / 未入队 / Reviewer 不满足 §12.2 准入硬条件 / `MISSING` |
| **UNBOUND** | e 步跳过或 EXTRA 未纳入 |

- **h6 占用表**（打印后进入 i）：`成员 | 角色 | cli | preflight | agmsg入队 | 近况 | 残留 | 任务绑定 | 综合`。Executor 为 `NOT_READY` 时警告「静态配置已写、动态层标记不可调度」——**不回滚 f**（意图与观测分离，对账交给 `macao doctor`）。

### i. 落盘动态配置

与 f 对偶：f 写 Git 跟踪的**规范**（`macao.yaml`）；i 写 `.macao/` 下的**运行时快照**。二者允许暂时不一致；`macao doctor` 负责对账。i **不是**第三份 yaml，也**不是**任务受理。

- **i1 落盘目标**：仅 `.macao/state.db`（f4 已保证 gitignore）。禁止把探测结果写回 `macao.yaml`（污染静态规范）；禁止新增 `.macao/runtime.yml`（避免三事实源）。
- **i2 表增量**（实现时补 `SCHEMA_DDL`，`CREATE TABLE IF NOT EXISTS`）：

```sql
CREATE TABLE IF NOT EXISTS agent_registry (
    agent_id         TEXT PRIMARY KEY,
    role             TEXT NOT NULL,          -- executor | reviewer
    agmsg_member_id  TEXT,
    cli              TEXT,
    model            TEXT,
    occupancy        TEXT NOT NULL,          -- READY | DEGRADED | NOT_READY | UNBOUND
    probe_json       TEXT NOT NULL,          -- h 步原始探测（含四轨明细）
    bound_task_id    TEXT,                   -- 仅存量只读绑定；新项目为 NULL
    probed_at        TEXT NOT NULL
);
```

- **i3 写入规则**（单一 SQLite 事务；失败回滚 i，**保留** f 已写的 yaml）：

| 进展（g） | 允许的写 | 禁止的写 |
|---|---|---|
| **新项目** | 建库（既有 `SCHEMA_DDL` + `agent_registry`）→ 按 h6 upsert 全员 → `audit_events` 插入 `PROJECT_INITIALIZED`（detail：`team.name`、席位数、occupancy 直方图、`agmsg_member_id` 列表） | `INSERT INTO tasks`；伪造活跃任务 |
| **已开始运行** | 迁移补表 → 按 `agent_id` upsert 本轮探测 → 插入 `ROLE_STATUS_PROBED`（detail 含 occupancy 差量） | `UPDATE tasks` / `create_task` / 改 artifacts / 改 overrides / 消费 message_queue |

- **i4 幂等**：重复 `init --force`：registry 覆盖为最新探测；`PROJECT_INITIALIZED` 仅当库中尚无该 type 时插入，否则只写 `ROLE_STATUS_PROBED`。无 `--force` 且 yaml 已存在 → 仍走 E5，本步不执行。
- **i5 校验**：`probe_json` 必须可 JSON 解析且含四轨键；`occupancy` 枚举闭合；`agent_id` 集合与 f 落盘的 executor+reviewers **双向零差集**（UNBOUND 除外）。失败不落盘，保留旧 registry。
- **i6 完成提示**：打印占用摘要 + 下一步——新项目 `macao task create`（建议先 `live-run`）；存量 `macao doctor` 与 `macao daemon --once`。显式声明：**init 仍不创建任务、不派发 CLI**。

## 3. 备选流

| # | 场景 | 行为 |
|---|---|---|
| A1 | 无 `--agteam` 参数 | 退化为现行 setup 流程（本机 CLI 探测 → 默认 3 Reviewer 建议），并提示"检测到 agmsg 团队 `<available_teams>`，可用 `--agteam` 绑定"——两条入口合一 |
| A2 | 团队成员数 < 3 | 角色建议降级为"1 Executor + 全部其余为 Reviewer"，警告法定人数风险（`policy.min_effective_votes`） |
| A3 | 同一 CLI 多个成员 | 允许（靠 `agmsg_member_id` / `id` 区分席位），模型可各异（29ef7bc 起支持 per-agent model）；h 步按席位分别探测身份与残留 |
| A4 | 部分席位 `BUSY_SUSPECTED` / `DEGRADED` | 仍完成 i 步落盘，占用表标黄；提示勿立即 `task create` / `live-run`，先 `macao doctor` |
| A5 | 确认席位未入队（`identities.sh` 无本项目记录） | 该席位 `NOT_READY`；提示对该成员执行 `join.sh <team> <name> <type> "$(pwd)"`（与 f5 编排者入队分开） |

## 4. 异常流

| # | 场景 | 行为 |
|---|---|---|
| E1 | 非 Git 仓库 | 询问是否裸模式；默认中止（Merge 拓扑门禁 `is_ancestor` 依赖 Git，见遗留决策②） |
| E2 | agmsg 未安装 | 明示"`--agteam` 需要 agmsg"，转 A1 纯本机流程 |
| E3 | 团队不存在 | 列出 `available_teams`，允许现场 `join.sh` 新建或改选 |
| E4 | 无任何受支持 CLI | 中止并给出安装指引（不允许产出不可运行的 macao.yaml） |
| E5 | macao.yaml 已存在且无 `--force` | 拒绝覆盖（对齐现行 `init` 保护语义），提示 `--force` 备份路径；**不执行** h/i |
| E6 | i 步 SQLite 事务失败或 `probe_json` 校验失败 | 回滚动态库写；保留 f 的 `macao.yaml` 与 `.gitignore`；提示 `macao doctor` 后重跑 `init --force` |

## 5. 后置条件

- **成功**：
  - **静态**：`macao.yaml` 通过 Schema 校验且每个成员可追溯（`agmsg_member_id` ↔ roster 名册一一对应）；`.gitignore` 含隔离规则；
  - **动态**：`.macao/state.db` 含与席位双向零差集的 `agent_registry` 快照 + `PROJECT_INITIALIZED` 或 `ROLE_STATUS_PROBED` 审计；
  - 进展判定与占用表已告知用户；
  - **零 FSM 副作用**：不 `create_task`、不 `update_task_state`、不消费 agmsg 收件箱、不删除 worktree。
- **失败**：静态半成品不留（f 写前校验 + 原子改名）；动态半成品不留（i 单事务回滚）。yaml 已成功而 i 失败 → E6，不假装动态层已就绪。

## 6. 验收标准（可测）

1. `--force` 备份语义 + 默认拒覆盖（正反例）
2. 建议表与 roster / CLI 探测交集一致；`MISSING` / `EXTRA` 正确标注
3. 角色启发式：构造"评审语义"历史语料 → Reviewer 建议命中；空历史 → 全交互
4. 产出 `macao.yaml` 过 `validate_config`，且 `agmsg_member_id` 与 `team.sh` 名册**双向零差集**
5. 进展判定：含 `state.db` 活跃任务 → "已开始"+doctor 提示；纯净目录 → "新项目"
6. 全程对 agmsg 仅脚本调用（代码审计断言：无 `sqlite3.connect(messages.db)`、无直读 `teams/`、无直读 `run/actas.*`；探测路径**无** `inbox.sh` / `check-inbox.sh`）
7. 角色探测：构造三 fixture——① CLI 未装 → `NOT_READY`；② `identities.sh` 无本项目记录 → `NOT_READY` + A5 提示；③ 残留 `.macao/worktrees/<id>/` → `BUSY_SUSPECTED`/`DEGRADED`。占用表与 fixture 一致。Reviewer 缺 `supports_worktree` 不得标 `READY`
8. 动态落盘：新项目 → `agent_registry` 行数 = executor+reviewers，`tasks` 表为空，恰一条 `PROJECT_INITIALIZED`；存量项目（预置活跃任务）→ `tasks.state` 与行数不变，新增 `ROLE_STATUS_PROBED`，registry upsert 不删旧任务
9. `init --force` 幂等：第二次只新增 `ROLE_STATUS_PROBED`，不重复 `PROJECT_INITIALIZED`；i 校验失败（坏 `probe_json`）不覆盖旧 registry（E6）

## 7. 实现落点

| 位置 | 变更 |
|---|---|
| `src/macao/cli/main.py:init` | 重写，吸收 `setup`（`setup` 保留为别名一个版本期） |
| `src/macao/cli/wizard.py` | 新增五个纯函数：`load_agmsg_roster()` / `infer_roles_from_history()` / `detect_project_progress()` / `probe_role_status()` / `persist_runtime_registry()`；history 与探测样本 fixture 化可单测（不依赖真实 agmsg / 真实 CLI） |
| `src/macao/storage/db.py` | `SCHEMA_DDL` 增 `agent_registry`；存量库 `IF NOT EXISTS` 迁移 |
| `src/macao/storage/store.py` | `upsert_agent_registry()` / `list_agent_registry()`；**无**任务写入口从 init 路径暴露 |
| `docs/MACAO_PRD_v2.md` §11.4 / §17 | 补 `agent_registry` DDL 与本 UC 交互序列（h/i） |
| `tests/` | 按第 6 节验收标准逐条建测（含 E1–E6、A4–A5；h 步注入假 `inbox.sh` 断言未被调用） |

## 8. 设计自审

- c3 角色启发式为**建议器**而非决策器：所有推断须经 e 步用户确认——与本项目 fail-closed 纪律一致（拒绝把启发式结果当事实落盘）
- g 步仍**只读**状态库：进展判定不写库。动态层的唯一写入口是 i，且白名单为 `agent_registry` upsert + 两类审计事件——**不是**放宽"init 可改 FSM"
- f / i 分离落实 FAQ「静态规范 vs 动态运行时」：`macao.yaml` 是期望，`agent_registry` 是观测；允许 DEGRADED 快照与规范并存，由 doctor 对账，禁止把观测写回 yaml
- h 步禁用 `inbox.sh`：探活不得产生 mark-read 副作用；会话锁无官方脚本则标 `BUSY_SUSPECTED` 而非假装 `OCCUPIED`——与「探测失败禁止默认版本冒充」同一诚实原则
- 本 UC 吸收 setup 后，codex P1-5 的两条验收标准（拒覆盖/探测驱动候选）成为 P5/E4 与 d1 的内在属性
- 遗留决策点（实现前需拍板）：①模型默认表是否独立配置文件化；②`--no-git` 裸模式是否真正支持（拓扑门禁 `is_ancestor` 依赖 Git，建议 v1 拒绝裸模式）；③是否向上游 agmsg 要一条只读 `lock-status.sh`，以便把 `BUSY_SUSPECTED` 升格为确定占用
