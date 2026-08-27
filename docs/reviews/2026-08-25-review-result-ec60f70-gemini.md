# MACAO 文档对齐评审报告

> **评审日期**：2026-08-25
> **评审人**：Gemini (Antigravity AI)
> **评审对象**：`docs/` 下四份核心文档的跨文档对齐情况
> **评审 ID**：mid（Multi-document Inter-Document）

---

## 评审范围

| 文档 | 角色 | 版本 |
|------|------|------|
| [`SRSv1.md`](../SRSv1.md) | v1.0 历史基线 | v1.0 |
| [`MACAO_PRD_v2.md`](../MACAO_PRD_v2.md) | **权威基准** | v2.0 |
| [`EXECUTIVE_SUMMARY.md`](../EXECUTIVE_SUMMARY.md) | v2.0 执行摘要 | v2.0 |
| [`IMPROVEMENT_SUMMARY.md`](../IMPROVEMENT_SUMMARY.md) | v1.0→v2.0 改进对比 | v2.0 |

---

## 一、总体对齐评级

| 文档对 | 对齐度 | 评级 |
|--------|--------|------|
| `MACAO_PRD_v2.md` ↔ `EXECUTIVE_SUMMARY.md` | 高度一致，存在少量细节差异 | ⭐⭐⭐⭐ |
| `MACAO_PRD_v2.md` ↔ `IMPROVEMENT_SUMMARY.md` | 整体一致，部分 Context 字段有微小出入 | ⭐⭐⭐⭐ |
| `SRSv1.md` ↔ `MACAO_PRD_v2.md` | 符合预期：v1.0 → v2.0 演进，SRSv1 标注了已知差异 | ⭐⭐⭐⭐⭐ |
| `EXECUTIVE_SUMMARY.md` ↔ `IMPROVEMENT_SUMMARY.md` | 整体一致，定位明确，无明显矛盾 | ⭐⭐⭐⭐ |

**综合结论**：文档体系整体对齐良好。`MACAO_PRD_v2.md` 确为权威基准，其他文档基本忠实地摘要/对比了其内容。以下记录发现的具体差异点，供后续修订参考。

---

## 二、详细对齐分析

### 2.1 文档体系声明对齐

#### 发现：体系描述一致 ✅

四份文档均声明了统一的文档体系层级关系，表述方向相同：

- `SRSv1.md` 标注自身为 v1.0 历史基线，指向 `MACAO_PRD_v2.md` 为权威基准 ✅
- `MACAO_PRD_v2.md` 列出完整文档体系表 ✅
- `EXECUTIVE_SUMMARY.md` 开头标注"细节以 PRD 为准" ✅
- `IMPROVEMENT_SUMMARY.md` 声明"设计细节与口径以 `MACAO_PRD_v2.md` 为准" ✅

**结论**：文档层级体系声明完全对齐，无歧义。

---

### 2.2 核心架构与工作流对齐

#### 发现 A：工作流阶段 CHECKPOINT 在摘要中被隐含 ⚠️

| 文档 | 核心工作流描述 |
|------|-------------|
| `EXECUTIVE_SUMMARY.md` | 7 步线性流程（§核心工作流 MVP） |
| `MACAO_PRD_v2.md` §1.1 | FSM 图含 REQUIREMENT→DEVELOPMENT→CHECKPOINT→REVIEW_REQUEST→REVIEWING→CONSENSUS→MERGE/REWORK 共 7 阶段 |
| `MACAO_PRD_v2.md` §1.2 | 阶段表列出 7 个阶段（含独立 CHECKPOINT 阶段，超时 1m） |

**问题**：`EXECUTIVE_SUMMARY.md` 的 7 步流程未单独提出 CHECKPOINT 阶段，将其隐含在步骤 3 与步骤 4 之间；而 PRD §1.2 明确将 CHECKPOINT 列为独立阶段（含 1m 超时）。

**建议**：在 `EXECUTIVE_SUMMARY.md` 的"核心工作流"部分补充 CHECKPOINT 阶段说明，或注明"详见 PRD §1.2"。

---

#### 发现 B：v2.0 架构中 v1.0 的 Project Manager 模块去向未说明 ⚠️

`EXECUTIVE_SUMMARY.md` 的架构速写包含：`Agent Registry`、`State Engine`、`Workflow Controller`
`SRSv1.md` v1.0 架构中有 `Project Manager`（负责项目、团队定义、角色绑定），v2.0 文档均未再提及该模块去向。

**建议**：PRD v2.0 应补充说明 v1.0 的 `Project Manager` 模块在 v2.0 中的归宿（合并入 Workflow Controller，或更名，或移除），避免读者困惑。

---

### 2.3 `.dev.yml` 格式字段对齐

#### 发现 C：`EXECUTIVE_SUMMARY.md` 示例字段不完整 ⚠️

`EXECUTIVE_SUMMARY.md` 中的 `.dev.yml` 示例（§三个关键 .yml 文件详解）包含字段：
`version`, `status`, `signal`, `executor`, `development.description`, `development.artifacts`, `development.quality_metrics`, `development.git`, `development.review_focus`

`MACAO_PRD_v2.md` §2.1 中的完整 `.dev.yml` 规范额外包含：
- `timestamp`
- `executor.role`, `executor.version`（摘要中 executor 只有 `id`, `cli`）
- `development.phase`
- `development.checklist`（关键检查清单，含 5 项 ✓）
- `artifacts` 中包含 `type` 字段（source_code/test_code/documentation）

**影响**：摘要示例字段不完整，读者若以摘要为实现参考可能遗漏关键字段（尤其是 `checklist` 和 `timestamp`）。

**建议**：在 `EXECUTIVE_SUMMARY.md` 中添加注释："示例为精简版，完整字段定义见 PRD §2.1"，或补全关键缺失字段。

---

#### 发现 D：`IMPROVEMENT_SUMMARY.md` 中 `.review.yml` 存储路径缺少 `.macao/` 前缀 ⚠️

`IMPROVEMENT_SUMMARY.md` §规范化流程中写道：
> `.reviews/<reviewer_id>.review.yml`

而 `MACAO_PRD_v2.md` §2.2 中明确：
> **位置**：`.macao/.reviews/<reviewer_id>.review.yml`

`IMPROVEMENT_SUMMARY.md` 省略了 `.macao/` 前缀，可能导致路径理解偏差。

**建议**：`IMPROVEMENT_SUMMARY.md` 中的路径统一补充 `.macao/` 前缀，与 PRD 保持一致。

---

### 2.4 投票规则对齐

#### 发现 E：2/3 规则措辞不统一（语义等价）⚠️

| 文档 | 措辞 |
|------|------|
| `EXECUTIVE_SUMMARY.md` §决策 2 | "2/3 规则下需**全票赞成**方可通过" |
| `MACAO_PRD_v2.md` §2.3 | "此时 2/3 规则要求**全票通过**" |

**结论**：语义等价，但措辞不统一。建议统一为"全票通过（2/2）"以减少歧义。

---

#### 发现 F：`IMPROVEMENT_SUMMARY.md` 中投票规则说明缺少 Deadlock 边界细节 ⚠️

`IMPROVEMENT_SUMMARY.md` §五提到：
> ✅ **多 Reviewer 冲突处理不清** | 定义 2/3 投票规则 + `vote_result.json` 记录

但未明确说明 **2 Reviewer 配置下 2/3 等价于全票通过**，以及 1:1 票数时触发人工接管的行为（PRD §2.3 和 EXECUTIVE_SUMMARY.md §决策 2 均有此说明）。

**建议**：在 `IMPROVEMENT_SUMMARY.md` 的投票规则改进说明中，补充 2 Reviewer 边界场景描述。

---

### 2.5 状态识别三层架构对齐

#### 发现 G：Layer 2 置信度标注一致 ✅

| 文档 | Layer 2 置信度 |
|------|-------------|
| `MACAO_PRD_v2.md` §3.1 | 80% 可信 |
| `EXECUTIVE_SUMMARY.md` §状态转换决策树 | 80% 猜测 |
| `IMPROVEMENT_SUMMARY.md` §三层识别 | 80% 可信 |

**结论**：三处表述一致。✅

---

#### 发现 H：Layer 3 LLM 输入日志行数 v1.0 vs v2.0 不一致，未说明原因 ⚠️

| 文档 | Layer 3 输入行数 |
|------|---------------|
| `MACAO_PRD_v2.md` §3.1 | 最后 **300** 行 Terminal Log |
| `SRSv1.md` §6.3 | last **200** logs |

**说明**：这是 v1.0 → v2.0 的有意调整（300 行 > 200 行），但无文档显式说明此变更原因。

**建议**：`IMPROVEMENT_SUMMARY.md` 或 `MACAO_PRD_v2.md` 版本历史中注明此调整。

---

### 2.6 MVP 范围对齐

#### 发现 I：4 CLI → 3 CLI 收敛已在 SRSv1.md 标注区声明 ✅

`SRSv1.md` 的标注区已明确说明此收敛，`MACAO_PRD_v2.md` §4.1 和各摘要文档均一致采用 3 CLI 方案。**对齐处理合规**。✅

---

#### 发现 J：Reviewer 从 Qwen → Kimi 的替换未在改进说明中明确 ⚠️

`SRSv1.md` 的 v1.0 原始设计中 Reviewer 列表包含 `cc-glm`（Codex）和 `qwen`（通义/Qwen）。
`IMPROVEMENT_SUMMARY.md` 全文均使用 "Codex/Kimi" 而非 v1.0 的 "Codex/Qwen"，但未明确说明 Qwen → Kimi 的替换。

**建议**：在 `IMPROVEMENT_SUMMARY.md` §六或改进总表中，明确说明 v1.0 中的 "qwen" Reviewer 在 v2.0 中由 Kimi 替换（或说明 qwen 与 cc-glm 是同一角色的不同示例标识）。

---

### 2.7 AEP 消息类型对齐

#### 发现 K：v1.0 消息名称映射已显式说明 ✅

`MACAO_PRD_v2.md` §2.4 的消息类型表已明确列出 v1.0 对应关系（`TASK_ASSIGN` → `DEVELOPMENT_STARTED`，`REVIEW_RESULT` → `REVIEW_RESPONSE` 等），`SRSv1.md` 的标注区亦已说明此映射。**对齐良好**。✅

#### 发现 L：AEP 7 种消息类型数量一致 ✅

`EXECUTIVE_SUMMARY.md` §MVP 范围清单与 `MACAO_PRD_v2.md` §2.4 均明确为 **7 种消息类型**。✅

---

### 2.8 KPI 数据对齐

#### 发现 M & N：技术 KPI 与用户 KPI 完全一致 ✅

| KPI | Target | 一致性 |
|-----|--------|---------|
| State Recognition Accuracy | >95% | ✅ |
| Explicit Signal Usage Rate | >99% | ✅ |
| Workflow Completion Rate | >90% | ✅ |
| Human Override Frequency | <10% | ✅ |
| Reviewer Average Response Time | <5min | ✅ |
| False Positive Alerts | <5% | ✅ |
| MACAO Recovery Time | <30s | ✅ |
| Code Review Turnaround | ↓87% | ✅ |
| Multi-Reviewer Consensus Time | ↓96% | ✅ |
| Developer Cognitive Load | ↓80% | ✅ |
| Rework Cycles | ↓30% | ✅ |

`EXECUTIVE_SUMMARY.md` 与 `MACAO_PRD_v2.md` §8.1/8.2 完全一致。✅

---

### 2.9 风险矩阵对齐

#### 发现 O：摘要风险表缺少"Git Conflict"风险项 ⚠️

| PRD §9.1 风险条目 | EXECUTIVE_SUMMARY.md |
|----------------|---------------------|
| CLI Hook API 不稳定 | ✅ |
| Reviewer CLI 响应慢 | ✅ |
| **Git Conflict 导致卡死**（低概率高影响） | ❌ 缺失 |
| .yml 格式破坏 | ✅（表述为".yml 文件损坏"） |
| 跨机器网络延迟 | ✅（表述为"网络临时中断"） |

**建议**：`EXECUTIVE_SUMMARY.md` 补充"Git Conflict"风险项，或注明"完整风险列表见 PRD §9.1"。

---

### 2.10 交付计划对齐

#### 发现 P：摘要 Week 1-2 交付物缺少"State Recognition FSM 文档" ⚠️

`MACAO_PRD_v2.md` §4.2 Week 1-2 明确要求完成"State Recognition FSM 文档"，而 `EXECUTIVE_SUMMARY.md` 的 Week 1-2 描述中未提及该交付物。

**建议**：摘要 Week 1-2 补充"State Recognition FSM 文档"交付物。

---

#### 发现 Q：扩展 CLI 列表（Gemini/Cursor）在 PRD §4.1 中未体现 ⚠️

`IMPROVEMENT_SUMMARY.md` Phase 4+ 和 `EXECUTIVE_SUMMARY.md` 的"不做这些"列表均提到"Gemini CLI / Cursor Agent 等"，但 `MACAO_PRD_v2.md` §4.1 的 P1+ 列表仅列出 Capability Registry、Dashboard 等，未提及扩展 CLI。

**建议**：PRD §4.1 的 P1+ 列表与摘要/改进说明保持同步，显式列出 Gemini CLI / Cursor Agent 等扩展 CLI 支持。

---

### 2.11 Reviewer Context 结构对齐

#### 发现 R：Context 示例缺少 `performance` 子字段 ⚠️

`MACAO_PRD_v2.md` §5.2 的 `review_context.quality_snapshot` 包含 `performance` 子字段（`avg_query_time_ms`, `p99_query_time_ms`），而 `IMPROVEMENT_SUMMARY.md` §三和 `EXECUTIVE_SUMMARY.md` 的 Context 示例均未包含。

**建议**：在两份摘要文档的 Context 示例中补充 `performance` 字段，或注明该字段为可选扩展项。

---

## 三、发现汇总

| ID | 类型 | 涉及文档 | 问题描述 | 严重度 | 建议操作 |
|----|------|---------|---------|--------|---------|
| A | 内容遗漏 | EXECUTIVE_SUMMARY ↔ PRD | 摘要工作流缺少 CHECKPOINT 独立阶段 | **中** | 补充说明或引用 PRD §1.2 |
| B | 内容遗漏 | PRD / EXECUTIVE_SUMMARY ↔ SRSv1 | v2.0 架构中 v1.0 的 Project Manager 模块去向未说明 | 低 | PRD 补充 Project Manager 归宿说明 |
| C | 字段不完整 | EXECUTIVE_SUMMARY ↔ PRD | `.dev.yml` 示例缺少 `timestamp`, `checklist`, `type` 字段 | **中** | 补充字段或添加"详见 PRD §2.1"注释 |
| D | 路径不一致 | IMPROVEMENT_SUMMARY ↔ PRD | `.review.yml` 路径缺少 `.macao/` 前缀 | **中** | 补全 `.macao/` 前缀 |
| E | 措辞差异 | EXECUTIVE_SUMMARY ↔ PRD | "全票赞成" vs "全票通过" 表述不统一（语义等价） | 低 | 统一措辞 |
| F | 内容遗漏 | IMPROVEMENT_SUMMARY ↔ PRD | 投票规则改进说明缺少 2 Reviewer Deadlock 边界描述 | 低 | 补充边界场景 |
| G | **一致** | 全部文档 | Layer 2 置信度 80% 表述一致 | — | 无需操作 |
| H | 数值差异（已演进） | PRD v2 ↔ SRSv1 | Layer 3 LLM 日志行数：300 vs 200，变更原因未说明 | 低 | 在改进说明中注明此变更 |
| I | **已声明差异** | SRSv1 ↔ 全部 v2.0 | 4 CLI → 3 CLI 的 MVP 收敛，已在标注区声明 | — | 无需操作 |
| J | 内容遗漏 | IMPROVEMENT_SUMMARY ↔ SRSv1 | Qwen → Kimi 的 Reviewer 替换未在改进说明中明确 | 低 | 补充说明 |
| K | **一致** | SRSv1 ↔ PRD | AEP 消息名称映射已显式说明 | — | 无需操作 |
| L | **一致** | EXECUTIVE_SUMMARY ↔ PRD | AEP 7 种消息类型数量一致 | — | 无需操作 |
| M | **一致** | EXECUTIVE_SUMMARY ↔ PRD | 技术 KPI 完全一致 | — | 无需操作 |
| N | **一致** | EXECUTIVE_SUMMARY ↔ PRD | 用户 KPI 完全一致 | — | 无需操作 |
| O | 内容遗漏 | EXECUTIVE_SUMMARY ↔ PRD | 摘要风险表缺少"Git Conflict 导致卡死"风险项 | **中** | 补充风险项或引用 PRD §9.1 |
| P | 内容遗漏 | EXECUTIVE_SUMMARY ↔ PRD | Week 1-2 交付物缺少"State Recognition FSM 文档" | 低 | 补充交付物 |
| Q | 列表差异 | IMPROVEMENT_SUMMARY ↔ PRD | Phase 4+ 扩展 CLI 列表（含 Gemini/Cursor）未在 PRD §4.1 体现 | 低 | PRD 补充扩展 CLI 说明 |
| R | 字段遗漏 | IMPROVEMENT_SUMMARY / EXECUTIVE_SUMMARY ↔ PRD | Context 示例缺少 `performance` 子字段 | 低 | 补充字段或标注为可选 |

---

## 四、优先修复建议

### 🔴 中等严重度（建议下次文档迭代优先处理）

1. **[C] `.dev.yml` 示例字段不完整**（`EXECUTIVE_SUMMARY.md`）
   → 添加注释 `# 完整字段见 PRD §2.1` 或补全 `timestamp` / `checklist` 字段

2. **[D] `.review.yml` 存储路径缺少 `.macao/` 前缀**（`IMPROVEMENT_SUMMARY.md`）
   → 将 `.reviews/<id>.review.yml` 改为 `.macao/.reviews/<id>.review.yml`

3. **[A] 摘要工作流缺少 CHECKPOINT 阶段**（`EXECUTIVE_SUMMARY.md`）
   → 在工作流步骤 3 与 4 之间补充 CHECKPOINT 说明，或添加脚注引用 PRD §1.2

4. **[O] 摘要风险表缺少"Git Conflict"风险**（`EXECUTIVE_SUMMARY.md`）
   → 补充第 5 条风险："Git Conflict 导致卡死 | 低概率高影响 | 自动检测 + 预警"

### 🟡 低严重度（可在后续版本统一处理）

5. **[E]** 统一 "全票赞成/通过" 措辞
6. **[F]** 改进说明补充 2 Reviewer Deadlock 边界
7. **[H]** 注明 Layer 3 日志行数从 200 → 300 的变更
8. **[J]** 说明 Qwen → Kimi 的 Reviewer 替换
9. **[P]** 摘要 Week 1-2 补充 FSM 文档交付物
10. **[Q]** PRD §4.1 补充扩展 CLI 列表
11. **[R]** Context 示例补充 `performance` 字段
12. **[B]** PRD 补充 Project Manager 模块归宿说明

---

## 五、评审总结

**文档体系整体设计规范**，层级关系清晰，`MACAO_PRD_v2.md` 作为权威基准的地位在所有文档中均有明确声明。

**核心一致性表现**：
- ✅ 三大核心创新（规范化流程、标准化 Context、可审计决策链）在所有文档中表述一致
- ✅ 状态识别三层架构（Explicit → Behavioral → LLM）在所有文档中方向一致
- ✅ 6 个 HUMAN_OVERRIDE 触发点在 PRD 和摘要中完全对应
- ✅ KPI 指标（技术 + 用户，共 11 条）在摘要与 PRD 中完全一致
- ✅ AEP 消息类型数量（7 种）和 v1.0→v2.0 映射均已正确标注

**主要改进空间**：集中在**示例细节的完整性**（`.dev.yml` 字段、存储路径前缀、风险条目）和**少量跨文档措辞一致性**，不影响整体设计理解，属于文档精修范畴。

---

*本报告由 Antigravity (Gemini) 自动生成，基于对四份文档的全量阅读与交叉比对。如有疑义，以 [`MACAO_PRD_v2.md`](../MACAO_PRD_v2.md) 为准。*
