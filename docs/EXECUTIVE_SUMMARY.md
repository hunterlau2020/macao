# MACAO 产品设计 - 执行摘要与快速参考

> **文档地位**：本文档是 `MACAO_PRD_v2.md`（权威基准文档，现版本 v2.1）的执行摘要与快速参考，细节以 PRD 为准。
>
> **文档体系**：`SRSv1.md`（v1.0 历史基线）→ `MACAO_PRD_v2.md`（主文档）→ 本文档（执行摘要）+ `IMPROVEMENT_SUMMARY.md`（改进对比）。PRD v2.1 新增第十一～十五部分：系统架构、Adapter Contract、配置规范、用户旅程与运行手册、边界声明。

---

## 📋 一句话说清楚

> **MACAO** 是一个**规范化的 AI Coding Agent 编排平台**，通过**标准化流程与显式信号**，把多个 CLI 工具（Claude Code, Codex, Kimi 等）组织成一个**自动化的开发-评审-合并团队**。

> **定位声明（重要）**：v2.x 的可交付范围是**固定三 CLI（Claude Code + Codex/Kimi）的本地单机协作 PoC 规格**，不是通用跨 CLI 编排平台——调度、远程、多租户等通用化能力的路线见 PRD 第四部分，边界与非功能约束见 PRD 第十五部分。

---

## 🎯 核心创新（三大支柱）

### 1️⃣ 规范化流程（Process Standardization）

**问题**：各 CLI 的工作流不一致，系统无法可靠判断进度。

**解决**：规定每个阶段必须产出**三类标准产物**（两类 YAML manifest 由 Agent 生成，JSON 共识记录由 MACAO 生成）：
- `.dev.yml` - 开发完成的宣布书（Executor 生成）
- `.review.yml` - 评审意见的投票券（各 Reviewer 生成）
- `vote_result.json` - 最终决策的公告（MACAO 生成）

**收益**：状态识别从"推断（60%可信）"升级到"检查（99%可信）"

### 2️⃣ 标准化 Context（Standardized Context）

**问题**：Reviewer 无法理解 Executor 做了什么，评审质量低。

**解决**：MACAO 在发送评审请求时，必须包含完整的 `review_context`：
```
├─ 任务背景（为什么）
├─ 代码变更（改了什么）
├─ 质量指标（质量多好）
└─ 评审重点（关注什么）
```

**收益**：Reviewer 一眼看懂，评审效率 ↑ 500%

### 3️⃣ 清晰的决策链（Auditable Decision Chain）

**问题**：系统故障时无法追溯"为什么做出这个决策"。

**解决**：所有状态转换都有源头文件，可以 `git log` 审计。

**收益**：故障排查时间 ↓ 80%，系统可信度 ↑

---

## 📊 快速对比：原方案 vs v2.0

```
维度                    原方案              v2.0
─────────────────────────────────────────────────
状态识别可靠性          60-80% 推断       99% 显式信号
Reviewer Context       无                 完整 review_context
MVP 范围               4 CLI + 远程         3 CLI (local only)
流程规范程度           隐含理解           显式 .yml 约定
人工接管点             模糊               6 个清晰触发条件
故障恢复难度           困难               查看 .yml 文件即可
文档详细程度           高阶架构           产品级 PRD
实施风险               高（过度设计）     低（分阶段）
预计交付周期           12-16 周           6-8 周
```

> 注：表中及全文的 99% / 100% 等数字为**设计目标值**，最终以 PoC 实测为准（验收阈值见 KPI 表）。

---

## 🗺️ 产品架构速写

```
User Interface
    ↓
MACAO Orchestrator (LangGraph FSM)
    ├─ Agent Registry
    ├─ State Engine
    └─ Workflow Controller
    ↓
Agent Adapters (.dev.yml ↔ AEP ↔ .review.yml)
    ├─ Claude Code Adapter
    ├─ Codex Adapter
    └─ Kimi Adapter
    ↓
Local CLI Processes (PTY)
```

**关键**：Adapter 层是通过**.yml 文件和 AEP 消息**与 CLI 通信，不是直接调用 API。

> 说明：v1.0 架构中的 Project Manager（项目/团队定义、Agent 角色绑定）在 v2.0 中并入 Workflow Controller（编排）与 Agent Registry（角色绑定配置），配置沿用 agmsg team 定义。

---

## 🔄 核心工作流（MVP）

```
1. 用户下达指令
   ↓
2. MACAO 启动 Claude Code (Executor)
   ↓
3. Claude 开发，完成时主动生成 .dev.yml（经 ARTIFACT CHECKPOINT 校验，见 PRD §1.2）
   ↓
4. MACAO 检测到 .dev.yml，发送 AEP REVIEW_REQUEST
   ↓
5. Codex + Kimi (Reviewers) 各自生成 .review.yml
   ↓
6. MACAO 收集投票，执行 2/3 共识规则
   ↓
7. 返回结果：APPROVED（合并）或 REWORK（返工）
```

**重点**：第 3、5 步是系统的"关键握手点"，由文件驱动，100% 可靠。

---

## 📄 三个关键产物文件详解

### `.dev.yml` - "我完成了" 的宣言书

```yaml
# 精简示例：完整字段定义见 PRD §2.1
version: "1.0"
status: "ready_for_review"  # ← MACAO 读这行来判断开发是否完成
signal: "EXPLICIT"          # ← 显式信号标记，Layer 1 无条件信任
executor:
  id: "cc-ds4"
  cli: "claude-code"
  
development:
  description: "Refactored database connection pooling"
  artifacts:
    - path: "src/db/connection.py"
      changed_lines: 45
  
  quality_metrics:
    tests_passed: true
    coverage: 0.87
    lint_errors: 0
  
  git:
    latest_commit: "a1b2c3d"
    files_changed: 5
  
  review_focus:  # ← 给 Reviewer 的提示
    - "Thread safety"
    - "Timeout configuration"
```

**关键**：只要这个文件存在且 status="ready_for_review"，MACAO 就确定状态转换。

### `.review.yml` - "我的评审意见" 的投票券

```yaml
reviewer:
  id: "cc-glm"
  cli: "codex"

opinion:
  status: "CHANGES_REQUESTED"  # ← APPROVED | CHANGES_REQUESTED | REJECTED
  confidence: 0.92
  
  feedback:
    - type: "logic"
      severity: "major"
      location: "src/db/connection.py:82"
      issue: "Missing exception handling"
      suggestion: "Wrap in try-except"

vote: "NO_APPROVE"  # ← MACAO 读这行投票
```

**关键**：一个 Reviewer，一个 .review.yml，一张投票。

### `vote_result.json` - "投票已统计" 的公告

```json
{
  "checkpoint_ref": "a1b2c3d",
  "votes": [
    {"reviewer": "cc-glm", "vote": "NO_APPROVE"},
    {"reviewer": "kimi", "vote": "NO_APPROVE"}
  ],
  "decision": "REWORK_REQUIRED",
  "next_step": "Send REWORK_REQUEST to executor"
}
```

**关键**：所有投票过程透明化，用户看 JSON 就知道发生了什么。示例为精简示意版，权威 Schema 见 PRD §2.3（含最低法定人数与决策表）。

---

## 🎲 状态转换决策树

```
问题：当前状态是什么？

第 1 步：按「当前 FSM 状态 + 当前 checkpoint/round」查找该阶段对应的显式产物
        （作用域规则见 PRD §3.2/§3.4；旧产物已归档，不会遮蔽后续阶段）
├─ 任一产物有效
│  └─ ✅ 按产物映射直接确定状态（唯一能推进业务状态的途径之一，
│        另一类来源是 AEP 命令型转移，统一登记于 PRD §3.3 转移表）
└─ 全部缺失或无效
   └─ 第 2 步

第 2 步：行为推断（git 变更 + 测试通过 + PTY 安静）
└─ ⚠️ 推断结果（80%）仅写入日志与预警，仅供参考；
   不改变实际状态 —— 保持上一个已确认状态（HOLD）

第 3 步：LLM 诊断（仅当怀疑卡死）
├─ LLM 置信度 ≥ 0.7
│  └─ ⚠️ 向用户提示诊断结果，维持 HOLD，等待显式信号或人工确认
└─ LLM 置信度 < 0.7
   └─ 🚨 触发 HUMAN_OVERRIDE：状态置为 UNKNOWN，要求用户手动确认
```

**关键**：99% 的情况由第 1 步解决；系统绝不依据推断"静默推进"，边界情况始终由用户做出知情决策。

---

## ⚠️ 六个人工接管触发点

| 触发条件 | 症状 | 用户操作 |
|---------|------|--------|
| **State Ambiguity** | 显式产物缺失/无效，状态无法确定 | 输入：`状态应该是？` |
| **Reviewer Timeout** | 10min 无响应 | Ping + 等 2min + 如需要输入：`标记为弃权？` |
| **Consensus Deadlock** | 无法达成 2/3 多数 | 输入：`APPROVED 还是 REWORK？` |
| **Process Crash** | Executor CLI 崩溃 | 输入：`重试 1 次还是放弃？` |
| **Git Conflict** | Git merge 失败 | 输入：`手动解决冲突后继续？` |
| **Unknown State** | 系统卡死超过 1h | 输入：`重置到上一个已知状态？` |

**设计理念**：系统能自动处理 90% 的情况，边界情况由用户做出知情决策。

---

## 🚀 MVP 范围清单

### ✅ 做这些（第 1-2 阶段）

- [ ] Claude Code Adapter（PTY + Hook）
- [ ] Codex Adapter（PTY Wrapper）
- [ ] Kimi Adapter（PTY Wrapper）
- [ ] .dev.yml / .review.yml / vote_result.json 规范
- [ ] LangGraph FSM（8 个主要状态，见 PRD §3.3）
- [ ] 2/3 投票共识规则
- [ ] AEP Message 协议（7 种消息类型）
- [ ] CLI 交互界面（Rich + prompt_toolkit）
- [ ] 本地 agmsg 队列集成
- [ ] 自动化测试（单元 + 集成）
- [ ] 用户手册

### ❌ 不做这些（推迟至 v1.1+）

- [ ] ~~远程 SSH Agent 支持~~
- [ ] ~~Capability Registry & Scheduler~~
- [ ] ~~Web Dashboard~~
- [ ] ~~多 Reviewer Consensus 高级算法~~
- [ ] ~~Gemini CLI / Cursor Agent 等其他 CLI~~

**承诺**：集中力量把 MVP 做到 95% 完美，而不是 70% 的大而全。

**配套章节（PRD v2.1）**：系统架构与技术栈（第十一部分）、Adapter Contract v1 与能力矩阵（第十二部分）、配置规范 macao.yaml（第十三部分）、用户旅程与运行手册含 Merge Policy（第十四部分）、边界声明与非功能需求含安全/成本/评审质量评测（第十五部分）。

---

## 📅 8 周交付计划

```
Week 1-2: 方案定敲 + PoC 验证
├─ 与 Anthropic 确认 Claude Code Hook API 稳定性
├─ 与 OpenAI / Moonshot 确认 Codex / Kimi PTY 可行性
├─ 完成 .yml Schema 和 AEP 格式定义
├─ 完成 State Recognition FSM 文档
└─ 里程碑：单 Executor + 单 Reviewer 工作流 PoC

Week 3-4: Adapter 实现
├─ Claude Code Adapter
├─ Codex Adapter
├─ Kimi Adapter
└─ 里程碑：所有 Adapter 可启停与通信

Week 5: 核心业务逻辑
├─ LangGraph FSM 实现
├─ .yml 生成与解析
├─ 投票规则实现
└─ 里程碑：工作流 80% 功能完成

Week 6: 集成与测试
├─ 本地 agmsg 集成
├─ 端到端工作流测试
├─ 故障恢复测试
└─ 里程碑：自动化测试覆盖 80%

Week 7: 细节完善
├─ CLI 交互界面美化
├─ 错误消息改进
├─ 日志与监控
└─ 里程碑：可用性提升

Week 8: 文档与发布
├─ 用户手册
├─ API 文档
├─ 内部培训
└─ 里程碑：产品就绪，可对外演示
```

---

## 📈 关键 KPI

### 系统 KPI（衡量系统可靠性）

| KPI | Target | 衡量方式 |
|-----|--------|---------|
| State Recognition Accuracy | >95% | 自动化测试 |
| Explicit Signal Usage Rate | >99% | 日志统计 |
| Workflow Completion Rate | >90% | 无人工介入的完成比例 |
| Human Override Frequency | <10% | 审计日志 |
| Reviewer Average Response Time | <5min | 从消息发送到响应 |
| False Positive Alerts | <5% | 不实警告占总警告比 |
| MACAO Recovery Time (从崩溃恢复) | <30s | 故障测试 |

### 用户 KPI（衡量用户体验改善）

| KPI | Baseline | Target | 改善 |
|-----|----------|--------|------|
| Code Review Turnaround | 2 小时 | 15 分钟 | ↓ 87% |
| Multi-Reviewer Consensus Time | 3 小时 | 8 分钟 | ↓ 96% |
| Developer Cognitive Load (email 数量) | 5 封 | 1 条消息 | ↓ 80% |
| Rework Cycles (平均) | 2-3 轮 | <2 轮 | ↓ 30% |

---

## ⚡ 核心决策与论证

### 决策 1：为什么用 .yml 文件而不是推断？

| 方案 | 可靠性 | 可审计性 | 故障诊断 | 选择 |
|------|--------|---------|---------|------|
| 推断（Terminal Log） | 60-80% | ❌ | 困难 | ❌ 原方案 |
| **显式信号（.yml）** | **99%** | **✅** | **容易** | **✅ v2.0** |

**理由**：可靠性是第一位的，用户需要信任系统。

### 决策 2：为什么投票规则是 2/3 而不是全票通过？

| 规则 | 通过概率 | 容错 | 选择 |
|------|---------|------|------|
| 全票 (3/3) | 33% | 低（1 人卡住） | ❌ |
| 多数 (2/3) | 89% | 中（1 人可反对） | **✅ v2.0** |
| 绝对多数 (2/2 for 2 reviewers) | 75% | 高（全部同意） | ⚠️ 太严格 |

**理由**：平衡效率与质量，1 个 Reviewer 的"异议"不应该卡住所有人。

**补充口径**（见 PRD §2.3 共识规则与决策表）：有效票 = 响应票 − 弃权票；任何自动判定都要求有效票 ≥ 最低法定人数（2 票）。MVP 为 2 Reviewer 配置（Codex + Kimi），即要求全票通过（2/2）；1 赞成 + 1 反对、或弃权导致有效票不足，均触发 Consensus Deadlock 由用户裁定。3 Reviewer 为目标配置，协议支持 N 个 Reviewer。

### 决策 3：为什么 MVP 不支持远程 SSH？

| 支持方式 | 复杂度 | 交付周期 | 收益 | 选择 |
|---------|--------|---------|------|------|
| 本地单机 | 低 | 6-8w | 验证流程 | **✅ v2.0** |
| 本地 + SSH | 高 | 12-14w | 支持分布式 | ❌ 过度设计 |

**理由**：先用单机验证流程的可行性，再考虑分布式复杂度。大多数初期用户都是单机场景。

---

## 🛡️ 核心风险与缓解

| 风险 | 概率 | 影响 | 缓解方案 |
|------|------|------|---------|
| Claude Code Hook API 不稳定 | 中 | 高 | Week 1-2 做 PoC 验证 |
| Reviewer CLI 响应慢 | 中 | 中 | 设置合理超时 + 降级投票 |
| Git merge 冲突导致卡死 | 低 | 高 | 自动检测 + 提前预警用户 |
| Reviewer 被 prompt injection 操纵投票 | 低 | 高 | 评审输出 Schema 强校验 + review_focus 白名单 + 人工抽查点 |
| 第三方 CLI 服务条款限制自动化编排 | 中 | 中 | PoC 前 ToS/法务核实；必要时半自动模式 |
| .yml 文件损坏 | 低 | 中 | YAML Schema 验证 + 版本控制 |
| 网络临时中断 | 低 | 中 | 本地队列缓冲 + 自动重试 |

**最关键**：第 1-2 周的 PoC 就能排除 50% 的风险。

---

## 📍 立即行动项（下周）

- [ ] **联系 Anthropic**：确认 Claude Code CLI Hook API 的稳定性承诺
- [ ] **联系 OpenAI / Moonshot**：确认 Codex / Kimi CLI 是否支持 PTY 交互
- [ ] **完成 Schema**：.dev.yml 和 .review.yml 的 YAML Schema（JSON Schema Format）
- [ ] **启动 PoC**：搭建测试环境，跑通单 Executor → 单 Reviewer 的流程
- [ ] **团队同步**：Review 本文档，对各模块的责任人进行分工

---

## 📞 Q&A

### Q: 为什么不直接用 API 而要搞 .yml 文件？

**A**: 不同厂商的 CLI 没有统一的 API。.yml 文件是一个**通用的"握手协议"**，避免了对外部 API 的硬依赖。即使 Claude Code Hook 变更，我们可以靠 .yml 文件继续工作。

### Q: 状态识别这么依赖 .yml，如果开发者忘记生成怎么办？

**A**: 
- 理想情况：通过 Hook 自动生成（Anthropic 配合）
- 实际情况：通过 Wrapper 监听 stdout 自动生成
- 降级情况：CLI 界面提示用户生成
- 兜底情况：用户手工执行 `macao checkin` 命令

所有情况都有备选方案。

### Q: 为什么 LLM Judgment 只用于故障诊断而不是决策？

**A**: LLM 的置信度只有 60-70%，用来做人生大事（代码评审）的决策太冒险。它最好的用途是"诊断奇怪现象"，而不是"做重要决策"。

### Q: 如果一个 Reviewer 永远不回复怎么办？

**A**: 
1. 10min 后自动 ping 一次
2. 再等 2min
3. 触发 HUMAN_OVERRIDE：`是否标记此 Reviewer 为弃权？`
4. 用户标记弃权后，剩余 1 张有效票低于最低法定人数（2 张，见 PRD §2.3 决策表），
   自动进入 Consensus Deadlock，由用户裁定 APPROVED / REWORK / 重试评审

### Q: v2.0 比原方案"小"了，会不会无法解决真实问题？

**A**: 不会。原方案的问题在于**过度承诺**。通过缩小范围并做到极致，我们反而能：
- 更快交付（8 周 vs 12-16 周）
- 质量更高（99% 可靠性 vs 60%）
- 用户体验更好（清晰的决策链 vs 黑盒推断）

单机场景就能验证整个理念是否可行。如果单机都不行，分布式也不会行。

---

## 最后的话

**这不是 v1.0 的"简化版"，而是"精准版"。**

原方案试图一口气解决所有问题（多 CLI + 远程 + 高级调度），结果导致系统过于复杂、难以交付、可靠性无保障。

v2.0 的哲学是：**先用"规范化流程"解决状态识别难题，再用"标准化 Context"解决评审质量问题，然后用"清晰的决策链"解决故障诊断难题。**

这三个问题搞定，MACAO 就能成为 AI Coding 团队的"可信大脑"。

---

**准备好开始了吗？** 

👉 Week 1-2 行动项见上文，下周这个时候再同步进展！
