# Evidence archive — pi-qwen Round 3 review of `7bc8d70`

- **Reviewer**: pi-qwen（harness: pi coding agent `PI_CODING_AGENT=true`；model `qwen3.8-max`；session `01a07bd3-8b24-72e9-8e95-62179f6a5946`）
- **Review object**: `docs/reviews/2026-09-08-review-request-7bc8d70.md`
- **Verified commit (full SHA)**: `7bc8d7091ba4e39c0b3282492c613817f8d664e9`（基线 `961bcfe`，范围 `961bcfe..7bc8d70`）
- **Script**: `repro_7bc8d70_pi_qwen.py`（自包含：自建 `tempfile.mkdtemp` 沙箱、自行 `git archive` 提取受审提交的纯净树、结束自清理；不依赖任何本地隐式状态）
- **外部前提**: `python3`（3.10+，本机 3.12）、`git`、包含提交 `7bc8d70` 的本仓库检出。**无需**网络、无需真实 CLI 厂商账号、无需预装任何 AI CLI（V04 中 `pi/opencode/codex` 二进制仅影响席位 READY 与否，不影响被测断言）。
- **最后实际执行**: **2026-09-08 01:43:37 +0800**，于 `/home/debian/macao`（工作树 HEAD `a705a49`），结果 **V01–V12 全部按预期复现、V13 FAIL（即变更清单失配缺陷被证实）**，输出已摘录入评审报告 §9。

## 脚本与 issue 的映射

| 检查 | 验证内容 | 对应 issue |
|---|---|---|
| V01 | 未知 CLI 席位 `MISSING`、`can_dispatch=False`、不借壳适配器 | 前序 P0-1（已闭环的复核） |
| V02 | WAL 库存在时 `probe --dry-run` 零 `-wal`/`-shm` 侧车 | 前序 P1-2（已闭环的复核） |
| V03 | **immutable=1 陈旧读**：写者持有未 checkpoint 的 WAL 时，probe 静默上报旧任务（`error=None`） | **本轮新发现 P2-A** |
| V04 | 12 条脱敏规则 + `_sanitize_session_name` 复用 + `probe --json` 无 PAT 明文 | 前序 P1-3（已闭环的复核） |
| V05 | Claude 同名子目录跨项目会话 → `[]` | 前序 P1-4（已闭环的复核） |
| V06 | `clean` 后 `git worktree list` 无 prunable、`.git/worktrees` 为空 | 前序 P1-5（已闭环的复核） |
| V07 | `--no-probe` 建任务被阻断（rc=1）；`--force` → E10 审计、单活动任务 | 前序 P1-6（已闭环的复核） |
| V08 | 畸形/缺失/Schema 非法配置 → `probe/doctor` 退出码 2、`create --dry-run` 非零 | 前序 P1-7（已闭环的复核） |
| V09 | 待决评审单 → `task create` UC-2 E7 阻断（rc=1） | 前序 P1-9（已闭环的复核） |
| V10 | `task adopt --dry-run` 零文件变更 | 申请 Focus 3（属实） |
| V11 | **`task adopt` 接受不存在的基线 commit** → 幽灵 `WAITING_REVIEW` 任务、全部派发失败、rc=0 | **本轮 P1-B**（与 Codex P1-01 独立互证） |
| V12 | 检查点防伪：错哈希/冒名 executor 被拒；**全零哈希被接受**；`executor.cli` 不校验 | **本轮 P1-A**（与 Grok/Codex/Qwen 独立互证） |
| V13 | 申请 §2 变更清单与 `git diff --numstat 961bcfe..7bc8d70` 对账 | **本轮 P2-B**（预期 FAIL 即缺陷成立） |

## 另行执行、未纳入脚本的机验（参照系声明，§3.4）

以下命令同样于 2026-09-08 00:55–01:44 +0800 在纯净树 `/tmp/v7bc`（`git archive 7bc8d70`）上执行：

```bash
# 测试套件（162 项）连续 4 轮全绿（1 轮初次 + 3 轮复跑）
python3 -m unittest discover tests                       # Ran 162 tests ... OK ×4
# 专项确定性（前序 P1-1 复核）：30/30 OK
for i in $(seq 1 30); do python3 -m unittest tests.test_pi_and_session_locator; done
# 提交洁净度（§3.4 参照系）
git show --check 7bc8d7091ba4e39c0b3282492c613817f8d664e9   # rc=0
# 宿主仓库实测零侧车（.macao 仅 state.db，前后集合相等）
python3 -m macao.cli.main probe --dry-run && ls .macao/
```
