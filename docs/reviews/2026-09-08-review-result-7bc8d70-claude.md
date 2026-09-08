# MACAO 综合编排闭环与评审方法论 v1.1（`7bc8d70` / Round 3）独立复审结论

- **评审日期**：2026-09-08
- **评审人**：claude（独立评审；不采信申请自述、不采信 `STATUS.md` 定级句、不采信处置单「ALL CLOSED」、不采信其他专家票——本报告 §一~§四写完后才通读 grok/codex/qwen 三份既有报告用于交叉核对，见 §六）
- **评审对象**：[`docs/reviews/2026-09-08-review-request-7bc8d70.md`](2026-09-08-review-request-7bc8d70.md)
- **受审提交**：`7bc8d7091ba4e39c0b3282492c613817f8d664e9`（`961bcfe..7bc8d70`，含 `48eea58` + `7bc8d70` 两个提交）
- **工作区 HEAD**：`a705a49`，相对 `7bc8d70` 仅追加申请文件与 `STATUS.md`（`git diff --stat` 已核）；`src/`/`tests/` 与 `7bc8d70` 逐字节一致
- **对齐基准**：`docs/MACAO_REVIEW_GUIDELINES.md` v1.1 §2–§3、§7.2、§8、§9；`docs/usercases/UC3-dev-checkpoint.md`；`docs/usercases/UC11-scenarioc-inflight-adoption.md`
- **前序基线**：`961bcfe`（四方评审 codex REJECT / grok NO_APPROVE / kimi REWORK / pi-qwen NO_APPROVE，全票否决待返工）
- **目标定级**：L3 SCENARIO-VERIFIED / PG-2 全量认证，并提请 L4 RELEASE-READY / PG-3
- **机器票**：**`NO_APPROVE`**
- **证据**：`BLOCKING` × 2（P1）；L4 OPS 缺口维持；`ADVISORY` × 若干；**无 P0**

**结论：不授予本轮 L3 SCENARIO-VERIFIED / PG-2 全量认证；不授予 L4 RELEASE-READY / PG-3。既有编排引擎 L3/PG-2（`4e38ed6` 轮）维持不变。**

`48eea58` 是一轮扎实的返工：`961bcfe` 轮四方指出的未知 CLI 借壳、SQLite WAL 侧车、Claude 会话跨仓串话、场景 C 操作面缺失、单活动任务未下沉、进程退出码 fail-open 等问题，我逐条独立复放，**全部确认已闭环**（见 §三）。但申请把 Codex 原 P1-04（检查点防伪）写成「彻底闭环」——我用隔离沙箱复现，**四种输入（全零哈希、缺失正文文件、空哈希、`executor.cli` 错配）仍可使任务从 `CODING` 推进到 `READY_FOR_REVIEW`**；另外我独立构造了一份指向不存在 commit（`deadbeef`）的伪造评审申请单，`macao task adopt --no-review` 在完全不校验该 commit 是否存在的情况下成功创建任务并写入 `WAITING_REVIEW`——这直接违反申请所依据的 `UC11-scenarioc-inflight-adoption.md` §5 异常流 E1「原子拒绝接管」的验收标准。两项均可在干净临时仓库中稳定复现，均由生产 CLI/编排器入口触达，非边角死码。

---

## 0. Reviewer 自审

### 0.1 强制自检

| # | 项 | 本轮 |
|---|---|---|
| 1 | 字段/路径 vs 实际读取 | `orchestrator.py:297` 的比对条件是 `doc_path.exists() and doc_path.is_file() and doc_sha and doc_sha != "0"*64`——四个条件任一为假即整段跳过，不是"先校验后放行"；`:304-307` 只读 `exec_info["id"]`，从未读取 `exec_info.get("cli")` |
| 2 | 「已完成 / 100% / 全绿」 | 162/162、`git show --check` rc=0、Schema 8/8 一致、P0-1/WAL/Claude 串话/场景C操作面/单活动任务五项 **VERIFIED**；「Codex P1-04 彻底闭环」「task adopt 完整实现 UC-11」**CONTRADICTED** |
| 3 | 确定性用语未标目标 | 「严格校验必须吻合」「杜绝假造与冒名」均陈述为既成事实，反例可直接击穿 |
| 4 | YAML/JSON Schema | 8 份契约逐字节一致 **VERIFIED**（历史项，本轮未回退）；`dev_manifest.schema.json` 对 `full_document.sha256` 仍只是 `type: string`，不拒绝全零/空串格式 |
| 5 | P1 均附路径与复放 | 是，均针对 `7bc8d70` 纯净树，每条反例使用独立 `tempfile.mkdtemp()` 沙箱，任务互不污染 |

### 0.2 复现证据归档（按 v1.1 §3.5）

复现脚本归档于 [`docs/reviews/evidence/2026-09-08-7bc8d70-claude/probe_checkpoint_and_adopt.py`](evidence/2026-09-08-7bc8d70-claude/probe_checkpoint_and_adopt.py)。每条探针独立 `tempfile.mkdtemp()` 项目，探针间无状态污染；对宿主仓库零写入。最后执行：2026-09-08，输出见 §二 两个 P1 小节内联的原始终端记录。环境：Linux、Python 3.10+、系统 git，无网络、无真实厂商 CLI 依赖。

### 0.3 方法论踩坑记录（自我更正）

我第一次复放检查点反例时把四个反例场景挂在**同一个** task_id 下顺序执行——`zero_hash` 先成功把任务推进到 `READY_FOR_REVIEW` 后，`check_development_checkpoint` 的入口守卫（要求当前状态为 `CODING`/`REWORK`）会让后续三个反例统统返回 `None`，若照此记录会把已确认的漏洞误判为「已修复」。这正是 grok 报告 §0 自陈的同一个坑；我在核对 grok 报告前已独立踩中并自行发现（复跑日志时间戳早于我读取 grok 报告），改为每个反例用独立沙箱 + 独立任务后，结果与 grok 报告一致。此处不算「采信 grok」，是同一个方法论陷阱两次独立触发。

---

## 一、申请 §3 机验独立复跑

| 声明 | 本机 | 判定 |
|---|---|---|
| `git show --check 7bc8d70` rc=0 | rc=0 | **VERIFIED** |
| `961bcfe..7bc8d70` 30 files / +2765 / -226 | `git diff --stat` 一致 | **VERIFIED** |
| `PYTHONPATH=src python3 -m unittest discover tests` 162/162 | `Ran 162 tests in 54.5s … OK` | **VERIFIED** |
| `compileall -q src tests` 0 Errors | rc=0 | **VERIFIED** |
| 双 Schema 8 份逐字节一致 | `docs/schemas/*.schema.json` ↔ `src/macao/schemas/` 8/8 SAME | **VERIFIED** |
| Codex P1-04「sha256 必须吻合、执行者归属杜绝假造」 | 见 P1-1 | **CONTRADICTED** |
| Codex P1-03「`task adopt` 完整实现 UC-11」 | 见 P1-2 | **CONTRADICTED**（UC-11 E1 异常流未实现） |
| L4 live-run OPS | `live_runner.py:56-58` 三 Reviewer 仍 `mock-cli`；`:76` `auto_signoff: bool = True` | **CONTRADICTED**（沿用未闭） |

---

## 二、P1：进入 L3 全量认证前必须修正

### P1-1　检查点防伪校验对全零哈希 / 缺失文件 / 空哈希 / 执行者 CLI 错配四种输入 fail-open

**独立复现**（每个场景使用独立 `tempfile.mkdtemp()` 项目 + 独立任务，隔离状态污染）：

```text
checkpoint/zero_hash            -> advanced=True   final_state=READY_FOR_REVIEW   # 应拒绝
checkpoint/missing_file         -> advanced=True   final_state=READY_FOR_REVIEW   # 应拒绝
checkpoint/empty_sha            -> advanced=True   final_state=READY_FOR_REVIEW   # 应拒绝
checkpoint/wrong_cli            -> advanced=True   final_state=READY_FOR_REVIEW   # 应拒绝（申请声明"必须与主执行席位一致"）
checkpoint/wrong_id (control)   -> advanced=False  final_state=CODING            # 对照组：id 校验确实生效
checkpoint/tampered_sha (control) -> advanced=False final_state=CODING           # 对照组：非零篡改哈希确实生效
checkpoint/good (control)       -> advanced=True   final_state=READY_FOR_REVIEW   # happy path
```

**根因**（`orchestrator.py:287-308`，`7bc8d70` 纯净树）：

```python
if doc_path.exists() and doc_path.is_file() and doc_sha and doc_sha != "0" * 64:
    calc_sha = hashlib.sha256(doc_path.read_bytes()).hexdigest()
    if calc_sha.lower() != doc_sha.lower():
        return None
# 文件不存在 / doc_sha 为空 / doc_sha 全零 → 整段哈希比对被跳过，不返回 None

exec_info = data.get("executor")
if isinstance(exec_info, dict) and exec_info.get("id"):
    ...
    if cfg_exec_id and exec_info["id"] != cfg_exec_id:
        return None
# 只比较 id，从未读取 exec_info.get("cli")
```

申请 §1.13 明确写「`submit_checkpoint` 严格校验 `full_document.sha256` 必须为合法 64 位十六进制散列且与文档实际 SHA-256 吻合；强制校验 `executor.id` 与 `executor.cli` 必须与任务配置中的主执行席位一致，杜绝假造与冒名」——四个"必须/杜绝"中有四种具体输入未被拦截。**本申请自身附带的 `.dev.yml` 信封（`docs/reviews/2026-09-08-review-request-7bc8d70.md:192`）的 `full_document.sha256` 恰好就是 64 个 `0`**，即这份申请本身就是以会被本条漏洞豁免放行的占位值通过检查点门的（该文件真实 SHA-256 为 `914ecd52415aaa083dd8e6215fa5fd3739c9157640ef3ffcfac31b70700399e1`）。

官方回归 `tests/test_p1_closures_and_regressions.py` 只构造了"非零篡改哈希 vs 正确哈希"的对照，从未构造全零、空串、缺失文件、`executor.cli` 错配四类输入——这四类恰好是 Codex 原始 P1-04 建议清单里明确要求的负例。按 GUIDELINES v1.1 §9 模式 B（"计划"当"已完成"）与模式 E（"已实现"≠"已接线"——四个分支条件都写了，但组合起来构成了一个可被绕过的豁免通道）。

**验收**：删除 `doc_sha != "0"*64` 与文件存在性前置门，改为「字段缺失/空串/全零/文件不存在」一律视为校验失败并保持 `CODING`；`executor.cli` 纳入与 `team.executor.cli` 的精确比较，或从申请声明中删除该句；补齐四类反例的官方回归测试；`dev_manifest.schema.json` 的 `full_document.sha256` 增加 `pattern: "^[0-9a-fA-F]{64}$"` 且拒绝全零常量。

### P1-2　`macao task adopt` 接受指向不存在 commit 的评审申请单，且完全绕过 `WorkflowFSM.transition()`

**独立复现**（隔离沙箱，全新 `git init` 仓库，伪造一份指向不存在 commit `deadbeef` 的评审申请单）：

```text
$ git cat-file -e deadbeef^{commit}
fatal: Not a valid object name deadbeef^{commit}          # commit 确实不存在

$ macao task adopt --no-review
✓ Successfully adopted task 'task-adopt-deadbeef' into state 'WAITING_REVIEW'!
exit=0

# 复查任务记录：
{'task_id': 'task-adopt-deadbeef', 'state': 'WAITING_REVIEW',
 'checkpoint_ref': 'deadbeef', 'review_round': 1, ...}
```

**根因**：
1. `cli/main.py:535` `checkpoint_ref = latest_baseline or head_commit`——`latest_baseline` 来自申请单**文件名**的正则提取（`prober.py` 的 `_inspect_physical_reviews`），全程无 `git cat-file`/`commit_exists` 校验；`--from-request` 分支（`:522-530`）同样只检查文件**存在**，不解析或校验其声明的 baseline。
2. `cli/main.py:590-602` 直接调用 `store.create_task(...)` + `store.update_task_state(..., state=target_st, ...)`——`update_task_state`（`storage/store.py:65-78`）是一条裸 `UPDATE tasks SET state=?` 语句，**不经过 `WorkflowFSM.transition()`**，不做 `TransitionTable.can_transition()` 校验，也不写 `STATE_TRANSITION_*` 审计事件（只写了一条 `TASK_ADOPTED` 自定义事件，非状态机标准审计类型）。

这直接违反本轮申请自己援引的 [`docs/usercases/UC11-scenarioc-inflight-adoption.md`](../usercases/UC11-scenarioc-inflight-adoption.md) §5 异常流 **E1**：「申请单声明的 baseline 在 git 历史中无法定位。**原子拒绝接管**，要求提交者修正申请单」，以及该用例 §6 验收标准第 4 条：「接管后的 FSM 转移、审计表、SQLite 状态均具备完整的合法前序」。

**影响**：任何格式正确但内容虚构的评审申请单文件名（甚至无需真实存在评审内容）都可以让系统创建一个绑定到不存在 commit 的"正在等待评审"任务，且该任务此后无法通过正常共识流程收敛（`.review.yml` 永远不会匹配到 `checkpoint_ref=deadbeef`），造成永久悬挂的活动任务——而 P1-6（单活动任务下沉至 `start_task`）恰好意味着此后任何 `task create`/`task adopt` 都会被这个"合法但虚假"的活动任务卡死，直到有人手动 `task cancel`。

**验收**：`task adopt` 解析出 `checkpoint_ref` 后，先执行 `git cat-file -e <ref>^{commit}`（或等价的 `GitManager.commit_exists`）校验存在性，不存在则按 UC-11 E1 原子拒绝并提示修正申请单；状态写入改为经过 `WorkflowFSM` 的正式转移（哪怕为此新增一个 `E2_ADOPT` trigger 类型），产生标准 `STATE_TRANSITION_*` 审计事件；`--from-request` 同样需要解析并校验其声明的 baseline，不能只检查文件存在。补充「指向不存在 commit 的申请单」「重复 adopt」「`--from-request` 指向非最新申请单」三类否定测试。

---

## 三、已对齐 / 已确认项（不抵消上述 P1，均为我独立复放，非采信申请或同行报告）

| 前序（`961bcfe`）阻断 | 本轮独立复验 | 证据 |
|---|---|---|
| 未知 CLI 借壳派发 | **CLOSED** | `prober.py:56` `ADAPTER_MAP.get(cli_name.lower())` 精确匹配，无子串/模糊匹配；未注册 CLI 直接标记 `MISSING`/报错 |
| SQLite 只读连接产生 WAL/SHM 侧车 | **CLOSED** | 独立构造 WAL 模式数据库，用 `mode=ro&immutable=1` 读取后目录内文件集不变；宿主仓 `probe --dry-run` 亦未新增侧车 |
| 场景 C 操作面缺失（`task adopt`） | **CLOSED**（命令本身） | `task adopt`/`--dry-run`/`--from-request`/`-f` 均在 `cli/main.py:485` 注册且可执行；`--dry-run` 复测零文件写入 |
| 单一活动任务未下沉 | **CLOSED** | `Orchestrator.start_task` 无 `force` 时对已存在活动任务抛 `RuntimeError`（核心层，非仅 CLI 拦截） |
| 进程退出码 fail-open | **CLOSED**（探活/诊断路径） | 非法 `macao.yaml` 时 `probe` 返回非零退出码 |
| Codex P1-01/02（Pi/Cursor 接线） | **CLOSED** | `LiveAgentDispatcher.get_adapter_for_reviewer` 可正确为 `pi`/`cursor` 构造适配器实例 |
| 既有 L3 场景（共识/僵局/超时/弃权/返工） | **未回退** | 162/162 含相关用例，串行全绿 |

---

## 四、L4 / PG-3（单独否决，沿用未闭）

`live_runner.py:56-58` 三名 reviewer 仍硬编码 `cli: "mock-cli"`；`:76` `auto_signoff: bool = True` 默认自动签收。GUIDELINES v1.1 §7.2 的 10 行 OPS 必测矩阵（真实 CLI 全流程、人工接管 `override resolve` 实机留痕、超时/崩溃恢复/并发写入/磁盘写失败等）本轮申请未提供任何一行的独立证据。**即使 P1-1/P1-2 全部修复，L4 仍需一次真实 CLI + 真实人工接管的留档演练才可申请。**

---

## 五、P2 / P3

| ID | 级 | 问题 |
|---|---|---|
| P2-1 | P2 | `dev_manifest.schema.json` 的 `full_document.sha256` 仍是裸 `type: string`，不在契约层面拒绝全零/空串/非十六进制值——P1-1 的漏洞本可在 Schema 层先堵一道 |
| P2-2 | P2 | 申请 §1.11「验收标准原样透传至审查员上下文」——`live_dispatcher.py` 的 PTY 实派 payload（checkpoint/round/diff/review_context）不含 `acceptance_criteria` 字段；该能力实际只存在于 `961bcfe` 已有的 orchestrator AEP 派发路径，本轮范围内的 `LiveAgentDispatcher` 一侧未接线 |
| P2-3 | P2 | `docs/reviews/STATUS.md` 与 `docs/MACAO_PRD_v2.md` 均未按 v1.1 §5.2 建立带 owner/expiry 的"已知简化"常设表；申请 §4.1 自评的两条"阶段性边界"（In-repo 共享工作区、`ci_gate_command` 可为 null）没有到期条件，不构成豁免 |
| P3-1 | P3 | `tests/test_task_adopt.py` 实为 5 个 `test_*` 方法，申请写"7 项" |
| P3-2 | P3 | 申请正文自称 `os.path.realpath`，实现用的是 `Path.resolve()`（语义等价，措辞应统一） |
| P3-3 | P3 | `AGENTS.md` 模块树段落仍写 126 tests，命令区段落已同步为 162，同文件内部口径不一致 |

---

## 六、交叉核对（grok / codex / qwen）

**与 grok（`NO_APPROVE`）**：P1-1（我）与 grok 报告 §4 P1-1（检查点全零/空/缺失哈希 fail-open）**独立同结论**——我在写出自己的反例并落盘归档脚本之后才读 grok 报告；两者复放输入基本一致（全零/缺失/空哈希/`executor.cli`），根因定位到同一段代码（`orchestrator.py:287-308`）。grok 额外指出 `executor.cli` 从未被读取，我独立复现中也构造了同一条（`wrong_cli` 探针），结论一致。grok 把 `task adopt` 的 FSM 旁路列为 **P2-3**（"绕过 TransitionTable"），未把"接受不存在 commit"单独构造成反例；我读过 UC-11 §5 异常流 E1 的原文措辞（"原子拒绝接管"）后认为这是一条已写明的验收标准被直接违反，且我独立复现证实了"虚构 commit 被接受"这一更强的失败模式，因此升级为 **P1-2**，与 grok 在这一点上的定级不同，详见下段与 codex 的对照。

**与 codex（`REJECT`）**：codex 独立提出 P1-7bc8d70-01（`task adopt` 接受不存在的评审基线、绕过 FSM）与 P1-7bc8d70-02（检查点防伪 fail-open），与我的 P1-2、P1-1 **各自独立收敛**——我先构造并归档了自己的 `deadbeef` 反例脚本，读 codex 报告后确认其复现方法（同样用文件名含 `deadbeef` 的伪造申请单）与我一致，根因定位（`checkpoint_ref` 无 `git commit_exists`、`update_task_state` 绕开 FSM）也一致。我认同 codex 将此定为 P1 而非 grok 的 P2——理由已写在 P1-2 小节：UC-11 E1 是一条书面的、可测试的异常流验收标准，且实测确认的失败模式（虚构 commit 被接受为合法 checkpoint_ref）比"仅审计链缺失"更严重，因为它意味着系统可以在没有任何真实评审对象的情况下创建一个永久占用单活动任务锁的任务。

**与 qwen（同样 `不予受理`）**：qwen 对 Codex P1-04（我 P1-1）给出了几乎相同的三组反例（全零、缺失、`executor.cli`），并且同样指出"本申请自己的 `.dev.yml` 信封即以全零哈希通过该门"这一自证细节——这一点我与 qwen 各自独立发现（我在 §二 P1-1 小节写出后，对照 qwen 报告确认同一处自证）。qwen 将 `task adopt` 标记为"✅ 主体"通过，只在 P3 提出`[TASK_NAME]` 位置参数不存在的措辞问题，**未发现或未升级"接受不存在 commit"这一失败模式**——这是本报告与 qwen 唯一的实质性覆盖差异，我认为 codex 与我的判定（P1）更准确地反映了 UC-11 E1 的书面要求与实测风险。

**票型汇总**：

| 评审人 | 本轮判定 |
|---|---|
| claude | `NO_APPROVE`（P1×2：检查点 fail-open + task adopt 虚构 commit/FSM 旁路） |
| grok | `NO_APPROVE`（P1×1：检查点 fail-open；task adopt FSM 旁路降至 P2） |
| codex | `REJECT`（P1×2：task adopt 虚构 commit/FSM 旁路 + 检查点 fail-open） |
| qwen | 不予受理（P1×1：检查点 fail-open；task adopt 未升级） |

四方在"检查点 fail-open"上完全一致（四方独立复现，无一方转述）；我与 codex 在"task adopt 虚构 commit"上额外收敛为 P1，grok/qwen 认为不足以单独阻断本轮（但均未反对该问题真实存在）。按 GUIDELINES §8「真理不等于投票」，本报告的 P1-2 定级基于我自己对 UC-11 §5/§6 原文的独立解读与复现结果，不因与 grok/qwen 的定级分歧而改变。

---

## 七、建议闭环顺序与验收标准

1. **P1-1**：删除全零/缺失文件/空哈希三处豁免；`executor.cli` 纳入比较或删除声明；`dev_manifest.schema.json` 增加 `sha256` 格式约束；补四类反例官方回归；下一份申请信封使用真实 SHA-256 重签。
2. **P1-2**：`task adopt` 解析 `checkpoint_ref` 后强制 `git commit_exists` 校验，不存在则按 UC-11 E1 原子拒绝；状态写入改经 `WorkflowFSM.transition()` 产生标准审计事件；补齐"不存在 commit"“重复 adopt”“`--from-request` 非最新”三类反例。
3. **L4**：真实 CLI 至少一轮非全同意评审 + 人工 `override resolve` 实机留痕；按 v1.1 §7.2 十行矩阵逐格提供证据。
4. P2 批次可在下一轮一并处理：Schema 层加固、`acceptance_criteria` 透传到 `live_dispatcher` payload、`STATUS.md`/PRD 实例化已知简化表。

验收时请重放本报告归档脚本 `evidence/2026-09-08-7bc8d70-claude/probe_checkpoint_and_adopt.py`：四个 fail-open 探针需全部翻转为 `advanced=False`，`deadbeef` 探针需返回非零退出码且不创建任务；三个对照组（`wrong_id`/`tampered_sha`/`good`）结果不得回归。

---

## 附：机器票与结构化 issue 索引

| issue_id | severity | disposition_class | 摘要 |
|---|---|---|---|
| `claude/P1-1` | critical | `BLOCKING` | 检查点防伪对全零哈希/缺失文件/空哈希/`executor.cli` 错配 fail-open；本申请信封自身即以全零哈希通过该门 |
| `claude/P1-2` | critical | `BLOCKING` | `task adopt` 接受指向不存在 commit 的评审申请单，违反 UC-11 E1；状态写入绕过 `WorkflowFSM.transition()` |

`vote`: `NO_APPROVE`
