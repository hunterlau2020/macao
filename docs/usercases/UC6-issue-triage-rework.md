# UC-6 意见筛选与返工（E5/E6 循环）

- **设计日期**：2026-09-01
- **设计人**：glm
- **状态**：用例设计稿（待实现；实现前须过 Schema/测试对账）
- **关联**：PRD v2.4 §3.3（E5/E6）、§15.2（返工策略）；FAQ Q13/Q15；UC-5 `issues_index`（唯一上游）；UC-3 g（返工轮入口）。
- **边界声明**：**汇总与采纳是执行者的内容工作**（FAQ Q13 / Q15、PRODUCT-FACTS F-13）：归并「同一问题被哪些专家发现」、写标题清单与正文索引、标是否采纳。执行者不写、不改 `vote_result.decision`。编排器只检测汇总段 Schema、引用 `id` ∈ `issues_index`、机器段哈希未变；不评判归并质量，不代写采纳取值。

---

## 1. 前置条件

| # | 条件 | 不满足时的行为 |
|---|---|---|
| P1 | 任务 `REWORK`（E5 已发 `REWORK_REQUEST`，round+1） | E1 |
| P2 | 本轮 `vote_result.json` 已落盘（含 `issues_index`）或 E7 裁定产物在场 | E2 |
| P3 | 执行者可读 `docs/reviews/` 全文与 `issues_index` | E3 |

## 2. 主成功场景

### a. 执行者读取意见

a1 读 `vote_result.json` 的 `issues_index`（目录）；a2 对每条 `id` 按需读对应全文（`full_document.path` + sha256 校验）；a3 **读全文**——目录的一行摘要不足以定位修复方案（FAQ Q14：全文在 docs/reviews/）。

### b. 执行者写汇总段（`vote_result.issues_summary`）

机器段（`votes` / `decision` / `issues_index`）已由 UC-5 落盘且只读。执行者在此之后写入汇总段（归并「相同问题」、`found_by[]`、正文索引、是否采纳）；不得改机器段。独立 `adoption.yml` 仅作过渡，见遗留③：

```yaml
adoption:
  - { id: "issue-<reviewer>-3", decision: ADOPTED }        # 将修复
  - { id: "issue-<reviewer>-1", decision: REJECTED, reason: "与 #3 同根因，随 #3 一并修复" }
  - { id: "issue-<reviewer>-5", decision: DEFERRED, reason: "非本轮验收范围" }
```

规则：清单必须**穷尽**本轮 `issues_index` 的全部 `id`（每条都有明确 decision）；`REJECTED/DEFERRED` 必须附 `reason`（理由是内容，但**必须存在**是流程）。

### c. 执行者改码并提交新检查点

按采纳项修复 → 新 commit（UC-3 P2：返工轮必须新 commit）→ 回 UC-3 a–g（申请全文含采纳清单 + 修复对照）。

### d. 编排器检测（确定性）

d1 清单 Schema（`id` 存在于本轮 `issues_index`；枚举闭合 ADOPTED/REJECTED/DEFERRED）；d2 穷尽性（零遗漏）；d3 reason 存在性。**不校验** reason 语义、不校验代码是否真的修了（那是下一轮评审的事——评审者对修复质量再投票）。

### e. E6 转移

新 `.dev.yml` 合法（UC-3 d1–d6，round+1）→ `REWORK → READY_FOR_REVIEW`，回到 UC-4，新一轮评审对**新 checkpoint_ref** 全量进行（不增量、不沿用上轮票）。

### f. 返工上限

`round ≥ max_rework_rounds` 仍 `REWORK_REQUIRED` → 不再 E6，E7 交管理员（UC-7）；审计 `MAX_REWORK_REACHED`。

## 3. 备选流

| # | 场景 | 行为 |
|---|---|---|
| A1 | 执行者认为某条意见错误并拒绝 | 合法（REJECTED + reason）；评审者下一轮若坚持，票面自然反映；多轮僵持由 E7 兜底 |
| A2 | 两位评审者指出同根因问题 | 两条 `id` 分别处置（默认不同条目，UC-1 h0(2)）；执行者可一条 ADOPTED 一条 REJECTED"随 X 一并修复" |
| A3 | E4b 返工（CI 失败/签字拒绝） | 入口同为 `REWORK`，但 `issues_index` 为空、`REWORK_REQUEST.reason` 注明流水线失败；清单穷尽性对空目录自然满足 |
| A4 | 管理员 E7 裁定 REWORK | 同 P1；裁定说明替代票面作为返工依据 |

## 4. 异常流

| # | 场景 | 行为 |
|---|---|---|
| E1 | 状态非 `REWORK` | 不受理清单；`next_action` 维持原值 |
| E2 | `issues_index` 缺失（如 E4b 路径数据不全） | 以 `REWORK_REQUEST.reason` 为返工依据，清单可空；审计 `ISSUES_INDEX_ABSENT` |
| E3 | 清单引用未知 `id` | 拒收（d1 fail-closed）；逐条列出未知 id |
| E4 | 清单遗漏部分 `id` | 拒收（d2）；列出遗漏集；不代为默认 REJECTED |
| E5 | 无新 commit | 同 UC-3 E2，拒绝 |

## 5. 后置条件

- **成功**：采纳清单过 d1–d3；新检查点合法；E6 → `READY_FOR_REVIEW`；审计含清单快照。
- **失败**：停留 `REWORK`；清单退回执行者；零状态副作用。

## 6. 验收标准（可测）

1. fixture：3 条 issue，清单只引 2 条 → E4 拒绝并列出遗漏；未知 id → E3
2. REJECTED 无 reason → 拒收；A1 正例（REJECTED+reason）通过
3. 编排器产物不含"采纳/不采纳"语义字段（内容审计，FAQ Q13）
4. E6 后 `checkpoint_ref` 更新、round+1；上轮票 STALE 不进新一轮计票
5. max_rework_rounds 边界：恰好达上限 → E7 而非 E6

## 7. 实现落点

| 位置 | 变更 |
|---|---|
| `src/macao/workflow/orchestrator.py:check_development_checkpoint` | 返工轮分支：清单 d1–d3 检测、f 上限判定 |
| `src/macao/core/schema.py` | adoption 清单 Schema（id/decision/reason 枚举） |
| `tests/` | 第 6 节 |

## 8. 设计自审

- 权责闭环：评审者提问题（UC-4）、执行者定取舍（本用例）、下轮评审验证取舍（UC-4/5）——编排器全程零内容判断
- "穷尽 + 必须给理由"是流程刚性，理由质量是内容柔性，两者不混淆
- 遗留决策点：①清单载体（`.dev.yml` 内嵌 vs 独立 `adoption.yml`，随 UC-1 遗留⑤一并定）；②DEFERRED 条目是否需要跨任务追踪（v1.1 backlog 建议）
