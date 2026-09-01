# UC-2 任务受理（`macao task create`）

- **设计日期**：2026-09-01
- **设计人**：glm
- **状态**：用例设计稿（待实现；实现前须过 Schema/测试对账）
- **关联**：目录见 `docs/usercases/README.md`；PRD v2.5 §3.3（E1）、§14.1 第 3 步、§11.4（tasks 表）；FAQ Q13（编排器不规划、不拆 WBS）；UC-1 h1（`IDLE → PROMPT_TASK_CREATE` 的落点）。
- **边界声明**：任务**规划**（拆需求、写验收、选分支）是**人或执行者 CLI 的内容工作**；编排器只做**表单受理**：Schema 校验、建 `tasks` 行、E1 转移、投递 `DEVELOPMENT_STARTED` 信封。编排器无模型（FAQ Q5），不得生成/补全/改写标题与验收标准。

---

## 1. 前置条件

| # | 条件 | 不满足时的行为 |
|---|---|---|
| P1 | `macao.yaml` 存在且过 `validate_config` | E1 |
| P2 | `.macao/state.db` 可写（init 已落动态层） | E2 |
| P3 | 当前无活动任务（MVP 串行编排，PRD §14.2 并发声明） | E3 |
| P4 | 调用者身份为管理员或 executor 席位（`agent_registry` 有记录） | E4 |
| P5 | Git 工作区干净（无未提交变更） | E5 |

## 2. 主成功场景

### a. 用户提交表单

`macao task create --title "<标题>" --acceptance "<可测判据>..." --branch feature/x [--target main]`

**最小 Schema**（PRD §14.1 第 3 步）：

| 字段 | 必填 | 校验 |
|---|---|---|
| `title` | ✅ | 非空字符串 |
| `acceptance[]` | ✅ | 非空数组；每条为可测试判据（映射 `DEVELOPMENT_STARTED.success_criteria`）；不得是"做好/优化"类不可测表述——编排器只查非空与长度，**不判语义** |
| `source_branch` | ✅ | 存在于本地 Git；缺省报错（E6） |
| `target_branch` | ✅ | 存在于本地 Git；缺省报错（E6） |
| `expected_artifacts[]` | 可选 | 路径列表 |

### b. 编排器校验（纯规则，无模型）

b1 Schema 校验（缺任一必填 → E6 拒绝，不建半行）；b2 `source != target`；b3 Git 拓扑：`target` 为 `source` 的祖先或可 ff；b4 P3 串行锁（同一时刻仅一个活动任务）。

### c. 建任务记录

`task_id = task-<yyyymmddHHMMSS>-<hash8>`（State Store 生成）；写 `tasks` 行：`state=IDLE→CODING`、`review_round=1`、`checkpoint_ref=NULL`；审计事件 `TASK_CREATED`（含表单全文快照 + 提交者身份）。

### d. E1 状态转移

`IDLE → CODING`（命令型来源，`fsm.transition(trigger="E1")`）；`agent_registry` 全席位的 `task_state` 冗余列同步刷新，Executor `role_view=SHOULD_CODE`、Reviewer `role_view=IDLE_WAIT_DISPATCH`。

### e. 投递 `DEVELOPMENT_STARTED` 信封

AEP 消息（Type A）只含：`task_id`、`title`、`success_criteria`、`source_branch`、`target_branch`、`expected_artifacts`。**不含**：编排器自拟的实施步骤、风险分析、代码指引。agmsg 对 executor 席位发 ping：「task `<id>` 已受理，开始 CODING；验收标准见 DEVELOPMENT_STARTED 信封」。

### f. 完成提示

打印 `task_id`、当前 FSM 态、`next_action=WAIT_OR_NOTIFY_EXECUTOR`；提示 UC-3 入口（执行者写 `.dev.yml` + 申请全文）。

## 3. 备选流

| # | 场景 | 行为 |
|---|---|---|
| A1 | acceptance 由执行者 CLI 代为起草后提交 | 允许（内容写者是执行者）；编排器仍只做 Schema 校验 |
| A2 | 调用者是未注册席位的 CLI | E4；提示 `join.sh` / `macao init --force` 补注册 |
| A3 | `--branch` 缺省 | 拒绝（E6）——MVP 不自动派生分支名（那是规划行为） |
| A4 | 上一任务处于 `DONE`/`CANCELLED` 终态 | 视为无活动任务，正常受理（终态不占串行锁） |

## 4. 异常流

| # | 场景 | 行为 |
|---|---|---|
| E1 | 无合法 `macao.yaml` | 中止，提示 `macao init` |
| E2 | State Store 不可写 | 中止；不投递任何 AEP（先建库后投递，防孤儿消息） |
| E3 | 已有活动任务（非终态） | 拒绝并列出当前任务与态；提示 `macao status` / `override resolve CANCEL` |
| E4 | 调用者非管理员/executor 席位 | 拒绝（评审者不得开任务，防利益冲突）；审计 `TASK_CREATE_DENIED` |
| E5 | Git 工作区脏 | 拒绝：checkpoint 硬绑定要求评审对象可追溯；提示先 commit/stash |
| E6 | 表单缺必填或 Git 拓扑校验失败 | 原子拒绝：不建 tasks 行、不发 AEP、不转移；错误逐字段指出 |

## 5. 后置条件

- **成功**：`tasks` 含新行（`CODING`/round=1）；审计含 `TASK_CREATED`；executor 收到 `DEVELOPMENT_STARTED` + agmsg ping；`next_action=WAIT_OR_NOTIFY_EXECUTOR`。
- **失败**：零副作用（无 tasks 行、无 AEP、无状态变化、无 agmsg 消息）。

## 6. 验收标准（可测）

1. 缺 `--acceptance` / `--branch` → 拒绝且 tasks 表零增量（正反例）
2. E1 转移 + `DEVELOPMENT_STARTED` 信封字段与表单逐字段一致；信封无编排器自拟内容（内容审计）
3. 串行锁：预置活动任务 → E3 拒绝；终态任务不阻断（A4）
4. Reviewer 席位调用 → E4；审计留痕
5. 崩溃恢复：b~e 任一步中断后重跑，`task_id` 不重复、无孤儿 AEP（事务 + message_id 幂等）

## 7. 实现落点

| 位置 | 变更 |
|---|---|
| `src/macao/cli/main.py:task create` | 补 P3/P4/P5 门禁与逐字段错误 |
| `src/macao/workflow/orchestrator.py:start_task` | 审计快照、席位投影刷新、AEP 投递与建行同事务 |
| `tests/` | 第 6 节 |

## 8. 设计自审

- 编排器零内容生成（FAQ Q13）：验收标准语义质量由提交者负责，本用例只保"可测判据以显式字段进入信封"
- 与 UC-1 h1 对齐：`IDLE → PROMPT_TASK_CREATE` 的下一步即本用例；本用例完成后的 `next_action` 由 UC-3 的 `.dev.yml` 驱动
- 遗留决策点：①`expected_artifacts` 是否在 E2 校验存在（建议 v1.1，MVP 仅登记）；②多任务并发（Scheduler，v1.2）
