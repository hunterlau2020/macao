# MACAO 综合编排闭环与评审方法论 v1.1 升级（`7bc8d70` / Round 3）评审结论

- **评审日期**：2026-09-08
- **评审人**：qwen（独立评审）
- **评审范围**：`961bcfe..7bc8d70`（申请 `2026-09-08-review-request-7bc8d70.md`；含代码整改 `48eea58` 与方法论 v1.1 `7bc8d70`；HEAD `a705a49` 仅增申请/STATUS）
- **对齐基准**：`docs/MACAO_REVIEW_GUIDELINES.md` **v1.1**（本轮受审交付物之一，按其 §3.4/§3.5/§8/§9/§10 执行本评审）、`docs/usercases/PRODUCT-FACTS.md` F-1~F-26、前序四方评审（codex/grok/kimi/pi-qwen @ `961bcfe`）与处置单 `2026-09-07-disposition-961bcfe.md`
- **结论**：**不予 L3 SCENARIO-VERIFIED / PG-2 全量认证；L4 RELEASE-READY / PG-3 准入不予受理。** 前序 14 项 P0/P1 中 **13 项实质闭环**（全部经生产入口动态复验）；**Codex P1-04（检查点防伪）闭环声明被反例击穿**：sha256 校验存在全零豁免与文档缺失豁免、`executor.cli` 完全不校验——且**本申请自己的 `.dev.yml` 信封即以 64 个零通过该门**（自证）。方法论 v1.1 升级本身属实且高质量。
- **结构化 issue**：`BLOCKING` × 1（P1，三facet同根）、`ADVISORY` × 5（P2×2 / P3×3）

## 已对齐 / 已确认项

逐项均经**生产入口动态复验**（非采信测试与自述），复现脚本见文末：

| 前序项 | 独立复验 | 判定 |
|---|---|---|
| P0-1 未知 CLI fail-closed | 合法配置 + `custom-claude` 席位 → `probe` exit 2、不借壳派发（模糊匹配代码已移除）；`MISSING` 标记存在于未安装已注册 CLI 路径（prober.py:485/513/738） | ✅（诊断缺口见 P2-1） |
| P1-1 会话排序确定性 | `session_locator.py:166/413` `(st_mtime, name)` 二元组稳定排序 | ✅ |
| P1-2 只读零侧车 | 已有 `state.db` 项目执行 `probe --dry-run`：前后目录比对 **0 个 `-wal`/`-shm` 增量**；`db.py`/`store.py` 注入 `immutable=1`；F-25 固化在案 | ✅ |
| P1-3 敏感词脱敏 | `secrets.py` 实含 ≥6 类正则（AKIA/AIza/JWT/Bearer/URL 口令/环境变量 token/PEM），集成点齐备 | ✅ |
| P1-4 跨项目会话隔离 | `Path.resolve()` 严格等值比对（:43/100/112/151；申请表述 `os.path.realpath`，语义等价） | ✅ |
| P1-5 worktree 幽灵引用 | `main.py:1228/1239` `worktree remove` + `prune` 组合 | ✅ |
| P1-6 单一活动任务下沉 | 第二次 `start_task` → `RuntimeError` 拒绝（核心层生效，非 CLI 层） | ✅ |
| P1-7 非零退出码 | 非法配置 → `doctor`/`probe` 均 exit 2；`--allow-degraded` 在位（can_dispatch 路径） | ✅ |
| P1-8 F-25/F-26 | PRODUCT-FACTS :57/:59 已固化，措辞含"零侧车""Fail-Closed 返回空列表" | ✅ |
| P1-9 待决评审单优先 | **本仓库活体验证**：`probe --dry-run` 正确检出 `2026-09-08-review-request-7bc8d70.md` 并列出席位；`task create` UC-2 E7 守卫在位（main.py:405-411） | ✅ |
| P1-10 / Codex P1-01/02 | `live_dispatcher` 显式接入 `CursorAgentAdapter`/`PiAdapter` 分支 + registry；**`acceptance_criteria` 透传系基线 `961bcfe` 已存在于 orchestrator AEP 路径，非本范围新增**（见 P2-2） | ⚠️ 主体 |
| Codex P1-03 `task adopt` | `--dry-run` exit 0 且零状态写入（无 state.db）；真实 adopt 建任务；7 项专项测试在位。**位置参数 `[TASK_NAME]` 不存在**（见 P3-1） | ✅ 主体 |
| 方法论 v1.1 | §3.4/§3.5/§5.2/§6/§7.2/§8.1-8.3/§9-E/§10 全部在位；§7.2 第 10 行"严禁 runner 伪造 YES_APPROVE"直接固化本评审方 08-31 轮 P1-Q4 教训；`REVIEW_GUIDEv2.md`（264 行）落地 | ✅ |
| 机验 | **162/162 OK**（实测 64.3s）、`git show --check 7bc8d70` exit 0（v1.1 §3.4 正确参照系）、`compileall` 0、diff stat 与申请"30 文件 +2765/-226"逐字吻合、STATUS 对账 146 结果+44 申请与实盘一致 | ✅ |

## P0：必须先解决

无。

## P1：发布/进入下一阶段前应修正

### QW-7BC-P1-1　Codex P1-04 检查点防伪门 fail-open——三处豁免可绕过，申请信封自证（issue_id: QW-7BC-P1-1a/b/c）

- **声明**（申请 §1.13）："`submit_checkpoint` 严格校验 `full_document.sha256` 必须为合法 64 位十六进制散列**且与文档实际 SHA-256 吻合**；强制校验 `executor.id` **与 `executor.cli`** 必须与任务配置中的主执行席位一致，**杜绝假造与冒名**"
- **反例击穿**（按 v1.1 §8.3 纪律，全部生产入口复现，`orchestrator.py:290-310`）：
  1. **全零豁免**：`sha256: "0"×64` → **ACCEPTED**（代码显式 `doc_sha != "0"*64` 才比对）。**本申请自带的 `.dev.yml` 信封正是全零 sha256**——即本次提审自己就是以占位哈希通过防伪门，声明与自证互斥；
  2. **文档缺失豁免**：`full_document.path` 指向不存在文件 → **ACCEPTED**（`doc_path.exists()` 为前置条件，缺失即跳过全部校验）；
  3. **`executor.cli` 零校验**：id 正确 + `cli: "WRONG-CLI"` → **ACCEPTED**（代码仅比对 `exec_info["id"] != cfg_exec_id`，cli 从未参与；且 id 比对仅在配置定义了 executor id 时生效）
- **对照组**（证明门并非全开）：真 sha → ACCEPTED；篡改 sha → REJECTED；冒名 id → REJECTED——与仓库测试 `test_checkpoint_full_document_sha256_validation` 覆盖一致；**三处豁免路径零测试覆盖**
- **可达性定级**（v1.1 §8.2）：检查点是评审管线的信任根（评审对象绑定），豁免以占位值即可触达，每次提审均可达 → 影响域"审计完整性/防伪" × 可达性"平凡可达" = **P1**
- **修正**：删除全零与缺失豁免（缺文档/零哈希一律拒绝）；`executor.cli` 纳入比对；schema 补 `pattern: "^[0-9a-f]{64}$"`；补三个负例测试；**申请信封重签真实 sha256**（本申请文档实哈希 `914ecd52…` 可立即验证）

## P2/P3：可延期但需登记

- **P2-1**：未知 CLI 路径诊断静默——`probe --json` 对含未知 CLI 的配置 exit 2 但 **stdout/stderr 均不含违规 CLI 名与 MISSING 标记**，且 `--allow-degraded` 在该路径无效（`valid_config=False` 先于 degraded 分支退出）。Fail-closed 方向正确，但"一律标记为 MISSING"的声明与可观测行为不符，运维无从定位是哪个席位
- **P2-2**：`acceptance_criteria` 透传归属失实——该能力在基线 `961bcfe` 已存在于 orchestrator AEP 派发路径；本范围 `live_dispatcher.py` 的 PTY 实派路径 payload（checkpoint/round/diff/review_context）**不含验收标准**，声明"LiveAgentDispatcher…原样透传"对该文件不成立
- **P3-1**：申请 §1.12 宣称 `macao task adopt [TASK_NAME]`——实测位置参数被拒（`Got unexpected extra argument`）；命令实为 `--from-request/--dry-run/-f` 选项族
- **P3-2**：申请 §1 表述 `os.path.realpath`，实现为 `Path.resolve()`（语义等价，措辞对齐即可）
- **P3-3**：探活对"存在活动任务"exit 2 属基线 `1c09dfb` 的预派发门禁设计（非本轮引入），建议在申请/文档中注明该语义，避免与 P1-7"非法配置或致命异常"口径混读

## 交叉文档需做的文字修订

1. 申请 §1.13 与处置单 `2026-09-07-disposition-961bcfe.md` 对应条目：撤回"杜绝假造与冒名"表述或改为"部分闭环"，直至 P1 修复；
2. 申请 §1.11：`acceptance_criteria` 透传注明实际落点（orchestrator AEP 路径，`961bcfe` 引入）；
3. 申请 §1.12：`task adopt` 命令签名改为实际选项族；
4. 申请"伴随机器信封"：sha256 以真实哈希重签，或显式标注 `EXAMPLE`（v1.1 §9 自检第 3 条：确定性表述与事实分离）。

## 建议的闭环顺序与验收标准

1. **QW-7BC-P1-1**（单文件级修复）：`orchestrator.py` 豁免删除 + cli 比对 + schema pattern + 3 负例测试 + 申请信封重签 → 验收：本报告证据脚本 P1-1a/b/c 三探针全部翻转为 REJECTED，对照组不回归；
2. P2-1：未知 CLI 在 probe 输出中命名 + MISSING 标记（或错误信息列出违规席位）；`--allow-degraded` 语义澄清；
3. P2-2：live 路径 payload 补 acceptance_criteria 引用，或申请措辞更正；
4. P3 批处理随下轮。
L4/PG-3 准入：待 P1 清零后，按 v1.1 §7.2 十行 OPS 矩阵提交演练证据（含第 9 行人工接管实机演练与第 10 行端到端真实性）再行受理——本轮申请未附任何 OPS 证据，不具备 L4 评审前提。

## 复现脚本与命令

- **归档脚本**：`docs/reviews/evidence/2026-09-08-7bc8d70-qwen/repro_7bc8d70_qwen.py`（自包含；每探针独立 `tempfile.mkdtemp()` 项目并清理；对宿主仓库零写入）
- **登记元数据**：issue_id = QW-7BC-P1-1a/b/c/d、QW-7BC-V-1~5、QW-7BC-P2-1、QW-7BC-P3-1；执行 commit = `7bc8d7091ba4e39c0b3282492c613817f8d664e9`（工作树与之一致，HEAD `a705a49` 仅文档）；前提 = Linux/Python 3.11/git≥2.30、无需网络与真实 CLI；**最后执行：2026-09-08，11/11 探针 CONFIRMED**
- **机验命令**：`PYTHONPATH=src python3 -m unittest discover tests`（162/162）；`git show --check 7bc8d70`（exit 0）；`python3 -m compileall -q src tests`（0）；`PYTHONPATH=src python3 -m macao.cli.main probe --dry-run`（本仓库 exit 0，检出待决评审单）

## Reviewer 自审记录

- 按 v1.1 §9 强制自检：第 6 项（"已实现≠已接线"模式 E）直接命中本轮 P1——防伪校验代码已实现，但豁免分支使其对占位输入不接线；第 7 项（修复完备性反例）对每个"严禁/杜绝"声明构造绕过输入，P1-1a/b/c 即产出
- 上轮（本人 08-31 Phase3 轨）曾判 live-run 伪造票 P1；本轮 v1.1 §7.2 第 10 行将其固化为条文——确认无利益冲突，条文内容独立成立
- 探针时序教训：首轮 L4/L5 探针因同任务状态污染产生假 REJECTED，已改为**每探针独立项目+独立任务**重测（脚本已按此实现），未让污染结果进入结论
- 13 项闭环判定全部先于读取本轮同行报告（codex/grok 已在盘）完成；同行结论仅用于本节后的面板登记
- 分歧预留：本 P1 与处置单"P1-04 彻底闭环"结论冲突，以反例证据为准（§8"真理不等于投票"）
- 未覆盖：win32、真实 LLM 评审质量、远端 push、多任务并发
