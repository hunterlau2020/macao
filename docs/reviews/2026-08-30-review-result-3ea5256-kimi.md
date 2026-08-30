# MACAO L3 / PG-2 全员一致终局定级复审结论

- **评审日期**：2026-08-30
- **评审范围**：`docs/reviews/2026-08-30-review-request-L3-PG2-Unanimous-Final.md` 所列 `7973853..HEAD` 整改，以及 HEAD=`3ea5256` 上相关代码 / 测试 / 产物一致性
- **对齐基准**：`docs/MACAO_PRD_v2.md` v2.3.1、`docs/MACAO_REVIEW_GUIDELINES.md` v1.0、`docs/schemas/*.schema.json`
- **评审角色**：kimi（独立复审）

## 结论

**L3 SCENARIO-VERIFIED / PG-2 授予。**

本轮申请所列 `P1-NEW-11 / P1-1 / P3-1`（`.dev.yml` 全量 Schema 先验校验与 Fail-closed 门禁）及 `P2-NEW-5`（E9 源状态限制）均已找到对应代码修复与测试证据，机验命令全部通过。经复核，关键场景（全同意、1:1 僵局、超时 / 弃权、崩溃恢复、返工循环、E9 重试两代际）均有可复现的测试证据，系统行为 fail-safe，满足 L3 判据。

---

## 已对齐 / 已确认项

| 申请编号 | 修复落点 | 验证状态 | 证据 |
|---|---|---|---|
| **P1-NEW-11 / P1-1 / P3-1** `.dev.yml` 全量 Schema 先验校验 | `src/macao/workflow/orchestrator.py:222-240` 先行调用 `validate_dev_manifest(data)` 进行 Draft-07 全量校验；严格执行 `signal == "EXPLICIT"`、`tests_passed is True`、`git.commit_exists(latest_commit)`，无宽容默认值 | CODE VERIFIED / TEST VERIFIED | `tests/test_p0_p1_rectification.py:1348-1513` `test_check_development_checkpoint_validation_fail_closed` 覆盖 9 个分支全部通过 |
| **P2-NEW-5** E9 源状态限制 | `src/macao/workflow/transitions.py:48-51` 显式守卫 `E9` 仅允许从 `CONSENSUS_CHECK` / `UNKNOWN` 转移至 `WAITING_REVIEW` | CODE VERIFIED / TEST VERIFIED | 现有 E9 相关测试均经由 `CONSENSUS_CHECK` 合法发起，全量测试通过 |

### 机验复现结果（本评审人独立执行）

```bash
# 1. 全量单元测试
PYTHONPATH=src python3 -m unittest discover tests -v
# => Ran 64 tests in 14.813s OK

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
python3 -m compileall -q src && git diff --check 7973853..HEAD
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

### P3-1：评审注册表计数与实际文件数不符

- **证据位置**：`docs/reviews/STATUS.md:20` 声明“62 份历史与当前评审报告 + 13 份申请”，但 `docs/reviews/` 目录实际包含 **63 份** `review-result` 文件与 13 份 `review-request` 文件。
- **影响**：对账计数存在 1 份偏差，不影响技术结论，但违反治理规则“每轮申请复审前，STATUS 必须与 `reviews/` 目录全量对账”。
- **建议**：更新 STATUS.md 中的计数并复核是否有文件遗漏登记。

### P3-2：`vote_result.json` 中 `input_artifacts.kind` 术语不一致

- **证据位置**：`src/macao/consensus/vote.py:102` 写入 `"kind": "review_manifest"`；PRD §2.3 示例（`docs/MACAO_PRD_v2.md:358`）为 `"kind": "review"`。
- **建议**：统一为 `"review_manifest"` 并同步修订 PRD 示例。

---

## 交叉文档需做的文字修订

1. **`docs/MACAO_PRD_v2.md` §6.1**：将 Reviewer 超时流程更新为 MVP 实际行为（自动标记 ABSTAIN + 强制 HUMAN_OVERRIDE），或补充说明 ping 为可选增强。
2. **`docs/MACAO_PRD_v2.md` §2.3**：`input_artifacts.kind` 示例改为 `"review_manifest"`。
3. **`docs/reviews/STATUS.md`**：修正评审报告计数为 63 份，并确认是否有未登记文件。

---

## Reviewer 自审记录

- **Checklist A（字段声明位置 vs 实际读取位置）**：已核对 `check_development_checkpoint` 中 `latest_commit`、`quality_metrics`、`signal` 读取路径与 PRD §2.1 一致；Schema 校验器已接入。
- **Checklist B（[x] ≠ 完成证据）**：申请文档中的机验命令与测试断言均已独立复跑。
- **Checklist C（确定性用语）**：申请文档中 "64/64 PASS"、"100% 一致" 等陈述已复现。
- **Checklist D（代码块可执行性）**：机验命令均为可直接执行的 shell 命令，已执行通过。
- **本轮结论说明**：上轮指出的 P3-1（`.dev.yml` 宽容默认值）与 P2-NEW-5 均已闭环；遗留 P2-1（超时流程简化）经评估为 fail-safe 流程差异，建议通过 PRD 修订对齐，不再作为 L3 阻断项。
