# Evidence archive — pi-qwen Round 5 review of `bdc177e`

- **Reviewer**: pi-qwen（harness: pi coding agent；model `qwen3.8-max`；session `01a07bd3-8b24-72e9-8e95-62179f6a5946`）
- **Review object**: `docs/reviews/2026-09-09-review-request-bdc177e.md`
- **Verified commit**: `bdc177e`（真实完整 SHA `bdc177eaaff577e119093e686f2164bcc133f781`，`git rev-parse` 与申请一致）
- **Range**: `e06d44c..bdc177e`（单提交 `bdc177e`）
- **Script**: `repro_bdc177e_pi_qwen.py`（自建沙箱 + `git archive bdc177e` 纯净提取 + 自清理；PTY 相关仅用 `mock-cli`）
- **外部前提**: python3 3.10+、git、含 `bdc177e` 的本仓库检出。无网络、无厂商账号。
- **最后实际执行**: **2026-09-10 00:48:16 +0800**，结果：**H01–H06 PASS**（R4 三项 P1 与 Codex/Claude 同型缺陷全部闭环为真），**H07 FAIL**（immutable 陈旧读仍在，须按 §8.3-2 登记）。

## 检查 ↔ issue 映射

| 检查 | 内容 | 结论 |
|---|---|---|
| H01 | 门禁 11 种伪造变体（含**兄弟目录逃逸**、**空 evidence_commit**）全拒；happy 推进；`checkpoint --auto --test-cmd` 端到端通过 | Codex P1-01 / Claude P1-1 / Grok P2-1 **CLOSED** |
| H02 | blob-vs-disk 篡改（磁盘 sha==manifest 但 != 提交 blob）被拒；**未提交证据文档跳过 blob 校验仍放行**（申请已写明前置条件；与 Claude 本轮新 P2 同源） | 前半 CLOSED；后半 P2（须登记） |
| H03 | `acceptance_criteria` 到达 **7/7** 执行器适配器提示词 | R4 Pi-Qwen P1-2 / Codex P1-02 / Claude P1-2 **CLOSED** |
| H04 | `get_orchestrator` 装配执行器（mock 实例化）；未知 CLI → None（fail-closed）；`task create` 完成 | Codex P1-02 / Claude P1-2 **CLOSED** |
| H05 | 真实完整 SHA；§3.3 命令 rc=0；信封 sha256 **三方一致**（磁盘 == bdc177e blob == manifest）；样例过 `validate_dev_manifest` | R4 Pi-Qwen P1-1 / Codex P1-03 / Claude P1-3 **CLOSED** |
| H06 | 变更清单 25/25 行与 numstat 完全一致、零漏列 | 上轮遗留质量项 **CLOSED** |
| H07 | `immutable=1` 陈旧读仍在：有效配置下写者持有 WAL 时 probe 报 `task-OLD`（真相 `task-NEW`，`error=null`，零新增侧车） | R4 Pi-Qwen P2-1 **未登记、仍在** → 本轮批准的**绑定条件** |

## 另行执行的机验（§3.4 参照系，2026-09-09 23:50 – 09-10 00:48 +0800，纯净树 `/tmp/v5`）

```bash
python3 -m unittest discover tests                                # Ran 170 tests, OK
python3 -m unittest tests.test_p1_closures_and_regressions        # Ran 26 tests, OK
python3 -m compileall -q src tests                                # rc=0
git show --check bdc177eaaff577e119093e686f2164bcc133f781         # rc=0（真实 SHA）
# 未知 CLI 诊断（QW-7BC-P2-1 复核）：有效配置下 probe --json 输出
#   {'id':'r-x','cli':'custom-claude','status':'MISSING',
#    'error':"Unrecognized CLI 'custom-claude' (not in ADAPTER_MAP)"} → 诊断已具名；
#   qwen 归档探针仍报 CONFIRMED 系其内建 config 在现行 Schema 下非法（probe 早退、无 reviewers 字段）的探针侧陈旧，非产品缺陷
# 宿主仓 probe --dry-run：rc=0、.macao 零侧车
```

## 评审人自勘记录（§3.5）

1. 本轮两次陈旧读复测曾因**沙箱缺 `macao.yaml`** 而无效（probe 在读库前 fail-closed 早退，`active_task=None` 误判为"已修复"）；已以有效配置重测并在 H07 固化，结论以 00:48 版本为准。
2. 探索期一次 `task create`（executor cli=kimi）真实拉起了 kimi PTY 会话——进程已确认清理（`ps` 无残留）；该现象记为 P3-1（`task create` 现按设计派发执行器，建议提供 `--no-dispatch` 逃生阀并在文档标注）。H04 已改用 mock-cli，脚本不含真实 CLI 拉起。
