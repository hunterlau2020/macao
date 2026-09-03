# PRD v2.5 设计同步轨复审（基线 `cd285dd`）评审结论

- **评审日期**：2026-09-03
- **评审人**：qwen（独立评审）
- **评审对象**：`2026-09-03-review-request-cd285dd-PRD-v2.5-Design-Sync.md`，钉死 `cd285dd`（HEAD `6746294` 仅增申请/STATUS）
- **结论**：**不授予 L1 DOC-ALIGNED / PG-0（轨 A）。** 本人 a0123e8 轮 3 项 P1 与 A-1 **全部实质闭环**（逐项独立探针验证）；但独立复现 **1 项新 P1**：仓库根 `macao.yaml`（PRD §13 钦定配置单一事实源）被本轮新落地的语义门禁**拒绝**——活配置与门禁承诺直接矛盾（与 grok 同判）。
- **结构化 issue**：`BLOCKING` × 1（P1）、`ADVISORY` × 3（P2×1 / P3×2）

## 1. 前序轮（a0123e8）本人阻断闭环核验（全部独立探针）

| 项 | 独立复验 | 判定 |
|---|---|---|
| B-1' 权重算术/独裁帽无语义校验 | `ConfigManager.load` 实测：权重 `100/1/1`（300≥204）→ **Dictator cap violation 拒绝**；`5/1/1`（15≥14）→ 拒绝；`seat_quorum=1`/`weight_quorum=1` → 拒绝；**合法 `2/1/1` + 调整后 quorum=3 → 接受**（无过度拦截）。语义校验落 `schema.py:113-157` + `config.py`，Draft-07 不做算术属正确分工；三份新反例 fixture 接入 `test_schema.py:344-346` | ✅ CLOSED |
| B-2' `vote_result_ref` 非必填 | `required` 已含 `vote_result_ref`；去掉该字段 → **REJECTED**；正例 fixture 含完整三要素；提案 §4.2 与 PRD §2.5 示例同备 | ✅ CLOSED |
| B-3' E7 "或 REWORK" 残留 | 提案 §4.5 E7 行与清单 L85 均已为 `HOLD (CONSENSUS_CHECK)`；`或 REWORK` 全文档 0 命中；提案 :218 超时停驻态对齐 `CONSENSUS_CHECK` | ✅ CLOSED |
| A-1 AEP 未封闭/嵌套预算逃逸 | 8 类 payload `additionalProperties: false` ×18 处；Type E 六项必填在位；**递归字节预算实测**：嵌套 3000 字符 ASCII 字段 → 拒绝；嵌套 700 个"中"（2100 字节 > 2048）→ 拒绝（多字节字节级计数成立） | ✅ CLOSED |

## 2. BLOCKING（P1，独立复现）

### P1-1　仓库根 `macao.yaml` 被本轮门禁拒绝——配置单一事实源自相矛盾

- **复现**：根配置 4 席 reviewer、`seat_quorum_required: 2`、`weight_quorum_required: 2` → `validate_config` **REJECTED：seat_quorum_required (2) is less than required minimum ceil(2N/3) = 3**；`ConfigManager.load` 同拒
- **定性**：PRD §13 把该文件定为配置单一事实源；本轮申请 §1.1 宣称"配置期语义校验全套落地"，落地的门禁立即拒绝仓库自己的活配置——闭环声明对活配置被证伪（申请 §3 机验 93/93 不含活配置校验，属口径遗漏）。本人 a0123e8 B-5"根配置合法"的闭环在本轮**回退**
- **修正**：根 `macao.yaml` 双 quorum 提至 ≥3（或席位调整），并把"活配置过 `validate_config`"纳入测试套件（与 grok 同判）

## 3. ADVISORY（P2/P3）

- **A-1（P2，跨层登记）**：codex 三项代码层差距（`ConsensusEngine` 人数浮点计票未读权重、`APPROVED` 无 `DISPOSITION_REQUIRED`/无条件 E4、超时弃权来源不入票面）——均属 **L2/Phase 1 实施域**，清单已排期；不阻断本轮 L1 文档判定，但为下轮 L2 的当然阻断项，登记备查（本人对"以代码未实装阻断 L1 文档定级"不采信：GUIDELINES L1/L2 判据分层，实施顺序见提案 §10.2）
- **A-2（P3）**：申请"126 份结论报告"计数与受审树实计仍存在口径差（计数问题第四轮复发）
- **A-3（P3）**：§14.5 五步与 UC-8 六关卡编号映射注记（连续四轮登记）

## 4. 机验复核

93/93 OK、`compileall` 0、fixtures **10/10 正例 + 20/20 反例**（其中 3 份 quorum/独裁反例经语义层拒绝，本人核得 `test_schema.py:344-346` 接线；两层合计 20/20 属实）、`docs/schemas` ↔ `src/macao/schemas` JSON 零漂移——**申请 §3 机验全部为真**；失实仅在 §1.1"配置期硬门禁闭环"对活配置的适用性（§2）。

## 5. 定级意见

**不授予本轨 L1**：唯一阻断为根配置与门禁的自相矛盾（单点修复：改两个数字 + 补活配置测试）。本人上轮全部阻断已确认闭环，修复面为历轮最窄。与面板关系：与 grok（P1×1）一致不授予；codex（P1×3，均代码层）分歧登记见 A-1。预计单轮闭环后可授予。

## Reviewer 自审记录

- 本轮对 B-1' 同时构造合法/非法两侧探针（`2/1/1`+quorum=3 接受），确认无过度拦截——上轮"锁覆盖范围穷举"纪律的对称执行
- A-1 嵌套预算探针含多字节字符（700"中"=2100 字节）专项，覆盖 codex 上轮"字节级"要求的边界
- 对 codex 代码层 P1 维持"L1/L2 分层"立场（连续两轮），不因 REJECT 阵营人数而改变判定口径
- 根配置反例为本人在收到 grok 报告前已列入必测项（B-5 回归检查），发现后与其独立证据互证
- 未覆盖：win32、Phase 1 实现
