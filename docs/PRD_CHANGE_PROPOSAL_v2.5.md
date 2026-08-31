# MACAO PRD 修改提案 v2.5：内容边界、评审处置与可审计协作

> **状态**：DRAFT v0.2 / 已吸收 commit `0042dc3` 的三份独立评审；qwen 复审授予 L1 DOC-ALIGNED，待管理员批准
> **日期**：2026-09-01
> **目标基线**：`docs/MACAO_PRD_v2.md` v2.3.1～v2.4 现有内容
> **事实基线**：`docs/usercases/PRODUCT-FACTS.md` F-1～F-22（commit `99fe377`）
> **评审输入**：`docs/reviews/2026-09-01-review-result-0042dc3-{gemini,glm,grok,qwen}.md`
> **生效条件**：本提案通过 L1 评审，并同步修改 PRD、SRS 兼容说明、PRODUCT-FACTS、Schema、代码、fixture、测试、FAQ 和 UC 后，方可标记为 `ACCEPTED/IMPLEMENTED`

---

## 1. 修改目的

现行规格在以下方面偏离了“Orchestrator 只负责规则、路由和确定性校验，不理解或裁决项目内容”的设计边界：

1. 将完整业务上下文和较大的产物正文放入 AEP/agmsg；
2. 让 Orchestrator 生成或改写评审问题、返工建议等语义内容；
3. `vote_result.json` 的机器裁决与 Executor 的意见处置存在双写者冲突；
4. 没有闭合“机器已批准但仍有意见”时的处置、超时和状态转移；
5. `macao init` 只覆盖静态配置生成，没有覆盖既有项目的动态状态接管；
6. 等权投票不能表达管理员经校准后对 Reviewer 席位的差异化配置；
7. `docs/reviews/`、SQLite、`.macao/archive/` 与远程 Git 证据 ref 的职责和失败恢复不完整。

本提案补齐长正文传输、逐项处置、动态接管、加权计票和审计闭环，同时保持单一任务 FSM 与确定性控制面。

---

## 2. 本提案作出的规范裁定

本节不是待选方案，而是 v2.5 的明确设计输入。

| ID | 裁定 |
|---|---|
| D-1 | `vote_result.json` 只保存机器输入、策略快照、票面、原始 issue 索引和机器决策，由 Orchestrator 单一写入并保持不可变。 |
| D-2 | Executor 的逐项采纳、延期、拒绝和请求人工处理写入独立、按 round 保存的 `review_disposition`。该方案正式替代旧 FAQ/UC 中由 Executor 回写 `vote_result.issues_summary` 的双写者方案，并解析 PRODUCT-FACTS F-20 的待定项。 |
| D-3 | Reviewer 可以显式投 `ABSTAIN`；Reviewer 主动弃权与 Orchestrator 因超时合成的弃权在计票上同构，在审计来源上必须区分。 |
| D-4 | `BACKLOG` 统一命名为 `DEFERRED`。它只要求理由，`followup_task_id` 可选且不检查 State Store 中已存在任务；后续任务应在当前任务 `DONE` 后由人或 Executor 创建。 |
| D-5 | 处置项必须显式填写 `requires_new_checkpoint: boolean`。Orchestrator 不得从自然语言理由、文件类型或处置枚举推断是否需要新检查点。 |
| D-6 | 加权投票同时保留配置期单席位防支配上限、运行期席位 quorum、运行期权重 quorum、胜方权重阈值和胜方最少席位数。 |
| D-7 | AEP 升级为 AEP/1.1，增加 `DISPOSITION_REQUIRED`；AEP/agmsg 只承载控制字段与可验证引用。 |
| D-8 | 评审证据进入独立 Git evidence ref，不因补写证据而改变被评审的 source `checkpoint_ref`；任务完成不自动把证据合入 source branch。 |
| D-9 | `macao init` 是入口，`doctor` 只读诊断，`reconcile` 是确定性恢复执行器，`adopt` 是 `init --adopt-existing` 的别名。 |

---

## 3. 核心设计原则

### P-1 Orchestrator 零语义创作

Orchestrator 可以：

- 校验 Schema、路径、commit、SHA-256、round、deadline 和身份；
- 按已冻结的 Reviewer 配置顺序拼接结构化字段；
- 根据配置执行整数计票公式；
- 根据显式结构化字段和 FSM 守卫推进状态；
- 生成路由信息、审计事件、技术性错误和产物索引。

Orchestrator 不得：

- 总结项目业务背景；
- 判断两条自然语言意见是否重复；
- 决定某条意见是否采纳；
- 判断某项处置是否需要改代码或生成新 checkpoint；
- 代替 Executor 撰写申请或处置理由；
- 代替 Reviewer 撰写结论、问题描述或修复建议。

### P-2 内容与控制分层

- source Git commit 是被评审业务检查点的事实源；
- evidence Git ref 是长正文与结构化评审证据的事实源；
- AEP/agmsg 是有版本化字节预算的控制与引用通道；
- SQLite 是运行时 FSM、deadline、消息和机器审计事实源；
- `.macao/archive/` 是轮次级本地机器产物快照；
- `docs/reviews/` 是 evidence ref 中人可读、Git 可追溯的语义证据路径。

### P-3 机器裁决与内容处置分离

- Orchestrator 单一写入不可变的 `vote_result.json`；
- Executor 单一写入不可变版本的 `review_disposition`；
- disposition 必须引用 vote result 的 `path + evidence_commit + sha256`；
- Executor 不得修改机器票、策略快照或 `decision`；
- Orchestrator 不得修改处置枚举、理由或 `requires_new_checkpoint`。

### P-4 显式证据优先，AI 仅诊断

动态状态接管优先使用 State Store、当前轮产物、Git 拓扑和审计记录。可选 AI 只在进程外 sidecar/adapter 中生成诊断报告，没有状态写接口；无法唯一判断时由管理员选择。

---

## 4. 评审、计票与逐项处置

### 4.1 Reviewer 票与 issue 的约束

Reviewer 的结果包含一张机器票和零到多条独立 issue：

- `YES_APPROVE`
- `NO_APPROVE`
- `ABSTAIN`

每条 issue 必须有稳定 `issue_id`、标题、严重性、`disposition_class` 和全文引用。`disposition_class` 只有：

| 值 | 语义 | 对该 Reviewer 票的约束 |
|---|---|---|
| `BLOCKING` | Reviewer 建议当前检查点不要合并 | 必须为 `NO_APPROVE` |
| `ADVISORY` | 不要求该 Reviewer 因此拒绝检查点，但必须留痕并处置 | `YES_APPROVE` 或 `NO_APPROVE` 均可 |

Schema 必须表达以下条件：

- 存在 `BLOCKING` ⇒ 该 Reviewer 的票只能是 `NO_APPROVE`；
- `YES_APPROVE` ⇒ 不得包含 `BLOCKING`；
- `NO_APPROVE` ⇒ 至少包含一条 `BLOCKING`；
- 显式 `ABSTAIN` ⇒ issue 列表为空，且必须提供 `abstain_reason`；
- 超时合成的 `ABSTAIN` 没有 Reviewer manifest，由 Orchestrator 记录 `source: timeout`、deadline 和最后一次 ping；
- 主动弃权与超时弃权均不进入有效票分母。`reviewers_responded` 统计收到合法 manifest 的席位（含主动弃权），`reviewers_accounted` 等于合法 manifest 席位数加已合成 timeout 的席位数。

“有条件通过，但条件必须先修复”必须表示为 `NO_APPROVE + BLOCKING`，不能用 `YES_APPROVE` 表示。

`BLOCKING` 是单个 Reviewer 对其票的约束，不是绕过共识公式的单票否决权。加权结果仍可能在少数 Reviewer 报告 `BLOCKING` 时得到 `APPROVED`；这些 issue 仍必须被 Executor 逐项处置。

### 4.2 不同机器结论的处理时点

| 场景 | 处理状态 | 行为 | 离开条件 |
|---|---|---|---|
| `REWORK_REQUIRED` | 立即进入 `REWORK` | 通知 Executor；Executor 写完本轮全部 issue 的 disposition 并修改检查点 | E6 要求完整 disposition、新 commit、新 `.dev.yml` 和新 review request |
| `APPROVED` 且无 issue | `CONSENSUS_CHECK` → `MERGING` | 无语义处置 | E4 机器守卫通过 |
| `APPROVED` 且有 issue | 留在 `CONSENSUS_CHECK`（HOLD） | 发送 `DISPOSITION_REQUIRED`；Executor 逐项处置 | 全部 `requires_new_checkpoint=false` 时 E4；任一为 `true` 时 E5a 进入 `REWORK` |
| `DEADLOCK`、门禁失败或 disposition 为 `NEEDS_ADMIN` | 当前状态 HOLD | 发送 `HUMAN_OVERRIDE_REQUEST` | E7 管理员决定 |

多数批准时，少数 Reviewer 的 `BLOCKING` 可以被 Executor 标为 `REJECTED` 或 `DEFERRED`，因为机器共识已经决定当前检查点可合并；这不是修改机器票。只有管理员用 E7 把原本的 `REWORK_REQUIRED` 覆盖为 `APPROVED` 时，相关未修复 `BLOCKING` 才必须标记为 `EXEMPTED_BY_ADMIN`。

### 4.3 disposition 产物与 Schema

活动路径按 round 隔离：

```text
.macao/.dispositions/r<round>/executor.disposition.yml
docs/reviews/<yyyy-MM-dd>-review-disposition-<checkpoint>-<executor>.md
```

结构化信封示例：

```yaml
version: "1.0"
task_id: "task-1"
checkpoint_ref: "a1b2c3d"
review_round: 1
artifact_revision: 1
executor_id: "cc-ds4"
status: "FINAL"
full_document:
  path: "docs/reviews/2026-09-01-review-disposition-a1b2c3d-cc-ds4.md"
  sha256: "<sha256>"
vote_result:
  path: ".macao/vote_result.json"
  evidence_commit: "c4d5e6f"
  sha256: "<sha256>"
issues_index_sha256: "<sha256>"
items:
  - issue_id: "codex/SEC-01"
    decision: "ADOPTED"
    requires_new_checkpoint: true
    reason_ref: "#codex-sec-01"
    followup_task_id: null
    override_id: null
```

`decision` 统一为：

- `ADOPTED`：已采纳；`requires_new_checkpoint` 可为 `true` 或 `false`；
- `DEFERRED`：延期，必须有理由，`followup_task_id` 可选，不查验任务存在性，`requires_new_checkpoint=false`；
- `REJECTED`：不采纳，必须有理由，`requires_new_checkpoint=false`；
- `NEEDS_ADMIN`：无法由 Executor 决定，`status=PENDING_ADMIN`，当前状态 HOLD；
- `EXEMPTED_BY_ADMIN`：仅在有效 E7 override 把 `REWORK_REQUIRED` 改为 `APPROVED` 时使用，必须有 `override_id`，`requires_new_checkpoint=false`。

强制规则：

1. 每个有效 disposition 版本必须按 `issues_index` 精确覆盖本轮全部 issue，一项不多、一项不少、每项恰好一次；
2. `issues_index` 的稳定顺序是“冻结的 Reviewer 配置顺序 × 各 manifest 原始 issue 顺序”，禁止排序、去重和语义合并；
3. `requires_new_checkpoint` 对每一项都是必填布尔值；缺失时失败关闭；
4. Markdown 保存完整理由，YAML 只保存结构化索引和锚点；
5. `status` 只有 `FINAL | PENDING_ADMIN`；产物一旦被状态转移消费即冻结并归档；`PENDING_ADMIN` 的后续结果用更高 `artifact_revision` 写新版本，不原地修改；
6. disposition 必须反向引用冻结的 vote result 和 `issues_index` 哈希；Orchestrator 只校验关联关系，不回写 vote result。

### 4.4 disposition 的完整协议边与超时

AEP/1.1 新增第八种消息 `DISPOSITION_REQUIRED`，最小 payload 为：

```yaml
task_id: "task-1"
checkpoint_ref: "a1b2c3d"
review_round: 1
vote_result_ref:
  path: ".macao/vote_result.json"
  evidence_commit: "c4d5e6f"
  sha256: "<sha256>"
issues_index_sha256: "<sha256>"
deadline: "2026-09-01T12:30:00Z"
```

- `timeouts.review_disposition` 默认 30 分钟，进入等待时持久化绝对 deadline；
- Orchestrator 按统一 timeout scanner 发送 ping，并在 deadline 后发送 `HUMAN_OVERRIDE_REQUEST`；
- 超时不会自动创建 disposition、自动忽略 issue 或进入 `MERGING`；
- `APPROVED` 场景继续停在 `CONSENSUS_CHECK`，`REWORK_REQUIRED` 场景继续停在 `REWORK`；
- E7 可选择 `APPROVED | REWORK | RETRY_REVIEW | CANCEL`。若从 `REWORK_REQUIRED` 覆盖成 `APPROVED`，E7 请求必须带 `exempt_issue_ids` 和 note，并为后续 `EXEMPTED_BY_ADMIN` 生成 `override_id`；override 不绕过逐项 disposition，E4 仍要求 FINAL disposition。

### 4.5 状态转移修订

| 转移 | 源状态 → 目标状态 | 新增或修订守卫 |
|---|---|---|
| E3 | `WAITING_REVIEW` → `CONSENSUS_CHECK` | 所有席位已响应或已被持久化 timeout 机制纳入 accounted 集合 |
| E4 | `CONSENSUS_CHECK` → `MERGING` | `APPROVED`；无 issue，或 FINAL disposition 精确覆盖全部 issue 且所有 `requires_new_checkpoint=false` |
| E5 | `CONSENSUS_CHECK` → `REWORK` | 机器决策为 `REWORK_REQUIRED` |
| E5a | `CONSENSUS_CHECK` → `REWORK` | 机器决策为 `APPROVED`，FINAL disposition 精确覆盖全部 issue，且至少一项 `requires_new_checkpoint=true` |
| E6 | `REWORK` → `READY_FOR_REVIEW` | 前一轮 FINAL disposition 已覆盖全部 issue；新 source commit、新 `.dev.yml`、新 review request 和 round 均有效 |
| E7 | HOLD → 管理员指定路径 | override 选项、note、操作者和 issue 级豁免信息完整并审计 |

E5a 不复用现有 MERGING 内部转移 E4a/E4b 的编号，避免审计语义混淆。

### 4.6 `vote_result.json` 完整示例

以下示例展示 3 席位 `2:1:1`、两票赞成、一票反对但最终批准的合法结果：

```json
{
  "version": "2.0",
  "generated_at": "2026-09-01T12:00:00Z",
  "task_id": "task-1",
  "checkpoint_ref": "a1b2c3d",
  "review_round": 1,
  "executor_id": "cc-ds4",
  "reviewers_total": 3,
  "reviewers_responded": 3,
  "reviewers_accounted": 3,
  "input_artifacts": [
    {"reviewer": "codex", "path": ".macao/.reviews/codex.review.yml", "evidence_commit": "b1c2d3e", "sha256": "<sha256>"},
    {"reviewer": "kimi", "path": ".macao/.reviews/kimi.review.yml", "evidence_commit": "b1c2d3e", "sha256": "<sha256>"},
    {"reviewer": "gemini", "path": ".macao/.reviews/gemini.review.yml", "evidence_commit": "b1c2d3e", "sha256": "<sha256>"}
  ],
  "votes": [
    {"reviewer": "codex", "vote": "YES_APPROVE", "weight": 2, "source": "manifest"},
    {"reviewer": "kimi", "vote": "YES_APPROVE", "weight": 1, "source": "manifest"},
    {"reviewer": "gemini", "vote": "NO_APPROVE", "weight": 1, "source": "manifest"}
  ],
  "policy_snapshot": {
    "rule": "weighted_2/3_v1",
    "configured_seats": 3,
    "configured_weight": 4,
    "seat_quorum_required": 2,
    "weight_quorum_required": 3,
    "decision_threshold_numerator": 2,
    "decision_threshold_denominator": 3,
    "minimum_winning_seats": 2,
    "max_single_weight_share_exclusive": "2/3"
  },
  "vote_breakdown": {
    "effective_seats": 3,
    "effective_weight": 4,
    "approve_seats": 2,
    "approve_weight": 3,
    "reject_seats": 1,
    "reject_weight": 1,
    "abstain_seats": 0,
    "abstain_weight": 0
  },
  "issues_index": [
    {
      "issue_id": "gemini/SEC-01",
      "reviewer": "gemini",
      "disposition_class": "BLOCKING",
      "severity": "major",
      "title": "缺少超时异常处理",
      "full_document": {
        "path": "docs/reviews/2026-09-01-review-result-a1b2c3d-gemini.md",
        "evidence_commit": "b1c2d3e",
        "sha256": "<sha256>",
        "anchor": "#sec-01"
      }
    }
  ],
  "issues_index_sha256": "<sha256>",
  "requires_disposition": true,
  "decision": "APPROVED",
  "resolution": "AUTO_WEIGHTED_CONSENSUS"
}
```

Schema 使用 `additionalProperties: false`。`issues_index` 只能从已通过 Schema 校验的 Reviewer manifest 原样拼接，不能增加“是否采纳”字段。

---

## 5. 产物分层、完整 context 与证据 Git ref

### 5.1 权威产物表

| 产物 | 写者 | 内容 | 权威位置 |
|---|---|---|---|
| review request Markdown | Executor | 目的、验收标准、业务背景、改动说明、已知限制、评审重点 | evidence ref 的 `docs/reviews/` |
| `.dev.yml` | Executor | checkpoint、round、质量快照、全文引用 | evidence ref + 活动 staging |
| `REVIEW_REQUEST` | Orchestrator | 路由、deadline、worktree、commit、引用和哈希 | AEP/SQLite |
| review result Markdown | Reviewer | 完整结论和全部证据 | evidence ref 的 `docs/reviews/` |
| `.review.yml` | Reviewer | 总票、issue 索引、全文引用、显式弃权理由 | evidence ref + 活动 staging |
| `vote_result.json` | Orchestrator | 票面、策略快照、确定性决策、原始 issue 索引 | evidence ref/archive/ledger |
| disposition Markdown | Executor | 逐项决定和完整理由 | evidence ref 的 `docs/reviews/` |
| disposition YAML | Executor | 逐项索引、显式 checkpoint 决定、全文哈希 | evidence ref/archive/ledger |

`.dev.yml` 和 `.review.yml` 是内容作者提供的结构化短信封，不是 Orchestrator 用模型生成的自然语言摘要。

### 5.2 现行 `review_context` 的逐块迁移

“完整 context”改为“足以定位和验证全部必需内容的完整引用集合”，不是把正文全部内联。

| 现行语义块 | v2.5 载体 | 首轮 | 后续轮 |
|---|---|---|---|
| `repository` | AEP 内联 repo/worktree/remote/fetch policy | 必需 | 必需 |
| `dev_checkpoint` | source `base_commit/head_commit` + dev manifest 的 evidence 引用 | 必需 | 必需 |
| `task_info` / 业务背景 | Executor 的 review request 引用 | 必需 | 必需 |
| `code_changes` | AEP 内联 base/head；Reviewer 在固定 worktree 本地生成 diff | 必需 | 必需 |
| `quality_snapshot` | `.dev.yml` 引用 | 必需 | 必需 |
| `executor_self_assessment` | review request 或 `.dev.yml` 中作者字段的引用 | 必需 | 必需 |
| `history` | 前轮 vote result、disposition 和 review result 引用 | 空集合 | 必需 |
| `references` | Executor 在 review request 中声明的明确路径和引用 | 可空 | 可空 |
| review 方法/指引 | 固定 repo path + source commit + sha256 | 必需 | 必需 |

完整控制信封至少包含：

```yaml
review_context:
  required_blocks:
    - repository
    - dev_checkpoint
    - task_info
    - code_changes
    - quality_snapshot
    - executor_self_assessment
    - history
    - references
    - review_guidelines
  repository:
    workspace_path: ".macao/worktrees/codex/task-1/r1"
    remote_name: "origin"
    fetch_policy: "fetch_source_and_evidence_before_diff"
  dev_checkpoint:
    base_commit: "b2c3d4e"
    head_commit: "a1b2c3d"
    review_round: 1
  evidence:
    ref: "refs/macao/evidence/task-1/r1"
    commit: "e5f6a7b"
    dev_manifest:
      path: ".macao/.dev.yml"
      commit: "e5f6a7b"
      sha256: "<sha256>"
  task_info:
    source: "review_request"
    path: "docs/reviews/2026-09-01-review-request-task-1.md"
    commit: "e5f6a7b"
    sha256: "<sha256>"
  code_changes:
    base_commit: "b2c3d4e"
    head_commit: "a1b2c3d"
    diff_policy: "generate_locally"
  quality_snapshot:
    source: "evidence.dev_manifest"
  executor_self_assessment:
    source: "task_info"
    anchor: "#self-assessment"
  review_guidelines:
    path: "docs/MACAO_REVIEW_GUIDELINES.md"
    commit: "a1b2c3d"
    sha256: "<sha256>"
  history: []
  references: []
```

缺少必需引用、commit 不可达、SHA-256 不匹配、路径越界或 source/evidence round 不一致时失败关闭。

### 5.3 AEP/agmsg 字节预算

- 配置项 `aep.max_message_bytes` 默认 `16384`，按 UTF-8 编码后的完整信封计算；
- `aep.max_inline_text_bytes` 默认 `2048`；
- 两个默认值属于协议版本配置，不得成为发送端或接收端的散落魔法数；
- 禁止内联 diff、完整申请、完整结论、处置正文和终端日志；
- 超限内容必须写到允许路径，并通过 `path + commit + sha256` 引用；
- 发送前和接收后都执行同一版本的字节级校验；超限拒绝，不得截断；
- 接收方必须校验允许根、规范化路径和 Git object，防止路径穿越。

默认值可在 PoC 后由协议版本升级调整。

### 5.4 evidence ref 投递、提升和读取生命周期

#### 5.4.1 Ref 与 fetch 约定

- canonical ref：`refs/macao/evidence/<task_id>/r<round>`；
- 远程作者临时投递 ref：`refs/macao/inbox/<task_id>/r<round>/<actor_id>/<message_id>`；
- 本地 staging：`.macao/inbox/<task_id>/r<round>/<actor_id>/<message_id>/`；
- 客户端必须配置并验证 evidence fetch refspec：`+refs/macao/evidence/*:refs/remotes/origin/macao/evidence/*`；
- 需要远程 Reviewer 时，还必须允许按消息精确 fetch inbox ref；临时 ref 在 canonical promotion 和审计确认后才能删除。

不可变 blob 不得内嵌“包含该 blob 的 Git commit ID”，否则会形成无法求解的自引用。同批正文与 manifest 之间使用 `path + sha256`；承载它们的 `evidence_commit` 由外层 AEP、artifact ledger 或后续产物记录。只有引用已经冻结的前序产物时，blob 内才可同时写 `path + evidence_commit + sha256`。

#### 5.4.2 投递顺序

1. Executor 先使 source `checkpoint_ref` 在远端可达，再提交 review request 和 `.dev.yml` 原始字节；
2. 本地作者写入受限 staging；远程作者 push 自己作用域内的 inbox ref，并在 AEP 中发送 commit/path/hash；
3. Orchestrator 校验作者、task、round、路径、Schema、blob hash 和 source checkpoint；
4. Orchestrator 串行把原始 blob 提升到 canonical evidence ref；允许生成 Git tree/commit 元数据，不得改动作者正文或结构化 blob；
5. Reviewer fetch 固定 source checkpoint 与 canonical evidence ref，验证 hash 后评审；review response 走相同的 staging/inbox/promotion 流程；
6. Orchestrator 只在所有输入 evidence 已远程 push 且 `ls-remote` 验证成功后生成 vote result；vote result 本身也必须 promotion、push、verify 后才能触发决策转移；disposition 同样先 promotion、push、verify 后才能触发 E4/E5a/E6；
7. 进入 source merge 前必须存在一个已验证的 pre-merge evidence seal；失败时 HOLD，禁止 push source；
8. source push 成功后生成 post-merge audit evidence。若其 push/verify 失败，任务保持 `MERGING` 并重试或请求人工处理，不回滚已经成功的远端 source，不得宣告 `DONE`。

State Store 对每个 artifact 记录 `task_id + checkpoint_ref + review_round + actor + evidence_commit + path + sha256 + consumed_at + archived_path`。

#### 5.4.3 完成后的可见性

evidence 文档不会自动合入 source branch，因为这会引入未作为业务检查点评审的新 commit。用户通过以下方式读取：

- `macao reviews show <task_id> [--round N]`；
- `macao reviews export <task_id> --to <directory>`；
- 显式查看 `refs/macao/evidence/...`。

如果产品未来要求在 `main` 直接看到这些文档，应创建独立、可审计的 docs 同步任务，不得把它隐式塞入当前 source merge。

---

## 6. `macao init`、动态接管与角色投影

### 6.1 命令边界

| 命令 | 职责 | 是否写状态 |
|---|---|---|
| `macao init --new` | 生成/校验静态配置；新项目建立 `IDLE` | 是，限新项目初始化 |
| `macao init --adopt-existing` | 编排静态配置、调用 doctor、展示计划并调用 reconcile | 经确认后 |
| `macao adopt` | 上一命令的稳定别名 | 经确认后 |
| `macao init --repair` | 展示配置/元数据修复计划 | 经确认后 |
| `macao doctor` | 只读收集证据、输出候选状态和冲突 | 否 |
| `macao reconcile` | 按确定性恢复计划执行受控事务 | 是 |

交互模式可以自动探测并推荐 mode；`--yes`/CI 模式必须显式给出 `--new`、`--adopt-existing` 或 `--repair`。歧义时即使带 `--yes` 也必须失败关闭。

### 6.2 动态状态判断优先级

1. `state.db` 中未终结任务、round、checkpoint 和不可变审计事件；
2. 当前 task/round 且 Schema、commit、hash 有效的 `.macao/` 产物；
3. archive 与 evidence Git 历史中的已消费产物；
4. Git branch、worktree、merge 和 push 拓扑；
5. CLI 进程、自报状态、终端日志等弱信号。

不得只凭 CLI 是否安装、是否运行或一段终端输出决定任务状态。

证据唯一时生成恢复计划；交互模式经管理员确认、无冲突的 `--yes` 模式可执行。证据冲突或不足时不写状态，保持 `UNKNOWN`/无活动任务并要求管理员选择。可选 AI sidecar 只能输出 `diagnostic_only` 的候选、支持/反对证据和建议，不得调用 State Store 写接口。

### 6.3 唯一规范名 `role_view`

State Store 只保存一个权威 `tasks.state`。角色显示使用 UC-1 已有的只读 `role_view`，不引入 `role_projection` 或第二套 FSM：

| task state / 条件 | Executor `role_view` | Reviewer `role_view` |
|---|---|---|
| `IDLE` / 无活动任务 | `AWAIT_TASK` | `AWAIT_TASK` |
| `CODING` / `REWORK` | `SHOULD_CODE` | `IDLE_WAIT_DISPATCH` |
| `READY_FOR_REVIEW` | `CHECKPOINT_SUBMITTED` | `IDLE_WAIT_DISPATCH` |
| `WAITING_REVIEW` / 未提交席位 | `AWAIT_REVIEWS` | `SHOULD_REVIEW` |
| `WAITING_REVIEW` / 已提交席位 | `AWAIT_REVIEWS` | `REVIEW_SUBMITTED` |
| `CONSENSUS_CHECK` | `AWAIT_DECISION` | `AWAIT_DECISION` |
| `MERGING` | `AWAIT_MERGE` | `AWAIT_MERGE` |
| `UNKNOWN` | `AWAIT_HUMAN` | `AWAIT_HUMAN` |
| `DONE` / `CANCELLED` | `AWAIT_TASK` | `AWAIT_TASK` |

`role_view` 不落入任务状态表，也不得作为 FSM 转移触发器。

---

## 7. 加权 2/3 共识规则

### 7.1 配置、冻结与配置期校验

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
    - id: gemini
      cli: gemini
      adapter: pty-wrapper
      vote_weight: 1
policy:
  consensus_rule: weighted_2/3_v1
  seat_quorum_ratio: "2/3"
  weight_quorum_ratio: "2/3"
  decision_threshold: "2/3"
  minimum_winning_seats: 2
  max_single_weight_share_exclusive: "2/3"
```

- Reviewer 数 `N >= 2`；`vote_weight` 是正整数，默认 1；
- 配置期必须满足每个 `3 * w_i < 2 * W`，否则拒绝启动；
- `minimum_winning_seats` 默认 2，Schema 强制 `2 <= minimum_winning_seats <= N`；
- 每轮开始时冻结 reviewer、权重和全部 policy 参数到 State Store/vote result；中途修改只影响下一轮；
- Orchestrator 不得根据文字长度、问题数量、自信度或当轮表现自动调整权重；
- 没有校准证据时默认全 1；非等权配置必须记录批准人、盲测依据、有效期、复核日期和回退开关。

### 7.2 三个 2/3 的不同含义

设配置席位数为 `N`，配置总权重为 `W`，非弃权席位数为 `E_N`，非弃权权重为 `E_W`：

1. **席位法定人数**：`E_N >= ceil(2N/3)`；
2. **权重法定人数**：`E_W >= ceil(2W/3)`，分母是配置总权重，不是有效权重；
3. **胜方阈值**：赞成满足 `3 * approve_weight >= 2 * E_W`，或反对满足 `3 * reject_weight >= 2 * E_W`；
4. **胜方席位门禁**：达到权重阈值的一方还必须达到冻结的 `minimum_winning_seats`，其值不得小于 2；
5. 赞成满足 3、4 ⇒ `APPROVED`；反对满足 3、4 ⇒ `REWORK_REQUIRED`；其余 ⇒ `DEADLOCK`。

全部计算使用整数，不使用浮点数。

配置期单席位上限防止天然独裁；运行期两个 quorum 防止高权重席位缺席后由过低权重决定；胜方最少席位数防止单席位在运行时单独裁决。三者叠加，不互相替代。

### 7.3 必须固化的决策表

| 配置 | 票面 | 结果 | 原因 |
|---|---|---|---|
| N=2，1:1 | 两票 YES | `APPROVED` | 两类 quorum 和胜方门禁均满足 |
| N=2，1:1 | 一 YES、一 NO | `DEADLOCK` | 无一方达到 2/3 |
| N=3，2:1:1 | 高权+一低权 YES，另一低权 NO | `APPROVED` | 赞成 3/4 且两席 |
| N=3，2:1:1 | 高权 NO，两低权 YES | `DEADLOCK` | 两方均未同时满足权重阈值和两席门禁 |
| N=3，2:1:1 | 高权 ABSTAIN，两低权 YES | `DEADLOCK` | `E_W=2 < ceil(8/3)=3` |
| N=3，1:1:1 | 一 timeout ABSTAIN，两票 NO | `REWORK_REQUIRED` | 两类 quorum、反对阈值和两席门禁满足 |

高权席位弃权导致其余席位即使一致也可能 deadlock，是本提案接受并要求管理员明确知晓的安全行为。

---

## 8. 三层审计与一致性

| 层 | 位置 | 内容 | 用途 |
|---|---|---|---|
| 语义证据 | evidence ref 的 `docs/reviews/` | 申请、完整结论、处置、人工裁定说明 | 追溯为什么这样开发、发现什么、为何采纳或拒绝 |
| 运行时审计 | `.macao/state.db` | 状态转移、消息、deadline、timeout、override、策略快照、artifact ledger | 恢复与机器审计 |
| 机器快照 | `.macao/archive/<checkpoint>/r<round>/` | manifest、vote result、disposition envelope、hash | 重放每轮协议行为 |

三层同时存在，互相通过 `task_id + checkpoint_ref + review_round + actor + evidence_commit + path + sha256` 关联。任何一层都不能替代其他层：

- 业务方向、验收标准、评审依据和意见取舍的正文必须进入 evidence Git 历史；
- 每次状态转移、timeout、override、push/verify 结果必须进入 SQLite；
- 每个被消费的结构化产物必须归档并正确标记 `consumed_at/archived_path`；
- 完整证据不得只存在于 agmsg、终端日志或模型会话。

---

## 9. PRD/SRS/FAQ/UC 的显式迁移清单

### 9.1 PRD

| 位置 | 必须修改的规范内容 |
|---|---|
| 文首版本、§1.2、§3.3 | 一次升级为 v2.5；加入 disposition HOLD、E5a、E6 完整处置守卫和 E7 issue 豁免字段 |
| §2.1 | `.dev.yml` 改为结构化信封，增加全文 `path/commit/sha256` |
| §2.2 | 承认显式 `ABSTAIN`，区分 manifest/timeout 来源；`.review.yml` 增加稳定 issue ID、分类和全文引用 |
| §2.2 写入约定（0042dc3 基线约 L416） | review artifact 不再提交到 source branch，整体迁移到 evidence ref |
| §2.3 | 等权规则升级为 `weighted_2/3_v1`；定义五个独立门禁、整数公式、快照和决策表 |
| §2.4 | 升级 AEP/1.1，加入 `DISPOSITION_REQUIRED`、版本化字节预算和引用失败关闭规则 |
| E3 伴随动作（约 L833） | 删除“`.review.yml` 纳入 source git commit”，改为 inbox → evidence promotion/push/verify |
| §3.4 生命周期（约 L859） | 增加 round-scoped disposition、artifact revision、evidence/archive/ledger 生命周期 |
| §5.2 | 将每个 context 语义块逐项改为内联 locator、source commit 或 evidence 引用，不删除现有语义块 |
| §6 | 增加 disposition deadline、ping、timeout、`NEEDS_ADMIN` 与 source/evidence push 失败的人工接管 |
| §11 | 增加每轮 reviewer/weight policy snapshot、disposition ledger、独立 evidence ref 和远程验证 |
| §14.1 第 7 步（约 L1510） | 删除“归档后随 source git 提交”，改为 canonical evidence ref 与本地 archive 双留痕 |
| §14 | 重写 `init/doctor/reconcile/adopt` 边界、交互/CI 行为和 AI diagnostic-only 边界 |
| §16 | 固化 vote result 与 disposition 的非重叠写者/完整性边界，废止 `issues_summary` 双写方案 |
| 其他 archive/push 表述（约 L1355、L1632、L1658–1669） | 全量检索并把 review 文档/manifest 的 source commit 语义迁移到 evidence ref；不得只改前述四处 |

### 9.2 PRODUCT-FACTS、FAQ 与 UC

- PRODUCT-FACTS F-20 的待定项在 v2.5 接受后解析为“独立 disposition”；F-13/F-18/F-19 保持机器裁决与逐项处置边界；
- 删除 FAQ Q15、UC-1、UC-5、UC-6 中 Executor 回写 `vote_result.issues_summary` 的旧方案；
- UC-5 固化 `issues_index` 的配置顺序 × 原始顺序，不排序去重；
- UC-6 统一处置枚举、round-scoped 路径、全 issue 穷尽性、E5a/E6 守卫和管理员豁免；
- UC-1 使用本提案唯一 `role_view` 表和命令边界；
- UC-4、Schema 与代码保留显式 ABSTAIN，并补全 timeout 来源审计；
- 所有包含“review artifact 随 source git 提交”的 FAQ/UC 语句迁移到 evidence ref。
- 清点 `docs/usercases/` 与 `docs/usecases/` 的重复内容和全部引用，选定唯一规范目录后迁移；兼容链接和引用更新完成前不得直接删除任一目录。

### 9.3 SRS

`docs/SRSv1.md` 作为历史基线不伪装改写早期原文，只在顶部“v2 已重定义”表增加：

- AEP 从正文内联演进为带 hash 的引用协议；
- 单一任务 FSM 与 `role_view` 只读投影；
- 加权共识是 v2.5 新规则，不宣称为 v1 原始设计；
- AI 只参与进程外诊断，状态只能由确定性证据或管理员确认；
- source checkpoint 与 evidence ref 分离。

---

## 10. Schema、代码与上线顺序

### 10.1 Schema

必须同步升级并收紧 `additionalProperties: false`：

- `macao_config.schema.json`：权重、五类门禁、AEP 字节预算、disposition timeout；
- `dev_manifest.schema.json`：review request 全文引用；
- `review_manifest.schema.json`：三值票、显式弃权理由、issue 分类、全文引用和票/issue 条件约束；
- `review_context.schema.json`：完整必需块的 locator/ref 集合；
- `vote_result.schema.json`：完整票面、来源、策略快照、breakdown、原始 `issues_index`；
- 新增 `review_disposition.schema.json`：round、revision、状态、精确覆盖、决定枚举和 `requires_new_checkpoint`；
- AEP Schema：增加 `DISPOSITION_REQUIRED` 及其 payload。

### 10.2 实施顺序

1. 先修改 PRD v2.5、SRS 兼容说明、PRODUCT-FACTS 状态、FAQ 和 UC，消除双真源；
2. 实现新旧 Schema 的版本读取和 fail-closed 校验；
3. 实现 inbox/evidence ref、refspec、路径与 SHA-256 校验；
4. 实现 AEP 字节预算和 `DISPOSITION_REQUIRED` deadline/ping；
5. 实现权重快照、整数共识公式和显式/超时 ABSTAIN；
6. 实现 disposition 生命周期及 E4/E5/E5a/E6/E7 守卫；
7. 实现 `init/doctor/reconcile/adopt` 的证据矩阵和确认事务；
8. 完成兼容 fixture、迁移工具和全部验收后切换默认协议版本。

同一 review round 不得混用等权/加权规则、AEP/1.0/1.1 或内联/引用式 context。

### 10.3 最低验收场景

1. 全票通过且无 issue，直接进入 `MERGING`；
2. 加权批准但存在少数方 `BLOCKING`，缺 disposition 时 HOLD，逐项 `REJECTED/DEFERRED` 且均不需新 checkpoint 后可合并；
3. 批准后任一处置声明 `requires_new_checkpoint=true`，经 E5a 进入 `REWORK`，必须产生新 commit 和新 round；
4. disposition 缺布尔字段、漏 issue、多 issue、重复 issue 或 hash 不匹配均失败关闭；
5. `REWORK_REQUIRED` 下完整 disposition、新 commit、新 `.dev.yml` 和新申请共同满足 E6；
6. disposition 超时停在当前状态、发送人工接管，不静默合并或重提；
7. E7 把拒绝覆盖为批准时，所有 `exempt_issue_ids` 都有 `EXEMPTED_BY_ADMIN + override_id`；
8. 显式 ABSTAIN 与 timeout ABSTAIN 计票同构、来源和 responded/accounted 统计不同；
9. AEP 超预算时拒绝发送，改用引用后成功；路径越界、commit 不可达、hash 不匹配均失败关闭；
10. 本地 staging 与远程 inbox 均可被原字节 promotion；未验证 evidence push 时不能 source merge；
11. source push 成功而 post-merge evidence push 暂时失败时保持 `MERGING` 并可重试，不做本地假回滚；
12. N=2 等权和 N=3 `2:1:1` 的完整决策表；高权 ABSTAIN + 两低权 YES 明确得到 `DEADLOCK`；
13. 单席位达到权重阈值但胜方席位数不足时不能单独决定；不满足配置期单席位上限时拒绝启动；
14. round 中途修改权重不影响已冻结策略；
15. 既有项目唯一状态可生成确定性恢复计划，歧义状态必须询问管理员；AI 错误诊断不能写 State Store；
16. `role_view` 对每个 task state 和 Reviewer 已/未提交条件的投影与唯一表一致；
17. `docs/reviews/`、SQLite、archive 和远程 evidence ref 可通过同一 artifact identity 互相追溯；
18. 多轮 disposition 路径不覆盖，消费记录正确填写 `consumed_at/archived_path`；
19. `DEFERRED` 无 `followup_task_id` 在单任务 FSM 下合法，当前任务完成后再创建后续任务；
20. evidence ref 前进不改变 source HEAD 或 `checkpoint_ref`，`macao reviews show/export` 可读取完成任务的证据。

---

## 11. 参数治理与后续决策

以下参数不改变本提案的结构裁定，可以在实现 PoC 或管理员配置中确定：

1. AEP 默认 16 KiB/单字段 2 KiB 是否需要按实测调整；
2. 非等权投票的首批权重、校准 corpus、有效期和复核频率；
3. disposition 默认 30 分钟是否按团队规模调整；
4. evidence ref 的保留期和远程 inbox ref 清理周期。
5. `docs/usercases/` 与 `docs/usecases/` 合并后的唯一目录名和兼容期。

独立 disposition、显式 ABSTAIN、E5a、`DEFERRED` 的可选 task ID、证据不自动合入 source、唯一 `role_view` 和 `init/doctor/reconcile/adopt` 边界不再列为开放项。

---

## 12. 对 `0042dc3` 评审意见的闭环

| 评审项 | 修订结果 |
|---|---|
| GLM P0-1 / Grok P1-1：独立 disposition 与旧 `issues_summary` 冲突 | D-2 明确选择独立产物，并在 §9 列出 PRODUCT-FACTS/FAQ/UC 的废止与迁移 |
| GLM P1-1：显式 ABSTAIN 与实现冲突 | D-3、§4.1、§10 明确保留显式弃权并区分 timeout 来源 |
| GLM P1-2：遗漏 source git 提交迁移点 | §9.1 覆盖约 L416/L833/L859/L1510 及其他 archive/push 文本 |
| GLM P2：处置不穷尽、角色术语、独裁帽、豁免、E4c、2/3 歧义 | §4.3、§6.3、§7、§4.4、E5a 和 §7.2 分别关闭 |
| Grok P0-1：由语义推断是否改码 | D-5 和 Schema 强制 `requires_new_checkpoint` |
| Grok P0-2：BACKLOG 与单任务 FSM 冲突 | D-4 改为 `DEFERRED`，task ID 可选且不查库 |
| Grok P1-2/P1-9：2:1 示例、门禁和高权弃权 | §7 使用 N=3 的 2:1:1，定义五类门禁、整数公式和接受的 deadlock 行为 |
| Grok P1-3/P1-4：HOLD 无协议边、timeout、管理员豁免 | §4.4 增 AEP/1.1 消息、deadline、ping、HOLD 和 E7 issue 级审计 |
| Grok P1-5：context 语义块不完整 | §5.2 对现行所有语义块逐项映射并区分首轮/后续轮 |
| Grok P1-6：evidence 投递/fetch/push/可见性未闭合 | §5.4 给出本地/远程投递、promotion、refspec、双阶段 push 与 show/export |
| Grok P1-7/P1-8：路径无 round、覆盖范围不一致 | §4.3 采用 round-scoped 路径并要求全部 issue 精确覆盖 |
| Grok P2：命令边界、枚举、顺序、示例、AI、预算 | §6.1、§4.3、§4.3-2、§4.6、P-4、§5.3 分别关闭 |
| Gemini 建议：票/issue 约束、单席位防支配、init 交互/CI | §4.1、§7.1-7.2、§6.1 分别纳入 |
| Qwen L1 复审 P3：生效清单遗漏 PRODUCT-FACTS、目录名分裂 | 文首补齐 PRODUCT-FACTS；§9.2/§11 登记目录清点、迁移和兼容期；PRD 升版及本稿提交由既有 §9.1/本次提交关闭 |

---

## 13. 建议决议

本修订稿申请重新进行 L1 评审，不申请直接进入编码或标记为已实现。若本提案获批：

1. PRD 文首和正文一次升级到 v2.5；
2. 按 §9 先消除文档体系中的双真源；
3. 按 §10 的依赖顺序修改 Schema、代码、fixture 和测试；
4. 实施和验收完成前，现有 v2.3/v2.4 行为保持不变；
5. 全部迁移与验收场景通过后，才将相关事实标记为 `IMPLEMENTED`。
