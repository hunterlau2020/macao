# PRD v2.5 Design-Sync 独立评审结论（Round 2，`6e35a71`）

- **评审日期**：2026-09-02
- **评审人**：grok
- **评审对象**：[`docs/reviews/2026-09-02-review-request-PRD-v2.5-Design-Sync-r2.md`](2026-09-02-review-request-PRD-v2.5-Design-Sync-r2.md)
- **申请声称基线**：`6e35a71`
- **工作区 HEAD**：`12a05e2`（仅新增申请文件 + STATUS；PRD/Schema/提案/清单/用例正文与 `6e35a71` 一致）
- **前序对象**：`2da1bc2`（本人 `NO_APPROVE`，P1×3：配置枚举、UC-6 示例结构、E7 FINAL 写者）；更早 `0bc6247`（P0 识别入口，已在后续提交闭环）
- **对齐基准**：`docs/MACAO_REVIEW_GUIDELINES.md` §1–§6、§9、§11；`docs/usercases/PRODUCT-FACTS.md` F-1～F-22；提案 §2 D-1～D-9
- **定级申请**：L1 DOC-ALIGNED / PG-0（v2.5 实施基线）
- **机器票**：`YES_APPROVE`
- **证据**：`BLOCKING` × 0；`ADVISORY` × 若干；**无 P0、无 P1**

**结论：授予 PRD v2.5 设计同步轨 L1 DOC-ALIGNED / PG-0。** 相对 `2da1bc2`，三条 P1 均已在后续差量（含 `caf3473` / `6e35a71`）真正改掉：`consensus_rule` 仅 `weighted_2/3_v1`；UC-6 示例为 `executor` 对象且过 Schema；E7 `APPROVED` 经 override → 执行者 FINAL → E4，Layer 1c 消费该边。申请把 Qwen 旧评语与「用例阻断彻底闭环」写进背景，**不采信**；本票只凭本机对照原文与机验。

L1 允许据此开始编码/PoC。86/86 **不是** L2：v2.5 计票、E5a、`admin_override` 命令路径在清单中仍为待实施。`storage/evidence.py` 标「新建」且仓库中不存在，与清单一致。

---

## 0. Reviewer 自审

- 不采信申请 §1 引用的他方「9/9 物理闭环」与 STATUS 自述。
- 对本人 `2da1bc2` 三条 P1 与 `0bc6247` P0-1 按 **现行** `6e35a71` 正文重读。
- 用例轨同日另文 [`2026-09-02-review-result-6e35a71-UseCases-grok.md`](2026-09-02-review-result-6e35a71-UseCases-grok.md)；本轨交付物 #8 为全量用例，结论与该文一致（授予 L1，P2 登记），不重复展开每一分册。
- 仪器同用例轨。CODE 待实施项 **NOT_APPLICABLE**。

强制自检：

| # | 项 | 本轮 |
|---|---|---|
| 1 | 字段名 vs 读取路径 | §2.5 / Schema / UC-6 / Layer 1c 同构；§14.2 投影表滞后于 UC-1（P2） |
| 2 | 「已完成 / 100%」 | 申请 §3 机验 **VERIFIED**（计数 179 vs 实测 181 为 P2）；「彻底闭环」对 P1 **VERIFIED** |
| 3 | 确定性用语 | §3.1 仍标设计目标值 |
| 4 | YAML/JSON | 正例 8/8、反例 7/7、UC 三围栏 PASS |
| 5 | P1 均附路径 | 本轮无 P1 |

---

## 一、申请 §3 机验（独立复跑）

| 声明 | 本机 | 判定 |
|---|---|---|
| 179 份 Markdown 0 控制字符 | `docs/**/*.md` **181** 份 + schemas JSON，控制字节 **0** | **结论 VERIFIED**；份数 **PARTIALLY**（P2-7） |
| UC-6 / UC-3 / gemini YAML | 三份 PASS | **VERIFIED** |
| valid 8/8、invalid 7/7、双副本 0 diff | 8/8、7/7、8×SAME | **VERIFIED** |
| 86/86；compileall 0 | Ran 86 OK；compile 0 | **VERIFIED** |

HEAD vs `6e35a71` 文件差：两份 r2 申请 + `STATUS.md`。评审对象钉 `6e35a71` 正文。

---

## 二、上轮 grok（`2da1bc2`）阻断闭环

| 上轮项 | 本轮判定 | 证据 |
|---|---|---|
| **P1-1** `consensus_rule` 仍接受 `2/3_majority` | **VERIFIED 闭环** | `docs/schemas/macao_config.schema.json:66` 枚举仅为 `weighted_2/3_v1`。探针 `'2/3_majority' is not one of ['weighted_2/3_v1']` |
| **P1-2** UC-6 示例无 `executor` 对象 / A2 写者含糊 | **VERIFIED 闭环** | 抽出 YAML 过 `review_disposition.schema.json`；A2 L75 执行者写 `EXEMPTED_BY_ADMIN`+`override_id` |
| **P1-3** E7 `APPROVED` FINAL 写者不能唯一推出 | **VERIFIED 闭环** | Layer 1c L776–790 读 override+FINAL；场景 6a / 6a-1；UC-7 L35；提案 §4.2 第 2 条已删代签。详见用例轨报告 §二 |

更早 `0bc6247` **P0-1**（Layer 1b/1c / 场景三仍为 v2.3.1）：**仍闭环且本轮加固**。Layer 1b 全席位 `accounted == configured`；Layer 1c 三值决策；DEADLOCK 现额外消费合法 override。场景三步骤 5 即时落盘 DEADLOCK。

`2766c69` Claude/Codex 历史项（抽查，非采信申请 §4 旧文）：

| 项 | 判定 |
|---|---|
| 五重门禁公式控制字符 | **VERIFIED**（全库扫描 0） |
| `vote_result.decision` 三值 | **VERIFIED**（枚举无 `RETRY_REVIEW`/`CANCELLED`；负例拦截） |
| `FINAL`+`NEEDS_ADMIN` | **VERIFIED**（负例拦截） |
| `review_context` 必需块 | **主体 VERIFIED**（`required` 10 键，含 `required_blocks` 字段定义；无 `content_base64`） |
| AEP 16 KiB 进信封 Schema | **未闭环，保持 P2**（payload 任意 object；协议枚举仍含 `AEP/1.0`） |
| UC-9 超时 ABSTAIN 口径 | **VERIFIED**（计入 accounted，不进 $E_N$/$E_W$） |
| 清单路径 | **VERIFIED**。`fsm.py` / `state_engine.py` 存在；`storage/evidence.py` 标新建且文件不存在 |

提案 §4.3 信封示例现为 `disposition_status` / `dispositions[]` / `disposition_type`，与 PRD §2.5 / Schema 同构（上轮 PARTIALLY 的字段三套在示例层已收敛）。

---

## 三、交付物清单（申请 §2）逐项

| # | 交付物 | 判定 |
|---|---|---|
| 1 | PRD v2.5 | **DOC/SPEC 主体 VERIFIED**。D-1～D-9 写入正文；§2.5 信封；Layer 1c 含 DEADLOCK+override+FINAL；场景三 6a-1。E7 压缩表与 §14.2 滞后为 P2 |
| 2 | Schema 库 | **VERIFIED**（L1 仪器）。配置封闭、decision 三值、disposition 守卫。16 KiB 未编码为 P2 |
| 3 | 提案 v0.3 | **VERIFIED**。§2 九行权威编号；§4.2 第 2 条禁代写。第 3 条「直接推进 MERGING」带 FINAL 守卫，略压缩（P2） |
| 4 | 代码变更清单 | **VERIFIED** 与模块树对齐；`evidence.py` 新建标注正确 |
| 5 | SRS | 头部映射抽查存在；非本轮主证据 |
| 6 | FAQ | Q12 有 `SHOULD_DISPOSE` 通项，缺 override 后专行（P2，与 §14.2 同源） |
| 7 | PRODUCT-FACTS | F-20 写 D-1/D-2 落实。本文件仍声明「不表示现行实现已满足」 |
| 8 | 全量用例 | 与用例轨报告一致：**授予 L1**，P2 见该文 |
| 9 | STATUS | **实时登记表，不是对齐证据**。本轮不按其「已闭环」句定级 |

未列入清单但跨文档：`docs/EXECUTIVE_SUMMARY.md` 仍自称权威基准 **v2.3**（P2-8）。

---

## 四、GUIDELINES §6 / 声明矩阵（本轨）

| 场景 | 能否从现行 PRD+Schema 唯一推出 |
|---|---|
| 全同意、无 issue | E4 直接 `MERGING`（Layer 1c `APPROVED` 且非 `requires_disposition`） |
| `APPROVED` 有 issue | 等 FINAL；全 false → E4；任一 true → E5a |
| 1:1 / DEADLOCK | 即时落盘 HOLD；E7 写独立 override；`APPROVED` 后等执行者 FINAL（Layer 1c） |
| 显式弃权 / 超时弃权 | 计入 accounted；不进有效分母（UC-9 / D-3） |
| 接管超时 | 保持 HOLD，不静默继续（UC-7 §2.f） |
| 未推送 evidence | UC-8 关卡 1 / §14.5 第 1 步 fail-closed |
| `YES_APPROVE` 含 BLOCKING | 提案 §3.1 / F-17：不得表示有条件通过 |

「N/3 多数」已由 D-6 纯整数五重替代；独立复算（N=3、W=4、2 YES + 1 NO）仍成立。Layer 2/3 仍只预警不改态。

---

## 五、已对齐 / 已确认项

1. D-1：三值 `decision`；DEADLOCK 即时落盘；override 不回写 `vote_result`。
2. D-2 / D-5：§2.5 信封 + 精确覆盖 + 必填布尔；E4/E5a 只认 `FINAL`。
3. D-6：公式可复制；配置契约不再放行 `2/3_majority`。
4. D-7：8 类 Type A–H；Type E 在 PRD 有完整 JSON 示例；fixture `AEP/1.1`。
5. D-8：evidence ref 不改 source `checkpoint_ref`；§14.5 含 Pre-merge `ls-remote`。
6. D-9：命令在 PRD §14.2 / 清单中；init/doctor 有用例；`reconcile` 缺用例分册（P2，不否定 PRD 有该命令）。
7. `role_view` 含 `SHOULD_DISPOSE` / `NOTIFY_EXECUTOR_DISPOSE`（PRD L1464；UC-1 另有 override 后行）。
8. Schema 双副本一致；fixture 正反例双向；86 测试绿。**不**证明 v2.5 引擎已实现。

---

## 六、P0 / P1

无。进入编码时必须以 **Layer 1c** 为识别入口，不得按 §3.3 E7 压缩句在无 FINAL 时转移。

---

## 七、P2 / P3

| ID | 级 | 问题 |
|---|---|---|
| P2-1 | P2 | §3.3 E7「APPROVED → E4」压缩；E4 自身条件与 Layer 1c 已要求有 issue 时 FINAL。实现锁 Layer 1c。 |
| P2-2 | P2 | §14.2 统一角色视图无「override APPROVED 待 FINAL」行；与 UC-1 h2 不一致。清单 `compute_role_view` 描述同样未写该行。 |
| P2-3 | P2 | AEP 16 KiB / 禁 1.0 未进 `aep_envelope.schema.json`（沿用 `2da1bc2` P2）。 |
| P2-4 | P2 | Layer 1c 未把「全部 BLOCKING 已 `EXEMPTED_BY_ADMIN`」写成伪代码条件（场景 6a-1 有文字）。 |
| P2-5 | P2 | 提案 §4.2 第 3 条「直接推进 MERGING」与「须 FINAL 豁免守卫」同句，略冲。 |
| P2-6 | P2 | 用例目录无 `reconcile`（D-9）。 |
| P2-7 | P2 | 申请称 179 份 md；实测 181。控制字符结论为真。HEAD `12a05e2` vs 钉钉 `6e35a71`。 |
| P2-8 | P2 | `EXECUTIVE_SUMMARY.md` 仍写权威基准 v2.3（未列入本申请交付物，跨文档漂移）。 |
| P3-1 | P3 | `review_context.required_blocks` 为可选数组，与「10 必需块」叙事需在实现时按 `required` 十键而非该数组。 |

与用例轨重叠的 P2（README「提升 evidence」、UC-5 加权占比旁注、gemini `task start`）以用例报告为准，本轨不重复编号。

---

## 八、建议闭环顺序（不阻断本票）

1. Phase 1 编码：识别入口抄 Layer 1c；`override resolve --choice APPROVED` 只落盘 override 并投影 `SHOULD_DISPOSE`。
2. 文档下一差量：E7 伴随动作与 §14.2 投影行与 UC-1 对齐；信封 Schema 收 16 KiB；摘要文档改 v2.5 或标明过期。
3. STATUS 登记本报告。勿把 L1 写成「规范已实现」。

---

## 九、机器票与 issue 索引

| issue_id | severity | disposition_class | 摘要 |
|---|---|---|---|
| `grok/DS-P2-1` | minor | `ADVISORY` | E7 压缩「APPROVED → E4」 |
| `grok/DS-P2-2` | minor | `ADVISORY` | §14.2 缺 override 后 `SHOULD_DISPOSE` |
| `grok/DS-P2-3` | minor | `ADVISORY` | AEP 信封未编码 16 KiB / 仍接受 1.0 |
| `grok/DS-P2-4` | minor | `ADVISORY` | Layer 1c 未编码 BLOCKING 全豁免 |
| `grok/DS-P2-5` | minor | `ADVISORY` | 提案 §4.2.3「直接推进」压缩 |
| `grok/DS-P2-6` | minor | `ADVISORY` | 用例无 `reconcile` |
| `grok/DS-P2-7` | minor | `ADVISORY` | md 计数 179 vs 181；SHA 漂移 |
| `grok/DS-P2-8` | minor | `ADVISORY` | 执行摘要仍标 v2.3 |

`vote`: `YES_APPROVE`
