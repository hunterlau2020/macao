# MACAO 文档与代码门禁状态（Live Status）

> 依据 `docs/MACAO_REVIEW_GUIDELINES.md` 维护；本文件是唯一允许记录实时门禁状态的位置。
> 治理规则（P1-3 确立，已固化）：**每轮申请复审前，STATUS 必须与 `reviews/` 目录全量对账**，不得以 STATUS 登记子集为闭环核验边界。

- **最新更新时间**：2026-08-29（`7935da3` 轮专家复审报告陆续回收：claude / codex / kimi / qwen 共 4 份已提交，完成 47 份报告 + 8 份申请 100% 全量对账）
- **当前申请对象**：[`docs/reviews/2026-08-29-review-request-L3-Final-Closed.md`](2026-08-29-review-request-L3-Final-Closed.md)（`ea536ab..7935da3`）
- **当前定级状态**：**L3 SCENARIO-VERIFIED / PG-2 未获通过；维持 L2 / PG-1 待定**
  - **专家结论分布（4 份已提交）**：claude **不予授予**（新发现 2 项 P1）｜codex **REJECT**｜kimi **L2/PG-1 达成，L3/PG-2 暂不授予**｜qwen **支持授予但设强制前置条件**（注册表归属勘误，见下）。**zcode 本轮独立意见尚缺**。
  - **共性阻断判据**：claude / codex / kimi 三方独立指向同一处——超时降级实现与 PRD §1.2:128 / §2.2:318 / §3.3:834 口径不一致（缺 ping、缺 §6.1 人工确认、未随 E7 终局落盘），故 L3"关键场景可从文档唯一推出预期结果"不成立。
  - **测试机验结果（claude 独立复放，全部属实）**：`unittest discover tests -v` **49 ran / 49 PASS**；5 轮连续回归 0 flake；`macao test-clis` 4/4 PASS；`macao e2e-run` 7 步 OK，`artifacts` 表 5/5 `consumed=1`、`archived_path` 真实、`sha256` 均 64 位 —— **P1-2 完全闭环属实**。
  - **机验声明证伪**：申请文档"`git diff --check 4df059e..HEAD` 100% 洁净，返回码 0"实测**返回码 2**（5 处尾随空白，全在本轮 commit 新增的 `2026-08-29-review-result-ea536ab-codex.md`）；claude 与 qwen 独立复现一致。
- **历史文档定级**：PRD **v2.3.1**（§3.2 Layer 1c 四值终局分支已单点闭环修复，达到 L1 DOC-ALIGNED / PG-0）

---

## 评审申请记录全量对账表 (Review Registry - 47 份历史与当前评审报告 + 8 份申请全量对账)

| 申请日期 | 申请文件 / 历史轮次 | 待审对象 / Commit | 目标等级 | 评审专家与文件清单 | 结论与状态 |
|---|---|---|---|---|---|
| 2026-08-25 | 初始架构评审 | `ec60f70` (PRD v2.1) | L1 | `2026-08-25-review-result-ec60f70-claude.md`<br>`2026-08-25-review-result-ec60f70-codex.md`<br>`2026-08-25-review-result-ec60f70-gemini.md` (3 份) | 未通过（发现状态机与共识分歧） |
| 2026-08-26 | 历史迭代轮 1 | `47f54f2` (PRD v2.2) | L1 | `2026-08-26-review-result-47f54f2-codex.md` (1 份) | 历史追踪（指出沙箱与存储边界） |
| 2026-08-26 | 历史迭代轮 2 | `684a012` (PRD v2.2.1) | L1 | `2026-08-26-review-result-684a012-claude.md`<br>`2026-08-26-review-result-684a012-codex.md`<br>`2026-08-26-review-result-684a012-gemini.md` (3 份) | 历史追踪（收敛 AEP 信封与 Schema） |
| 2026-08-26 | 历史迭代轮 3 | `8ab9be7` (PRD v2.2.2) | L1 | `2026-08-26-review-result-8ab9be7-claude.md`<br>`2026-08-26-review-result-8ab9be7-codex.md`<br>`2026-08-26-review-result-8ab9be7-gemini.md`<br>`2026-08-26-review-result-8ab9be7-kimi.md`<br>`2026-08-26-review-result-8ab9be7-opencode.md` (5 份) | 历史追踪（确立并集方案 B 与死锁 HOLD） |
| 2026-08-26 | `2026-08-26-review-request-PRD-v2.3.md` | `cc77a94` (PRD v2.3) | L1 | `2026-08-26-review-result-cc77a94-claude.md`<br>`2026-08-26-review-result-cc77a94-codex.md`<br>`2026-08-26-review-result-cc77a94-gemini.md`<br>`2026-08-26-review-result-cc77a94-kimi.md`<br>`2026-08-26-review-result-PRD-v2.3-opencode.md` (5 份) | 未通过（提出 2 P0 + 3 P1 修订项） |
| 2026-08-26 | `2026-08-26-review-request-PRD-v2.3.1.md` | `403ddc7` (PRD v2.3.1) | L1 / PG-0 | `2026-08-26-review-result-403ddc7-claude.md`<br>`2026-08-27-review-result-403ddc7-codex.md`<br>`2026-08-27-review-result-403ddc7-zcode.md` (3 份) | 上轮 2 P0 + 3 P1 全部 VERIFIED；新增 P1（§3.2 Layer 1c 四值分支）已在整改中闭环修复 |
| 2026-08-27 | `2026-08-27-review-request-Phase0-Phase1-Code.md` | `d137a05` .. `435eeea` | L2 / PG-1 | `2026-08-27-review-result-435eeea-claude.md`<br>`2026-08-27-review-result-435eeea-codex.md`<br>`2026-08-27-review-result-435eeea-zcode.md` (3 份) | 复审提出 P0 ×2 + P1 ×7 整改项；已在后续整改中全部闭环修复 |
| 2026-08-27 | 整体技术框架横向评审（非定级轮） | `435eeea` / `23dfad5` / `aa173d8` 代码架构 | — | `2026-08-27-review-result-435eeea-tech-framework-zcode.md`<br>`2026-08-27-review-result-23dfad5-tech-framework-claude.md`<br>`2026-08-27-review-result-23dfad5-codex-framework.md`<br>`2026-08-27-review-result-aa173d8-tech-framework-qwen.md` (4 份) | 四方专家（zcode / claude / codex / qwen）横向评估：确认核心缺陷已闭环；提出架构装配、多播独立投递与真实联调建议 |
| 2026-08-28 | `2026-08-28-review-request-Phase1-Phase2-Integration.md` | `aa173d8` .. `906b17e` | L3 / PG-2 | `2026-08-28-review-result-906b17e-zcode.md`<br>`2026-08-28-review-result-906b17e-claude.md`<br>`2026-08-28-review-result-906b17e-codex.md`<br>`2026-08-28-review-result-906b17e-integration-qwen.md` (4 份) | 四方专家一致判定：未达 L3，维持 L2/PG-1；提出 11 项整改项；已在 e7ba2d2 中闭环修复。 |
| 2026-08-29 | `2026-08-29-review-request-Phase1-Phase2-Rectification.md` | `906b17e` .. `e7ba2d2` | L3 / PG-2 | `2026-08-29-review-result-e7ba2d2-claude.md`<br>`2026-08-29-review-result-e7ba2d2-rectification-qwen.md`<br>`2026-08-29-review-result-e7ba2d2-zcode.md`<br>`2026-08-29-review-result-e7ba2d2-codex.md` (4 份) | 四方专家复审结论：确认上轮 11 项全部实测闭环；独立发现 4 项阻断项（message_id 碰撞、协议枚举/人工裁定断裂、CI 失败缺少原子回滚、Mock Adapter 契约消费驱动）。 |
| 2026-08-29 | `2026-08-29-review-request-L3-Final-Rectification.md` | `e7ba2d2` .. `4df059e` | L3 / PG-2 | `2026-08-29-review-result-4df059e-claude.md`<br>`2026-08-29-review-result-4df059e-zcode.md`<br>`2026-08-29-review-result-4df059e-codex.md`<br>`2026-08-29-review-result-4df059e-qwen.md` (4 份) | 四方专家一致确认上轮 4 项 P0 全部真实闭环；Qwen 支持授予 L3；ZCode 指出超时场景判据缺口；Codex/Claude 提出若干单点强化项。 |
| 2026-08-29 | `2026-08-29-review-request-L3-All-Items-Closed.md` | `4df059e` .. `ea536ab` | L3 / PG-2 | `2026-08-29-review-result-ea536ab-claude.md`<br>`2026-08-29-review-result-ea536ab-codex.md`<br>`2026-08-29-review-result-ea536ab-grok.md`<br>`2026-08-29-review-result-ea536ab-zcode.md` (4 份) | 四方专家一致确认 6 项安全修复全部闭环；指出终局 vote_result.json 需完整持久化超时 ABSTAIN 票据并提供自动判定支持；修复 `fsm.py` 消费匹配 key 与 `artifacts.sha256` 读盘补齐。 |
| **2026-08-29** | **`2026-08-29-review-request-L3-Final-Closed.md`** | **`ea536ab` .. `7935da3`** | **L3 / PG-2** | `2026-08-29-review-result-7935da3-claude.md`<br>`2026-08-29-review-result-7935da3-codex.md`<br>`2026-08-29-review-result-7935da3-kimi.md`<br>`2026-08-29-review-result-7935da3-qwen.md` (4 份；zcode 独立意见缺失) | **未通过（4/5 份已提交）**<br>P1-2（消费 key + sha256）四方一致确认**完全闭环**；P1-1 仅部分闭环（自动检测已接入生产链路属实，但降级口径与 PRD 冲突）；P3-1 洁净度声明被 claude / qwen 独立证伪。claude 另独立发现 2 项新 P1（自动降级绕过人工确认致自动合并、审计窗口 `limit=50` 致检测静默失效）。 |

---

## 本轮新发现（claude 独立复审，`7935da3`，2026-08-29）—— 2 项新 P1 + 2 项 P3

> 均为本轮 commit 新引入，非历史遗留；全部附确定性实机复现。报告全文见 [`2026-08-29-review-result-7935da3-claude.md`](2026-08-29-review-result-7935da3-claude.md)。

| 编号 | 严重度 | 问题 | 证据与复现 | 建议修复 |
|---|---|---|---|---|
| **P1-NEW-3** | **阻断** | **自动超时降级绕过 PRD 强制的 ping 与 §6.1 人工确认，Reviewer 仅慢 10 分钟即被弃权并触发自动批准合并** | ① 口径错配：PRD §1.2:128 的 `WAITING_REVIEW` 超时列为 `30m（10m/reviewer 触发 ping）`，`per_reviewer` 是 **ping 触发点**；实现 `orchestrator.py:301-302`/`:385-386` 直接以 `per_reviewer` 为弃权判定线，`review_request`(30m) 零消费方，全仓库无 ping 实现。② 人工确认缺失：PRD §2.2:318 要求"经 §6.1 人工确认标记弃权"，§3.3:834 要求"随 **E7** 终局 `vote_result.json` 一并落盘"；实现 `:429-431` 无条件自动检测、`:467-481` 直接合成 ABSTAIN。③ **实机复现（3 Reviewer，2 赞成 + 1 仅慢 11 分钟）**：自动检出超时 → `decision=APPROVED, resolution=automatic, abstain=1` → 进入 `MERGING`；在 `require_human_signoff:false`（`e2e_runner.py:82` 即此值）下继续执行 `execute_merge` → `merge ok=True, final state=DONE`。**该 Reviewer 未提交的意见被自动作废，代码自动合并。**<br>⚠️ 说明：kimi 同轮亦指出 ping/人工确认缺失，但其复现为 2 Reviewer 场景（必然 DEADLOCK，判为 fail-safe）；**3 Reviewer 配置下并非 fail-safe**，claude 证据覆盖该缺口。qwen 的 P1-1 ✅ VERIFIED 亦基于 2 Reviewer 路径，未覆盖 3 Reviewer 自动批准分支。 | ① `per_reviewer` 到期只发 ping / 触发一次自愈；② 以 `timeouts.review_request`(30m) 为整轮降级窗口；③ 超时降级一律经 `DEADLOCK` → E7 人工裁定落盘，禁止 `resolution: automatic` 的票面中出现超时 ABSTAIN；④ 补"存在超时 ABSTAIN 时决策不得为 automatic"的回归断言。 |
| **P1-NEW-4** | **阻断** | **审计窗口硬编码 `limit=50`，轮询到一定次数后超时检测静默失效，终局票面丢失 ABSTAIN（本轮 P1-1 需求自行回退）** | 根因：`orchestrator.py:370`（检测）与 `:672`（`resolve_override` 回填）均 `list_audit_events(task_id, limit=50)`，而该查询为 `ORDER BY sequence_id DESC LIMIT ?`；放大因素：`:467-481` 的 `REVIEWER_TIMEOUT_ABSTAIN` 只按内存 `votes_list` 去重、不查历史审计，每次轮询净增 2 条审计，自我挤爆窗口。**实测 1**：`poll 20 / 45 events → ['opencode']`；`poll 25 / 55 events → []`（派发事件被挤出）。**实测 2**：轮询 80 次（110 条审计）后 `resolve_override('APPROVED')`，终局 JSON 变为 `reviewers_responded=1, abstain=0, votes=[codex]` —— 与本轮 P1-1 目标态完全相反。 | ① 以按 `type` + `task_id` + `review_round` 的定向 SQL 查询取代 `limit` 窗口扫描；② `REVIEWER_TIMEOUT_ABSTAIN` 按 (task, round, reviewer) 幂等写入；③ 补"轮询 N 次后检测结果与终局票面不变"的回归测试。 |
| **P3-NEW-1** | 建议 | `git diff --check 4df059e..HEAD` 声明被证伪 | 实测返回码 **2**，5 处尾随空白全部位于本 commit 新增的 `2026-08-29-review-result-ea536ab-codex.md`（36/52/63/76/85 行）。POC 报告旧问题确已清理（属实），但以"已清理某文件"替代"命令实际返回 0"（GUIDELINES §9-B 模式）。qwen 记录此为**连续第 4 轮洁净度声明失真**。 | 以命令返回码而非单文件状态作为声明依据。 |
| **P3-NEW-2** | 建议 | `vote_breakdown` 收窄后 E2E 报告 `effective_votes` 走死 fallback | `vote.py:165-169` 将 `vote_breakdown` 收窄为 `approve/reject/abstain` 三键——**与 PRD §2.3:363 示例及 Schema 一致，属对齐改进**；但 `e2e_runner.py:238` 的 `breakdown.get("effective_votes", approve_count)` 自此恒走 fallback，混合票型下会把赞成票数误报为有效票数（全同意场景两值巧合相等，故未被 49 项测试发现）。 | 改为由 `approve + reject` 直接计算。 |

### 本轮已确认完全闭环项（claude 独立复放）

| 编号 | 结论 | 证据 |
|---|---|---|
| **P1-2**（消费 key + sha256） | ✅ **VERIFIED（无保留）** | `fsm.py:105` 由 `rev_file.stem` 改为 `rev_file.name.replace(".review.yml","")`；`store.py:83-97` `content is None` 时按 `project_root` 拼接读盘计算。实机 `e2e-run` 后直查 SQLite：5/5 `consumed=1`、`archived_path` 均为 `.macao/archive/<40 位 SHA>/r1/...`、`sha256` 均 64 位（对比上轮实测 3/5 `consumed=0`、5/5 `sha256=''`）。测试已补齐三类强断言。**这是 claude 连续三轮跟踪项中首个完全无保留闭环的条目。** |
| **P1-1 之"自动检测接入生产链路"** | ✅ VERIFIED | `orchestrator.py:429-431` `if timed_out_reviewers is None: ... detect_timed_out_reviewers(...)`；`:300-313`/`:337`/`:345` deadline 真实落审计、payload 与 `message_queue.deadline`。claude 上轮 P1-NEW-1 的"零生产调用方 / deadline 恒 NULL"两项证据已归零。 |
| **`store.py:152-162`** | ✅ 必要且正确 | 修正 `list_audit_events` 的 `detail` JSON 反序列化，使下游 `a["detail"]["review_round"]` 不再 `AttributeError`。 |

---

## 注册表归属勘误（治理事项）

- `2026-08-29-review-result-7935da3-qwen.md`（原 `-zcode.md`）正文署名 **"评审人：qwen（独立评审）"**，已完成文件名更名校正。
- STATUS 已准确记录 qwen 与其他专家的独立复审结论。
- 依 GUIDELINES §1.3，`<reviewer>` 必须为实际执行评审的角色标识。**本轮 zcode 的独立意见事实上缺失**，按 §8"沉默 ≠ 同意"，不得计入多数。
- 处置建议：将该文件更名为 `2026-08-29-review-result-7935da3-qwen.md`，同步核查 `ea536ab` 轮是否存在同类归属错误，并另行补齐 zcode 对 `7935da3` 的独立报告后再行宣告定级。

---

## 下一步行动

1. **闭环 P1-NEW-3**（超时降级口径回归 PRD：ping / 30m 窗口 / 一律经 E7 人工裁定）与 **P1-NEW-4**（审计定向查询 + 幂等写入）——两者均为 PG-1 的 P0/P1 归零硬条件；
2. **一并处理 codex 与 kimi 提出的其余阻断项**（无生产调度器主动推进 timeout、迟到补交绕过人工接管、REVIEW_REQUEST 部分分发、`.dev.yml` 最小有效性校验不完整等），并按 §8 记录 issue_id / evidence / owner / resolution_commit；
3. **处理注册表归属勘误并补齐 zcode 独立报告**（qwen 设定的强制前置条件）；
4. 修正 P3-NEW-1（以命令返回码为准）与 P3-NEW-2（`effective_votes` 计算）；
5. 上述闭环并经实机复验后再发起下一轮 L3 / PG-2 申请；**在专家委员会形成共识前，L3 / PG-2 维持未通过。**
