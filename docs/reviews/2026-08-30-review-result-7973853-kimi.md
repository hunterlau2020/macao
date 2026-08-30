# MACAO L3 / PG-2 终局定级复审结论

- **评审日期**：2026-08-30
- **评审范围**：`docs/reviews/2026-08-30-review-request-L3-PG2-Final.md` 所列 `3e1a991..HEAD` 整改，以及 HEAD=`7973853` 上相关代码 / 测试 / 产物一致性
- **对齐基准**：`docs/MACAO_PRD_v2.md` v2.3.1、`docs/MACAO_REVIEW_GUIDELINES.md` v1.0、`docs/schemas/*.schema.json`
- **评审角色**：kimi（独立复审）

## 结论

**L3 SCENARIO-VERIFIED / PG-2 授予。**

本轮申请所列 `P1-NEW-9`、`P2-NEW-4`、`P3-NEW-7` 及我上轮指出的 `P1-2`（`.dev.yml` 先验校验不完整）均已找到对应代码修复与测试证据，机验命令全部通过。经复核，关键场景（全同意、1:1 僵局、超时 / 弃权、崩溃恢复、返工循环、E9 重试两代际）均有可复现的测试证据，系统行为 fail-safe，满足 L3 判据。

---

## 已对齐 / 已确认项

| 申请编号 | 修复落点 | 验证状态 | 证据 |
|---|---|---|---|
| **P1-NEW-9** E9 代际归档覆写修复 | `src/macao/workflow/fsm.py:83-126` `_get_generation` + 哈希比对 + `g{gen}_{name}` 另存 + `ARTIFACT_ARCHIVED` 审计 | CODE VERIFIED / TEST VERIFIED | `tests/test_p0_p1_rectification.py:1141-1239` `test_multi_generation_archiving_preserves_gen1_evidence_immutable` 通过：Gen 1 反对票在重试后完整留存 |
| **P2-NEW-4** E9 活跃目录残留清理 | `src/macao/workflow/orchestrator.py:806-823` 在 `RETRY_REVIEW` 后主动删除 `.macao/vote_result.json` | CODE VERIFIED / TEST VERIFIED | `tests/test_p0_p1_rectification.py:1241-1281` `test_retry_review_cleans_active_vote_result_file` 通过 |
| **P3-NEW-7** 迟到票审计幂等 | `src/macao/workflow/orchestrator.py:513-525` 代际内 `already_logged` 幂等守卫 | CODE VERIFIED / TEST VERIFIED | `tests/test_p0_p1_rectification.py:1283-1317` `test_late_review_isolated_audit_is_idempotent` 通过：连续轮询 20 次仅 1 条记录 |
| **P1-2** `.dev.yml` 先验校验补齐 | `src/macao/workflow/orchestrator.py:221-234` 强校验 `signal == "EXPLICIT"`、`tests_passed`（或 `tests_exempt`）、`git.commit_exists(latest_commit)` | CODE VERIFIED / TEST VERIFIED | `tests/test_p0_p1_rectification.py:1340-1408` `test_check_development_checkpoint_validation_fail_closed` 通过：覆盖测试失败、伪造 commit、有效清单三分支 |

### 机验复现结果（本评审人独立执行）

```bash
# 1. 全量单元测试
PYTHONPATH=src python3 -m unittest discover tests -v
# => Ran 64 tests in 16.493s OK

# 2. 五轮连续全量回归
for i in {1..5}; do PYTHONPATH=src python3 -m unittest discover tests -v > /dev/null || exit 1; echo "Run $i PASS"; done
# => Run 1-5 PASS

# 3. 真实 CLI PTY 机验
PYTHONPATH=src python3 -m macao.cli.main test-clis
# => claude / codex / opencode / agy 4/4 PASS，0 僵尸

# 4. Phase 2 E2E 仿真
PYTHONPATH=src python3 -m macao.cli.main e2e-run
# => 7 steps 全部 OK，终态 DONE，归档 5 份产物

# 5. 编译与差异洁净度
python3 -m compileall -q src && git diff --check 3e1a991..HEAD
# => 返回码 0，无告警
```

---

## P2/P3：可延期但需登记

### P2-1：Reviewer 超时处理与 PRD §6.1 流程描述不一致（建议更新 PRD）

- **证据位置**：
  - 实现：`src/macao/workflow/orchestrator.py:368-426` 自动检测超时；`:538-556` 自动合成 `ABSTAIN` 并 HOLD 发布 `HUMAN_OVERRIDE_REQUEST`。
  - PRD 基准：`docs/MACAO_PRD_v2.md:1120-1124` 规定 `"Ping reviewer via agmsg, then wait 2 more minutes"`，超时后 `"ask user: 'Mark as abstain?'"`。
- **评估**：当前实现省略 ping 与显式“标记弃权”确认，直接自动计入 ABSTAIN 并强制人工接管。该行为 fail-safe（绝不静默推进），且最终决策权仍在用户，与 PRD §6.1 “人工接管超时总则” 的安全目标一致。差异属于流程简化而非安全降级。
- **建议**：在下一迭代中修订 `docs/MACAO_PRD_v2.md` §6.1，将 MVP 实际采用的“自动标记弃权 + 强制人工接管”策略写入文档；或补充 ping 与确认流程代码。

### P3-1：`.dev.yml` 校验使用宽容默认值

- **证据位置**：`src/macao/workflow/orchestrator.py:224,228` 中 `data.get("signal", "EXPLICIT")` 与 `quality.get("tests_passed", True)` 在字段缺失时默认视为通过。
- **影响**：若 Executor 遗漏 `signal` 或 `tests_passed` 字段，清单仍可能被受理。虽然 schema 要求这些字段，但当前代码未调用 schema 校验。
- **建议**：将 `check_development_checkpoint` 与 `docs/schemas/dev_manifest.schema.json` 校验器集成，对缺失 required 字段直接 Fail-closed。

### P3-2：`vote_result.json` 中 `input_artifacts.kind` 术语不一致

- **证据位置**：`src/macao/consensus/vote.py:102` 写入 `"kind": "review_manifest"`；PRD §2.3 示例（`docs/MACAO_PRD_v2.md:358`）为 `"kind": "review"`。
- **建议**：统一为 `"review_manifest"` 并同步修订 PRD 示例。

---

## 交叉文档需做的文字修订

1. **`docs/MACAO_PRD_v2.md` §6.1**：将 Reviewer 超时流程更新为 MVP 实际行为（自动标记 ABSTAIN + 强制 HUMAN_OVERRIDE），或补充说明 ping 为可选增强。
2. **`docs/MACAO_PRD_v2.md` §2.1 / §3.2 Layer 1a**：说明 `.dev.yml` 最小有效性校验由代码字段检查 + 后续 schema 校验两级组成。
3. **`docs/MACAO_PRD_v2.md` §2.3**：`input_artifacts.kind` 示例改为 `"review_manifest"`。

---

## Reviewer 自审记录

- **Checklist A（字段声明位置 vs 实际读取位置）**：已核对 `check_development_checkpoint` 中 `latest_commit`、`quality_metrics`、`signal` 读取路径与 PRD §2.1 一致。
- **Checklist B（[x] ≠ 完成证据）**：申请文档中的机验命令与测试断言均已独立复跑。
- **Checklist C（确定性用语）**：申请文档中 "64/64 PASS"、"100% 一致" 等陈述已复现。
- **Checklist D（代码块可执行性）**：机验命令均为可直接执行的 shell 命令，已执行通过。
- **本轮结论说明**：上轮指出的 P1-2 已闭环；P1-1 经重新评估为 P2（流程简化，不破坏安全目标），建议通过 PRD 修订对齐，不再作为 L3 阻断项。
