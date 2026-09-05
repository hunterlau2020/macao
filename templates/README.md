# MACAO 全生命周期规范模板库

本目录（`templates/`）汇集了 MACAO 架构中各个协作环节的标准化输出物模板。

MACAO 遵循**“双轨约束（Dual-Track Specification）”**模型：
1. **机器轨（结构化信封 / Manifest）**：用严格的 Draft-07 Schema 闭环约束，供编排器（Orchestrator）、状态机（FSM）与守护进程自动解析，驱动任务状态跃迁；
2. **人类/理解轨（标准化 Markdown 文档）**：为人类工程师、管理员及 LLM Agent 提供完整的背景上下文、因果推导、代码 Diff 分析与复现证据。

---

## 模板清单与映射索引

### 1. 人类/理解轨（Markdown 文档模板）

| 环节 | 模板文件 | 对应旅程/用例 | 核心约束内容 |
|---|---|---|---|
| **1. 需求与任务受理** | [`task-template.md`](task-template.md) | UC-2 任务受理 | 任务设计与验收卡（用户故事 Given/When/Then、验收清单、Non-Goals） |
| **2. 开发与检查点** | [`review-request-template.md`](review-request-template.md) | UC-3 开发与检查点 | 提审申请（改动摘要、自测验证输出、审查重点） |
| **3. 评审要求与派发** | [`review-instructions-template.md`](review-instructions-template.md) | UC-4 评审派发与审查 | Reviewer 行为准则、P0~P3 缺陷分级标准、F-17 一票否决纪律 |
| **4. 专家审查报告** | [`review-result-template.md`](review-result-template.md) | UC-4 专家审查输出 | 对齐 GUIDELINES §10：L1~L4 定级、阻塞缺陷行号与复现命令、自审记录 |
| **5. 意见处置与返工** | [`disposition-template.md`](disposition-template.md) | UC-6 意见处置与返工 | 100% 穷尽覆盖 issue、采纳/驳回技术论证、E4/E5a 分流路由 |
| **6. 人工接管备忘** | [`admin-override-template.md`](admin-override-template.md) | UC-7 人工接管 | 接管触发原因、五项裁决方案（APPROVED/REWORK/EXTEND/CANCEL）、风险签名 |

### 2. 机器轨（独立结构化 JSON/YAML 模板：`templates/manifests/`）

为了方便 CLI 脚手架生成、程序直接加载以及向 LLM Prompt 直接注入 Few-Shot 模板，在 `templates/manifests/` 提供了全部纯结构化的模板文件：

| 独立模板文件 | 对应产物路径 | 遵循的契约 Schema | 主要用途 |
|---|---|---|---|
| [`manifests/dev.template.yml`](manifests/dev.template.yml) | `.macao/.dev.yml` | `dev_manifest.schema.json` | 开发者/执行者提交检查点摘要信封 |
| [`manifests/review.template.yml`](manifests/review.template.yml) | `.macao/.reviews/r<round>/<rev>.review.yml` | `review_manifest.schema.json` | 审查席位输出的投票、缺陷列表信封 |
| [`manifests/disposition.template.yml`](manifests/disposition.template.yml) | `.macao/.dispositions/r<round>/executor.disposition.yml` | `review_disposition.schema.json` | 执行者意见处置信封（含 100% 覆盖校验） |
| [`manifests/vote_result.template.json`](manifests/vote_result.template.json) | `.macao/vote_result.json` | `vote_result.schema.json` | 编排器自动共识计票不可变落盘产物 |
| [`manifests/admin_override.template.json`](manifests/admin_override.template.json) | `.macao/admin_override.json` | `admin_override.schema.json` | 管理员人工干预或接管生效凭证 |
| [`manifests/macao_config.template.yaml`](manifests/macao_config.template.yaml) | `macao.yaml` | `macao_config.schema.json` | 项目根目录全局多 Agent 编排配置 |
| [`manifests/aep_task_started.template.json`](manifests/aep_task_started.template.json) | AEP Type A 信封 | `aep_envelope.schema.json` | 任务受理开发启动通信消息 |
| [`manifests/aep_review_request.template.json`](manifests/aep_review_request.template.json) | AEP Type B 信封 | `aep_envelope.schema.json` | 隔离 Worktree 评审派发通信消息 |

---

## 使用场景与原则

1. **Prompt 注入（Few-Shot 引导）**：
   向 LLM 下发任务指令时，直接读取对应 `manifests/*.template.json` 作为格式约束样例注入 System Prompt，确保大模型输出的 JSON 100% 符合结构。
2. **CLI 脚手架一键生成**：
   执行者开始编写处置说明时，CLI 工具可直接基于 `manifests/disposition.template.yml` 复制出带骨架的基础文件，仅需开发者填写 issues 列表，杜绝手写遗漏字段。
3. **测试自守卫（Template as Code）**：
   `tests/test_prd_snippets_schema.py` 永久集成了对 `templates/manifests/` 中所有独立文件的自动化 Schema 校验，确保模板与规范演进永远不脱节。
4. **命名规范不可变**：
   - 评审申请文件必须命名为：`docs/reviews/<yyyy-MM-dd>-review-request-<mid>[-<topic>].md`；
   - 评审结论文件必须命名为：`docs/reviews/<yyyy-MM-dd>-review-result-<mid>-<reviewer>.md`；
   - 其中 `<mid>` 必须使用当前被审 Git Commit 的短哈希（如 `95b7b35`），严禁跨轮次同名覆盖。
5. **字段命名唯一**：
   - 时间戳一律使用 `timestamp`（ISO 8601 UTC 格式），严禁使用已废弃的别名。
6. **机器信封与全文强绑定**：
   - 所有 Manifest 必须包含 `full_document` 对象（含 `path`, `evidence_commit`, `sha256`），实现结构化摘要与长篇 Markdown 报告的确定性密码学绑定。

