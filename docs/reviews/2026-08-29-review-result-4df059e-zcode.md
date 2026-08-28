# MACAO Phase 1/2 终局整改 独立复核结论（L3 / PG-2 定级轮）

- **评审日期**：2026-08-29
- **评审人**：zcode（独立评审，GLM）
- **评审对象**：commit `e7ba2d2` .. `4df059e`（四方复审 P0-NEW-1~4 闭环整改 + `test_p0_p1_rectification.py` 扩充至 9 项 + 43 项全量测试）
- **对齐基准**：`docs/MACAO_PRD_v2.md` v2.3.1 + `docs/MACAO_REVIEW_GUIDELINES.md` v1.0（L3 = SCENARIO-VERIFIED）
- **申请文件**：`docs/reviews/2026-08-29-review-request-L3-Final-Rectification.md`
- **结论**：**本轮不予 L3 SCENARIO-VERIFIED / PG-2——差一步**。申请所列 4 项 P0-NEW 整改经独立复验**全部真实关闭、无一虚报**（含本人上轮双重复现的 message_id 碰撞在本机复测归零）；但 **L3 判据中明列的"超时"场景仍为零覆盖**（`tests/` 无任何超时测试、运行时无时钟机制）——这是本人上轮报告明示的授予前提之一（`2026-08-29-review-result-e7ba2d2-zcode.md` §五.3），也是 codex 上轮结论明列的 L3 缺口（其报告 §1"未达到 L3 明定的超时…要求"），本轮申请未包含该项。**补齐超时场景证据（最小代价：fake-clock 单测）并顺手修复两处新登记 P2 后，本人支持授予 L3 / PG-2。**

---

## 一、整改逐项独立复验（对照申请 §一）

| 编号 | 申请声明 | 独立复验方法与结果 | 判定 |
|---|---|---|---|
| **P0-NEW-1**<br>message_id 碰撞 | 16 位高熵随机后缀，0 碰撞 | `msg/envelope.py:16-22` 确认 `str(uuid.uuid4().int)[:16]`（10^16 空间，严格符合 `^msg-[0-9]{8}-[0-9]{3,}$`）；**本人上轮崩溃复现脚本重放：500/500 publish 全部成功**（上轮第 129 条即 IntegrityError）；全量套件本机 **6 次运行 43/43 全绿、0 flake**；`test_message_id_entropy_zero_collisions_in_5000` PASS | **✅ 关闭** |
| **P0-NEW-2**<br>协议枚举/裁定断裂 | 恢复 10 状态、7 AEP 类型、4 裁定值 | `core/types.py:8-19` AgentState 含 `UNKNOWN` 恢复 ✓；`:22-30` AEPType 七种标准类型与 Schema 一致 ✓；`:62-67` OverrideChoice 四值 ✓；`test_resolve_override_all_four_choices_and_valid_aep` 覆盖四分支（含字符串 `"REWORK"` 归一化——codex 上轮 ValueError 反例消除）且**断言全部发出消息通过 Draft-07 Schema 校验**；`resolve_override` 广播改用标准 `STATE_CHANGED` | **✅ 关闭** |
| **P0-NEW-3**<br>merge 原子回滚/远端 | pre_merge_head 回滚 + 远端三重校验 | `merge/controller.py:64`（记录 pre_merge_head）、`:84-89`（CI 失败 `reset --hard` 回滚）、`:92-98`（HEAD==完整 checkpoint 否则回滚）、`:101-106`（remote 不存在 Fail-closed + 回滚）、`:108-112`（push 失败回滚）、`:114-121`（ls-remote 远端 SHA==checkpoint 否则回滚）；两项专项测试 PASS。codex 上轮"状态说返工、目标分支已前移"的双账本反例路径消除 | **✅ 关闭** |
| **P0-NEW-4**<br>Adapter 契约驱动/事务性分发 | e2e 全生命周期驱动 + worktree 事务 | `e2e_runner.py:173-181`（executor `start→inject_task→simulate_produce_dev_manifest→stop`）、`:211-226`（reviewer `start→inject_task→simulate_produce_review_manifest→ack→stop`）——codex 上轮"契约方法零调用"反例消除；`orchestrator.py:204-259` dispatch 改事务性：**全部 worktree 准备成功后才 E2 转移并归档**，失败清理并保持 READY_FOR_REVIEW；`test_worktree_dispatch_transactional_fail_closed` PASS；本机 e2e-run 实测 `status=PASS / archived=5 / votes_yes=3` | **✅ 关闭** |

**附带确认**：e2e 的 `.dev.yml` 已删除伪 `base_commit: "main"` 字段（本人连续三轮登记的 P3 至此关闭）；`vote_result` 对 CANCELLED 整体省略 `next_step`（schema 合法，P0-NEW-2 子项 4 落实）。

## 二、未满足的 L3 授予条件：超时场景证据（本轮唯一阻断）

- GUIDELINES §2.1 对 L3 SCENARIO-VERIFIED 的最低条件原文："**全同意/1:1 僵局/超时/弃权/崩溃恢复/返工循环**等场景均有可复现推演或测试证据"。当前对账：全同意 ✓（S1/e2e）、1:1 僵局 ✓（S3/deadlock 测试）、弃权 ✓（consensus 弃权算术）、崩溃恢复 ✓（reconcile ×2）、返工循环 ✓（S2）、**超时 ✗**。
- 实证：`grep -rln "timeout|超时|deadline|fake_clock|mock_clock" tests/` **零命中**；运行时无任何定时器/时钟机制（§13 五项超时仍无实现）。弃权算术测试覆盖的是"票已到且为 ABSTAIN"，未覆盖"超时未响应→Orchestrator 标记弃权"的时间侧链路（PRD §6.1/§6.2/§3.3 超时行）。
- 本轮申请 §一清单与 §三定级请求均未提及超时——非虚报，是遗漏了 codex 与本人两份上轮报告中的明示条件。
- **最小补齐路径**：以可注入时钟（fake clock）的单元测试覆盖"per_reviewer 超时未响应 → 标记弃权 → 有效票不足 → DEADLOCK → E7 人工裁定"全链（约一个测试函数 + 一个可注入的 deadline 判定入口），或提交经评审认可的等价推演文档。

## 三、新登记问题（P2×2 + P3×2，均非本轮阻断项，建议随超时补齐一并处理）

- **P2-1（回归）** `consensus/vote.py:176-183`：Schema 校验被移至**写盘之后**——`write_to_disk` 先落盘再 `validate_vote_result` 抛错，无效产物会先污染磁盘再报错。上轮（`e7ba2d2`）顺序为"先校验后写盘"，本轮重写时倒置，违反 fail-closed 纪律。虽当前无已知非法生成路径（测试全绿），防御顺序应复原。
- **P2-2（第三轮遗留）** `consensus/vote.py:128-129`：未知 `human_resolution` 值仍静默落 `Decision.APPROVED`（qwen R1，`e7ba2d2` 轮登记后连续两轮未入整改清单）——人工裁定入口的非法输入等价于批准合并，应 fail-fast 抛异常。
- **P3-1** `merge/controller.py:116`：`ls-remote` 命令失败或返回空时，远端 SHA 校验被**静默跳过**而非 fail-closed（`if code_ls == 0 and out_ls.strip():` 不满足即放行）——校验步骤自身的 fail-open。
- **P3-2** `pyproject.toml:31-32`：`pytest`/`prompt_toolkit` 死依赖仍在（claude 评审三轮前指出）。

## 四、评审人机验记录（win32 / Python 3.11.9，全部可复现）

| 项目 | 结果 |
|---|---|
| 全量套件 ×6 | **43/43 OK ×6**（含 PTY 4 项 SKIPPED；0 flake） |
| 碰撞复现重放 | **500/500 publish 成功**（上轮同脚本第 129 条 IntegrityError） |
| `macao e2e-run` | votes_yes=3 / Archived 5 files / 终态 DONE；适配器契约生命周期驱动 |
| 深检 | 4 分支裁定测试含字符串归一化与全消息 Schema 断言；事务性分发代码路径核对 |
| `git diff --check` | clean（工作区） |

## 五、定级判定与闭环路径

1. **本轮不予 L3 / PG-2**：L3 判据"超时"场景零证据——这是 GUIDELINES 明列项、本人与 codex 两份上轮报告的明示条件，不能豁免（"P2/P3 可延期"不适用于定级最低条件的显式清单项）。
2. **对整改的评价**：4 项 P0-NEW 全部真实闭环且质量高（原子回滚五处一致、事务性分发、契约驱动、碰撞归零），且修复了 codex 独立发现的协议层回归（该回归本人上轮未能捕获，已在自审记录登记）。当前与 L3 的距离从"两项 P0 + 判据缺口"收敛为**单一判据补齐**。
3. **闭环路径**（预计单点补齐 + 快速复核）：补 fake-clock 超时链路测试（或等价推演文档）→ 顺手复原 `vote.py` 校验顺序 + 修 R1 → 任一已排班 reviewer 书面确认 → **本人支持授予 L3 SCENARIO-VERIFIED / PG-2**。

## 六、Reviewer 自审记录

- **漏审登记（GUIDELINES §9）**：`e7ba2d2` 轮本人未发现 `types.py` 协议枚举被改坏（UNKNOWN→HUMAN_OVERRIDE、OverrideChoice 改名）——该轮本人复核聚焦于自身上轮清单的闭环验证，未对"本轮新增改动"做全量 diff 审读，属 B 类盲点（"整改回归"检测缺口）。本轮已对 `e7ba2d2..4df059e` 全量 diff 补齐审读，并因此捕获 P2-1（校验顺序倒置）。后续轮次将把"整改 diff 全量重读"列为固定动作。
- 本报告未采信其他专家结论；全部判定附路径+行号或本机实测输出；6×43/43 与 500/500 publish 均为实际执行结果。
