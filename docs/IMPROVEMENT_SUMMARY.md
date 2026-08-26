# MACAO 改进对比总结（v2.0 → v2.3）

> 本文档详细说明 v2.0 如何融合了评审意见、第二位专家的优化建议，以及最关键的"规范化流程"创新。
>
> **文档地位**：本文档对比说明 v1.0（`SRSv1.md`）→ v2.0（`MACAO_PRD_v2.md`）的改进；设计细节与口径以 `MACAO_PRD_v2.md` 为准。

---

## 核心改进框架

### 原方案痛点 → v2.0 解决方案

```
原方案的三大隐患：
├─ ❌ State Detection 可靠性未定义
│  └─ ✅ v2.0: 显式信号优先，三层递进，99%+ 的状态转换由 .yml 文件驱动
│
├─ ❌ Reviewer 无上下文，质量无保障
│  └─ ✅ v2.0: 标准化 review_context，包含任务、代码、质量指标等完整信息
│
└─ ❌ MVP 范围过大，风险难以控制
   └─ ✅ v2.0: 严格的 P0/P1 划分（Week 1–2 PoC 先跑通单 Executor + 单 Reviewer 最小闭环；
      MVP 完整配置为单机 Claude Code + Codex/Kimi 双 Reviewer），后续渐进式扩展
```

---

## 一、规范化流程（最大创新）

### 问题定义
**原方案**：依赖"黑盒推断"（Terminal Log 分析 + LLM 判断）来识别状态

```
User Input → Claude Executor (黑盒) → 观察 Terminal 输出 → 推断状态？
                                  ↓
                          (置信度 60-80%)
                          容易误判、难以调试
```

**v2.0 创新**：引入"约定式通信"，每个阶段都有**物理产物**作为状态信号

```
User Input → Claude Executor → 主动生成 .dev.yml → MACAO 读取文件 → 确定状态
                                      ↑
                            (Explicit Signal, 100% 可信)
                      无歧义、易于调试、可审计
```

### 关键产物规范

| 阶段 | 产物文件 | 格式 | 作用 |
|------|---------|------|------|
| **Development Complete** | `.dev.yml` | YAML | Executor 宣布"我完成了" |
| **Review Response** | `.macao/.reviews/<reviewer_id>.review.yml` | YAML | 每个 Reviewer 的评审意见与投票 |
| **Consensus Decision** | `vote_result.json` | JSON | MACAO 的投票统计与最终决策 |

### 为什么这样设计更好？

1. **可审计性** ✅
   ```bash
   git log --oneline .macao/
   # 可以看到每一次状态转换的完整历史，不是"推断猜测"
   ```

2. **易于调试** ✅
   ```bash
   # 问题诊断变得清晰
   cat .macao/.dev.yml  # 开发者说了什么
   cat .macao/vote_result.json  # 投票结果是什么
   diff <(jq '.vote' vote_result.json) <(git log --oneline | head -1)  # 是否一致？
   ```

3. **支持离线工作** ✅
   ```
   # 即使 agmsg 消息队列临时不可用，.yml 文件始终存在
   # 恢复时只需重新解析即可
   ```

4. **易于扩展** ✅
   ```
   # 添加新的 CLI？只需理解这三个 .yml 格式
   # 不需要修改核心状态识别逻辑
   ```

---

## 二、改进的状态识别架构

### 三层识别（改进版 vs 原版）

**原方案**：
```
Layer 1: Hook (如果有)
Layer 2: 行为推断 (git + tests + terminal)
Layer 3: LLM Judge (置信度 60%)
       ↓
      决策 (风险：三层混合，责任不清)
```

**v2.0**：
```
Layer 1: Explicit Signal (.yml 文件) — 100% 可信
         ├─ 如果有 → 直接采用，不进入后续层
         └─ 优先权最高，无条件信任
         ↓ (仅在无显式信号时继续)
         
Layer 2: Behavioral Inference (git+tests+PTY) — 80% 可信
         ├─ 仅作辅助诊断，发出预警
         └─ 不改变实际状态，仅用于日志
         ↓ (仅在怀疑异常时继续)
         
Layer 3: LLM Diagnosis (故障诊断) — 60% 可信
         ├─ 仅用于排故，不用于决策
         └─ 触发 HUMAN_OVERRIDE，等待用户确认
```

**差异**：
- ❌ 原方案：三层混合投票，谁说了算不明确
- ✅ v2.0：清晰的优先级链，显式信号一票否决（veto）

> 注：上文各层标注的可信度（100% / 80% / 60%）及全文 "99%+" 表述均为**设计目标值**，以 PoC 实测数据为准。Layer 2 的推断结果只进入日志与预警，不推进状态机（行为约定见 PRD §3.2）。

---

## 三、解决 Reviewer 信息不对称问题

### 原方案的痛点

```
Executor (Claude Code) 完成工作
        ↓
发送 AEP REVIEW_REQUEST
        ↓
Reviewer 收到消息，但...
├─ 不知道为什么评审（业务背景）
├─ 不知道改了什么（代码变更）
├─ 不知道质量如何（测试覆盖率）
└─ 需要反复询问 Executor
   ↓
   评审效率低，质量无保障
```

### v2.0 的规范化 Context

```
Executor 完成工作，生成 .dev.yml
        ↓
.dev.yml 包含：
├─ 任务描述（为什么做）
├─ 产物清单（做了什么）
├─ 质量指标（质量多好）
├─ Git Commit ID（改了什么文件）
└─ 评审重点提示（重点评什么）
        ↓
MACAO 打包完整 review_context，发送 AEP REVIEW_REQUEST
        ↓
Reviewer 收到 review_context，包含：
├─ task_info（任务背景）
├─ code_changes（变更 refs：base_commit / head_commit，Reviewer 本地自行取 diff）
├─ quality_snapshot（质量快照）
├─ executor_self_assessment（开发者自评）
└─ references（相关文档与历史）
        ↓
Reviewer 有了全部信息，评审质量提升 ✅
```

### Context 结构详解

```yaml
# 唯一权威完整模型见 PRD §5.2；本示例可通过 docs/schemas/review_context.schema.json 校验
review_context:

  # ⓪ 传输块 - Reviewer 定位仓库与检查点所需
  dev_checkpoint:
    path: ".macao/.dev.yml"
  repository:
    workspace_path: "~/work/macao-demo/.macao/worktrees/codex/r1"  # 独立 worktree 路径
    remote_name: "origin"
    fetch_policy: "fetch_before_diff"

  # 1️⃣ 任务背景 - 为什么评审？
  task_info:
    description: "实现数据库连接池重构"
    business_impact: "提升连接复用率 30%"

  # 2️⃣ 代码变更 - 改了什么？（传 refs，Reviewer 本地自行取 diff）
  code_changes:
    refs:
      base_commit: "b2c3d4e"
      head_commit: "a1b2c3d"
    diff_command: "git diff b2c3d4e..a1b2c3d"  # 参考命令，非传输内容
    summary: { files_changed: 2, insertions: 115, deletions: 42 }
    files_list:
      - { path: "src/db/connection.py", status: "modified", added_lines: 80, deleted_lines: 30 }
      - { path: "tests/test_db.py", status: "modified", added_lines: 35, deleted_lines: 12 }

  # 3️⃣ 质量指标 - 质量多好？
  quality_snapshot:
    tests: { passed: 24, failed: 0, coverage: 0.87 }
    static_analysis: { lint_errors: 0, security_issues: 0 }

  # 4️⃣ 开发者自评 - 应该关注什么？
  executor_self_assessment:
    review_focus:
      - "Thread safety in connection pool"
      - "Timeout configuration correctness"
      - "Backward compatibility"
    known_limitations:
      - "Connection retry logic 暂未实现"

  # 5️⃣ 历史上下文 - 这是第几次评审？
  history:
    previous_reviews: 0
    previous_feedback: []

  # 6️⃣ 参考资源 - 在哪里找更多信息？
  references:
    architecture_doc: "docs/db_design.md"
    related_tickets: ["TASK-123"]
```

**结果**：Reviewer 可以立即开始评审，无需反复提问 ✅

---

## 四、融合两位专家的意见

### 第一位评审专家（我）的建议

| 建议 | v2.0 采纳方式 |
|------|-------------|
| ✅ **缩小 MVP 范围** | P0: 单机 Claude + 本地 Codex/Kimi; P1: 远程 SSH |
| ✅ **State Detection 不可靠** | 用 Explicit Signal 替代推断，99%+ 由 .yml 驱动 |
| ✅ **Reviewer Context 不完整** | 标准化 `review_context` 包，包含完整信息 |
| ✅ **多 Reviewer 冲突处理不清** | 定义 2/3 投票规则 + 最低法定人数（2 张有效票）+ `vote_result.json` 记录；2 Reviewer 配置下等价全票通过，1:1 或有效票不足进入人工仲裁 |
| ✅ **人工介入点不清楚** | 明确列出 6 个 HUMAN_OVERRIDE_TRIGGERS |
| ✅ **依赖外部 API 风险** | PoC 第一步验证 Hook 可用性 |

### 第二位专家的建议（文档中新增）

| 建议 | v2.0 采纳方式 |
|------|-------------|
| ✅ **流程规范化** | `.dev.yml` + `.review.yml` 约定式设计 |
| ✅ **排版与格式统一** | 完全按 PRD 标准格式撰写 |
| ✅ **细节补充** | 补充 AEP 消息规范（定义 7 类消息；详细格式覆盖主流程 4 类，其余遵循统一信封）、workflow FSM 图等 |
| ✅ **架构映射清晰** | K8s 对标表与 CI/CD 对标表 |
| ✅ **交付计划具体** | 8 周分阶段计划，含周度里程碑 |
| ✅ **成功指标量化** | KPI 表（State Accuracy >95%, Override <10% 等） |

---

## 五、关键设计决策的论证

### 决策 1：为什么用 YAML 而不是其他格式？

```
选项对比：

YAML (.dev.yml)        JSON                 Protocol Buffer
✅ 人类可读             ⚠️ 冗长              ❌ 二进制
✅ Git diff 友好       ⚠️ git diff 不够清   ❌ 无法直观 diff
✅ 易于版本控制        ✅ 结构化             ✅ 高效
✅ 支持注释            ❌ 不支持注释         ❌ 不支持注释
✅ 广泛的语言支持      ✅ 广泛支持           ⚠️ 需特殊库

选择 YAML 的理由：
1. 开发者友好 - 可读性最高
2. 易于 audit - git log 可以看到所有改动
3. 易于故障排查 - 直接查看文件，无需解析工具
4. 支持版本控制 - 可以 blame、cherry-pick 等
```

### 决策 2：为什么 Executor 要自己生成 .dev.yml？

```
方案 A（原方案）：MACAO 推断
├─ 优点：Executor 不需要改动
├─ 缺点：推断不准、难以调试
└─ 可靠性：60-80%

方案 B（v2.0 选择）：Executor 主动生成
├─ 优点：100% 准确、易于调试、有明确的"确认时刻"
├─ 缺点：需要改动 Executor（但可以用 Wrapper 或 Hook 自动生成）
└─ 可靠性：100%

对于 Claude Code 的实现方案：
├─ 理想情况：Claude 原生支持生成 .dev.yml（Anthropic 配合）
├─ 中等情况：通过 Hook API 拦截 TaskCompleted 事件，自动生成
├─ 降级情况：用 Python wrapper 监听 stdout，自动生成
└─ 兜底情况：人工提示开发者生成（影响体验但可行）

选择方案 B 的原因：
- Reviewer 需要可信的信号源
- System 需要可审计的决策链
- 故障恢复需要清晰的检查点
```

### 决策 3：为什么三层识别中 Layer 3 只用于故障诊断？

```
LLM 判断的风险：

❌ 用 LLM 做决策（原方案的隐患）
├─ 置信度只有 60-70%
├─ 推理过程不透明（黑盒）
├─ 同一输入多次调用可能不同（幻觉风险）
└─ 用户无法审计为什么做出这个决策

✅ 用 LLM 做诊断（v2.0 的设计）
├─ 仅在系统卡死、无法判断时触发
├─ 输出用于"提示用户"，不用于"自动决策"
├─ 输出的诊断报告用户可以看懂
└─ 最终决策权始终在人
```

---

## 六、MVP 范围的严格控制

### 为什么要缩小 MVP？

```
原方案承诺：
├─ 支持 Claude Code, Codex, Kimi, OpenCode
├─ 支持本地 + 远程 Agent
├─ 支持高级调度算法
├─ 支持 Dashboard 与 CLI 两种界面
└─ 风险：过度工程化，6-8 周无法交付

v2.0 承诺（第一阶段）：
├─ 只支持 Claude Code (Executor) + Codex/Kimi (Reviewers)
├─ 只支持本地单机（远程延至 v1.1）
├─ 投票规则简单（2/3 多数）
├─ 只有 CLI 界面（Dashboard 延至 v1.1）
└─ 优势：6-8 周可以交付，质量有保障
```

> 说明：v1.0 示例中的远程 Reviewer qwen（SSH 上的第二个 Codex 实例）随单机化收敛移出 MVP 范围；v2.0 的 Reviewer 为本地 Codex（cc-glm）+ Kimi（kimi）。qwen 可作为 3 Reviewer 目标配置在 v1.1 回归。

### 交付计划的可信度

```
Week 1-2: 架构与方案（理论工作）【计划】
Week 3-4: Adapter 层（技术验证）【计划】
Week 5: 工作流引擎（核心逻辑）【计划】
Week 6: 集成与测试（整合工作）【计划】
Week 7-8: 完善与文档（交付准备）【计划】

总耗时目标：8 周，相比原方案的 12-16 周大幅缩减（待 PoC 验证后回填实际数据）
```

---

## 七、与业界的对标

### 为什么这个设计学 Kubernetes？

```
Kubernetes 成功的关键：
1. 标准化接口（CRI, CNI, CSI）
2. 显式的 Manifest（YAML 配置）
3. Controller Pattern（observe → 调整 → 重复）
4. 可审计的决策链（kubectl apply → 资源变更 → etcd 记录）

MACAO 学到的教训：
1. 标准化接口 → AgentAdapter 接口
2. 显式的 Manifest → .dev.yml, .review.yml, vote_result.json
3. 状态机模式 → LangGraph FSM
4. 可审计的决策 → 所有状态转换都有源头文件
```

### 为什么这个设计像 CI/CD？

```
GitHub Actions 的启发：
├─ .github/workflows/ci.yml 定义流程
├─ 每个 step 都有明确的入出口
├─ 失败时用户知道在哪一步卡住了
├─ 日志完整可重放（replay）

MACAO 的借鉴：
├─ .macao/.dev.yml 定义进度检查点
├─ 每个阶段都有明确的 Artifact
├─ 卡住时用户看 .yml 文件就能诊断
├─ 所有状态转换可以从文件历史重放
```

---

## 八、对原方案的改进总结表

| 原方案问题 | 影响范围 | v2.0 解决方案 | 改进度 |
|-----------|---------|------------|-------|
| State Detection 黑盒 | 核心问题 | 用 .yml 文件作为显式信号 | ⭐⭐⭐⭐⭐ |
| Reviewer 无 Context | 高影响 | 标准化 review_context 包 | ⭐⭐⭐⭐⭐ |
| 多 CLI 集成风险大 | 中影响 | 缩小 MVP，单机先行 | ⭐⭐⭐⭐ |
| 人工接管点不明确 | 中影响 | 列出 6 个 HUMAN_OVERRIDE_TRIGGERS | ⭐⭐⭐⭐ |
| 投票规则模糊 | 低影响 | 定义 2/3 多数 + vote_result.json | ⭐⭐⭐ |
| 文档细节不足 | 低影响 | 补充 AEP Message、Workflow 图等 | ⭐⭐⭐⭐ |

---

## 九、实施路线图

### Phase 1: PoC Validation (Week 1-2)
```
目标：验证关键假设是否成立
├─ [ ] Claude Code Hook API 能否稳定获取任务完成信号？（待验证）
├─ [ ] Codex/Kimi CLI 能否通过 PTY 可靠交互？（待验证）
├─ [ ] .yml 文件作为状态信号是否足够？（待验证）
└─ 里程碑：能跑通单个 Executor + 单个 Reviewer 的流程
```

### Phase 2: Core Implementation (Week 3-6)
```
目标：实现 MVP 的所有核心功能
├─ Week 3-4: Adapter 层（3 个 CLI）
├─ Week 5: 工作流引擎（LangGraph FSM）
├─ Week 6: 集成 + 自动化测试
└─ 里程碑：完整的开发→评审→合并流程
```

### Phase 3: Polish & Release (Week 7-8)
```
目标：产品化、文档、内部培训
├─ 错误处理与恢复
├─ 日志与监控
├─ 用户手册
└─ 里程碑：可对外演示与文档
```

### Phase 4+: Expansion
```
不在 MVP 范围内（v1.1+）：
├─ Remote SSH Agent 支持
├─ Capability Registry & Scheduler
├─ Web Dashboard
├─ 其他 CLI 集成（Gemini, Cursor Agent 等）
└─ 企业级功能（RBAC, Audit, Multi-tenant）
```

---

## 十、为什么这个版本值得实施？

### 问题解决度量

```
原方案              v2.0
├─ 状态识别不可靠    → 显式信号 99%+ 可靠 ✅
├─ Reviewer 质量差   → 完整 Context 保证质量 ✅
├─ 集成风险难控      → MVP 明确范围可控 ✅
├─ 人工接管点不明确  → 6 个触发条件清晰 ✅
└─ 文档细节不足      → 产品级 PRD 交付 ✅
```

### 创新点

1. **规范化流程**（最大创新）
   - 打破"黑盒推断"，建立"约定式通信"
   - 每个阶段都有物理产物（.yml 文件）作为信号源
   
2. **标准化 Context**（高价值创新）
   - Reviewer 不再信息盲目
   - 评审质量有保障

3. **可审计的决策链**（系统性创新）
   - 所有状态转换都能追溯来源
   - 故障恢复时能明确重放历史

---

## 最终建议

### 立即行动（下周）
- [ ] 与 Anthropic 接洽确认 Claude Code Hook API 稳定性
- [ ] 与 OpenAI / Moonshot 接洽确认 Codex / Kimi PTY 交互方式
- [ ] 完成 .dev.yml 与 .review.yml 的 Schema 定义
- [ ] 启动 PoC：单 Executor + 单 Reviewer 流程

### 关键决策点（Week 2）
- Claude Code Hook 可用 → 继续实施
- Claude Code Hook 不可用 → 评估 Wrapper 方案成本
- 无法联系 Anthropic → 启动 Hook reverse-engineering 或 PTY 方案

### 成功指标（MVP 完成，验收目标——未达成前不得勾选）
- [ ] 单机 Claude + 2x Reviewer 完整工作流通过
- [ ] State Accuracy > 95%（99% 由显式信号驱动）
- [ ] Human Override < 10%（人工介入比例）
- [ ] 自动化测试覆盖 > 80%
- [ ] 文档完备（用户手册 + 内部 API 文档）

---

**版本历史**
- v1.0: 原始高阶架构设计（即 `SRSv1.md`，产品暂定名 "A"）
- v1.5: 第一位专家评审意见反馈
- v2.0: 融合两位专家意见 + 规范化流程创新（即 `MACAO_PRD_v2.md`）
- v2.0.1: 按 `docs/reviews/` 三份评审反馈修订口径（checkpoint_ref 统一命名、diff 载体改为 refs、
  共识规则引入最低法定人数、PoC 与 MVP 范围表述区分等），以 PRD 为准
- v2.1: 按 2026-08-26 复审闭环状态作用域/Context 契约问题；PRD 新增第十一～十五部分
  （系统架构、Adapter Contract、配置规范、用户旅程、边界与非功能需求），产品定位收敛为
  「固定三 CLI 的本地协作 PoC 规格」
- v2.1.1: PRD 新增第十六部分《部署形态与协作拓扑》：
  角色单一写者原则 + 七阶段流程通道标注；单机同置（MVP）与跨机分布（v1.1：Gateway /
  R1 push 前置校验 / hosts 配置段）两种场景下的角色协作设计
- v2.2: 按 2026-08-26 三份复审闭环：MERGING 中间态承接 CI gate 失败回退、Reviewer 执行权限
  边界强制 sandboxed+worktree、repository 路径统一、Task Schema 与 merge 配置段、State Store
  DDL + 双写恢复算法、agmsg DLQ、输出自愈与 PTY 规范、  docs/schemas/ 版本化 Schema + fixtures；
  另补 docs/README.md 文档索引
- v2.3: 按 8ab9be7 两份复审（kimi/opencode）闭环：review_context 收敛为唯一权威结构
  （§5.2 完整模型 + §2.4 最小子集，新增 review_context.schema.json）；Deadlock 裁定落盘
  终局 vote_result（resolution 字段）；override 枚举统一（APPROVED/REWORK/RETRY_REVIEW/CANCEL）
  并新增 E9/E10 与 CANCELLED 终态（FSM 10 态）；§6.1 触发条件 1 改 Layer 3 口径 + 人工接管
  超时总则；摘要文档三处产物示例重写为 Schema 合规；计划类 ✅ 全部改为待验证表述
- v2.3.1: 按 cc77a94 五份独立复审（kimi/opencode/codex/claude/gemini）闭环 2 P0 + 3 P1：
  rebase 豁免废除（评审对象=合并对象硬校验，任何新 hash → E4b）；Reviewer worktree
  强制化（§16.3/示例/supports_worktree 准入）；弃权口径两清（.review.yml 移出 ABSTAIN，
  仅 Orchestrator 写 vote_result）；artifacts 复合主键 + 追加归档语义；Deadlock 入口边内联
  E3 + §3.4 场景三 + E7 CANCEL→E10；评审治理全量对账规则。  P2/P3 随版本一并勘误

**下一步**：Review 本文档，反馈是否有理解偏差或遗漏之处。
