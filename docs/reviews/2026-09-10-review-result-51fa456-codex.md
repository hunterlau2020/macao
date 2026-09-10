# Commit 51fa456 Round 6 独立评审结论

- 评审日期：2026-09-10（Asia/Taipei）
- 受审对象：`51fa456ada474818a1107f1a11b061661dab1063`，范围 `bdc177e..51fa456`
- 评审基准：`docs/MACAO_REVIEW_GUIDELINES.md` v1.1；`docs/MACAO_PRD_v2.md`；`docs/usecases/UC3-dev-checkpoint.md`
- 结论：**REJECT**。不授予 L3 / PG-2；L4 / PG-3 亦不具备申请所要求的 §7.2 OPS 十项实机证据。

## 已确认项

- `git show --check 51fa456ada474818a1107f1a11b061661dab1063` 通过。
- 在隔离 clone、精确 checkout 至受审 SHA 的参照系中，`PYTHONPATH=src python3 -m unittest discover tests` 为 **173 tests / OK**；`tests/test_p1_closures_and_regressions.py` 为 **29 tests / OK**；`python3 -m compileall -q src tests` 通过。
- 前轮 P1 的普通未跟踪文件路径已被阻断：`orchestrator.py:430-441` 对 Git tree 中不存在的普通路径返回 `None`；未知 executor CLI 也会在 `main.py:191-196` 以非零退出阻断。

## P1：进入下一阶段前必须修正

### P1-51fa456-01：解析符号链接后校验 Git blob，未提交的声明路径仍可借用已提交正文放行

- 严重级与可达性：**P1，在线真实可达**。`macao task checkpoint` 调用 `check_development_checkpoint()`；这是 `CODING -> READY_FOR_REVIEW` 的状态机门卫。未被证据提交所包含的 `full_document.path` 仍可使检查点进入评审，破坏 UC3 P3/d5 的全文路径—提交—SHA 链。
- 证据：`src/macao/workflow/orchestrator.py:414-416` 先对用户申明的路径调用 `resolve()`；`430-436` 随后以解析后的 `rel_doc_path` 调用 `git cat-file` 与读取 blob。因此 `docs/reviews/untracked-alias.md -> committed.md` 会改为验证 Git 中的 `docs/reviews/committed.md`，而非 manifest 声明且未提交的 alias。
- 实测：归档脚本创建临时 repo，在 commit 中仅写入 `docs/reviews/committed.md`，随后创建未跟踪 symlink `untracked-alias.md` 并将其作为 manifest 的 `full_document.path`。`git cat-file -e HEAD:docs/reviews/untracked-alias.md` 返回非零，但真实 `check_development_checkpoint()` 仍转为 `READY_FOR_REVIEW`。
- 影响：工作树可接受，但按 `evidence_commit` checkout 的 reviewer/worktree 没有该申明路径；审计记录的路径亦不能从提交唯一复现。
- 修复建议：保留未经解析的、词法规范化后的相对声明路径作为 Git tree 查询键；拒绝路径本身及任一父目录为 symlink，并要求该**原始声明路径**在 `evidence_commit` 中为普通 blob。再将该 blob 的 SHA-256 与文件的 `lstat` 常规文件内容及 manifest 一并比较。
- 处置字段：`owner=MACAO Architecture & Engineering Team`；`due_date=进入 PG-2 前`；`resolution_commit=null`；`status=OPEN`。

## P2/P3：需登记或修正

### P2-51fa456-02：申请列出的“专家复现脚本机验”不是修复验证脚本

申请 §3.5 让 reviewer 执行 `docs/reviews/evidence/2026-09-10-bdc177e-codex/reproduce_remaining_fail_closed_gaps.py`，并宣称预期为保持 `CODING`。但该脚本 `:104` 仍断言 `change is not None` 且状态为 `READY_FOR_REVIEW`，即断言旧漏洞应成功；在受审 SHA 它因此以 `AssertionError: CODING` 非零退出。该文件无法作为 Guidelines §3.5 所要求的可复跑“修复绿灯”证据。应改为断言拒绝并将最后一次执行结果、目标 SHA 写入元数据；若延期，按 Guidelines §8.3-2 在 `STATUS.md` 登记风险接受。

## L4 / PG-3

申请没有提供 Guidelines §7.2 的十项明确 OPS 结论及人工接管实机演练。现有 `ControlledE2ERunner` 仍直接实例化 `MockAgentAdapter`（`src/macao/workflow/e2e_runner.py:112-122`），不满足 §7.2 第 10 项“穿透真实生产组件”的 L4 证据要求。因此 L4 状态为 **UNKNOWN / 未授予**，不是 PASS。

## 建议闭环顺序与验收标准

1. 修复 P1-51fa456-01，并新增一条经公开 `task checkpoint` 路径驱动的回归：未跟踪 symlink、已提交 symlink、父目录 symlink 均须非零/保持 `CODING`；普通的已提交 regular file 仍应进入 `READY_FOR_REVIEW`。
2. 把申请 §3.5 的旧漏洞复现脚本改造成“漏洞被阻断”的回归脚本，并以受审 SHA 实跑成功。
3. P1 为零后再申请 L3 / PG-2；L4 另补完整 §7.2 OPS 矩阵与真实人工接管演练。

## 复现脚本与命令

- `docs/reviews/evidence/2026-09-10-51fa456-codex/reproduce_untracked_symlink_evidence_bypass.py`
  - issue_id：P1-51fa456-01
  - target：`51fa456ada474818a1107f1a11b061661dab1063`
  - prerequisites：Python 3.10+、Git；无需网络、厂商 CLI 或账号。
  - last executed：2026-09-10 Asia/Taipei；输出：`REPRODUCED: untracked symlink declaration advanced to READY_FOR_REVIEW`。
  - command：`python3 docs/reviews/evidence/2026-09-10-51fa456-codex/reproduce_untracked_symlink_evidence_bypass.py`

## Reviewer 自审记录

- 本轮按 Guidelines §9 模式 E 检查了新增组合根防线的生产调用；并按前轮“Git blob 强绑定”修复目标构造 symlink 反例，而非重复普通未跟踪文件反例。
