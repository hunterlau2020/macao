# MACAO Phase 1/2 整改闭环 独立复核结论（L3 / PG-2 定级轮）

- **评审日期**：2026-08-29
- **评审人**：zcode（独立评审，GLM）
- **评审对象**：commit `906b17e` .. `e7ba2d2`（四方评审 P0×3 + P1×6 + P2 整改 + `test_p0_p1_rectification.py` 专项回归 + 38 项全量测试）
- **对齐基准**：`docs/MACAO_PRD_v2.md` v2.3.1 + `docs/MACAO_REVIEW_GUIDELINES.md` v1.0（L3 = SCENARIO-VERIFIED）
- **申请文件**：`docs/reviews/2026-08-29-review-request-Phase1-Phase2-Rectification.md`
- **结论**：**本轮不予 L3 SCENARIO-VERIFIED / PG-2**。整改质量高——本人上轮（`906b17e`）清单 13 项中 **12 项经独立复验确认关闭、无一虚报**；但同轮 claude 独立发现的新 P0（`message_id` 生成碰撞）经本人**双重复现坐实**（数学仿真 + 真实 `MessageBus.publish` 循环第 129 条触发主键冲突崩溃），单独构成 PG-2（乃至 PG-1"P0 为零"）的阻断项。**修复该 P0 后，本人支持在补齐超时场景证据的前提下授予 L3**。

---

## 一、整改逐项独立复验（对照本人 `906b17e` 轮清单 + 申请 §二对照表）

| 编号 | 本人上轮发现 | 独立复验方法与结果 | 判定 |
|---|---|---|---|
| P0-1 配置注入键路径断裂 | `core/config.py:53-92`：`to_runtime_config()` 双层结构（原始嵌套 + 规范化运行时键）；`orchestrator.py` 读 `require_signoff`/`ci_gate_command`/`remote_name` 等规范化键；`require_signoff` 默认值改为 **True（fail-safe 方向正确）**；专项测试 `test_config_keys_penetration_and_require_signoff_fail_closed` PASS；claude 另以 `require_human_signoff: true` + 无签字实测 `execute_merge` 返回拒绝 | **✅ 关闭** |
| P0-2 e2e 证据真实度 | 本机实测 `e2e-run`：**votes_yes=3 / effective_votes=3**（`e2e_runner.py:249-250` 改为 `approve` 主键 + `yes_approve` 兼容读取；`consensus/engine.py` breakdown 补齐双键）；**Archived 5 files**（`.dev.yml` + 3×`.review.yml` + `vote_result.json`，路径改 `archive/<checkpoint_ref>/r1` 与 fsm 一致，`status` 判定增加 `len(archived_files) > 0` 非空硬条件 `e2e_runner.py:292`）；**worktree 实际建给 codex/opencode/antigravity**（适配器注入驱动，硬编码 cc-glm/kimi 回退消除） | **✅ 关闭** |
| P1-1 e2e 伪造产物/L3 主张 | 适配器已注入（`e2e_runner.py:106-122`）驱动 reviewer 身份与分发白名单；但 `.dev.yml`/`.review.yml` 内容仍由 runner 直接写 YAML（`:175-243`），未走适配器产物方法；申请口径已改为"适配器驱动的受控仿真"（§四.2 明示 MockAgentAdapter）——**定性诚实化**。以 L3 SCENARIO-VERIFIED 判据衡量（L3 不要求真实 CLI，那是 L4/OPS 范畴），该形态可接受，残余见 §四 P3-1 | **✅ 关闭（附注）** |
| P1-2 merge"模拟成功"逃生舱 | `merge/controller.py:54-57`：非 git 目录 `return False, "...not a valid git repository (Fail-closed)"`；专项测试 PASS | **✅ 关闭** |
| P1-3 worktree fail-open 降级 | `utils/git_utils.py:98-105`：非 git 目录 / commit 不存在 / worktree 命令失败均抛 `RuntimeError`；专项测试 PASS | **✅ 关闭** |
| P1-4 硬编码回退实际生效 | `orchestrator.py:64-75`：reviewer/executor ID 自注入适配器与配置动态派生，默认回退同步为 `["codex","opencode","antigravity"]`；实测 worktree 接收方与配置一致（本机 e2e 复现）；`cc-ds4/cc-glm/kimi` 在 orchestrator 中无命中 | **✅ 关闭** |
| P1-5 PTY harness 无平台检查 | `integ_harness.py:11-15` `HAS_PTY` 探测 + 非 POSIX SKIPPED；**本机（win32，装有 claude/codex CLI）6 次全量套件 38/38 OK**——上轮 3 FAIL 场景消除 | **✅ 关闭** |
| P1-6 `get_changed_files` 伪造兜底 | `utils/git_utils.py:66-69`：失败一律返回 `[]`；专项测试 PASS（qwen 追踪三轮的 C7/F4 至此关闭） | **✅ 关闭** |
| P2-1 push 未接线 | `orchestrator.py:383-390` 传 `remote_name`；e2e 建立 bare remote 并 push——本机实测 **remote HEAD（b42299b7）== checkpoint（b42299b7）** | **✅ 关闭** |
| P2-2 归档校验空转 | 见 P0-2：非空硬条件 + 路径一致 | **✅ 关闭** |
| P2-3 L3 术语/判据 | 术语已改 **L3 SCENARIO-VERIFIED**（采纳）；但 **超时场景仍为零覆盖**（`grep -rln "timeout|超时" tests/` 无命中；§13 五项超时机制仍无实现）——见 §四 P2-1 | **部分关闭** |
| P2-6 SHA 前缀弱校验 | `merge/controller.py:87-89`：`resolve_ref()` 展开完整 SHA 后 `head != full_checkpoint_ref` 即拒 | **✅ 关闭** |

## 二、阻断项：新 P0（message_id 碰撞）——本人双重复现

同轮 claude 首先发现（`2026-08-29-review-result-e7ba2d2-claude.md` §三）；本人**不采信其报告、独立重做**：

1. **数学仿真**（20 万样本）：`msg/envelope.py:19` `str(uuid.uuid4().int)[:4].zfill(4)`——取 122 位随机整数十进制串的前 4 位，仅产生 **8983 个不同后缀**，两两碰撞概率 **2.64e-4**（均匀 4 位数为 1e-4；规范 UUID 应为 ~1e-37）。同库同日 k 条消息至少一撞：k=20 → 4.9%，k=60 → 37.3%，k=120 → 84.8%。
2. **真实代码路径复现**（win32 本机）：单库循环 `MessageBus.publish("STATE_CHANGED", ...)`——**第 129 条触发 `sqlite3.IntegrityError: UNIQUE constraint failed: message_queue.message_id`**。
3. **影响面**：`message_queue.message_id` 为主键；真实运行中一个项目库单日积累数十至百余条消息（开发分发 + 3 Reviewer 广播 + 返工 + ping）即进入高危区，`publish` 抛错沿 `dispatch_review_requests` 上抛使编排崩溃——核心消息通路在正常用量下的**随机崩溃**。同时证伪申请"38/38 100% PASS"的无条件表述（本机 6/6 通过恰说明其概率性：约四分之一运行会失败）。
4. **定级**：沿用本项目先例（`906b17e` 轮三方均将"申报证据与实测不符/核心路径崩溃"定为 P0）：**P0**。修复极简单（`uuid.uuid4().hex[:12]` 或完整 uuid，保持 `^msg-[0-9]{8}-[0-9]{3,}$` 模式兼容可截取 hex 数字串），建议附"万条 publish 无碰撞"回归测试。

## 三、评审人机验记录（win32 / Python 3.11.9）

| 项目 | 结果 |
|---|---|
| 全量套件 ×6 | **38/38 OK ×6**（PTY 4 项在 win32 优雅 SKIPPED——上轮 3 FAIL 消除） |
| `macao e2e-run` | 全 7 步 OK；votes_yes=3 / effective_votes=3 / Archived 5 files / 终态 DONE |
| e2e 深检 | worktree 实际接收方 = antigravity/codex/opencode；bare remote 推送后 HEAD == checkpoint（b42299b7） |
| publish 循环 | 129 条触发主键冲突（§二） |
| `git diff --check` | clean（工作区） |

## 四、残余问题（P2/P3，不阻断本轮定级结论的方向，随修复 P0 一并处理）

- **P2-1 超时场景零覆盖**：GUIDELINES §2.1 对 L3 明列"超时"；当前无任何超时机制实现与测试（弃权降级仅覆盖"票已到且为 ABSTAIN"的算术侧，未覆盖"超时未响应→标记弃权"的时间侧）。建议以可注入时钟（fake clock）的单元测试 + PRD §6.1 推演补齐后作为 L3 授予的条件项。
- **P2-2**（与 qwen R1 一致，本人复认）：`consensus/vote.py:138-139` 未知 `human_resolution` 值静默落 `Decision.APPROVED`——人工裁定入口的非法输入等于批准合并，应 fail-fast。CLI 层 `click.Choice` 兜底不构成公共 API 的自保护。
- **P3-1** e2e 产物内容仍绕过适配器（runner 直写 YAML）；且 Mock 适配器 ID 硬编码于 runner（`:106-115`）而非读 `config["reviewer_ids"]`——建议改走 `simulate_produce_*` 并自配置派生。
- **P3-2** `e2e_runner.py:184` `.dev.yml` 仍以分支名 `"main"` 作 `git.base_commit`（本人连续三轮登记；e2e 主链路已用 merge-base，仅此演示数据残留）。
- **P3-3** `pyproject.toml:31-32` `pytest`/`prompt_toolkit` 死依赖仍在（claude 评审两轮前已指出）；`cli task create` 仍伪造 `tests_passed: True` 验收标准。

## 五、定级判定与闭环路径

1. **本轮不予 L3 / PG-2**：PG-2 以 PG-1（P0/P1 为零）为前提；message_id 碰撞 P0 经双重复现成立（§二）。与 claude 结论一致；qwen 的支持结论系其未覆盖该新发现所致——按"真理不等于投票"，以可复现证据为准。
2. **对整改本身的评价**：申请 11 项对照声明与代码行为**全部相符**，与上轮"证据与代码不符"形成鲜明对比；本人清单 13 项关 12 项，剩余 1 项（超时）属判据补齐而非整改虚报。整改纪律应予肯定。
3. **闭环路径**（预计单点修复 + 快速复核）：修 `envelope.py:19`（附无碰撞回归测试）→ 任一已排班 reviewer 书面确认该单点 + 超时场景测试/推演补齐登记 → **本人支持授予 L3 SCENARIO-VERIFIED / PG-2**（届时按 GUIDELINES §2.1 逐场景对账：全同意 ✓、1:1 僵局 ✓、弃权 ✓、崩溃恢复 ✓、返工循环 ✓、超时 = 补齐项）。

## 六、Reviewer 自审记录

- 本报告未采信 claude/qwen 既有结论，全部复验独立完成；message_id P0 的两重复现（仿真 + 真实代码路径）均在本机执行、命令可重放。
- GUIDELINES §9 五项自检：全部 REJECT 附路径+行号或实测输出；"38/38×6 OK"如实报告且明确其与碰撞 P0 并不矛盾（概率性缺陷的幸存者偏差恰是本题考点）；无确定性用语未标注。
