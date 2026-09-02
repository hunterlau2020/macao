# MACAO PRD 修改提案 v2.5：内容边界、评审处置与可审计协作

> **状态**：DRAFT v0.3 / 已全量吸收四方独立评审意见（Qwen、Gemini、Kimi、Grok），完备闭环
> **日期**：2026-09-01
> **目标基线**：`docs/MACAO_PRD_v2.md` 现行内容（升级目标：v2.5）
> **事实基线**：`docs/usercases/PRODUCT-FACTS.md` F-1～F-22（commit `99fe377`）
> **评审输入**：`docs/reviews/2026-09-01-review-result-0042dc3-{gemini,glm,grok,qwen}.md`、`2026-09-01-review-2.5-2-{gemini,grok}.md`、`2026-09-01-review-result-PRD-v2.5-v0.2-kimi.md`
> **生效条件**：本提案经评审批准，并同步修改 PRD v2.5、SRS 兼容说明、PRODUCT-FACTS 状态、Schema、代码、fixture、测试、FAQ 和 UC 后，方可标记为 `ACCEPTED/IMPLEMENTED`

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

## 2. 本提案作出的规范裁定（D-1 ～ D-9）

本节不是待选方案，而是 v2.5 的明确设计输入。

| ID | 裁定 |
|---|---|
| D-1 | `vote_result.json` 只保存机器输入、策略快照、票面、原始 issue 索引和机器决策，由 Orchestrator 单一写入并保持不可变；DEADLOCK 亦即时落盘留痕。 |
| D-2 | Executor 的逐项采纳、延期、拒绝和请求人工处理写入独立、按 round 保存的 `review_disposition`。该方案正式替代旧 FAQ/UC 中由 Executor 回写 `vote_result.issues_summary` 的双写者方案，并解析 PRODUCT-FACTS F-20 的待定项。 |
| D-3 | Reviewer 可以显式投 `ABSTAIN`；Reviewer 主动弃权与 Orchestrator 因超时合成的弃权在计票上同构，在审计来源（`source: manifest | timeout`）上必须严格区分。 |
| D-4 | `BACKLOG` 统一命名为 `DEFERRED`。它只要求理由，`followup_task_id` 可选且不检查 State Store 中已存在任务；后续任务应在当前任务 `DONE` 后由人或 Executor 创建。 |
| D-5 | 处置项必须显式填写 `requires_new_checkpoint: boolean`。Orchestrator 不得从自然语言理由、文件类型或处置枚举推断是否需要新检查点。 |
| D-6 | 加权投票同时保留配置期单席位防支配上限（$3w_i < 2W$）、运行期席位 quorum（$\lceil 2N/3 \rceil$）、运行期权重 quorum（$\lceil 2W/3 \rceil$）、胜方权重阈值（$3W_{win} \ge 2E_W$）和胜方最少席位数（$\ge 2$）。 |
| D-7 | AEP 升级为 AEP/1.1，增加 `DISPOSITION_REQUIRED`（第 8 类消息）；AEP/agmsg 只承载控制字段与可验证引用，定义 16 KiB 字节预算。 |
| D-8 | 评审证据进入独立 Git evidence ref（`refs/macao/evidence/...`），不因补写证据而改变被评审的 source `checkpoint_ref`；任务完成不自动把证据合入 source branch。 |
| D-9 | `macao init` 是入口，`doctor` 只读诊断，`reconcile` 是确定性恢复执行器，`adopt` 是 `init --adopt-existing` 的稳定别名。 |

---

## 3. 核心设计原则

### P-1 Orchestrator 零语义创作

Orchestrator 可以：

- 校验 Schema、路径、commit、SHA-256、round、deadline 和身份；
- 按已冻结的 Reviewer 配置顺序拼接结构化字段；
- 根据配置执行纯整数计票公式；
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
- AEP/agmsg 是有版本化字节预算（16 KiB）的控制与引用通道；
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

Schema 必须通过 `allOf` 条件约束表达以下规则：

- 存在 `BLOCKING` ⇒ 该 Reviewer 的票只能是 `NO_APPROVE`；
- `YES_APPROVE` ⇒ 不得包含 `BLOCKING`；
- `NO_APPROVE` ⇒ 至少包含一条 `BLOCKING`；
- 显式 `ABSTAIN` ⇒ issue 列表为空，且必须提供 `abstain_reason`；
- 超时合成的 `ABSTAIN` 没有 Reviewer manifest，由 Orchestrator 记录 `source: timeout`、deadline 和最后一次 ping；
- 主动弃权与超时弃权均不进入有效票分母。`reviewers_responded` 统计收到合法 manifest 的席位（含主动弃权），`reviewers_accounted` 等于合法 manifest 席位数加已合成 timeout 的席位数。

“有条件通过，但条件必须先修复”必须表示为 `NO_APPROVE + BLOCKING`，不能用 `YES_APPROVE` 表示。

`BLOCKING` 是单个 Reviewer 对其票的约束，不是绕过共识公式的单票否决权。加权结果仍可能在少数 Reviewer 报告 `BLOCKING` 时得到 `APPROVED`；这些 issue 仍必须被 Executor 逐项处置。

### 4.2 不同机器结论的处理时点与覆盖转移

| 场景 | 处理状态 | 行为 | 离开条件 |
|---|---|---|---|
| `REWORK_REQUIRED` | `CONSENSUS_CHECK` → `REWORK`（E5） | 机器计票拒绝，通知 Executor；Executor 写本轮 issue disposition 并修复代码 | E6 守卫（完整 disposition、新 commit、新 `.dev.yml` 与新申请） |
| `APPROVED` 且无 issue | `CONSENSUS_CHECK` → `MERGING`（E4） | 无语义处置 | E4 机器守卫通过 |
| `APPROVED` 且有 issue | 留在 `CONSENSUS_CHECK`（HOLD） | 发送 `DISPOSITION_REQUIRED`；Executor 逐项处置 | 全部 `requires_new_checkpoint=false` 时 E4；任一为 `true` 时 E5a 进入 `REWORK` |
| `DEADLOCK` 或门禁失败 | `CONSENSUS_CHECK`（HOLD） | 即时落盘 `vote_result.json`（`decision: DEADLOCK`），发送 `HUMAN_OVERRIDE_REQUEST` | E7 管理员裁决（`APPROVED | REWORK | RETRY_REVIEW | CANCEL`） |
| disposition 超时 | 当前状态（HOLD） | 发送 `HUMAN_OVERRIDE_REQUEST` | E7 管理员裁决（`APPROVED(带豁免) | EXTEND | REWORK | CANCEL`） |
| disposition 标记 `NEEDS_ADMIN` | 当前状态（HOLD） | 发送 `HUMAN_OVERRIDE_REQUEST`（带 issue 级上下文） | 管理员提供 issue 级应答后 Executor 产出 FINAL disposition |

#### 管理员 E7 覆盖与豁免语义

1. **DEADLOCK 覆盖为 APPROVED**：管理员提交 override，指定 `exempt_issue_ids` 与 note，系统生成 `override_id` 并记录独立 `admin_override.json`。Executor 据此将相关 issue 标记为 `EXEMPTED_BY_ADMIN` 并产出 FINAL disposition，满足 E4 进入 `MERGING`。
2. **处置超时覆盖为 APPROVED**：管理员提交 override 附带 `exempt_issue_ids` 与 note，系统生成独立 `admin_override.json`（含 `override_id`）；执行者在 `.macao/.dispositions/r<round>/executor.disposition.yml` 中将对应 issue 标记为 `EXEMPTED_BY_ADMIN`+`override_id` 并提交 FINAL disposition，编排器校验满足 E4 进入 `MERGING`。严格保持执行者对 disposition 的单一垄断写者权，严禁管理员代写 disposition。
3. **REWORK_REQUIRED / 门禁失败覆盖为 APPROVED**：当发生 DEADLOCK 或 REWORK 轮次耗尽进入 HOLD 时，管理员若决定豁免推进，出具独立 `admin_override.json`（含 `override_id` 与 `exempt_issue_ids`）；系统解除 HOLD 并将执行者角色投影置为 `SHOULD_DISPOSE`；执行者据此出具带有 `EXEMPTED_BY_ADMIN`+`override_id` 且 `requires_new_checkpoint: false` 的 FINAL disposition；编排器双重校验合法后经 E4 转移推进至 `MERGING`（严格遵守单写者垄断，严禁无 FINAL disposition 直跳 `MERGING`）。
4. **`vote_result.json` 不可变**：任何 override 不修改原 `vote_result.json` 的 `decision` 字段，终局机器状态与人工裁定依据通过 `override_id` 与 SQLite 审计表链接。

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
executor:
  id: "cc-ds4"
  role: "executor"
  cli: "claude-code"
disposition_status: "FINAL"  # DRAFT | FINAL | PENDING_ADMIN
generated_at: "2026-09-01T12:10:00Z"
issues_index_sha256: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
full_document:
  path: "docs/reviews/2026-09-01-review-disposition-task-1-r1.md"
  evidence_commit: "c2d3e4f"
  sha256: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
vote_result_ref:
  path: ".macao/vote_result.json"
  evidence_commit: "c2d3e4f"
  sha256: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
dispositions:
  - issue_id: "codex/SEC-01"
    reviewer_id: "codex"
    disposition_type: "ADOPTED"
    requires_new_checkpoint: true
    rationale: "已在代码中增加超时捕获与重试机制"
    full_document:
      path: "docs/reviews/2026-09-01-review-disposition-task-1-r1.md"
      evidence_commit: "c2d3e4f"
      sha256: "<sha256>"
      anchor: "#codex-sec-01"
```

`disposition_type` 统一为：

- `ADOPTED`：已采纳；`requires_new_checkpoint` 可为 `true` 或 `false`；
- `DEFERRED`：延期，必须有理由，`requires_new_checkpoint=false`；
- `REJECTED`：不采纳，必须有理由，`requires_new_checkpoint=false`；
- `NEEDS_ADMIN`：无法由 Executor 决定，`disposition_status=PENDING_ADMIN`，当前状态 HOLD；
- `EXEMPTED_BY_ADMIN`：仅在有效 E7 override 覆盖时使用，必须有 `override_id`，`requires_new_checkpoint=false`。

强制规则：

1. 每个有效 disposition 版本必须按 `issues_index` 精确覆盖本轮全部 issue，一项不多、一项不少、每项恰好一次；
2. `issues_index` 的稳定顺序是“冻结的 Reviewer 配置顺序 × 各 manifest 原始 issue 顺序”，禁止排序、去重和语义合并；
3. `requires_new_checkpoint` 对每一项都是必填布尔值；缺失时失败关闭；
4. Markdown 保存完整理由，YAML 只保存结构化索引和锚点；
5. `disposition_status` 枚举为 `DRAFT | FINAL | PENDING_ADMIN`；产物一旦被状态转移消费即冻结并归档；`FINAL` 状态下严禁遗留 `NEEDS_ADMIN`；
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
- 超时停留在 `CONSENSUS_CHECK`（HOLD 态等待管理员介入）；
- `NEEDS_ADMIN` 处置：管理员在 override 中对单条 issue 提供明确答复（记录独立 `admin_override.json` 与 `override_id`），执行者读取 override 后提交带 `EXEMPTED_BY_ADMIN` + `override_id` 的 FINAL disposition（严禁管理员代写 disposition）。

### 4.5 状态转移表修订（E3 ～ E7）

| 转移 | 源状态 → 目标状态 | 新增或修订守卫 |
|---|---|---|
| **E3** | `WAITING_REVIEW` → `CONSENSUS_CHECK` | **所有配置席位已响应（收到合法 manifest）或已被持久化 timeout 机制纳入 accounted 集合**（不再提早触发） |
| **E4** | `CONSENSUS_CHECK` → `MERGING` | 机器决策为 `APPROVED`（或经合法 E7 override 裁决）；无 issue，或存在 FINAL disposition 精确覆盖全部 issue 且所有 `requires_new_checkpoint=false` |
| **E5** | `CONSENSUS_CHECK` → `REWORK` | 机器决策为 `REWORK_REQUIRED`（且未发生即时 E7 覆盖） |
| **E5a** | `CONSENSUS_CHECK` → `REWORK` | 机器决策为 `APPROVED`，FINAL disposition 精确覆盖全部 issue，且至少一项 `requires_new_checkpoint=true` |
| **E6** | `REWORK` → `READY_FOR_REVIEW` | 前一轮 FINAL disposition 已覆盖全部 issue；新 source commit（不等于上一轮）、新 `.dev.yml`、新 review request 和 round 均有效 |
| **E7** | `HOLD`（`CONSENSUS_CHECK`） → 管理员指定目标状态 | override 选项（`APPROVED | REWORK | RETRY_REVIEW | CANCEL | EXTEND`）、note、操作者、issue 级豁免与 `override_id` 完整并审计 |

### 4.6 `vote_result.json` 完整示例

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
    "max_single_weight_share_numerator": 2,
    "max_single_weight_share_denominator": 3
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

### 5.2 现行 `review_context` 逐块迁移

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

### 5.3 AEP/agmsg 字节预算

- 配置项 `aep.max_message_bytes` 默认 `16384`（16 KiB），按 UTF-8 编码后的完整信封计算；
- `aep.max_inline_text_bytes` 默认 `2048`；
- 禁止内联 diff、完整申请、完整结论、处置正文和终端日志；超限内容必须外置并通过 `path + commit + sha256` 引用。

### 5.4 evidence ref 投递与两阶段 Push

1. **Ref 约定**：`refs/macao/evidence/<task_id>/r<round>`；远程 inbox 为 `refs/macao/inbox/<task_id>/r<round>/<actor_id>/<message_id>`；本地 staging 为 `.macao/inbox/...`。
2. **投递与提升**：作者写入 staging/inbox $\to$ Orchestrator 校验 Schema 与 Hash $\to$ 串行提升至 canonical evidence ref。
3. **两阶段验证**：
   - 阶段 1（Pre-merge Evidence Seal）：进入 source merge 前必须验证 evidence 已成功 push（`ls-remote` 校验通过）；
   - 阶段 2（Post-merge Audit Evidence）：source push 成功后生成最终审计快照。若 post-merge push 临时失败，保持 `MERGING` 并重试，**严禁本地回滚已成功的远端 source 分支**。
4. **单机本地模式退化**：在无 remote origin 的本地单机环境下，跳过 `ls-remote` 检查，以本地 Git ref 存在与 SHA 校验作为等价通过条件。
5. **证据可见性**：证据文档不自动并入 source 分支代码，通过 `macao reviews show <task_id>` 与 `macao reviews export <task_id> --to <dir>` 查阅。

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
| `macao reviews show / export` | 查阅与导出 evidence ref 中的评审及处置产物 | 否 |

交互模式自动探测并推荐 mode；CI/脚本模式必须显式声明子命令。歧义状态遇 `--yes` 严格 fail-closed。

### 6.2 动态状态判断优先级

1. `state.db` 中未终结任务、round、checkpoint 和不可变审计事件；
2. 当前 task/round 且 Schema、commit、hash 有效的 `.macao/` 产物；
3. archive 与 evidence Git 历史中的已消费产物；
4. Git branch、worktree、merge 和 push 拓扑；
5. CLI 进程、自报状态、终端日志等弱信号。

### 6.3 统一规范名 `role_view` 与 `next_action`

| 任务状态与前置条件 | Executor `role_view` | Reviewer `role_view` | `next_action` |
|---|---|---|---|
| `IDLE` / 无活动任务 | `AWAIT_TASK` | `AWAIT_TASK` | `WAIT_TASK_INPUT` |
| `CODING` / `REWORK` | `SHOULD_CODE` | `IDLE_WAIT_DISPATCH` | `EXECUTOR_DEVELOPING` |
| `READY_FOR_REVIEW` | `CHECKPOINT_SUBMITTED` | `IDLE_WAIT_DISPATCH` | `DISPATCH_REVIEWS` |
| `WAITING_REVIEW`（席位未提交且有效） | `AWAIT_REVIEWS` | `SHOULD_REVIEW` | `AWAIT_REVIEW_SUBMISSIONS` |
| `WAITING_REVIEW`（席位已提交有效产物） | `AWAIT_REVIEWS` | `REVIEW_SUBMITTED` | `AWAIT_REMAINING_OR_TIMEOUT` |
| `CONSENSUS_CHECK`（尚无 vote_result） | `AWAIT_DECISION` | `AWAIT_DECISION` | `TALLY_CONSENSUS` |
| `CONSENSUS_CHECK`（`requires_disposition` 且无 FINAL） | **`SHOULD_DISPOSE`** | `AWAIT_DECISION` | **`NOTIFY_EXECUTOR_DISPOSE`** |
| `CONSENSUS_CHECK`（HOLD: DEADLOCK/超时/NEEDS_ADMIN） | `AWAIT_HUMAN` | `AWAIT_HUMAN` | `ASK_ADMIN` |
| `MERGING` | `AWAIT_MERGE` | `AWAIT_MERGE` | `PERFORM_MERGE_AND_PUSH` |
| `UNKNOWN` | `AWAIT_HUMAN` | `AWAIT_HUMAN` | `RUN_DOCTOR_OR_ASK_ADMIN` |
| `DONE` / `CANCELLED` | `AWAIT_TASK` | `AWAIT_TASK` | `TASK_COMPLETED` |

---

## 7. 加权 2/3 共识规则

### 7.1 配置与纯整数五重门禁

```yaml
team:
  reviewers:
    - id: codex
      vote_weight: 2
    - id: kimi
      vote_weight: 1
    - id: gemini
      vote_weight: 1
policy:
  consensus_rule: weighted_2/3_v1
  seat_quorum_ratio: "2/3"
  weight_quorum_ratio: "2/3"
  decision_threshold: "2/3"
  minimum_winning_seats: 2
  max_single_weight_share_exclusive: "2/3"
```

设配置席位数为 $N$，配置总权重为 $W$，非弃权有效席位数为 $E_N$，非弃权有效权重为 $E_W$：

1. **配置期独裁帽**：$\forall i, 3 \times w_i < 2 \times W$（不满足则拒绝启动）；
2. **席位法定人数**：$E_N \ge \lceil 2N/3 \rceil$；
3. **权重法定人数**：$E_W \ge \lceil 2W/3 \rceil$（分母为配置总权重 $W$）；
4. **胜方权重阈值**：赞成满足 $3 \times approve\_weight \ge 2 \times E_W$，或反对满足 $3 \times reject\_weight \ge 2 \times E_W$；
5. **胜方最少席位门禁**：胜方有效席位数 $\ge minimum\_winning\_seats$（默认 2，且 $2 \le minimum\_winning\_seats \le N$）。

### 7.2 决策表矩阵

| 配置 | 票面情况 | 决策结果 | 逻辑推导原因 |
|---|---|---|---|
| $N=2$ (1:1) | 两票 YES | `APPROVED` | 两类 Quorum 及两席门禁均满足 |
| $N=2$ (1:1) | 一 YES、一 NO | `DEADLOCK` | 无一方达到 2/3 权重 |
| $N=2$ (1:1) | 一 YES、一 ABSTAIN | `DEADLOCK` | 有效席位 $1 < 2$，席位 Quorum 不足 |
| $N=3$ (2:1:1) | 高权(Y) + 一低权(Y) + 一低权(N) | `APPROVED` | 赞成权重 $3 \ge \lceil 8/3 \rceil=3$，席位 $2 \ge 2$ |
| $N=3$ (2:1:1) | 高权(N) + 两低权(Y) | `DEADLOCK` | 赞成权重 $2 < 3$；反对席位 $1 < 2$ |
| $N=3$ (2:1:1) | 高权(ABSTAIN) + 两低权(Y) | `DEADLOCK` | 有效权重 $2 < 3$，权重 Quorum 不足 |
| $N=3$ (2:1:1) | 高权(Y) + 一低权(ABSTAIN) + 一低权(N) | `DEADLOCK` | 赞成权重 $2 \times 3 = 6 \ge 2 \times 3$，但赞成席位 $1 < 2$ |
| $N=3$ (1:1:1) | 一 timeout ABSTAIN + 两票 NO | `REWORK_REQUIRED` | 两类 Quorum、反对权重及两席门禁均满足 |

---

## 8. 三层审计与一致性

| 层 | 位置 | 内容 | 用途 |
|---|---|---|---|
| 语义证据 | evidence ref 的 `docs/reviews/` | 申请、完整结论、处置、人工裁定说明 | 追溯为什么这样开发、发现什么、为何采纳或拒绝 |
| 运行时审计 | `.macao/state.db` | 状态转移、消息、deadline、timeout、override、策略快照、artifact ledger | 恢复与机器审计 |
| 机器快照 | `.macao/archive/<checkpoint>/r<round>/` | manifest、vote result、disposition envelope、hash | 重放每轮协议行为 |

---

## 9. 文档体系逐项迁移清单（消除双真源）

### 9.1 PRD (`docs/MACAO_PRD_v2.md`)

1. **版本升级**：文首及全局标题升级为 **v2.5**；
2. **状态机与守卫**：
   - §1.2 & §3.3：增加 disposition HOLD、E5a 转移边、E6 完整处置守卫；
   - E3 伴随守卫修改为：**所有席位已响应或进入持久化超时**；
   - E7 明确包含 `REWORK_REQUIRED` 覆盖与 issue 豁免契约；
3. **产物与写者解耦**：
   - §2.1：`.dev.yml` 改为信封，增加全文引用；
   - §2.2：`.review.yml` 引入三值票（含 `ABSTAIN` 理由）、issue 分类与全文引用；
   - §2.2 / §3.4 / §14.1 / §16.4：全面删除“评审产物提交到 source branch”的表述（包括 L416、L833、L859、L1355、L1510、L1632、L1658 等全量位置），迁移到 Evidence Git Ref；
   - §2.3：升级为 `weighted_2/3_v1` 五重门禁；
   - §2.4：升级 AEP/1.1 与 16 KiB 字节预算；
   - §16：固化 `vote_result.json`（Orchestrator 单写）与 `review_disposition`（Executor 单写）边界，彻底废止 `issues_summary` 双写方案；
4. **Context 与接管**：
   - §5.2：10 大 context 语义块逐项映射；
   - §14：`init / doctor / reconcile / adopt` 边界、`role_view` 投影与 AI diagnostic-only 约束。

### 9.2 PRODUCT-FACTS、FAQ 与 UC-1～UC-10

- **PRODUCT-FACTS**：F-20 待定项解析为独立 `review_disposition`，标记全集 F-1～F-22 为 `ACCEPTED-FOR-V2.5-SPEC`；
- **FAQ.md**：更新 Q10、Q11、Q12、Q14、Q15、Q16，废止 `vote_result.issues_summary` 双写描述，更新为独立 disposition 与 Evidence Ref；
- **UC-1**：采用唯一 `role_view`（含 `SHOULD_DISPOSE`）与 `next_action` 表；
- **UC-4**：保留显式 `ABSTAIN` 与超时来源区分；
- **UC-5**：E3 触发条件改为全席位 accounted；固化配置顺序 × 原始顺序的 `issues_index`；更新 DEADLOCK 即时落盘与 E7 关联；
- **UC-6**：更新为独立 `review_disposition` 产物、`requires_new_checkpoint` 布尔值守卫及 E5a/E6 状态机流转；
- **UC-2 / UC-3 / UC-7 ～ UC-10**：全量清理“评审产物随 source commit 提交”的旧描述，统一为 Evidence Ref。

### 9.3 SRS (`docs/SRSv1.md`)

顶部“v2 已重定义”表增加：
- AEP 1.1 引用协议与 16 KiB 预算；
- 单一任务 FSM 与 `role_view` 投影；
- 加权 2/3 共识五重门禁；
- AI 仅参与进程外诊断；
- source checkpoint 与 evidence ref 分离。

---

## 10. Schema、代码与上线顺序

### 10.1 Schema 变更

1. `macao_config.schema.json`：权重、五类门禁参数、AEP 字节预算、disposition 超时；
2. `dev_manifest.schema.json`：review request 全文引用；
3. `review_manifest.schema.json`：三值票、显式弃权理由、`BLOCKING/ADVISORY` 分类、全文引用、`allOf` 条件互锁；
4. `review_context.schema.json`：10 大必需块 locator/ref 集合；
5. `vote_result.schema.json`：策略快照、breakdown、原始 `issues_index`、`decision: DEADLOCK`、`resolution` 枚举；
6. `review_disposition.schema.json`（新增）：round、revision、状态、精确覆盖、决定枚举、`requires_new_checkpoint`；
7. AEP Schema：新增 `DISPOSITION_REQUIRED` payload。

### 10.2 实施顺序

1. **第 1 步**：文档体系升级（PRD v2.5 / SRS / PRODUCT-FACTS / FAQ / UC），消除双真源；
2. **第 2 步**：Schema 同步收紧（`additionalProperties: false`）；
3. **第 3 步**：实现 Evidence Git Ref、Refspec 与远程两阶段 Push 校验；
4. **第 4 步**：AEP/1.1 协议升级与 `DISPOSITION_REQUIRED` 调度通道；
5. **第 5 步**：权重快照、纯整数计票函数与显式/超时 ABSTAIN 引擎；
6. **第 6 步**：Review Disposition 生命周期、E5a 转移与 E7 豁免机制；
7. **第 7 步**：`init / doctor / reconcile / adopt` 状态接管引擎；
8. **第 8 步**：通过 20 项最低验收场景测试，切换默认协议版本。

---

## 11. 建议决议

1. 确认本提案为 **`ACCEPTED`**；
2. 正式升级 [`docs/MACAO_PRD_v2.md`](file:///home/debian/macao/docs/MACAO_PRD_v2.md) 至 **v2.5**；
3. 同步完成 SRS、FAQ、UC 全套文档改造，并建立代码变更清单。
