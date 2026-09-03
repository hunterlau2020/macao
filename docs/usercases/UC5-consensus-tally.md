# UC-5 共识计票（E3 → `vote_result.json`）

- **设计日期**：2026-09-01
- **设计人**：glm
- **状态**：用例设计稿（待实现；实现前须过 Schema/测试对账）
- **关联**：PRD v2.5 §2.3（vote_result）、§3.3（E3/E4/E5/E5a）；FAQ Q15；UC-1 h0(2)(3)（问题目录 + 加权规则）；`VoteAggregator`/`ConsensusEngine`；GUIDELINES §2.1（L1–L4 判据外部评审用，本用例只算票）。
- **边界声明**：编排器**无模型**：从各 `.review.yml` **原样摘录** `vote`，加权 2/3 + 席位法定人数 + 独裁帽写出 `decision`（执行者不写此字段，只做后续汇总，见 UC-6 / FAQ Q15 / PRODUCT-FACTS F-13）；`issues_index` **原样拼接**各信封索引，不合并同类项、不标采纳；僵局 HOLD 问**管理员**（UC-7），不问执行者。

---

## 1. 前置条件

| # | 条件 | 不满足时的行为 |
|---|---|---|
| P1 | 任务 `WAITING_REVIEW`（或超时降级完成，UC-9） | E1 |
| P2 | 当前 ref/round 所有配置席位已 accounted（收到合法 manifest 或被持久化 timeout 纳入 accounted 集合） | E2（交 UC-9） |
| P3 | 每张票已过 UC-4 f1–f4（Schema/上下文/去重） | 该票剔除，审计 |

## 2. 主成功场景

### a. 收敛触发

E3 产物型转移 `WAITING_REVIEW → CONSENSUS_CHECK`；收集本轮全部合法 `.review.yml`（含超时席位由 UC-9 注入的 `ABSTAIN`）。

### b. 加权计票（确定性，UC-1 h0(3)）

- 每席位读 `vote`（三值）与 `macao.yaml` 的 `vote_weight`（静态政策，默认 1）
- **有效权重** = 未弃权席位权重和（弃权不进分母）
- **赞成加权占比** = Σ(approve 权重) / 有效权重；反对同理（该占比仅用于展示与 `decision_confidence` 报告量，不参与任何门禁判定）
- **加权五重门禁（纯整数）**：
  1. 配置期独裁帽：$\forall i, 3w_i < 2W$
  2. 席位法定人数：$E_N \ge \lceil 2N/3 \rceil$
  3. 权重法定人数：$E_W \ge \lceil 2W/3 \rceil$
  4. 胜方权重门槛：$3W_{win} \ge 2E_W$
  5. 胜方最少席位：胜方席位数 $\ge 2$

决策表（唯一）：

| 结果 | 条件 | decision |
|---|---|---|
| `APPROVED` | 赞成通过加权五重门禁 | → E4（无改码需求）或 E5a（需改码） |
| `REWORK_REQUIRED` | 反对通过加权五重门禁 | → E5（round < max）或 E7 |
| `DEADLOCK` | 其余一切（未达法定人数、1:1、全弃权） | → 即时写盘不可变 vote_result（decision=DEADLOCK），发 `HUMAN_OVERRIDE_REQUEST` → UC-7 |

### c. 生成 `vote_result.json`（Orchestrator 单一写入、不可变产物）

1. **计票与策略快照**：各席位 `reviewer/vote/weight/source`、纯整数 `policy_snapshot`、`vote_breakdown`、`decision`、`resolution`
2. **`issues_index`**（编排器**原样复制**）：逐信封拼接 `{issue_id, reviewer, disposition_class, severity, title, full_document}`；**不合并、不改写、不排序去重**
3. **内容处置与采纳彻底外置**：`vote_result.json` 仅声明 `requires_disposition: boolean`。具体逐项处置由 Executor 写入独立按轮隔离的 `executor.disposition.yml`（见 UC-6）
4. 不可变单写保证：落盘后由 Orchestrator 即时提升至 evidence ref，严禁任何后续覆盖或回写。

### d. 落盘与转移

所有计票场景（含 DEADLOCK）均即时落盘 `vote_result.json`；DEADLOCK 进入 HOLD 于 `CONSENSUS_CHECK`；其余若 `requires_disposition=true` 发送 `DISPOSITION_REQUIRED`（HOLD）等待 Executor 处置；处置完成后按 decision + `requires_new_checkpoint` 走 E4/E5a/E5；审计记录 `CONSENSUS_TALLIED`。

### e. 通知

agmsg ping：E4 → 管理员（`SIGNOFF_OR_MERGE`）；E5 / E5a → 执行者（`REWORK_REQUEST`，round+1）；DISPOSITION → 执行者（`DISPOSITION_REQUIRED`）。

## 3. 备选流

| # | 场景 | 行为 |
|---|---|---|
| A1 | 权重全 1 | 退化为标准 2/3 席位多数，行为与既有测试一致 |
| A2 | 部分席位 ABSTAIN | 弃权不进分母；法定人数按配置总权重与总席位计；全弃权 → DEADLOCK |
| A3 | 管理员人工接管（E7 裁定） | 独立生成 `admin_override.json` 并记录 `override_id` 关联原 DEADLOCK `vote_result.json`（原 `vote_result.json` 保持不变） |
| A4 | `require_signoff` 与 decision | 计票只产 decision；签字是 UC-8 流水线步骤，不在本用例 |

## 4. 异常流

| # | 场景 | 行为 |
|---|---|---|
| E1 | 状态非 `WAITING_REVIEW` | 不计票（产物生命周期窗口，PRD §3.4）；旧轮票不得重复消费 |
| E2 | 席位尚未全部 accounted | 不进 CONSENSUS_CHECK；交 UC-9 守护（催票/超时降级） |
| E3 | 生成的 vote_result 未过 Schema | `raise`（fail-closed）；不落盘不转移 |
| E4 | 权重配置违反独裁帽 | `validate_config` 期拒绝（不进入运行期）；运行期发现 → HOLD + 审计 `POLICY_VIOLATION` |

## 5. 后置条件

- **成功**：`vote_result.json` 落盘且 Schema 合法；审计含票面与权重快照；`issues_index` 与各信封逐条对账一致。
- **失败**：任务态停留 `CONSENSUS_CHECK`（HOLD）或回 `WAITING_REVIEW`；无半成品文件。

## 6. 验收标准（可测）

1. 决策表全场景：全同意、1:1、1 赞 1 反 1 弃、全弃权、加权 2:1:1 各组合 → decision 唯一可推出；DEADLOCK 即时落盘不可变 `vote_result.json` 并 HOLD
2. `issues_index` 与 fixture 信封逐条零差集；编排器不代写采纳，不包含 `issues_summary` 混合段
3. 独裁帽：单席位达 2/3 总权重配置 → `validate_config` 拒绝
4. 权重只作用于总票：单条 issue 不因权重被增删（对账断言）
5. 编排器路径无 LLM 调用；同一票面重算结果幂等

## 7. 实现落点

| 位置 | 变更 |
|---|---|
| `src/macao/consensus/engine.py` + `vote.py` | 加权五重门禁纯整数计票、不可变 vote_result（计票/policy_snapshot/issues_index）、DEADLOCK 即时落盘 |
| `src/macao/core/schema.py` | `vote_result` Schema v2.0：`policy_snapshot`、`issues_index`、`requires_disposition`、移除旧 `issues_summary` |
| `src/macao/core/config.py` | `vote_weight` 校验 + 纯整数独裁帽 |
| `tests/` | 第 6 节 |

## 8. 设计自审

- 计票 ≠ 采纳 ≠ 评审结论（FAQ Q15）：三段边界在本用例与 UC-6 间显式切开
- 僵局问管理员不问执行者（自裁禁令，GUIDELINES §8"真理不等于投票"的对偶：投票也不等于真理）
- 遗留决策点：①`decision_confidence` 语义（建议 = 赞成加权占比，纯算术）；②权重公示格式（是否入审计正文）
