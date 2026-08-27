# MACAO Phase 1/2 受控联调与架构装配 独立评审结论（L3 / PG-2 定级轮）

- **评审日期**：2026-08-28
- **评审人**：zcode（独立评审，GLM）
- **评审对象**：commit `aa173d8` .. `906b17e`（架构装配整改、4 款 CLI 适配器矩阵、Phase 1 PTY 联调 Harness、Phase 2 E2E Runner、34 项测试）
- **对齐基准**：`docs/MACAO_PRD_v2.md` v2.3.1 + `docs/MACAO_REVIEW_GUIDELINES.md` v1.0（L3 = **SCENARIO-VERIFIED**）
- **申请文件**：`docs/reviews/2026-08-28-review-request-Phase1-Phase2-Integration.md`
- **结论**：**未达 L3 / PG-2，不授予**。维持 **L2 SPEC-CODE-ALIGNED / PG-1**，并确认两项增量成绩（编排管线 E2E 自动化闭环、消息总线独立投递表）。本轮发现 **P0 ×2、P1 ×6、P2 ×6、P3 ×4**，其中两项 P0 分别是"配置注入键路径断裂导致签字门禁静默失效"与"申请/POC 报告的机验证据与代码实测输出不符"——后者按 GUIDELINES §1.1/§3.3（作者自述与单一示例不能代替证据）直接影响定级资格。

---

## 一、评审人实测记录（win32 / Python 3.11.9，全部可复现）

| 项目 | 申请声明 | 评审人实测 |
|---|---|---|
| `unittest discover tests` | 34/34 PASS (100%) | 初跑 31 项（本机缺 `rich`，`test_config` 导入 ERROR；申请未给出依赖安装步骤）；`pip install rich` 后 **34 ran / 3 FAIL**——3 项失败全部为 `test_integ_harness` PTY 测试（本机装有 claude 2.1.233/codex 2.1.0，win32 无 `pty` 模块，harness 无平台检查直接 FAIL，测试仅对"CLI 未安装"接受 SKIPPED） |
| `macao e2e-run` | 报告显示 votes_yes=3、effective_votes=3、Archived files persisted、reviewers=[codex,opencode,antigravity] | **实测输出 votes_yes=0、effective_votes=0（键名不存在，恒 0）；Archived 0 files（归档路径键错配）；报告 reviewers 列表为硬编码**——详见 P0-2 |
| `macao doctor` | 只读幂等 | ✓ 正常，无副作用（Arch-4 落实） |
| `macao preflight` | 环境探针 | ✓ 诚实探测（本机 claude/codex/kimi 检出 OK，opencode/agy 未装 FAIL） |
| e2e 实际 worktree 接收方 | "为 3 位 Reviewer 分别创建专属 Worktree" | **实测 worktree 实际建给 `cc-glm`、`kimi`**（orchestrator 硬编码回退名单，含已被替换的 Kimi），报告展示的 codex/opencode/antigravity 为 e2e_runner 硬编码字符串 |
| e2e 实际归档键 | 产物追加归档 persisted | 实测归档键 = checkpoint SHA（`9454c49...`），而 e2e_runner 检查 `archive/<task_id>/r1` → 恒 0 文件 |
| `git diff --check` | clean | ✓ clean |

**值得明确肯定**：e2e 编排管线本身真实且可复现——真实 git init/commit/checkout/FF merge、FSM E1→E4a 全程、2/3 仲裁、目标分支 HEAD 与 checkpoint_ref SHA 精确相等校验、终态 DONE，在本机一次通过。这是真实的工程增量，不是伪造的。

## 二、P0：必须先解决

### P0-1 配置注入键路径断裂：`require_human_signoff: true` 被静默忽略，签字门禁永不激活

- `core/config.py:53-56`：`ConfigManager.load_config` 返回**嵌套** dict（`policy.max_rework_rounds` / `merge.require_human_signoff` / `merge.ci_gate_command`）；
- `workflow/orchestrator.py:49-54, 220, 344-345`：Orchestrator 读取**顶层键** `config.get("max_rework_rounds", 3)`、`config.get("require_signoff", False)`、`config.get("ci_gate_command")`——与嵌套结构永不匹配，**全部命中默认值**；
- 后果链：`macao.yaml` 中 `require_human_signoff: true`（PRD §13 刻意的保守安全默认、§14.5 第 4 步强制人工签字）→ orchestrator 恒传 `False` → `merge/controller.py:49-53` 签字检查恒跳过 → **E4a 在未经人工放行时可直接达成**。同理 `ci_gate_command` 配置恒失效、`max_rework_rounds` 恒为默认 3。
- 申请 §二.1"CLI 组装根统一通过 get_orchestrator() 注入配置字典，**彻底消除硬编码默认值**"与代码事实相反——注入的字典键从未被消费。
- 修复方向：Orchestrator 统一改读嵌套路径（或 get_orchestrator 做一次显式展平映射并写测试断言每个键真正到达）。

### P0-2 申请/POC 报告的机验证据与代码实测输出不符（证据链完整性）

GUIDELINES §1.1："作者自述、单一 happy-path 示例、reviewer 投票均不能代替证据"。本轮申请 §三.4 与 `docs/POC_VERIFICATION_REPORT.md`（假设 5/Phase 2 行）粘贴的 e2e 报告，与评审人在 `906b17e` 代码上的实测输出存在**三处不符**：

| 报告字段 | 申请粘贴值 | 代码实测值 | 根因 |
|---|---|---|---|
| votes_yes / effective_votes | 3 / 3 | **0 / 0** | `e2e_runner.py:225-226` 读取 `breakdown.get("yes_approve")`/`get("effective_votes")`，而 `consensus/engine.py:43-47` 的 breakdown 键为 `approve/reject/abstain`——两键不存在恒返 0 |
| Physical Archive | "Archived files persisted" | **"Archived 0 files"** | `e2e_runner.py:249` 检查 `archive/<task_id>/r1`，fsm 实际归档键为 checkpoint_ref（实测 `archive/9454c49.../`）；且 0 文件时状态仍渲染 "PERSISTED" |
| Worktree Dispatch reviewers | ['codex','opencode','antigravity'] | **实际建给 ['cc-glm','kimi']** | `e2e_runner.py:186` 为硬编码展示列表；orchestrator.py:155 无适配器时回退 `["cc-glm","kimi"]` |

另申请 §二.4 第 5 步声明"**3 方在各自 Worktree 产出合法 .review.yml**"——代码事实：三份 `.review.yml` 由 runner 自身在主仓 `.macao/.reviews/` 直接生成（`e2e_runner.py:198-213`，硬编码 YES_APPROVE），worktree 创建后从未被任何评审方进入。方案文档 `CONTROLLED_E2E_INTEGRATION_PHASE2.md` §二 mermaid 图（Exec=Claude Code 编写代码、Rev=三方独立审查）与实现同样不符。

**处置**：粘贴报告无法由当前代码复现产出（数值/列表与代码输出矛盾），按证据规则不得作为 L3 定级依据；需以可复现命令+原始输出重新提交，并修正上述三处代码或声明。

## 三、P1：进入下一阶段前应修正

1. **P1-1 e2e 伪造 Executor 与 Reviewer 产物，L3"真实协同"核心主张不成立**：Executor 代码由 runner `write_text()` 直接产出（`e2e_runner.py:113-135`），`.dev.yml` 与三份 `.review.yml` 均为 runner 脚本伪造（`:148-168, 198-213`）。全流程**没有任何真实 CLI 参与任务执行**。Phase 1 的 `test-clis` 仅验证 `<cli> --version` 的 PTY 拉起与强杀（`integ_harness.py:62-72`），未验证任务注入、非交互执行与产物解析。因此"L3 INTEGRATED"所主张的真实集成证据为 **CLAIM_ONLY**；已达成的真实成绩是"编排管线级 E2E 自动化（含真实 git 合并）"。
2. **P1-2 MergeController"模拟环境"逃生舱**（`merge/controller.py:56-59`）：非 git 仓库时直接返回成功并将 `checkpoint_ref` 冒充 merge_commit → E4a DONE 在零校验下达成。这是为让单测通过而写入生产代码的假成功路径（测试污染生产逻辑）；应改为显式注入 merge 策略或在非 git 环境直接报错。
3. **P1-3 worktree 创建非 git 降级 fail-open**（`utils/git_utils.py:97-99`）：非 git 目录时静默 `mkdir` 空目录并当作"worktree"返回——与上轮 P0-2 修复承诺的 FAIL-CLOSED（`orchestrator.py:154-168`，仅对 git 命令失败生效）矛盾：对"根本不是 git 仓库"这一更严重情形反而放行，隔离语义完全丢失。
4. **P1-4 硬编码回退值实际生效并已产生错位**：`orchestrator.py:78`（"cc-ds4"）、`:155`（`["cc-glm","kimi"]`，Kimi 已被 opencode 替换却仍在回退名单）、`:219`（读 tasks 表不存在的 `executor_id` 列，恒回退）；`cli/main.py:93-94` 配置加载失败 `except: pass` 静默回退默认值。e2e 实测 worktree 建给 cc-glm/kimi 即其后果（见 P0-2 表）。
5. **P1-5 PTY harness 无平台检查，"34/34"为平台条件性结论**：`test_integ_harness` 仅对"CLI 未安装"接受 SKIPPED（`tests/test_integ_harness.py`），win32 有 CLI 但无 `pty` 时 3 项 FAIL。这是继"22/22""24/24"后第三次未注明平台限定的全绿声明。应在 harness 中探测 `pty` 可用性并 SKIPPED+标注，或声明仅支持 POSIX。
6. **P1-6 `get_changed_files` 伪造兜底**（`utils/git_utils.py:63, 78`）：git 命令失败或输出为空时返回 `[{"path": "src/main.py", "status": "modified"}]` 假数据——该列表经 `orchestrator.py:182` 流入权威 `review_context.code_changes.files_list`。伪造数据进入决策链的模式（上轮 P1-6）在 git 工具层复发。

## 四、P2：应修正

1. **P2-1 push 步骤未接线**：`orchestrator.execute_merge` 未传 `remote_name`（`orchestrator.py:347-352`），`merge/controller.py:93-96` 的 push 分支在接线路径永不执行；§14.5 第 5 步/E4a"push 完成"语义未达成（本地闭环成立，对外推送未验证）。
2. **P2-2 归档校验空转**：0 文件仍渲染 "PERSISTED"（`e2e_runner.py:249-253` + ui）；路径键错配见 P0-2。归档断言应为 `archived_files` 非空且含三类产物。
3. **P2-3 L3 判据缺口**：其一，GUIDELINES §2.1 定义的 L3 是 **SCENARIO-VERIFIED**（全同意/1:1 僵局/**超时**/弃权/崩溃恢复/返工循环全覆盖），"L3 INTEGRATED"并非阶梯中的等级，若要引入须按 GUIDELINES §11 修订方法论；其二，§13 五项超时至今零实现零测试（无事件循环/定时器，四方评审共同指出，未见行动）；其三，GUIDELINES §6 反例库多项仍未覆盖（消费端重复 message_id 幂等、同 reviewer 双份 .review.yml、`.dev.yml` 缺字段但 signal=EXPLICIT 等）。
4. **P2-4 POC_VERIFICATION_REPORT 与事实不符的"VERIFIED"**：假设 3 称"单进程主事件循环……VERIFIED"（系统无事件循环）；同报告"配置组装根注入……闭环"与 P0-1 矛盾。§9-B 模式（[x]/✅ 无证据）第三轮复发。
5. **P2-5 DTO 残留双定义**：`core/types.py:120-130` 新增 `AEPEnvelope` dataclass 与 `msg/envelope.py` 的同名类冲突（未见使用方）；`MessageType = AEPType` 别名保留（claude 评审建议删除，未采纳）。
6. **P2-6 E4a 精确匹配弱化**：`merge/controller.py:89` 的 `head.startswith(checkpoint_ref)` 前缀放行使"100% 精确等于"降级为前缀匹配（e2e 用全 SHA 时精确；短 SHA 场景应先 rev-parse 归一化再比较）。

## 五、P3：登记备查

1. e2e 的 `.dev.yml` 以分支名 `"main"` 作 `git.base_commit`（沿上轮旧病；schema 未约束该字段故通过）；
2. `cli/main.py:235` `task create` 将 `{"raw": acceptance, "tests_passed": True}` 伪造为验收标准；
3. `pyproject.toml` dev 依赖 `pytest`/`prompt_toolkit` 仍为零使用死依赖（claude 评审已指出，未处理）；
4. preflight 仍探测已移出矩阵的 kimi（结果诚实但矩阵口径未同步 `macao.yaml` allowed_clis 叙事）。

## 六、已对齐 / 已确认项（VERIFIED，给予肯定）

1. **编排管线 E2E 真实闭环**（win32 实测复现）：git init→commit→checkpoint→worktree 分发→共识→FF merge→HEAD==checkpoint SHA→DONE 全链路自动完成；`merge_exact_match` 校验真实有效。
2. **`message_deliveries` 独立投递表**（Arch-3）：DDL（`db.py:86-96`，UNIQUE(message_id,recipient)+FK）与 bus 实现（fan-out 拆分、按接收者 ACK、全部 ACK 后主消息置 ACKED、DLQ 联动）语义正确，彻底解决多播遮蔽问题——本轮工程质量最好的子项。
3. **CLI 只读化**（Arch-4）：status/doctor 严格只读，`task recover` 显式对齐（实测 doctor 无副作用）。
4. **DTO 收敛**（Arch-2）：`PreflightCheckResult`/`CapabilityManifest` 单点定义于 types；`OpinionStatus` 移除 ABSTAIN；`Decision` 四值 + DEADLOCK"仅中间态"注记。
5. **上轮修复全部保持**：deadlock HOLD 不写盘（`vote.py:176-178`）、E5/E7 轮次守卫、四选项终局落盘、reviewer 白名单去重、E2 归档扩展至 `.review.yml`（`fsm.py:76`）、vote_result 写盘前 Schema 校验、`kind` 统一 `review_manifest`。
6. **adapter/__init__ 注册表 + 适配器 preflight 诚实**（未装即 FAIL/SKIPPED，报告不粉饰）。

## 七、定级结论与建议闭环顺序

**结论**：L3 / PG-2 **不授予**。当前可辩护的等级仍是 **L2 SPEC-CODE-ALIGNED / PG-1**（维持），新增证据（管线 E2E + deliveries + PTY 冒烟）可作为未来 L3 的 SIM/TEST/OPS 部分输入，但 L3 核心主张"真实 CLI 端到端协同"无真实参与方，且申请证据链存在与实测不符的 P0 问题。PG-2 另要求"接口稳定"——本轮刚替换 Kimi→OpenCode/新增 agy，接口仍在变动。

**闭环顺序**：
1. 修 P0-1（配置键路径，附"每个配置键端到端到达"断言测试）与 P0-2（修正 e2e_runner 三处 + 以可复现原始输出重提证据）；
2. 修 P1-2/P1-3（删除模拟成功与 fail-open 降级）、P1-6（伪造兜底改抛错/空列表）；
3. Phase 2 升级为真实协同：至少一次人工监督下由真实 claude-code 产出 commit+`.dev.yml`、真实 codex/opencode/agy 在 worktree 内产出 `.review.yml` 的受控运行（哪怕 1 次成功记录 + 原始日志），届时 L3 主张才有事实基础；
4. 补超时体系（事件循环/定时器）与 §6 反例库测试后再议 L3 SCENARIO-VERIFIED；
5. 平台策略：harness/harness 测试加 `pty` 探测，声明 POSIX-only 或补 win32 支持；今后所有"N/N PASS"声明注明平台与依赖安装步骤。

## 八、Reviewer 自审记录

- 首轮参与该仓库多评审人排班中的"zcode"席位；无连续漏审史。
- GUIDELINES §9 五项自检：本报告全部 REJECT 附路径+行号；全部实测命令与输出可复现（win32，需 `pip install rich`，属 pyproject 声明依赖、非代码缺陷）；确定性用语无；无未标注的"已验证"表述——凡本机不可复现者（Linux 真实 CLI 4/4 PTY 报告）均标 CLAIM_ONLY 待核，不作为定级依据。
