# MACAO Round 7 复审（基线 `b90a40b`）评审结论

- **评审日期**：2026-09-10
- **评审人**：muse（独立评审）
- **评审对象**：`docs/reviews/2026-09-10-review-request-b90a40b.md`，钉死 `b90a40b`（HEAD `9a2f598` 仅增申请/STATUS）
- **结论**：**授予 L3 SCENARIO-VERIFIED / PG-2；L4 RELEASE-READY / PG-3 暂不准入**
- **结构化 issue**：`BLOCKING` × 0、`ADVISORY` × 2（P3 × 2）

---

## 1. 前序（`51fa456`）阻断闭环核验（独立探针）

| # | 前序阻断 | 独立复验 | 判定 |
|---|---|---|---|
| Codex P1-01（symlink 借用已提交正文放行） | 自写探针（生产路径，5 场景）：未跟踪 symlink→已提交目标 REJECTED；已提交 symlink（120000 blob）REJECTED；父目录 symlink REJECTED；`../` 逃逸 REJECTED；**常规已提交文件 ADVANCED → READY_FOR_REVIEW**（无过度拦截） | ✅ CLOSED |
| Codex P2-02（旧脚本非绿灯证据） | 正向探针 `verify_p1_51fa456_01_closed.py` 本机运行退出码 0 并打印 `ALL SYMLINK REMEDIATION CHECKS PASSED`；申请 §3.5 已替换引用 | ✅ CLOSED |
| Claude P3-1（live_runner 未透传准则） | `live_runner.py:152-160` 规范化（dict/list/str → list，缺省 `["unit_tests_pass"]`）并传入 `dispatch_review_in_worktree(acceptance_criteria=…)`；被调函数签名含该 kwarg（`:294`）；新回归测试通过 | ✅ CLOSED |
| Muse A-1（mock 回退说明） | `mock.py:172-174` 已补 Fail-Closed 边界注释 | ✅ CLOSED |
| Muse A-3（双重报错打印） | `main.py` 删除 `click.echo` 行，仅保留 Rich 输出（diff `-1` 行证实） | ✅ CLOSED |

修复实现细读：`normpath` 词法规范化拒 `..` 逃逸；文件及全部祖先 `is_symlink()` 回溯拒止；`lstat` + `S_ISREG` + `O_NOFOLLOW` 打开读（TOCTOU 安全）；`ls-tree` 强制 `blob` + `100644/100755`，拒 `120000`/tree/submodule。分层完备，未发现绕过路径。

## 2. 申请 §2–§4 机验复核（本机重放）

- §2 numstat：`git diff --numstat 51fa456..b90a40b` **18 行逐项吻合**；
- §3.1 全量 **175/175 OK**（60.4s）；§3.2 专项 **31/31 OK**（29→31，新增 symlink 多场景 + 准则透传）；§3.3 `show --check` 退出 0；§3.4 compileall 0；
- §4 信封：`validate_dev_manifest` **PASS**；`sha256` 与 `git show b90a40b:<disposition>` blob **逐字符一致**（`98a06d17…`）。

## 3. ADVISORY（P3 × 2）

- **A-1**：`self.root` 自身为 symlink 的极端情形不在检查内（`relative_to` 为词法操作）。生产 `root` 均为仓库绝对路径，风险可忽略，登记备查。
- **A-2**：L4 相关存续项（非本轮范围）：① Codex §7.2 OPS 十项矩阵证据仍无新增；② 本人 d042395-B3（`--auto-signoff` 默认 True + `HUMAN_MERGE_APPROVED`/`system-runner`）依然存续。本轮范围无 OPS 交付，L4 维持不准入。

## 4. 定级意见

- **授予 L3 / PG-2**：`51fa456` 唯一 P1 经独立 SIM（5 场景）+ TEST（31 专项）+ 正向绿灯探针三重证实闭环；P2/P3 建议项全部解决；P0/P1 为零。
- **L4 / PG-3 暂不准入**：理由同 A-2（OPS 矩阵 + 默认代签事件），均需独立轮次补足。

## 5. Reviewer 自审记录

- 本人为 `51fa456` 轮 YES_APPROVE 出具者之一；本轮对新增修复面全量新查，未因前票免检；
- 未读同期他家 `b90a40b` 报告，保持独立；
- 未覆盖：win32、真实厂商 CLI 额度演练、Phase 1 实现。
