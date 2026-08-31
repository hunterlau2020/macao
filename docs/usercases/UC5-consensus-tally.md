# UC-5 共识计票（E3 → `vote_result.json`）

- **设计日期**：2026-09-01
- **设计人**：glm
- **状态**：用例设计稿（待实现；实现前须过 Schema/测试对账）
- **关联**：PRD v2.4 §2.3（vote_result）、§3.3（E3/E4/E5）；FAQ Q15；UC-1 h0(2)(3)（问题目录 + 加权规则）；`VoteAggregator`/`ConsensusEngine`；GUIDELINES §2.1（L1–L4 判据外部评审用，本用例只算票）。
- **边界声明**：编排器**无模型**：计票是确定性函数（加权 2/3 + 席位法定人数 + 独裁帽）；`issues_index` **原样拼接**各信封索引，不合并同类项、不标采纳；僵局 HOLD 问**管理员**（UC-7），不问执行者。

---

## 1. 前置条件

| # | 条件 | 不满足时的行为 |
|---|---|---|
| P1 | 任务 `WAITING_REVIEW`（或超时降级完成，UC-9） | E1 |
| P2 | 当前 ref/round 有效票 ≥ `minimum_quorum`（含超时 ABSTAIN 票） | E2（交 UC-9） |
| P3 | 每张票已过 UC-4 f1–f4（Schema/上下文/去重） | 该票剔除，审计 |

## 2. 主成功场景

### a. 收敛触发

E3 产物型转移 `WAITING_REVIEW → CONSENSUS_CHECK`；收集本轮全部合法 `.review.yml`（含超时席位由 UC-9 注入的 `ABSTAIN`）。

### b. 加权计票（确定性，UC-1 h0(3)）

- 每席位读 `vote`（三值）与 `macao.yaml` 的 `vote_weight`（静态政策，默认 1）
- **有效权重** = 未弃权席位权重和（弃权不进分母）
- **赞成加权占比** = Σ(approve 权重) / 有效权重；反对同理
- **双门槛**：占比 ≥ 2/3 **且** 未弃权席位数 ≥ `⌈2N/3⌉`（N=配置席位数）
- **独裁帽**：配置校验期已保证任一席位权重 < 2/3 Σweight（否则 `validate_config` 拒绝启动）

决策表（唯一）：

| 结果 | 条件 | decision |
|---|---|---|
| `APPROVED` | 赞成双门槛达标 | → E4 → UC-8 |
| `REWORK_REQUIRED` | 反对双门槛达标 | → E5（round < max）或 E7 |
| `DEADLOCK` | 其余一切（含 1:1、全弃权） | → HOLD，不写盘，发 `HUMAN_OVERRIDE_REQUEST` → UC-7 |

### c. 生成 `vote_result.json`（三段式，UC-1 h0(2)）

1. **计票段**（编排器算）：各席位 `reviewer/vote/weight`、加权合计、`decision`、`decision_confidence`
2. **`issues_index`**（编排器**复制**）：逐信封拼接 `{id, reviewer, severity, summary, full_document{path,sha256}}`；id 保留 reviewer 前缀；**不合并、不改写、不排序去重**
3. **不写采纳**：`next_step.issues_to_fix.description/suggestion` 由编排器代写的旧字段**废止**（UC-1 h0 决议）；采纳清单是 UC-6 执行者产物
   `summary.critical/major/minor_issues` 仅允许对信封已声明 severity 计数求和。

### d. 落盘与转移

DEADLOCK → **不写** `vote_result.json`（PRD §3.3 E3：不提前写决策未定文件），HOLD 于 `CONSENSUS_CHECK`；其余 → Schema 校验（fail-closed）后落盘，按 decision 走 E4/E5；审计 `CONSENSUS_TALLIED`（票面快照 + 权重快照）。

### e. 通知

agmsg ping：E4 → 管理员（`SIGNOFF_OR_MERGE`）+ 全员结果通告（decision + `vote_result.json` 路径）；E5 → 执行者（`REWORK_REQUEST`，round+1，ping 附 `issues_index` 路径与全文路径，**不附编排器归纳**）。

## 3. 备选流

| # | 场景 | 行为 |
|---|---|---|
| A1 | 权重全 1 | 退化为现行决策表（2/3 席位多数），行为与既有测试一致 |
| A2 | 部分席位 ABSTAIN | 弃权不进分母；法定人数按未弃权计；全弃权 → DEADLOCK |
| A3 | `resolution: human_override`（E7 终局） | UC-7 裁定后由裁定路径落盘终局 `vote_result.json`（UC-9/超时弃权票随终局一并写入） |
| A4 | `require_signoff` 与 decision | 计票只产 decision；签字是 UC-8 流水线步骤，不在本用例 |

## 4. 异常流

| # | 场景 | 行为 |
|---|---|---|
| E1 | 状态非 `WAITING_REVIEW` | 不计票（产物生命周期窗口，PRD §3.4）；旧轮票不得重复消费 |
| E2 | 票数不足 | 不进 CONSENSUS_CHECK；交 UC-9 守护（催票/超时降级） |
| E3 | 生成的 vote_result 未过 Schema | `raise`（fail-closed，现行 `generate_vote_result` 行为）；不落盘不转移 |
| E4 | 权重配置违反独裁帽 | `validate_config` 期拒绝（不进入运行期）；运行期发现 → HOLD + 审计 `POLICY_VIOLATION` |

## 5. 后置条件

- **成功**：`vote_result.json` 落盘且 Schema 合法（DEADLOCK 除外——HOLD）；审计含票面与权重快照；`issues_index` 与各信封逐条可对账（id/ sha256 一致）。
- **失败**：任务态停留 `CONSENSUS_CHECK`（HOLD）或回 `WAITING_REVIEW`；无半成品文件。

## 6. 验收标准（可测）

1. 决策表全场景：全同意、1:1、1 赞 1 反 1 弃、全弃权、加权 2:1:1 各组合 → decision 唯一可推出；DEADLOCK 不落盘（断言文件不存在）
2. `issues_index` 与 fixture 信封逐条零差集；编排器产物无 description/suggestion 代写字段
3. 独裁帽：权重 5:1:1:1 配置 → `validate_config` 拒绝
4. 权重只作用于总票：单条 issue 不因权重被增删（对账断言）
5. 编排器路径无 LLM 调用；同一票面重算结果幂等

## 7. 实现落点

| 位置 | 变更 |
|---|---|
| `src/macao/consensus/engine.py` + `vote.py` | 加权计票、双门槛、三段式 vote_result、issues_index 原样拼接 |
| `src/macao/core/schema.py` | `vote_result` Schema：`issues_index`、`weights`、废止 `issues_to_fix` 正文代写 |
| `src/macao/core/config.py` | `vote_weight` 校验 + 独裁帽 |
| `tests/` | 第 6 节 |

## 8. 设计自审

- 计票 ≠ 采纳 ≠ 评审结论（FAQ Q15）：三段边界在本用例与 UC-6 间显式切开
- 僵局问管理员不问执行者（自裁禁令，GUIDELINES §8"真理不等于投票"的对偶：投票也不等于真理）
- 遗留决策点：①`decision_confidence` 语义（建议 = 赞成加权占比，纯算术）；②权重公示格式（是否入审计正文）
