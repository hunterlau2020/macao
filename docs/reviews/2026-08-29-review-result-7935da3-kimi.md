# MACAO Phase 1/Phase 2 全量阻断项闭环评审结论（L3/PG-2 申请）

- **评审日期**：2026-08-29
- **评审范围**：`docs/reviews/2026-08-29-review-request-L3-All-Items-Closed.md` 所列 REQ-TIMEOUT、P0-1、P0-2、P0-3、P1-1、P1-2、P2-1、P2-2 的闭环整改，以及 HEAD=`7935da3` 上相关代码/测试/产物一致性
- **对齐基准**：`docs/MACAO_PRD_v2.md` v2.3.1、`docs/MACAO_REVIEW_GUIDELINES.md` v1.0、`docs/schemas/*.schema.json`
- **评审角色**：kimi（独立复审）

## 结论

**L2 SPEC-CODE-ALIGNED / PG-1 达成；L3 SCENARIO-VERIFIED / PG-2 暂不授予。**

申请文档中列出的 8 项阻断/重要/建议项均已在代码中找到对应修复点，且机验命令全部通过。但存在两项与 PRD v2.3.1 行为描述不一致的偏差，导致超时场景无法从文档唯一推导出当前实现行为，因此不满足 L3 "关键场景可从文档或系统唯一推出预期结果" 的判据。

---

## 已对齐 / 已确认项

| 申请编号 | 修复落点 | 验证状态 | 证据 |
|---|---|---|---|
| **REQ-TIMEOUT** 超时弃权/死锁/接管 | `src/macao/workflow/orchestrator.py:350-401` 新增超时检测；`:467-481` 合成 ABSTAIN；`:489-510` DEADLOCK HOLD 不写盘；`:623-718` resolve_override 终局落盘 | CODE VERIFIED / TEST VERIFIED | `tests/test_p0_p1_rectification.py:67-154` `test_reviewer_timeout_degradation_scenario` 通过；机验 49/49 PASS |
| **P0-1** 高熵 task_id | `src/macao/workflow/orchestrator.py:132-134` 使用 `uuid.uuid4().hex[:6]` 后缀 | CODE VERIFIED / TEST VERIFIED | `tests/test_p0_p1_rectification.py:50-65` 同秒 100 任务 0 碰撞 |
| **P0-2** max-round 不写盘 | `src/macao/workflow/orchestrator.py:513-534` 在 `rnd >= max_rework_rounds` 时直接返回，不调用 `generate_vote_result(write_to_disk=True)` | CODE VERIFIED / TEST VERIFIED | `tests/test_p0_p1_rectification.py:156-204` 断言磁盘无自动 vote_result；reconcile 后状态保持 CONSENSUS_CHECK |
| **P0-3** 脏工作区保护 | `src/macao/merge/controller.py:60-64` 检查 `git diff --name-only` 与 `git diff --cached --name-only` | CODE VERIFIED / TEST VERIFIED | `tests/test_p0_p1_rectification.py:206-236` 脏数据完整保留、合并被拒绝 |
| **P1-1** Worktree 物理清理 | `src/macao/utils/git_utils.py:109-121` 新增 `remove_isolated_worktree`；`src/macao/workflow/orchestrator.py:280-286` 异常时回滚 | CODE VERIFIED / TEST VERIFIED | `tests/test_p0_p1_rectification.py:238-279` 断言 reviewer1 worktree 被物理删除 |
| **P1-2** Artifact 注册 | `src/macao/workflow/orchestrator.py:220-226`、`:448-456`、`:549-555`、`:694-700` 注册 dev_manifest / review_manifest / vote_result | CODE VERIFIED / TEST VERIFIED | `tests/test_p0_p1_rectification.py:281-306` 断言 5 份产物均被消费、归档、SHA256 完整 |
| **P2-1** 校验先于写盘 | `src/macao/consensus/vote.py:192-194` 在 `write_to_disk` 前调用 `validate_vote_result` | CODE VERIFIED / TEST VERIFIED | `tests/test_p0_p1_rectification.py:308-327` 非法 resolution 抛 ValueError 且磁盘无文件 |
| **P2-2** human_resolution 非法输入 Fail-fast | `src/macao/consensus/vote.py:142-145` 未知输入抛 ValueError | CODE VERIFIED / TEST VERIFIED | 同上 |

### 机验复现结果（本评审人独立执行）

```bash
# 1. 全量单元测试
PYTHONPATH=src python3 -m unittest discover tests -v
# => Ran 49 tests in 11.569s OK

# 2. 五轮连续回归
for i in {1..5}; do PYTHONPATH=src python3 -m unittest discover tests -v > /dev/null || exit 1; echo "Run $i PASS"; done
# => Run 1-5 PASS

# 3. 真实 CLI PTY 机验
PYTHONPATH=src python3 -m macao.cli.main test-clis
# => claude / codex / opencode / agy 4/4 PASS

# 4. Phase 2 E2E 仿真
PYTHONPATH=src python3 -m macao.cli.main e2e-run
# => 7 steps 全部 OK，最终状态 DONE，归档 5 份产物
```

---

## P1：发布 / 进入下一阶段前应修正

### P1-1：Reviewer 超时处理未实现 PRD §6.1 的 ping + 人工确认流程

- **证据位置**：
  - 实现：`src/macao/workflow/orchestrator.py:350-401` `detect_timed_out_reviewers` 仅比较当前时间与 dispatch 时间；`:467-481` 直接合成 `ABSTAIN` 票。
  - PRD 基准：`docs/MACAO_PRD_v2.md:1120-1124` 规定 `"action": "Ping reviewer via agmsg, then wait 2 more minutes", "escalation": "If still no response, ask user: 'Mark as abstain?'"`；`:318` 明确 `"Reviewer 超时经 §6.1 人工确认标记弃权后，由 Orchestrator 记入本轮票面"`；`:834` 规定超时降级流程完成需 `"ping/弃权/人工裁定"`。
- **偏差影响**：当前实现把超时自动降级为 ABSTAIN，跳过了 ping 与显式人工确认。虽然结果仍进入 DEADLOCK 并触发 HUMAN_OVERRIDE_REQUEST， fail-safe，但行为与 PRD 文档描述不一致，导致 L3 要求的"可从文档唯一推出预期结果"不成立。
- **验收标准**：补充 ping 超时 reviewer 的 AEP/ agmsg 机制与 2 分钟宽限期；在确认用户选择"标记弃权"后再合成 ABSTAIN；提供覆盖 ping 无响应后用户确认/取消两种分支的测试。

### P1-2：`.dev.yml` 最小有效性校验不完整

- **证据位置**：
  - 实现：`src/macao/workflow/orchestrator.py:180-238` `check_development_checkpoint` 仅检查 `status == "ready_for_review"`、`review_round` 匹配、`latest_commit` 非空。
  - PRD 基准：`docs/MACAO_PRD_v2.md:207-228` 要求同时校验 `version` 存在、`signal == "EXPLICIT"`、`tests_passed` 为 true 或 `tests_exempt` 为 true、`latest_commit` 存在于本地 git 历史且未被消费过。
  - Schema：`docs/schemas/dev_manifest.schema.json:6` required 字段包含 `version`、`executor`、`development`、`status`、`signal`、`review_round`。
- **偏差影响**：测试用例中的 `.dev.yml` 缺少 `version`、`executor`、`development`、`signal` 等字段仍可通过检查点校验。这会导致实际运行中未按 PRD 最小有效性规则过滤无效产物，可能让 Executor 在尚未声明 EXPLICIT 信号时进入 READY_FOR_REVIEW。
- **验收标准**：`check_development_checkpoint` 完整实现 PRD §2.1 的最小有效性规则，并调用 schema 校验；测试用例中的 `.dev.yml` 应为合法 Schema 示例。

---

## P2/P3：可延期但需登记

### P2-1：`vote_result.json` 中 `input_artifacts.kind` 术语不一致

- **证据位置**：
  - 代码：`src/macao/consensus/vote.py:102` 写入 `"kind": "review_manifest"`。
  - PRD 示例：`docs/MACAO_PRD_v2.md:358` 示例为 `"kind": "review"`。
  - Schema：`docs/schemas/vote_result.schema.json:44` 仅要求 `string`，不限制枚举值，因此不触发校验失败。
- **影响**：术语不一致，违反《评审指引》§5 "产物 — 生成者 — 路径 — 格式 — 关键字段 — 版本/保留策略" 唯一对照表要求。建议统一为 `"review_manifest"` 并在 PRD §2.3 示例中同步修正。

### P3-1：评审编号跨轮次混用

- 本次申请将 dirty worktree 编号为 P0-3，而此前 `ea536ab` 评审中 zcode 将 CI gate 原子回滚编号为 P0-NEW-3。编号冲突虽未导致技术问题，但增加了审计追踪成本，建议在 STATUS 中显式标注编号前缀规则（如按复审轮次 `P0-R2-1`）。

---

## 交叉文档需做的文字修订

1. **`docs/MACAO_PRD_v2.md` §2.3 `vote_result.json` 示例**：将 `"kind": "review"` 改为 `"kind": "review_manifest"`，与代码产物注册、DDL 注释保持一致。
2. **`docs/MACAO_PRD_v2.md` §6.1**：若项目决定保留"自动标记弃权"的简化实现，应显式修订 PRD，删除 ping + 人工确认要求，并说明 MVP 采用自动降级策略；否则应保留 PRD 并修改代码。
3. **`docs/MACAO_PRD_v2.md` §2.1 / §3.2 Layer 1a**：若代码的简化 `.dev.yml` 校验是故意的 MVP 折中，应在 PRD 中说明哪些最小有效性检查由 Layer 1a 完成、哪些延后到 schema 校验；否则应补齐代码实现。

---

## 建议的闭环顺序与验收标准

1. **关闭 P1-1**：实现 PRD §6.1 超时流程（ping → 2min 等待 → 用户确认弃权）或修订 PRD 并补充对应测试。复测：`test_reviewer_timeout_degradation_scenario` 需覆盖 ping 无响应后用户确认/取消两条路径。
2. **关闭 P1-2**：补齐 `check_development_checkpoint` 对 `signal`、`version`、`quality_metrics`、`commit_exists`、`not_consumed` 的校验。复测：新增无效 `.dev.yml` 不触发 READY_FOR_REVIEW 的测试。
3. **关闭 P2-1**：同步 PRD 示例字段名。
4. **复评 L3/PG-2**：在上述 P1 关闭后，由至少一名未参与本轮实现的 reviewer 重新执行 §6 反例库场景推演（含 2-reviewer 全超时、1:1 僵局、max-round、崩溃恢复、脏工作区、重复投票去重等）并确认 49 项测试 + 5 轮回归 + `test-clis` + `e2e-run` 全绿。

---

## Reviewer 自审记录

- **Checklist A（字段声明位置 vs 实际读取位置）**：已核对 `check_development_checkpoint` 中 `latest_commit` 从 `data["development"]["git"]["latest_commit"]` 读取，与 PRD §2.1 字段路径一致；未发现字段路径错位。
- **Checklist B（[x] ≠ 完成证据）**：申请文档中的 `[x]` 均对应到具体测试用例或机验命令，已独立复跑。
- **Checklist C（确定性用语）**：申请文档中 "100% 通过"、"0 flake" 等陈述已复现；未将设计目标误标为事实。
- **Checklist D（代码块可执行性）**：机验命令均为可直接执行的 shell 命令，已执行通过。
- **本轮新登记漏审模式**：无新增连续漏审；但提醒后续 reviewer 关注 PRD §6.1 超时流程与代码实现的语义一致性，该点在本轮申请中曾被当作已关闭项处理。
