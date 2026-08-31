# PRD v2.5 全文档体系同步（Design-Sync）L1 复审结论

- **评审日期**：2026-09-01
- **评审人**：qwen（独立评审）
- **评审对象**：`2026-09-01-review-request-PRD-v2.5-Design-Sync.md`，钉死提交 `0bc6247`（范围：该提交全量文档变更，12 文件 1049+/871-）
- **评审级别**：L1 DOC-ALIGNED / PG-0（v2.5 实施基线准入）；CODE/TEST 为 NOT_APPLICABLE（实施前文档轮）
- **对齐基准**：`docs/PRD_CHANGE_PROPOSAL_v2.5.md` DRAFT v0.3、`docs/usercases/PRODUCT-FACTS.md` F-1~F-22、GUIDELINES §1–§6/§9/§11
- **结论**：**不予 L1 DOC-ALIGNED / PG-0。** 同步工作量与质量总体很高——D-1~D-9 九项裁定在 PRD/SRS/FAQ/UC/清单中绝大部分物理落地（§一逐项实证），13/13 示例可解析；但存在 **2 项 P1 级 SPEC 矛盾**：①§3.4 场景推演三整段未迁移，与 §3.3 新 E3/E7 语义直接冲突；②`review_disposition` 契约在权威 PRD 中无定义章节，且生命周期枚举跨文档分裂（提案 `FINAL|PENDING_ADMIN` vs UC-6/清单 `DRAFT|FINAL`），申请 §3 两处"在 PRD §6.1 定义"的闭环声明被证伪。均为单点可修。

---

## 一、属实闭环核验（独立逐项取证）

| 声明项 | 独立核验 | 判定 |
|---|---|---|
| PRD 升版 v2.5 + 零语义创作 | 文首标题/理念/地位声明已更新；"文档地位：权威基准"条款在位 | ✅ |
| **Kimi P1-1** E3 全席位 accounted | §3.3 E3 行（L789）"所有配置席位已响应或被持久化 timeout 纳入 accounted"+ 超时行（L790）`source: timeout` 不提前截断 | ✅ |
| **Kimi P1-2** DEADLOCK 即时落盘 | §2.3 判定规则、§3.3 E3 行、§3.4 生命周期行（L817"计票完成即时落盘"）、UC-5 L85/L95 一致 | ✅（冲突残留见 §二-1） |
| **Kimi P0-1** E7 豁免机制 | §3.3 E7 行：源态 HOLD（CONSENSUS_CHECK/REWORK）、5 选项（含新增 EXTEND）、`exempt_issue_ids`、独立 `admin_override.json` + `override_id`、严禁回写 vote_result | ✅ |
| **Grok P1-2** 角色视图 | §14.2 `SHOULD_DISPOSE`/`NOTIFY_EXECUTOR_DISPOSE`/HOLD→`ASK_ADMIN`（L1498-1499）；UC-1 L152 同表 | ✅ |
| **Gemini P1-1 / D-6** 加权五重门禁 | §2.3 纯整数五门禁公式逐条复核无误（独裁帽 `3w_i<2W`、双 quorum、胜方阈值、最少席位）；§2.2 三值票+`abstain_reason`+Schema 互锁（BLOCKING⇔NO_APPROVE、ABSTAIN⇔空 items）；FAQ Q15 同文复述一致 | ✅ |
| **Qwen 0042dc3 轮 / D-2** 双写废除 | `issues_summary` 仅存于"废除声明"语境（PRD L1529、UC-5 L86/L96 移除说明）；FAQ Q15 重写为两产物物理分离表 | ✅ |
| Evidence Ref 迁移 | §2.2 写入约定（严禁 source branch）、§3.4 生命周期 4 行、§5.2/§5.4 canonical+inbox+staging、SRS 头部重定义 6 行、清单 §2.4 两阶段 push（禁本地假回滚） | ✅ |
| E5a/E6 守卫 | E5a 行（L795）+ E6 行（L796：前轮 FINAL disposition 覆盖 + 新 commit≠上轮）；UC-6 E4/E5a 判定规则一致 | ✅ |
| AEP/1.1 框架 | §2.4 八类消息表 + 16384/2048 预算 + 超限拒绝禁截断（缺 payload 规格见 §三） | ⚠️ 部分 |
| 示例可解析性 | PRD 全文 13 个 YAML/JSON 块 `safe_load/json.loads` **13/13 通过** | ✅ |
| 代码变更清单 | `v2.5_CODE_CHANGE_INVENTORY.md`：6 模块 + 5 阶段排期，与 PRD v2.5 逐条同构（E3~E7 守卫、DEADLOCK 落盘、两阶段 push、测试矩阵覆盖加权边界/E5a/E6/豁免）；状态诚实标注"已冻结待实施" | ✅ |

## 二、P1 阻断项（SPEC 矛盾，L1"交叉引用不矛盾"判据未满足）

### P1-A §3.4 场景推演三未迁移——与 §3.3 新语义直接冲突

- **证据**：`MACAO_PRD_v2.md:855` 步骤 5 仍写"**不写 `vote_result.json`**，`CONSENSUS_CHECK` HOLD"——与 L789 E3 行"即时落盘不可变 `vote_result.json`（decision: DEADLOCK）"**直接矛盾**；步骤 6a-6d（L856-859）仍写"裁定落盘**终局 vote_result**（resolution=human_override）"——与 L797 E7 行"记录独立 `admin_override.json`、vote_result 不可变"**直接矛盾**；尾注（L863）更引用旧 Schema 语义为权威（"`resolution: human_override` 的终局 vote_result 由 Schema 强制"）；同段消息编号"Type G"与 E3 行"Type H"不一致
- **定性**：提案 §9.1 明确预警"不得只改前述四处"，此段即漏网；申请 §4"不存在歧义转移分支""100% 语义对齐"声明被证伪。实施者按此段编码将复现旧双写者缺陷
- **修复面**：重写场景推演三步骤 5/6a-6d + 尾注（约 10 行），对齐 DEADLOCK 即时落盘 + admin_override.json 语义

### P1-B `review_disposition` 契约在权威 PRD 中无定义，生命周期枚举跨文档分裂

- **证据 1（缺失）**：全文检索 `review_disposition` 仅得 6 处**引用**（流程图/阶段表/E4 守卫/角色表/写者表/变更记录），**无任何章节定义**其信封字段、决定枚举、覆盖率规则、状态生命周期与超时——而提案 §4.3 有完整契约、§9.1 要求其并入 PRD
- **证据 2（分裂）**：提案 v0.3 §4.3 规则 5 "`status` 只有 `FINAL | PENDING_ADMIN`"+ `artifact_revision` 递增模型 ↔ UC-6:32 与清单 §2.1 "`DRAFT | FINAL`"——**三处文档两套枚举**，且 `PENDING_ADMIN`/`artifact_revision` 在 PRD/UC/清单中零出现
- **证据 3（闭环声明失实）**：申请 §3"Kimi P1-3（NEEDS_ADMIN 闭环）在 PRD §6.1 与 UC-6 明确"、"Grok P1-1（disposition 超时 30m）在 PRD §6.1 定义"——实测 §6.1 触发器表 6 项中**无** disposition 超时与 NEEDS_ADMIN 条目（仅 AEP 表 L383/角色表 L1499 顺带提及）；`timeouts` 配置例（L1434-1440）亦无 `review_disposition` 键（30m 仅见于 §3.2 阶段表一栏，无配置锚点；清单 §2.2 config 行同样遗漏）
- **修复面**：PRD 增补 disposition 契约小节（字段/枚举/覆盖/超时/NEEDS_ADMIN 回路），统一枚举（建议 `DRAFT|FINAL` 并同步提案，或反之）；§6.1 补触发器；配置例补键

## 三、P2/P3 登记

| 级 | 项 |
|---|---|
| P2 | **F-20 待定项未解析**：PRODUCT-FACTS F-20 原文仍为"必须由后续规范显式裁定"（提案 §9.2 承诺"v2.5 接受后解析为独立 disposition"未兑现）——L1 事实基线含未决锚点 |
| P2 | §2.4 `DISPOSITION_REQUIRED` **无信封格式节**（现有 Type A~G 七节，第 8 类缺 payload 规格，提案 §10.1 要求"增加其 payload"）；引言"全部 7 个消息类型/5-7 为信封级/适用于全部 7 类"三处措辞残留（已 8 类） |
| P3 | §6.1 死锁触发器选项枚举缺 `EXTEND`（§3.3 E7/§14.2 均为 5 选项） |
| P3 | FAQ Q13 项目符号（L275"执行者汇总问题清单…是否采纳"）表述贴近旧方案语感，建议改指 disposition（Q15 已清晰，影响轻微） |
| P3 | 评审过程观察：`0042dc3` 同行报告文件在评审窗口内多次出现/消失（未跟踪态抖动）——建议评审期冻结注册表写入 |

## 四、定级判定

**不予 L1 DOC-ALIGNED / PG-0。**

- L1 判据核对：示例可解析 ✓、确定性用语合规 ✓、字段对照大体一致 ✗（P1-A 场景段、P1-B 枚举分裂）——"交叉引用不矛盾"未满足
- 两项 P1 均为**单点文档修复**（~30 行量级），不涉及架构方向；修复后可快速复审。建议同批捎带 §三 P2（F-20 解析 + DISPOSITION_REQUIRED 信封节）
- **代码基线不受影响**：按提案 §13.4，v2.3.1/v2.4 行为在实施验收前保持不变；本轮 REJECT 仅阻断"以 0bc6247 文档体系为实施基线"
- 与申请自评差异：§4 两项自检声明（无歧义分支/100% 对齐）被 §二证伪；§3 八行闭环表中 6 行属实、2 行（Kimi P1-3、Grok P1-1 的"§6.1"落点）失实

## 五、对账与自审记录

- 交付物 10 项全部通读（PRD 703 行变更逐节抽验 + 清单 154 行全文 + UC-1/5/6 差异 + SRS 头部 + FAQ Q13/Q15 + STATUS）
- 加权公式、E3~E7/E5a/E6 守卫、示例解析为本人独立复核；行号引用均指 `0bc6247` 版本
- 独立性声明：评审窗口内 `0bc6247-{claude,codex,grok}` 同行报告出现后消失，**未读取任何内容**；本结论全部出自一手文档核验
- 利益相关：本人系 0042dc3 轮 L1 授予方——本轮不因前轮授予而放宽；P1-B 的提案侧（v0.3 枚举）与 PRD 侧（沉默）均有责任，修复建议以 PRD 权威条款为准
- 未覆盖：代码实施正确性（NOT_APPLICABLE）；win32
