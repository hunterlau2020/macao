# MACAO 最新文档评审结论（PRD v2.2，独立复核）

- 评审日期：2026-08-26
- 被评审 commit：`8ab9be7`
- 评审范围：`docs/MACAO_PRD_v2.md`（v2.2）、`docs/schemas/`、`EXECUTIVE_SUMMARY.md`、`IMPROVEMENT_SUMMARY.md`、`docs/reviews/STATUS.md`
- 定位：本轮不重复已被 `2026-08-26-review-result-8ab9be7-codex.md` 覆盖的分析过程，而是先验证其结论，再补充其未覆盖的角度。
- 结论：**同意 codex 本轮的 PARTIALLY_VERIFIED / 未达 L1 判定，并追加 1 个新 P0**——`vote_result.json` 的 `decision` 枚举与 Layer 1c 状态识别代码无法安全表达"Consensus Deadlock"这一决策表明确定义的结果，存在把死锁静默误判为返工、或使统一转移表失去自证的"穷尽性"的风险。

## 一、对 codex 本轮结论的独立验证

逐条核对 `2026-08-26-review-result-8ab9be7-codex.md` 的证据行号，结果：**全部属实，予以采纳**。

| codex 编号 | 复核结果 | 核对方式 |
|---|---|---|
| P0-1（clean rebase 改变被合并 commit，却不触发复审） | **确认** | 读 `MACAO_PRD_v2.md:1459` 原文："rebase 仅改变 commit 哈希、不触发新一轮评审"；与 §3.2/§3.3 "checkpoint_ref + review_round 双匹配"的作用域读取原则（评审对象=合并对象）直接冲突。 |
| P0-2（worktree 强制性被架构图/示例削弱） | **确认** | 读 `MACAO_PRD_v2.md:493-496`（`REVIEW_REQUEST` 示例仍用 `~/work/macao-demo` 主工作区路径）与 `MACAO_PRD_v2.md:1554`（§16.3 表格写"隔离：**可选** git worktree"），与 §12.2 "MVP 阶段强制 sandboxed + 独立 worktree" 矛盾。 |
| P1-1（`review_manifest.schema.json` 无法表达 ABSTAIN） | **确认** | 读 `docs/schemas/review_manifest.schema.json:22-30`：`opinion.status` 枚举仅 `APPROVED/CHANGES_REQUESTED/REJECTED`，无 `ABSTAIN` 选项，但顶层 `vote` 枚举含 `ABSTAIN`（第 31 行）——任何遵循 Schema 必填 `opinion.status` 的 Reviewer manifest 都无法合法产出弃权票。 |
| P1-2（AEP payload 非 type-specific，Task/Capability Schema 缺失） | **确认** | 读 `docs/schemas/aep_envelope.schema.json:29`：`"payload": {"type": "object"}`，未按 7 种 `type` 做 `oneOf` 判别。 |

未发现 codex 本轮证据有误判或引用行号偏移的情况。

## 二、新增 P0：`vote_result.json.decision` 无法表达 Consensus Deadlock

**证据链**：

1. `MACAO_PRD_v2.md:395`："其余一切情形（含 1:1、有效票低于法定人数、全弃权/全超时）→ Consensus Deadlock，触发人工接管"——决策表明确把 Deadlock 列为与 APPROVED / REWORK_REQUIRED 并列的第三种结果，且规定了触发方式。
2. `MACAO_PRD_v2.md:404-409` 决策表逐行给出 Deadlock 场景（1:1、1 弃权+1 票、全弃权/全超时、1:1:1）。
3. `docs/schemas/vote_result.schema.json:51`：`"decision": { "enum": ["APPROVED", "REWORK_REQUIRED"] }`——**枚举没有第三个值**，无法合法序列化 Deadlock 结果。
4. `MACAO_PRD_v2.md:743-751`（Layer 1c 状态识别伪代码）：
   ```python
   result = load_and_validate('.macao/vote_result.json', VOTE_RESULT_SCHEMA, ...)
   if result.valid:
       archive_round_artifacts(ref, rnd)
       return (AgentState.DONE if result.decision == 'APPROVED'
               else AgentState.REWORK)
   ```
   这是**二元分支**：只要 `result.decision` 不等于 `'APPROVED'`，一律判为 `REWORK`。如果 Deadlock 场景仍然写出了 `vote_result.json`（哪怕字段留空或塞入非法值导致 schema 校验失败），"不是 APPROVED" 会被直接当作 REWORK 处理，**而不会触发 §6.1 的人工接管**——这与决策表"Deadlock 必须转人工裁定，不得自动判定"的规则正面冲突。
5. 若换一种读法——Deadlock 场景 Orchestrator 根本不写 `vote_result.json`，而是绕过状态识别代码、直接调用人工接管——那么问题转移到统一转移表本身：`MACAO_PRD_v2.md:~801` 明确声明"除本表所列来源外，任何实现不得引入其他状态转移路径"，但表中唯一提到 Deadlock 的 `E7` 行（`MACAO_PRD_v2.md:800`）触发条件是"**命令**"类型（即人工已经做出裁定之后的落地转移），并不是"检测到 Deadlock 时"的入口转移。换言之，"票已收齐、判定为 Deadlock、需要向用户提问"这一时刻本身，在 E1–E8 中找不到对应的产物/命令/超时来源——唯一可能兜底的是 E8 的"60 分钟无进展"通用诊断，但这与 §6.1 给 Consensus deadlock 单独标注的"10 分钟"超时（`MACAO_PRD_v2.md:1058-1062`）不一致，且把"票已收齐但结果有争议"降级成了"长时间无进展"的模糊诊断，丢失了本可以立即、确定性触发的信号。

**两种读法都指向同一个洞**：Deadlock 是决策表里被反复强调、需要"立即转人工"的一等结果，但它既没有在机器可校验的 `vote_result.json` Schema 中获得合法表达，也没有在自称穷尽的统一转移表中获得独立的入口边。这不是文字措辞问题，而是"两票选民 1:1 打平"这个 MVP 阶段（2 Reviewer）**必然会遇到的常见场景**缺少可靠的自动化路径——考虑到 MVP 明确是 2-Reviewer 配置，1:1 平票并非边角案例，而是高频路径。

**建议**（二选一，写入 Schema 与转移表）：
- 方案 A：`decision` 枚举增加 `"DEADLOCK"`，Layer 1c 伪代码改为三分支（`APPROVED→DONE` / `REWORK_REQUIRED→REWORK` / `DEADLOCK→UNKNOWN`+`trigger_human_override`），并在统一转移表新增一条产物触发的边（如 `E3a`：`CONSENSUS_CHECK` + 产物 + `decision == DEADLOCK` → `UNKNOWN`，触发 HUMAN_OVERRIDE，超时沿用 §6.1 的 10 分钟）。
- 方案 B：明确 Deadlock 时不写 `vote_result.json`，改为直接发送 `HUMAN_OVERRIDE_REQUEST`（Type G）作为唯一信号源；此时需要在统一转移表补一条独立的"命令/信号"触发边（而非依附于 E7 的事后落地），并在 §2.3 决策表旁注明"Deadlock 不产生 `vote_result.json`"，避免读者（包括 Adapter 实现者）默认三种决策结果都会落盘。

无论哪种方案，都应在 §3.4 的场景推演中补一条"两票 1:1 → Deadlock → 人工裁定"的完整推演（当前两个推演场景只覆盖 APPROVED 首次通过与 REWORK 返工，均未覆盖 Deadlock），并为 `docs/schemas/fixtures/` 补一个 Deadlock 相关的 fixture。

## 三、补充的 P2/P3（次要，登记即可）

| 编号 | 发现 | 证据 | 建议 |
|---|---|---|---|
| N1 | `macao merge approve` 是默认配置（`require_human_signoff: true`）下**正常路径**的必经命令，但未出现在 §14.2 日常运维命令表 | `MACAO_PRD_v2.md:1462`（引用该命令）vs `MACAO_PRD_v2.md:1437-1443`（命令表未列出） | 补入命令表，说明其语义与 `override resolve` 的区别（前者是常规签字，后者是异常接管） |
| N2 | §14.1 主旅程第 6 步指向"见 14.6 Merge Policy"，但 Merge Policy 实际章节号是 §14.5 | `MACAO_PRD_v2.md:1432` vs 实际标题 `MACAO_PRD_v2.md:1455`（`### 14.5 Merge Policy`） | 修正为 "见 14.5" |
| N3 | §16.3 用"其余全自动"描述单机场景用户体感，但默认配置下每次成功合并都需要用户执行 `macao merge approve` 才能推送——这是常规路径的强制人工步骤，不是"接管/例外" | `MACAO_PRD_v2.md:1556`（"override resolve 处理接管，其余全自动"）vs `MACAO_PRD_v2.md:1462`（默认 `require_human_signoff: true`，推送前必须人工签字） | 措辞改为"status 看进度、override resolve 处理接管、merge approve 完成签字放行，其余自动"，避免读者误以为默认配置下合并会无人值守直接推送 |

## 四、与本轮已闭环项的关系

STATUS.md 记录的 F1/F2（我上一轮报告的两个 P0）与 codex 上一轮 P1-1~P1-5，本次逐条比对文本，确认修订**均已在 v2.2 落地且方向正确**（`MERGING` 中间态、`execution_mode` 强制规则、State Store DDL/恢复算法、`docs/schemas/` 均可在当前文本找到对应内容），未发现"声称已修但实际未改"的情况。新发现的 Deadlock 决策表达缺口与 codex 本轮的 P0-1/P0-2 属于同一类问题模式——**"正文承诺的安全/仲裁规则，未同步落到机器可校验的 Schema 或转移表里"**——建议本轮修订时一并处理，避免下一轮复审再次逐个发现。

## 五、建议的闭环顺序（叠加 codex 本轮清单）

1. codex P0-1（rebase 一致性）、P0-2（worktree 强制化）——已有明确建议，优先级最高；
2. 本报告新增 P0（Deadlock 决策表达）——建议与 P0-1/P0-2 同批处理，三者都是"决策/状态语义 vs Schema/转移表"一致性问题，适合一次性做完整性审计而非逐个打补丁；
3. codex P1-1～P1-4（ABSTAIN 表达、AEP type-specific payload、artifacts 主键、审计保留策略）；
4. 本报告 N1～N3（命令表补全、章节号勘误、"全自动"措辞）可随下一轮顺带修正。

## Reviewer 自审记录

本轮方法：先做"结论复用"（逐条核对 codex 证据行号是否仍然成立，而非重新独立发现同一批问题），再针对"决策语义是否在所有涉及的 Schema/伪代码/转移表中保持三态一致"做定向复核——这是上两轮我自己和 codex 都未系统检查过的角度（此前的检查集中在字段路径漂移和产物覆盖时序，而非决策枚举的穷尽性）。未验证真实代码、CLI 行为或 SQLite 恢复过程；结论仅覆盖文档、Schema 与 fixture 级证据。
