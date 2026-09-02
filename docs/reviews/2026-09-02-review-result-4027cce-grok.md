# PRD v2.5 / 用例体系独立评审结论（总入口 `4027cce`）

- **评审日期**：2026-09-02
- **评审人**：grok
- **评审对象**：[`docs/reviews/2026-09-02-review-request-4027cce.md`](2026-09-02-review-request-4027cce.md)（总入口；分轨 [`…-PRD-v2.5-Design-Sync.md`](2026-09-02-review-request-4027cce-PRD-v2.5-Design-Sync.md)、[`…-UseCases-v2.5-Alignment.md`](2026-09-02-review-request-4027cce-UseCases-v2.5-Alignment.md) 一并核验）
- **申请声称基线**：`4027cce`（`fix(governance): resolve all round 2 review findings across schemas, PRD, and usecases`）
- **工作区 HEAD**：`be5ee25`（申请改名 + GUIDELINES/STATUS；PRD/Schema/用例正文与 `4027cce` 一致）
- **前序对象**：`6e35a71`（本人双轨 `YES_APPROVE` / L1；Claude DesignSync P1×5、UseCases P1×4；Codex P1×8 `REJECT`）
- **对齐基准**：`docs/MACAO_REVIEW_GUIDELINES.md` §1–§6、§9、§11；`docs/MACAO_PRD_v2.md`；提案 §2 D-1～D-9；`docs/usercases/PRODUCT-FACTS.md` F-1～F-22
- **定级申请**：L1 DOC-ALIGNED / PG-0（两轨）
- **机器票**：`NO_APPROVE`
- **证据**：`BLOCKING` × 2（P1）；`ADVISORY` × 若干；**无 P0**

**结论：不授予 L1 DOC-ALIGNED / PG-0（两轨均不授予）。** 相对 `6e35a71`，Claude/Codex 多条阻断已真正改掉：E4 关卡顺序与 §14.5 对齐；E7 伴随动作写成 override → `SHOULD_DISPOSE` → FINAL → E4/E5a；E6 与清单补拓扑子孙；disposition 枚举联动与 `issues_index_sha256`；`policy` 根级必填；dev_manifest 核心引用必填；AEP Type A/B/E/H 有 payload 形状；UC-7 收敛为 P1–P4；UC-6/7 补齐 5–8 节。申请 §3 机验本机复跑成立（9/9、13/13、双副本 0 diff、86/86）。

申请「全部阻断项全量物理修复」仍不成立。**D-6 两道反支配门禁在契约层仍可关掉**（Claude DS-P1-1 未闭部分，本机复现可改变计票结果）；本轮为闭合 UC-8 远端/本地而引入的 `remote_name: null` **无法通过 `macao_config` 契约，且权威 PRD §14.5 没有该模式**。两处都会让两套实现接受不同配置或走不同合并边。按 F-17 / GUIDELINES §8，不能投有条件通过。

86/86 **不是** L2。

---

## 0. Reviewer 自审

- 不采信 STATUS「全量阻断闭环」与申请 §1/§4 的 100% 表述。
- 对 Claude `6e35a71` P1 与 Codex P1 按 **现行** `4027cce` 原文+探针逐条复验，不把本人上轮 YES 当作本轮证据。
- **漏审登记**：`6e35a71` 轮本人只查了 `consensus_rule` 枚举封闭，未查 `minimum_winning_seats` 下界与 `dictator_cap_enabled` 开关。Claude 给出可复算反例后，本轮独立复跑成立。属 GUIDELINES §9 模式 A 的近亲（查取值域不查约束下界）。已并入本轮 P1-1。
- 仪器：Draft-07（含 `$ref` store）；控制字符扫描；Schema 双副本；`unittest discover`；`compileall`；计票脚本复算。
- CODE 待实施项 **NOT_APPLICABLE**（L1）。

强制自检：

| # | 项 | 本轮 |
|---|---|---|
| 1 | 字段名 vs 读取路径 | disposition / Layer 1c / E7 主边同句 ✓；**policy 约束下界与 UC-8 `remote_name` 类型不一致** |
| 2 | 「已完成 / 100%」 | 申请 §3 机验 **VERIFIED**；「全部阻断物理闭环」**CONTRADICTED**（P1-1、P1-2） |
| 3 | 确定性用语 | 申请「100%」未标目标 |
| 4 | YAML/JSON 过 Schema | 正例 9/9、UC 三围栏 PASS；**UC-8 规定的 `remote_name: null` 过不了契约** |
| 5 | P1 均附路径 | 是 |

---

## 一、申请 §3 机验（独立复跑）

| 声明 | 本机 | 判定 |
|---|---|---|
| Markdown 控制字符 0 | 扫描 `docs/**/*.md` 192 份 + schemas JSON，控制字节 **0**；`git ls-files '*.md'` **179**（申请写 170/188，计数漂移见 P2） | **结论 VERIFIED** |
| Schema 双副本 0 diff | 8 份 SAME | **VERIFIED** |
| valid 9/9、invalid 13/13 | 9/9 PASS；13/13 REJECTED | **VERIFIED** |
| UC-6 / UC-3 / gemini YAML | 三份 PASS | **VERIFIED** |
| 86/86；compileall 0 | Ran 86 OK，36.9s；compile rc=0 | **VERIFIED** |

---

## 二、上轮阻断闭环（独立，不采信 STATUS）

### 2.1 Claude Design-Sync `6e35a71`

| 项 | 本轮判定 | 证据 |
|---|---|---|
| **DS-P1-1** `policy` 可缺席；反支配门禁可关 | **部分闭环** | `policy` 现为根级 required；缺 `policy` 探针 **REJECTED**。**未闭环**：见本轮 P1-1 |
| **DS-P1-2** E4 关卡顺序与 §14.5 倒置 | **VERIFIED 闭环** | PRD L853：关卡 1 `ls-remote` → 2 检出 → 3 技术合并 → 4 CI → 5 签字 → 6 push。Pre-merge 不再排在检出之后。§14.5 仍把「检出+合并」写在第 2 步、第 6 步为通告（编号不完全 1:1，P2） |
| **DS-P1-3** 返工拓扑四种强度 | **主体闭环** | E6 L858 与清单 L85 均为上一轮 checkpoint 之拓扑子孙 / `git merge-base --is-ancestor`。Layer 1a 仍 `require_new_commit=True`（P2） |
| **DS-P1-4** STATUS 计数 | **不作为 L1 仪器** | 仍自称 115/26；本轮不按其自述定级（P2） |
| **DS-P1-5** disposition 枚举联动 | **VERIFIED 闭环** | `issues_index_sha256` required；`DEFERRED`/`REJECTED`/`EXEMPTED_BY_ADMIN` → `requires_new_checkpoint` const false。探针 `DEFERRED+true` **REJECTED** |

### 2.2 Claude UseCases `6e35a71`

| 项 | 本轮判定 | 证据 |
|---|---|---|
| **UC-P1-1** UC-7 P3/P6 无 E7 边 | **VERIFIED 闭环** | 触发收敛为 P1–P4（均 `CONSENSUS_CHECK`）。init 归 UC-1；Git Conflict → E4b（UC-7 L21、PRD E4b L855 含 conflict、UC-8 关卡 3） |
| **UC-P1-2** UC-6/7 缺标准节 | **VERIFIED 闭环** | 两份均有 §5–§8（后置条件 / 验收 / 落点 / 设计自审） |
| **UC-P1-3** 拓扑子孙（跨轨） | **主体闭环** | 同 DS-P1-3 |
| **UC-P1-4** 远端不可达双结果 | **CONTRADICTED（修复引入新双真源）** | 见本轮 P1-2 |

### 2.3 Codex `6e35a71` P1×8（抽查）

| 项 | 判定 |
|---|---|
| P1-1 AEP per-type + 预算 | **部分闭环**。Type A/B/E/H 有 required payload；Type A 空包与 3000 字符 summary **REJECTED**。**未编码**：信封 16 KiB；`protocol` 仍含 `AEP/1.0`；Type C/D/F/G payload 仍任意。探针 Type C + 50 KiB + `AEP/1.0` **ACCEPTED**（P2） |
| P1-2 `dev_manifest` 核心引用 | **VERIFIED**。required 含 `task_id`/`checkpoint_ref`/`full_document`；缺字段反例拦截 |
| P1-3 `macao_config` 封闭 | **部分闭环**。`policy` 必填、`consensus_rule` 仅 `weighted_2/3_v1`。反支配下界未封（P1-1） |
| P1-4 disposition 联动 | **VERIFIED**（同 DS-P1-5） |
| P1-5 E7 出口 / 单写者 | **VERIFIED**。PRD L859 与 UC-7 L37 同序；禁代写 |
| P1-6 UC-7 init/MERGING 混塞 | **VERIFIED**（同 UC-P1-1） |
| P1-7 UC-8 远端 | **未真正闭环**（P1-2） |
| P1-8 SRS 7 类 | **VERIFIED**。`SRSv1.md:613` 现为 8 类 AEP/1.1 |

本人 `6e35a71` 的 P2（E7 压缩表、§14.2 投影行、`reconcile` 缺分册、AEP 16 KiB）中，E7 压缩表 **已改**；其余仍在。

---

## 三、已对齐 / 已确认项

1. D-1 / D-2 写者边界；DEADLOCK 即时落盘；override 不回写 `vote_result`。
2. E7 `APPROVED`：override → `SHOULD_DISPOSE` → 执行者 FINAL → E4/E5a。Layer 1c 仍读 override+FINAL。
3. E4 伴随动作以 Pre-merge `ls-remote` 为关卡 1。
4. `dev_manifest` / `review_disposition` 必填集与枚举联动可被 Draft-07 执行。
5. UC-7 运行期触发与 §3.3 E7 起态相容；Git Conflict 走 E4b。
6. UC-6/7 模板 5–8 节齐。
7. 9/9、13/13、双副本、86/86 本机为真。

---

## 四、P1：进入实施基线前应修正

### P1-1　D-6 反支配门禁在契约层仍可关闭（Claude DS-P1-1 未闭部分）

申请与 STATUS 写：`macao_config`「强制 `policy` 且封闭为 `weighted_2/3_v1`」。`policy` 缺席已拒。**封闭的是规则名，不是 D-6 的两道硬边界。**

**证据**：

1. 提案 L410：配置期独裁帽「不满足则拒绝启动」。L414：`2 ≤ minimum_winning_seats ≤ N`。FAQ L310：胜方席位 ≥ 2，「禁止单席位独裁裁决」。PRD §13 示例写 `minimum_winning_seats: 2`、`dictator_cap_enabled: true`。
2. `docs/schemas/macao_config.schema.json:74-75`：`dictator_cap_enabled` 仍为任意 boolean；`minimum_winning_seats` 仍 `"minimum": 1`。`vote_result.schema.json:70` 同。
3. 本机构造：`policy.consensus_rule=weighted_2/3_v1`、`dictator_cap_enabled=false`、`minimum_winning_seats=1`，其余 required 齐 → Draft-07 **ACCEPTED**。
4. 复算 Claude 反例（权重 `[5,2,1,1]`，票面 YES/ABSTAIN/NO/NO，独裁帽本身合法）：`minimum_winning_seats=1` → **APPROVED（胜方席位 1）**；`=2` → **DEADLOCK**。契约放行的配置会改变机器决策。
5. `min_effective_votes` 现为 policy **必填**，但五重门禁不读它；UC-1-gemini L167 仍写该键。GUIDELINES §5：同一席位法定人数两个名字。

`schemas/README.md`「跨项规则归运行时」不适用：`"minimum": 2` 与 `"const": true` 都是单键 Draft-07 约束。

**验收**：两份 Schema 将 `minimum_winning_seats.minimum` 改为 **2**；`dictator_cap_enabled` 改为 `const: true` 或删除该键并同步 PRD §13 / 清单「选项」措辞；`min_effective_votes` 删除或标明 v2.5 废止且 Loader 忽略；补反例 fixture（`minwin=1`、`dictator_cap_enabled=false`）。

### P1-2　UC-8「纯本地 `remote_name: null`」无法配置，且与 PRD §14.5 互斥（本轮修复引入）

为闭合 Codex P1-7 / Claude UC-P1-4，UC-8 拆出远端 fail-closed 与纯本地跳过 `ls-remote`。拆完之后三份权威材料仍不是同一条边。

**证据**：

1. UC-8 L23–24、L56：纯本地模式 = `repository.remote_name: null`；关卡 1 只查本地 ref；关卡 6 跳过远端 push。
2. `macao_config.schema.json:16-19`：`remote_name` **必填**且 `type: string, minLength: 1`。`review_context.schema.json` 同样。本机 `remote_name: null` → **`None is not of type 'string'`**。合法 `macao.yaml` **表达不了** UC-8 的本地模式。
3. PRD §14.5 L1482 关卡 1 **无**本地豁免：一律 `ls-remote` 校验已推送到远端。L853 E4 伴随动作同。正文零命中 `remote_name: null` / 「纯本地」。
4. 推演：按 Schema 实现 → 不存在本地模式，无 remote 的仓库永远配不出合法 yaml。按 UC-8 实现 → 接受 null 并跳过 fail-closed。按 PRD §14.5 实现 → 即使有人写了 null 仍要 `ls-remote`。三种下一动作。

**验收**：三选一并写进 Schema + PRD §14.5 + UC-8 同一句。若保留本地模式：`remote_name` 改为 `string | null`（或省略键），§14.5 关卡 1 写明 `null` 时只验本地 ref；补正例/反例 fixture。若取消本地模式：删除 UC-8 L24/A3，远端不可达一律 E4b。

---

## 五、P2 / P3

| ID | 级 | 问题 |
|---|---|---|
| P2-1 | P2 | AEP：Type C/D/F/G 仍任意 payload；`AEP/1.0` 仍合法；信封 16 KiB 未进契约。Type C + 50 KiB 探针 ACCEPT |
| P2-2 | P2 | PRD §14.2 仍无「override APPROVED 且待 FINAL」→ `SHOULD_DISPOSE`（UC-1 h2 已有） |
| P2-3 | P2 | Layer 1a 仍 `require_new_commit=True`；E6/清单已写拓扑子孙 |
| P2-4 | P2 | §14.5 六步把合并并进第 2 步、第 6 步为通告；E4 行把技术合并列为关卡 3。顺序起点已对齐，编号未对齐 |
| P2-5 | P2 | `docs/usercases/` 仍无 `reconcile`（D-9） |
| P2-6 | P2 | README L79 仍写合并后「提升至」evidence ref |
| P2-7 | P2 | 申请 md 计数 170/188 vs 本机 `git ls-files` 179 / glob 192；钉钉 `4027cce` vs HEAD `be5ee25` |
| P2-8 | P2 | Design-Sync 分轨申请 §1 仍写「阻断在 `6e35a71` 闭环」；UseCases 分轨申请 §1 仍只提 `caf3473`/`5583bdd`，未列 Claude/Codex `6e35a71` 项 |
| P2-9 | P2 | `EXECUTIVE_SUMMARY.md` 仍标权威基准 v2.3 |
| P3-1 | P3 | STATUS 作为交付物 #9 的计数仍不可复算；不按其自述定级 |

---

## 六、建议闭环顺序

1. **P1-1**：Schema 下界与 `const`（约数行）+ 两份反例 fixture。
2. **P1-2**：要么契约承认 `null` 并改 §14.5，要么删 UC-8 本地模式。
3. P2-1 可与 L2 同期把 16 KiB / 禁 1.0 收进信封。
4. 更新 STATUS 登记本报告。不要用 9/9、13/13、86/86 代替 D-6 下界与 `remote_name` 类型对账。

闭合后再评 **L1 / PG-0**。在 `minimum_winning_seats` 下界改为 2 之前，Loader 不得把 Schema 默认值当成 D-6。在三份材料写死本地模式之前，不得按 `remote_name: null` 跳过 Pre-merge fail-closed。

---

## 七、机器票与 issue 索引

| issue_id | severity | disposition_class | 摘要 |
|---|---|---|---|
| `grok/P1-1` | major | `BLOCKING` | D-6：`minimum_winning_seats` 契约下界仍为 1、`dictator_cap_enabled` 可 false；复算可单席位 APPROVED（Claude DS-P1-1 未闭） |
| `grok/P1-2` | major | `BLOCKING` | UC-8 `remote_name: null` 被 `macao_config` 拒绝，且 PRD §14.5 无本地豁免（本轮修复引入的三真源） |

`vote`: `NO_APPROVE`
