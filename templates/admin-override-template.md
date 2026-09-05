# 人工接管与干预审计备忘录模板（Admin Override Memo）

- **任务 ID (Task ID)**: `task-<id>`
- **被审 Commit (Checkpoint Ref)**: `<mid>`
- **评审轮次 (Review Round)**: `1`
- **接管时间 (Timestamp)**: `YYYY-MM-DDTHH:MM:SSZ`
- **操作管理员 (Admin Identity)**: `admin@macao.local`
- **接管原因 (Trigger)**: `consensus_deadlock` / `reviewer_timeout` / `max_rework_rounds_reached` / `manual_intervention`
- **裁决决定 (Override Choice)**: `APPROVED` / `REWORK` / `RETRY_REVIEW` / `CANCEL` / `EXTEND`

---

## 1. 接管背景与前置状态 (Trigger Context)
详述触发人工介入的具体原因（如：加权投票形成 1:1 僵局、某专家席位持续超时未响应、已达最大返工轮次 3 次等）。

## 2. 裁决方案与技术依据 (Rationale & Decision)
说明为何做出上述选择：
- 若为 `APPROVED`（强制放行）：说明为什么未通过共识的代码在当前阶段可被安全合入主干；
- 若为 `REWORK`（强制返工）：指出执行者下轮需重点修改的具体方向；
- 若为 `EXTEND`（延长时限）：说明延长的合理诉求及预期解决时间；
- 若为 `CANCEL`（取消任务）：说明取消的原因与影响。

## 3. 风险接受与责任签名 (Risk Acceptance & Sign-off)
- **风险接受人**: `[签字人姓名/邮箱]`
- **豁免缺陷清单 (`exempt_issue_ids`)**: 列出本次强制通过所豁免的审查意见 ID
- **后续补救承诺**: 说明技术债务或豁免事项预计在何时何地完成闭环

---

## 伴随机器信封：`.macao/admin_override.json`

```json
{
  "override_id": "ovr-task-001-r1",
  "timestamp": "2026-09-05T12:45:00Z",
  "task_id": "task-001",
  "checkpoint_ref": "95b7b35",
  "review_round": 1,
  "admin_identity": "admin@macao.local",
  "trigger": "consensus_deadlock",
  "choice": "APPROVED",
  "exempt_issue_ids": [
    "codex/ISSUE-01"
  ],
  "note": "经人工架构评估，该边缘超时分支已在网关层截流，批准放行合入"
}
```
