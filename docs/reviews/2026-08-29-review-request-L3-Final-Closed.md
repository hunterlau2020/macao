# MACAO L3 / PG-2 终局整改全量闭环评审申请 (commit `ea536ab..HEAD`)

- **申请日期**：2026-08-29
- **申请目标**：**L3 SCENARIO-VERIFIED / Process Gate 2 (PG-2)**
- **待审范围**：`ea536ab..HEAD`（针对四方专家在 `ea536ab` 轮复审所提 P1-1、P1-2、P3-1 的终局单点闭环整改）
- **依据基准**：`docs/MACAO_PRD_v2.md` v2.3.1、`docs/MACAO_REVIEW_GUIDELINES.md`、`docs/schemas/*.schema.json`
- **机验结果**：`PYTHONPATH=src python3 -m unittest discover tests -v` **49 ran / 49 PASS (100%)**；5 轮连续全量回归 0 flake / 0 碰撞；`macao test-clis` 4/4 CLI PTY 验证 PASS；`macao e2e-run` 产物与状态 100% 匹配；`artifacts` 表 5 份产物全部 `consumed=1`、`archived_path` 真实非空、`sha256` 64 位哈希非空。

---

## 一、本轮四方专家复审意见精准闭环整改清单

| 编号 | 严重度 | 阻断问题描述 | 根因与修复落点 | 验证与回归测试 |
|---|---|---|---|---|
| **P1-1**<br>(四方专家共同指出) | **阻断** | **超时弃权未写入终局 `vote_result.json` & 自动检测机制**<br>超时合成的 ABSTAIN 仅在内存参与死锁判定，`resolve_override` 时未携带超时 ABSTAIN，导致终局文件中缺少弃权记录；生产环境缺少超时自动检测。 | 1. 修复 `src/macao/consensus/vote.py`：`generate_vote_result()` 接收 `timed_out_reviewers`，将超时 Reviewer 以 `vote=ABSTAIN` 写入 `votes` 数组，并计入 `reviewers_responded` 与 `vote_breakdown.abstain`，完全符合 PRD §2.2 / §3.3 明文；<br>2. 修复 `src/macao/workflow/orchestrator.py`：`dispatch_review_requests` 记录 deadline 并发布带 deadline 的消息；新增 `detect_timed_out_reviewers()` 基于时钟自动检测超时；`resolve_override()` 自动从审计日志提取超时 Reviewer 注入终局 `vote_result.json` 生成。 | `test_reviewer_timeout_degradation_scenario`：<br>1. 推进可控时钟触发 `detect_timed_out_reviewers` 自动检测；<br>2. 强断言落盘 JSON 文件的 `votes`（含 `opencode: ABSTAIN`）、`reviewers_responded == 2`、`vote_breakdown.abstain == 1`、`vote_breakdown.approve == 1`；<br>3. 强断言 `REVIEWER_TIMEOUT_ABSTAIN` 审计事件与 `HUMAN_OVERRIDE_REQUEST` 消息。 |
| **P1-2**<br>(Claude, Grok, Codex, Qwen) | **阻断** | **`review_manifest` 消费归档 key 错配 & `artifacts.sha256` 为空**<br>`fsm.py` 使用 `rev_file.stem` 导致匹配到 `codex.review` 而非 `codex`，`consumed` 恒为 0；`register_artifact` 未计算 sha256。 | 1. 修复 `src/macao/workflow/fsm.py:111`：使用 `rev_file.name.replace(".review.yml", "")` 准确提取 `reviewer_id`；<br>2. 修复 `src/macao/storage/store.py`：在 `content is None` 时自动读取磁盘文件计算 64 位 `sha256` 校验和。 | `test_artifacts_registered_and_tracked_in_database`：<br>强断言 `artifacts` 表 5 份产物全部 `consumed == 1`、`archived_path` 均为 `.macao/archive/...`、`sha256` 均为 64 位有效哈希。 |
| **P3-1**<br>(Claude, Qwen) | **建议** | **文档尾随空白清理** | 清理 `docs/POC_VERIFICATION_REPORT.md` 尾随空白。 | `git diff --check 4df059e..HEAD` 100% 洁净，返回码 0。 |

---

## 二、代码测试与机验清单

```bash
# 1. 全量 49 项单元与回归测试（49/49 全部 PASS，100% 通过）
PYTHONPATH=src python3 -m unittest discover tests -v

# 2. 五轮连续全量回归（0 flake / 0 碰撞 / 0 崩溃）
for i in {1..5}; do PYTHONPATH=src python3 -m unittest discover tests -v > /dev/null || exit 1; echo "Run $i PASS"; done

# 3. 4 款真实 AI CLI 进程生命周期与 PTY 强杀机验
PYTHONPATH=src python3 -m macao.cli.main test-clis

# 4. Phase 2 端到端微任务协同仿真（Adapter 驱动、3 评审人、物理归档 5 份、数据库跟踪 5 份全 consumed=1/全 sha256）
PYTHONPATH=src python3 -m macao.cli.main e2e-run

# 5. 代码差异洁净度
git diff --check 4df059e..HEAD
```

---

## 三、申请定级请求

四方专家在 `ea536ab` 轮指出的所有残余阻断项（超时 ABSTAIN 票据落盘与时钟检测、Artifact 消费归档 key 匹配与 sha256 补齐、文档空白）已全部彻底单点闭环，经 49 项全量测试及 5 轮连续回归验证无误。

特此向专家委员会（Claude / Codex / Grok / Qwen / ZCode）发起终局评审申请，请求授予 **L3 SCENARIO-VERIFIED / Process Gate 2 (PG-2)** 门禁认证。
