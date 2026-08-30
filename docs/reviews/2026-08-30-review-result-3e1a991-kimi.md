# MACAO L3 / PG-2 终局封板认证复审结论

- **评审日期**：2026-08-30
- **评审范围**：`docs/reviews/2026-08-30-review-request-L3-Final-Seal.md` 所列 `99526aa..HEAD` 整改，以及 HEAD=`3e1a991` 上相关代码 / 测试 / 产物一致性
- **对齐基准**：`docs/MACAO_PRD_v2.md` v2.3.1、`docs/MACAO_REVIEW_GUIDELINES.md` v1.0、`docs/schemas/*.schema.json`
- **评审角色**：kimi（独立复审）

## 结论

**L2 / PG-1 维持达成；L3 SCENARIO-VERIFIED / PG-2 暂不授予。**

本轮申请聚焦的 `P1-NEW-8 / P1-Q3 / P1-1`（E9 重试代际超时解绑）、`P2-CARRY-1`（ANSI 真实校验）、Schema 环境变量单测与 GOV-1 注册表勘误均已找到对应代码与测试，机验命令全部通过。但我在 `7935da3` 轮独立评审中指出的两项 P1 问题在本轮仍未关闭，导致超时场景与 `.dev.yml` 场景无法从 PRD v2.3.1 唯一推导出当前实现行为，因此不满足 L3 判据。

---

## 已对齐 / 已确认项

| 申请编号 | 修复落点 | 验证状态 | 证据 |
|---|---|---|---|
| **P1-NEW-8 / P1-Q3 / P1-1** E9 重试代际解绑 | `src/macao/workflow/orchestrator.py:454-472` 在 `collect_and_evaluate_consensus` 中以 `sequence_id >= latest_dispatch_seq` 过滤上一代际超时记录；`:754-763` 在 `resolve_override` 中采用同一代际口径；`:792-801` 在 `RETRY_REVIEW` 时清理旧 `.review.yml` 并重新派发 | CODE VERIFIED / TEST VERIFIED | `tests/test_p0_p1_rectification.py:952-1046` `test_retry_review_override_full_recovery_and_consensus` 通过：重试后全员如期提交赞成票，自动推进至 `MERGING`，`resolution == automatic` |
| **P1-NEW-8** 重试轮再次超时正确 HOLD | 同上 | CODE VERIFIED / TEST VERIFIED | `tests/test_p0_p1_rectification.py:1048-1104` `test_retry_review_override_repeated_timeout_holds` 通过：新代际再次超时后稳定 HOLD，并记录 2 条 `REVIEWER_TIMEOUT_ABSTAIN` |
| **P2-CARRY-1** ANSI 真实校验 | `src/macao/adapter/integ_harness.py:109-110` 使用 `ANSI_ESCAPE_RE` 逐行扫描 `clean_logs` | CODE VERIFIED / TEST VERIFIED | `PYTHONPATH=src python3 -m macao.cli.main test-clis` 4/4 PASS，ANSI Strip 列真实检测 |
| **Schema 单测覆盖** | `tests/test_config.py:116-127` 真实设置 `MACAO_SCHEMAS_DIR` 并验证优先级 | CODE VERIFIED / TEST VERIFIED | 单测通过 |
| **GOV-1** 注册表勘误 | `docs/reviews/STATUS.md:13` 将 `bf5ae2d-zcode.md` 更名为 `-qwen.md`，台账总数修正为 55 份结果 + 11 份申请 | DOC VERIFIED | `docs/reviews/` 目录与 STATUS 对账一致 |

### 机验复现结果（本评审人独立执行）

```bash
# 1. 全量单元测试
PYTHONPATH=src python3 -m unittest discover tests -v
# => Ran 60 tests in 12.972s OK

# 2. 五轮连续全量回归
for i in {1..5}; do PYTHONPATH=src python3 -m unittest discover tests -v > /dev/null || exit 1; echo "Run $i PASS"; done
# => Run 1-5 PASS

# 3. 真实 CLI PTY 机验
PYTHONPATH=src python3 -m macao.cli.main test-clis
# => claude / codex / opencode / agy 4/4 PASS，0 僵尸

# 4. Phase 2 E2E 仿真
PYTHONPATH=src python3 -m macao.cli.main e2e-run
# => 7 steps 全部 OK，终态 DONE，归档 5 份产物

# 5. 差异洁净度
git diff --check 99526aa..HEAD
# => 返回码 0，无告警
```

---

## P1：发布 / 进入下一阶段前应修正

### P1-1（上轮遗留，未关闭）：Reviewer 超时处理未实现 PRD §6.1 的 ping + 人工确认流程

- **证据位置**：
  - 实现：`src/macao/workflow/orchestrator.py:368-426` `detect_timed_out_reviewers` 仅比较当前时间与 dispatch 时间；`:523-539` 直接合成 `ABSTAIN` 票；`:549-574` 在存在超时票时 HOLD 并发布 `HUMAN_OVERRIDE_REQUEST`。
  - PRD 基准：`docs/MACAO_PRD_v2.md:1120-1124` 规定 `"action": "Ping reviewer via agmsg, then wait 2 more minutes", "escalation": "If still no response, ask user: 'Mark as abstain?'"`；`:318` 明确 `"Reviewer 超时经 §6.1 人工确认标记弃权后，由 Orchestrator 记入本轮票面"`；`:834` 规定超时降级流程完成需 `"ping/弃权/人工裁定"`。
- **偏差影响**：当前实现跳过 ping 与显式“标记弃权”确认，直接自动计入 ABSTAIN 并进入 HOLD。虽然最终结果仍是人工裁定， fail-safe，但行为路径与 PRD 文档描述不一致，导致 L3 要求的“可从文档唯一推出预期结果”不成立。
- **验收标准**：实现 PRD §6.1 的 ping → 2 分钟等待 → 用户确认“标记弃权”流程，并补充覆盖“ping 无响应后用户确认 / 取消”两条分支的测试；若项目决定保留自动降级实现，则应修订 PRD 并说明 MVP 采用该简化策略。

### P1-2（上轮遗留，未关闭）：`.dev.yml` 最小有效性校验不完整

- **证据位置**：
  - 实现：`src/macao/workflow/orchestrator.py:194-252` `check_development_checkpoint` 仅检查 `status == "ready_for_review"`、`review_round` 匹配、`latest_commit` 非空。
  - PRD 基准：`docs/MACAO_PRD_v2.md:207-228` 要求同时校验 `version` 存在、`signal == "EXPLICIT"`、`tests_passed` 为 true 或 `tests_exempt` 为 true、`latest_commit` 存在于本地 git 历史且未被消费过。
  - Schema：`docs/schemas/dev_manifest.schema.json:6` required 字段包含 `version`、`executor`、`development`、`status`、`signal`、`review_round`。
- **偏差影响**：测试与 E2E 中使用的 `.dev.yml` 缺少 `version`、`executor`、`development`、`signal` 等字段仍可通过检查点校验。实际运行中，Executor 可在未声明 `EXPLICIT` 信号、未满足质量门槛的情况下触发 `READY_FOR_REVIEW`，违反 PRD 最小有效性规则。
- **验收标准**：`check_development_checkpoint` 完整实现 PRD §2.1 的最小有效性规则并调用 schema 校验；测试用例中的 `.dev.yml` 应为合法 Schema 示例。

---

## P2/P3：可延期但需登记

### P2-1：`vote_result.json` 中 `input_artifacts.kind` 术语不一致

- **证据位置**：
  - 代码：`src/macao/consensus/vote.py:102` 写入 `"kind": "review_manifest"`。
  - PRD 示例：`docs/MACAO_PRD_v2.md:358` 示例为 `"kind": "review"`。
  - Schema：`docs/schemas/vote_result.schema.json:44` 仅要求 `string`，不限制枚举值，因此不触发校验失败。
- **影响**：术语不一致，违反《评审指引》§5 唯一对照表要求。建议统一为 `"review_manifest"` 并在 PRD §2.3 示例中同步修正。

### P3-1：评审编号跨轮次混用

- 本轮申请将 `P1-NEW-8 / P1-Q3 / P1-1` 并列为同一问题，但 STATUS 台账中不同轮次对同一问题使用了多个编号，增加了审计追踪成本。建议在 STATUS 中显式标注编号前缀规则（如按复审轮次 `P1-R{n}-{m}`）。

---

## 交叉文档需做的文字修订

1. **`docs/MACAO_PRD_v2.md` §2.3 `vote_result.json` 示例**：将 `"kind": "review"` 改为 `"kind": "review_manifest"`，与代码产物注册、DDL 注释保持一致。
2. **`docs/MACAO_PRD_v2.md` §6.1**：若项目决定保留“自动标记弃权 + 强制人工接管”的简化实现，应显式修订 PRD，删除 ping + 人工确认要求，并说明 MVP 采用该策略；否则应保留 PRD 并修改代码。
3. **`docs/MACAO_PRD_v2.md` §2.1 / §3.2 Layer 1a**：若代码的简化 `.dev.yml` 校验是故意的 MVP 折中，应在 PRD 中说明哪些最小有效性检查由 Layer 1a 完成、哪些延后到 schema 校验；否则应补齐代码实现。

---

## 建议的闭环顺序与验收标准

1. **关闭 P1-1**：实现 PRD §6.1 超时流程（ping → 2min 等待 → 用户确认弃权）或修订 PRD 并补充对应测试。复测：新增覆盖 ping 无响应后用户确认 / 取消两条路径的测试。
2. **关闭 P1-2**：补齐 `check_development_checkpoint` 对 `signal`、`version`、`quality_metrics`、`commit_exists`、`not_consumed` 的校验。复测：新增无效 `.dev.yml` 不触发 `READY_FOR_REVIEW` 的测试。
3. **关闭 P2-1**：同步 PRD 示例字段名。
4. **复评 L3/PG-2**：在上述 P1 关闭后，由至少一名未参与本轮实现的 reviewer 重新执行 §6 反例库场景推演（含 2-reviewer 全超时、1:1 僵局、max-round、崩溃恢复、脏工作区、重复投票去重、E9 重试两代际）并确认 60 项测试 + 5 轮回归 + `test-clis` + `e2e-run` 全绿。

---

## Reviewer 自审记录

- **Checklist A（字段声明位置 vs 实际读取位置）**：已核对 `check_development_checkpoint` 中 `latest_commit` 从 `data["development"]["git"]["latest_commit"]` 读取，与 PRD §2.1 字段路径一致；未发现字段路径错位。
- **Checklist B（[x] ≠ 完成证据）**：申请文档中的机验命令与测试断言均已独立复跑。
- **Checklist C（确定性用语）**：申请文档中 "60/60 PASS"、"100% 一致" 等陈述已复现；未将设计目标误标为事实。
- **Checklist D（代码块可执行性）**：机验命令均为可直接执行的 shell 命令，已执行通过。
- **本轮新登记漏审模式**：无新增连续漏审；但提醒后续 reviewer 关注 PRD §6.1 超时流程与代码实现的语义一致性，以及 `.dev.yml` 最小有效性规则与代码实现的差距——该两项在本轮申请中未被列入待整改清单。
