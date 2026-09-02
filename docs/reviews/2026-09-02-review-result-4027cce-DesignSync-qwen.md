# PRD v2.5 Design-Sync 复审（基线 `4027cce`）评审结论

- **评审日期**：2026-09-02
- **评审对象**：`docs/reviews/2026-09-02-review-request-4027cce-PRD-v2.5-Design-Sync.md`；受审基线 **`4027cce`**（HEAD `be5ee25` 交付物内容与之一致）
- **评审人**：`qwen`（独立评审；前两轮本人均投 APPROVE，本轮发现新证据后改判——全部以可复现探针为准，不因前票惯性维持）
- **机器票**：**`NO_APPROVE`**
- **结构化 issue**：`BLOCKING` × 5（P1）、`ADVISORY` × 4

---

## 1. 前序轮阻断闭环核验（独立复验）

| 项 | 复验 | 判定 |
|---|---|---|
| Claude DS-P1-2：E4 关卡顺序与 §14.5 倒置 | `§14.5` 第 1 步 = Pre-merge `ls-remote` 校验，检出第 2 步 | ✅ CLOSED |
| Claude DS-P1-5 / Codex P1-4：disposition 枚举联动 | `issues_index_sha256` 必填；`DEFERRED`/`REJECTED`+`requires_new_checkpoint=true` 反例实测拦截 | ✅ CLOSED |
| Codex P1-2：`.dev.yml` 核心引用必填 | `dev_manifest` required 含 `task_id`/`checkpoint_ref`/`full_document`；反例 `dev_missing_core_fields` 实测拦截 | ✅ CLOSED |
| Codex P1-3：`macao_config` 封闭 | `policy` 根级必填（`macao_config_missing_policy` 实测拦截）、`consensus_rule` 仅 `weighted_2/3_v1` | ✅ 部分（未闭环部分见 B-4） |
| Codex P1-8：SRS 7 类 | `SRSv1.md:613` 已为 8 类 AEP/1.1 | ✅ CLOSED |
| Codex P1-1：AEP per-type payload | Type A/B 空 payload 反例实测拦截；**未闭环部分见 B-2** | 部分 |
| Codex P1-5：E7 出口 / 单写者 | PRD `:859` E7 伴随动作与 UC-7 两步路径同序、禁代写 | ✅ 主体（残留见 B-3） |
| Codex P1-6/7 | 同 UseCases 轨报告 §1 | ✅ / ✘（变形） |

## 2. BLOCKING（P1，全部本机复现）

### B-1　PRD 正式示例与刚收紧的 Schema 五处失配（复现 5/5 REJECT）

用 `docs/schemas/` 权威契约（含 `$ref` store）校验 `MACAO_PRD_v2.md` 正式代码块：

| PRD 示例 | 契约 | 实测 | 缺字段 |
|---|---|---|---|
| `:372` Type A | `aep_envelope` | REJECT | `payload.specification_summary` |
| `:403` Type B | `aep_envelope` | REJECT | `review_context.evidence` |
| `:537` Type E | `aep_envelope` | REJECT | `vote_result_ref`（示例写 `vote_result`） |
| `:642` §2.5 disposition | `review_disposition` | REJECT | `issues_index_sha256` |
| `:1370` §13 `macao.yaml` | `macao_config` | REJECT | `version`（及 policy 全组字段） |

申请把用例体系定位为"测试验收官方基准"，而 PRD 自身的正式示例通不过其权威契约，实施者将得到两套字段命名（如 `vote_result` vs `vote_result_ref`）。

### B-2　AEP 16 KiB / 2048 字节预算未在契约层实施（部分复现）

- **复现**：契约仅用 `maxLength`（Unicode **字符**计数）。探针：单字段 2048 个"中"（6144 UTF-8 字节）**ACCEPTED**；多字段组合总包 **33,767 字节 > 16384** 仍 **ACCEPTED**——PRD `:359-362` 承诺的"16384 字节总量 / 2048 字节内联 / 收发双向拒绝"在契约层不存在。
- **与 Codex 报告的差异（如实记录）**：Codex 称 Type C/D/F/G `payload: {}` 被接受；本机探针四类均 **REJECTED**（且新增 `aep_type_a/b_empty_payload` 反例实测拦截）。该子项判定为**已闭环**，不采信原表述；未闭环的是字节语义与总包预算。

### B-3　E7/E9 源态冲突与提案"直接推进至 MERGING"残留

- `MACAO_PRD_v2.md:859` E7 源态为 `HOLD(CONSENSUS_CHECK 或 REWORK)`，`RETRY_REVIEW → 触发 E9`；但 `:860` E9 源态仅 `CONSENSUS_CHECK`——从 `REWORK` HOLD 选 `RETRY_REVIEW` 无边可达。
- `PRD_CHANGE_PROPOSAL_v2.5.md:135` 仍写"通过 E7 转移**直接**推进至 `MERGING`"，与 PRD `:859`、UC-7 `:35` 的两步路径（override → `SHOULD_DISPOSE` → 执行者 FINAL → E4/E5a）冲突，同一管理员选择可推出两种状态机。
- **修正**：固定 E7 源态 × choice 矩阵；提案 :135 删除"直接"表述并对齐两步路径。

### B-4　D-6 防支配门禁契约层可关（与 UseCases 轨 B-2 同源）

`dictator_cap_enabled: false` + `minimum_winning_seats: 1` 探针 **ACCEPTED**；与提案 `:39`、`UC5-consensus-tally.md:76/87`、`UC1-init-glm.md:108` 的强制性表述矛盾。详见 UseCases 轨报告 §2 B-2。

### B-5　仓库根 `macao.yaml` 被自家契约拒绝（与 UseCases 轨 B-1 同源）

根配置 10 处校验错误、`consensus_rule` 仍 `2/3_majority`；叠加 `remote_name: null`（UC-8 本地模式）不被契约接受。详见 UseCases 轨报告 §2 B-1。

## 3. ADVISORY（P2/P3）

- **A-1（P2）**：Codex P2-1：disposition 反向引用冻结 `vote_result`（path/evidence_commit/sha256）仍只有一个任意 `issues_index_sha256`，无 `vote_result_ref` 字段，运行时跨产物比对不可表达。
- **A-2（P2）**：实现层 AEP 仍 1.0（`envelope.py:14`、`types.py` 缺第 8 枚举、`test_msg_bus.py` 断言 1.0）——非 L1 交付物，但 86 项回归不能证明 v1.1；Phase 1 必闭环。
- **A-3（P3）**：申请文档计数（188/170）在受审 commit 不可复现（本机 `git ls-files '*.md'` 与树内实计均不符），应固定计数命令与口径。
- **A-4（P3）**：§14.5 五步与 UC-8 六关卡编号非 1:1（语义已一致），建议映射注记。

## 4. 申请 §3 自动化声明复核

控制字符 0、9/9 正例、13/13 反例、双目录 0 diff、86/86、compileall 0——**全部本机重放为真**。但 §1"全部阻断项彻底闭环"不成立（B-1~B-5）。

## 5. 定级意见

核心契约库与用例轨的大部分前序阻断确已真实闭环，本轮整改质量显著；但 B-1（PRD 正式示例 5/5 失配）与 B-2~B-5 均为"文档/契约不能唯一推出实现"的 L1 级缺陷，其中 B-4/B-5 直接动摇 D-6 裁定与配置单一事实源。

**结论：`NO_APPROVE`，不授予 L1 DOC-ALIGNED / PG-0，Phase 1~5 准入暂不成立。** 修复后单提交复审，验收标准：
1. §2 B-1 表中 5 个示例全部过对应契约（或契约字段命名裁定后同步）；
2. AEP 字节预算可执行（UTF-8 字节语义 + 总包 16384 + 正反例含 CJK 边界）；
3. E7 源态 × choice 矩阵唯一，提案 :135 对齐两步路径；
4. `dictator_cap_enabled=false`/`minimum_winning_seats=1`/`remote_name=null` 三探针与文档语义一致；
5. 根 `macao.yaml` 过 `macao_config.schema.json`。

## 6. Reviewer 自审记录

- **改判声明**：本人 `6e35a71` 轮两轨 APPROVE 存在两处漏审——① 对 `macao_config` 只验证枚举封闭与根级必填，未探约束下界/开关闭包（漏 B-4）；② 未对"修复新增的本地模式"做契约可表示性探针、未用新收紧的 Schema 回验 PRD 自身示例（漏 B-1/B-5）。已按 GUIDELINES §9 登记漏审模式，本轮全部以探针补验；
- 对同基线 Codex（REJECT P1×5）/Grok（NO_APPROVE P1×2）报告逐条独立复现；其中 Codex P1-2 的"空 payload 被接受"子项**未能复现**，按实证改判为已闭环，未随原报告引用；
- 无利益冲突；本报告的复现脚本均可由报告内命令重建。
