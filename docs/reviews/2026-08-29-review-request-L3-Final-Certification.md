# MACAO L3 / PG-2 终局封板与深度自查认证评审申请 (commit `f41b9da..bf5ae2d`)

- **申请日期**：2026-08-29
- **申请目标**：**L3 SCENARIO-VERIFIED / Process Gate 2 (PG-2)**
- **待审范围**：`f41b9da..bf5ae2d`（HEAD）
- **依据基准**：`docs/MACAO_PRD_v2.md` v2.3.1、`docs/MACAO_REVIEW_GUIDELINES.md`、`docs/EXPERT_QUALITY.md`、`docs/schemas/*.schema.json`
- **全量机验结果**：
  - `PYTHONPATH=src python3 -m unittest discover tests -v`：**58 ran / 58 PASS (100%)**；
  - 5 轮连续全量回归（290 次用例执行）：**0 flake / 0 碰撞 / 0 崩溃**；
  - `macao test-clis`：**4/4 真实 CLI PTY 验证 PASS**（Claude Code / Codex / OpenCode / AGY），0 孤儿/0 僵尸残留；
  - `macao e2e-run`：**7/7 步骤全绿，终态 DONE**，5 份物理产物与 SQLite 账本（全 `consumed=1`、`archived_path` 真实非空、`sha256` 64 位哈希非空）双向核对 100% 一致；
  - 差异洁净度：`git diff --check f41b9da..HEAD` **返回码 0，无任何告警**。

---

## 一、针对 `f41b9da` 专家评审意见全量闭环清单

| 编号 | 严重度 | 专家来源 | 复审问题描述 | 根因与修复落点 | 对应测试与验证 |
|---|---|---|---|---|---|
| **P1-NEW-5** | **阻断** | Claude, Codex | **合并签字未绑定 checkpoint_ref，第 1 轮签字可误放行第 2 轮返工代码** | 修复 `src/macao/merge/controller.py:49-62`：签字校验不仅采用定向 SQL 查询，而且**严格比对 `signoff.detail.checkpoint_ref == task.checkpoint_ref`**，确保“评审对象 = 合并对象”硬绑定，完全符合 PRD §3.3 E4a 与 §14.5。 | 新增 `test_signoff_bound_to_checkpoint_ref_prevents_stale_merge`：<br>断言仅持 Round 1 签字时合并 Round 2 commit 必被 Fail-closed 拒绝；重新授予 Round 2 签字后方可通过。 |
| **P1-NEW-7 / P1-Q2** | **阻断** | Claude, Qwen, Codex | **超时 HOLD 后若迟到 Reviewer 补交，再次 collect 会绕过接管自动合并** | 修复 `src/macao/workflow/orchestrator.py:435-515` 与 `src/macao/consensus/vote.py:84-95`：建立**持久化超时处置（Timeout Disposition）**。一旦 Reviewer 记录超时弃权，迟到文件自动隔离为 `LATE_REVIEW_ISOLATED`，不参与自动共识；系统持久维持 HOLD 于 `CONSENSUS_CHECK` 并要求人工接管，终局 `vote_result.json` 保持 `ABSTAIN`。 | 新增 `test_late_review_after_timeout_maintains_hold_and_does_not_auto_merge`：<br>断言超时 HOLD 后即使迟到补交赞成票，系统依然维持 `CONSENSUS_CHECK`，唯有人工 `resolve_override("APPROVED")` 方可合并且终局含 `ABSTAIN` 票据。 |
| **P1-NEW-6** | **阻断** | Claude | **`RETRY_REVIEW` 人工裁定（E9）未清空旧票并重新派发请求，导致超时活锁** | 修复 `src/macao/workflow/orchestrator.py:770-785`：在 `resolve_override` 选择 `RETRY_REVIEW` 时，先由 FSM 归档，随后清理 `.macao/.reviews/` 活跃目录旧票，并调用 `dispatch_review_requests` 重新生成带有新 deadline 的 `REVIEW_REQUEST` 与派发审计。 | 新增 `test_retry_review_override_clears_reviews_and_redispatches_fresh_requests`：<br>断言 `RETRY_REVIEW` 触发后 `.reviews/` 旧票彻底清除，生成新 deadline 派发审计与消息。 |
| **P2-NEW-2** | **安全** | Claude | **`resolve_override` 先写盘后校验状态机，非法转移遗留孤儿产物** | 修复 `src/macao/workflow/orchestrator.py:730-745`：在写任何文件或注册产物前，先行调用 `TransitionTable.can_transition` 进行合法性校验；非法状态直接拒绝并记录审计。 | 新增 `test_resolve_override_invalid_transition_does_not_write_orphan_vote_result`：<br>断言在 `CODING` 状态非法调用 `resolve_override` 抛出 `ValueError`，磁盘与数据库均无残留产物。 |
| **GOV-1** | **治理** | Qwen, Claude | **评审注册表历史更名归属勘误** | 将 `2026-08-29-review-result-ea536ab-zcode.md` 与 `2026-08-29-review-result-f41b9da-zcode.md` 正式更名为以 `-qwen.md` 命名，并在 `STATUS.md` 中完成 47 份报告全量对账。 | 物理文件与评审注册表 100% 对账一致。 |

---

## 二、对照六大专家审查模型的主动自查与深度加固清单

在完成上述闭环后，进一步对照六大专家（Claude、Codex、Qwen、Kimi、Grok、Gemini）的完整攻击模型，进行了全局穷尽式自查并完成了 6 项深度工程加固：

| 维度 / 对应专家 | 隐患描述 | 修复与加固机制 | 对应代码与测试 |
|---|---|---|---|
| **Adapter 契约一致性**<br>(Codex) | `PTYSession.get_clean_logs` 无参返回 `List[str]`，与 Adapter 接收 `tail_lines` 返回 `str` 产生类型签名冲突；Mock 缺少方法 | 1. `PTYSession.get_clean_logs(tail_lines: Optional[int] = None)` 支持尾部切片；<br>2. 基类 `AgentAdapter` 声明抽象 `cancel()` 与 `get_logs()`，所有 5 个真实适配器与 Mock 均严格实现，返回统一字符串。 | `src/macao/adapter/*.py`<br>新增 `test_adapter_interface_and_log_consistency` |
| **Schema 动态寻址**<br>(Qwen) | `get_schemas_dir()` 仅做相对向上遍历，在 pip 分发包或指定环境变量时可能失效 | 升级为四级寻址：`MACAO_SCHEMAS_DIR` 环境变量 -> 包内捆绑路径 -> 源码 `docs/schemas` -> 相对路径。 | `src/macao/core/schema.py`<br>新增 `test_schemas_dir_lookup_and_env_override` |
| **时间解析显式校验**<br>(Qwen) | `parse_duration` 遇非法字符串静默回落为 600s | 增加非法格式校验，非空非法字符串显式抛出 `ValueError`。 | `src/macao/workflow/orchestrator.py`<br>新增 `test_parse_duration_units_and_validation` |
| **Task ID 高熵并发防碰**<br>(Codex) | 24-bit 熵在同秒高频并发下有极低概率碰撞 | 升级为 32-bit（8 位十六进制）高熵后缀，并在 SQLite 冲突时提供 5 次递增重试。 | `src/macao/workflow/orchestrator.py` |
| **产物 SHA256 归档自愈**<br>(Claude, Codex) | 产物注册时尚未写盘时 `sha256` 为空，归档后可能仍保留空值 | `mark_artifact_consumed` 在归档完成时自动读取物理文件补齐 64 位 `sha256`。 | `src/macao/storage/store.py` |
| **专家质量与防御十律**<br>(全专家) | 缺少系统的专家审查特征、攻击模型与工程自查防御矩阵沉淀 | 重构 `docs/EXPERT_QUALITY.md`，沉淀六大专家画像、攻击模型与工程自查十项铁律。 | `docs/EXPERT_QUALITY.md` |

---

## 三、代码与系统机验命令清单

```bash
# 1. 全量 58 项单元与场景测试（58/58 全部 PASS，100% 通过）
PYTHONPATH=src python3 -m unittest discover tests -v

# 2. 五轮连续全量回归（290 次用例执行，0 flake / 0 碰撞 / 0 崩溃）
for i in {1..5}; do PYTHONPATH=src python3 -m unittest discover tests -v > /dev/null || exit 1; echo "Run $i PASS"; done

# 3. 4 款真实 AI CLI 进程生命周期与 PTY 强杀机验
PYTHONPATH=src python3 -m macao.cli.main test-clis

# 4. Phase 2 端到端微任务协同仿真（Adapter 契约驱动、5 份产物归档、5 份数据库账本全 consumed=1 / 全 64 位 sha256）
PYTHONPATH=src python3 -m macao.cli.main e2e-run

# 5. 代码差异洁净度
git diff --check f41b9da..HEAD
```

---

## 四、申请定级结论请求

本轮提交（`f41b9da..bf5ae2d`）已彻底闭环 `f41b9da` 专家委员会指出的全部问题，并完成了超越单点缺陷的全局深度自查加固（测试集扩充至 58 项全量通过，5 轮高压回归 290/290 PASS，CLI 4/4 PASS，E2E 仿真 7/7 OK）。

特此向专家委员会（Claude / Codex / Qwen / Grok / Kimi）正式发起 **L3 SCENARIO-VERIFIED / Process Gate 2 (PG-2)** 终局封板认证评审申请，请求专家委员会开展复验并授予门禁认证。
