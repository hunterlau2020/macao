# grok 独立机验证据（`51fa456` / Round 6）

- **审查专家**: grok
- **被审完整 SHA**: `51fa456ada474818a1107f1a11b061661dab1063`
- **最后执行**: `2026-09-10T01:47:25+08:00`
- **平台**: Linux；无网络；无厂商 CLI 额度
- **依赖**: Python 3.10+；系统 `git` / `sqlite3`

## 脚本

| 文件 | 验证的 issue_id | 说明 |
|---|---|---|
| `probe_51fa456.py` | Codex P1-bdc177e-01 / grok P2-1；Codex P1-bdc177e-02 / grok P2-2；grok P2-3；前序防伪/逃逸；L4-OPS；Pi cwd；schema 契约 | 每个检查点反例一枚新 CODING 任务；宿主仓 `src/` / `tests/` 零写入 |
| `probe_51fa456.out.txt` | 同上 | 本机最后一次完整输出（`ALL_MATCH`） |

## 复跑

```bash
cd /home/debian/macao
PYTHONPATH=src python3 docs/reviews/evidence/2026-09-10-51fa456-grok/probe_51fa456.py
```

临时工作区由脚本 `tempfile.mkdtemp()` 自建自毁。
