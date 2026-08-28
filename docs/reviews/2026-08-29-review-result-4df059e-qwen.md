# MACAO 终局整改（P0-NEW×4）独立复审结论（L3 SCENARIO-VERIFIED / PG-2 定级轮）

- **评审日期**：2026-08-29
- **评审人**：qwen（独立评审）
- **被评审范围**：`e7ba2d2..4df059e`（申请文件 `2026-08-29-review-request-L3-Final-Rectification.md`）
- **评审性质**：**终局整改复审 / L3 SCENARIO-VERIFIED / PG-2 定级轮**
- **评审方法**：全部声明独立复放——43 项测试两轮重跑、真实 git 仓库中复现 CI 回滚/缺失远端/message_id 碰撞、`test-clis`/`e2e-run` 实机重放、归档物证物理核验；不采信申请粘贴的输出
- **结论**：**P0-NEW-1 ~ P0-NEW-4 全部独立复验关闭，属实。** 仅余 1 个 P2（历史遗留 schema 打包）+ 4 个 P3。按门禁纪律"仅余 P2/P3 可宣告定级"，**本评审人支持授予 L3 SCENARIO-VERIFIED / PG-2**；最终门禁以四方专家报告对账为准。

---

## 一、整改项逐条独立复验

| 编号 | 申请声明 | 独立复验方法与结果 | 判定 |
|------|---------|-------------------|------|
| **P0-NEW-1** | message_id 升级 16 位高熵、0 碰撞 | `envelope.py:17-21` `str(uuid.uuid4().int)[:16]`；**独立复现 5,000 次采样 0 碰撞**，且 100% 匹配 Schema 正则 `^msg-[0-9]{8}-[0-9]{3,}$` | ✅ 关闭 |
| **P0-NEW-2** | 协议枚举/Schema/PRD 对齐 + 人工裁定修复 | `types.py:18` `UNKNOWN` 恢复（10 态）；`AEPType` 7 种标准类型（24-30 行）与 Schema 枚举一致；`OverrideChoice`（62-67 行）规范为 4 值；`resolve_override` 字符串归一化后非法值走 `OverrideChoice(choice_upper)` **抛 ValueError fail-fast**（orchestrator.py:484） | ✅ 关闭 |
| **P0-NEW-3** | CI 失败原子回滚 + 远端守卫 | 真实 git 仓库复现：**CI 非零退出分支**（`false`）→ 拒绝 + `reset --hard` 后 HEAD 原子复位 ✓；**CI 异常分支**（命令不存在）→ 同样回滚 ✓；**配置不存在远端 `ghost`** → "not found in repository remotes (Fail-closed)" 拒绝 ✓；push 后 `ls-remote` 全量 SHA 校验（controller.py:114-121）静态确认 | ✅ 关闭 |
| **P0-NEW-4** | Adapter 契约全生命周期 + Worktree 事务性 | `e2e_runner.py:173-226` 完整驱动 `start/inject_task/simulate_produce_*/ack/stop`；`orchestrator.py:235-261` 先建全部 Worktree、任一失败即清理已建部分并抛错、**FSM 推进发生在全部成功之后** | ✅ 关闭 |

## 二、机验独立复放

| 证据项 | 独立复放结果 |
|--------|--------------|
| 43/43 自动化测试 | **两轮** `unittest discover` → Ran 43 tests OK ×2（9.53s / 8.43s，0 flake）；含 P0 专项 `test_message_id_entropy_zero_collisions_in_5000`、`test_resolve_override_all_four_choices_and_valid_aep`、`test_merge_controller_ci_gate_failure_rollback`、`test_merge_controller_missing_remote_fail_closed`、`test_worktree_dispatch_transactional_fail_closed` |
| Phase 1 实机 `test-clis --cli all` | claude 2.1.251 / codex 2.1.0 / opencode 1.18.25 / agy 1.1.22 **4/4 PASS**，0 孤儿 |
| Phase 2 实机 `e2e-run` | 全 7 步 OK，votes_yes=3 / effective_votes=3，Archived 5 files，终态 DONE |
| 归档物证 | 从一次早前中断运行的遗留沙箱 `/tmp/macao_e2e_phase2_*/` 物理核验：`.macao/archive/<40位完整SHA>/r1/` 下 3 份 review manifest + vote_result.json 真实存在，路径方案与声明一致 |

## 三、残余项（不阻塞定级，登记随下轮闭环）

| # | 级别 | 发现 | 证据 |
|---|------|------|------|
| R1 | P2 | **历史遗留（aa173d8 轮 T2，连续三轮未修）**：`get_schemas_dir()` 向上遍历定位 `docs/schemas/`，pip 安装后必然失联。本轮范围未触及（`schema.py` 无 diff）。PoC 可缓，分发前必修 | `core/schema.py:13-14` |
| R2 | P3 | **本人三轮追踪项降级**：`vote.py:127-128` 未知 `human_resolution` 仍静默落 APPROVED——但本轮 `resolve_override` 已在入口 fail-fast（ValueError），生产路径已闭合；`VoteEngine.resolve()` 作为公共 API 的裸调用仍是隐患，建议加一行 fail-fast 彻底关闭 | `consensus/vote.py` |
| R3 | P3 | **申请 §二.5 "0 尾随空白"声明不实**：`git diff --check e7ba2d2..4df059e` 仍有 10 处尾随空白（`POC_VERIFICATION_REPORT.md:25` + 上轮整改申请文档 9 处）——申请方跑的很可能是裸 `git diff --check`（仅查工作区）而非范围检查。代码文件本身干净 | `git diff --check e7ba2d2..4df059e` |
| R4 | P3 | E2E Harness 中断运行时临时沙箱泄漏（发现 8-28 遗留 `/tmp/macao_e2e_phase2_ocopgtng` 未清理）；正常退出路径清理正确（`e2e_runner.py:283-285`） | 物理核验 |
| R5 | P3 | push 后 `ls-remote` 远端 SHA 校验仅有静态确认与单测覆盖，未做真实远端动态复现（本机无可用远端）；逻辑直白且 fail-closed，风险低 | `controller.py:114-121` |

## 四、定级判定

**判定：支持授予 L3 SCENARIO-VERIFIED / PG-2。**

- 四方专家上轮新提的 4 个 P0 经独立复验**逐项关闭且无一条虚报**，其中 message_id 碰撞（claude 发现、zcode 双重复现坐实）已以 10^16 空间彻底消除；
- 本人三轮追踪的签字贯穿、证据真实化、fail-closed 三件套在前轮已闭环，本轮复审中再次复放保持绿；
- 仅余 P2×1（历史登记项）+ P3×4，满足"仅余 P2/P3 即可宣告定级"的门禁惯例。

**附条件**：R1 随分发准备强制修复；R2 一行修复建议并入下一提交；最终定级以 zcode 复审补齐后四方对账、由 STATUS 统一宣告为准。

## 五、全量对账声明

按 P1-3 治理规则与 `reviews/` 目录对账：目录现有 38 份评审报告（含 claude/codex 已出具、尚未提交的 4df059e 轮 2 份）+ 6 份申请；STATUS.md 存在未提交修改（他方登记中）。本报告为 4df059e 轮第 3 份专家报告，zcode 报告待补。

---

## Reviewer 自审记录

- **方法**：延续"上轮失败态→本轮通过态"对照复现；CI 回滚同时覆盖非零退出与异常两个分支；message_id 独立采样而非仅读测试断言；归档物证取自真实运行遗留沙箱而非申请截图
- **复现过程教训登记**：本轮复现中曾误判 `.macao` 目录被产品代码删除（疑似新 P0），经纯 bash 对照实验定位真因为**我的复现脚本 `git add .` 将 `.macao/state.db` 扫入 feat 分支提交**、切回 main 时 git 按跟踪文件正常删除——属复现方法缺陷而非产品缺陷，特此登记避免误报；同时确认 e2e 沙箱自带 `.gitignore` 防护此陷阱
- **连续漏审登记**：前轮 R1（静默 APPROVED）本轮由入口 fail-fast 部分闭环（降级 P3）；无新漏审
- **未覆盖项**：真实远端 push 动态复现（R5）；真实 LLM 评审质量（§15.5 范畴）；Windows 平台实测（本机 Linux）