# 开发检查点与评审申请模板（Review Request）

- **文档归档路径**: `docs/reviews/<yyyy-MM-dd>-review-request-<mid>[-<topic>].md`
- **申请日期 (Date)**: `YYYY-MM-DD`
- **申请人 (Author)**: `[执行席位 ID / 开发者姓名]`
- **目标定级 (Target Level)**: `L1 DOC-ALIGNED` / `L2 SPEC-CODE-ALIGNED` / `L3 SCENARIO-VERIFIED` / `L4 RELEASE-READY`
- **被审 Commit (Checkpoint Ref)**: `<mid>` (例如 `961bcfe`)
- **评审轮次 (Review Round)**: `1` (返工整改轮递增为 2, 3...)
- **关联任务 ID (Task ID)**: `task-<id>`
- **前序受审基线与处置单 (Previous Baseline & Disposition)**: `docs/reviews/<date>-disposition-<prev_mid>.md`（若为第 1 轮初审可标为 N/A）

---

## 1. 变更摘要与目标 (Summary & Rationale)

清晰说明本轮迭代解决的核心问题、实现的架构/功能演进、以及非显然的设计决策与约束：
- **背景与目标**：...
- **关键设计决策**：...

---

## 2. 靶向变更清单 (Targeted Code Changes & Issue Mapping)

按模块列出本轮所有涉及文件、变更类型、代码行数变化、核心修改点以及对应的阻断项/缺陷编号：

| 文件路径 | 变更类型 | 增/删行数 | 核心修改说明 | 对应 Issue / P1 编号 |
| :--- | :--- | :--- | :--- | :--- |
| `src/macao/workflow/prober.py` | 核心逻辑 | +87 / -12 | dry-run 守卫零写盘；进度三元组 pending 判定 | P1-1, P1-3, P1-4 |
| `src/macao/adapter/session_locator.py` | 适配治理 | +496 / -120 | 跨 CLI 原生会话严格路径比对，消除伪造 | P1-2 |
| `src/macao/utils/secrets.py` | 新增模块 | +46 / -0 | API Key/Token 敏感词正则掩码清洗器 | P1-5 |
| `tests/test_p1_closures_and_regressions.py` | 自动化测试 | +370 / -0 | 10 项 P1 核心阻塞项专项负向与回归断言 | P1-1 ~ P1-8 |

---

## 3. 现成测试脚本与质量快照 (Quality Snapshot & Reproducible Commands)

### 3.1 一键复现与验证命令
审查员可在本地工作树中直接执行以下命令验证本轮产物与质量指标：

```bash
# 1. 执行全量自动化单元与集成测试
python3 -m unittest discover tests

# 2. 验证探活只读零写盘与三方对账
python3 -m macao.cli.main probe --dry-run

# 3. 语法与字节码编译校验
python3 -m compileall src tests
```

### 3.2 质量快照指标
- [x] **自动化测试**：`100% PASS`（全部测试用例通过，0 失败，0 错误）
- [x] **新增测试覆盖**：新增 N 项用例针对边界条件与反例断言
- [x] **代码编译检查**：Python 3.10+ 编译通过，0 语法警告
- [x] **只读零副作用**：`--dry-run` 探活不触碰任何磁盘文件，0 DDL，0 数据库修改
- [x] **契约与架构一致性**：双 Schema 契约目录逐字节一致

---

## 4. 开发者自评与审查聚焦点 (Self-Assessment & Review Focus Checklist)

### 4.1 开发者自评 (Executor Self-Assessment)
- **实现总结 (What was done)**：说明本轮代码实现的完整性，是否解决所有已定义需求；
- **已知局限性 (Known Limitations)**：诚实说明当前实现的技术边界或未覆盖场景（例如：某 CLI 在本地无持久化索引时采用 Fail-Closed 返回空列表）；
- **对前序评审意见的吸收**：说明前序轮次中审查员指出的问题如何被彻底解决。

### 4.2 提请专家重点关注事项 (Review Focus Checklist)
请各位评审专家在独立沙箱中重点核验以下边界场景与高危逻辑：
- [ ] **Focus 1: 零副作用与只读守卫**：验证 `--dry-run` 在各种异常分支下是否均保证 100% 零修改；
- [ ] **Focus 2: 会话路径与项目绑定**：验证跨项目或者同名子目录时，会话定位器是否发生误报或串话；
- [ ] **Focus 3: 法定人数与权重门控**：验证席位充足但权重不足、权重充足但席位不足等边界下决策算法是否正确阻断；
- [ ] **Focus 4: 日志敏感信息脱敏**：核验真实 PTY 日志与终端回显是否有效遮蔽各类 API Token 与密码。

---

## 伴随机器信封：`.macao/.dev.yml`

```yaml
version: "1.0"
task_id: "task-001"
checkpoint_ref: "961bcfe"
review_round: 1
status: "ready_for_review"
signal: "EXPLICIT"
executor:
  id: "dev-claude"
  cli: "claude-code"
full_document:
  path: "docs/reviews/2026-09-07-review-request-961bcfe.md"
  evidence_commit: "961bcfe"
  sha256: "0000000000000000000000000000000000000000000000000000000000000000"
development:
  description: "Implementation of feature with tests and self-assessment"
  quality_metrics:
    tests_passed: true
    tests_total: 145
    test_coverage: 0.88
    lint_errors: 0
    security_scan_passed: true
  git:
    latest_commit: "961bcfe"
    branch: "main"
  review_focus:
    - "verify boundary condition handling"
    - "verify zero side effects in read-only mode"
```
