# MACAO 整体技术框架评审结论（技术选型 / 代码组织 / 实现质量 / 其他）

- **评审日期**：2026-08-27
- **评审人**：zcode（独立评审，GLM）
- **评审性质**：架构级技术评审（非 L1~L4 定级轮；对 `[2026-08-27-review-request-Phase0-Phase1-Code.md]` 交付物的技术面横向评审，与同日三份 L2 定级报告互补）
- **评审对象**：commit `435eeea` 时点的 `src/macao/`（27 文件）+ `tests/`（9 套件）+ `pyproject.toml` + `docs/TECH_INTRUDUCE.md` 选型声明
- **证据方式**：全量通读源码与测试 + 本机实测（win32 / Python 3.11.9）；缺陷级发现的逐条证据见同日 `2026-08-27-review-result-435eeea-zcode.md`（P0 ×2 + P1 ×7 + P2 ×6 + P3 ×8），本报告只做**模式级归纳与结构性判断**，不重复逐条清单
- **整改核对**：评审完成于 `435eeea`；**附录一**逐项核对 commit `23dfad5`（P0/P1 全量整改提交）后的最新状态

---

## 总评

概念建模与文档治理超预期地强，工程化与"让系统真正跑起来"的部分是欠账。分层设计清晰、领域概念（FSM/共识/产物契约/适配器）扎实、评审流程严格；但在评审时点（`435eeea`），项目形态是**一套高质量的领域库 + 测试演示，还不是自驱动的编排系统**——核心的"事件循环"不存在、关键子系统（合并流水线）未接线、文档声明系统性领先于代码事实。`23dfad5` 整改后，缺陷级问题（2 P0 + 7 P1）已全部闭环且 win32 实测 24/24 PASS，但**结构性建议（驱动层、CI、依赖锁定、选型声明漂移）仍开放**。

---

## 一、技术选型评审

### 1.1 选得对的

| 选型 | 判断 |
|---|---|
| SQLite + WAL 单机状态存储 | 正确：MVP 零运维、单文件可审计、与 PRD §11.4/§11.6 一致 |
| **手写确定性 FSM 而非引入 LangGraph** | 实际上是**正确决定**：确定性状态机不需要 LLM 图编排框架；`TECH_INTRUDUCE.md:77` 已如实降级为"预留接口"——比盲目引入框架的判断力更好 |
| Click + Rich | 正确：与 §14 用户旅程的"增强型 CLI"定位匹配 |
| jsonschema + `docs/schemas` 单一契约源 | 好实践：产物校验与文档契约同源（`core/schema.py` 直读 docs/schemas） |
| AEP 信封 + SQLite 消息表 | 与 §11.6"agmsg 本地形态 = SQLite 消息表"一致 |

### 1.2 问题

1. **选型声明与实现脱节三处**（评审时点）：
   - PRD §11.3（`MACAO_PRD_v2.md:917` 等三处）仍写 LangGraph；
   - `prompt_toolkit` 列于 `pyproject.toml` dev extras 但代码零引用；
   - claude-code 声称 "PTY + Hook" 双通道（§12.3 claude-hook 类型），实现只有 PTY 写 prompt 一种。
   这类"选型幻影"会持续误导后续开发者与评审排期。
2. **PTY 无跨平台策略**：`pty_session.py` 模块级 `import pty`（评审时点），Windows 导入即崩；CapabilityManifest 声明 supported_os 仅 linux/darwin，但开发机是 Windows——错位不解决则每次开发都踩坑（评审时点实测：6 项测试 ERROR、CLI 全灭）。要么 ConPTY 分支，要么声明不支持 + 惰性导入。
3. **"单进程事件循环"只存在于纸面**：PRD §11.1 核心架构声明，代码无 asyncio、无调度线程、无任何 timer；§13 五项超时（development 2h / checkpoint 1m / per_reviewer 10m 等）零实现。这不是选错了，是选型后没有落子——需要先决定 asyncio 还是轮询线程。
4. **依赖无锁定**：`pyproject.toml` 只有 `>=` 下界，无 lock 文件，上游大版本升级会无声进入环境。

## 二、代码组织结构评审

### 2.1 好的方面

- src layout 标准；领域分包（core/storage/msg/adapter/consensus/workflow/merge/utils/cli）与 PRD 概念一一对应，定位成本低；
- Adapter ABC + CapabilityManifest 是兑现"可插拔"承诺的正确形状（`adapter/base.py`）；
- Schema 校验绑定单一契约源（`core/schema.py`）。

### 2.2 结构性问题（评审时点）

1. **缺"驱动者"层——最大的洞**：`Orchestrator` 是一组需要外部按正确顺序手动调用的方法（`start_task → check_development_checkpoint → dispatch_review_requests → collect_and_evaluate_consensus`），只有测试在驱动；没有 `run()`、没有事件循环、没有定时器，CLI 只有手动子命令，**没有任何东西推进 FSM**。PRD 把 Orchestrator 定义为系统心脏，代码里它只是一个 API 集合。
2. **双实现分歧**：`cli/main.py` override resolve 与 `Orchestrator.resolve_override` 两套 E7 实现、行为不一致（同日 L2 报告 P1-3 的结构根源）；状态推进散落于 `fsm.step` / orchestrator 各方法 / `reconcile` 三处，各走各的校验。
3. **`merge/` 整包死代码**：包结构存在、全仓零引用——"占位包"制造已实现的错觉。
4. **分层渗漏**：`consensus/vote.py` 共识层直接写磁盘；`fsm.py` 工作流层直接 `shutil` 归档；最典型的反模式是 **`status`/`doctor` 只读命令每次触发 reconcile 状态变更**（`cli/main.py:118,146`）——读命令带副作用，正是 P0-1 能被静默放大的结构原因。
5. **全局单例 DB + 零配置注入**：`db.get_db` 全局单例；`ConfigManager` 与 Orchestrator 未接线，`configured_reviewers=2`、`"cc-ds4"` 等默认值硬编码在函数签名。
6. **无共享测试基建**：9 个测试文件各自 tempfile setUp，场景构造无法复用。

## 三、代码实现质量评审（模式级根因）

缺陷级逐条清单见 `2026-08-27-review-result-435eeea-zcode.md`，此处只归纳**四类模式级根因**：

1. **静默吞异常成风**：`except Exception: pass` 遍布 state_engine（3 处）、orchestrator worktree 创建、schema 加载、pty terminate；全项目零 `logging` 使用——观察性为零，出问题只能靠猜。
2. **双写协议未实现**：PRD §11.5"fsync → SQLite 事务 → git 提交"三段顺序一处都没做（无 fsync、`stage_and_commit` 零调用）；状态转移与产物登记是分离的独立 commit，中途崩溃即不一致，而补偿方 reconcile 自身还有误映射缺陷（同日报告 P2-1）。
3. **伪造数据当真实数据流**：context_builder 占位默认值（files_list 恒为 `src/main.py`）、usage 命令硬编码 token 数、vote.py 伪造 message_id——同一模式的四张面孔。根因是"先做接口形状"阶段没有定义显式的 NOT_AVAILABLE 语义，占位数据直接流进决策链。
4. **枚举与 Schema 漂移 + 测试是"顺序演示"**：`Decision` 缺 RETRY_REVIEW/CANCELLED、`OpinionStatus` 多 ABSTAIN——"单一事实源"只做到了 Schema 层没做到代码层；测试按实现的调用顺序写断言，无非法转移/轮次上限/重复消息等反例（恰是全部 P0/P1 漏网处），`test_context_builder` 甚至把 `base_commit=="main"` 的错误语义固化进断言。

## 四、其他方面

1. **无 CI 是最不成比例的缺口**：评审治理严格到"机验 18 项、全量对账"的项目没有 `.github/workflows`——"全绿"声明无任何自动门禁背书。建议第一优先补 linux+windows 矩阵（评审时点的 6 ERROR 当场会被拦住）。
2. **文档-代码治理落差是本项目独特的风险**：治理强度两侧不对称——文档侧有四级定级、机验、对账规则，代码侧"✅ 对齐/已完成"却无自动核验（追溯矩阵 10 行 5 行失实、PLAN/ROADMAP 存在无证据 ✅、《PoC 三假设验证技术报告》当时不存在）。建议把追溯矩阵变成可执行断言：每行引用测试函数名，CI 校验引用有效性。
3. **单任务串行无强制**：§14.2 声明 MVP 单活动任务，代码无锁无检查，`get_active_task` 只是取最新一条。
4. 小项：schemas `$id` v2.3 vs PRD v2.3.1；无 lint/format 配置（PRD §5.3 自己提到了 pylint/bandit）。

## 五、修复优先级建议

1. **补驱动层**（事件循环 + 超时调度），让 CLI 成为它的薄壳——这是所有缺陷级修复的承重结构，也是 PRD 架构承诺的核心；
2. 修复缺陷级 P0/P1（顺序见同日 L2 报告；→ **已由 `23dfad5` 完成**，见附录一）；
3. 补双平台 CI + 枚举/Schema 一致性测试 + 依赖 lock；
4. 收敛 override 双实现、merge 接线或移除、`status` 去副作用（→ 前两项已由 `23dfad5` 完成）；
5. 消灭 `except: pass`，引入 logging。

---

## 附录一：整改状态核对（@ `23dfad5`，评审人本机验证）

commit `23dfad5`（"完成 PRD v2.3.1 与 Phase 0/1 专家复审发现的全部 P0/P1 整改，新增回归测试"）逐项核对：

### 已闭环（VERIFIED，附新代码行号）

| 本报告/同日报告发现 | 整改后状态与证据（`23dfad5`） |
|---|---|
| P0-1 Deadlock 伪写落盘 | **已修**：`consensus/vote.py:79,176-177` DEADLOCK 分支明确不写盘 |
| P0-2 worktree 未注入 + 静默回退 | **已修**：`workflow/orchestrator.py:149-170` FAIL-CLOSED（创建失败阻断分发并告警）+ `workspace_path=str(worktree_path)` 注入权威 context |
| P1-1 转移表未接线 | **已修**：`workflow/fsm.py:32` `TransitionTable.can_transition` 接入 `transition()` |
| P1-2 E5 无轮次守卫 | **已修**：`state_engine.py:26,105` + `orchestrator.py:215,256` |
| P1-3 Decision 枚举缺值 / override 双实现 | **已修**：`core/types.py:50-56` 四值（DEADLOCK 注明"仅中间态、永不落盘"）；`cli/main.py:176` 改为委托 `orchestrator.resolve_override` 单实现 |
| P1-4 MergeController 死代码 | **已修**：`orchestrator.py:19,40` 完成接线 |
| P1-5 artifacts 覆盖语义 | **已修**：`storage/db.py:26-28` `artifact_id AUTOINCREMENT` + 五元组 UNIQUE；`store.py:84-98` 按 artifact_id 追加/更新，无 `INSERT OR REPLACE` |
| P1-6 context 伪造数据 | **已修**：`context_builder.py:48-57` 新增 `populate_from_dev_manifest`；`orchestrator.py:166-178` 喂入真实 dev 数据与 diff 统计 |
| P1-7 SQLite 连接泄漏 + 平台崩溃 | **已修**：`db.py:96-110` `@contextmanager` 保证 close；`pty_session.py` pty 改守卫导入；**评审人 win32 实测 `unittest discover` 24/24 OK** |
| 结构 2.2-④（部分）logging 缺失 | **部分改善**：`orchestrator.py:6` 已引入 logging |

### 仍开放（建议纳入后续计划）

| 结构性发现 | 状态（@ `23dfad5`） |
|---|---|
| 驱动层/事件循环缺失（本报告 §2.2-①、§一.2.3） | **开放**：orchestrator/cli 中仍无 `run()`/asyncio/scheduler/timer；§13 超时体系仍未落地 |
| 无 CI（§四.1） | **开放**：`.github/` 仍不存在 |
| 依赖无锁定（§一.2.4） | **开放**：无 lock 文件 |
| PRD LangGraph 措辞漂移（§一.2.1） | **开放**：`MACAO_PRD_v2.md:917,947,1186` 仍写 LangGraph；prompt_toolkit 仍在 dev extras 且零引用 |
| `status`/`doctor` 读命令触发 reconcile 副作用（§2.2-④） | **开放**（严重度降低：P0-1 已修，副作用不再能劫持裁定，但仍是架构异味）：`cli/main.py:105-106,143` |
| 单任务串行无强制（§四.3） | 未见变化 |
| 共享测试基建缺失（§2.2-⑥） | 未见变化 |

## 附录二：Reviewer 自审记录

- 本报告为架构级横向评审，不构成 L1~L4/PG-x 定级；定级结论以同日三份 L2 定级报告与后续复核为准。
- 评审基于 `435eeea` 快照完成，附录一基于 `23dfad5` 快照复核；两快照差异（39 文件）中与本报告相关的部分已逐项核对，行号证据以对应快照为准。
- GUIDELINES §9 自检：无确定性用语未标注；全部判断附文件路径+行号或实测命令；本报告不改变 STATUS 中任何定级状态，仅作为技术债登记与后续行动依据。
