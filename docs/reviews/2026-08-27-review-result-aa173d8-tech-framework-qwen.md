# MACAO 整体技术框架评审（技术选型 / 代码组织 / 代码质量 / 其他）

- **评审日期**：2026-08-27
- **评审人**：qwen（独立评审）
- **被评审 commit**：`aa173d8`（记录时 `main` HEAD；代码状态与 `23dfad5` 一致，`c3dd887`/`aa173d8` 均为纯文档归档提交）
- **评审性质**：架构级技术评审（非 L1~L4 定级轮），响应用户四问：技术选型 / 代码组织结构 / 代码实现质量 / 其他
- **评审范围**：`src/macao/`（27 文件，约 4000 行）+ `tests/`（9 套件）+ `pyproject.toml` + `macao.yaml` + `docs/schemas/macao_config.schema.json` + `docs/TECH_INTRUDUCE.md`
- **证据方式**：全量通读源码；关键调用链以 AST/静态比对独立复现（不采信任何既有报告的结论，含 `23dfad5` 提交说明中的"全部 P0/P1 整改"声明）

---

## 总评

**框架方向正确、主干扎实，但"真实 CLI 接入层"是带必现运行时错误的空壳；测试恰好绕开了全部缺陷区。**
FSM/共识/存储/合并主干与 PRD v2.3.1 高度一致（Deadlock 不落盘、worktree fail-closed、E4a 哈希硬校验均已正确实现）；但 Adapter/CLI/Config 三条"测试未覆盖的链"经独立静态复验**全部断裂**，且与 `23dfad5` 提交声明不符——该提交整改的是 zcode 一轮的缺陷清单，本报告与同日 claude/codex 框架评审所发现的 Adapter/配置系缺陷在 `aa173d8` 时点**仍然全部存在**（逐条复验见下）。

---

## 一、技术选型

### 1.1 合理之处（可保留）

| 选型 | 评价 |
|------|------|
| Python 3.10+ / SQLite(WAL) / jsonschema draft-07 / Click+Rich | 对单机 PoC 是恰当的最小栈，无过度设计 |
| 手写白名单 FSM（`workflow/transitions.py`） | 优于 PRD §11.3 原写的 LangGraph：转移表可枚举、可测试、零外部依赖，与"每步最多命中一个合法转移"验收标准天然契合 |
| 运行时直接复用 `docs/schemas/`（`core/schema.py:11-19`） | 文档契约即运行时契约，单一事实源，设计亮点 |
| MockAdapter 测试缝（`adapter/mock.py`） | 24 用例无需真实 CLI，PoC 阶段正确策略 |

### 1.2 问题

| # | 级别 | 问题 | 证据 |
|---|------|------|------|
| T1 | P2 | **文档-实现背离**：PRD §11.3 写 LangGraph + agmsg；实现为手写 FSM + SQLite `message_queue` 表，`pyproject.toml` 无 langgraph/agmsg 依赖；`msg/bus.py:1` 自称 "agmsg SQLite 实现" | 需回填 PRD §11.3 与 TECH_INTRODUCE 的技术栈表述（zcode 附录亦登记此项） |
| T2 | P1 | **打包后 Schema 必失联**：`get_schemas_dir()` 靠向上遍历目录树找 `docs/schemas/`，pip 安装后必然找不到（schemas 不在包内），届时所有校验返回 "not found"，全部产物判无效 | `core/schema.py:11-19`；应改 `importlib.resources` / package data |

## 二、代码组织结构

分层（core/adapter/workflow/consensus/merge/msg/storage/utils/cli）与 PRD 章节一一对应，依赖方向无环，模块粒度适中（最大 396 行）。三处结构性瑕疵：

| # | 级别 | 问题 | 证据 |
|---|------|------|------|
| S1 | P2 | **类型重复定义**：`CapabilityManifest` 两份且字段不同；`AEPEnvelope` 同样双份（dataclass vs 工厂类），实际只用其一，漂移隐患 | `core/types.py:93` vs `adapter/base.py:10`；`core/types.py:80` vs `msg/envelope.py:11` |
| S2 | P2 | **双路径状态识别**：`state_engine.py` Layer 1b/1c 只被 `check_development_checkpoint` 用到（仅 1a）；quorum/投票在 `orchestrator.py:222-240` 另走 `VoteAggregator` 一套——同一语义两处实现，未来必然分叉 | 见左 |
| S3 | P1 | **CLI 未接线 Adapter**：`task create` 创建 Orchestrator 不注入任何 adapter，也无 `run/poll` 类驱动命令；从 CLI 无法触达真实评审循环 | `cli/main.py:127` |

## 三、代码实现质量

### 3.1 做得好的（与 PRD v2.3.1 严格对齐，独立复核确认）

- Deadlock 不落盘 `vote_result.json`（`orchestrator.py:300-328`、`vote.py:176-178`）——§3.3 E3 新规实现正确
- worktree 创建 fail-closed（`orchestrator.py:149-163`）——P0-2 安全红线落地
- E4a 硬校验 `head == checkpoint_ref`（`merge/controller.py:87-90`）——P0-1 落地
- max_rework_rounds 守卫（`orchestrator.py:279-298`）、转移白名单拒绝即审计（`fsm.py:32-41`）、DB 事务上下文管理器、追加式归档语义（`store.py:74-108`）

### 3.2 缺陷清单（全部经 `aa173d8` 静态复验仍然成立）

| # | 级别 | 缺陷 | 证据（复验于 aa173d8） |
|---|------|------|------|
| C1 | **P0** | 三个真实适配器 `preflight()` 必然 **TypeError**：`PreflightCheckResult` 字段为 `agent_id/installed/version/execution_mode/error`，构造却传 `cli_name=/details=/remediation=/auth_valid=/in_matrix=` | `core/types.py:122-133` vs `claude.py:33-56`、`codex.py:30-46`、`kimi.py:29-45`（与 23dfad5-codex L32、23dfad5-claude §3.1 独立同判） |
| C2 | **P0** | 适配器调用 `session.write_input()`/`get_clean_logs()`——PTYSession 只有 `send_input()` 与 `.logs` → `inject_task`/`get_logs` 必然 **AttributeError** | `pty_session.py:100` vs `claude.py:77,86`、`codex.py:67,76`、`kimi.py:65,74`（与 23dfad5-codex L33 独立同判） |
| C3 | **P0** | `macao init` 模板（`agents/consensus/orchestration` 段）无法通过 `macao_config.schema.json`（required `project+team`）；且默认 `require_human_signoff: false` 违背 PRD 保守默认 | `cli/main.py:50-82` vs `docs/schemas/macao_config.schema.json:6`（与 23dfad5-claude 配置系结论独立同判） |
| C4 | **P1** | `cli preflight` 为硬编码假数据，从不调用适配器 preflight（调了也撞 C1）——违反 PRD §14.1 第 1 步 | `cli/main.py:29-35` |
| C5 | **P1** | ConfigManager 属性读取路径全错：读 `policy.rework_policy.*`/`policy.merge_policy.*`/`policy.rebase_policy.*`，Schema 实为扁平 `policy.max_rework_rounds`、`merge.require_human_signoff` → 永远返回默认值；且 Orchestrator 从不使用 ConfigManager | `core/config.py:67-88`（复验：70/81/87 行仍为嵌套读取） |
| C6 | **P1** | 未知 `human_resolution` 值**静默落为 APPROVED**（typo = 批准合并），应 fail-fast 抛异常 | `consensus/vote.py:138-139`（复验：139 行仍为 `decision = Decision.APPROVED`） |
| C7 | P2 | `get_changed_files()` git 失败时编造 `[{"path":"src/main.py"}]` 注入 review_context | `utils/git_utils.py:63,78` |
| C8 | P2 | Orchestrator 默认 `require_signoff: False` 且键名与 PRD/CLI 的 `require_human_signoff` 不一致 | `orchestrator.py:44-49` |
| C9 | P2 | 无超时/截止时间执行器（PRD §6.1 的 10m/30m 时限与 HOLD 升级告警无实现载体）；`pyproject.toml:9` 声明 `readme = "README.md"` 但根目录无此文件（安装会失败） | 复验：README.md 仍不存在 |

### 3.3 测试质量

9 个测试文件覆盖 FSM/共识/Schema/Store/Reconcile/消息总线/编排仿真，质量尚可；**但恰好绕开全部缺陷区**——真实适配器（C1/C2）、CLI（C3/C4）、ConfigManager（C5）、MergeController 零测试（复验：`tests/` 仍为原 9 文件，`23dfad5` 未新增适配层测试）。"24/24 PASS" 只证明 mock 路径成立，不能作为适配层可用性的证据。

## 四、其他

1. **文档卫生**：`TECH_INTRUDUCE.md` 文件名拼写错误（应 INTRODUCE），正文自称 TECH_INTRODUCE；PRD §11.3 技术选型表待回填实际栈（见 T1）
2. **安全**：`claude.py:59` 以 `--dangerously-skip-permissions` 启动 Executor——PRD §12.2 承诺的"任务工作区路径白名单 + 命令审计"在代码中只有 cwd 隔离，无白名单机制，登记为已知缺口
3. **仓库卫生**：本地 `build/`、`__pycache__/`、`.macao/state.db` 均已被 .gitignore 覆盖（复验未被跟踪），保持即可

## 五、与既有评审的交叉印证（全量对账声明）

本报告出具前已核对 `reviews/` 目录同日全部技术框架评审，避免重复登记、确认独立印证关系：

| 既有报告 | 关系 |
|----------|------|
| `2026-08-27-review-result-23dfad5-codex-framework.md` | C1/C2 与其 L32/L33 **独立同判**（本报告先静态复现，后知其已登记）；其总评"仅适合作纯 Mock 概念验证"与本报告总评一致 |
| `2026-08-27-review-result-23dfad5-tech-framework-claude.md` | C1/C3/C5 与其 §3.1 及配置系结论**独立同判**；其"测试覆盖的路径干净、未覆盖的路径几乎全坏"模式归纳与本报告 §3.3 一致 |
| `2026-08-27-review-result-435eeea-tech-framework-zcode.md`（含 23dfad5 整改核对附录） | 其"缺陷级 P0/P1 全部 VERIFIED"仅覆盖 zcode 自身清单；**本报告证实**：23dfad5 之后（含当前 HEAD）C1~C7 仍全部存在——`23dfad5` 提交说明"全部 P0/P1 整改"的表述范围失实，应以 reviews/ 全量对账为准（P1-3 治理规则的又一次实证） |

## 六、建议修复顺序

1. **C1→C2**：统一 `PreflightCheckResult` 字段（或恢复适配器旧字段名）+ PTYSession 补 `write_input`/`get_clean_logs`（或适配器改调 `send_input`/`.logs`）——两处都是分钟级修复，但阻断全部真实接入
2. **C3**：`init` 模板对齐 `macao_config.schema.json`（`project+team+policy+merge`），`require_human_signoff` 默认改 `true`
3. **C5**：ConfigManager 读取路径改扁平键，并接线进 Orchestrator（取代手写默认 dict，顺带关闭 C8）
4. **C6**：未知 resolution fail-fast
5. **补测试**：真实适配器冒烟测试（构造即测，不需真实 CLI：`preflight()` 返回、`inject_task` 走 PTYSession stub）+ CLI `init/doctor` 往返测试 + ConfigManager 往返测试
6. **T2**：schemas 打包方案（`importlib.resources`），否则一切"安装后运行"都是空谈
7. 文档回填：PRD §11.3、TECH_INTRODUCE（并改文件名）、根目录补 README.md

---

## Reviewer 自审记录

- 方法：全量通读 27 个源文件与 9 个测试文件；C1~C7 均用 AST 字段比对/方法存在性检查独立复现，非仅凭阅读推断；未运行真实 CLI（环境无厂商二进制），运行时结论以"必现的构造/调用不匹配"为证据级别
- 连续漏审登记：本轮未发现自身前序轮次（首次参评）；登记一条**流程观察**——`23dfad5` 提交声明与 `reviews/` 实际对账结果不符（见 §五），再次验证 STATUS 全量对账规则的必要性
- 未覆盖项：真实厂商 CLI 行为、网络/凭据路径、性能；结论仅覆盖静态代码一致性与契约层