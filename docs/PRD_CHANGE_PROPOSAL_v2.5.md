# MACAO PRD 修改提案 v2.5：内容边界、评审处置与可审计协作

> **状态**：DRAFT / 待管理员与 Reviewer 评审，不是现行规范
> **日期**：2026-09-01
> **目标基线**：`docs/MACAO_PRD_v2.md` v2.3.1～v2.4 现有内容
> **输入**：`docs/usercases/PRODUCT-FACTS.md` F-1～F-16，以及对该文件的复审回复
> **生效条件**：本提案经评审批准，并同步修改 PRD、Schema、代码、fixture、测试和 UC 后，方可标记为 `ACCEPTED/IMPLEMENTED`

---

## 1. 修改目的

现行 PRD 在以下方面偏离了“编排器只负责规则与路由、不理解和裁决项目内容”的早期设计原则：

1. 将完整业务上下文和较大的产物内容放入 AEP/agmsg；
2. 让 Orchestrator 生成或改写评审问题正文、返工建议等语义内容；
3. 没有明确区分“阻断合并的问题”和“通过后仍值得处理的建议”；
4. `macao init` 只覆盖静态配置生成，没有覆盖既有项目的动态状态接管；
5. 等权投票不能表达不同 Reviewer 席位经过管理员校准后的可信度差异；
6. `docs/reviews/`、SQLite 审计和 `.macao/archive/` 的职责边界不完整。

本提案保持 MACAO 为确定性规则系统，同时补齐长正文传输、意见处置、动态接管、加权计票和审计闭环。

---

## 2. 核心设计原则

### P-1 编排器零语义创作

Orchestrator 可以做以下确定性操作：

- 校验 Schema、路径、commit、SHA-256、review round 和 reviewer 身份；
- 原样复制或排序结构化字段；
- 根据配置执行计票公式；
- 根据 FSM 守卫推进状态；
- 生成技术性路由信息、deadline、审计事件和产物索引。

Orchestrator 不得：

- 总结项目业务背景；
- 判断两条自然语言意见是否是同一个问题；
- 决定某条意见是否采纳；
- 代替 Executor 撰写评审申请；
- 代替 Reviewer 撰写结论、问题描述或修复建议。

### P-2 内容与控制分层

- Git 中的文档和代码是内容事实源；
- Git 内进一步区分不可变的业务代码检查点 `checkpoint_ref` 与独立演进的证据提交 `evidence_ref`；
- AEP/agmsg 是有明确字节预算的控制与引用通道；
- SQLite 是运行时 FSM 和机器审计事实源；
- `.macao/archive/` 保存轮次级机器产物快照；
- `docs/reviews/` 保存人可读、可随 Git 追溯的开发方向、申请、结论与处置依据。

### P-3 机器裁决与内容处置分离

- `vote_result.json` 是不可变的机器裁决记录，由 Orchestrator 单一写入；
- “哪些意见采纳、延期或拒绝”是 Executor 的内容工作，写入独立的 `review_disposition` 产物；
- Executor 不得填写或修改 `vote_result.decision`、票面、权重快照或机器哈希。

### P-4 显式证据优先，AI 仅诊断

动态状态接管优先使用 State Store、当前轮产物、Git 拓扑和审计记录。AI 可整理冲突证据、解释候选状态，但不能直接写状态；无法唯一判断时必须由管理员选择。

---

## 3. 评审结论与意见处置闭环

### 3.1 评审结论分层

Reviewer 的结论由两部分组成：

1. **机器票**：`YES_APPROVE`、`NO_APPROVE`；`ABSTAIN` 仍只由超时降级流程生成；
2. **证据列表**：每条问题或建议必须有稳定 `issue_id`、标题、严重性、处置级别和全文位置。

新增字段 `disposition_class`：

| 值 | 含义 | 对机器票的约束 |
|---|---|---|
| `BLOCKING` | 合并前必须修复或由管理员显式豁免 | Reviewer 必须投 `NO_APPROVE` |
| `ADVISORY` | 不阻断当前合并，但必须确认采纳、延期或拒绝 | 可与 `YES_APPROVE` 同时出现 |

“有条件通过，但条件必须先修复”不得表示为 `YES_APPROVE`；它在机器语义上是 `NO_APPROVE + BLOCKING`。这样不会出现文字说“通过”、FSM 却必须返工的二义性。

### 3.2 不同结论的处理时点

| 场景 | 处理状态 | 处理动作 | 离开条件 |
|---|---|---|---|
| `REWORK_REQUIRED`，存在 `BLOCKING` 问题 | `REWORK` | Executor 阅读全文，写处置记录并修复；产生新 commit 和新 `.dev.yml` | 新检查点满足 E6 |
| `APPROVED`，没有问题或建议 | `CONSENSUS_CHECK` → `MERGING` | 无内容处置 | `vote_result.json` 校验通过 |
| `APPROVED`，存在 `ADVISORY` 建议 | `CONSENSUS_CHECK`（HOLD） | Executor 写 `review_disposition`，逐条标记采纳、延期或拒绝 | 不改代码则进入 `MERGING`；需要立即改码则经新增 E4c 进入 `REWORK` |
| Deadlock、超时或权重门禁失败 | `CONSENSUS_CHECK`（HOLD） | 管理员裁定 | E7/E9/E10 |

`ADVISORY` 处置不要求在当前 checkpoint 修改代码。若标记为 `ADOPTED_NOW` 并需要改变代码，则由新增转移 E4c 将 `CONSENSUS_CHECK` 转到 `REWORK`（round + 1）；Executor 产生新 commit 后重新评审。不得带着未经评审的新 commit 进入 `MERGING`。

### 3.3 新增 Executor 处置产物

建议增加：

```text
.macao/review_disposition.yml
docs/reviews/<yyyy-MM-dd>-review-disposition-<checkpoint>-<executor>.md
```

YAML 只保存结构化索引，Markdown 保存完整理由：

```yaml
version: "1.0"
checkpoint_ref: "a1b2c3d"
review_round: 1
executor_id: "cc-ds4"
full_document:
  path: "docs/reviews/2026-09-01-review-disposition-a1b2c3d-cc-ds4.md"
  sha256: "<sha256>"
vote_result:
  path: ".macao/vote_result.json"
  evidence_commit: "e5f6a7b"
  sha256: "<sha256>"
items:
  - issue_id: "codex/SEC-01"
    decision: "ADOPTED_NOW"       # ADOPTED_NOW | BACKLOG | REJECTED | NEEDS_ADMIN
    reason_ref: "#codex-sec-01"
    followup_task_id: null
```

规则：

- 必须覆盖本轮全部 `BLOCKING` 问题；`APPROVED + ADVISORY` 进入合并前必须覆盖全部 advisory；
- `BACKLOG` 必须关联已创建的后续 task，或由管理员明确豁免；
- `REJECTED` 必须有理由，但 Orchestrator 只校验理由存在，不判断其质量；
- disposition 必须反向引用已经冻结的 `vote_result.json` 及其 SHA-256；Orchestrator 将关联关系记录进 artifact ledger 和独立审计事件，不回写、不复制或改写 `vote_result.json`；
- 产物一旦用于状态转移即冻结并归档，后续修改必须生成新版本。

### 3.4 `vote_result.json` 的修改

保留 Orchestrator 单一写者，增加纯机器生成字段：

```json
{
  "consensus_rule": "weighted_2/3_v1",
  "policy_snapshot": {
    "reviewers": [
      {"reviewer": "codex", "vote_weight": 2},
      {"reviewer": "kimi", "vote_weight": 1}
    ],
    "seat_quorum": 2,
    "weight_quorum": 2,
    "threshold": "2/3"
  },
  "issues_index": [
    {
      "issue_id": "codex/SEC-01",
      "reviewer": "codex",
      "disposition_class": "BLOCKING",
      "severity": "major",
      "title": "缺少超时异常处理",
      "full_document": {
        "path": "docs/reviews/2026-09-01-review-result-a1b2c3d-codex.md",
        "sha256": "<sha256>",
        "anchor": "#sec-01"
      }
    }
  ],
  "requires_disposition": true,
  "decision": "REWORK_REQUIRED"
}
```

`issues_index` 只能由 Orchestrator 从通过 Schema 校验的 `.review.yml` 原样复制；不得进行语义合并，也不得出现“是否采纳”。采纳信息只在 `review_disposition` 中。`requires_disposition` 由是否存在待处置 issue 确定；E4 必须在其为 `false`，或存在反向引用该 vote result 哈希的合法 disposition 时才能进入 `MERGING`。

---

## 4. 产物分层与长消息治理

### 4.1 新的权威产物表

| 产物 | 写者 | 内容 | 是否含长正文 |
|---|---|---|---|
| `docs/reviews/*-review-request-*.md` | Executor | 评审申请全文：目的、验收标准、改动说明、已知限制、评审重点 | 是 |
| `.macao/.dev.yml` | Executor | 检查点信封：commit、round、质量摘要、申请全文路径和 SHA-256 | 否 |
| `REVIEW_REQUEST` | Orchestrator | 路由、deadline、worktree、commit、各权威文档引用和哈希 | 否 |
| `docs/reviews/*-review-result-*.md` | Reviewer | 评审结论与全部证据 | 是 |
| `.macao/.reviews/*.review.yml` | Reviewer | 总票、问题索引、评审全文路径和 SHA-256 | 否 |
| `.macao/vote_result.json` | Orchestrator | 票面、权重快照、确定性决策、原始问题索引 | 否 |
| `docs/reviews/*-review-disposition-*.md` | Executor | 采纳、延期、拒绝的完整理由 | 是 |
| `.macao/review_disposition.yml` | Executor | 处置索引和全文哈希 | 否 |

`.dev.yml` 和 `.review.yml` 的“摘要”不是由 Orchestrator 使用模型生成的自然语言总结，而是各内容作者提供的结构化信封。Orchestrator 只校验和转发。

### 4.2 `review_context` 改为完整引用集合

“完整 context”不再等于“把完整正文内联到消息”。修改后的 `review_context` 必须完整提供 Reviewer 获取全部上下文所需的定位信息：

```yaml
review_context:
  repository:
    workspace_path: ".macao/worktrees/codex/task-1/r1"
    remote_name: "origin"
    fetch_policy: "fetch_before_diff"
  checkpoint:
    base_commit: "b2c3d4e"
    head_commit: "a1b2c3d"
    review_round: 1
  evidence:
    ref: "refs/macao/evidence/task-1/r1"
    commit: "e5f6a7b"
  review_request:
    path: "docs/reviews/2026-09-01-review-request-task-1.md"
    commit: "e5f6a7b"
    sha256: "<sha256>"
  dev_manifest:
    path: ".macao/.dev.yml"
    commit: "e5f6a7b"
    sha256: "<sha256>"
```

Reviewer 必须从指定 worktree、指定 commit 读取这些文件并验证 SHA-256。缺少任一必需引用、commit 不可达、哈希不匹配或路径越界时，`REVIEW_REQUEST` 失败关闭。

### 4.3 AEP/agmsg 字节预算

不依赖底层 SQLite 或命令行的理论上限，MACAO 在协议层定义应用预算：

- `aep.max_message_bytes` 默认 `16384`，按 UTF-8 编码后的完整信封计算；
- 单个内联自然语言字段默认不超过 `2048` bytes；
- 禁止内联 diff、完整评审申请、完整评审结论和终端日志；
- 超限内容必须写入允许的 Git 路径，并通过 `path + commit + sha256` 引用；
- 发布前做字节级校验，超限则拒绝发送并给出需外置的字段，不允许静默截断；
- 接收方必须校验路径位于允许根目录内，防止路径穿越和读取工作区外文件。

具体默认值可在 PoC 后调整，但在 Schema、发送端和接收端必须使用同一个版本化配置值。

### 4.4 业务代码与证据 Git ref 分离

评审申请、评审结果和 disposition 都可能在业务 checkpoint 生成之后继续增加。若把这些文件提交到同一 source branch，会改变待合并 HEAD，破坏“评审对象 = 合并对象”的硬约束。因此新增证据平面：

- `checkpoint_ref` 永远指向被评审和待合并的业务代码 commit；
- `refs/macao/evidence/<task_id>/r<round>` 独立保存 `docs/reviews/`、manifest、vote result 和 disposition 的版本化副本；
- Reviewer 的 source worktree 固定在 `checkpoint_ref`，证据通过 `git show <evidence_commit>:<path>` 或只读 evidence worktree 获取；
- 内容作者仍是 Executor/Reviewer；Orchestrator 只校验并提交其原始字节到 evidence ref，不改写正文；
- evidence ref 的推进不得改变 source branch HEAD，Merge Controller 仍只比较并合入 `checkpoint_ref`；
- State Store 必须记录每个产物所在的 `evidence_commit`，远程部署时同时验证 source ref 和 evidence ref 均已可靠 push。

这样既保留 `docs/reviews/` 的 Git 历史，又不会因为补写评审证据而触发“未经评审的新业务 commit”。

---

## 5. `macao init` 与动态状态接管

### 5.1 命令职责调整

`macao init` 作为统一入口，内部明确分成两个模块，避免把静态配置和动态状态混成一次不可审计的猜测：

```text
macao init --new                 新项目：生成/校验配置，状态为 IDLE
macao init --adopt-existing      既有项目：静态配置 + 动态状态接管
macao init --repair              修复配置或运行时元数据，必须展示变更计划
```

现有 `macao setup` 的 CLI/模型/仓库探测能力并入静态配置阶段；`reconcile` 作为动态接管的内部执行器和日常恢复命令继续保留。

### 5.2 动态状态判断优先级

判断依据从高到低：

1. `state.db` 中未终结任务、round、checkpoint 和不可变审计事件；
2. 当前 commit 上、当前 round 且 Schema/哈希有效的 `.macao/` 产物；
3. `.macao/archive/` 与 Git 历史中的已消费产物；
4. Git 分支、worktree、merge/push 拓扑；
5. CLI 进程、自报状态、终端日志等弱信号。

不得仅凭 CLI 是否安装、是否运行或一段终端输出确定业务状态。

### 5.3 唯一态、歧义态和 AI 介入

| 判断结果 | 行为 |
|---|---|
| 证据唯一推出一个合法状态 | 输出恢复计划；管理员确认后通过受控事务写入；新项目 `IDLE` 可直接初始化 |
| 多个候选状态或证据冲突 | HOLD，不写状态；展示证据矩阵并要求管理员选择 |
| 证据不足 | 保持 `UNKNOWN` 或无活动任务，要求管理员补充信息/选择 |

可选 AI 模型只生成以下诊断结果：候选状态、支持/反对证据、冲突解释和建议选项。模型输出必须标为 `diagnostic_only`，不能直接调用状态写接口。最终选择由管理员完成，并记录：原始证据哈希、模型诊断、管理员选择、旧状态、新状态和时间。

`--yes` 只能接受“证据唯一且无冲突”的恢复计划；遇到歧义时不得替管理员选择。

### 5.4 状态模型

State Store 仍只保存一个权威 `tasks.state`。界面中的 Executor/Reviewer 状态是任务态和席位产物完成度的只读投影，不建立第二套可独立转移的 FSM。

建议增加非权威展示字段：

```text
role_projection = WAITING | ACTION_REQUIRED | WORKING | RESPONDED | NOT_APPLICABLE
```

这些字段不得作为 FSM 转移触发器；例如 Reviewer 在任务态 `WAITING_REVIEW` 下可显示 `WORKING`，而不是引入第十一业务状态 `REVIEWING`。

---

## 6. 加权 2/3 共识规则

### 6.1 配置与冻结

```yaml
team:
  reviewers:
    - id: codex
      cli: codex
      adapter: pty-wrapper
      vote_weight: 2
    - id: kimi
      cli: kimi
      adapter: pty-wrapper
      vote_weight: 1

policy:
  consensus_rule: weighted_2/3_v1
  seat_quorum_ratio: 2/3
  weight_quorum_ratio: 2/3
  decision_threshold: 2/3
  minimum_winning_seats: 2
```

- `vote_weight` 是管理员为席位配置的正整数，默认值为 1；
- Orchestrator 不得根据文本长度、问题数量、模型自信度或当轮表现自动改变权重；
- 每轮开始时把 reviewer 列表和权重快照冻结到 State Store；运行中修改仅对下一轮生效；
- 所有权重变更必须进入 Git 和 SQLite 审计。

### 6.2 决策公式

设配置席位数为 `N`，配置总权重为 `W`：

1. 非弃权有效席位数必须达到 `ceil(2N/3)`；
2. 非弃权有效权重必须达到 `ceil(2W/3)`；
3. `approve_weight / effective_weight >= 2/3` 且赞成方至少包含 `minimum_winning_seats` 个席位 → `APPROVED`；
4. `reject_weight / effective_weight >= 2/3` 且反对方至少包含 `minimum_winning_seats` 个席位 → `REWORK_REQUIRED`；
5. 其余情形 → Deadlock，转人工处理；

同时保留席位 quorum、权重 quorum 和胜方最少席位数，避免高权重席位超时后少量低权重票自动决定结果，也避免单个高权重模型在其他席位反对时成为事实上的唯一裁判。

### 6.3 权重治理

“部分模型更细致”可以成为管理员设定权重的产品理由，但不能成为系统运行时的自动推断规则。正式启用非等权配置前，应保存：

- 使用相同 review corpus 的盲测结果；
- 漏报阻断问题、误报问题和复审翻转率；
- 权重批准人、依据、有效期和复核日期；
- 回退到全 1 权重的开关。

在没有校准证据时，默认所有席位权重为 1。

---

## 7. 三层审计与留痕

三类记录同时存在，互相引用，任何一层都不能替代另外两层：

| 层 | 位置 | 保存内容 | 主要用途 |
|---|---|---|---|
| 语义与方向留痕 | evidence ref 中的 `docs/reviews/` | 评审申请、完整结论、意见处置、必要的人工裁定说明 | 追溯为什么这样开发、发现过什么、为何采纳或拒绝 |
| 运行时审计 | `.macao/state.db` | 状态转移、消息、超时、override、权重快照、产物消费 | 恢复与机器审计 |
| 机器产物归档 | `.macao/archive/<ref>/r<round>/` | manifest、vote result、disposition envelope、哈希 | 重放每轮协议行为 |

约束：

- 涉及项目方向、验收标准、评审依据和意见取舍的自然语言正文必须进入 `docs/reviews/` 并随 Git 版本化；
- 每次机器状态转移必须进入 SQLite 审计；
- 每轮被消费的结构化产物必须进入 archive；
- 三层通过 `task_id + checkpoint_ref + review_round + evidence_commit + path + sha256` 六元组关联；
- 不得把完整评审证据只保存在 agmsg、终端日志或模型会话历史中。

---

## 8. 对 PRD/SRS 的具体修改清单

### 8.1 PRD

| PRD 位置 | 修改 |
|---|---|
| §1.2 / §3.3 | 增加 `APPROVED + ADVISORY` 在 `CONSENSUS_CHECK` HOLD 等待 disposition 的守卫；明确阻断问题进入 `REWORK`；增加 advisory 立即改码的 E4c |
| §2.1 | `.dev.yml` 改为结构化信封，增加 `full_document{path,commit,sha256}` |
| §2.2 | `.review.yml` 改为结构化信封，增加稳定 issue ID、`disposition_class` 和全文引用 |
| §2.3 | 等权规则升级为 `weighted_2/3_v1`；增加 policy snapshot、issues index 和单席位防支配规则 |
| §2.4 / §5.2 | `review_context` 从内联完整内容改为完整引用集合；定义 AEP 字节预算和失败关闭规则 |
| §3.4 | 加入 `review_disposition` 生命周期和归档规则 |
| §6 | 增加权重门禁失败、处置缺失、引用哈希失败的人工接管条件 |
| §11 | 增加每轮 reviewer/weight policy snapshot、disposition artifact ledger 与独立 evidence ref |
| §14 | 重写 `macao init --new/--adopt-existing/--repair`；描述 AI 诊断和管理员确认边界 |
| §16 | 保持 `vote_result` 的 Orchestrator 单一写者；明确 Executor 是 disposition 的单一写者；分离 source checkpoint 与 evidence ref |

### 8.2 SRS

`docs/SRSv1.md` 继续作为历史基线，不回写或伪装修改早期原文。只在文件顶部的“v2 已重定义”表中增加：

- AEP 从内联内容演进为带哈希的引用传递；
- 单一任务 FSM 与角色只读投影；
- 加权共识为新版本规则，不宣称是 v1 原始设计；
- AI 仅参与动态接管诊断，最终状态由显式证据或管理员确认。

---

## 9. Schema、代码和测试迁移

### 9.1 Schema

必须同步升级并收紧 `additionalProperties`：

- `macao_config.schema.json`：`vote_weight`、AEP 字节预算、加权策略；
- `dev_manifest.schema.json`：评审申请全文引用；
- `review_manifest.schema.json`：全文引用、issue index、`disposition_class`；
- `review_context.schema.json`：引用集合；
- `vote_result.schema.json`：权重快照、加权 breakdown、`issues_index`、`requires_disposition`；
- 新增 `review_disposition.schema.json`。

### 9.2 代码

实施顺序：

1. 先实现新旧 Schema 版本读取和 fail-closed 校验；
2. 实现 evidence ref、文档引用路径与 SHA-256 校验；
3. 实现 AEP 字节预算；
4. 实现权重快照与共识公式；
5. 实现 disposition 守卫及生命周期；
6. 实现 `init --adopt-existing` 的证据矩阵、诊断和确认事务；
7. 最后切换默认协议版本。

迁移期间不得让同一 review round 混用等权和加权规则，也不得混用内联 context 和引用式 context。

### 9.3 最低验收场景

1. 两 Reviewer 全通过，无意见，直接进入 `MERGING`；
2. 通过但有 advisory，缺 disposition 时 HOLD，齐全后进入 `MERGING`；
3. advisory 选择立即修改时，经 E4c 进入 `REWORK`，必须产生新 commit、新 round 评审；
4. 有条件通过但要求先修，必须映射成 `NO_APPROVE + BLOCKING`；
5. `REWORK_REQUIRED` 下 disposition、修复、新 `.dev.yml` 闭环；
6. AEP 超过 16 KiB 时拒绝发送，改为引用后成功；
7. 引用路径越界、commit 不匹配、SHA-256 不匹配均失败关闭；
8. 等权、非等权、弃权、超时、1:1、1:1:1、单席位达到权重阈值等决策表；
9. 权重在 round 中途修改不影响当前 round；
10. 既有项目唯一状态自动生成恢复计划，歧义状态必须询问管理员；
11. AI 给出错误候选状态也不能绕过管理员或直接写 State Store；
12. `docs/reviews/`、SQLite、archive 三层可由同一六元组互相追溯；
13. 增加评审结果和 disposition 时 evidence ref 前进，但 source HEAD 与 `checkpoint_ref` 保持不变。

---

## 10. 需要管理员最终裁定的事项

1. `APPROVED + ADVISORY` 是否必须在合并前完成 disposition；本提案默认“必须确认，但不一定立即改码”；
2. disposition 使用独立 YAML，还是并入下一轮 `.dev.yml`；本提案采用独立 YAML，以覆盖无需返工的批准场景；
3. AEP 默认预算采用 16 KiB 还是其他实测值；
4. 非等权投票的首批权重和校准证据；
5. `macao init --adopt-existing` 是否保留独立别名 `macao adopt`；
6. `BACKLOG` 是由 MACAO 自动创建后续 task，还是只校验管理员提供的 task ID；为避免编排器介入任务规划，本提案默认后者。

---

## 11. 建议决议

若本提案获批：

1. 将 `PRODUCT-FACTS.md` 中相关事实标记为 `ACCEPTED-PENDING-SPEC`，而不是 `IMPLEMENTED`；
2. PRD 升级到 v2.5，并使其再次成为上述协议的唯一权威来源；
3. Schema、代码和测试完成前，现有 v2.3/v2.4 行为保持不变；
4. 完成迁移和场景验证后，再把 FAQ/UC 中的“待落地”表述改为既成事实。
