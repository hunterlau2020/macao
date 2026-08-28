# MACAO 第一/二阶段受控联调与架构装配 独立评审结论（L3 INTEGRATED / PG-2 定级轮）

- **评审日期**：2026-08-28
- **评审人**：qwen（独立评审）
- **被评审范围**：`aa173d8` .. `906b17e`（申请文件 `2026-08-28-review-request-Phase1-Phase2-Integration.md`）
- **评审性质**：**L3 INTEGRATED / PG-2 定级轮**（非横向评估）
- **评审方法**：全部证据独立复放，不采信申请方粘贴的输出——`unittest discover` 全量重跑、`macao test-clis`/`macao e2e-run` 实机重放、配置注入链脚本复现、归档树物理核对
- **结论**：**未达 L3 INTEGRATED / PG-2，维持 PENDING_REVIEW。** Phase 1（4 款真实 CLI PTY 生命周期）与 Phase 2（微任务端到端闭环）的核心能力**真实成立且可独立复现**（这是本轮最重要的事实）；但存在 **1 个 P1**——`macao.yaml` 的 `require_human_signoff: true` 因配置形状失配被静默反转为 `False`，签字门禁在真实装配链路上失效——以及 1 组证据呈现缺陷。闭环面极小（1 处消费层修复 + 自检路径勘误），修后可直复审宣告 L3。

---

## 一、独立复放结果（申请声明逐条核验）

| 申请声明 | 独立复放结果 | 判定 |
|----------|--------------|------|
| 34/34 自动化测试全绿 | `PYTHONPATH=src python3 -m unittest discover tests -v` → **Ran 34 tests — OK**（6.87s） | ✅ 属实 |
| Phase 1：4 款真实 CLI PTY 拉起/ANSI 清洗/killpg 强杀/0 孤儿 | 本机实放 `test-clis --cli all`：claude 2.1.247 / codex 2.1.0 / opencode 1.18.23 / agy 1.1.22 **4/4 PASS**，0 zombie | ✅ 属实 |
| Phase 2：CODING→…→DONE 全链路、FF 合并 HEAD==checkpoint 100% 匹配 | 本机实放 `e2e-run`：全 7 步通过，`Target HEAD == checkpoint_ref` **100% MATCH**，终态 DONE | ✅ 属实 |
| 产物非覆盖追加归档 | 物理核对沙箱归档树：`archive/<checkpoint_ref>/r1/` 下 5 件产物（.dev.yml + 3×.review.yml + vote_result.json）齐全 | ✅ 属实（但 Runner 自检路径错误，见 F2） |
| `git diff --check` 0 errors clean | `git diff --check aa173d8..906b17e` 发现 **5 处尾随空白**（两份联调方案文档 + POC 报告） | ⚠️ 不准确（P3） |
| 机验输出（votes_yes=3、Archived files persisted 等） | 复放输出为 **votes_yes=0 / effective_votes=0 / Archived 0 files**——与申请粘贴不符 | ⚠️ 证据呈现缺陷（F2） |

## 二、上轮（aa173d8 框架评审）缺陷闭环核验

| 上轮编号 | 修复声明 | 独立复验 | 状态 |
|----------|---------|---------|------|
| C1 PreflightCheckResult TypeError | Arch-2 DTO 收敛 | 字段已扩为 10 项兼容构造；`test_adapter_preflight_probes_no_type_error` PASS | ✅ 关闭 |
| C2 PTYSession write_input/get_clean_logs 缺失 | Arch-2 | 两方法已补齐（AST 复核）；Phase 1 实机链路在用 | ✅ 关闭 |
| C3 init 模板不过 Schema | Arch-1 | `DEFAULT_CONFIG_TEMPLATE` 过 `macao_config.schema.json` VALID；signoff=true / rebase=false 安全默认 | ✅ 关闭 |
| C4 preflight 硬编码假探针 | Arch-4 | 已改真实探针（git/SQLite/各 CLI which+version） | ✅ 关闭 |
| C5 ConfigManager 读取路径全错 | Arch-1 | 属性实测：max_rework=3 / signoff=True / min_votes=2 / rebase 禁用=True | ✅ 关闭（但消费链断裂，见 F1） |
| C6 未知 human_resolution 静默 APPROVED | 未声明 | `vote.py:139` 仍为 `else: decision = Decision.APPROVED` | ❌ 未修（F3） |
| C7 git_utils 编造 src/main.py 兜底 | 未声明 | `git_utils.py:63,78` 仍在 | ❌ 未修（F4） |
| S1 类型双份 | Arch-2 | `CapabilityManifest` 已收敛为单份；`AEPEnvelope` 仍双份（types.py dataclass + envelope.py 工厂） | ⚠️ 部分（P3） |
| T2 Schema 打包（get_schemas_dir 向上遍历） | 未声明 | 安装后仍会失联 | ❌ 未修（登记，不阻塞 L3） |

## 三、本轮新发现

| # | 级别 | 发现 | 证据（可复现） |
|---|------|------|---------------|
| **F1** | **P1** | **签字门禁静默失效**：`get_orchestrator()`（`cli/main.py:86-99`）与 `ControlledE2ERunner` 注入的是 **Schema 形**配置字典（`{project, team, policy, merge, …}`），而 `Orchestrator` 读**扁平键**（`config.get("require_signoff")`，`orchestrator.py:345`）。复现：以仓库 `macao.yaml`（`merge.require_human_signoff: true`）走真实装配链，Orchestrator 实际读到 `require_signoff=False`——PRD §14.5 的保守安全默认在真实链路上被反转，merge 可无签字直通。`test_orchestrator_config_injection` 用扁平字典注入，恰好掩盖了该形状失配。Arch-1 声明"彻底消除硬编码默认值"失实 | 复现脚本输出：`macao.yaml=True → ConfigManager=True → Orchestrator 读到 False` |
| **F2** | P2 | **E2E 自检与报表两处失真**：① 归档自检读 `.macao/archive/<task_id>/r1`（`e2e_runner.py:249`），FSM 实际归档到 `archive/<checkpoint_ref>/r<round>`（`fsm.py:85`）→ 恒报 "Archived 0 files"；② 报表读 `breakdown.get("yes_approve")/get("effective_votes")`（`e2e_runner.py:225-226`），而 `ConsensusEngine` 的 breakdown 键是 `approve/reject/abstain` → 恒报 0。归档与共识本身正确（已物理核对），但自证指标全坏，申请粘贴的输出与 906b17e 代码不可同时成立 | 独立复放输出 votes_yes=0/Archived 0 files；归档树实物在 `<ref>/r1/` |
| **F3** | P2 | 上轮 C6 未修：未知 `human_resolution` 静默落 APPROVED（typo=批准合并），应 fail-fast | `consensus/vote.py:138-139` |
| **F4** | P2 | 上轮 C7 未修：`get_changed_files()` git 失败时编造 `[{"path":"src/main.py"}]` 注入 review_context | `utils/git_utils.py:63,78` |
| **F5** | P2 | **Phase 2 表述与证据边界**：申请称"3 方在各自 Worktree 产出 `.review.yml`"，实际是 Runner 直接写入共享 `.macao/.reviews/`（`e2e_runner.py:195-213`）——Reviewer 并未在 worktree 中真实运行（受控仿真）。Worktree 已按 fail-closed 创建（已验证），但评审产出环节是模拟的。此外沙箱配置显式 `require_human_signoff: false`（自动化有意为之，应显式声明），导致 **signoff→拒绝→E4b 路径至今无任何测试执行过**（与 F1 叠加：签字分支是全测试盲区） | 代码 + `rg signoff tests/` 无 require_signoff=True 用例 |
| **F6** | P3 | 申请声称 `git diff --check` clean，范围内实有 5 处尾随空白（两份联调方案 + POC 报告，均为新增行） | `git diff --check aa173d8..906b17e` |

## 四、定级判定与闭环顺序

**判定：PENDING_REVIEW，暂不授予 L3 / PG-2。**

理由：L3 的两项核心能力（真实 CLI PTY 生命周期、端到端协同流转）经独立复放**确认成立**，这是实质性的里程碑；但 F1 属安全默认反转——本仓库的门禁纪律（worktree fail-closed、rebase 豁免废除、签字保守默认）一贯以"安全边界不得静默削弱"为红线，一条 P1 即阻断定级（Guidelines：P0/P1 闭环后方可授级）。

**闭环顺序（改动面极小，可一批提交后直复审）**：

1. **F1（必改）**：Orchestrator 改为消费 `ConfigManager` 属性（或在组装根做一次 Schema 形→运行形的显式 flatten），并补**形状失配回归测试**——以真实 `macao.yaml` 走 `get_orchestrator()`，断言 `require_human_signoff=True` 到达 `execute_merge`；
2. **F2（必改）**：归档自检路径改 `<checkpoint_ref>/r<round>`；报表改读 `approve`/（approve+reject）；
3. **F5（必改）**：补 `require_signoff=True → 无签字拒绝 → E4b` 的测试；Phase 2 文档将"受控仿真产出"与"真实 CLI 产出"的边界写明；
4. **F3/F4（建议同批）**：fail-fast 抛异常；删除编造兜底（改返回空列表 + 告警）；
5. **F6**：清理 5 处尾随空白；
6. 复审宣告 **L3 INTEGRATED / PG-2**。

## 五、全量对账声明

按 P1-3 治理规则，本轮评审前已与 `reviews/` 目录全量对账：历史评审报告共 **28 份**（含本报告前的 27 份）+ 4 份申请，STATUS 对账表已覆盖。本报告为 Phase1/Phase2 申请的第 1 份专家报告（zcode / claude / codex 待出）。本轮未发现 STATUS 登记与目录不符之处。

---

## Reviewer 自审记录

- **方法**：所有"属实"判定均来自独立复放（测试重跑、两条实机命令重放、配置链脚本复现、归档树物理核对），未直接采信申请第三节粘贴的任何输出；恰恰是复放发现了申请输出与代码行为的两处不符（F2、F6）
- **连续漏审登记**：本人上轮（aa173d8）报告的 C1~C5 本轮全部复核闭环属实；C6/C7 上轮已登记、本轮确认未修，无漏审；新发现 F1 属装配链形状失配，上轮因 Orchestrator 尚未接配置注入而无法提前发现，登记为模式教训：**"注入存在"与"注入被消费"是两件事，复审必须追踪到消费点**
- **未覆盖项**：真实 CLI 的实际评审产出质量（Phase 2 为受控仿真，真实 LLM 评审召回率属 §15.5 评测范畴）；跨机场景（v1.1）；结论覆盖代码静态一致性、受控实机行为与测试证据层