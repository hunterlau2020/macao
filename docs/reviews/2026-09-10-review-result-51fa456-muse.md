# MACAO Round 6 复审（基线 `51fa456`）评审结论

- **评审日期**：2026-09-10
- **评审人**：muse（独立评审）
- **评审对象**：`docs/reviews/2026-09-10-review-request-51fa456.md`，钉死 `51fa456`（HEAD `8953b8d` 仅增申请/STATUS）
- **结论**：**授予 L3 SCENARIO-VERIFIED / PG-2；L4 RELEASE-READY / PG-3 暂不准入**
- **结构化 issue**：`BLOCKING` × 0、`ADVISORY` × 4（P2 × 1 / P3 × 3）

---

## 1. 前序（`bdc177e`）阻断闭环核验（全部独立探针，非复述申请）

| # | 前序阻断 | 独立复验 | 判定 |
|---|---|---|---|
| Codex P1-01（未跟踪证据放行） | 自写探针（生产路径 `start_task → .dev.yml → check_development_checkpoint`）：未跟踪事后文件 REJECTED（CODING）；后续提交声明旧 commit REJECTED；篡改 blob REJECTED；**正向对照（正确 commit + 正确字节）ADVANCED → READY_FOR_REVIEW**——无过度拦截 | ✅ CLOSED |
| Codex P1-02（未知 CLI 静默悬空） | 黑盒 CLI：`task create --no-probe` + `cli: unknown-executor` → **exit 1，错误点名 `unknown-executor`，`state.db` 0 任务**；调用点仅两处（`main.py:192` 守卫退出 / `orchestrator.py:107` 直接抛），无吞异常路径 | ✅ CLOSED |
| Grok P2-3（审查员准则透传） | 自写探针（正确 API：`role: reviewer` + mock session）：7/7 prompt 含 `Acceptance Criteria` 与准则条目；空准则不崩溃且省略该节 | ✅ CLOSED |
| Claude P2-1 / Grok P2-1·P2-2 | 与上述 P1 同源同修复，覆盖 | ✅ CLOSED |
| Pi-Qwen 条件①② / Codex P2（已知简化登记） | `STATUS.md:32-41` 常设表已登记 `immutable=1` 陈旧读与 `--auto` 草稿边界（含 §5.2 依据与 v2.6.0 计划） | ✅ CLOSED |

## 2. 申请 §2–§4 机验复核（本机重放）

- §2 numstat：`git diff --numstat bdc177e..51fa456` **32 行逐项吻合**（含 +139 测试、+9/-7 orchestrator 等关键行数）；
- §3.1 全量 **173/173 OK**（64.1s）；§3.2 专项 **29/29 OK**；§3.3 `git show --check` 退出 0；§3.4 compileall 0；
- §3.5 Codex 归档脚本现以 `AssertionError: CODING` 失败——该脚本断言的是旧缺陷行为（放行至 READY_FOR_REVIEW），其失败本身即证明缺陷不可复现（状态保持 CODING）；但作为"验收物"它退出非零，见 A-2；
- §4 信封：`validate_dev_manifest` **PASS**；`full_document.sha256` 与 `git show 51fa456:<disposition>` 的 blob SHA-256 **逐字符一致**（`a78035b8…`）。

## 3. ADVISORY

- **A-1（P2）**：`mock.py` 优先复用已提交评审文档（`ls-tree`），否则现场创建未提交 mock 文档——后者在 mock 驱动路径下仍可能产出"未提交证据"，所幸生产校验现已 fail-closed 且回归测试均为手写 manifest，不构成掩护。建议 mock 回退路径补注释说明此为演练简化。
- **A-2（P3）**：§3.5 把旧复现脚本的非零退出表述为"验证通过"，方法论上应正向移植为断言拒绝的新脚本（本人探针 A 已补此缺口，行为无问题）。
- **A-3（P3）**：未知 CLI 错误被打印两次（`console.print` + `click.echo`，`main.py:194-195`）， cosmetic。
- **A-4（P3）**：本人 `d042395` 轮 L4 阻断在本基线复查：B-1（dry-run 落盘）已加门（`prober.py:854-855`）✅；B-2（掩码）已落地 `utils/secrets.py:mask_secrets` 并接入日志展示路径 ✅；**B-3（`--auto-signoff` 默认 True + `HUMAN_MERGE_APPROVED`/`system-runner`）依然存续**（`main.py:1165`、`live_runner.py:189`）。

## 4. 定级意见

- **授予 L3 / PG-2**：`bdc177e` 全部 P1（Codex × 2）经独立 SIM + TEST 双重证实闭环，无过度拦截（正向对照通过）；P0/P1 为零；证据链完整（代码 diff + 自写探针 + 29 专项 + 173 全量 + 信封哈希锚定）。
- **L4 / PG-3 暂不准入**：① Codex 指出的 §7.2 十项 OPS 矩阵证据在本轮范围无新增（同意其 UNKNOWN 判定）；② 本人 d042395-B3（默认代签人类批准事件）依然存续。两者任一即足以暂缓 L4，与"3 批准 / 1 否决 → REWORK 严谨闭环"的共识逻辑一致。

## 5. Reviewer 自审记录

- 首轮探针 A 正向对照曾误判为过度拦截，经查为探针自身 bug（case 3 篡改磁盘文件后未恢复即做对照），修正后通过——已按 GUIDELINES §9 登记"先疑代码、实为脚手架"模式；
- 首轮适配器探针因 API 误用（`inject_task(payload, role=)` 不存在）全 False，经读测试改用正确调用后 7/7 通过——未将误用结论写入判定；
- 未读同期他家 `51fa456` 草稿报告，保持独立；
- 未覆盖：win32、真实厂商 CLI 额度演练、Phase 1 实现。
