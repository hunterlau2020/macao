# UC-1 初始化 MACAO 项目配置（`macao init --agteam <team>`）

- **设计日期**：2026-08-31
- **设计人**：glm
- **状态**：用例设计稿（待实现；实现前须过 Schema/测试对账）
- **关联**：吸收并统一现行 `macao init` 与 `macao setup`；总体目录见 `docs/usercases/README.md`；FAQ Q5/Q10–Q16；PRD v2.4 §3；评审方法以 `docs/MACAO_REVIEW_GUIDELINES.md` 为准、`docs/reference/*.md` 为方法来源；留痕只进 `docs/reviews/`；回应 codex 3c5ed32 轮 P1-5。
- **agmsg 定位**：总线**主用途是通知**其他 team agents（init 完成、`next_action`、请谁行动）。名册/历史仍可经官方脚本读取（`team.sh` / `history.sh` / `identities.sh` / `whoami.sh` / `join.sh`），但 **agmsg 正文不是 FSM 事实源，也不是评审结论**。禁止直读 `db/`、`teams/`、`run/actas.*`；探活禁用 `inbox.sh` / `check-inbox.sh`（会 mark-read）。

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

| 判定 | 信号 | 后续动作 |
|---|---|---|
| **已开始（确定）** | `.macao/state.db` 存在且含活跃任务 | 进入 h 做 FSM 精识别（仍不擅自改状态库） |
| **可疑已开始** | 无活跃任务，但 ① agmsg 历史含 workflow 样本文本，或 ② `.macao/archive/` 非空 | 进入 h；**推不出唯一 10 态则问管理员**（init 允许，见 h5） |
| **新项目** | 以上全无 | h 全员 `IDLE`；提示 `macao task create` / `live-run` |

### h. 项目各个角色状态探测

目的：回答调度问题——**现在该通知 Reviewer 评审，还是该等 Executor 继续 coding？** 答案来自**任务级 FSM（单一事实源）**。init **默认只识别、不转移**；**识别不出唯一态时问管理员**（本用例是初始化，管理员在场），不得用 CLI 自报或 agmsg 闲聊来猜。

编排器是**无模型的规则机**（流程裁判 + 邮差），**不读、不写、不裁决项目内容**（FAQ Q10：最小感知仅 Git 拓扑 + 通信拓扑）。下表把「下一步」拆成内容写者 vs 编排器动作，避免把通知误写成「编排器懂项目」。

| 动作 | 内容写者（接模型） | 编排器（规则，不读业务） | 禁止编排器做的 |
|---|---|---|---|
| 开任务 | **管理员或执行者** 规划并 `macao task create` | 校验 Schema、建 `tasks` 行、发信封 | 拆解需求、写 WBS |
| 评审申请 | **执行者** 全文 → `docs/reviews/*-review-request-*.md`；`.dev.yml` **只含摘要 + 指针 + sha256** | 校验 manifest、把指针原样放进 `REVIEW_REQUEST`；agmsg ping 更短（路径/SHA/round） | 写/改申请全文或摘要 |
| 票面结论 | **各专家** 全文 → `docs/reviews/*-review-result-<mid>-<reviewer>.md`；`.review.yml` **只含摘要 + 问题索引 + 指针 + 总票** | 校验 manifest、按**加权**决策表写 `vote_result.decision`；`issues_index` **原样拼接**各专家索引（不合并同类项） | 归纳意见、合并「相同问题」、撰写 `issues_to_fix` 正文 |
| 意见筛选 | **执行者** 读全文与索引，写采纳清单（下轮 `.dev.yml` 或 `adoption.yml`） | 只检测清单是否按 Schema 出现 | 代为决定采纳哪条 |

`vote_result.decision` 仍是计票（可加权），不是采纳清单。现 Schema 里由编排器填写的 `next_step.issues_to_fix.description/suggestion` **废止**（那是内容写作）。

#### h0. 产物分层、问题索引与加权计票（实现前须回写 PRD §2.2–2.3 / Schema）

**（1）三层载体——agmsg 有体积上限，yml 不当全文库**

| 层 | 放什么 | 体积 |
|---|---|---|
| agmsg 正文 | ping：谁行动、`checkpoint_ref` 短 SHA、manifest 路径、全文路径 | 最短 |
| `.dev.yml` / `.review.yml` | 信封：status/vote、一段 `summary`（建议 ≤2KB）、`issues[]` 索引（id/severity/one-line）、`full_document.path` + `sha256` | 摘要 |
| `docs/reviews/*.md` | 评审申请 / 评审结论**全文**（GUIDELINES §1.3 命名） | 不限 |

编排器只校验 yml Schema 与 sha256 是否对得上文件字节，**不解析 md 语义**。sha256 对不上 → 该 manifest 无效票（fail-closed）。

**（2）`vote_result.json`：总票 + 问题目录 + 执行者汇总段（编排器不写「采纳」，采纳由执行者写入本文件汇总段）**

一份评审结论 = 一张总票 + 若干问题点；不同模型的问题点**默认视为不同条目**（id 必须带 `reviewer_id` 前缀，禁止编排器做语义去重）。

`vote_result` 建议三段：

1. **计票**（编排器算）：各席位 `vote`、`weight`、加权合计、`decision`
2. **问题目录 `issues_index`**（编排器**复制**自各 `.review.yml` 的 `issues[]`，不改写 description）：`{id, reviewer, severity, summary, full_document, sha256}`。这回答「要不要体现在 vote_result」——**要目录，不要正文、不要合并**；编排器**不标采纳**
3. **汇总段 `issues_summary`**（**执行者写**，PRODUCT-FACTS F-13/F-16）：归并「同一问题被哪些专家发现」（`found_by[]`）、标题清单、正文索引、**是否采纳**——写入本文件，不是另立文件；执行者不写、不改 `decision` 与机器段（见 UC-6 b）

现行 `summary.critical_issues` 若保留，只能是各 manifest 里已声明计数的**求和**，禁止编排器读全文再统计。

**（3）权重：静态政策，不从「写得细」推断**

细致程度因模型而异，用票数一刀切确实粗。但权重必须是 **`macao.yaml` 里管理员写死的政策**（`team.reviewers[].vote_weight`，默认 1），**禁止**编排器根据字数/问题条数自动加权重——那就是在评判内容。

加权规则（仍是确定性函数，无模型）：

- 有效权重 = 未弃权席位的 `vote_weight` 之和（弃权仍不进分母）
- 赞成加权占比 ≥ 2/3 且满足法定人数 → `APPROVED`；反对同理 → `REWORK_REQUIRED`；否则 Deadlock → **管理员**（不是执行者）
- **双门槛**：席位法定人数 `⌈2N/3⌉` **仍然保留**（防一票权重大户单独过门）
- **独裁帽**：任一席位 `vote_weight / Σweight < 2/3`，配置校验失败则拒绝启动
- 权重只作用于总票 `YES/NO`，不作用于单条问题是否成立——单条是否改代码仍是执行者内容工作

2 人且权重 1:1 时行为与现决策表相同；3 人可把更细的模型配成 2、其余为 1，但仍不能单人 ≥ 2/3。

#### h1. 任务级 FSM（调度罗盘，Layer 1）

只读复用 `recognize_agent_state` 的作用域规则（当前 `state` + `checkpoint_ref` / `review_round`；无活跃任务则视为 `IDLE`）。**禁止**把 Layer 2/3 推断当成转移。`next_action` 只表示「通知谁 / 等哪份产物」，**不是**编排器去写那份产物。

| `task_state` | `next_action` | 实际由谁做事 |
|---|---|---|
| `IDLE`（无任务） | `PROMPT_TASK_CREATE` | **管理员/执行者** 创建任务；编排器只收表单 |
| `CODING` / `REWORK` | `WAIT_OR_NOTIFY_EXECUTOR` | 执行者编码；返工时由执行者筛选上轮意见 |
| `READY_FOR_REVIEW` | `ROUTE_REVIEW` | 执行者**已经写好** `.dev.yml`；编排器校验信封并 ping 专家（不改摘要） |
| `WAITING_REVIEW` | `WAIT_OR_NOTIFY_REVIEWERS` | 专家写 `.review.yml` + `docs/reviews/`；编排器只催票/收票 |
| `CONSENSUS_CHECK` | `TALLY_OR_ASK_ADMIN` | 编排器跑决策表；僵局问**管理员**（不是问执行者自裁） |
| `MERGING` | `SIGNOFF_OR_MERGE` | 规则合并 + 管理员签字；编排器不总结评审 |
| `UNKNOWN` 或无法唯一推出 | `ASK_ADMIN` | 问管理员（init）；见 h5 |
| `DONE` / `CANCELLED` | `PROMPT_TASK_CREATE` | 同 IDLE：等人开下一单 |

这张表回答「通知谁」。Layer 1 唯一时不问人；不唯一时不要猜，走 h5。编排器**从不**因「需要懂项目」而调用模型。

#### h2. 席位投影（各角色「此刻该做什么」）

任务只有一个 `state`。各角色的「状态」是该态在席位上的投影 + 本席位 Layer 1 产物是否已交（PRD §1.2 Reviewer 侧 `REVIEWING` 即此）。

| 任务态 | Executor `role_view` | Reviewer `role_view`（每席位独立看产物） |
|---|---|---|
| `IDLE` / 无任务 | `AWAIT_TASK`（规划并提交任务的是人或执行者） | `AWAIT_TASK` |
| `CODING` / `REWORK` | `SHOULD_CODE`（`REWORK` 含阅读意见并筛选采纳） | `IDLE_WAIT_DISPATCH` |
| `READY_FOR_REVIEW` | `CHECKPOINT_SUBMITTED`（评审申请=已落盘的 `.dev.yml`） | `IDLE_WAIT_DISPATCH` |
| `WAITING_REVIEW` | `AWAIT_REVIEWS` | 无本轮合法 `.review.yml` → `SHOULD_REVIEW`（即 `REVIEWING`）；已交 → `REVIEW_SUBMITTED` |
| `CONSENSUS_CHECK` | `AWAIT_DECISION` | `AWAIT_DECISION` |
| `MERGING` | `AWAIT_MERGE` | `AWAIT_MERGE` |
| `UNKNOWN` | `AWAIT_HUMAN`（先 h5 问管理员） | `AWAIT_HUMAN` |
| `DONE` / `CANCELLED` | `AWAIT_TASK` | `AWAIT_TASK` |

`artifact_status` ∈ `ABSENT` / `VALID` / `STALE`（ref/round 不匹配）/ `CONSUMED`。STALE 不得把 `SHOULD_REVIEW` 改成 `REVIEW_SUBMITTED`。

#### h3. 向 CLI 询问 + 从消息界面判断（Layer 2/3，旁证）

对应原设计「问每个 CLI 当前任务/当前 FSM 态」和「从消息界面判断」。**默认不拉起新会话**（init 不烧额度、不抢 actas 锁）。

- **h3a 消息界面（Layer 2，默认做）**：只读已有信号——PTY/会话日志（strip_ansi）、孤儿 worktree、`history.sh` 近况、未归档 `.review.yml`。产出 `ui_hint`（如 `pty_idle` / `review_prompt_visible` / `permission_dialog`）。只预警，不改 `next_action`。禁用 `inbox.sh`（会 mark-read）。
- **h3b 向 CLI 询问（Layer 3，显式 `--ask-clis`）**：对可派发席位发一条短问：「当前任务是什么？当前状态是 10 态中哪一种？」超时 / 无枚举内回答 → `NO_REPLY` / `INVALID_SELF_REPORT`。解析结果写入 `cli_self_report`，**禁止**用它覆盖 `task_state`。
- **h3c 对账**：一致 → `corroborated`；不一致 → **不得静默信库**，进入 h5 问管理员（A6）。

#### h4. 派发门禁（次级，不驱动调度）

`dispatchable` = Adapter.`preflight()`+`capabilities()` 通过 ∧ `identities.sh` 已入队 ∧ Reviewer 满足 §12.2（`can_review` ∧ sandboxed ∧ `supports_worktree`）。`next_action=WAIT_OR_NOTIFY_REVIEWERS` 但某席位 `dispatchable=false`：调度结论不变，该席位标阻塞，提示 `doctor` / A5 `join.sh`。不可调度 ≠ 改去等 Executor。

#### h5. 编排器无法判断 → 问管理员（init 特有）

本步是初始化向导，管理员在终端前。凡 Layer 1 不能唯一推出 10 态（含 X2–X5、可疑已开始、自报互斥），**停下来问人**，不要 HOLD 装懂，也不要把问题丢给 agmsg 里的其他 agent。

向管理员展示：已见产物 / 库中 `tasks.state` / 各席位 `artifact_status` / 旁证差异。选项闭合：

1. 指定当前为 10 态之一（并确认 `next_action`）
2. 当作新项目：全员 `IDLE` / `PROMPT_TASK_CREATE`（不伪造历史任务）
3. 中止 init 的动态落盘（保留 f 的 yaml）→ E6/E7

管理员选择写入审计 `ADMIN_STATE_RESOLVED`（`signer`、时戳、选项、证据摘要）。**默认不** `update_task_state`；仅当管理员显式确认「以该态写入任务库」才改 `tasks.state`（视为 init 阶段的人工命令，等同 override 语义，必须留痕）。

`--yes` 不得代选：无法唯一判定 → `next_action=ASK_ADMIN`，动态层按未决议落盘或中止 i（A7），禁止用启发式填态。

#### h5b. 其余异常（仍可能升级为问管理员）

| # | 场景 | 行为 |
|---|---|---|
| X1 | 无活跃任务且无可疑信号 | 全员 `IDLE` / `AWAIT_TASK` / `PROMPT_TASK_CREATE`；不问 |
| X2 | `tasks.state` 与 Layer 1 产物矛盾 | **问管理员**（不要自行 E1/E2，也不要只提示 daemon） |
| X3 | `--ask-clis` 无应答或非枚举 | 旁证记 `NO_REPLY\|INVALID`；若 Layer 1 已唯一则不问；否则问管理员 |
| X4 | 多名 CLI 自报互斥 | **问管理员**；禁止用投票打破互斥（GUIDELINES：真理不等于投票） |
| X5 | 消息界面像卡死 | `ui_hint` 预警；Layer 1 不唯一则问管理员；init **不**触发运行期 E8 |

#### h6. 探测表（进入 i）

`成员 | 角色 | task_state | role_view | artifact | cli_self_report | ui_hint | dispatchable`。表首或页脚打印全局唯一的 **`next_action`**（可为 `ASK_ADMIN`）。`dispatchable=false` 不改变「该等谁」；`ASK_ADMIN` 时不把行动通知发出去。

### i. 落盘动态配置

与 f 对偶：f 写 Git 跟踪的**规范**；i 把 h 的 **FSM 观测快照**写入 SQLite。i **不是**第三份 yaml，也**不是**任务受理或状态转移。

- **i1 落盘目标**：仅 `.macao/state.db`。禁止把观测写回 `macao.yaml`；禁止 `.macao/runtime.yml`。
- **i2 表增量**（`CREATE TABLE IF NOT EXISTS`）：

```sql
CREATE TABLE IF NOT EXISTS agent_registry (
    agent_id          TEXT PRIMARY KEY,
    role              TEXT NOT NULL,       -- executor | reviewer
    agmsg_member_id   TEXT,
    cli               TEXT,
    model             TEXT,
    task_id           TEXT,                -- 无活跃任务为 NULL
    task_state        TEXT NOT NULL,       -- 10 态之一；无任务为 IDLE
    role_view         TEXT NOT NULL,       -- h2 投影
    artifact_status   TEXT NOT NULL,       -- ABSENT | VALID | STALE | CONSUMED
    next_action       TEXT NOT NULL,       -- 含 ASK_ADMIN；每行冗余同一值
    dispatchable      INTEGER NOT NULL,    -- 0/1 派发门禁
    cli_self_report   TEXT,                -- 10 态 | NO_REPLY | INVALID | NULL(未询问)
    ui_hint           TEXT,
    discrepancy       INTEGER NOT NULL,    -- 0/1 自报/界面与投影不一致
    probe_json        TEXT NOT NULL,
    probed_at         TEXT NOT NULL
);
```

- **i3 写入规则**（单事务；失败回滚 i，保留 f 的 yaml）：

| 进展（g） | 允许的写 | 禁止的写 |
|---|---|---|
| **新项目** | 建库 → upsert 全员（`task_state=IDLE`，`next_action=PROMPT_TASK_CREATE`）→ `PROJECT_INITIALIZED` | `INSERT INTO tasks`；把询问结果写成非 IDLE |
| **已开始 / 可疑** | 迁移补表 → upsert 本轮投影（含管理员裁决）→ `ROLE_STATUS_PROBED`；若发生 h5 则另写 `ADMIN_STATE_RESOLVED` | 未经管理员确认的 `UPDATE tasks.state`；发 AEP 当评审结论；把 agmsg 正文当事实源 |

- **i4 幂等**：`init --force` 覆盖 registry 为最新观测；`PROJECT_INITIALIZED` 仅首次插入，其后只写 `ROLE_STATUS_PROBED`。无 `--force` 且 yaml 已存在 → E5，不跑 h/i。
- **i5 校验**：同一快照内所有行的 `task_state`、`next_action` 必须一致；`role_view` 必须可由 `(role, task_state, artifact_status)` 复现；`agent_id` 与 f 的 executor+reviewers 双向零差集。失败不覆盖旧 registry。
- **i6 完成提示**（按 `next_action` 分支，init 仍不派发）：

| `next_action` | 提示 |
|---|---|
| `PROMPT_TASK_CREATE` | 提示**管理员或执行者** `macao task create`（编排器不拆解需求）；建议先 `live-run` |
| `WAIT_OR_NOTIFY_EXECUTOR` | ping 执行者去编码；返工时 ping 其阅读 `.review.yml` / `docs/reviews/` 并自行筛选采纳 |
| `ROUTE_REVIEW` / `WAIT_OR_NOTIFY_REVIEWERS` | ping 专家：申请正文在 `.dev.yml`（执行者已写），结论写 `docs/reviews/`；编排器不代写摘要 |
| `ASK_ADMIN` | 未决议：打印证据，等待管理员（`--yes` → A7） |
| `TALLY_OR_ASK_ADMIN` | 计票由规则完成；僵局才 `macao override list`（管理员，不是执行者自裁） |
| `SIGNOFF_OR_MERGE` | `macao merge approve` |

- **i7 通知与评审留痕**（agmsg 只送信，不存结论）：
  - init 成功后，用 `send.sh` ping **该行动的席位**。ping 只含：`next_action`、短 SHA、产物路径（执行者申请=`.dev.yml`，专家结论=`docs/reviews/`）。**不含**任务摘要、意见归纳、采纳建议。
  - 评审过程与结论：**方法** = `docs/MACAO_REVIEW_GUIDELINES.md`（权威）+ `docs/reference/REVIEW_METHODOLOGY.md` / `REVIEW_GUIDE.md`（方法来源）；**留痕** = `docs/reviews/<yyyy-MM-dd>-review-result-<mid>-<reviewer>.md` 及申请件 `docs/reviews/<yyyy-MM-dd>-review-request-*.md`（GUIDELINES §1.3）。门禁实时状态只更新 `docs/reviews/STATUS.md`。
  - 禁止：把 L1–L4 / 票面 / Required action 只写在 agmsg 消息里；禁止用 agmsg 历史代替 `docs/reviews/` 审计。
  - `--yes` 且 `next_action=ASK_ADMIN`：不发「请开始评审」类通知（避免在未决议时把团队拉进错阶段）。

## 3. 备选流

| # | 场景 | 行为 |
|---|---|---|
| A1 | 无 `--agteam` 参数 | 退化为现行 setup 流程（本机 CLI 探测 → 默认 3 Reviewer 建议），并提示"检测到 agmsg 团队 `<available_teams>`，可用 `--agteam` 绑定"——两条入口合一 |
| A2 | 团队成员数 < 3 | 角色建议降级为"1 Executor + 全部其余为 Reviewer"，警告法定人数风险（`policy.min_effective_votes`） |
| A3 | 同一 CLI 多个成员 | 允许（靠 `agmsg_member_id` / `id` 区分席位），模型可各异；h2 按席位分别投影产物（同一二进制、两张票） |
| A4 | 部分席位 `dispatchable=false` | 不改 `next_action`；该席位标阻塞，提示 `doctor`；其余席位照常投影 |
| A5 | 确认席位未入队（`identities.sh` 无本项目记录） | `dispatchable=false`；提示 `join.sh <team> <name> <type> "$(pwd)"`（与 f5 编排者入队分开） |
| A6 | CLI 自报 / 消息界面与 h2 投影不一致 | **问管理员**（h5）；落盘 `discrepancy=1`；未裁决前 `next_action=ASK_ADMIN` |
| A7 | `--yes` 且无法唯一判定 10 态 | 禁止启发式填态；`next_action=ASK_ADMIN`；不发行动通知；退出码非 0 或明确 UNRESOLVED，提示去掉 `--yes` 重跑 |

## 4. 异常流

| # | 场景 | 行为 |
|---|---|---|
| E1 | 非 Git 仓库 | 询问是否裸模式；默认中止（Merge 拓扑门禁 `is_ancestor` 依赖 Git，见遗留决策②） |
| E2 | agmsg 未安装 | 明示"`--agteam` 需要 agmsg"，转 A1 纯本机流程 |
| E3 | 团队不存在 | 列出 `available_teams`，允许现场 `join.sh` 新建或改选 |
| E4 | 无任何受支持 CLI | 中止并给出安装指引（不允许产出不可运行的 macao.yaml） |
| E5 | macao.yaml 已存在且无 `--force` | 拒绝覆盖（对齐现行 `init` 保护语义），提示 `--force` 备份路径；**不执行** h/i |
| E6 | i 步 SQLite 事务失败或快照校验失败 | 回滚动态库写；保留 f 的 yaml 与 `.gitignore`；提示 `macao doctor` 后 `init --force` |
| E7 | 管理员选「中止动态落盘」或 `--yes`+未决议且策略为硬失败 | 不写 registry 或只写 `ASK_ADMIN` 未决议行（实现二选一，须单测锁死）；不通知团队开始评审 |

## 5. 后置条件

- **成功**：
  - **静态**：`macao.yaml` 通过 Schema 校验且每个成员可追溯（`agmsg_member_id` ↔ roster 名册一一对应）；`.gitignore` 含隔离规则；
  - **动态**：`.macao/state.db` 含与席位双向零差集的 `agent_registry`（同一 `task_state` / `next_action`）+ `PROJECT_INITIALIZED` 或 `ROLE_STATUS_PROBED`；
  - 用户看到 **`next_action`**；若曾歧义，审计含 `ADMIN_STATE_RESOLVED`；
  - 该行动席位收到 agmsg **通知**（ping，非结论）；
  - **零擅自 FSM 副作用**：未经管理员确认不 `update_task_state`、不发 AEP 评审结论、不消费收件箱、不删除 worktree。
- **失败**：静态半成品不留（f 写前校验 + 原子改名）；动态半成品不留（i 单事务回滚）。yaml 已成功而 i 失败 → E6，不假装动态层已就绪。

## 6. 验收标准（可测）

1. `--force` 备份语义 + 默认拒覆盖（正反例）
2. 建议表与 roster / CLI 探测交集一致；`MISSING` / `EXTRA` 正确标注
3. 角色启发式：构造"评审语义"历史语料 → Reviewer 建议命中；空历史 → 全交互
4. 产出 `macao.yaml` 过 `validate_config`，且 `agmsg_member_id` 与 `team.sh` 名册**双向零差集**
5. 进展判定：有活跃任务 → 已开始并进入 h；仅 agmsg 形态/仅 archive → 可疑，推不出 10 态则问管理员；纯净目录 → 全员 `IDLE` / `PROMPT_TASK_CREATE`
6. agmsg：代码审计无直读 `messages.db` / `teams/` / `run/actas.*`、探测路径无 `inbox.sh`；init 成功后的 `send.sh` 正文不含 L1–L4 结论与评审摘要，只含 ping + 产物路径（`.dev.yml` / `docs/reviews/`）
7. FSM 罗盘：预置 `CODING` 且无合法 `.dev.yml` → `WAIT_OR_NOTIFY_EXECUTOR`。预置 `READY_FOR_REVIEW` + 合法 `.dev.yml` → `ROUTE_REVIEW`（编排器不得改写 `.dev.yml` 摘要）。预置 `WAITING_REVIEW` + 仅 A 交合法票 → A=`REVIEW_SUBMITTED`、B=`SHOULD_REVIEW`
8. 无法判断须问人：`CODING` 但已有未消费合法 `.dev.yml` → h5，不自动写申请、不自动 E2。`--yes` 同 fixture → A7。自报互斥不得用多数票、也不得让执行者自裁 `decision`
9. 内容/流程：单测断言编排器路径不调用 LLM；`vote_result.decision` 仅由票数字典写出；fixture 中「意见采纳清单」只允许出现在执行者产物（下一轮 `.dev.yml` 或独立采纳文件），不得由编排器生成

## 7. 实现落点

| 位置 | 变更 |
|---|---|
| `src/macao/cli/main.py:init` | 重写，吸收 `setup`（`setup` 保留为别名一个版本期） |
| `src/macao/cli/wizard.py` | 新增：`load_agmsg_roster()` / `infer_roles_from_history()` / `detect_project_progress()` / `recognize_task_fsm()` / `project_role_views()` / `collect_cli_side_evidence()` / `ask_admin_to_resolve_fsm()` / `persist_runtime_registry()` / `notify_team_next_action()` |
| `src/macao/storage/db.py` | `SCHEMA_DDL` 增 `agent_registry` |
| `src/macao/storage/store.py` | `upsert_agent_registry()`；init 默认不暴露任务写入口；仅 h5 确认后可写态 |
| `docs/MACAO_PRD_v2.md` §2.2 / §2.3 / Schema | yml=摘要+指针；`issues_index` 原样拼接；废止编排器代写 `issues_to_fix` 正文；`vote_weight` + 双门槛 + 独裁帽 |
| `tests/` | 第 6 节（含 E1–E7、A4–A7、X2/X4、`--yes` 歧义、`send.sh` 正文不含评审结论） |

## 8. 设计自审

- c3 仍为建议器：角色启发式经 e 确认；agmsg 历史只用于建议与通知上下文，不当 FSM 事实
- **编排器不介入内容**（FAQ Q10）：不规划任务、不写评审申请、不定哪些意见可采纳。`REVIEW_REQUEST` 是信封；正文是执行者的 `.dev.yml`。`vote_result.decision` 是计票，采纳清单是执行者返工产物
- **调度罗盘是任务 FSM**；init 推不出唯一态时**问管理员**，不问执行者自裁、不用 CLI 自报多数决
- **agmsg = 通知**：ping 不含摘要；评审方法看 `MACAO_REVIEW_GUIDELINES.md` 与 `docs/reference/*.md`；结论只落 `docs/reviews/*.md`
- `--yes` 在歧义上 fail-closed（A7）
- 遗留决策点：①模型默认表；②`--no-git`；③`--ask-clis`；④E7 硬失败 vs `ASK_ADMIN` 行；⑤采纳清单文件名（建议 `adoption.yml` 按 issue `id` 引用，不复用 `vote_result`）；⑥`vote_weight` 默认全 1 直到管理员显式配置，Loader 强制独裁帽
