# PRD v2.5 设计同步轨 与 全量用例体系轨 独立评审结论（`4027cce`）

- **评审日期**：2026-09-02
- **评审人**：claude
- **评审对象（两份申请，分轨判定）**：
  - 轨 A：[`2026-09-02-review-request-4027cce-PRD-v2.5-Design-Sync.md`](2026-09-02-review-request-4027cce-PRD-v2.5-Design-Sync.md)
  - 轨 B：[`2026-09-02-review-request-4027cce-UseCases-v2.5-Alignment.md`](2026-09-02-review-request-4027cce-UseCases-v2.5-Alignment.md)
  - 总入口 [`2026-09-02-review-request-4027cce.md`](2026-09-02-review-request-4027cce.md) 一并核验
- **申请声称基线**：`4027cce`；**工作区 HEAD**：`be5ee25`（差量 = 申请文件改名 + `MACAO_REVIEW_GUIDELINES.md` §1.3 命名条款 + `STATUS.md`；被审正文与 `4027cce` 一致）
- **本人前序票**：`caf3473`（NO_APPROVE，P1×5）→ `6e35a71` 双轨（NO_APPROVE，轨 A P1×5 / 轨 B P1×4）
- **对齐基准**：`docs/MACAO_REVIEW_GUIDELINES.md` §2/§3/§5/§6/§8/§9；`docs/PRD_CHANGE_PROPOSAL_v2.5.md` §2 L34–L42（D-1～D-9）；`docs/usercases/PRODUCT-FACTS.md` F-1～F-22

## 结论

- **轨 A（PRD 设计同步）：`NO_APPROVE`**，不授予 L1 DOC-ALIGNED / PG-0。P1×4。
- **轨 B（全量用例体系）：`NO_APPROVE`**，不授予 L1 DOC-ALIGNED / PG-0。P1×1。

机器票不得为「有条件通过」（PRODUCT-FACTS F-17）。

**本轮整改的质量是六轮以来最高的。** 我在 `6e35a71` 提的 9 条 P1 里，**7 条真实闭环**，其中 UC-7 触发域收敛（轨 B P1-1）与 UC-8 远端/本地判据（轨 B P1-4）两条，改法比我建议的更干净。E4 六关卡顺序、E6 拓扑子孙守卫、disposition 枚举联动、`policy`/`vote_weight` 根级必填、`dev_manifest` 核心引用必填、SRS 8 类 AEP、UC-6/UC-7 补齐 5–8 节——逐条机验属实。

阻断本次定级的是**一条回归**和**三条未闭环**：

1. **回归（轨 A P1-1）**：为闭合我与 Codex 的契约类 P1 而收紧 Schema，却没有同步 PRD 正文——**PRD 自己的 5 处规范示例现在通不过 PRD 自己指定的契约**，仓库根 `macao.yaml` 也通不过产品自己的校验器。这正是 `0bc6247` P0-2 → `2766c69` N-6 → `2da1bc2` M-1 那条链；我在上一轮报告里刚认定它「首次断开」，本轮**重新接上**。
2. **未闭环（轨 A P1-2）**：D-6 的两道反支配门禁在契约层仍可关掉（`minimum_winning_seats: 1`、`dictator_cap_enabled: false`），`min_effective_votes` 从可选孤儿键变成了**必填**孤儿键。
3. **新发现（轨 A P1-3）**：PRD E7 声明源态含 `REWORK`，但 5 个闭合选项里 **4 个从 `REWORK` 没有可达边**；提案 §L135 还给出与 PRD 互斥的「直接推进 MERGING」。这与我上轮的轨 B P1-1 是同一缺陷类，只是换了个源态。
4. **未闭环（轨 A P1-4）**：`STATUS.md` 双向对账仍不平——基线上 **12 份结论未登记**，其中包含本申请据以论证「已修复」的全部 7 份 `6e35a71` 轮报告。
5. **新引入（轨 B P1-1）**：为闭合我上轮轨 B P1-4 而引入的 `remote_name: null` 判据，**通不过 `macao_config` 契约**（`{"type":"string","minLength":1}` 且必填），纯本地模式因此不可达；权威 PRD §14.5 也没有该模式。

第 1 条与第 5 条是同一个模式的两面：**本轮的修复动作本身产生了新的同类缺陷**。这个「每轮闭上一轮、同类再开一处」的模式我已连续第 6 轮登记（§六）。

**票型**：同基线 grok `NO_APPROVE`（P1×2）、Codex `REJECT`（P1×5）、本报告 `NO_APPROVE`（P1×5）。**三方独立收敛，无一方投赞成**（详见 §七）。

---

## 0. Reviewer 自审记录（GUIDELINES §9）

### 0.1 本轮被我自己证伪、因而**未**上报的两条假设

1. **`src/macao/core/schema.py` 依赖进程 CWD，`macao init` 在用户项目目录下会全量丧失契约校验** ——
   我看到 `get_schemas_dir()` 末行 `return Path("docs/schemas").resolve()` 就先下了结论。回头读全函数：那是**第 4 级兜底**，前面有环境变量 `MACAO_SCHEMAS_DIR`、包内 `src/macao/schemas/`（存在且已与 `docs/schemas/` 逐字节一致）、向上遍历三级。包内一级必然命中。**假设撤回。**
2. **`STATUS.md` 登记了两份不存在的文件（`2026-09-01-review-2.5-2-{gemini,grok}.md`）** ——
   我的对账脚本用 `'/review-2.5' in p` 过滤，而实际路径是 `…/2026-09-01-review-2.5-2-gemini.md`，`/review-2.5` 不是它的子串，于是这两份被算进「登记但文件不存在」。修正过滤条件后重跑：**该方向为 0**。**假设撤回**——轨 A P1-4 只保留另一个方向的证据。

### 0.2 一条我给出的是「不可复现」而非「结论为假」的判定

申请 §3.1 称「`git ls-files "*.md"` 169 份，`docs/` 175 份」。本机：`git ls-files '*.md'` = **179**，`find docs` = **180**，`find -L docs`（跟随 `docs/usecases` 软链）= **193**。四个口径无一等于 169/175。**但「0 控制字符」的结论我复现为真**（193 份全扫，0 命中）。故判 P3，且措辞是「计数不可复现」，不是「扫描结论为假」。

### 0.3 强制自检 5 项

| # | 项 | 本轮 |
|---|---|---|
| 1 | 字段声明位置 vs 实际读取位置 | **轨 A P1-1 即此类**：Schema 收紧了，PRD 示例与根配置没跟 |
| 2 | 「已完成 / 100%」是否等同证据 | 申请 §3/§4 五组机验逐条重放：4 组 VERIFIED，md 份数 CONTRADICTED |
| 3 | 确定性语言是否标注 | 「被接受 / 不可达 / 无出边」均附实例或原文行号 |
| 4 | 代码块可执行性 | 本报告全部脚本原样贴出并已实跑 |
| 5 | 每条 P1 是否附路径行号 | 是 |

### 0.4 证据类型适用性（GUIDELINES §3.1）

本轮为 **DOC + SPEC**。`src/` 只在两处作为**证据**而非定级依据：仓库根 `macao.yaml` 过不了产品自己的 `validate_config()`（轨 A P1-1 的佐证），以及 `src/macao/core/schema.py` 的 resolver 行为（轨 A P2-1）。`86/86` 覆盖的是 v2.3.1 引擎，与 L1 无关，**NOT_APPLICABLE**。

---

## 一、申请 §3 / §4 自动化结论：独立重放

| 申请声明 | 本机结果 | 判定 |
|---|---|---|
| 全库 Markdown 0 控制字符 | 193 份（跟随软链）按字节扫 `0x09/0x0b/0x0c/0x0d`，**0 命中** | 结论 **VERIFIED**；份数（169/175）**CONTRADICTED**，见 §0.2 |
| UC-6 / UC-3 / UC-1-gemini 示例 Draft-07 PASS | 三处围栏分别过 `review_disposition` / `dev_manifest` / `macao_config`，**0 error** | **VERIFIED** |
| 正例 9/9 PASS、反例 13/13 FAIL-CLOSED | 9/9 + 13/13，**逐条打印拒绝原因**确认拒的是名义约束 | **VERIFIED**，但需附加条件，见 P2-1 |
| `docs/schemas/` 与 `src/macao/schemas/` 0 diff | 8 份契约 `cmp` 全 SAME；**fixtures 目录本轮也已同步，`diff -rq` 无差异** | **VERIFIED** |
| 86/86 OK；`compileall` 0 Errors | `Ran 86 tests in 34.588s ... OK`；退出 0 | **VERIFIED**（与 L1 无关） |

**补跑（申请未做，也是本轮的核心发现来源）——PRD 正文规范示例 vs 其自称契约**：

```bash
python3 - <<'PY'
import re,json,yaml,jsonschema,glob,os
S={};store={}
for p in glob.glob('docs/schemas/*.schema.json'):
    d=json.load(open(p)); S[os.path.basename(p).replace('.schema.json','')]=d
    store[d['$id']]=d; store[os.path.basename(p)]=d
def V(n): return jsonschema.Draft7Validator(S[n], resolver=jsonschema.RefResolver.from_schema(S[n],store=store))
lines=open('docs/MACAO_PRD_v2.md').read().split('\n')
def sect(a_re,b_re):
    a=b=None
    for i,l in enumerate(lines):
        if a is None and re.match(a_re,l): a=i
        elif a is not None and re.match(b_re,l): b=i;break
    return '\n'.join(lines[a:b])
for a,b,sch in [(r'^### 2\.1 ',r'^### 2\.2 ','dev_manifest'),(r'^### 2\.2 ',r'^### 2\.3 ','review_manifest'),
                (r'^### 2\.3 ',r'^### 2\.4 ','vote_result'),(r'^### 2\.5 ',r'^## 第三部分','review_disposition'),
                (r'^### 5\.2 ',r'^### 5\.3 ','review_context'),(r'^## 第十三部分',r'^## 第十四部分','macao_config')]:
    for lang,f in re.findall(r'^```(yaml|json)\n(.*?)^```', sect(a,b), re.M|re.S):
        o=yaml.safe_load(f); k=list(o) if isinstance(o,dict) else []
        cand=[o]+([o[k[0]]] if len(k)==1 and isinstance(o.get(k[0]),dict) else [])
        best=min((list(V(sch).iter_errors(c)) for c in cand), key=len)
        print(f"PRD {a[4:12]:14s} -> {sch:20s} {'PASS' if not best else 'FAIL('+str(len(best))+')'}")
        for e in best[:3]: print("      -", '/'.join(map(str,e.path)) or '(root)', ':', e.message[:100])
for lang,f in re.findall(r'^```(json)\n(.*?)^```', sect(r'^### 2\.4 ',r'^### 2\.5 '), re.M|re.S):
    try: o=json.loads(f)
    except Exception: continue
    if not isinstance(o,dict) or 'type' not in o: continue
    errs=list(V('aep_envelope').iter_errors(o))
    print(f"PRD §2.4 {o['type']:24s} -> aep_envelope {'PASS' if not errs else 'FAIL('+str(len(errs))+')'}")
    for e in errs[:2]: print("      -", '/'.join(map(str,e.path)) or '(root)', ':', e.message[:100])
PY
```

输出：

```
PRD  2\.1          -> dev_manifest         PASS
PRD  2\.2          -> review_manifest      PASS
PRD  2\.3          -> vote_result          PASS
PRD  2\.5          -> review_disposition   FAIL(1)
      - (root) : 'issues_index_sha256' is a required property
PRD  5\.2          -> review_context       PASS
PRD 第十三部分          -> macao_config         FAIL(2)
      - (root) : 'version' is a required property
      - policy : 'min_effective_votes' is a required property
PRD §2.4 DEVELOPMENT_STARTED      -> aep_envelope FAIL(2)
      - payload : 'specification_summary' is a required property
      - payload : 'acceptance_criteria' is a required property
PRD §2.4 REVIEW_REQUEST           -> aep_envelope FAIL(8)
      - payload/review_context : 'evidence' is a required property
      - payload/review_context/dev_checkpoint : 'base_commit' is a required property
PRD §2.4 REVIEW_RESPONSE          -> aep_envelope PASS
PRD §2.4 REWORK_REQUEST           -> aep_envelope PASS
PRD §2.4 DISPOSITION_REQUIRED     -> aep_envelope FAIL(2)
      - payload : 'vote_result_ref' is a required property
      - payload : 'timeout_deadline' is a required property
PRD §2.4 MERGE_COMPLETED          -> aep_envelope PASS
PRD §2.4 STATE_CHANGED            -> aep_envelope PASS
PRD §2.4 HUMAN_OVERRIDE_REQUEST   -> aep_envelope PASS
```

**5 处 FAIL。** 详见轨 A P1-1。

---

## 二、本人 `6e35a71` 轮 9 条 P1 闭环核验（逐条机验，不采信自述）

| 轨 | 上轮项 | 判定 | 证据 |
|---|---|---|---|
| A | **DS-P1-2** E4 行流水线顺序倒置 | **VERIFIED 闭环** | `MACAO_PRD_v2.md:853` 现为「六道关卡合并流水线（§14.5：关卡 1 pre-merge evidence push 校验 (ls-remote) → 关卡 2 检出 → … → 关卡 6 …）」，与 §14.5 编号与 UC-8 关卡表三方一致 |
| A | **DS-P1-3** 拓扑守卫四种强度 | **VERIFIED 闭环** | `MACAO_PRD_v2.md:858` E6 增「且为上一轮 checkpoint_ref 之拓扑子孙」；`v2.5_CODE_CHANGE_INVENTORY.md:85` 增「必须为上一轮 `checkpoint_ref` 之严格拓扑子孙：`git merge-base --is-ancestor <prev_ref> <new_ref>`」。与 UC-3 `:16`/`:53` 及 `orchestrator.py:260` 四方同强度 |
| A | **DS-P1-5** `DEFERRED`/`REJECTED` 联动缺失 | **VERIFIED 闭环** | 新增反例 `disposition_deferred_with_new_checkpoint.yml` / `disposition_rejected_with_new_checkpoint.yml` 实测均被拒（`False was expected`）；`issues_index_sha256` 已进 `required` |
| A | **DS-P2-6** `dev_manifest` 必填集 | **VERIFIED 闭环** | `task_id`/`checkpoint_ref`/`full_document` 已必填；反例 `dev_missing_core_fields.yml` 被拒 |
| A | **DS-P2-7** SRS「7 类 AEP」 | **VERIFIED 闭环** | `SRSv1.md:612` 现为「8 类 AEP/1.1 消息（Type A～Type H，含 Type E `DISPOSITION_REQUIRED`）」 |
| A | **DS-P1-1** policy 配置面 | **部分闭环** | 根级已必填 `policy`+`version`，`reviewers[].vote_weight` 已必填 ✓；`minimum_winning_seats`/`dictator_cap_enabled`/`min_effective_votes` **未闭环**，见轨 A P1-2 |
| A | **DS-P1-4** STATUS 对账 | **未闭环** | 见轨 A P1-4 |
| B | **UC-P1-1** UC-7 P6/P3 无 E7 可达边 | **VERIFIED 闭环（改得比我建议的干净）** | UC-7 §1 收敛为 P1–P4，四个触发全部进入 `CONSENSUS_CHECK`，全部经 E7 可达；Init 歧义与 Git Conflict 以显式「边界说明」剥离，且 `MACAO_PRD_v2.md:855` E4b 同步增列「或 Git conflict」，使冲突有确定性出边 |
| B | **UC-P1-2** UC-6/UC-7 缺模板小节 | **VERIFIED 闭环** | 11 份 UC 逐份扫描：UC-6 与 UC-7 的验收标准/后置条件/异常流/实现落点/设计自审均为 1（仅 UC-1-gemini 仍为 0，属我上轮 P2-4） |
| B | **UC-P1-3** 拓扑守卫（跨轨同 DS-P1-3） | **VERIFIED 闭环** | 同上 |
| B | **UC-P1-4** UC-8 远端不可达两种互斥结果 | **文字层闭环，契约层新破** | UC-8 `:23`/`:24`/`:56` 已按「`remote_name` 非空 = 远端共享 / `remote_name: null` = 纯本地」给出确定性判据——这正是我建议的改法；但该判据**不可表达**，见轨 B P1-1 |

**9 条里 7 条真实闭环。** 这是六轮以来闭环率最高的一轮。

---

## 三、轨 A（PRD 设计同步）P1：必须先解决（4 项）

### A-P1-1　收紧 Schema 未同步 PRD 正文：5 处规范示例通不过 PRD 自己指定的契约，仓库根配置通不过产品自己的校验器

**证据**（复现脚本与完整输出见 §一）

| 位置 | 失败原因 | 成因 |
|---|---|---|
| PRD §2.5 `executor.disposition.yml` 规范示例 | `'issues_index_sha256' is a required property` | 本轮为闭合我的 DS-P1-5 把该字段移入 `required` |
| PRD 第十三部分 `macao.yaml` 规范示例 | `'version' is a required property`；`policy: 'min_effective_votes' is a required property` | 本轮为闭合 Codex P1-3 把根级 `version` 与整组 `policy` 键设为必填 |
| PRD §2.4 Type A `DEVELOPMENT_STARTED` 示例 | `payload: 'specification_summary'` / `'acceptance_criteria' is a required property` | 本轮新增 per-type payload 契约 |
| PRD §2.4 Type B `REVIEW_REQUEST` 示例 | FAIL(8)，首条 `payload/review_context: 'evidence' is a required property` | 同上 + 新增 `$ref` 到 `review_context.schema.json` |
| PRD §2.4 Type E `DISPOSITION_REQUIRED` 示例 | `payload: 'vote_result_ref'` / `'timeout_deadline' is a required property` | 同上 |

外加**仓库根配置**：

```bash
PYTHONPATH=src python3 -c "
import yaml; from macao.core.schema import validate_config
print(validate_config(yaml.safe_load(open('macao.yaml'))))"
```

输出：`(False, "'version' is a required property")`。补测每一位 reviewer 亦缺 `vote_weight`（3 处）。**产品自带的 `macao.yaml` 通不过产品自己的 `validate_config()`。** 86/86 绿灯不覆盖这一点。

**为什么这是 P1 而不是文字瑕疵**

- PRD §2.5 与第十三部分自称是这两个产物的**规范定义**；§2.4 的八个 JSON 是 AEP/1.1 的**规范信封样本**。L1 的判据（GUIDELINES §2.1）恰是「设计文档之间、与权威基准之间一致；所有 YAML/JSON 示例是合法可解析格式」——示例过不了自己的契约，正落在这句话里。
- 这是**回归**，不是遗留。我在 `6e35a71` 轮报告 §一 明确记录过「六处示例全部 errors=0，`P0-2 → N-6 → M-1` 复发链首次断开」。本轮为闭合 P1 而收紧契约，把它重新接上了。
- Phase 1 实现者从 PRD 抄示例建 fixture，会得到一批过不了契约的产物。

**附带发现（同一处，独立成条更清楚）**：PRD §2.4 Type B 内嵌的 `review_context` 只有 **9 个**顶层块（缺 `evidence`），而 §5.2 自称「唯一权威完整模型」的是 **10 大必需块**：

```
§2.4 Type B 内嵌 review_context 顶层键: [code_changes, dev_checkpoint, executor_self_assessment,
                                          history, quality_snapshot, references, repository,
                                          review_guidelines, task_info]      ← 9 个
§5.2 唯一权威模型 顶层键                : 上列 9 个 + evidence + required_blocks
§5.2 有而 §2.4 缺: ['evidence', 'required_blocks']
```

这与我上轮的 DS-P2-1（提案两处写「9 大 context 语义块」，PRD/Schema/README 写 10）**同源且仍未闭环**（`grep -c '9 大' docs/PRD_CHANGE_PROPOSAL_v2.5.md` = 2）。本轮的 `$ref` 让它第一次变成机器可检出的。

**最小闭环**
1. PRD §2.5 示例补 `issues_index_sha256`；
2. PRD §13 示例补 `version: "2.5"` 与 `policy.min_effective_votes`（若采纳 A-P1-2 的删键方案，则改为从契约移除该键）；
3. PRD §2.4 Type A/E 示例补齐新必填字段；Type B 的内嵌 `review_context` 直接改用 §5.2 的十块模型；
4. 仓库根 `macao.yaml` 补 `version` 与三处 `vote_weight`；
5. **把「PRD 全部规范示例 × 其对应契约」做成交付前门禁**（§一 的脚本可直接用）——这是本条能复发三次的根因。

---

### A-P1-2　D-6 的两道反支配门禁在契约层仍可关闭；`min_effective_votes` 由可选孤儿键升级为必填孤儿键

**证据**

本轮 `macao_config.schema.json` 确实收紧了，但收紧的是**存在性**，不是**取值域**：

```python
import json,yaml,jsonschema,copy
c=json.load(open('docs/schemas/macao_config.schema.json'))
base=yaml.safe_load(open('docs/schemas/fixtures/valid/macao_config.yaml'))
V=jsonschema.Draft7Validator(c)
print("control:", "PASS" if not list(V.iter_errors(base)) else "FAIL")
for k,v in [('minimum_winning_seats',1),('dictator_cap_enabled',False)]:
    x=copy.deepcopy(base); x['policy'][k]=v
    e=list(V.iter_errors(x))
    print(f"  policy.{k} = {v!r:6} -> {'ACCEPTED' if not e else 'REJECTED'}")
```

```
control: PASS
  policy.minimum_winning_seats = 1      -> ACCEPTED
  policy.dictator_cap_enabled = False  -> ACCEPTED
```

对照权威：

- `docs/PRD_CHANGE_PROPOSAL_v2.5.md:414`（本轮未改动）：「胜方最少席位门禁：胜方有效席位数 $\ge minimum\_winning\_seats$（默认 2，**且 $2 \le minimum\_winning\_seats \le N$**）」
- `docs/PRD_CHANGE_PROPOSAL_v2.5.md:410`：「配置期独裁帽：$\forall i, 3 w_i < 2W$（**不满足则拒绝启动**）」——无条件
- `docs/FAQ.md:310`：「胜方最少席位：胜方席位数 $\ge 2$（**禁止单席位独裁裁决**）」
- `docs/schemas/macao_config.schema.json:75`：`"minimum_winning_seats": { "type": "integer", "minimum": 1 }`
- `docs/schemas/macao_config.schema.json:74`：`"dictator_cap_enabled": { "type": "boolean" }`

我在 `6e35a71` 轮给出的判定改变反例仍然成立（权重 `[5,2,1,1]`，$W=9$，独裁帽合法因 $3\times5=15<18$；票 `YES(5)/ABSTAIN(2)/NO(1)/NO(1)`）：`minimum_winning_seats=1` → **APPROVED，胜方席位数 = 1**；`=2` → DEADLOCK。**一份完全合规的配置可以让单一席位批准合并**，正是 FAQ:310 明文说这道门禁存在就是为了禁止的情形。

`min_effective_votes` 则走向了相反方向：本轮把它写进了 `policy.required`（六个必填键之一），但五重门禁**不读这个键**，`vote_result.policy_snapshot` 的 required 里也没有它，`UC1-init-glm.md:253` 仍指引管理员用它调「法定人数风险」。同一个「席位法定人数」现在有 `min_effective_votes` 与 `seat_quorum_required` 两个名字，且**两个都强制填写**（GUIDELINES §5 唯一权威表）。

**最小闭环**
1. `macao_config.schema.json` 与 `vote_result.schema.json` 的 `minimum_winning_seats` 下界由 `1` 改 `2`；
2. `dictator_cap_enabled` 改 `{"type":"boolean","const":true}`，或直接删键（推荐：D-6 说它不可选）；
3. `min_effective_votes` 从 `required` 移出并删键，同步清理 PRD §13 示例、`UC1-init-gemini.md:167`、`UC1-init-glm.md:253`；
4. `minimum_winning_seats <= N` 的上界写进 PRD §13 与 Loader（Draft-07 表达不了，属运行时）。
   *验收*：`{"minimum_winning_seats":1}`、`{"dictator_cap_enabled":false}` 两个反例进 `fixtures/invalid/`，**均须被拒并打印拒绝原因**。

---

### A-P1-3　PRD E7 声明源态含 `REWORK`，但 5 个闭合选项里 4 个从 `REWORK` 无可达边；提案 §L135 另给一条与 PRD 互斥的边

**证据**

`docs/MACAO_PRD_v2.md:859` E7 行**当前状态**一栏：`HOLD`（`CONSENSUS_CHECK` **或 `REWORK`**）；同行伴随动作把 5 个 choice 映射到 E4/E5/E5a/E9/E10。

把这 5 条目标边的**当前状态**逐一取出：

| choice | 目标转移 | 该转移的「当前状态」 | 从 `REWORK` 可达？ |
|---|---|---|---|
| `APPROVED` | E4（或 E5a） | `CONSENSUS_CHECK` | ✘ |
| `REWORK` | E5 | `CONSENSUS_CHECK` | ✘ |
| `RETRY_REVIEW` | E9 | `CONSENSUS_CHECK` | ✘ |
| `CANCEL` | E10 | `*`（任意活动态） | ✔ |
| `EXTEND` | 保持当前状态 | — | ✔ |

而 `docs/MACAO_PRD_v2.md:867` 明文：「**除本表所列来源外，任何实现不得引入其他状态转移路径**」。所以从 `REWORK` HOLD 发起 override，5 个「闭合选项」里 3 个在状态机上无法执行。

同时 `docs/PRD_CHANGE_PROPOSAL_v2.5.md:135` 给出第三种说法：

> **REWORK_REQUIRED 覆盖为 APPROVED**：E7 源状态包含 `REWORK` 与 `CONSENSUS_CHECK`。当在 `REWORK` 状态下管理员决定豁免合并时，**通过 E7 转移直接推进至 `MERGING`**

这与 PRD E7 本轮刚写进去的「解除 HOLD → `SHOULD_DISPOSE` → 待执行者 FINAL disposition 校验通过后分流 E4/E5a」以及 UC-7 `:35` 的「**严禁无 FINAL 直跳 MERGING**」**直接互斥**。

**这是我上轮轨 B P1-1 的同一缺陷类换了个源态**：上轮是 UC-7 声明 `MERGING`/init 两个源态而 E7 只接受 `CONSENSUS_CHECK`/`REWORK`；本轮用例侧收敛到了 `CONSENSUS_CHECK`（改得对），但 **PRD 侧的 `REWORK` 源态没有一并收敛**——现在变成 PRD 声明了一个连 UC-7 都不再使用、且大部分选项无法执行的源态。

**最小闭环**（二选一）
- (a) 把 E7 的当前状态收敛为 `CONSENSUS_CHECK`（与 UC-7 §1 的 P1–P4 一致），并删除提案 §L135 的「直接推进至 `MERGING`」段；或
- (b) 保留 `REWORK` 源态，则须在 §3.3 为 E4/E5/E5a/E9 各补一条 `REWORK` 起态的行，并让提案 §L135 与 PRD/UC-7 的两步豁免流一致。
  *验收*：脚本比对「E7 伴随动作提到的每个目标转移编号」× 「该编号行的当前状态集合」⊇「E7 的当前状态集合」，无空缺。

---

### A-P1-4　交付物 #9 `STATUS.md` 双向对账仍不平：基线上 12 份结论未登记，含本申请据以论证闭环的全部 7 份 `6e35a71` 轮报告

**证据**（`STATUS.md:4` 自己确立的治理规则：「**每轮申请复审前，STATUS 必须与 `reviews/` 目录全量对账**，不得以 STATUS 登记子集为闭环核验边界」）

```bash
python3 - <<'PY'
import subprocess,re,os
tree=[p for p in subprocess.run(['git','ls-tree','-r','--name-only','4027cce'],
      capture_output=True,text=True).stdout.split('\n')
      if p.startswith('docs/reviews/') and p.endswith('.md')]
res=[os.path.basename(p) for p in tree if 'review-result' in p or 'review-2.5' in p or 'REVIEW_METHODOLOGY' in p]
req=[os.path.basename(p) for p in tree if 'review-request' in p]
allf={os.path.basename(p) for p in tree}
st=subprocess.run(['git','show','4027cce:docs/reviews/STATUS.md'],capture_output=True,text=True).stdout
linked={os.path.basename(x) for x in set(re.findall(r'\(([^)]*\.md)\)',st))|set(re.findall(r'`([^`]*\.md)`',st))}
print(f"@4027cce  结论类={len(res)}  申请类={len(req)}")
u=[f for f in sorted(res) if f not in linked]
print(f"存在但未登记 = {len(u)}"); [print("   ",f) for f in u]
print(f"登记但文件不存在 = {len([f for f in linked if f.startswith('20') and f not in allf])}")
PY
```

输出：

```
@4027cce  结论类=119  申请类=23
存在但未登记 = 12
    2026-09-01-review-result-5583bdd-grok.md
    2026-09-01-review-result-caf3473-DesignSync-r2-qwen.md
    2026-09-01-review-result-caf3473-qwen.md
    2026-09-02-review-result-6e35a71-DesignSync-claude.md
    2026-09-02-review-result-6e35a71-DesignSync-grok.md
    2026-09-02-review-result-6e35a71-DesignSync-r2-qwen.md
    2026-09-02-review-result-6e35a71-UseCases-claude.md
    2026-09-02-review-result-6e35a71-UseCases-grok.md
    2026-09-02-review-result-6e35a71-codex.md
    2026-09-02-review-result-6e35a71-qwen.md
    REVIEW_METHODOLOGY_review_cc.md
    REVIEW_METHODOLOGY_review_glm.md
登记但文件不存在 = 0
```

另有三处计数互斥：

| 位置 | 数字 |
|---|---|
| `STATUS.md:6` 头部 | 报告 **115**、申请 **26** |
| `STATUS.md` 登记表标题 | 「**107** 份历史与当前评审报告 + **21** 份申请全量对账」 |
| 对账正文 | 仍为 **2026-09-01** 那次的记录（「存在但未登记 —— 4 份」） |
| 本机实测 @`4027cce` | 结论类 **119**、申请类 **23** |

**相比上轮恶化**：`6e35a71` 时未登记 3 份，本轮 12 份。且未登记的 10 份里有 7 份正是 `6e35a71` 轮的全部专家报告——本申请 §1「针对专家委员会对上一轮提交 `6e35a71` 提出的全部阻断项……已实施全量物理修复」所依据的那批文件，一份都没进登记表。轨 A 申请 §2 第 9 行仍称 STATUS「完整如实记录全量 115 份专家评审报告与 26 份评审申请」。

**最小闭环**：以 `git ls-files docs/reviews/` 为唯一源重算三处计数使之相等；补登 12 份；把上述对账脚本落进 `tests/` 或 CI。**这已是自 `2766c69` Codex P2-1 起连续第 5 轮未固化的同一项。**

---

## 四、轨 B（全量用例体系）P1：必须先解决（1 项）

### B-P1-1　UC-8 新引入的 `remote_name: null` 判据通不过 `macao_config` 契约，纯本地模式不可达；PRD §14.5 也没有该模式

**证据**

本轮 UC-8 按我上轮轨 B P1-4 的建议，给「远端不可达」加了确定性判据：

- `docs/usercases/UC8-merge-signoff.md:23`：「**远端共享模式**（`repository.remote_name` 配置非空，默认 `origin`）：……`git ls-remote --exit-code` ……**100% fail-closed 拦截**并触发 E4b」
- `docs/usercases/UC8-merge-signoff.md:24`：「**纯本地模式**（`repository.remote_name: null` **显式声明**）：跳过远端 `ls-remote`，仅强校验本地 `refs/macao/evidence/...` 引用存在性」
- `docs/usercases/UC8-merge-signoff.md:56` A3、`:17` P3（「或纯本地」）同源

判据本身是对的。问题是它**不可表达**：

```python
import json,yaml,jsonschema,copy
c=json.load(open('docs/schemas/macao_config.schema.json'))
print("project.repository:", json.dumps(c['properties']['project']['properties']['repository'],ensure_ascii=False))
base=yaml.safe_load(open('docs/schemas/fixtures/valid/macao_config.yaml'))
V=jsonschema.Draft7Validator(c)
print("control:", "PASS" if not list(V.iter_errors(base)) else "FAIL")
x=copy.deepcopy(base); x['project']['repository']['remote_name']=None
print("remote_name: null ->", [e.message for e in V.iter_errors(x)][:1] or "ACCEPTED")
y=copy.deepcopy(base); del y['project']['repository']['remote_name']
print("省略 remote_name  ->", [e.message for e in V.iter_errors(y)][:1] or "ACCEPTED")
```

```
project.repository: {"type": "object", "required": ["workspace_path", "remote_name"],
                     "properties": {"workspace_path": {...}, "remote_name": {"type": "string", "minLength": 1}, ...}}
control: PASS
remote_name: null -> ["None is not of type 'string'"]
省略 remote_name  -> ["'remote_name' is a required property"]
```

`remote_name` 既是**必填**又限定为 `minLength: 1` 的字符串。**没有任何一份能通过契约的 `macao.yaml` 可以选中纯本地模式**——UC-8 关卡 1 的第二条、备选流 A3、前置条件 P3 的「或纯本地」全是死分支。

同时权威侧完全没有这个模式：

```bash
sed -n '/^### 14.5/,/^## 第十五/p' docs/MACAO_PRD_v2.md | grep -c 'remote_name\|纯本地\|local'   # -> 0
```

PRD §14.5（合并流水线的权威定义）第 1 步只有无条件的 `ls-remote` 校验。UC-8 §6 验收标准 `:78` 第 2 条也只写了远端路径，**没有纯本地模式的 fixture**。

**为什么这是 P1**：它同时是「用例声明的分支在契约上不可触发」（我上轮 UC-P1-1 的同一类）与「用例引入了权威 PRD 没有的模式」（GUIDELINES §5）。实现者二选一：按契约做，则 UC-8 的本地模式永远进不去，无远端环境下任务卡死在关卡 1；按 UC-8 做，则要接受一份契约判为非法的配置。

**最小闭环**
1. `macao_config.schema.json` 的 `project.repository.remote_name` 改为 `{"type":["string","null"],"minLength":1}`（Draft-07 下 `minLength` 对 null 不生效）或从 `required` 移出并允许缺省；`review_context.schema.json` 的同名字段一并处理（现同为必填非空串）；
2. PRD §14.5 第 1 步补「远端共享 / 纯本地」两分支，与 UC-8 关卡 1 同措辞；
3. UC-8 §6 验收标准增一条纯本地 fixture 断言；
4. `fixtures/valid/` 增一份 `macao_config_local_only.yaml`。
   *验收*：该正例 fixture 通过契约，且 `ls-remote` 分支的反例仍被拒。

**来源**：本条与 grok `4027cce` 报告、Codex `4027cce` 报告 P1-4 **三方独立收敛**。

---

## 五、P2 / P3：登记（两轨合并）

| ID | 轨 | 级 | 问题 |
|---|---|---|---|
| **P2-1** | A | P2 | `aep_envelope.schema.json:64` 新增 `"$ref": "review_context.schema.json"`，相对 `$id` 解析为 `https://macao.dev/schemas/v2.5/review_context.schema.json`。用**无 store 的 stock `Draft7Validator`** 校验任何 `REVIEW_REQUEST` 信封会**抛 `RefResolutionError` 并发起对 `macao.dev` 的出站 DNS/HTTPS 请求**（本机：`Failed to resolve 'macao.dev'`），不是「校验失败」而是「异常」。仓库代码 `src/macao/core/schema.py:76` 预置了 store 所以运行期正常，但**契约库因此不再是自包含的**：申请 §3.3/§4.3 的「9/9 + 13/13」在没有那份私有 store 映射时复现不出来，而该映射只存在于 `src/`，`docs/schemas/README.md` 未记载。建议改用 `$defs` 内联或相对文件路径 `$ref`，并在 README 写明离线校验方法 |
| **P2-2** | A | P2 | AEP 的 **16 KiB 整信封字节预算**仍未进契约（D-7 与申请 §3 均声称「硬约束」）；per-type payload 只覆盖 **4/8** 类（A/B/E/H），C/D/F/G 的 payload 仍是任意 object；`protocol` 仍接受 `AEP/1.0`。**与 Codex P1-2、grok 收敛**，我判 P2：`docs/schemas/README.md:28` 明写「跨项业务规则由对应运行时模块保证」，字节预算确非 Draft-07 可表达 |
| **P2-3** | A | P2 | 提案两处仍写「**9 大** context 语义块」（`:458`、`:489`），与 PRD §5.2 / Schema `required`（实测 10 键）/ `schemas/README.md:26` / UC-4 的 **10 大**冲突。上轮 DS-P2-1 未闭环；本轮因 §2.4 Type B 的 `$ref` 而首次机器可检出（见 A-P1-1 附带发现） |
| **P2-4** | A | P2 | `schemas/README.md:26` 仍宣称 `review_context.schema.json`「禁止 base64 内联」，契约实际不拦：`code_changes.diff_policy` 是无枚举的 `{"type":"string"}`，置 `"inline_base64"` 并在 `diff_command` 放 base64 大块 → **ACCEPTED**。上轮 DS-P2-2 未闭环 |
| **P2-5** | A | P2 | PRD §14.2 `role_view` 表仍缺「override APPROVED 且待 FINAL → `SHOULD_DISPOSE`」行（`grep` 命中 0），与 `UC1-init-glm.md:146` 不一致。上轮 DS-P2-4 = grok DS-P2-2 = qwen P2-2，四轮未闭 |
| **P2-6** | B | P2 | `UC5-consensus-tally.md` 仍保留浮点「赞成加权占比 = Σ/有效权重」（2 处），与 D-6「严禁浮点数运算与静默四舍五入」抵触。诚实说明：我上轮穷举 $E_W\le5000$ 未找到数值分歧，故仍判 P2。**与 grok / qwen 历轮收敛** |
| **P2-7** | B | P2 | 悬空章节引用未修：`UC2-task-create.md` §11.4（PRD 第十一部分只有 11.1/11.2）×1、`UC4-review-dispatch.md` §12.5（第十二部分只有 12.1/12.2；输出自愈实为 §17.2）×3、`UC8-merge-signoff.md`「§14.5 三条件」×1（§14.5 无此三条件）。上轮 UC-P2-2 未闭环 |
| **P2-8** | B | P2 | D-9 明列四命令，`reconcile` 在 `docs/usercases/` 仍**零出现**。上轮采纳自 grok P2-3 / qwen P2-3，未闭环 |
| **P2-9** | B | P2 | `UC1-init-gemini.md` 仍与其余 10 份用例不同构（验收标准/后置条件/异常流/实现落点/设计自审五节全缺）。上轮 UC-P2-4 未闭环 |
| **P3-1** | B | P3 | `README.md` 仍写合并成功后产物「**提升至** evidence ref」，与 UC-8 关卡 6 的 Post-merge 封存措辞不一。上轮采纳自 grok P2-4 / qwen P2-4 |
| **P3-2** | B | P3 | `UC3-dev-checkpoint.md` 仍在同一文档内三重复用 `E1`–`E5`（前置条件行 5 处、异常流行 5 处、PRD §3.3 全局转移编号）。上轮 UC-P3-4，采纳自 Codex P2-1 |
| **P3-3** | A | P3 | 文档份数仍不可复现：申请称 `git ls-files "*.md"` 169 / `docs/` 175；本机 **179** / **180** / **193**（跟随软链）。0 控制字符的结论各方一致为真。建议申请改为写明命令与口径，而不是写一个数 |

---

## 六、GUIDELINES §6 反例库：11/11 可唯一推导（无回退）

前 4 项由五重门禁纯整数复算（脚本与上轮同，输出一致）：

```
S1 2人全弃权              -> DEADLOCK(席位法定人数 0<2)
S2 1超时+1批准            -> DEADLOCK(席位法定人数 1<2)
S3 1:1 僵局               -> DEADLOCK(阈值 aw=1 rw=1 EW=2 asz=1 rsz=1)
S4 3人 YES/NO/ABSTAIN     -> DEADLOCK(阈值 aw=1 rw=1 EW=2 asz=1 rsz=1)
S4b 3人 YES/NO/NO         -> REWORK_REQUIRED
```

| # | 场景 | 唯一推导来源 | 结果 |
|---|---|---|---|
| 1–4 | 全弃权 / 1超时+1批准 / 1:1 / 1:1:1 | 上表；`UC9:41`、`UC5:41` 决策表 | 唯一 |
| 5 | 崩溃重启重复投票 | `UC4:68` E5 幂等 | 唯一 |
| 6 | 同 reviewer 两份票 | `UC4:44` f4 + `:58` A5，审计 `REVIEW_DEDUP` | 唯一 |
| 7 | `.dev.yml` 缺字段但 `signal=EXPLICIT` | `UC3:53` d1 先于 d2；`dev_manifest` required **本轮已含 `checkpoint_ref`/`full_document`**（加固） | 唯一（fail-closed） |
| 8 | 第二轮 `.review.yml` 是否覆盖第一轮 | `PRD:876` 双匹配；`UC1-glm:152` STALE | 唯一（不覆盖） |
| 9 | 人工接管超时默认动作 | `PRD:1160` 总则 + `UC7:53` §2.f | 唯一（HOLD + 升级告警） |
| 10 | Git 冲突致 checkpoint 与工作区不一致 | `UC8:63` E2 `CHECKPOINT_DRIFT`；**本轮 `PRD:855` E4b 增列「或 Git conflict」，UC-7 §1 边界说明明确剥离** | 唯一（**本轮加固**） |
| 11 | `review_context` diff 载体不一致 | `PRD:1031` `diff_policy: generate_locally` | 正文唯一；**契约层仍不拦，见 P2-4** |

**11/11**，且第 10 项本轮由「可推导」升级为「有显式出边」。

### 连续漏审 / 复发模式登记（第 6 轮）

我在 `2da1bc2` 轮把「把回归检查固化为交付前门禁」列为编号闭环项，在 `6e35a71` 轮再次登记，本轮**第三次**登记，并且这一次有了直接后果：

> 本轮为闭合评审意见而收紧了 4 份 Schema，**没有任何一步回跑「PRD 示例 × 契约」**，于是一次性打破 5 处规范示例 + 仓库根配置（A-P1-1）；为闭合 UC-8 而引入 `remote_name: null`，**没有回跑「用例判据 × 配置契约」**，于是造出一个不可达分支（B-P1-1）。

模式已经从「每轮闭上一轮、同类再开一处」演进为「**修复动作本身是新缺陷的成因**」。§一 的示例×契约脚本、B-P1-1 的判据×契约检查、A-P1-4 的对账脚本三者合起来不足 60 行，建议本轮务必落进 CI。

---

## 七、与其他 Reviewer 的交叉核对（GUIDELINES §8）

同基线三份报告：**grok `NO_APPROVE`（P1×2）**、**Codex `REJECT`（P1×5）**、**本报告 `NO_APPROVE`（P1×5）**。三方独立，**无一方投赞成**——这是 `caf3473` 以来第一次全体一致不通过。

**三方独立收敛（1 项，阻断级）**

| 项 | 对应 |
|---|---|
| **B-P1-1** `remote_name: null` 通不过 `macao_config` 契约、PRD §14.5 无该模式 | = grok 结论段第 2 条 = Codex **P1-4**。三人从三条路径到达同一处 |

**与 grok 收敛（1 项，阻断级）**

| 项 | 对应 |
|---|---|
| **A-P1-2** D-6 两道反支配门禁在契约层仍可关闭 | = grok 结论段第 1 条（「本机复现可改变计票结果」）。grok 与我的反例一致 |

**与 Codex 收敛（2 项）**

| 我的项 | Codex | 状态 |
|---|---|---|
| **A-P1-1** PRD 规范示例 + 根配置通不过收紧后的契约 | **P1-1**「PRD 的正式产物/AEP 示例与刚收紧的 Schema 不一致」 | **独立收敛**。我另加了逐条 FAIL 原因与 §2.4 Type B 的 9 vs 10 块比对 |
| **P2-2** AEP 16 KiB / 8 类 payload | **P1-2** | **收敛**，我判 P2 他判 P1；分歧点：`schemas/README.md:28` 明写跨项规则归运行时，且字节预算 Draft-07 表达不了 |

**部分收敛、我给出不同切面的（1 项）**

| 我的项 | Codex | 差异 |
|---|---|---|
| **A-P1-3** E7 源态 `REWORK` 下 4/5 选项无可达边 + 提案 §L135 互斥 | **P1-5**「E7/E9 和提案的 REWORK 覆盖边仍给出互斥状态机」 | 同一处。Codex 侧重 E9 与提案；我补了完整的**可达性矩阵**（把 E7 的 5 个目标转移逐一对照其「当前状态」栏），把它量化成 3/5 无边 |

**我提出、三方中只有我给出证据的（1 项）**

| 我的项 | 依据 |
|---|---|
| **A-P1-4** STATUS 双向对账不平（12 份未登记，含全部 7 份 `6e35a71` 轮报告） | 对账脚本可复跑；`STATUS.md:4` 自己确立的治理规则要求「每轮申请复审前全量对账」，而对账正文仍停在 2026-09-01 |

**Codex 提出、我未列入定级依据的**

- Codex **P1-3**「AEP/1.1 与 `DISPOSITION_REQUIRED` 在实现层仍不可用，现有测试反而固化了旧协议」——我复核属实（`src/` 侧），但本轮申请定级为 **L1 DOC-ALIGNED**，实现层差距属 L2 判据，按 GUIDELINES §3.1 我把 CODE 标为不作定级依据。登记，不计入我的票。

**关于本轮的整体判断**：三方都确认了整改的实质性（grok 与 Codex 都在「已对齐」段落逐条肯定），也都确认了整改**不完整**。我与 grok 的两条阻断完全重合，我与 Codex 的两条阻断完全重合，四条合起来正好是「契约取值域」「PRD 示例同步」「E7 源态」「本地模式判据」四个面。没有一条是文字口味问题，全部可复跑。

---

## 八、建议闭环顺序与验收标准

1. **A-P1-1**（先做，因为它挡住其余验收）：修 5 处 PRD 示例 + 仓库根 `macao.yaml`；**同时**把 §一 的「PRD 示例 × 契约」脚本落进 CI。
   *验收*：脚本对 §2.1/2.2/2.3/2.5/5.2/§13 与 §2.4 八个信封全部输出 `PASS`；`validate_config(macao.yaml)` 返回 `(True, None)`。
2. **B-P1-1**：`remote_name` 放开 null（两份 Schema）+ PRD §14.5 补两分支 + UC-8 §6 增断言 + 新增 `fixtures/valid/macao_config_local_only.yaml`。
   *验收*：新正例通过；`ls-remote` 分支反例仍被拒。
3. **A-P1-2**：`minimum_winning_seats.minimum: 2`；`dictator_cap_enabled` 收 `const: true` 或删键；`min_effective_votes` 删键并清理三处引用。
   *验收*：两个新反例进 `fixtures/invalid/` 并被拒。
4. **A-P1-3**：E7 源态收敛为 `CONSENSUS_CHECK`（推荐）+ 删提案 §L135「直接推进至 MERGING」。
   *验收*：可达性矩阵脚本无空缺。
5. **A-P1-4**：重算 STATUS 三处计数、补登 12 份、对账脚本入 CI。
   *验收*：双向输出均为 0，三处计数相等。
6. **P2 批次**：`$ref` 改内联或相对路径（P2-1）；提案 9→10（P2-3）；`diff_policy` 收敛枚举或改 README 措辞（P2-4）；§14.2 补 role_view 行（P2-5）；UC-5 删浮点旁注（P2-6）；修 5 处悬空引用（P2-7）；补 `reconcile` 分册（P2-8）；UC-1-gemini 补五节（P2-9）。
7. **门禁固化（连续第 3 轮登记，本轮务必执行）**：把 §一、B-P1-1、A-P1-4 三段脚本合为一个交付前门禁。**不做这一步，下一轮大概率仍是「闭上一轮、同类再开一处」。**

---

## 附：机器票与结构化 issue 索引

- 轨 A（PRD 设计同步）：`vote`: **`NO_APPROVE`**　`opinion.status`: `CHANGES_REQUESTED`
- 轨 B（全量用例体系）：`vote`: **`NO_APPROVE`**　`opinion.status`: `CHANGES_REQUESTED`

| issue_id | 轨 | severity | disposition_class | 摘要 |
|---|---|---|---|---|
| `claude/A-P1-1` | A | critical | `BLOCKING` | 收紧 Schema 未同步正文：PRD §2.5 / §13 / §2.4 Type A、B、E 共 5 处规范示例通不过其自称契约；仓库根 `macao.yaml` 通不过 `validate_config()`。该缺陷类第 4 次复发 |
| `claude/A-P1-2` | A | critical | `BLOCKING` | D-6 两道反支配门禁契约层仍可关闭（`minimum_winning_seats:1`、`dictator_cap_enabled:false` 均被接受，反例可让单席位批准合并）；`min_effective_votes` 升级为必填孤儿键 |
| `claude/A-P1-3` | A | major | `BLOCKING` | PRD E7 源态含 `REWORK`，但 5 个闭合选项中 3 个从 `REWORK` 无可达边；提案 `:135` 另给「直接推进 MERGING」与 PRD/UC-7 的两步豁免流互斥 |
| `claude/A-P1-4` | A | major | `BLOCKING` | `STATUS.md` 双向对账不平：@`4027cce` 存在但未登记 12 份（含全部 7 份 `6e35a71` 轮报告）；三处计数互斥（115/107/实测 119） |
| `claude/B-P1-1` | B | critical | `BLOCKING` | UC-8 纯本地模式判据 `remote_name: null` 通不过 `macao_config` 契约（必填且 `minLength:1` 字符串），分支不可达；PRD §14.5 无该模式；UC-8 §6 无对应 fixture |
| `claude/A-P2-1` | A | major | `ADVISORY` | `aep_envelope.schema.json:64` 的 `$ref` 解析为网络 URL `https://macao.dev/...`，stock 校验器抛异常并发起出站请求；契约库不再自包含，申请的机验声明离线复现不出 |
| `claude/A-P2-2` | A | minor | `ADVISORY` | AEP 16 KiB 预算未入契约；per-type payload 仅覆盖 4/8 类；`protocol` 仍接受 `AEP/1.0` |
| `claude/A-P2-3` | A | minor | `ADVISORY` | 提案 `:458`/`:489` 「9 大 context 语义块」vs PRD/Schema/README 的 10（PRD §2.4 Type B 内嵌实例亦为 9 块，缺 `evidence`） |
| `claude/A-P2-4` | A | minor | `ADVISORY` | `schemas/README.md:26` 宣称禁 base64，契约实际接受 `diff_policy: inline_base64` + base64 载荷 |
| `claude/A-P2-5` | A | minor | `ADVISORY` | PRD §14.2 role_view 缺 override 后 `SHOULD_DISPOSE` 行（四轮未闭） |
| `claude/B-P2-6` | B | minor | `ADVISORY` | UC-5 §2.b 残留浮点「赞成加权占比」，与 D-6 禁浮点抵触（未能构造数值分歧） |
| `claude/B-P2-7` | B | minor | `ADVISORY` | 悬空引用：UC-2 §11.4、UC-4 §12.5×3、UC-8「§14.5 三条件」 |
| `claude/B-P2-8` | B | minor | `ADVISORY` | D-9 的 `reconcile` 在 `docs/usercases/` 零出现 |
| `claude/B-P2-9` | B | minor | `ADVISORY` | UC-1-gemini 与其余 10 份用例不同构，五个可验收小节全缺 |
| `claude/B-P3-1` | B | minor | `ADVISORY` | README 仍写「提升至 evidence ref」，与 UC-8 关卡 6 措辞不一 |
| `claude/B-P3-2` | B | minor | `ADVISORY` | UC-3 同文三重复用 E1–E5 标识 |
| `claude/A-P3-3` | A | minor | `ADVISORY` | 文档份数不可复现（申请 169/175；本机 179/180/193） |
