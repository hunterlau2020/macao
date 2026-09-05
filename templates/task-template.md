# 任务设计与验收卡模板（Task Specification）

- **任务 ID (Task ID)**: `task-<slug-or-uuid>`
- **特性分支 (Feature Branch)**: `feature/<task-name>`
- **目标主干 (Target Branch)**: `main`
- **执行席位 (Assigned Executor)**: `claude-code` (或 `opencode` / `codex` / `agy`)
- **创建时间 (Created At)**: `YYYY-MM-DDTHH:MM:SSZ`

---

## 1. 业务目标与背景 (Context & Goals)
简述当前任务要解决的核心问题或新增的业务价值。避免长篇大论，突出“为什么要改”与“预期的最小闭环”。

## 2. 用户故事与验收准则 (Acceptance Criteria)

### 用户故事 (User Story)
- **Given** [前置条件或系统初始状态]
- **When** [触发动作或执行输入]
- **Then** [预期的明确系统行为与产物状态]

### 明确验收标准 (Checklist)
- [ ] `AC-1`: [明确可测的标准 1，如接口返回 200 且符合 Schema]
- [ ] `AC-2`: [明确可测的标准 2，如单元测试全部 PASS，覆盖边界条件]
- [ ] `AC-3`: [非功能约束，如执行耗时 <= 200ms]

## 3. 不在本次范围 (Non-Goals)
明确本次小步迭代坚决不做的内容，防止任务膨胀：
- [ ] 不做 [暂不需要的扩展特性 A]
- [ ] 不重构 [非核心关联模块 B]

---

## 伴随机器信封：Type A AEP 任务受理信封

```json
{
  "protocol": "AEP/1.0",
  "message_id": "msg-20260905-001",
  "timestamp": "2026-09-05T12:00:00Z",
  "type": "DEVELOPMENT_STARTED",
  "from": "admin",
  "to": "claude-code",
  "payload": {
    "task_id": "task-001",
    "specification_summary": "实现安全算术计算模块",
    "acceptance_criteria": [
      "unit_tests_pass == true",
      "coverage == 100"
    ]
  }
}
```
