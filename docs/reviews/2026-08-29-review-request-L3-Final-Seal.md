# MACAO L3 / PG-2 终局封板评审申请 (commit `7935da3..f41b9da`)

- **申请日期**：2026-08-29
- **申请目标**：**L3 SCENARIO-VERIFIED / Process Gate 2 (PG-2)**
- **待审范围**：`7935da3..f41b9da`（HEAD）
- **依据基准**：`docs/MACAO_PRD_v2.md` v2.3.1、`docs/MACAO_REVIEW_GUIDELINES.md`、`docs/schemas/*.schema.json`
- **机验结果**：
  - `PYTHONPATH=src python3 -m unittest discover tests -v`：**51 ran / 51 PASS (100%)**；
  - 5 轮连续全量回归（255 次用例执行）：**0 flake / 0 碰撞 / 0 崩溃**；
  - `macao test-clis`：**4/4 真实 CLI PTY 验证 PASS**（Claude Code / Codex / OpenCode / AGY），0 孤儿/0 僵尸残留；
  - `macao e2e-run`：**7/7 步骤全绿，终态 DONE**，5 份物理产物与 SQLite 账本（全 `consumed=1`、`archived_path` 真实非空、`sha256` 64 位哈希非空）双向核对 100% 一致；
  - 差异洁净度：`git diff --check 7935da3..HEAD` **返回码 0，无任何告警**。

---

## 一、针对 `7935da3` 复审意见闭环清单

| 编号 | 严重度 | 复审问题描述 | 根因与修复落点 | 对应测试与验证 |
|---|---|---|---|---|
| **P1-NEW-3**<br>(Claude, Kimi, Codex) | **阻断** | **3 Reviewer 超时（2 赞成 + 1 超时）直接合成 ABSTAIN 达到 2/3 多数并触发自动批准合并，绕过 PRD 强制的人工接管** | 修复 `src/macao/workflow/orchestrator.py:488-511`：在 `collect_and_evaluate_consensus` 中，**只要存在超时 Reviewer，无论其余票数是否满足多数，一律强制 HOLD 于 `CONSENSUS_CHECK` 并发布 `HUMAN_OVERRIDE_REQUEST`**，绝不走 `resolution: automatic` 自动批准合并，完全对齐 PRD §1.2:128、§2.2:318、§3.3:834 与 §6.1 规范。 | 新增 `test_three_reviewer_timeout_must_hold_and_require_human_override`：<br>1. 3 Reviewer 场景下 2 票通过 + 1 票超时，强断言状态保持 `CONSENSUS_CHECK` 且磁盘无自动 vote_result.json；<br>2. 强断言唯有管理员通过 `resolve_override("APPROVED")` 才能驱动转入 `MERGING` 并生成终局 `vote_result.json`（含 3 Reviewer, 2 Approve, 1 Abstain）。 |
| **P1-NEW-4**<br>(Claude) | **阻断** | **审计日志硬编码 `limit=50` 且无定向查询，高频轮询后 dispatch 记录被挤出窗口导致超时检测失效与终局回填丢失** | 1. 修复 `src/macao/storage/store.py`：新增 `get_audit_events_by_type(task_id, event_type, review_round)` 定向 SQL 索引查询，彻底摆脱 `limit` 窗口截断；<br>2. 修复 `src/macao/workflow/orchestrator.py`：超时检测与 `resolve_override` 回填均采用定向查询；`REVIEWER_TIMEOUT_ABSTAIN` 改为按 (task, round, reviewer) 幂等写入。 | 新增 `test_audit_polling_over_50_does_not_lose_timeout_reviewers`：<br>强断言在 100+ 次高频轮询及大量心跳审计事件后，`detect_timed_out_reviewers` 与 `resolve_override` 依然 100% 稳定检出并回填超时 Reviewer，无任何数据丢失。 |
| **P3-NEW-2**<br>(Claude, Qwen) | **建议** | **E2E 报告 `effective_votes` 取值逻辑走 fallback** | 修复 `src/macao/workflow/e2e_runner.py:236-239`：由 `approve_count + reject_count` 精确计算有效票数。 | `macao e2e-run` 实测：`effective_votes=3`，与 `approve=3, reject=0, abstain=0` 统计口径 100% 吻合。 |
| **GOV-1**<br>(Qwen) | **治理** | **评审注册表文件名归属勘误** | 将 `2026-08-29-review-result-7935da3-zcode.md` 更名为 `2026-08-29-review-result-7935da3-qwen.md`（正文署名 qwen），并在 `STATUS.md` 中修正登记。 | 评审注册表与物理文件全量对账一致。 |
| **P3-NEW-1**<br>(Claude, Qwen) | **规范** | **尾随空白清理** | 清理历史报告中的尾随空白。 | `git diff --check 7935da3..HEAD` 返回码 0。 |

---

## 二、代码与系统机验命令清单

```bash
# 1. 全量 51 项单元与回归测试（51/51 全部 PASS，100% 通过）
PYTHONPATH=src python3 -m unittest discover tests -v

# 2. 五轮连续全量回归（255 次用例执行，0 flake / 0 碰撞 / 0 崩溃）
for i in {1..5}; do PYTHONPATH=src python3 -m unittest discover tests -v > /dev/null || exit 1; echo "Run $i PASS"; done

# 3. 4 款真实 AI CLI 进程生命周期与 PTY 强杀机验
PYTHONPATH=src python3 -m macao.cli.main test-clis

# 4. Phase 2 端到端微任务协同仿真（Adapter 契约驱动、5 份产物归档、5 份数据库账本全 consumed=1 / 全 64 位 sha256）
PYTHONPATH=src python3 -m macao.cli.main e2e-run

# 5. 代码差异洁净度
git diff --check 7935da3..HEAD
```

---

## 三、申请定级结论请求

在 `7935da3` 轮四方专家复审中，**P1-2（产物账本与 SHA256）已被四方一致确认完全无保留闭环**；本轮提交针对所有专家指出的残余问题（超时降级强制人工确认守卫 P1-NEW-3、定向审计查询 P1-NEW-4、有效票数计算、注册表勘误及代码洁净度）实施了彻底的单点闭环，经 51 项测试与 5 轮连续回归验证均 100% 通过。

特此向专家委员会（Claude / Codex / Kimi / Qwen / Grok / ZCode）发起 **L3 SCENARIO-VERIFIED / Process Gate 2 (PG-2)** 终局封板评审申请，请求授予门禁认证。
