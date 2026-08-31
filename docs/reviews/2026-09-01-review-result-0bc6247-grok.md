# PRD v2.5 产品方案 / 技术设计同步 评审结论

- **评审日期**：2026-09-01
- **评审人**：grok
- **评审对象**：[`docs/reviews/2026-09-01-review-request-PRD-v2.5-Design-Sync.md`](2026-09-01-review-request-PRD-v2.5-Design-Sync.md)
- **对应 commit**：`0bc6247`（`docs: sync PRD v2.5 design, add code change inventory, and submit review request`）
- **对齐基准**：`docs/MACAO_REVIEW_GUIDELINES.md` §1–§6、§9、§11；`docs/usercases/PRODUCT-FACTS.md` F-1～F-22；提案 D-1～D-9；上轮 grok `cb0e9a7` / `2026-09-01-review-2.5-2-grok.md`
- **定级申请**：L1 DOC-ALIGNED / PG-0（v2.5 实施基线定级与技术准入）
- **机器票**：`NO_APPROVE`
- **证据**：`BLOCKING` × 1（P0），`BLOCKING` × 4（P1），`ADVISORY` × 若干

**结论：不授予 L1 DOC-ALIGNED / PG-0，不得据此进入 Phase 1～5 编码。** 架构方向 D-1～D-9 仍成立，§3.3 转移表、§14.2 `role_view`、UC-1 h1/h2、UC-5 计票主路径已吸收上轮意见。但申请所称「全量完成同步」「专家关切 100% 物理闭环」不成立：权威 PRD 的「唯一规范入口」与场景推演仍按 v2.3.1 运行，与同一份 PRD 的 §3.3 / D-1 / E4 / E5a 互斥；处置契约、FAQ、F-20、UC-7、§6.1 触发器、AEP 示例与代码清单路径均未收敛到可唯一实现的对照表。

本轮不同意把 `0bc6247` 标为实施基线。

---

## 0. Reviewer 自审

- 上轮本人 P1-1（处置超时后 E7 `APPROVED`）在提案 §4.2 第 2 条有「管理员可签署替代 FINAL disposition」草案，**未写入 PRD §3.3 E7 / §6.1**，判定 **PARTIALLY_VERIFIED**。
- 上轮本人 P1-2（`SHOULD_DISPOSE` / `NOTIFY_EXECUTOR_DISPOSE`）在 PRD §14.2 与 UC-1 h1/h2 **VERIFIED**；FAQ Q12 仍为旧表，判定 **CONTRADICTED**。
- 不把 STATUS 自述「Grok 批准实施」当作证据；上轮原文机器票为 `NO_APPROVE`。
- 示例围栏：PRD 8 段 JSON、5 段 YAML，提案 1 JSON + 3 YAML，UC-6 1 YAML，均能 `json.loads` / `yaml.safe_load`。
- CODE/TEST：本轮对象是文档体系与实施清单，实现代码 **NOT_APPLICABLE**（清单路径核验除外）。

---

## 一、申请闭环表核验（相对申请 §3）

| 申请声称 | 本轮判定 | 证据要点 |
|---|---|---|
| Kimi P0-1 E7 豁免 | **PARTIALLY_VERIFIED** | §3.3 E7 有 `exempt_issue_ids` 与 `admin_override.json`；场景三 / Layer 1c 仍回写终局 `vote_result` |
| Kimi P1-1 E3 全席位 accounted | **PARTIALLY_VERIFIED** | §3.3 E3 已改；§3.2 Layer 1b 与流程图仍用法定人数提前截断 |
| Kimi P1-2 DEADLOCK 即时落盘 | **CONTRADICTED** | E3 伴随动作写「即时落盘」；场景三步骤 5 写「不写 `vote_result.json`」 |
| Kimi P1-3 `NEEDS_ADMIN` | **PARTIALLY_VERIFIED** | 提案 / role_view 有；§6.1 触发器列表无此项 |
| Grok P1-1 处置超时 | **CONTRADICTED**（相对申请落点） | 申请写「PRD §6.1 定义 `timeouts.review_disposition`」；§6.1 无该字段，仅 §1.2 超时列写 30m |
| Grok P1-2 `SHOULD_DISPOSE` | **PARTIALLY_VERIFIED** | PRD §14.2 / UC-1 已补；FAQ Q12 未改 |
| Qwen P1-1 写者边界 | **PARTIALLY_VERIFIED** | Q15 / UC-5 / UC-6 主路径已独立 disposition；Q13 仍写「执行者汇总」；F-20 仍待定 |
| Gemini P1-1 纯整数加权 | **VERIFIED**（公式与 §4.6 示例复算通过） | 配置期 `3w_i<2W`、五门禁与 N=3 `2:1:1` 决策表自洽 |

STATUS.md L67 写「Gemini & Grok 批准实施」与上轮 grok 报告原文相反，属登记错误，不进入本轮定级分子。

---

## 二、已对齐 / 已确认项

1. **D-2 / D-5 方向**：独立 `review_disposition`、`requires_new_checkpoint` 必填布尔、E5a 只读该布尔——UC-6 守卫 1～3 与 PRD §3.3 E4/E5a 同向。
2. **D-6**：`weighted_2/3_v1` 五重纯整数门禁。独立复算 PRD §2.3 示例（N=3，W=4，2 YES + 1 NO）：席位 quorum 3≥2，权重 quorum 4≥3，`3×3≥2×4`，胜方席位 2≥2 → `APPROVED`。提案 §7.2「高权 Y + 低权 ABSTAIN + 低权 N」：`3×2≥2×3` 但席位 1<2 → `DEADLOCK`。与 F-22 同向。
3. **D-8 Evidence Ref**：PRD §2.1/§2.2 写入约定、§5.4 提案、§14.1 归档「不污染 source 分支」一致。
4. **role_view 主表**：PRD L1490–1502 与 UC-1 L131–156 含 `SHOULD_DISPOSE` / `NOTIFY_EXECUTOR_DISPOSE`，覆盖上轮 grok P1-2 的 PRD/UC 落点。
5. **YAML/JSON 围栏可解析**（见 §0）。

---

## 三、P0：必须先解决

### P0-1　权威 PRD 无法唯一推出 v2.5 状态机（识别入口 / 场景三 仍是 v2.3.1）

申请把 `docs/MACAO_PRD_v2.md` 定为「v2.5 权威基准」，并声称 10 状态单一事实源、每步转移由确定性产物驱动。同一文件内部至少三处互相否决，实现者按「唯一规范入口」编码会直接绕过 v2.5 主路径。

**证据 A — Layer 1c 仍按旧终局 `decision` 推进，且 APPROVED 无条件进 MERGING**

```728:747:docs/MACAO_PRD_v2.md
    elif st == AgentState.CONSENSUS_CHECK:
        result = load_and_validate('.macao/vote_result.json', VOTE_RESULT_SCHEMA,
                                   expect_checkpoint_ref=ref,
                                   expect_review_round=rnd)
        if result.valid:
            archive_round_artifacts(ref, rnd)
            # 显式四分支：终局 decision 枚举包含 APPROVED | REWORK_REQUIRED | RETRY_REVIEW | CANCELLED（Schema 强制）
            if result.decision == 'APPROVED':
                return AgentState.MERGING                  # E4
            elif result.decision == 'REWORK_REQUIRED':
                ...
            elif result.decision == 'RETRY_REVIEW':
                return AgentState.WAITING_REVIEW
            elif result.decision == 'CANCELLED':
                return AgentState.CANCELLED
```

- 注释与分支把 `RETRY_REVIEW` / `CANCELLED` 当作 `vote_result.decision`，与 D-1（机器决策仅 `APPROVED | REWORK_REQUIRED | DEADLOCK`，E7 写独立 `admin_override.json`、严禁回写）互斥。
- `decision == APPROVED` 立即 `MERGING`，不读 `requires_disposition`、不读 FINAL disposition、不存在 E5a。与 §3.3 E4（有 issue 必须 FINAL 且全 `requires_new_checkpoint=false`）和 E5a（任一 `true` → `REWORK`）互斥。
- 无 `DEADLOCK` 分支：若按 E3「即时落盘 `decision: DEADLOCK`」，Layer 1c 会在 `result.valid` 后落入未匹配分支，行为未定义（静默 HOLD / 误进 MERGING / 抛错均无法从正文唯一推出）。

**证据 B — Layer 1b 仍用法定人数提前截断，否定 E3 全席位 accounted**

```720:726:docs/MACAO_PRD_v2.md
    elif st == AgentState.WAITING_REVIEW:
        reviews = load_all_validated(...)
        if reviews.count_valid >= minimum_quorum(reviews.configured):
            return AgentState.CONSENSUS_CHECK
```

对照 §3.3 E3（L789）：「所有配置席位已响应……或已被持久化 timeout 纳入 accounted」。流程图 L90 仍写「达到法定人数或超时降级」。§16.2 阶段 4 仍写「有效票 ≥ 法定人数（E3）」。Kimi P1-1 申请声称已在 PRD §3.3 与 UC-5 闭环；识别伪代码未改，则编码仍会提前计票。

**证据 C — 场景推演三仍禁止 DEADLOCK 落盘，并回写终局 `vote_result`**

```854:859:docs/MACAO_PRD_v2.md
| 5 | … **不写 `vote_result.json`**，`CONSENSUS_CHECK` HOLD | …
| 6a | … 裁定落盘终局 vote_result（decision=APPROVED, resolution=human_override）→ `MERGING`（E4） |
```

对照同一张表 E3 伴随动作（L789）：「若算出 Deadlock，即时落盘不可变 `vote_result.json`（`decision: DEADLOCK`）」。L862 还要求「步骤 5 期间没有任何 `vote_result.json` 处于可被读走状态」。这是 D-1 的正反命题写在同一节。

**推演（GUIDELINES §6：1:1 僵局）**

1. N=2，1 YES + 1 NO → E3 进入 `CONSENSUS_CHECK`。
2. 实现者若信 E3：写 `decision: DEADLOCK` 的不可变文件。
3. 实现者若信场景三：不写文件，等 E7 再写 `decision: APPROVED, resolution: human_override`。
4. 实现者若信 Layer 1c：一旦盘上有 `APPROVED` 就进 `MERGING`，哪怕仍有 BLOCKING issue、尚未 disposition。

**不可唯一推出**：DEADLOCK 时磁盘有没有 `vote_result.json`；E7 改的是 override 还是 `vote_result.decision`；`APPROVED`+issue 是停在 `CONSENSUS_CHECK` 还是直接 `MERGING`。

**验收（须同时成立）**

1. §3.2 Layer 1b = 全席位 accounted（与 E3 同一谓词）；删除或改写 `minimum_quorum` 提前返回。
2. §3.2 Layer 1c：`DEADLOCK` → HOLD；`APPROVED` 且 `requires_disposition` → 不转移，等 FINAL disposition；有 FINAL 后按布尔走 E4 或 E5a；E7 只读 `admin_override.json`，不把 `RETRY_REVIEW`/`CANCELLED` 写入 `vote_result.decision`。
3. §3.4 场景三步骤 5–6 改为：即时落盘 `DEADLOCK`；E7 生成 `admin_override.json`；有 issue 时 E4 仍要 FINAL disposition（或条文写死管理员代签替代 FINAL 的写者与路径）。
4. 删除 L735「四分支含 RETRY_REVIEW | CANCELLED」及 L862「步骤 5 无 vote_result」类旧口径。

---

## 四、P1：进入下一阶段前应修正

### P1-1　`review_disposition` 契约三套字段，且未进入权威 PRD 产物章

v2.5 的核心新产物在权威 PRD **没有** §2.x 信封示例（仅生命周期表出现文件名 `executor.disposition.yml`）。提案、UC-6、代码清单三套命名并存：

| 字段 | 提案 §4.3 | UC-6 / 清单 §2.1 |
|---|---|---|
| 状态 | `status: FINAL \| PENDING_ADMIN` | `disposition_status: DRAFT \| FINAL` |
| 列表 | `items[]` | `dispositions[]` |
| 逐项决定 | `decision` | `disposition_type` |
| 理由 | `reason_ref` | `rationale` |
| 修订 | `artifact_revision` | 无（清单另用 DRAFT） |

提案 D-4/D-5 与 `PENDING_ADMIN`/`NEEDS_ADMIN` 依赖 `status` 与 `artifact_revision` 不原地修改。UC-6 示例无 `PENDING_ADMIN`，用 `DRAFT` 代替，E4 守卫无法区分「未完成草稿」与「等管理员」。GUIDELINES §5：禁止同一实体多套字段名。

**验收**：在 PRD §2 增加唯一信封；UC-6、清单、未来 Schema 逐字段同名；废止 `DRAFT` 或把它定义为不得触发 E4/E5a 的非消费状态并写进转移表。

### P1-2　申请列出的「已同步」文档未改到与 PRD 同向

| 交付物 | 申请声明 | 实际 |
|---|---|---|
| `PRODUCT-FACTS.md` F-20 | 「22 条完整作为设计约束」；提案 §9.2「F-20 解析为独立 disposition，全集 ACCEPTED-FOR-V2.5-SPEC」 | F-20 仍写「同一文件分区还是独立产物必须由后续规范显式裁定」 |
| `FAQ.md` Q12 | 「更新 Q11/Q12/Q14/Q15」 | Q12 `CONSENSUS_CHECK` 仍为「等计票结果 / 僵局问管理员」，无 `SHOULD_DISPOSE` |
| `FAQ.md` Q13 | 与 Q15 写者边界一致 | Q13 仍「执行者**汇总**问题清单……详见 Q15」 |
| PRD §6.1 | 「定义 `timeouts.review_disposition`（默认 30m）」 | `HUMAN_OVERRIDE_TRIGGERS` 六条仍无 disposition 超时、无 `NEEDS_ADMIN`、options 无 `EXTEND` |
| `UC7-human-override.md` | 提案 §9.2 要求 E7 关联 D-1 | 全文仍为 PRD v2.4：DEADLOCK 期间**不存在** vote_result；裁定**产生终局** `resolution: human_override`；options 无 `EXTEND`；无 `exempt_issue_ids` |
| `STATUS.md` | 「完整记录评审履历」 | 文首当前申请仍是 Phase3 L4；L33 历史定级仍写 PRD v2.3.1；L67 误报 grok 批准 |

GUIDELINES §3.3：L1 要求 DOC 交叉引用不矛盾。申请把 FAQ / PRODUCT-FACTS / STATUS 列入待审交付物，这些文件就是本轮边界，不是「可稍后打扫的周边」。

**验收**：F-20 改为已裁定独立产物（或显式 SUPERSEDED 指针）；Q12 与 PRD §14.2 同行；§6.1 增加 disposition 超时与 `NEEDS_ADMIN`；UC-7 按 D-1 重写；STATUS 更正 grok 票型并把当前对象改为本申请。

### P1-3　AEP/1.1「8 种消息」声明与示例/字母编号不一致

- L372：共定义 **8 种**，第 5 类为 `DISPOSITION_REQUIRED`。
- L390–392：紧接着写「全部 **7** 个消息类型」「适用于全部 **7** 类消息」。
- Type A–G 示例存在；**没有** `DISPOSITION_REQUIRED` 的 JSON 示例。
- E3 伴随动作称 `HUMAN_OVERRIDE_REQUEST` 为 **Type H**（L789）；§2.4 与场景三称为 **Type G**（L627、L855）。
- 全部示例 `"protocol": "AEP/1.0"`。
- Type G `options`（L642）无 `EXTEND`，与 E7 五选项不一致。

GUIDELINES §4：「AEP 定义 N 种消息」必须与实际详细 Schema 数量一致。第 8 类是 v2.5 调度主通道，不能只出现在表头。

**验收**：正文「8 类」与 8 个示例（含 `DISPOSITION_REQUIRED` payload）一致；Type 字母唯一；`protocol` 与版本策略写死（1.1 或兼容规则）；options 与 E7 同一枚举。

### P1-4　代码变更清单不能作为实施准入图

申请要求批准按 [`docs/v2.5_CODE_CHANGE_INVENTORY.md`](../v2.5_CODE_CHANGE_INVENTORY.md) 进入 Phase 1～5。清单把下列路径标为「变更」，仓库中不存在对应模块：

| 清单路径 | 仓库实情 |
|---|---|
| `src/macao/workflow/state.py` | 现有 `fsm.py` / `state_engine.py` |
| `src/macao/workflow/override.py` | 无此文件；override 在 `orchestrator.py` / CLI |
| `src/macao/git/evidence.py`、`git/merge.py` | 无 `git/` 包；合并在 `src/macao/merge/controller.py` |
| `src/macao/cli/commands/*.py` | 现有 `cli/main.py`，无 `commands/` 包 |

另：清单 Schema 使用 UC-6 字段名（P1-1）；`vote_result.schema.json` 现行 `decision` 枚举仍为 `APPROVED | REWORK_REQUIRED | RETRY_REVIEW | CANCELLED`、无 `DEADLOCK`——与 D-1 冲突，清单写「重构」但未把「删除 RETRY_REVIEW/CANCELLED 作为机器 decision」列为破坏性变更。把这份清单当编码地图会平行长出第二套目录，并复现 P0-1。

**验收**：清单每个「变更」行指向现存文件或明确标「新建」；字段名与 PRD 唯一信封一致；写明 `vote_result.decision` 与 `admin_override` 的迁移。

---

## 五、P2 / P3（不单独否决 L1，但回写时必须处理）

| ID | 级 | 问题 |
|---|---|---|
| P2-1 | P2 | PRD 文首把 `EXECUTIVE_SUMMARY.md` 标为「v2.5 执行摘要」；该文件 L3 仍写权威基准「现版本 v2.3」，产物表无 disposition。`IMPROVEMENT_SUMMARY.md` 标题仍为 v2.0→v2.3。 |
| P2-2 | P2 | `.review.yml` 同时保留 `opinion.status`（`APPROVED \| CHANGES_REQUESTED \| …`）与顶层 `vote`（`YES_APPROVE \| …`）。条件互锁只绑 `vote`↔`items`，未定义 `status` 与 `vote` 冲突时谁胜。现行 fixture 有 `review_status_vote_conflict.yml`，v2.5 未交代是否废止 `status`。 |
| P2-3 | P2 | UC-1 L80 仍允许采纳清单写在「下轮 `.dev.yml` 或 `adoption.yml`」；L318 遗留决策点 ⑤ 仍建议 `adoption.yml`。与 D-2 唯一 disposition 并存。 |
| P2-4 | P2 | UC-8 L39「本轮全部产物……并随 git 提交」；UC-9 L36「弃权随终局 vote_result 落盘」——提案 §9.2 声称 UC-2～UC-10 已清理 source 提交与旧 DEADLOCK 口径，未完成。 |
| P2-5 | P2 | UC-5 文首仍关联「PRD v2.4」；P2 前置条件仍写「有效票 ≥ `minimum_quorum`」，与同文件 E2「席位尚未全部 accounted 不进 CONSENSUS_CHECK」打架。 |
| P2-6 | P2 | E5 伴随「本轮产物归档」发生在 disposition 写入之前；E6 又要求前一轮 FINAL disposition。REWORK 路径上 staging 文件是否已归档、Executor 往哪写，未唯一规定（上轮 grok P2-1 同类）。 |
| P2-7 | P2 | 提案 §7.2 对 YYN 的解释写「赞成权重 3 ≥ ⌈8/3⌉=3」，把权重 quorum 公式误用到胜方权重；结果碰巧正确，公式叙述应改为 `3×3≥2×4`。 |
| P3-1 | P3 | 示例日期混用 2024-01-15 与 2026-09-01；不影响语义。 |
| P3-2 | P3 | 显式 `ABSTAIN` 强制 `items=[]`（上轮 P3-2），仍可接受，登记即可。 |

---

## 六、交叉文档需做的文字修订（最小闭环）

1. **只改 PRD 不够**：必须让 §3.2 伪代码、§3.4 场景三、§6.1 触发器、§2.4 示例与 §3.3 成为同一张表的三个投影。
2. **唯一 disposition 信封**写入 PRD §2，然后回写 UC-6、清单、FAQ Q13/Q15。
3. **F-20** 结案或显式「已被 D-2 取代」。
4. **UC-7** 按 D-1 重写，否则计票（UC-5）与接管（UC-7）继续双真源。
5. **清单**对齐现存模块树。
6. **STATUS** 更正票型与当前申请对象。

不要在未改 Layer 1c 的情况下声称「状态机无歧义转移分支」。

---

## 七、建议闭环顺序与验收标准

1. 修复 P0-1（识别入口 + 场景三 + E3 谓词三处同构）。验收：按 GUIDELINES §6 手工推演「1:1 僵局」「APPROVED+ADVISORY 未处置」「处置超时后 E7 APPROVED」三条，每步只能命中 §3.3 一行。
2. 修复 P1-1（PRD 信封为唯一真源）。验收：`grep -n disposition_status\|disposition_type\|PENDING_ADMIN\|artifact_revision` 在 PRD/UC-6/清单中同名同枚举。
3. 修复 P1-2（F-20、Q12、§6.1、UC-7、STATUS）。验收：申请 §3 每一行能指到 PRD/UC 行号，且无反向句子。
4. 修复 P1-3、P1-4。验收：8 类 AEP 均有合法 JSON；清单路径 `test -f` 或标明新建。
5. 以上闭合后再评 **L1 DOC-ALIGNED / PG-0**。期间现行实现与 v2.3.1 行为不变；不得把本 commit 的 PRD 标题「v2.5」当作已准入。

**不建议**：以 STATUS「100% 物理闭环」或提案 DRAFT v0.3 文首「完备闭环」代替正文核验；不建议在 Layer 1c 仍直跳 `MERGING` 时开始 Schema/计票编码。

---

## 八、机器票与处置建议

| issue_id | severity | disposition_class | 摘要 |
|---|---|---|---|
| `grok/P0-1` | critical | `BLOCKING` | PRD Layer 1c / 场景三 / Layer 1b 与 §3.3、D-1、E4/E5a 互斥 |
| `grok/P1-1` | major | `BLOCKING` | disposition 契约三套字段且未进 PRD §2 |
| `grok/P1-2` | major | `BLOCKING` | F-20 / FAQ Q12 / §6.1 / UC-7 / STATUS 未按申请同步 |
| `grok/P1-3` | major | `BLOCKING` | AEP 8 vs 7、Type G/H、缺 `DISPOSITION_REQUIRED` 示例 |
| `grok/P1-4` | major | `BLOCKING` | 实施清单路径与仓库不符 |

`vote`: `NO_APPROVE`  
`requires_new_checkpoint`（若本轮走 disposition）：**文档修订，不要求业务代码 checkpoint**。
