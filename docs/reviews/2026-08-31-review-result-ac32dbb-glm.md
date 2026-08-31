# MACAO Phase 3 PG-3 / L4 终审验收 对齐/评审结论

- **评审日期**：2026-08-31
- **评审范围**：Commit `15e8918`..`b76cbfb`（完整链 `3c5ed32`..`ac32dbb`），重点 `ac32dbb`
- **评审对象**：`docs/reviews/2026-08-31-review-request-Phase3-PG3-L4-Final.md`
- **对齐基准**：`docs/MACAO_PRD_v2.md`（v2.4）、`docs/MACAO_REVIEW_GUIDELINES.md` v1.0
- **评审人**：glm（独立复审，全部关键声明本机复现）
- **结论**：**L4 RELEASE-READY / PG-3 有条件授予（CONDITIONAL GRANT）**——运行时判据全部满足；唯一未闭环项为 1 处文档徽章与申请声明矛盾（P1-F1，1 行修复），修正并提交单 commit 复核后 L4/PG-3 即生效。L3/PG-2 保持有效，无回归。

---

## 0. Reviewer 自审记录

按 §9 强制自检 5 项逐条执行。上轮（15e8918，本 reviewer）提出的 P1-R1/P1-R2 与 P2-R3/R4 已逐项复核闭环情况（见 §1）。本轮新登记一次 checklist-B/C 类偏差（P1-F1，申请声称"README 徽章对齐 81/81"与实测矛盾）。

## 1. 上轮阻断项闭环复核（本 reviewer P1-R1/P1-R2/P2-R3 视角，交叉验证其他专家项）

| 上轮项 | 闭环证据（本机核验） | 状态 |
|---|---|---|
| **P1-R1 live-run 模拟评审冒充实机** | `live_runner.py:134-152`：真实调用 `dispatcher.dispatch_review_in_worktree`，物理创建/清理 worktree（`test_live_dispatcher_worktree_mock_execution` 验证）；评审适配器诚实配置为 `mock-cli`（live_runner.py:52-54），不再伪装真实 CLI。**"实机演练"措辞降级为真实管线 + mock 适配器，措辞与事实对齐** | **VERIFIED** |
| **P1-R1 真实操作员签字** | `live_runner.py:171-175`：默认签字诚实标注 `signer: "system-runner"`；`--no-auto-signoff` 下 runner 停在 MERGING 并提示 `macao merge approve`（本机实测 exit 0，状态 MERGING）；`main.py:299` `merge approve` 命令真实存在——**人工接管入口真实可用** | **VERIFIED** |
| **P1-R2 确定性措辞失实** | live-run 输出、配置、签字均已按事实表述；遗留一处见 P1-F1 | **PARTIALLY_VERIFIED** |
| **P2-R3 ABSTAIN 语义失真** | `review_manifest.schema.json`（src/docs 一致）:26/:59/:75-76 支持 `ABSTAIN`/`ABSTAINED` 且 allOf 互锁；`types.py:45`；`live_dispatcher.py` 新调和逻辑 ABSTAIN→ABSTAINED 语义正确 | **VERIFIED** |
| **P2-R4 上下文绑定弱** | reviewer.id / checkpoint_ref / review_round 三维强校验保留并加 strip/int 归一；但新增**双向前缀匹配**（见 P2-F3） | **PARTIALLY_VERIFIED** |

## 2. 本轮申请各项声明核验

| 申请项 | 证据 | 状态 |
|---|---|---|
| Extractor 末块优先 | `live_dispatcher.py:63,141-143`：收集全部有效块返回 `valid_candidates[-1]`；`test_review_extractor_last_valid_block_wins` | **VERIFIED** |
| 矛盾票 Fail-Closed | `live_dispatcher.py:88-101`：6 组 status/vote 矛盾组合全部拒绝；`test_review_extractor_rejects_contradictory_vote_and_status` | **VERIFIED** |
| Mock 契约对齐 | `mock.py:23` `cli_name="mock-cli"` 默认值；`live_dispatcher.py:179-180` 专用构造；Mock 缺省行为生成完整 manifest 并落盘 worktree | **VERIFIED** |
| 适配器注入 review_round/diff | 12 处 `review_round` 注入（如 `claude.py:96-103` diff 段） | **VERIFIED** |
| gitignore 逐行差量升级 | `wizard.py:80-103` 9 条规则逐条比对幂等追加；`test_wizard_gitignore_isolation_upgrade` | **VERIFIED** |
| 2/3 多数票修正 | `wizard.py:139` `math.ceil(2*rev_count/3)` | **VERIFIED** |
| setup 备份防护 | `main.py:362-364` `macao.yaml.bak.<ts>` | **VERIFIED** |
| FAQ/UC1 洁净度 | FAQ 无 `e2e-run` 残留；`git diff --check 3c5ed32..ac32dbb` 本机 rc=0 | **VERIFIED** |
| **81/81 全绿** | 本机复现 `Ran 81 tests in 22.356s, OK` | **VERIFIED** |
| **live-run 7 步** | 本机复现：默认模式 DONE（7 步 OK，5 产物归档）；`--no-auto-signoff` 模式停在 MERGING 待人工 | **VERIFIED (OPS)** |
| **人工接管演练** | `test_manual_override_resolution`（test_phase3.py:356-440）：1 赞成+1 反对+1 超时弃权 → DEADLOCK HOLD 于 CONSENSUS_CHECK → `resolve_override("APPROVED")` → MERGING → 签字 → 合并 DONE，全部真实 FSM/git 状态机路径 | **VERIFIED (TEST)** |
| **README 徽章对齐 81/81** | **CONTRADICTED**：`README.md:5` 实测仍为 `tests-75/75 PASS`（Gate 徽章 L3/PG-2 已对齐 :7，但 tests 徽章未更新） | **CONTRADICTED** |

## 3. 分级问题清单

### P1（L4 生效前置条件，1 行修复）

- **P1-F1**　申请 §一"P1-6"行声称"README 徽章对齐为 …`81/81 PASS`"，实测 `README.md:5` 仍为 `75/75 PASS`。属声明矩阵"已完成无证据"命中（checklist-B/C）。修复：徽章改 `81/81`（或改为动态区间表述），申请文档无需回改但 STATUS 登记本证伪点。**不影响运行时行为，但按"回归无 P0/P1"字面判据须先修正。**

### P2（可延期，须登记）

- **P2-F2**　L4 演练链路中评审均为 `mock-cli` 适配器（诚实标注），尚无一次真实 LLM CLI 参与的端到端非全同意评审演练记录。建议作为发布后首个跟进项（配合 `preflight`/`test-clis` 已验证的 PTY 能力）。
- **P2-F3**　`live_dispatcher.py:126-128` checkpoint_ref 改为双向前缀匹配（`startswith`）：缩写 SHA 匹配属有意放宽，但理论上允许仅共享前缀的错误 ref 通过（40 位 SHA 下风险极低）。建议注释标注意图或限定位数。

### P3

- **P3-F4**　`test_manual_override_resolution` 中 `signer: "lead-architect"` 为测试夹具字面量；作为"人工接管演练"证据时应说明系自动化替身，避免下游误读为真人操作记录。
- **P3-F5**　live-run 演练仅有全同意路径经 dispatcher 真实跑通；非全同意/超时路径目前在单测层闭环（FSM 真实、输入构造）。

## 4. L4 判据对账

| L4 条件（指南 §2.1/§3.3） | 状态 |
|---|---|
| L3 基础 | ✅ 维持有效（81/81 本机复现，Phase 2 已认证路径无回归） |
| 人工接管路径演练 | ✅ DEADLOCK→HOLD→`resolve_override`→签字→merge→DONE 全路径真实 FSM 实测；`--no-auto-signoff` + `macao merge approve` 提供真实人工入口（本机验证停在 MERGING） |
| 回归无 P0/P1 | ⚠️ P1-F1（文档徽章，1 行） |
| 用户手册齐备 | ✅ README/FAQ 命令文档与实际 CLI 对齐 |
| OPS VERIFIED | ✅ live-run（含 no-signoff 变体）、daemon --once、preflight、diff-check 本机复现 |

## 5. 最终判定

- **L4 RELEASE-READY / PG-3：有条件授予**。条件：修正 `README.md:5` tests 徽章为 81/81（P1-F1），提交单 commit 后 L4/PG-3 即时生效，无需全量复审（复核范围仅限该 diff）。
- **维持 L3/PG-2**：无回归。
- **P2-F2/F3、P3-F4/F5** 登记 STATUS.md，作为发布后跟进项，不阻断本次授予。
