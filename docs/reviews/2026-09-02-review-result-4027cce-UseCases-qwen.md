# 全量用例体系（UseCases）PRD v2.5 对齐复审（基线 `4027cce`）评审结论

- **评审日期**：2026-09-02
- **评审对象**：`docs/reviews/2026-09-02-review-request-4027cce-UseCases-v2.5-Alignment.md`；受审基线 **`4027cce`**（HEAD `be5ee25` 仅改名申请文件与 STATUS/GUIDELINES，交付物内容与 `4027cce` 一致，已逐文件比对确认）
- **评审人**：`qwen`（独立评审；对同基线 Codex/Grok 未提交报告的全部阻断逐项独立复现，不直接采信）
- **机器票**：**`NO_APPROVE`**（PRODUCT-FACTS F-17：机器票不得为有条件通过）
- **结构化 issue**：`BLOCKING` × 2（P1）、`ADVISORY` × 3

---

## 1. 前序轮阻断闭环核验（独立复验）

`6e35a71` 轮 Claude（P1×4）与 Codex（P1×8）中属用例轨的项，本机复验结果：

| 项 | 复验 | 判定 |
|---|---|---|
| Claude UC-P1-1 / Codex P1-6：UC-7 五选项塞入 init 与 MERGING 不相容起态 | `UC7-human-override.md:10-14` 触发条件收敛为 P1~P4（均 `CONSENSUS_CHECK` 系）；`:69` E1 拒绝非接管态调用；init 归 UC-1、Git Conflict 归 E4b | ✅ CLOSED |
| Claude UC-P1-2：UC-6/UC-7 缺验收等模板小节 | 两份均含 §5~§8 四节（实测计数各 4） | ✅ CLOSED |
| Claude UC-P1-3 / Codex P1-2 跨轨：拓扑子孙守卫 | `MACAO_PRD_v2.md:858` E6 与清单均为"上一轮 checkpoint 之拓扑子孙" | ✅ CLOSED（主体） |
| Codex P1-8：SRS AEP 7 类 | `SRSv1.md:613` 已为"统一为 8 类 AEP/1.1 消息" | ✅ CLOSED |
| Claude P3-1：PRD §14.2 投影表缺 `SHOULD_DISPOSE` 行 | `MACAO_PRD_v2.md:1464` 已补 | ✅ CLOSED |
| Codex P1-7 / Claude UC-P1-4：UC-8 远端不可达双结果 | **修复引入新矛盾** → 见 §2 B-1 | ✘ OPEN（变形） |

本人 `caf3473` 轮 6 项与 `5583bdd` 轮 Grok 2 项的闭环状态维持前轮结论，未发现回退。

## 2. BLOCKING（P1，本轮新复现）

### B-1　UC-8 纯本地模式无法由机器契约表达，且仓库根配置自身不合法

- **证据 1（复现探针）**：`UC8-merge-signoff.md:24/56` 把纯本地模式定义为 `repository.remote_name: null`；`macao_config.schema.json` 的 `project.repository.remote_name` 为必填非空 `string`。将合法正例 `macao_config.yaml` 的 `remote_name` 改为 `null` 后 `Draft7Validator` 判 **REJECTED（None is not of type 'string'）**。UC-8 声称支持的模式在单一事实源中不可表示。
- **证据 2（复现探针）**：仓库根 `macao.yaml` 按现行 `macao_config.schema.json` 校验得 **10 处错误**（缺 `version`/`dictator_cap_enabled`/`minimum_winning_seats`/两个 quorum；`consensus_rule` 仍为 `2/3_majority`）。项目自己的现行配置被自家契约拒绝，`init`/merge 消费方取不到唯一合法配置。
- **证据 3**：PRD §14.5 合并流水线无本地模式分支（关卡 1 恒为远端 `ls-remote`），UC-8 的本地分支在权威基准中无对应。
- **后果**：同一用例按两种实现会接受不同配置、走不同合并边；照契约实现则 UC-8 A3 分支永不可达。
- **修正**：二选一并三处同步——若支持本地模式，Schema/ConfigManager 允许显式 `null`（不得回填 `origin`），PRD §14.5 补本地分支；若不支持，删除 UC-8:24/56 本地分支。无论何种，更新根 `macao.yaml` 至合法 v2.5 配置。

### B-2　D-6 两道防支配门禁在契约层可被关闭（跨轨，同步计入 Design-Sync 轨）

- **证据（复现探针）**：`macao_config.schema.json` 中 `policy.dictator_cap_enabled` 为普通布尔（**可取 `false`**），`minimum_winning_seats` 下界为 `minimum: 1`（**可取 1**）。将正例改为 `dictator_cap_enabled: false` + `minimum_winning_seats: 1` 后 **ACCEPTED**。
- **冲突基准**：提案 `:39` D-6 将独裁帽与"胜方席位 ≥ 2"定义为 `weighted_2/3_v1` 的构成性门禁；`UC5-consensus-tally.md:76/87` 明文"权重配置违反独裁帽 → `validate_config` 期拒绝"；`UC1-init-glm.md:108` 五重门禁并列为必要条件。契约却允许配置关掉其中两道——用例的"拒绝"承诺与该配置合法并存，不能唯一推导。
- **修正**：`dictator_cap_enabled` 删除或 `const: true`；`minimum_winning_seats` `minimum: 2`（若允许管理员加严，只能向上不能低于裁定下界）。

## 3. ADVISORY（P2/P3，不阻断但须登记）

- **A-1（P2）**：Codex P1-3 指出实现层仍为 AEP/1.0（`src/macao/msg/envelope.py:14` `PROTOCOL="AEP/1.0"`、`core/types.py` 无 `DISPOSITION_REQUIRED` 枚举、`tests/test_msg_bus.py` 断言 1.0）。L1 交付物不含源码，不作为本轮阻断；但意味着 86 项回归**不能证明** AEP/1.1 已切换，Phase 1 必须闭环并补双向兼容测试。
- **A-2（P3）**：申请与受审提交的文档计数均不可复现（申请称 13 份用例跟随软链扫描，实测 `docs/**/*.md` 194 份含未跟踪报告；应固定"受审 commit 树内计数"命令）。
- **A-3（P3）**：UC-8 六关卡与 PRD §14.5 五步编号不完全 1:1（语义顺序已一致），建议加编号映射注记。

## 4. 申请 §4 自动化声明复核

| 声明 | 本机 | 判定 |
|---|---|---|
| 13 份用例 0 控制字符 | 全库扫描 0 | ✅ |
| UC-6/UC-3/UC-1-gemini 示例过契约 | 三块复跑 PASS | ✅ |
| fixtures valid 9/9、invalid 13/13 | 实测 9/9 + 13/13（含新增 `aep_type_a/b_empty_payload`、`dev_missing_core_fields`、`disposition_deferred/rejected_with_new_checkpoint`、`macao_config_missing_policy`，全部拦截） | ✅ |
| 双 Schema 目录 0 diff | ✅ | ✅ |
| 86/86、compileall 0 | ✅ | ✅ |

**自动化声明全部为真，但 §1 背景中"全部阻断项已完成全面物理闭环"不成立（B-1/B-2）。**

## 5. 定级意见

前序用例轨阻断确已大部分真实闭环（含本人前两轮全部项），但 B-1 使一条用例分支在契约下不可达、B-2 使两条裁定门禁在契约下可关闭——均为"按文档无法唯一推出实现行为"的 L1 级缺陷。

**结论：`NO_APPROVE`，不授予 L1 DOC-ALIGNED / PG-0。** 修复 B-1/B-2 并回归后单提交复审；验收标准：① `remote_name: null` 探针与 UC-8 文本、PRD §14.5 三者一致（或本地分支删除）；② 根 `macao.yaml` 过 `macao_config.schema.json`；③ `dictator_cap_enabled=false`/`minimum_winning_seats=1` 探针被拒。

## 6. Reviewer 自审记录

- 与本人 `6e35a71` 轮 APPROVE 的差异：本轮对 `macao_config` 只查了 `consensus_rule` 枚举与根级 `required`，未查约束下界与开关闭包，漏掉 B-2；对"新增本地模式"只核了文字自洽，未做配置可表示性探针，漏掉 B-1。已按 GUIDELINES §9 登记模式（查取值域不查下界；新增分支只做文本核不做契约探针）；
- 对 Grok/Codex 同基线报告逐条独立复现后才引用；对 Codex"Type C/D/F/G 空 payload 被接受"一项**未能复现**（现行 Schema 已拒绝，见 Design-Sync 轨报告），未予采信。
