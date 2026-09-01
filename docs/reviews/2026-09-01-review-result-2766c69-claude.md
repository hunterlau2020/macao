# MACAO PRD v2.5 全文档体系终局定级复核 评审结论

- **评审日期**：2026-09-01
- **评审人**：`claude`
- **评审对象**：[`docs/reviews/2026-09-01-review-request-PRD-v2.5-Design-Sync.md`](2026-09-01-review-request-PRD-v2.5-Design-Sync.md)（已于本轮重写）
- **对应 commit**：`2766c69`（`docs: close all 5 expert reviews on 0bc6247, align PRD v2.5 schemas and FSM guards`），工作区 clean
- **上一轮对象**：`0bc6247`（本人结论：`NO_APPROVE`，P0 × 2 + P1 × 8）
- **评审基准**：`docs/MACAO_REVIEW_GUIDELINES.md` v1.0 §1–§6、§9、§11
- **事实锚点**：`docs/usercases/PRODUCT-FACTS.md` F-1～F-22
- **申请定级**：L1 DOC-ALIGNED / PG-0
- **机器票**：`NO_APPROVE`
- **结构化 issue**：`BLOCKING` × 2（P1），`ADVISORY` × 12（P2 × 8 / P3 × 4）

---

## 结论

**本轮整改是真实、可验证、大幅度的。我上轮提出的 10 项阻断（P0 × 2、P1 × 8）经独立机验，全部 10 项实质闭环**——不是自述闭环，是我用能证伪它们的测试重跑后闭环。此外 P2 × 7、P3 × 3 亦一并关闭。这是本项目迄今整改质量最高的一轮。

**但仍不能授予 L1 DOC-ALIGNED / PG-0**，原因只有两条，且都很窄：

1. **本次整改把 §2.3 加权五重门禁公式改坏了**（新引入的回归）：`\forall` / `\times` / `\rceil` 被 shell 转义吞成了控制字符（FF/TAB/CR 共 9 个），全库仅此 4 行受损，而这 4 行正是 v2.5 唯一权威的共识判定公式。上一版 `0bc6247` 该处完好，故此为本 commit 引入。
2. **`vote_result.schema.json` 的 `decision` 枚举仍含 `RETRY_REVIEW` / `CANCELLED`**，而 §2.3 正文与 §3.2 状态机都只认三值。契约放行、状态机无分支——申请 §3 第 1 行声称「移除 RETRY_REVIEW/CANCELLED 机器决策」，正文确实移除了，**机器契约没有**。

两项合计约 6 行改动，无任何设计风险。按 `PRODUCT-FACTS` **F-17**（「要求合并前完成修复的『有条件通过』在机器语义上属于阻断性不通过，不能以 `YES_APPROVE` 绕过重新评审」），我不能投「有条件通过」——即便我认为这一轮离通过只差一步，机器票也必须是 `NO_APPROVE`。**建议按最小修订走一次快速复评，我预期届时可直接授予 L1/PG-0。**

---

## 0. Reviewer 自审记录（GUIDELINES §9）

### 0.1 我自己的测量错误与更正（本轮 2 次）

- **仪器失效，未当成证据**：我先把上轮报告里内嵌的 3 段脚本原样重跑，结果脚本 1、2 报 FAIL。**这不是被审对象的问题，是我的仪器过期**——那 3 段脚本用硬编码行偏移（`after=158/216/280`）定位代码块，并用我手抄的旧 §5.2 实例做输入；本轮 PRD 改动 1142 行，偏移全部失效，脚本读到了错误的代码块（报错形态是根级 `'executor' is a required property`，典型的抓错块特征）。我据此**作废了脚本 1、2 的本轮输出**，改写为按章节标题定位的提取器后重测，结论反转为全部 PASS。只有脚本 3（直接读 Schema、无偏移依赖）本轮结果有效。
- **PCRE 陷阱**：我第一次扫控制字符用了 `grep -cP '[\t\f\v]'`，得到「PRD 1587 行命中 / SRS 1131 行命中」这种几乎等于总行数的结果。原因是 PCRE 里 `\v` 是**竖向空白字符类**（含换行），不是垂直制表符，等于逐行匹配换行。该次测量作废，改用 Python 按字节值 `0x09/0x0b/0x0c/0x0d` 逐字节定位，得到真实结果：**全文档集共 9 个控制字符，全部集中在 PRD L332–335**。N-1 的范围结论以后者为准。

### 0.2 撤回上轮一项判定

上轮我在 §六 反例库把 GUIDELINES §6 第 5、6 条（「Reviewer 崩溃重启后重复提交投票」「同一 checkpoint 两份同 reviewer_id 的 `.review.yml`」）判为**不可唯一推出**，理由是全 PRD 的幂等去重只定义在 AEP `message_id` 层。本轮我去查了 `UC4-review-dispatch.md`，该文件**明确定义了产物层去重**：P4「无本轮该 `reviewer_id` 已消费票（去重前置）」、f4「去重取最新合法票」、A5「同 reviewer_id 两份同轮票 → f4 去重 + 审计，不双计」、E5「评审者进程崩溃重启后重复提交 → f4 去重幂等，崩溃前已消费票不重复计数」。

这些条文在上轮就已存在。我当时以「UC-4 不在申请交付物清单内」为由未纳入核验，但**可推导性的判据是文档体系整体，不是申请人圈定的清单**。因此上轮该判定**错误，予以撤回**：这两个场景是可唯一推出的。残留问题降级为 N-13（P3）：权威基准 PRD 正文未写产物层去重、也未给出指向 UC-4 的指针。

### 0.3 强制自检 5 项

| # | 检查项 | 本轮结果 |
|---|---|---|
| 1 | 字段名 vs 实际读取路径 | **VERIFIED**：§5.2 `code_changes.refs.*` = §5.3 `jq` 读取路径 = `review_context.schema.json` 三者同构（上轮 P0-2 已闭环）。残留 N-7（`signal` 的 `const` 使 UC-3 d2 不可达） |
| 2 | 每处「已完成」是否有证据 | PRD 21 个复选框仍全为 `[ ]` ✓；申请 §4 自述的 3 段脚本结果我逐条重放，**与自述一致，无夸大**；申请 §3 有一处半条不实（N-4） |
| 3 | 确定性用语是否标注 | §3.1 L686 等价条文保留「设计目标值，以 PoC 实测为准」✓；申请标题「100% 物理闭环」在我复核下**基本属实**（10/10 实质闭环），不再判为夸大 |
| 4 | 代码块是否真能解析 | YAML/JSON **全部 PASS**（见 §二）；**LaTeX 公式 FAIL**（N-1） |
| 5 | 每个 P1 是否给出可复现证据 | 是；两条 BLOCKING 均附可直接重跑的脚本（§五） |

### 0.4 连续漏审模式登记

上轮我登记过「行号引用漂移」并改为逐条 `sed -n` 回读。本轮进一步暴露的是**同一类问题的上游形态：把上一轮的验证脚本当成可跨 commit 复用的仪器**。已登记：跨轮复用的验证脚本必须按语义锚点（章节标题、Schema 键名）定位，禁止硬编码行偏移；重跑结果与预期不符时，**先证伪仪器，再证伪对象**。

---

## 一、上轮 10 项阻断的闭环核验（逐项独立机验）

| 上轮 issue | 本轮判定 | 决定性证据（我自己重跑/回读） |
|---|---|---|
| **P0-1** FSM 识别入口与场景推演残留 v2.3.1 | **VERIFIED（完全闭环）** | §3.2 Layer 1b（L751–756）改为 `accounted == configured`，`minimum_quorum` 提前 return 已删除；Layer 1c（L758–789）三分支齐备：`DEADLOCK`→HOLD、`APPROVED`+`requires_disposition`→读 FINAL disposition→按 `requires_new_checkpoint` 分流 E5a/E4、`REWORK_REQUIRED`→E5；`RETRY_REVIEW`/`CANCELLED` 分支已移除。§3.4 场景三 Step 5 改为「**即时落盘不可变 `vote_result.json`（`decision: DEADLOCK`）**」，Step 6a–6e 全部落盘独立 `admin_override.json`，并补齐 6e `EXTEND`。L862「步骤 5 期间无 vote_result」的反向断言已删除 |
| **P0-2** `review_context` 与其自称机器契约互斥 | **VERIFIED（主体闭环）** | §5.2 改为嵌套 `code_changes.refs.{base_commit, head_commit}`（L1001），§5.3 `jq` 读同一路径；`evidence`、`review_guidelines` 已进入 Schema `properties`。**实测：§5.2 实例 vs `review_context.schema.json` → PASS**（上轮 FAIL 7 项）。残留 N-6（块数与 `required` 强制面） |
| **P1-1** disposition 无 PRD 契约、4 套文件名 | **VERIFIED（完全闭环）** | 新增 **§2.5 `executor.disposition.yml`**（L634–683）：用途/位置/完整格式/三条守卫齐全，且**明确裁定了我上轮点出的 `DRAFT` vs `PENDING_ADMIN` 语义空洞**——规则 3「只有 `FINAL` 能触发 E4/E5a；`DRAFT` 或 `PENDING_ADMIN` 保持 HOLD」。文件名全库统一为 `executor.disposition.yml`（PRD 22 处 / FAQ 4 / UC 6 / SRS 2 / 清单 2，`review_disposition.yml` 零残留） |
| **P1-2** AEP 声明 8 类实给 7 类等 6 项 | **VERIFIED（完全闭环）** | 8 类 Type A–H 齐备，**Type E `DISPOSITION_REQUIRED` 完整 JSON 示例已补**（L535–563，payload 含 `vote_result` 三元组引用 + `issues_index_sha256` + `deadline` + `expected_output`）；8 处 `"protocol"` **全部为 `AEP/1.1`**；**`grep -c base64` = 0**（Type B/C/F 三处内联全部改为 `{path, evidence_commit, sha256}`）；Type G/H 编号冲突消除（HUMAN_OVERRIDE_REQUEST 现统一为 Type H）；Type H `options` 含 `EXTEND` 与 `exempt_issue_ids`；16 KiB / 2048 字节预算条文在位（L360） |
| **P1-3** §13 `macao.yaml` 单一事实源未升级 | **VERIFIED（8/8 补齐）** | `vote_weight`（L1356–1358）、`dictator_cap_enabled`、`minimum_winning_seats`、`seat_quorum_required`、`weight_quorum_required`、`timeouts.review_disposition: "30m"`、`aep.max_message_bytes: 16384` + `max_inline_text_bytes: 2048`、`consensus_rule: "weighted_2/3_v1"`、`allowed_clis` 扩展至 7 项。**实测：§13 示例 vs `macao_config.schema.json` → PASS**。算术自洽：N=3 → `seat_quorum_required=2=⌈6/3⌉` ✓；W=2+1+1=4 → `weight_quorum_required=3=⌈8/3⌉` ✓。残留 N-5、N-12 |
| **P1-4** §6.1 缺 disposition 超时与 `NEEDS_ADMIN` | **VERIFIED（完全闭环）** | 触发器由 6 条增至 **8 条**，新增 `Disposition timeout`（引用 `timeouts.review_disposition`，默认 30m）与 `NEEDS_ADMIN unresolved`；`Consensus deadlock` 的 `--choice` 补齐 `EXTEND` 与 `[--exempt-issue-ids]`；`Reviewer timeout` 改为确定性推进口径。§6.2 降级路径同步改写为「记录超时弃权票 → 进入计票 → 满足门禁则 APPROVED，否则 DEADLOCK 转人工」——**上轮该处「必然 Deadlock」的错误口径已修正** |
| **P1-5** 产物示例与「唯一校验依据」互斥、互锁未强制 | **VERIFIED（完全闭环）** | 我按章节标题重建提取器后实测：**§2.1 / §2.2 / §2.3 / §2.5 四份示例对各自 Schema 全部 PASS**（上轮 §2.3 FAIL 10、§2.1 FAIL 1）。互锁falsify **5/5 全部正确拒绝**（上轮 4 条未强制）：BLOCKING+YES 拒、NO+空 items 拒、ABSTAIN+非空 items 拒、ABSTAIN 缺 reason 拒、status/vote 冲突拒。`review_manifest.schema.json` 现有 8 组 `allOf`。残留 N-3（`resolution` 同义值） |
| **P1-6** F-20 / FAQ Q12·Q13 / UC-5 / UC-1 / UC-7 / STATUS | **VERIFIED（5/6 闭环）** | **F-20** 改写为「…（已被 PRD v2.5 D-1 / D-2 显式裁定落实）」✓；**FAQ Q12** `CONSENSUS_CHECK` 行补入 `SHOULD_DISPOSE` 与 `DISPOSITION_REQUIRED` ✓；**FAQ Q13** 改为「`issues_index` 由编排器原样提取拼装…执行者逐项处置并写入独立 `executor.disposition.yml`，**不回写** `vote_result.json`」✓；**UC-5** 头部改 v2.5、P2 改为全席位 accounted（自相矛盾消除）✓；**UC-1** `adoption.yml` 已废除 ✓；**UC-7 全文重写**——边界声明、c 表五选项、L45 独立 `admin_override.json`、**L81 验收标准改为「DEADLOCK HOLD 期间 `vote_result.json` 已经存在且 `decision=DEADLOCK`；裁定后…内容与哈希无任何改写」**（与上轮完全相反，这是本轮最彻底的一处重写）✓。**STATUS 未闭环 → N-9** |
| **P1-7** 代码清单 10 条路径不存在 | **VERIFIED（完全闭环）** | 逐路径 `test -e`：`fsm.py` / `orchestrator.py` / `controller.py` / `main.py` / `wizard.py` / `git_utils.py` / `core/config.py` / `core/schema.py` / `consensus/*.py` 与 7 份 Schema **全部 EXISTS**；仅 `storage/evidence.py` 与 5 份 `tests/unit`·`tests/integration` 不存在，而清单**已明确标注「新建」**（L33、L93）与新增测试套件——标注与事实一致 |
| **P1-8** §14.5 与第十五部分缺失（8 处死链） | **VERIFIED（完全闭环）** | §14.3 日志与保留、§14.4 升级与降级、**§14.5 Merge Policy** 已恢复；**第十五部分 §15.1–§15.5** 已恢复。脚本化核验：全文 `§x.y` 引用 **8 个，悬空 0 个**；「第 X 部分」引用 20 个与实际标题集合**完全相等，缺失 0**；`§2.3 决策表` 悬空引用**已清零** |

**另核验通过的上轮 P2/P3**：§17.2 删除「自动对齐 `vote` / 自动补齐 `checkpoint_ref`·`review_round`」，改为「原样提取票面，**严禁代写或修改任何投票决策**」（P2-1 闭环，与 P-1 零语义创作、F-12/F-13 同向）；§18 改为「所有席位 accounted 后…若无法达成共识则即时落盘 DEADLOCK」（P2-2 闭环）；§4.1/§4.2 全面 v2.5 化并与清单 Phase 1–5 对齐（P2-3 闭环）；两份互斥版本演进记录合并为单一附录且移至文末，**v2.4 行「达成 L4 RELEASE-READY / PG-3 规格」的未授予门禁记录已删除**（P2-7、P2-8 闭环）；§1.1 流程图重复块与空框修复（P2-10 闭环）；§5.3 heredoc 改用字面 `codex.review.yml`（P3-1 闭环）；SRS 头部表格 12 行补齐 `>` 前缀（P3-2 闭环）；§5.3/§5.4 顺序归位（P3-4 闭环）。

**申请 §4 自动化验证结果复核**：我本机独立重跑 —— `PYTHONPATH=src python3 -m unittest discover tests` → **Ran 84 tests，OK（32.9s）**；`python3 -m compileall -q src tests` → **rc=0**。与申请自述一致。

**Schema 双份镜像**：`docs/schemas/` 与 `src/macao/schemas/` 8 份同名文件 **`diff` 全部 SAME**，无单边漂移。

---

## 二、P1：必须先解决（2 项）

### N-1　§2.3 加权五重门禁公式被控制字符损坏（本 commit 引入的回归）

`docs/MACAO_PRD_v2.md` L332–335，即 v2.5 **唯一权威的共识判定公式**：

```
332: 1. **配置期独裁帽**：$<FF>orall i, 3 <TAB>imes w_i < 2 <TAB>imes W$（单席位权重达 2/3 拒绝启动系统）；
333: 2. **席位法定人数**：$E_N \ge \lceil 2N/3 <CR>ceil$；
334: 3. **权重法定人数**：$E_W \ge \lceil 2W/3 <CR>ceil$（分母为配置总权重 $W$）；
335: 4. **胜方权重阈值**：赞成满足 $3 <TAB>imes approve\_weight \ge 2 <TAB>imes E_W$，或反对满足 $3 <TAB>imes reject\_weight \ge 2 <TAB>imes E_W$；
```

**逐字节证据**（`cat -A`）：`\forall` → `^L`(0x0C) + `orall`；`\times` → `^I`(0x09) + `imes`（共 6 处）；`\rceil` → `^M`(0x0D) + `ceil`（共 2 处）。成因是整改过程中 `\f` / `\t` / `\r` 被 shell 或 `sed` 当作转义序列消费。

**范围与归因（按字节精确定位）**：全文档集（PRD + FAQ + SRS + 清单 + 11 份 UC）控制字符**共 9 个，全部在 PRD L332–335**，其余文件为 0。`git show 0bc6247:docs/MACAO_PRD_v2.md` 对应位置为 `$\forall i, 3 \times w_i < 2 \times W$` 与 `\lceil 2N/3 \rceil` —— **完好**。因此这是 `2766c69` 引入的回归，不是历史遗留。

**为什么判 P1 而不是排版瑕疵**：
1. 受损的是 §2.3，即 D-6「纯整数加权共识」的**权威定义处**，也是 Gemini P1-1「加权共识算法的整数确定性」唯一的落点；
2. 门禁 1 的全称量词 `∀` 被销毁，而门禁 1 就是**独裁帽**——防单模型支配的核心约束（F-22）；
3. 门禁 2、3 变成 `\lceil 2N/3 ceil`，`\lceil` 无配对，任何 LaTeX 渲染器都会报错，属 GUIDELINES §9-D「代码块/公式不可执行」；
4. GUIDELINES §8：投票公式属「审计相关的结构性内容」。

**减轻情节（据实记录）**：语义可从三处完好的下游复述恢复——`FAQ.md` L306–309、`UC5-consensus-tally.md` L31–33、`v2.5_CODE_CHANGE_INVENTORY.md` L75 的公式**均完好**；§13 的数值参数（`seat_quorum_required` / `weight_quorum_required` / `minimum_winning_seats`）亦完好。故实现者不会因此推出错误算法，风险是「权威基准本身不可用」而非「行为歧义」。

**验收标准**：L332–335 恢复 `\forall` / `\times` / `\rceil`；全文档集按字节复扫 `0x09/0x0b/0x0c/0x0d` 计数归零（§五脚本 A 应输出 `控制字符总数: 0`）。

### N-2　`vote_result.schema.json` 仍放行 `RETRY_REVIEW` / `CANCELLED`，与本轮闭环声明矛盾

申请 §3 第 1 行明写整改内容为「…**移除 RETRY_REVIEW/CANCELLED 机器决策**」。正文侧确已移除：§2.3 规则 6 只定义三个终值（`APPROVED` / `REWORK_REQUIRED` / `DEADLOCK`），§3.2 Layer 1c 只有三个分支。**但机器契约没有同步**：

```
docs/schemas/vote_result.schema.json → decision enum:
  ['APPROVED', 'REWORK_REQUIRED', 'DEADLOCK', 'RETRY_REVIEW', 'CANCELLED']
```

**falsify 实测**（§五脚本 B，以 PRD §2.3 示例为基底逐值替换）：

| decision | Schema | §3.2 Layer 1c 有分支 |
|---|---|---|
| `APPROVED` | 接受 | 是 |
| `REWORK_REQUIRED` | 接受 | 是 |
| `DEADLOCK` | 接受 | 是 |
| `RETRY_REVIEW` | **接受** | **否** |
| `CANCELLED` | **接受** | **否** |

后两行即 GUIDELINES §9 漏审模式 A 的契约层形态：**契约放行、消费方无分支**。一份 `decision: "RETRY_REVIEW"` 的 `vote_result.json` 能通过 Draft-07 强校验、通过 §3.2 的 `load_and_validate`，然后落在 Layer 1c 全部 `elif` 之外，坠入 Layer 2 —— 行为退化为静默 HOLD，且不产生任何契约级告警。

这也重新打开了 D-1 的口子：`RETRY_REVIEW`（E9）与 `CANCELLED`（E10）在 v2.5 是**命令型转移**，其记录载体是 `admin_override.json`；把它们保留在机器 `decision` 枚举里，等于契约仍然允许把人工裁定写进不可变的 `vote_result.json`。

需要说明的是，**旧的 `allOf` 条件（`decision ∈ {RETRY_REVIEW, CANCELLED} ⟹ resolution = human_override`）已被正确删除**（`allOf` 现为 `null`），所以这两个值现在既无条件约束也无消费者——是纯粹的悬空枚举值。

**验收标准**：`decision` 枚举收敛为 `["APPROVED","REWORK_REQUIRED","DEADLOCK"]`；`src/macao/schemas/vote_result.schema.json` 同步；§五脚本 B 的后两行应变为「拒绝」。若确需保留兼容读取历史产物，须在 §2.3 显式写明「仅用于读取 v2.3.1 存量产物，禁止新产出」并在 Schema 用 `if/then` 绑定 `version`。

---

## 三、P2：登记，Phase 1 前处理（8 项）

| ID | 问题 | 证据 |
|---|---|---|
| **N-3** | `vote_result.resolution` 枚举为 `["automatic","human_override","AUTO_WEIGHTED_CONSENSUS"]`。上轮我指出 `AUTO_WEIGHTED_CONSENSUS` 无定义，本轮的修法是**把它加进枚举**，于是 `automatic` 与 `AUTO_WEIGHTED_CONSENSUS` 成为同一语义的两个名字，且无规则说明何时用哪个——GUIDELINES §5 明文禁止「用不同名词描述同一决策结果」。另 `UC5-consensus-tally.md` L66 的 A3 行标仍写 `resolution: human_override`（行内描述已正确改为「独立生成 `admin_override.json`」），而在 D-1 下不可变的 `vote_result` 落盘于 DEADLOCK 时刻，此后不可能再被写入 `human_override`，该行标指向一个永远写不出的取值 | `vote_result.schema.json:resolution`；PRD L325；UC-5 L66 |
| **N-4** | 申请 §3 第 6 行声称 admin_override 的管理员排他写入权「记录于 §3.4 生命周期表**与 §16.1 垄断权表**」。§3.4 生命周期表**确已补入** `admin_override.json`（生成者 `Orchestrator (Admin)`）✓；但 **§16.1 垄断权表（L1499–1503）只有编排者/执行者/评审专家三行，编排者的垄断权列为「唯一写不可变 `vote_result.json`、唯一执行 merge、唯一管理 evidence promotion」，无 `admin_override.json`，且全表无管理员角色行**。该闭环声明有半条不成立 | PRD L1499–1503 |
| **N-5** | §13 引入 `dictator_cap_enabled: true` **布尔开关**，而 §2.3 门禁 1 是无条件表述（「单席位权重达 2/3 **拒绝启动系统**」），F-22 亦为强制事实（「权重…不能使单个 Reviewer 在其他有效席位反对时独自形成自动决定」）。一个可被置 `false` 的开关，等于给事实源规定为强制的门禁开了合法关闭路径。另实测：权重 `10/1/1`（W=12，3×10=30 ≥ 2×12=24）的独裁配置**被 `macao_config.schema.json` 接受**——Draft-07 无法表达跨条目求和约束，这本身合理（清单 §2.2 已把该校验指派给 `config.py`），但文档未说明「Schema 不负责该校验、由 Loader 负责」，也未说明开关语义 | PRD L1361 vs L332；`macao_config.schema.json` |
| **N-6** | §5.2 三处表述「**9 大**语义块」（L948 / L950 标题 / L952「两个传输块 + 七个语义块，共 9 大必需块」），而 `required_blocks` **实列 10 项**、YAML 实际定义 **10 块**。且 `review_context.schema.json` 的 `required` 只有 5 项——实测删除 §5.2 自称必需的 `evidence` 与 `review_guidelines` 后，实例**仍被接受**。上轮 P0-2 的主体（路径互斥）已闭环，此为残留的计数与强制面 | PRD L948/950/952；`review_context.schema.json:required` |
| **N-7** | `dev_manifest.schema.json` 将 `signal` 定义为 `{"const": "EXPLICIT"}` 且列入 `required`。但 `UC3-dev-checkpoint.md` 把 Schema 校验（d1）与 `signal == EXPLICIT`（d2）列为**两道独立门禁**，并在 A1 把 `signal: IMPLICIT` 当作**合法输入类**（「不转移；Layer 2 只预警」）。在 `const` 约束下，`IMPLICIT` 在 d1 即被判为产物非法，d2 与 A1 永不可达——GUIDELINES §9 模式 A。两条路径的最终外部行为恰好相同（不转移 + Layer 2 告警），故不影响状态机结果，但契约与用例对「什么是合法 `.dev.yml`」的定义不一致 | `dev_manifest.schema.json`；UC-3 L51/L69 |
| **N-8** | worktree 路径仍有两套相反的层级顺序：§5.2（`worktrees/codex/task-1/r1`）、FAQ Q11.4（`worktrees/<reviewer>/<task>/r<round>`）、UC-4 L32（`worktrees/<agent_id>/<task_id>/r<round>`）为 **reviewer/task/round**；而 **§17.1（L1541）为 `worktrees/<task_id>/<reviewer_id>`，顺序颠倒且无 round**。以实现为准可判定 §17.1 是错的一方：`src/macao/utils/git_utils.py:104` 与 `:127` 均为 `.macao/worktrees/<reviewer_id>/<task_id>/r<review_round>`。上轮 6 种写法已收敛到 2 种 | PRD L1541 vs L971；`git_utils.py:104` |
| **N-9** | 交付物 #13 称 STATUS.md「**完整如实**记录全部 5 份专家评审报告结论与闭环履历」。登记表行确已补入 5 份报告文件名 ✓，但 STATUS **文首未随本轮更新**：「最新更新时间」仍写 `b76cbfb`/`ac32dbb` 轮次，「当前申请对象」仍指向 `2026-09-01-review-request-Phase3-PG3-L4-Certification.md`，而非本申请。按 STATUS 自身治理规则（「每轮申请复审前，STATUS 必须与 `reviews/` 目录全量对账」）我做了全量对账：**登记但文件不存在 —— 0；存在但未登记 —— `2026-09-01-review-result-2766c69-glm.md`（1 份）** | STATUS L6–L7；对账实测 |
| **N-10** | `aep_envelope.schema.json` 的 `protocol` 枚举为 `["AEP/1.0","AEP/1.1"]`——这本身与 §2.4「`protocol` 统一为 `AEP/1.1`（**兼容读取 AEP/1.0**）」一致，**不是缺陷**。缺陷在于 `type` 集合未与 `protocol` 版本绑定：一份 `protocol: "AEP/1.0"` 的信封携带 `type: "DISPOSITION_REQUIRED"`（1.1 才引入的第 8 类）可通过校验。另 16 KiB / 2048 字节预算在契约中无任何表达，也未在清单中指明由哪个模块强制（§2.4 只说「发送与接收端双向严格校验」） | `aep_envelope.schema.json`；PRD L360、L366 |

---

## 四、P3：可延期（4 项）

| ID | 问题 | 证据 |
|---|---|---|
| N-11 | §4.1 标题仍为「严格的 MVP 范围（**第一期，6-8 周**）」，而同节 §4.2 已改写为 Phase 1–5 / **Day 1–7**。同一节内两套工期 | PRD L896 vs L913–938 |
| N-12 | §19 声称「在 `macao.yaml` 中通过 `model: "<model_id>"` 显式声明具体模型」，但 §13 单一事实源的 `team.reviewers[]` 与 `executor` 样例**均无 `model` 字段**，`macao_config.schema.json` 亦未定义 | PRD L1564 vs L1352–1358 |
| N-13 | 权威基准 PRD 正文未规定 `.review.yml` 的**产物层**去重（全文幂等去重只有 L1321 的 `ack(message_id)`）。GUIDELINES §6 第 5、6 条实际可由 `UC4-review-dispatch.md` P4/f4/A5/E5 唯一推出（见 §0.2 我的撤回），但 PRD 未给出指向 UC-4 的指针 | PRD L1321；UC-4 L18/L44/L58/L68 |
| N-14 | `signal` 字段在 PRD 全文只出现于 §2.1 示例 L185 一处，无任何正文条文说明其语义与消费方（语义实际定义在 UC-3）。与 N-7 同源 | PRD L185 |

---

## 五、反例与边界场景推演（GUIDELINES §6 全量重放）

| # | 场景 | 上轮 | 本轮 | 依据 |
|---|---|---|---|---|
| 1 | 2-reviewer 全部弃权 | 否 | **是** ✓ | $E_N=0 \ge \lceil 4/3 \rceil=2$ ✗ → 门禁 6「其余一切情形」→ `DEADLOCK` 即时落盘 → §3.2 Layer 1c `DEADLOCK` 分支 → HOLD → E7。UC-5 A2 同口径 |
| 2 | 1 超时 + 1 批准 | 部分 | **是** ✓ | §3.3 超时行记 `source: timeout` 计入 accounted → §18 全席位 accounted 后计票 → $E_N=1<2$ → `DEADLOCK` → HOLD。§6.2 降级路径已改写为同一口径（上轮的「必然 Deadlock」错误表述已修正为「满足门禁则 APPROVED，否则 DEADLOCK」） |
| 3 | 1 批准 + 1 反对（1:1 僵局） | **否（P0）** | **是** ✓ | 门禁 4：$3\times1=3 \ge 2\times2=4$ ✗（双向）→ `DEADLOCK`；落盘与否不再有二义（§3.3 E3 与 §3.4 场景三现已同口径） |
| 4 | 3-reviewer 1:1:1 | 否 | **是** ✓ | $E_N=2\ge2$ ✓、$E_W=2\ge\lceil6/3\rceil=2$ ✓、门禁 4 $3\ge4$ ✗ → `DEADLOCK`。§3.4 场景三即以此为例 |
| 5 | Reviewer 崩溃重启后重复提交投票 | 否（**已撤回**） | **是** ✓ | UC-4 E5「f4 去重幂等；崩溃前已消费票不重复计数」。见 §0.2 |
| 6 | 同一 checkpoint 两份同 reviewer_id 票 | 否（**已撤回**） | **是** ✓ | UC-4 P4 去重前置 + A5「f4 去重 + 审计；不双计」 |
| 7 | `.dev.yml` 缺字段但 `signal=EXPLICIT` | 否 | **是** ✓ | 上轮「# 显式信号，MACAO **强制认可**」的注释已删除，Schema 校验唯一决定受理与否。残留 N-7/N-14 |
| 8 | 第二轮返工 `.review.yml` 是否覆盖第一轮 | 是 | **是** ✓ | §3.4 生命周期表；场景推演二 Step 7「r1 产物已归档」 |
| 9 | 人工接管超时后默认动作 | 部分 | **是** ✓ | §6.1 总则 + 触发器扩至 8 条（含 Disposition timeout 与 NEEDS_ADMIN），v2.5 新增的两类 HOLD 现已有明确默认动作 |
| 10 | Git 冲突致 checkpoint 与工作区不一致 | 是 | **是** ✓ | E4a 硬校验并细化为 `ff_only` 下 remote tip == checkpoint_ref、`no_ff` 下 merge commit 第二父 == checkpoint_ref |
| 11 | `review_context` diff 载体与 Reviewer 工作流不一致 | **否（P0）** | **是** ✓ | §5.2 = §5.3 = Schema 三者同构，实例校验 PASS |

**11 / 11 全部可唯一推出**（上轮：唯一可推出 2、部分 2、不可推出 7）。这是本轮最有说服力的单项指标——**GUIDELINES §6 反例库首次全通过**。

**追加推演（v2.5 专有）**：上轮我指出「场景推演二无法满足 E6 守卫」（缺 FINAL disposition 步骤）。本轮场景二 Step 6 已补入「Executor 提交 `executor.disposition.yml`（FINAL，`requires_new_checkpoint=true`）→ E5a/E5 进 REWORK」，Step 8 再走 E6，**守卫前提成立**，闭环 ✓。

### 复现脚本

```bash
cd /path/to/macao && python3 - <<'PY'
# 脚本 A：控制字符按字节精确扫描（N-1）——注意勿用 grep -P '[\t\f\v]'，PCRE 的 \v 是竖向空白类，会逐行匹配换行
import glob
files=['docs/MACAO_PRD_v2.md','docs/FAQ.md','docs/SRSv1.md',
       'docs/v2.5_CODE_CHANGE_INVENTORY.md']+sorted(glob.glob('docs/usercases/*.md'))
bad={0x09:'TAB',0x0b:'VT',0x0c:'FF',0x0d:'CR'}; tot=0
for f in files:
    b=open(f,'rb').read(); hits={}
    for i,ch in enumerate(b):
        if ch in bad: hits.setdefault(bad[ch],[]).append(b[:i].count(b'\n')+1)
    if hits:
        tot+=sum(len(v) for v in hits.values())
        print("%-42s %s"%(f,{k:(len(v),sorted(set(v))) for k,v in hits.items()}))
print("控制字符总数:",tot,"  (期望 0)")

# 脚本 B：decision 枚举 vs §3.2 Layer 1c 分支（N-2）
import json,copy,jsonschema
L=open('docs/MACAO_PRD_v2.md').read().split('\n')
a=next(i for i,l in enumerate(L) if l.startswith('### 2.3 '))
s=next(i for i in range(a,a+30) if L[i].strip()=='```json')+1
e=next(i for i in range(s,s+200) if L[i].strip()=='```')
base=json.loads('\n'.join(L[s:e]))
V=jsonschema.Draft7Validator(json.load(open('docs/schemas/vote_result.schema.json')))
for dv in ['APPROVED','REWORK_REQUIRED','DEADLOCK','RETRY_REVIEW','CANCELLED']:
    x=copy.deepcopy(base); x['decision']=dv
    ok=not list(V.iter_errors(x)); fsm=dv in ('DEADLOCK','APPROVED','REWORK_REQUIRED')
    print("  decision=%-16s schema:%-4s Layer1c分支:%-4s %s"%(
        dv,"接受" if ok else "拒绝","有" if fsm else "无",
        "  <-- 契约放行但状态机无分支" if (ok and not fsm) else ""))

# 脚本 C：四份产物示例 + review_context + macao.yaml 对各自 Schema 校验（按章节标题定位，勿用行偏移）
import re,yaml
def sec(pat):
    st=None
    for i,l in enumerate(L):
        if re.match(r'^#{2,4} ',l):
            if st is not None: return st,i
            if re.search(pat,l): st=i
    return st,len(L)
def first_block(a,b,lang):
    for i in range(a,b):
        if L[i].strip()=='```'+lang:
            j=i+1
            while L[j].strip()!='```': j+=1
            return '\n'.join(L[i+1:j])
for name,pat,lang,sf,load,key in [
    ('§2.1 .dev.yml',    r'### 2\.1 ','yaml','dev_manifest',      yaml.safe_load,None),
    ('§2.2 .review.yml', r'### 2\.2 ','yaml','review_manifest',   yaml.safe_load,None),
    ('§2.3 vote_result', r'### 2\.3 ','json','vote_result',       json.loads,    None),
    ('§2.5 disposition', r'### 2\.5 ','yaml','review_disposition',yaml.safe_load,None),
    ('§5.2 context',     r'### 5\.2 ','yaml','review_context',    yaml.safe_load,'review_context'),
    ('§13 macao.yaml',   r'^## 第十三部分','yaml','macao_config', yaml.safe_load,None)]:
    a,b=sec(pat); inst=load(first_block(a,b,lang))
    if key: inst=inst[key]
    errs=sorted(jsonschema.Draft7Validator(json.load(open('docs/schemas/%s.schema.json'%sf))).iter_errors(inst),
                key=lambda x:list(x.path))
    print("  %-20s vs %-28s -> %s"%(name,sf+'.schema.json',"PASS" if not errs else "FAIL(%d)"%len(errs)))
    for x in errs[:6]: print("       -",list(x.path) or "(root)",x.message[:130])

# 脚本 D：§2.2 五重条件互锁 falsify
sch=json.load(open('docs/schemas/review_manifest.schema.json')); V2=jsonschema.Draft7Validator(sch)
def mk(vote,items,ar=None,st="APPROVED"):
    d={"version":"1.0","timestamp":"2026-09-01T10:45:30Z","task_id":"task-1","checkpoint_ref":"a1b2c3d",
       "review_round":1,"reviewer":{"id":"codex","role":"reviewer","cli":"codex","version":"2.1.0"},
       "opinion":{"status":st,"confidence":0.9,"feedback_summary":"x"},"items":items,"vote":vote}
    if ar is not None: d["abstain_reason"]=ar
    return d
B=[{"issue_id":"codex/SEC-01","disposition_class":"BLOCKING","severity":"major","title":"t"}]
for n,i in [("BLOCKING+YES_APPROVE 应拒",mk("YES_APPROVE",B)),
            ("NO_APPROVE+空 items 应拒",mk("NO_APPROVE",[],st="CHANGES_REQUESTED")),
            ("ABSTAIN+非空 items 应拒",mk("ABSTAIN",B,ar="x",st="ABSTAINED")),
            ("ABSTAIN 缺 reason 应拒",mk("ABSTAIN",[],st="ABSTAINED")),
            ("status/vote 冲突 应拒",mk("NO_APPROVE",B,st="APPROVED"))]:
    print("  %s %s"%("拒绝OK " if list(V2.iter_errors(i)) else "**接受✗**",n))
PY

# 脚本 E：Schema 双份镜像一致性 + 清单路径存在性
for f in docs/schemas/*.json; do b=$(basename "$f")
  diff -q "$f" "src/macao/schemas/$b" >/dev/null 2>&1 && echo "SAME  $b" || echo "DRIFT $b"; done
grep -oE '`src/macao/[a-z_/]+\.py`' docs/v2.5_CODE_CHANGE_INVENTORY.md | tr -d '`' | sort -u \
  | while read p; do [ -e "$p" ] && echo "EXISTS  $p" || echo "MISSING $p (须在清单标注「新建」)"; done
```

---

## 六、建议的闭环顺序与验收标准

| 序 | 事项 | 验收标准 |
|---|---|---|
| 1 | **N-1** 恢复 §2.3 公式 | §五脚本 A 输出 `控制字符总数: 0`；L332–335 与 FAQ L306–309 逐字符一致 |
| 2 | **N-2** 收敛 `decision` 枚举 | §五脚本 B 后两行为「拒绝」；`docs/` 与 `src/macao/` 两份 Schema 同步（脚本 E 全 SAME） |
| 3 | 复评 L1 / PG-0 | 上述两项闭合即可授予。**建议走最小差量快速复评**，不要求重跑全量交付物核验 |
| 4 | N-3～N-10（P2） | Phase 1 启动前处理：`resolution` 枚举去同义值；§16.1 补管理员行与 `admin_override.json`；`dictator_cap_enabled` 语义裁定（建议直接删除该开关，改为无条件校验）；§5.2 块数改 10 并把 `evidence`/`review_guidelines` 提入 Schema `required`；§17.1 worktree 路径按 `git_utils.py:104` 改正；STATUS 文首更新并登记 glm 报告 |
| 5 | N-11～N-14（P3） | 随后续文档修订顺带处理 |

**不建议**：因为「只差两条」就把它们降级为 P2 放行。N-2 是契约层的 fail-open，且与申请 §3 的具体闭环声明直接矛盾；按 F-17，需要修复后才能合入的「有条件通过」在机器语义上就是阻断性不通过。**同样不建议**：因本轮仍为 `NO_APPROVE` 而低估整改质量——10/10 阻断项实质闭环、反例库 11/11 首次全通过，这是可验证的实质进展，与上一轮不是同一量级。

---

## 七、与其他 Reviewer 的交叉核对（GUIDELINES §8）

本轮读到同 commit 的 [`2026-09-01-review-result-2766c69-glm.md`](2026-09-01-review-result-2766c69-glm.md)（未被 STATUS 登记，见 N-9），结论为 **APPROVE（授予 L1/PG-0）**，附 3 项非阻断登记项。

**独立复现后确认一致**：glm 核验表 13 项中，第 1–11、13 项我均独立重跑并得到相同结论（Layer 1b/1c、场景三、`refs` 嵌套、`policy_snapshot`、互锁 5/5、两份新 Schema、§2.5、AEP 8 类与 0 base64、§14.3–15.5 无死链、清单路径、84/84 测试）。glm 的 P3-2（两份 Schema 拷贝无同步守卫）我亦独立确认：当前 `diff` 全部 SAME，但仓库内确无 `diff -r` 守卫。

**与 glm 的分歧（各 1 项，均附证据）**：

1. **glm 的 P2-1 我判为已闭环**。glm 写「disposition 超时后的转移（继续 HOLD→人工接管？）在 §3.3/§6 未见显式行」。**§6.1 现已有专门触发器**：`{"condition": "Disposition timeout", "description": "Executor failed to submit executor.disposition.yml within timeouts.review_disposition (default 30m)", "action": "Ask user: '--choice APPROVED | REWORK | CANCEL | EXTEND [--exempt-issue-ids]'", "timeout": "30 minutes"}`，且 §6.1 总则规定默认 HOLD + 持续告警。glm 关于 §3.3 无独立行的观察成立，但 E7 行已覆盖「HOLD（`CONSENSUS_CHECK` 或 `REWORK`）」的全部人工裁定入口，我认为不构成登记项。
2. **glm 未发现 N-1 与 N-2**。glm 第 5 项核验了 `policy_snapshot` 与整数计票结构存在，但未对 `decision` 枚举做逐值 falsify；第 9 项核验了 AEP 与 base64，未按字节扫描控制字符。这两项是我本轮的独立发现，也是我与 glm 结论分歧（`NO_APPROVE` vs `APPROVE`）的**全部原因**——除这两条外，我与 glm 对本轮整改质量的判断完全一致。

按 §8「真理不等于投票」，我不因 glm 已投 APPROVE 而放行，也不因自己投 NO_APPROVE 而否定 glm 已复现的 11 项闭环。按 §8「沉默 ≠ 同意」，Codex / Gemini / Grok / Kimi / Qwen / ZCode 本轮尚未出具报告，不计入任何一方。

---

## 附：机器票与结构化 issue 清单

| issue_id | severity | disposition_class | 摘要 |
|---|---|---|---|
| `claude/N-1` | major | `BLOCKING` | §2.3 加权五重门禁公式被控制字符损坏（FF/TAB/CR × 9，全库仅 L332–335），为本 commit 引入的回归；`\lceil` 失配不可渲染，独裁帽的全称量词被销毁 |
| `claude/N-2` | major | `BLOCKING` | `vote_result.schema.json` 的 `decision` 仍放行 `RETRY_REVIEW`/`CANCELLED`，契约接受而 §3.2 Layer 1c 无分支；与申请 §3「移除 RETRY_REVIEW/CANCELLED 机器决策」的闭环声明矛盾 |
| `claude/N-3` | minor | `ADVISORY` | `resolution` 枚举含同义对 `automatic` / `AUTO_WEIGHTED_CONSENSUS`；UC-5 A3 行标 `resolution: human_override` 指向不可写取值 |
| `claude/N-4` | minor | `ADVISORY` | §16.1 垄断权表无 `admin_override.json` 与管理员角色行，申请 §3 第 6 行该半条不成立 |
| `claude/N-5` | minor | `ADVISORY` | `dictator_cap_enabled` 布尔开关与 §2.3 无条件表述、F-22 强制事实冲突；Schema 不拦截独裁配置且文档未指明校验落点 |
| `claude/N-6` | minor | `ADVISORY` | §5.2 三处「9 大必需块」vs `required_blocks` 实列 10；Schema `required` 仅 5，缺 `evidence`/`review_guidelines` 的实例仍被接受 |
| `claude/N-7` | minor | `ADVISORY` | `dev_manifest` 的 `signal: {"const":"EXPLICIT"}` 使 UC-3 d2 与 A1（`signal: IMPLICIT`）不可达 |
| `claude/N-8` | minor | `ADVISORY` | §17.1 worktree 路径层级与 §5.2/FAQ/UC-4 及实现 `git_utils.py:104` 相反 |
| `claude/N-9` | minor | `ADVISORY` | STATUS.md 文首未随本轮更新；对账缺登记 `2026-09-01-review-result-2766c69-glm.md` |
| `claude/N-10` | minor | `ADVISORY` | `aep_envelope` 未把 `type` 集合绑定 `protocol` 版本；16 KiB/2048 预算无契约表达且未指明强制模块 |
| `claude/N-11`…`N-14` | trivial | `ADVISORY` | §4.1「6-8 周」vs §4.2 Day 1-7；§19 `model:` 未进 §13；PRD 未指向 UC-4 去重；`signal` 语义未在 PRD 正文定义 |

```
vote: NO_APPROVE
requires_new_checkpoint: true   # 需产生新的文档 checkpoint；预计改动约 6 行，建议最小差量快速复评
```
