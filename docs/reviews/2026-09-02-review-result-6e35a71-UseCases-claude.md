# 全量用例体系（UseCases）PRD v2.5 对齐 独立评审结论（Round 2，`6e35a71`）

- **评审日期**：2026-09-02
- **评审人**：claude
- **评审对象**：[`docs/reviews/2026-09-02-review-request-UseCases-v2.5-Alignment-r2.md`](2026-09-02-review-request-UseCases-v2.5-Alignment-r2.md)
- **申请声称基线**：`6e35a71`；**工作区 HEAD**：`12a05e2`（差量仅两份 r2 申请 + `STATUS.md`，13 份用例正文与 `6e35a71` 逐字节相同）
- **本人前序票**：`caf3473`（`NO_APPROVE`，P1×5：U-1 处置路径分裂 / U-2 AEP Type 字母错位 / U-3 `items[]` 字段名 / U-4 UC-8 缺 Pre-merge 关卡 / U-13 示例通不过契约）
- **对齐基准**：`docs/MACAO_PRD_v2.md`（v2.5）；`docs/PRD_CHANGE_PROPOSAL_v2.5.md` §2 L34–L42（D-1～D-9 唯一权威定义源）；`docs/usercases/PRODUCT-FACTS.md` F-1～F-22；`docs/MACAO_REVIEW_GUIDELINES.md`
- **申请定级**：L1 DOC-ALIGNED / PG-0

## 结论

**`NO_APPROVE`。** 机器票不得为「有条件通过」（PRODUCT-FACTS F-17）。

**我上轮的 5 条 P1 全部真实闭环，无一回退**，逐条机验见 §二。这一轮用例体系的正文质量与 `caf3473` 相比是实质跃升。

阻断本次定级的是三条**此前未被任何一方检查过**的项：

1. UC-7 的六个接管触发自称「全部枚举闭合」，但其中两个在 PRD §3.3 里**没有可达的 E7 边**，而 UC-8 关卡 3 明文把 Git Conflict 回环到其中之一——这条回路在状态机上不存在（P1-1）；
2. UC-6 与 UC-7——恰好是承载两条最新裁定 D-2 与 E7 豁免流的两份文档——**缺失验收标准 / 后置条件 / 设计自审**，而本申请 §6 请求把用例体系批准为「Phase 1~5 研发实施与**测试验收**的官方操作基准」（P1-2）；
3. UC-3 的拓扑子孙守卫在 PRD 与技术变更清单侧无对应，按清单施工会弱化现有代码里已有的守卫（P1-3，与设计同步轨同一条，两轨都登记）；
4. UC-8 对「远端不可达」同时给出 fail-closed 拦截与降级成功两种互斥结果（P1-4，与 Codex 独立收敛）。

**票型说明**：同基线四份报告为 **2 YES（grok、qwen）: 2 NO（Codex `REJECT` P1×8、本报告）**。Codex 独立到达了我的 P1-1（UC-7 五选项塞进 init 与 MERGING 两个不相容起态）与 P1-4，这两条是本轮**唯二被两名 reviewer 独立复现的用例轨阻断项**。按 GUIDELINES §8「真理不等于投票」，2:2 不构成裁决，建议以可复跑证据逐条裁定。

设计同步轨另文出具：[`2026-09-02-review-result-6e35a71-DesignSync-claude.md`](2026-09-02-review-result-6e35a71-DesignSync-claude.md)。

---

## 0. Reviewer 自审记录（GUIDELINES §9）

### 0.1 本轮被我自己证伪、因而**未**上报的两条假设

1. **UC-1-gemini 的 `seat_quorum_required: 2 / weight_quorum_required: 2` 违反 $\lceil 2N/3 \rceil / \lceil 2W/3 \rceil$** ——
   我先把它当成「示例配置违反自己的公式」。实算：该文件 `:144-161` 定义 $N=3$ 名 reviewer，`vote_weight` 各 1 故 $W=3$；$\lceil 6/3 \rceil = 2$，两个键都等于 2。**两值均正确，假设撤回。** PRD §13 示例（$N=3$，$W=2{+}1{+}1=4$ → 2 与 3）同样自洽。
2. **UC-6 §2.b `:24` 的归档路径 `.macao/archive/<checkpoint_ref>/r<round>/` 是第二条处置路径（U-1 未真正闭环）** ——
   核对后：`.macao/archive/` 是 v2.5 之前既有的**轮次级本地快照目录**（`PRD_CHANGE_PROPOSAL_v2.5.md:73`、`:437`、`PLAN.md:77`、`ROADMAP.md:84`、`src/macao/cli/wizard.py:88` 的 gitignore 规则），与写入路径 `.macao/.dispositions/r<round>/` 是**写入位置 vs 归档位置**两件事，不是分裂。**假设撤回。**

### 0.2 一条我只能给出弱结论的判定

UC-5 §2.b 残留的浮点「赞成加权占比 = Σ(approve 权重) / 有效权重」（P2-1）：我穷举 $E_W\in[1,5000]$、$W_{win}\in[0,E_W]$ 约 1.25×10⁷ 组，`(W_win/E_W) >= 2/3` 与 `3*W_win >= 2*E_W` **零数值分歧**。因此只能判为**规范歧义**（与 D-6「严禁浮点数运算与静默四舍五入」抵触），**不能**断言会算错票。据此定 P2，不定 P1。

### 0.3 强制自检 5 项

| # | 项 | 本轮 |
|---|---|---|
| 1 | 字段声明位置 vs 实际读取位置 | 处置产物路径四方同构 ✓；**UC-7 接管选项集与 PRD §3.3 可达边不一致（P1-1）** |
| 2 | 「已完成 / 100%」是否等同证据 | 申请 §4 五项逐条重放；「13 份 0 控制字符」VERIFIED，「179/13 份」计数口径 CONTRADICTED |
| 3 | 确定性语言是否标注 | 「未被拦截 / 无可达边」均附原文行号与推导 |
| 4 | 代码块可执行性 | 本报告脚本原样贴出，均已实跑 |
| 5 | 每条 P1 是否附路径行号 | 是 |

### 0.4 连续漏审模式登记

我在 `caf3473` 轮登记过「能解析 ≠ 合契约」。本轮延伸出**第二条**：**「本文自洽 ≠ 跨文档可达」**。UC-7 §1 与 §2.c 单看完全自洽（六个触发、五个闭合选项、确定性映射表），只有把它压到 PRD §3.3 的转移表上才会发现两个触发没有出边。我把「用例声明的每一个入口/出口，是否在 §3.3 表里存在对应边」加入常备检查项。

### 0.5 证据类型适用性

本轮为 **DOC + SPEC**。`src/macao/workflow/orchestrator.py:257` 仅在 P1-3 作**反证**引用（现有实现比 PRD 严），不作定级证据。86/86 测试覆盖的是 v2.3.1 引擎，**NOT_APPLICABLE**。

---

## 一、申请 §4 自动化结论：独立重放

| 申请声明 | 本机结果 | 判定 |
|---|---|---|
| 13 份用例文档 0 控制字符 | `docs/usercases/*.md` 实测 **13 份**，按字节扫 `0x09/0x0b/0x0c/0x0d` **0 命中**（全库同样 0） | **VERIFIED** |
| UC-6 / UC-3 / UC-1-gemini 示例过 Draft-07 | 抽出全部围栏（13 份文档共 **3 个 yaml 围栏**，恰好就是这三处）→ `review_disposition` / `dev_manifest` / `macao_config` 各 0 error | **VERIFIED**，且申请覆盖完整 |
| valid 8/8、invalid 7/7 FAIL-CLOSED | 8/8 通过；7/7 被拒，**逐条打印拒绝原因**确认拒的是名义约束（含对 `review_status_vote_conflict.yml` 的隔离复验，见 §0 说明） | **VERIFIED** |
| `docs/schemas/` vs `src/macao/schemas/` 0 diff | 8 份同名契约 `cmp` 全 SAME | **VERIFIED** |
| 86/86、`compileall` 0 Errors | `Ran 86 tests ... OK`；退出 0 | **VERIFIED**（但与 L1 无关，见 §0.5） |

**补充观察**：13 份用例文档合计只有 **3 个 yaml 围栏 + 1 个 json/sql/mermaid/text 若干**。也就是说 UC-5（`vote_result.json`）、UC-7（`admin_override.json`）、UC-4（`.review.yml` / AEP 信封）——三份承载 D-1 / E7 / D-7 的核心用例——**没有任何可机器校验的实例**。这不构成阻断（用例不必带示例），但它意味着「100% 机器语义级对齐」这句话在这三份上没有机器证据支撑，只有正文比对。

---

## 二、本人 `caf3473` 轮 5 条 P1 闭环核验（逐条机验，不采信自述）

| 上轮项 | 本轮判定 | 证据 |
|---|---|---|
| **U-1** 处置产物路径三方分裂，照 UC-6 实现会永久 HOLD | **VERIFIED 闭环** | `grep -o '\.macao/[^ \`）)、,，]*executor\.disposition\.yml'` 全库（排除 `docs/reviews/`）：除 `UC6:24` 的**归档**路径外，全部为 `.macao/.dispositions/r<round>/`；与 `MACAO_PRD_v2.md:638`、Layer 1c 读取路径 `.macao/.dispositions/r{rnd}/executor.disposition.yml` 一致。归档路径的性质见 §0.1-2 |
| **U-2** AEP Type 字母整体错位一位且用例内部不自洽 | **VERIFIED 闭环** | 用例集内所有 `Type [A-H]` 出现共 4 处：`UC2:51` = Type A、`UC4:7` / `README:45` = Type B、`UC7:25` = Type H，与 `MACAO_PRD_v2.md:350-357` 权威表逐条相符；其余五类只写消息名不写字母，**无错位可能** |
| **U-3** `.review.yml` issue 列表字段名与机器契约不符 | **VERIFIED 闭环** | `README:95`、`UC1-glm:85`、`UC4:40`、`UC4:81` 全部为 `items[]`；`review_manifest.schema.json` 的 `items` 与四条 `allOf` 互锁（vote↔status、YES↔无 BLOCKING、NO↔至少一条 BLOCKING、ABSTAIN↔空 items+`abstain_reason`）实测全部生效 |
| **U-4** UC-8 缺 Pre-merge Evidence Push 校验，两阶段封存顺序倒置 | **VERIFIED 闭环** | `UC8:21` 关卡 1 = Pre-merge Evidence Push 校验（`ls-remote`，fail-closed）；关卡 1..6 与 `MACAO_PRD_v2.md:1480-1489` §14.5 第 1..6 步**逐条对应**；新增 `:65` `E4a_pre` 异常行与 `:77` 验收断言 2。（顺序问题在 PRD §3.3 E4 行仍存在——见设计同步轨 P1-2，不计入本条） |
| **U-13** 两份用例示例通不过其权威契约，其一整体停留 v2.4 | **VERIFIED 闭环** | UC-1-gemini `:126` 现为 `version: "2.5"` + `consensus_rule: "weighted_2/3_v1"`，过 `macao_config.schema.json`；UC-3 `:33` 含 `full_document{path,evidence_commit,sha256}`，过 `dev_manifest.schema.json` |

**5/5 闭环。** 我在上轮登记的 P2×5、P3×3 中，`items[]`、Type 字母、gitignore 9 规则（`UC1-gemini:98` / `UC10:32` / `src/macao/cli/wizard.py:83-92` 三方均为 9）三项亦已收敛。

---

## 三、P1：必须先解决（4 项）

### P1-1　UC-7 自称「触发条件全部枚举闭合」，其中两个触发在 PRD §3.3 无可达的 E7 边；UC-8 关卡 3 把 Git Conflict 明文回环到其中之一

**证据**

`docs/usercases/UC7-human-override.md:10` 标题即「前置条件（接管触发条件，**全部枚举闭合**）」，列 P1–P6；`:31` §2.c 标题为「编排器执行（**确定性映射，PRD §3.3 E7**）」，给出 5 个闭合选项的转移表。

而 `docs/MACAO_PRD_v2.md:859` 的 E7 行，**当前状态**一栏是：

> `HOLD`（`CONSENSUS_CHECK` 或 `REWORK`）

且 `docs/MACAO_PRD_v2.md:867` 明文：「**除本表所列来源外，任何实现不得引入其他状态转移路径**」。

把 UC-7 的六个触发逐一压到转移表上：

| UC-7 触发 | 声明进入态 | E7 可达？ | 实际可用出边 |
|---|---|---|---|
| P1 计票 DEADLOCK | `CONSENSUS_CHECK` | ✔ | 5 选项全可用 |
| P2 `round ≥ max_rework_rounds` | `CONSENSUS_CHECK` | ✔ | 5 选项全可用 |
| **P3 init 无法唯一识别 10 态** | **「init 上下文」** | ✘ | 「init 上下文」不是 10 个业务态之一，转移表无此行；5 个选项（APPROVED/REWORK/RETRY_REVIEW/CANCEL/EXTEND）对 init 无语义 |
| P4 Disposition 超时 | `CONSENSUS_CHECK` | ✔ | 5 选项全可用 |
| P5 执行者声明 `NEEDS_ADMIN` | `CONSENSUS_CHECK` | ✔ | 5 选项全可用 |
| **P6 Git Conflict / MERGING 内不可自动恢复失败** | **`MERGING`** | ✘ | 从 `MERGING` 出发，§3.3 只有 E4a、E4b、E8（→`UNKNOWN`）、E10（→`CANCELLED`）。5 个选项里**只有 `CANCEL` 经 E10 可达**；`APPROVED` / `REWORK` / `RETRY_REVIEW` / `EXTEND` **均无边** |

P6 不是纸面遗漏——`docs/usercases/UC8-merge-signoff.md:33` 关卡 3 明文把它当作正式出口：

> **Git Conflict** → 不自动解冲突……**转 UC-7 P6 管理员裁定**：人工解冲突后按新 commit 走 E4b 增量复审，或 CANCEL。

这句话里给出的两个动作，**没有一个是 E7 的选项**：「按新 commit 走 E4b」是合并流水线自身的失败转移（E4b 由 CI/push/签字失败触发，不由 override 触发），「CANCEL」走的是 E10 而不是 E7。也就是说 UC-8 → UC-7 P6 → 回到流程，这条回路在 §3.3 上不闭合。

同时对照 `docs/MACAO_PRD_v2.md:1105` §6.1 的 `HUMAN_OVERRIDE_TRIGGERS`：它列 **8 个**触发（State ambiguity / Reviewer timeout / Consensus deadlock / Disposition timeout / NEEDS_ADMIN unresolved / Process crash / Git conflict / Unknown state），且**每个触发的 `action` 选项集各不相同**——Disposition timeout 给 4 项（无 RETRY_REVIEW），NEEDS_ADMIN 给 3 项，Process crash 给 `Retry or abandon?`，Git conflict 给 `Resolve conflict manually and continue?`，Unknown state 给 `Reset to last known state?`。UC-7 §2.b 则声明 5 项「**选项闭合，无其他值**」。

于是同一个人工接管决策面存在**三套互不相同的枚举**：PRD §6.1 的 8 触发 × 各自选项集、PRD §3.3 E7 的 2 个合法起态 × 5 选项、UC-7 的 6 触发 × 5 选项。两两取交集：`{P1,P4,P5}` 三个触发同时被三方覆盖，`P2`、`P3` 只在 UC-7，`Process crash`、`State ambiguity`、`Reviewer timeout`、`Unknown state` 只在 §6.1。这是 GUIDELINES §5「唯一权威表」在人工接管面的直接违反。

**影响**：Phase 1 实现 `macao override resolve` 时，从 `MERGING` 收到 `--choice REWORK` 该做什么，三处文档给不出一致答案；照 §3.3「不得引入其他转移路径」的硬约束实现，UC-8 关卡 3 写明的路径**做不出来**，Git 冲突会卡在 `MERGING` 无出口（除非 CANCEL 整个任务）。

**最小闭环**（三选一，任一即可，但必须选一）
- (a) 在 §3.3 增一条 `E7a | MERGING | 命令 | 管理员裁定冲突处置 | REWORK/CANCELLED | ...`，并把 UC-7 §2.c 拆成「CONSENSUS_CHECK/REWORK 起态」与「MERGING 起态」两张映射表；
- (b) 把 UC-7 P6 改写为「不走 E7，冲突由 UC-8 E4b 确定性转 `REWORK`；管理员只在 E4b 之后的 `REWORK` 态介入」，并同步改 `UC8:33`；
- (c) 把 §6.1 的 8 触发与 UC-7 的 6 触发合并为唯一一张表，逐行标注「起态 / 可用 choice 子集 / 对应转移编号」。

无论选哪条，**P3（init 上下文）必须一并处理**：要么明确 init 期的接管走的是 UC-1 h5 的另一套问答（不是 E7），要么从 UC-7 §1 移除。

---

### P1-2　UC-6 / UC-7 缺失验收标准等模板小节，而本申请正是要把用例体系批准为「测试验收的官方操作基准」

**证据**

```bash
for f in docs/usercases/UC*.md; do
  printf "%-38s 验收=%s 后置=%s 自审=%s 异常=%s 落点=%s\n" $(basename $f) \
    $(grep -cE '^## .*验收标准' $f) $(grep -cE '^## .*后置条件' $f) \
    $(grep -cE '^## .*设计自审' $f) $(grep -cE '^## .*异常流' $f) $(grep -cE '^## .*实现落点' $f)
done
```

输出：

```
UC10-existing-project-doctor.md        验收=1 后置=1 自审=1 异常=1 落点=1
UC1-init-gemini.md                     验收=0 后置=0 自审=0 异常=0 落点=0
UC1-init-glm.md                        验收=1 后置=1 自审=1 异常=1 落点=1
UC2-task-create.md                     验收=1 后置=1 自审=1 异常=1 落点=1
UC3-dev-checkpoint.md                  验收=1 后置=1 自审=1 异常=1 落点=1
UC4-review-dispatch.md                 验收=1 后置=1 自审=1 异常=1 落点=1
UC5-consensus-tally.md                 验收=1 后置=1 自审=1 异常=1 落点=1
UC6-issue-triage-rework.md             验收=0 后置=0 自审=0 异常=1 落点=1
UC7-human-override.md                  验收=1 后置=1 自审=0 异常=1 落点=1
UC8-merge-signoff.md                   验收=1 后置=1 自审=1 异常=1 落点=1
UC9-timeout-daemon.md                  验收=1 后置=1 自审=1 异常=1 落点=1
```

`docs/usercases/UC6-issue-triage-rework.md` 的全部小节是 `1. 前置条件` / `2. 主成功场景` / `3. 备选流与异常流` / `4. 实现落点`——**没有「6. 验收标准（可测）」，没有「5. 后置条件」，没有「8. 设计自审」**。UC-7 缺「8. 设计自审」。UC-1-gemini 五项全无（它用的是另一套模板）。

**为什么这是 P1 而不是格式问题**：本申请 §6 的诉求原文是——批准用例体系「作为 Phase 1~5 研发实施与**测试验收**的官方操作基准」。用例的「验收标准（可测）」小节就是这个基准的**唯一载体**：UC-8 §6 有 6 条可注入 fixture 的断言，UC-5 §6 有独裁帽拒绝断言，UC-3 §6 有 sha256 篡改断言。UC-6 承载 D-2（独立 disposition 产物）、D-4（DEFERRED）、D-5（`requires_new_checkpoint` 守卫）、E5a 分流与管理员豁免流——是 v2.5 新增面最集中的一份——**它没有一条可测断言**；`docs/v2.5_CODE_CHANGE_INVENTORY.md:113` 反过来把 `tests/unit/test_review_disposition.py` 的覆盖点写在了变更清单里，方向恰好倒了（测试要点应由用例定义，清单只登记落点）。

UC-7 同理承载 E7 全流程且**恰好是 P1-1 那条断链所在**，它缺的是「设计自审」——本可以自查出 P1-1 的那一节。

**最小闭环**：为 UC-6 补 `5. 后置条件` / `6. 验收标准（可测）` / `8. 设计自审`，为 UC-7 补 `8. 设计自审`。UC-6 的验收标准至少须覆盖：① 遗漏 issue 的 disposition 被拒；② `FINAL` 含 `NEEDS_ADMIN` 被拒（契约侧已有反例 fixture，补上用例侧断言即可）；③ 全 `requires_new_checkpoint=false` → E4，任一 true → E5a；④ `EXEMPTED_BY_ADMIN` 缺 `override_id` 被拒（契约侧已生效，见 §0.1-2）。

---

### P1-3　UC-3 的拓扑子孙守卫在 PRD 与技术变更清单侧无对应（跨轨，与设计同步轨 `claude/DS-P1-3` 为同一条）

**证据**

| 位置 | 守卫强度 |
|---|---|
| `docs/usercases/UC3-dev-checkpoint.md:16` P2 | 「拓扑前进的新 commit（**严格为上轮 `checkpoint_ref` 之子孙**且未被消费）」 |
| `docs/usercases/UC3-dev-checkpoint.md:53` d3 | 「`checkpoint_ref != 上轮 ref` 且 `commit_exists`（**严格为上轮 checkpoint 之拓扑子孙提交**）」 |
| `docs/usercases/README.md:64` | 「返工轮严格要求**拓扑前进**的新 commit（且未被消费）」 |
| `docs/MACAO_PRD_v2.md:858`（§3.3 E6） | 「新 source commit **`!=` 上一轮**」 |
| `docs/v2.5_CODE_CHANGE_INVENTORY.md:85`（E6 守卫） | 「新 commit（**`!= 上轮 checkpoint_ref`**）」 |
| `src/macao/workflow/orchestrator.py:257` | `if not self.git.is_ancestor(prev_ref, latest_commit): return None` |

`!=` 放行上轮 checkpoint 的**祖先**与**另一条分支上的无关 commit**；「子孙」不放行。用例与现有代码取严，权威 PRD 与施工清单取松。

**影响**：本申请把用例体系定位为「Phase 1~5 研发实施……的官方操作基准」，而 Phase 1 的施工图（交付物 #4）在这一点上与用例矛盾，且更松。按清单施工会把 `orchestrator.py:257` 已经存在的 `is_ancestor` 守卫弱化掉；UC-3 §6 验收标准 `:94` 第 1 条只写「新 commit」，没有针对该守卫的反例，弱化不会被测试发现。

**最小闭环**：`MACAO_PRD_v2.md:849`/`:858` 与 `v2.5_CODE_CHANGE_INVENTORY.md:85` 补「拓扑子孙（`is_ancestor`）」；UC-3 §6 增反例断言「提交上轮 checkpoint 的祖先 → E6 拒绝且任务态不变」。

---

### P1-4　UC-8 对「远端不可达」同时给出 fail-closed 拦截与降级成功两种互斥结果

**证据**

- `docs/usercases/UC8-merge-signoff.md:23` 关卡 1：「Orchestrator 通过 `git ls-remote` 校验 `refs/macao/evidence/<task_id>/r<round>` **已成功推送到远端**；若未推送或校验失败，**fail-closed 拦截**，不得进入后续合并步骤」。
- `docs/usercases/UC8-merge-signoff.md:55` 备选流 A3：「**远端不可达**（本地/个人仓库场景） | push 关卡**降级为本地 merge 完成** + 审计 `PUSH_SKIPPED_LOCAL`」。
- `docs/usercases/UC8-merge-signoff.md:17` 前置条件 P3：「target 分支检出成功且与远端不冲突（**或纯本地**）」——明确把无远端场景放进流水线入口。

三句互斥：远端不可达时 `ls-remote` 必然失败，按关卡 1 应当在**第一关**就 fail-closed 拦截、任务不得进入合并；按 A3 与 P3，同一情形应当**一路走到 push 关卡再降级为本地完成**并进 `DONE`。用例没有给出「evidence ref 在纯本地场景如何满足关卡 1」的规则——`refs/macao/evidence/...` 在无远端时根本无处可推。

**影响**：这正是 D-8 两阶段 Push 校验要防的那个洞的镜像面。实现者二选一：选关卡 1 则 A3 的本地场景永远进不了合并（与 P3 的入口声明矛盾）；选 A3 则关卡 1 的 fail-closed 可被「判定为本地场景」绕过——而「是否本地场景」在用例中没有确定性判据（`merge.strategy`、配置项、还是 `ls-remote` 的失败本身？后者会让拦截条件自我豁免）。

**最小闭环**：在关卡 1 补一条显式分支——例如「配置 `project.repository.remote_name` 为空或 `merge.push_policy: local_only` 时，关卡 1 改为校验本地 `refs/macao/evidence/<task_id>/r<round>` 存在；否则一律按远端 `ls-remote` fail-closed」——并把该判据写进 `macao.yaml` 契约与 UC-8 §6 验收标准（现 `:76` 第 1 条的 fixture 矩阵含「Pre-merge 未推送」，但不含「纯本地」）。

**来源**：本条与 Codex `6e35a71` 报告 P1-7 独立收敛；上述三处原文为我本机核对。

---

## 四、P2：登记，Phase 1 前处理（4 项）

| ID | 问题 | 证据 |
|---|---|---|
| **P2-1** | UC-5 §2.b 与纯整数五重门禁**并列**保留浮点「赞成加权占比 = Σ(approve 权重) / 有效权重」，与 D-6「严禁浮点数运算与静默四舍五入」抵触 | `UC5-consensus-tally.md:29-30` 的旁注 vs `:31-35` 的五重门禁。该量在 `vote_result.schema.json` 中**无对应字段**（`vote_breakdown` 八个键全为 integer），在 UC-5 自己引的来源 `UC1-init-glm.md:105-110` 中**也不存在**，决策表也不消费它——是纯残留。诚实说明：见 §0.2，我未能构造数值分歧，故不判 P1。**与 grok P2-5 / qwen P2-5 收敛** |
| **P2-2** | 用例中 4 处指向 PRD 不存在的小节 | `UC2-task-create.md:6` **§11.4**（第十一部分只有 11.1/11.2；tasks 表在 §11.2。同一错误锚点也出现在 `src/macao/workflow/orchestrator.py:268` 的注释里）；`UC4-review-dispatch.md:6`/`:32`/`:57` **§12.5**（第十二部分只有 12.1/12.2；「输出自愈」实际在 §17.2 `ReviewExtractor`）；`UC8-merge-signoff.md:27` 「v1.1 受控门禁**三条件**见 PRD §14.5」——§14.5 全文无此三条件，`rebase_before_merge` 全库只在两处配置示例出现。`UC4:57` 那一处是**备选流 A4 的行为定义**，指向空锚点等于该分支无规范来源 |
| **P2-3** | `min_effective_votes` 在 v2.5 用例中继续流通，但五重门禁不读它 | `UC1-init-gemini.md:167` 的 v2.5 示例仍写 `min_effective_votes: 2`；`UC1-init-glm.md:253` 备选流 A2 指引管理员用 `policy.min_effective_votes` 处理「法定人数风险」。该键在 `macao_config.schema.json:67` 仍被接受，但不属于五重门禁任何一道，`policy_snapshot` 的 required 里也没有。同一个「席位法定人数」于是有两个名字（GUIDELINES §5）。详见设计同步轨 `claude/DS-P1-1` |
| **P2-4** | UC-1-gemini 与其余 12 份用例不同构 | 它使用「1. 基本信息 / 2. 核心主业务流程 / 3. 详细步骤 / 4. 分支流程与异常处理 / 5. 产物规格 / 6. 终端交互界面设计」六节模板，没有验收标准、后置条件、异常流表、实现落点、设计自审中的任何一节（见 P1-2 的表）。UC-1 由两份文档共同承载（`UC1-init-glm.md` 结构完整），故不阻断，但「13 份用例达成 100% 对齐」的口径里包含一份无法验收的文档 |

---

## 五、P3：可延期（4 项）

| ID | 问题 |
|---|---|
| **P3-1** | `UC1-init-glm.md:145-146` 的 `role_view` 表比 PRD §14.2（`MACAO_PRD_v2.md:1454-1466`）多一行「`CONSENSUS_CHECK`（已出具 `admin_override` APPROVED 且待 FINAL）→ `SHOULD_DISPOSE`」。逐格比对：两表共有的 11 行**枚举值完全相同**，差异是用例更细。方向应是 PRD 补齐而非用例删行。**与 grok DS-P2-2 / qwen P2-2 收敛** |
| **P3-2** | 申请 §2 第 5 行称 UC-3 要求返工 commit「**未被消费**」——`UC3:16` P2 确有此语；但申请 §2 第 8 行把 D-7（AEP 8 类消息）的落点写作「UC-6 §2.a」，而 UC-6 §2.a（`:20-21`）只写「读 `vote_result.json` 的 `issues_index`」，全文中 `DISPOSITION_REQUIRED` 仅出现于 `:14` 的前置条件表。落点应改写为「UC-6 §1 P1」 |
| **P3-4** | UC-3 在同一文档内三重复用 `E1`–`E5` 标识 | `:15-19` 用 E1–E5 标**前置条件行**，`:80-84` 用 E1–E5 标**异常流行**，而 PRD §3.3 的 E1–E10 是**全局转移编号**（且 `:6` 与 `:65` 同文引用 §3.3 的 E6）。同一文档内 `E2` 既是「已产生新 commit」的前置条件，又是「无新 commit → 拒绝」的异常行，还是 PRD 里 `READY_FOR_REVIEW → WAITING_REVIEW` 的转移。GUIDELINES §5。**与 Codex P2-1 收敛** |
| **P3-3** | 申请 §4.1 的份数口径不可复现且各方不一：本人实测 `docs/usercases/*.md` = **13**（与申请一致 ✓），但同期 Design-Sync 申请称全库 179 份，我得到 167（`git ls-tree 6e35a71`）/ 172（`find docs`）/ 185（`find -L docs`，跟随 `docs/usecases` 软链），grok 与 qwen 各报 181。0 控制字符的结论各方一致为真 |

---

## 六、GUIDELINES §6 反例库：11/11 可唯一推导（按申请 §5.1 要求逐条核验）

前 4 项由五重门禁纯整数复算，脚本与输出：

```python
import math
def tally(weights, votes, minwin=2):
    N=len(weights); W=sum(weights)
    if any(3*w >= 2*W for w in weights): return "CONFIG_REJECT(独裁帽)"
    eff=[(w,v) for w,v in zip(weights,votes) if v!='ABSTAIN']
    EN=len(eff); EW=sum(w for w,_ in eff)
    if EN < math.ceil(2*N/3): return "DEADLOCK(席位法定人数 %d<%d)"%(EN,math.ceil(2*N/3))
    if EW < math.ceil(2*W/3): return "DEADLOCK(权重法定人数 %d<%d)"%(EW,math.ceil(2*W/3))
    aw=sum(w for w,v in eff if v=='YES'); asz=sum(1 for w,v in eff if v=='YES')
    rw=sum(w for w,v in eff if v=='NO');  rsz=sum(1 for w,v in eff if v=='NO')
    if 3*aw>=2*EW and asz>=minwin: return "APPROVED"
    if 3*rw>=2*EW and rsz>=minwin: return "REWORK_REQUIRED"
    return "DEADLOCK(阈值 aw=%d rw=%d EW=%d asz=%d rsz=%d)"%(aw,rw,EW,asz,rsz)

for n,w,v in [("S1 2人全弃权",[1,1],['ABSTAIN','ABSTAIN']),
              ("S2 1超时+1批准",[1,1],['ABSTAIN','YES']),
              ("S3 1:1 僵局",[1,1],['YES','NO']),
              ("S4 3人 YES/NO/ABSTAIN",[1,1,1],['YES','NO','ABSTAIN']),
              ("S4b 3人 YES/NO/NO",[1,1,1],['YES','NO','NO'])]:
    print("%-24s -> %s" % (n, tally(w,v)))
```

```
S1 2人全弃权              -> DEADLOCK(席位法定人数 0<2)
S2 1超时+1批准            -> DEADLOCK(席位法定人数 1<2)
S3 1:1 僵局               -> DEADLOCK(阈值 aw=1 rw=1 EW=2 asz=1 rsz=1)
S4 3人 YES/NO/ABSTAIN     -> DEADLOCK(阈值 aw=1 rw=1 EW=2 asz=1 rsz=1)
S4b 3人 YES/NO/NO         -> REWORK_REQUIRED
```

| # | 场景 | 唯一推导来源 | 结果 |
|---|---|---|---|
| 1 | 2-reviewer 全部弃权 | 上表 S1；`UC9:41` 明写「全体弃权 $\Rightarrow E_N=0 \Rightarrow$ 必然 DEADLOCK」 | 唯一 |
| 2 | 1 超时 + 1 批准 | 上表 S2；`UC9:36` 超时弃权计入 accounted、不进 $E_N/E_W$ | 唯一 |
| 3 | 1:1 僵局 | 上表 S3；`UC5:41` 决策表 DEADLOCK 行明列「1:1」 | 唯一 |
| 4 | 3-reviewer 1:1:1 | 上表 S4 / S4b 两种读法均唯一 | 唯一 |
| 5 | Reviewer 崩溃重启重复投票 | `UC4:68` E5「f4 去重幂等；崩溃前已消费票不重复计数」 | 唯一 |
| 6 | 同 checkpoint 两份同 `reviewer_id` | `UC4:44` f4 + `:58` A5「去重 + 审计，不双计」，审计码 `REVIEW_DEDUP` | 唯一 |
| 7 | `.dev.yml` 缺必需字段但 `signal=EXPLICIT` | `UC3:53` d1 Schema 校验先于 d2 signal；`dev_manifest.schema.json` required 六键 | 唯一（fail-closed） |
| 8 | 第二轮返工 `.review.yml` 是否覆盖第一轮 | `MACAO_PRD_v2.md:876` ref+round 双匹配；`UC1-glm:152` `STALE` 不改投影；`UC3:72` A2 窗口内取最新 | 唯一（不覆盖） |
| 9 | 人工接管超时默认动作 | `MACAO_PRD_v2.md:1160` 总则 +`UC7:51` §2.f「不得静默按高置信度继续」 | 唯一（HOLD + 升级告警） |
| 10 | Git 冲突致 checkpoint 与工作区不一致 | `UC8:63` E2 `CHECKPOINT_DRIFT` + `:78` 验收 3 | 唯一（不合并 → E4b）。**但后续的管理员介入路径不唯一，见 P1-1** |
| 11 | `review_context` diff 载体不一致 | `MACAO_PRD_v2.md:1031` `diff_policy: generate_locally` + `UC4:28` 「严禁 base64 内联」 | 正文唯一；**契约层不拦，见设计同步轨 `claude/DS-P2-2`** |

**11/11 在正文层可唯一推导**（上轮同为 11/11，无回退）。第 10、11 两项各带一个附注。

---

## 七、交叉文档需做的文字修订（最小闭环清单）

1. `UC7-human-override.md:10` 六触发表 + `:31` §2.c 映射表：按 P1-1 三选一方案改写；`UC8-merge-signoff.md:33` 关卡 3 的「转 UC-7 P6」同步。
2. `UC6-issue-triage-rework.md`：补 `5. 后置条件` / `6. 验收标准（可测）` / `8. 设计自审`；`UC7-human-override.md` 补 `8. 设计自审`。
3. `MACAO_PRD_v2.md:849`/`:858`、`v2.5_CODE_CHANGE_INVENTORY.md:85`：补拓扑子孙守卫；`UC3-dev-checkpoint.md:94` 增反例断言。
4. `UC5-consensus-tally.md:29-30`：删除浮点「加权占比」两行（决策不消费该量）。
5. `UC2-task-create.md:6` §11.4 → §11.2；`UC4-review-dispatch.md:6`/`:32`/`:57` §12.5 → §17.2；`UC8-merge-signoff.md:27` 删除或补齐「三条件」出处。
6. `UC1-init-gemini.md:167` 与 `UC1-init-glm.md:253`：清理 `min_effective_votes`。
7. `MACAO_PRD_v2.md:1454-1466` §14.2：补「override APPROVED 且待 FINAL → `SHOULD_DISPOSE`」行（与 `UC1-glm:146` 对齐）。
8. 申请 §2 第 8 行：D-7 落点「UC-6 §2.a」→「UC-6 §1 P1」。
9. `UC8-merge-signoff.md:23`/`:55`/`:17`：按 P1-4 给出「纯本地场景」的确定性判据，并写进 §6 验收标准的 fixture 矩阵。
10. `docs/usercases/`：补 `reconcile` 分册或在 README 产物表说明其为 `doctor --fix` 的子集（D-9 落点缺口，采纳自 grok P2-3 / qwen P2-3）。
11. `README.md:79`：「提升至 evidence ref」改为与 UC-8 关卡 6 一致的「Post-merge 证据封存」措辞（采纳自 grok P2-4 / qwen P2-4）。

---

## 八、与其他 Reviewer 的交叉核对（GUIDELINES §8）

同基线共四份报告：grok（`YES_APPROVE`，无 P0/P1）、qwen（`YES_APPROVE`，ADVISORY×2）、**Codex（`REJECT`，P1×8，两轨合并出具）**、本报告（`NO_APPROVE`）。票型 **2:2**。

**与 Codex 的独立收敛（2 项，均为阻断级）**

| 我的项 | Codex 的项 | 状态 |
|---|---|---|
| **P1-1** UC-7 六触发中 P6/P3 无 E7 可达边，PRD §6.1 / §3.3 E7 / UC-7 三套枚举 | **P1-6**「UC-7 把不相容的 init 与 MERGING 异常塞进同一五选项，无法确定性执行」 | **独立收敛**。两人从不同入口到达同一处：他从「五选项对两个起态不可执行」切入，我从「§3.3 无对应出边 + UC-8 关卡 3 的回环不闭合」切入。这是本轮用例轨**唯一被两名 reviewer 独立复现的核心阻断项** |
| **P1-4** UC-8 远端不可达的两种互斥结果 | **P1-7** | **独立收敛**，三处原文一致 |

**与 grok / qwen 的收敛（3 项）**

| 项 | 一致情况 |
|---|---|
| 我上轮 5 条 P1 + qwen 6 条 BLOCKING + grok 2 条 P1 全部闭环、无回退 | 四方一致。三方机验路径不同（我走全量围栏×全契约交叉，qwen 走逐条修复点，grok 走反向断言，codex 走未覆盖反例），结论相同 |
| UC-5 残留浮点「加权占比」 | 我 P2-1 = grok P2-5 = qwen P2-5 |
| §14.2 / FAQ 缺 override 后 `SHOULD_DISPOSE` 行 | 我 P3-1 = grok P2-2 = qwen P2-2 |

**我认可对方、本轮自己未查到的（4 项）**

- grok P2-3 / qwen P2-3：**D-9 里的 `reconcile` 在 `docs/usercases/` 零出现**。我复核属实（`grep -rn reconcile docs/usercases/` 无命中），采纳登记。**这是我的漏审**：我在 §三 逐条核 D-x 落点时，D-9 只核到 init/doctor/adopt 就停了，没把四个命令都走一遍。登记为常备检查项——「裁定里的枚举必须逐项而非抽样核落点」。
- grok P2-4 / qwen P2-4：`README.md:79` 仍写合并成功后「全部产物**提升至** evidence ref」，与 UC-8 关卡 6 的 Post-merge 封存措辞不一。复核属实，采纳。
- qwen P2-8：`UC1-init-gemini.md` TUI 示例用 `macao task start`，与 UC-2 的 `task create` 不一致。复核属实，采纳（与我 P2-4 同源）。
- Codex P2-1：UC-3 三重复用 E1–E5 标识。复核属实，已作为 P3-4 登记。

**我提出、四方中只有我给出证据的（2 项）**

| 我的项 | 其余三方 | 我坚持的依据 |
|---|---|---|
| P1-2 UC-6 缺验收标准 / 后置条件 / 设计自审，UC-7 缺设计自审 | 均未涉及 | §三 的 shell 脚本可原样复跑；申请 §6 的诉求原文点名「**测试验收**的官方操作基准」，而承载 D-2/D-4/D-5/E5a/豁免流的 UC-6 没有一条可测断言 |
| P1-3 拓扑守卫四种强度 | 均未涉及 | 六处原文并列可比；`orchestrator.py:257` 是反向证据（现有实现比权威文档严） |

**关于定级差异**：grok 与 qwen 的 YES 基于「前序阻断项 8/8（或 6+2）物理闭环 + 申请 §4 五组自动化声明重放为真」。这两条我**独立复现，结论完全相同**（见 §一 §二），也就是说四方在「已查过的项」上没有分歧。分歧在**查了什么**：本报告四条 P1 落在「用例内部自洽但跨到 §3.3 转移表不可达」（P1-1、P1-4）、「模板完整性 vs 申请的验收基准诉求」（P1-2）、「用例 vs 施工清单的守卫强度」（P1-3）三个方向；Codex 从第四个方向（构造未覆盖反例打契约）切入，独立命中了其中两条。按 GUIDELINES §2.1，L1 的判据是「设计文档之间、与权威基准之间一致」——P1-1、P1-3、P1-4 都是文档之间的不一致，因此我认为它们阻断 PG-0。

## 附：机器票与结构化 issue 索引

`vote`: **`NO_APPROVE`**　`opinion.status`: `CHANGES_REQUESTED`

| issue_id | severity | disposition_class | 摘要 |
|---|---|---|---|
| `claude/UC-P1-1` | critical | `BLOCKING` | UC-7 六触发自称枚举闭合，P6（MERGING）与 P3（init）在 §3.3 无 E7 可达边；UC-8 关卡 3 回环 UC-7 P6 的路径在状态机上不存在；PRD §6.1 / §3.3 E7 / UC-7 三套互不相同的触发与选项枚举 |
| `claude/UC-P1-2` | major | `BLOCKING` | UC-6 缺后置条件/验收标准（可测）/设计自审，UC-7 缺设计自审；申请诉求为把用例批准为测试验收官方基准 |
| `claude/UC-P1-3` | major | `BLOCKING` | UC-3 拓扑子孙守卫在 PRD `:858` 与变更清单 `:85` 侧只写 `!=`，弱于用例与 `orchestrator.py:257` 现有实现 |
| `claude/UC-P1-4` | major | `BLOCKING` | UC-8 对「远端不可达」同时给出关卡 1 fail-closed 拦截（`:23`）与 A3 降级为本地完成（`:55`）两种互斥结果，且无确定性判据区分 |
| `claude/UC-P2-1` | minor | `ADVISORY` | UC-5 §2.b 残留浮点「赞成加权占比」，与 D-6 禁浮点抵触（未能构造数值分歧，故非 P1） |
| `claude/UC-P2-2` | major | `ADVISORY` | 悬空引用：UC-2 §11.4、UC-4 §12.5×3、UC-8「§14.5 三条件」 |
| `claude/UC-P2-3` | minor | `ADVISORY` | `min_effective_votes` 在 v2.5 用例中继续流通，五重门禁不读它 |
| `claude/UC-P2-4` | minor | `ADVISORY` | UC-1-gemini 与其余 12 份模板不同构，五个可验收小节全缺 |
| `claude/UC-P3-1` | minor | `ADVISORY` | UC-1-glm role_view 表比 PRD §14.2 多一行（方向应是 PRD 补齐） |
| `claude/UC-P3-2` | minor | `ADVISORY` | 申请 §2 第 8 行 D-7 落点「UC-6 §2.a」应为「UC-6 §1 P1」 |
| `claude/UC-P3-3` | minor | `ADVISORY` | 文档份数口径不可复现，三名 reviewer 三个数 |
| `claude/UC-P3-4` | minor | `ADVISORY` | UC-3 在同一文档内三重复用 E1–E5 标识（前置条件 / 异常流 / PRD 全局转移编号） |
