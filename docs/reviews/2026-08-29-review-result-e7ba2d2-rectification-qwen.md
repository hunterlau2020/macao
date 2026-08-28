# MACAO 第一/二阶段专家意见闭环整改 独立复审结论（L3 SCENARIO-VERIFIED / PG-2 定级轮）

- **评审日期**：2026-08-29
- **评审人**：qwen（独立评审）
- **被评审范围**：`906b17e` .. `e7ba2d2`（申请文件 `2026-08-29-review-request-Phase1-Phase2-Rectification.md`）
- **评审性质**：**整改闭环复审 / L3 SCENARIO-VERIFIED / PG-2 定级轮**
- **评审方法**：全部声明独立复放——38 项测试重跑、`test-clis`/`e2e-run` 实机重放、签字贯穿链脚本复现、non-git fail-closed 三场景复现、归档树与报表字段物理核对；不采信申请第三节粘贴的输出
- **结论**：**申请所列 P0×3 + P1×6 + P2×2 全部独立复验关闭，属实。** 仅余 2 个 P2（均为本人前两轮已登记的历史遗留项，未在本轮整改清单内）+ 3 个 P3。按门禁纪律"仅余 P2/P3 可宣告定级"，**本评审人支持授予 L3 SCENARIO-VERIFIED / PG-2**；最终门禁以四方专家报告对账为准。

---

## 一、整改项逐条独立复验

| 编号 | 申请声明 | 独立复验方法与结果 | 判定 |
|------|---------|-------------------|------|
| **P0-1** | 配置单一真理源贯穿 + 签字 fail-closed | 以仓库真实 `macao.yaml` 走 `get_orchestrator()` 复现：`require_signoff=True`（上轮实测为 False，本轮已贯通）、`reviewer_ids=['codex','opencode','antigravity']` 来自配置；`require_signoff=True` 且无签字时 `execute_merge_pipeline` 返回"Human signoff required"拒绝合并 | ✅ 关闭 |
| **P0-2** | E2E 证据真实化 + Adapter 注入 + 归档路径 | 实机重放 `e2e-run`：**votes_yes=3 / effective_votes=3**（上轮 0/0）、**Archived 5 files**（上轮 0）；`ConsensusEngine` breakdown 已含 `yes_approve/effective_votes` 键；归档实落 `.macao/archive/<checkpoint_ref>/r1/` | ✅ 关闭 |
| **P0-3** | 沙箱边界诚实定性 | `types.py:74` `SANDBOXED` 注释改"Worktree and working directory isolation (Process-isolated; Container namespaces planned for Phase 3)"；POC 报告改"Git Worktree 物理路径隔离" | ✅ 关闭 |
| **P1-2** | MergeController non-git 逃生舱移除 | 在确认非 git 的目录构造 `MergeController` 复现：返回 `False, "Directory is not a valid git repository (Fail-closed)"` | ✅ 关闭 |
| **P1-3** | Worktree 静默 mkdir 降级移除 | 非 git 目录调 `create_isolated_worktree` 复现：抛 `RuntimeError: ... not a valid git repository (Fail-closed)` | ✅ 关闭 |
| **P1-4** | 硬编码 reviewer/executor 回退移除 | `rg "cc-glm\|kimi\|cc-ds4" orchestrator.py` 无命中；IDs 动态取自注入配置 | ✅ 关闭 |
| **P1-5** | PTY Harness 跨平台优雅跳过 | `integ_harness.py` 含 `HAS_PTY` 探测（13/15 行）与非 POSIX `SKIPPED` 分支（59/64 行） | ✅ 关闭 |
| **P1-6** | `get_changed_files` 伪造兜底移除 | 非法 ref 复现：返回 `[]`（本人 aa173d8 轮 C7 / 906b17e 轮 F4，**三轮追踪至此关闭**） | ✅ 关闭 |
| **P2-5** | AEPEnvelope 重复定义消除 | `rg -l "class AEPEnvelope" src/` 仅 `msg/envelope.py` 一份 | ✅ 关闭 |
| **P2-6** | 合并 SHA 全量精确校验 | `controller.py:87-89` `resolve_ref` 展开完整 40 位后 `head != full_checkpoint_ref` 即拒（前缀比对已废除） | ✅ 关闭 |

## 二、机验独立复放

| 证据项 | 独立复放结果 |
|--------|--------------|
| 38/38 自动化测试 | `PYTHONPATH=src python3 -m unittest discover tests -v` → **Ran 38 tests — OK**（7.53s，含 `test_p0_p1_rectification.py` 4 项专项） |
| Phase 1 实机 `test-clis --cli all` | claude 2.1.250 / codex 2.1.0 / opencode 1.18.25 / agy 1.1.22 **4/4 PASS**，0 孤儿（版本号与申请日略有差异，系真实探针随环境更新，属正常） |
| Phase 2 实机 `e2e-run` | 全 7 步 OK，`decision=APPROVED`，FF 合并成功，终态 DONE，5 份产物归档齐全 |

## 三、残余项（不阻塞定级，登记随下轮闭环）

| # | 级别 | 发现 | 证据 |
|---|------|------|------|
| R1 | P2 | **历史遗留（本人 906b17e 轮 F3，连续两轮未入整改清单）**：未知 `human_resolution` 值仍静默落 `Decision.APPROVED`——人工裁定入口的 typo/非法值等于批准合并，应 fail-fast 抛异常。当前由 CLI 层 `click.Choice` 兜住，但 `resolve_override` 作为公共 API 无自保护 | `consensus/vote.py:138-139` |
| R2 | P2 | **历史遗留（aa173d8 轮 T2）**：`get_schemas_dir()` 向上遍历目录树定位 `docs/schemas/`，pip 安装后必然失联、全部校验判无效。PoC 阶段可暂缓，正式分发前必须改 `importlib.resources`/package data | `core/schema.py:11-19` |
| R3 | P3 | 范围内 `git diff --check` 仍有尾随空白：`POC_VERIFICATION_REPORT.md:25` + `2026-08-28` 旧申请文档 7 处（上轮点名的两份联调方案文档已清理，F6 部分闭环） | `git diff --check 906b17e..e7ba2d2` |
| R4 | P3 | **申请自相矛盾的表述**：§二 P0-2 行称"显式注入配置对应的 3 位 Reviewer Adapter（codex, opencode, antigravity）"，§四.2 又称"使用注入的 `MockAgentAdapter` 实例"——代码事实是后者（按配置 reviewer id 构造的 Mock 实例，`e2e_runner.py:105-111`）。Phase 2 是**适配器驱动的受控仿真**（真实 CLI 能力由 Phase 1 覆盖），建议下轮申请统一口径，避免再次出现"证据与代码不可同时成立"的观感 | `e2e_runner.py` |
| R5 | P3 | E2E 沙箱配置 `require_human_signoff: false` 为自动化有意覆盖——本轮已无测试盲区（`test_config_keys_penetration_and_require_signoff_fail_closed` 覆盖了签字拒绝→阻断路径），仅需在方案文档中显式声明该覆盖是刻意的 | `e2e_runner.py` 内置配置 |

## 四、定级判定

**判定：支持授予 L3 SCENARIO-VERIFIED / PG-2。**

- 上轮四方专家全部 P0（3 项）与 P1（6 项）经独立复验**逐项关闭且无一条虚报**——本轮申请的"✅ 100% VERIFIED"声明与实际代码行为完全相符，与上一轮"证据与代码不符"的情况形成鲜明对比，整改纪律值得肯定；
- 仅余 P2×2（均为历史登记项，非本轮整改范围）+ P3×3，满足"仅余 P2/P3 即可宣告定级"的门禁惯例；
- 本人三轮追踪项（C1/C2/C3/C4/C5/C7 → F1/F2/F3/F4）中除 F3（=R1）外全部闭环。

**附条件**：R1 建议随下一个功能提交强制修复（一行 fail-fast）；最终定级以 zcode/claude/codex 三方复审对账后由 STATUS 统一宣告为准。

## 五、全量对账声明

按 P1-3 治理规则与 `reviews/` 目录对账：本报告前目录含 31 份评审报告 + 5 份申请，STATUS 对账表（`afc85e0` 更新）与目录相符，未发现漏登。本报告为本轮整改复审的第 1 份专家报告。

---

## Reviewer 自审记录

- **方法**：所有"关闭"判定均来自独立复现脚本或实机重放，逐条先复现"上轮失败态→本轮通过态"的对照，不做单点确认；non-git fail-closed 复现时首次测试因 GitManager 路径绑定写错（进程 CWD ≠ 仓库根），纠正后重放通过——登记为复现方法教训
- **连续漏审登记**：上轮（906b17e）报告 F1~F6 本轮全部复核：F1/F2/F6 关闭、F3→R1/F4→P1-6 关闭、F5 由受控仿真定性 + 签字测试补盲部分闭环（残余见 R4/R5）；无新漏审
- **未覆盖项**：真实 LLM 评审产出质量（§15.5 评测范畴）；Windows 平台实测（本机 Linux，P1-5 仅静态核验跳过逻辑）；容器级沙箱（Phase 3 规划，本轮定性诚实）