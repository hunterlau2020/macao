# PRD v2.5 设计同步轨 与 全量用例体系轨 独立评审结论（`a0123e8`）

- **评审日期**：2026-09-02
- **评审人**：claude
- **评审对象（两份申请，分轨判定）**：
  - 轨 A：[`2026-09-02-review-request-a0123e8-PRD-v2.5-Design-Sync.md`](2026-09-02-review-request-a0123e8-PRD-v2.5-Design-Sync.md)
  - 轨 B：[`2026-09-02-review-request-a0123e8-UseCases-v2.5-Alignment.md`](2026-09-02-review-request-a0123e8-UseCases-v2.5-Alignment.md)
  - 总入口 [`2026-09-02-review-request-a0123e8.md`](2026-09-02-review-request-a0123e8.md) 一并核验
- **申请声称基线**：`a0123e8`；**工作区 HEAD**：`3b60d3a`（差量 = 三份申请文件 + `STATUS.md` 头部计数；被审交付物正文与 `a0123e8` 逐字节一致）
- **本人前序票**：`caf3473`（NO_APPROVE P1×5）→ `6e35a71` 双轨（NO_APPROVE，A P1×5 / B P1×4）→ `4027cce` 双轨（NO_APPROVE，A P1×4 / B P1×1）
- **对齐基准**：`docs/MACAO_REVIEW_GUIDELINES.md` §2/§3/§5/§6/§8/§9；`docs/PRD_CHANGE_PROPOSAL_v2.5.md` §2 L34–L42（D-1～D-9）；`docs/usercases/PRODUCT-FACTS.md` F-1～F-22

## 结论

- **轨 B（全量用例体系）：`YES_APPROVE`** —— **授予 L1 DOC-ALIGNED / PG-0**。P0×0，**P1×0**，P2×6，P3×2。
- **轨 A（PRD 设计同步）：`NO_APPROVE`** —— 不授予 L1 DOC-ALIGNED / PG-0。P0×0，**P1×2**，P2×8，P3×3。

**这是我在本工程六轮评审中第一次投出授予票。** 需要说明为什么：我在 `4027cce` 轮提的 5 条 P1，本轮 **4 条完全闭环、1 条部分闭环**，且闭环全部经我本机机验，不是采信自述——

| 我上轮的 P1 | 本轮判定 |
|---|---|
| A-P1-1 PRD 5 处规范示例 + 仓库根 `macao.yaml` 通不过自家契约 | **完全闭环**。§2.1/2.2/2.3/2.5/5.2/§13 与 §2.4 全部 8 个 AEP 信封，**14/14 PASS**；根 `macao.yaml` PASS |
| A-P1-2 D-6 两道反支配门禁契约层可关 | **部分闭环**。我上轮提交的两个反例现被拒；但**独裁帽从未对实际权重生效**——见 §0.1b 的自我更正与 §三 A-P1-2 |
| A-P1-3 E7 源态 `REWORK` 下 3/5 选项无可达边 | **部分闭环**。PRD `:881` 与提案 `:135` 已改对；**提案 `:226` 与变更清单 `:85` 仍写旧值**——本轮唯一 P1 |
| A-P1-4 `STATUS.md` 双向对账不平 | **完全闭环**。@`a0123e8` 双向均为 **0/0/0**，计数 124/26 与实测相符 |
| B-P1-1 UC-8 `remote_name: null` 不可表达 | **完全闭环**。两份契约放开 null、新增 `macao_config_local_only.yaml` 正例、PRD §14.5 补两分支 |

**轨 B 已无任何 P1。** 用例体系 13 份文档与 PRD、契约、D-1～D-9 之间我未能找出机器可证的不一致；§6 反例库 11/11 可唯一推导；3 处内嵌围栏全部过契约。按 GUIDELINES §2.1 的 L1 判据（「设计文档之间、与权威基准之间一致；所有 YAML/JSON 示例是合法可解析格式」），轨 B 达标。我连续三轮对该轨投反对票，本轮证据支持授予，就应当授予——按 GUIDELINES §8「真理不等于投票」，前票不构成后轮的立场惯性。

**轨 A 仍差两条**：一是 E7 的源态在四处权威位置里改对了两处；二是我在初稿中把 A-P1-2 判成「完全闭环」，经 Codex 同基线报告提示后复验，该判定**不成立**（详见 §0.1b）——`dictator_cap_enabled: {"const": true}` 只锁死了「开关必须为真」，从未校验权重本身是否满足 $\forall i, 3w_i < 2W$。

关于 E7：`docs/v2.5_CODE_CHANGE_INVENTORY.md:85`（交付物 #4，Phase 1 的 `orchestrator.py` 施工图）仍指示「从 HOLD（`CONSENSUS_CHECK` **或 `REWORK`**）接收管理员裁定」，与 PRD `:881` 直接冲突，而 PRD `:889` 明文「除本表所列来源外，任何实现不得引入其他状态转移路径」。这是两行的修改量，但它落在 L1 的定义域正中。

**同基线暂无其他 reviewer 出具报告**（`ls docs/reviews/*result-a0123e8*` 无命中），本报告为本轮首份。

---

## 0. Reviewer 自审记录（GUIDELINES §9）

### 0.1 本轮我先怀疑、经隔离测试后**撤回**的三条

1. **`min_effective_votes` 并未真正删除（全库仍有 7 处）** ——
   逐处核对：7 处**全部**在 `src/` 与 `tests/`，`docs/` 与 `docs/schemas/` 零残留。且 `src/macao/core/config.py:48` 现为 `policy["min_effective_votes"] = policy.get("seat_quorum_required", derived_quorum)`——它已从「第二个事实源」降级为**由 `seat_quorum_required` 派生的内部别名**，正是我上轮建议的处置方向之一。**假设撤回**（残留的契约未禁问题另记 P2-7，性质不同）。
2. **16 KiB 字节预算完全没有落点** ——
   我先只查了契约层（确实不拦，见 P2-2）。再查 `src/macao/msg/envelope.py`：`MAX_MESSAGE_BYTES = 16384`、`validate_budget()` 实现整信封与逐字段字节校验，且**已接入** `create()`（`:79`，失败即 `raise`）与 `parse()`（`:90`）两条路径，不是死代码。Draft-07 本就无法表达整文档字节长度，落到运行时是**正确分工**。**假设撤回**，P2-2 只保留「反例 fixture 名不副实」这一维。
3. **`STATUS.md` 登记表标题 26 与实际 29 不符，对账未真正闭环** ——
   分别在 `a0123e8`（被审基线）与 `3b60d3a`（HEAD）复跑：**@`a0123e8` 双向 0/0/0，结论类 124 / 申请类 26，标题与实测完全一致**。29 是 HEAD 提交新增三份申请文件后才出现的差，且 HEAD 头部已同步为 29、仅表标题未跟。**被审基线上该项是干净的，假设撤回**，仅以 P3 记 HEAD 侧的标题滞后。

### 0.1b 本轮我判错、经同行提示后复验并**推翻自己**的一条

初稿中我把 A-P1-2 判为「完全闭环」，依据是这两个探针现在都被拒：`minimum_winning_seats=1` → `1 is less than the minimum of 2`，`dictator_cap_enabled=false` → `True was expected`。

Codex 同基线报告 P1-1 指出这只是「布尔开关及一个局部下限，并没有验证 PRD 的五重公式」。我本机复验，**Codex 是对的**：

```
### 权重实际违反独裁帽（dictator_cap_enabled 仍为 true）
   weights=[5,1,1] W=7  独裁帽判据 3*5=15 < 2W=14 ? -> False（违反）
   契约判定 -> **ACCEPTED（独裁帽未对实际权重生效）**
   validate_config(权重[5,1,1]) -> (True, None)      ← 产品自身校验器同样放行
### quorum 声明值与公式不符
   N=3 W=3  公式要求 seat>=⌈2N/3⌉=2  weight>=⌈2W/3⌉=2
   声明 seat=1 / weight=1 -> **ACCEPTED（契约不校验公式）**
```

**我的错误在于只测了我自己上一轮写下的两个探针，没有回到 D-6 的公式本身重新出题。** 这正是我在前几轮反复指摘他人的「枚举封闭 ≠ 语义成立」——契约把 `dictator_cap_enabled` 钉成 `const: true`，读起来像「独裁帽已物理锁死」，实际锁死的只是**声明这面旗子是开着的**。登记为本轮漏审，已作为 §三 A-P1-2 独立成条，并把轨 A 的 P1 计数由 1 更正为 2。

### 0.2 一条「名义拒绝 ≠ 拒对了」的复现

`docs/schemas/fixtures/invalid/aep_payload_oversized.json` 依文件名应当是字节预算的反例，两份申请也把它计入「16 份反例 16/16 准确拦截」。逐维隔离后（见 P2-2）：该 fixture 的 `specification_summary` 仅 **44 字符**、整信封仅 **298 字节**，**没有任何一维超标**；它被拒的唯一原因是 `acceptance_criteria: []` 违反 `minItems: 1`。把这一个字段补成合法后，同一个信封**被接受**。这正是我在第 3 轮登记过的「负例因错误原因通过」模式，本轮在对方的 fixture 上复现。

### 0.3 强制自检 5 项

| # | 项 | 本轮 |
|---|---|---|
| 1 | 字段声明位置 vs 实际读取位置 | 契约与 PRD 正文本轮首次全对齐；**E7 源态在 4 处声明位置中 2 处未跟**（P1-1） |
| 2 | 「已完成 / 100%」是否等同证据 | 申请 §3/§4 五组机验逐条重放：4 组 VERIFIED，md 份数 CONTRADICTED（P3-3）；「16/16 准确拦截」名义成立但其中 1 份名不副实（P2-2） |
| 3 | 确定性语言是否标注 | 「被接受 / 被拒 / 未编码」均附实例与运行输出 |
| 4 | 代码块可执行性 | 本报告全部脚本原样贴出并已实跑 |
| 5 | 每条 P1/P2 是否附路径行号 | 是 |

### 0.4 证据类型适用性（GUIDELINES §3.1）

本轮为 **DOC + SPEC**。`src/` 仅两处作为**佐证**：`msg/envelope.py` 的字节预算实现（用于**撤回**我的一条拟议 P1，见 §0.1-2）、`workflow/orchestrator.py` 的 HOLD 语义（用于判定 E7 分裂中哪一方是对的）。**92/92 不构成 L2 证据**：其覆盖的仍是 v2.3.1 引擎主体，v2.5 计票、E5a、`admin_override` 命令路径在变更清单中仍标待实施。

---

## 一、申请 §3 / §4 自动化结论：独立重放

| 申请声明 | 本机结果 | 判定 |
|---|---|---|
| PRD 全量代码块 Draft-07 校验 100% PASS | 我用**自己的**提取器复跑（不跑对方的 `tests/test_prd_snippets_schema.py`）：§2.1/2.2/2.3/2.5/5.2/§13 六处 + §2.4 八个 AEP 信封，**14/14 PASS** | **VERIFIED** |
| 188 份 Markdown、0 控制字符 | **0 控制字符**（按字节扫 `0x09/0x0b/0x0c/0x0d`，199 份全扫）；份数复现不出 188：`git ls-tree -r a0123e8` = **184**，`git ls-files` = 187，`find docs` = 187，`find -L docs` = 200 | 结论 **VERIFIED**；份数 **CONTRADICTED**（P3-3） |
| 正例 10/10、反例 16/16 FAIL-CLOSED | 10/10 + 16/16，**逐条打印拒绝原因**；15 份拒因与名义一致，**1 份不一致**（P2-2） | **PARTIALLY_VERIFIED** |
| `docs/schemas/` 与 `src/macao/schemas/` 0 diff | 8 份契约 `cmp` 全 SAME；**fixtures 目录 `diff -rq` 亦无差异** | **VERIFIED** |
| 92/92 OK；`compileall` 0 Errors | `Ran 92 tests in 39.031s ... OK`；退出 0 | **VERIFIED**（与 L1 无关） |
| 用例三处示例过契约 | 我扩到**全部 13 份用例 × 全部 8 份契约**交叉验证：共 3 处围栏，全部 PASS，申请点名的三份即全集 | **VERIFIED**，申请覆盖完整 |

**核心复跑脚本**（本轮最重要的正面结论来源）：

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
for lang,f in re.findall(r'^```(json)\n(.*?)^```', sect(r'^### 2\.4 ',r'^### 2\.5 '), re.M|re.S):
    o=json.loads(f)
    if not isinstance(o,dict) or 'type' not in o: continue
    errs=list(V('aep_envelope').iter_errors(o))
    print(f"PRD §2.4 {o['type']:24s} -> aep_envelope {'PASS' if not errs else 'FAIL('+str(len(errs))+')'}")
o=yaml.safe_load(open('macao.yaml'))
print("仓库根 macao.yaml ->", "PASS" if not list(V('macao_config').iter_errors(o)) else "FAIL")
PY
```

输出：**14 行全 PASS + 根 `macao.yaml` PASS**。这条「权威文档的规范示例通不过自己指定的契约」的缺陷链自 `0bc6247` P0-2 起复发四次（P0-2 → N-6 → M-1 → A-P1-1），本轮是**第二次全部成立，也是第一次在契约被大幅收紧之后仍全部成立**。

---

## 二、本人 `4027cce` 轮 5 条 P1 闭环核验（逐条机验）

### A-P1-1 —— **完全闭环** ✓

见 §一 的 14/14 + 根配置 PASS。上轮 5 处 FAIL（§2.5 缺 `issues_index_sha256`、§13 缺 `version` 与 `policy.min_effective_votes`、Type A 缺两字段、Type B 内嵌 context FAIL(8)、Type E 缺两字段）与根 `macao.yaml` 的 `(False, "'version' is a required property")` 全部消失。

附带核对：§2.4 Type B 内嵌的 `review_context` 现为 **10 个顶层块**（上轮 9 个，缺 `evidence`），与 §5.2「唯一权威完整模型」一致；差异只剩可选的 `required_blocks`。我上轮的 A-P2-3（提案两处写「9 大」）亦已改为「10 大」（`grep -c '9 大'` = **0**）。

### A-P1-2 —— **部分闭环**，见 §三 A-P1-2

```
policy.required = ['consensus_rule','dictator_cap_enabled','minimum_winning_seats','seat_quorum_required','weight_quorum_required']
  minimum_winning_seats = {"type":"integer","minimum":2}
  dictator_cap_enabled  = {"type":"boolean","const":true}
  min_effective_votes   = None（已删）
vote_result.policy_snapshot.minimum_winning_seats = {"type":"integer","minimum":2}

control (valid fixture): PASS
  policy.minimum_winning_seats=1     -> REJECTED: 1 is less than the minimum of 2
  policy.dictator_cap_enabled=False  -> REJECTED: True was expected
```

我在 `6e35a71`/`4027cce` 两轮给出的判定改变反例（权重 `[5,2,1,1]`，`YES(5)/ABSTAIN(2)/NO(1)/NO(1)`，`mws=1` 时单席位 APPROVED）**现已在契约层被物理阻断**，且新增了两份对应反例 fixture（`macao_config_minimum_seats_one.yaml`、`macao_config_dictator_cap_false.yaml`），拒因与名义一致。**这一半是真闭环。**

**但另一半不是**：`const: true` 锁的是旗子，不是权重。D-6 gate 1 对实际权重的约束、以及 gate 2/3 的两个 quorum 公式，均未进入任何机器校验。详见 §0.1b 与 §三 A-P1-2。

### A-P1-3 —— **部分闭环**，见 §三 A-P1-1

PRD `:881` 已收敛为 `HOLD`（`CONSENSUS_CHECK`）；提案 `:135` 的「通过 E7 转移**直接推进至 `MERGING`**」已重写为两步豁免流（`grep -c '直接推进'` = **0**）。但提案 `:226` 与变更清单 `:85` 未跟。

### A-P1-4 —— **完全闭环** ✓

```
@a0123e8: 结论类=124 申请类=26 | 未登记(结论)=0 未登记(申请)=0 幽灵=0
     table title: Review Registry - 124 份结论类文件 + 26 份申请全量对账)
```

上轮 12 份未登记（含全部 7 份 `6e35a71` 轮报告）已全部补入，三处互斥计数已统一。

### B-P1-1 —— **完全闭环** ✓

```
macao_config  project.repository.remote_name = {"type":["string","null"]}
review_context repository.remote_name        = {"type":["string","null"]}
remote_name: null -> ACCEPTED
fixtures/valid/macao_config_local_only.yaml -> PASS | remote_name = None
```

`docs/MACAO_PRD_v2.md` §14.5 第 1 步现分「远端共享模式（`remote_name` 非空 → `ls-remote --exit-code`，fail-closed 触发 E4b）」与「纯本地模式（`remote_name: null` → 校验本地 evidence ref 存在性与哈希）」两分支，与 UC-8 关卡 1、A3、P3 措辞一致。**我上轮给出的四项最小闭环里，前三项全部落实**（第 4 项见 P2-5）。

---

## 三、轨 A：P1（2 项）

### A-P1-1　E7 源态在四处权威位置只改对两处，变更清单仍指示实现被 PRD 明文禁止的转移路径

**证据**

| 位置 | E7 源态 | 状态 |
|---|---|---|
| `docs/MACAO_PRD_v2.md:881`（§3.3 统一状态转移表，**权威**） | `HOLD`（`CONSENSUS_CHECK`） | ✅ 本轮改对 |
| `docs/PRD_CHANGE_PROPOSAL_v2.5.md:135`（§4.2 覆盖场景 3） | 已重写为两步豁免流，不再提源态 | ✅ 本轮改对 |
| `docs/PRD_CHANGE_PROPOSAL_v2.5.md:226`（**§4.5 状态转移表修订**） | `HOLD`（`CONSENSUS_CHECK` **或 `REWORK`**） | ❌ **未改** |
| `docs/v2.5_CODE_CHANGE_INVENTORY.md:85`（交付物 #4，E7 Override 守卫） | 「从 HOLD（`CONSENSUS_CHECK` **或 `REWORK`**）接收管理员裁定」 | ❌ **未改** |

`docs/MACAO_PRD_v2.md:889` 明文：

> - 除本表所列来源外，任何实现不得引入其他状态转移路径。

代码侧站在 PRD 一边：`src/macao/workflow/orchestrator.py:483-484` 的两条 HOLD 语义注释均为 `HOLDS in CONSENSUS_CHECK`（DEADLOCK 与 `MAX_REWORK_ROUNDS_REACHED` 都停在 `CONSENSUS_CHECK`）。UC-7 亦已站在 PRD 一边（§1 的 P1–P4 四个触发全部进入 `CONSENSUS_CHECK`）。**落单的是提案 §4.5 与变更清单。**

**为什么这是 P1 而不是文字瑕疵**

- 申请 §1.3 的原文是「E7 源态精准固化为 `HOLD (CONSENSUS_CHECK)`：PRD §3.3 状态机表与提案**彻底清理**……」。提案并未彻底清理——`:226` 是提案自己的状态转移表，是同一份文件里比 `:135` 更正式的规范位置。
- `docs/v2.5_CODE_CHANGE_INVENTORY.md` 是 Phase 1 重构 `orchestrator.py` 的施工图。按 `:85` 施工，会实现一条 PRD `:889` 明文禁止的转移路径；而现有代码本来是对的，等于**照施工图改会把已正确的行为改错**。这与我在 `6e35a71` 轮 A-P1-3 指出的模式相同（施工图比权威更松），只是方向反了过来。
- L1 的判据（GUIDELINES §2.1）就是「设计文档之间、与权威基准之间一致」。PRD 的转移表与提案的转移表对同一条边给出不同源态，正落在这句话里。

**最小闭环**（两行）
1. `docs/PRD_CHANGE_PROPOSAL_v2.5.md:226`：`HOLD`（`CONSENSUS_CHECK` 或 `REWORK`）→ `HOLD`（`CONSENSUS_CHECK`）；
2. `docs/v2.5_CODE_CHANGE_INVENTORY.md:85` 第 6 项：同样删去「或 `REWORK`」。

*验收*：`grep -rn 'CONSENSUS_CHECK` 或 `REWORK' docs/ --include='*.md' | grep -v '/reviews/'` 零命中；并把「E7 伴随动作提到的每个目标转移编号 × 该编号行的当前状态集合 ⊇ E7 的当前状态集合」写成脚本纳入门禁。

---

### A-P1-2　D-6 的独裁帽与两个 quorum 公式从未成为机器约束；`const: true` 锁死的是旗子，不是权重

**证据**

`docs/PRD_CHANGE_PROPOSAL_v2.5.md:410` 与 PRD §2.3 把 D-6 gate 1 定为无条件硬边界：「配置期独裁帽：$\forall i, 3 \times w_i < 2 \times W$（**不满足则拒绝启动**）」；gate 2/3 为 $E_N \ge \lceil 2N/3 \rceil$、$E_W \ge \lceil 2W/3 \rceil$。

本轮契约新增的是：

```json
"dictator_cap_enabled": { "type": "boolean", "const": true },
"minimum_winning_seats": { "type": "integer", "minimum": 2 },
"seat_quorum_required":  { "type": "integer", "minimum": 1 },
"weight_quorum_required":{ "type": "integer", "minimum": 1 }
```

`const: true` 断言的是**这个布尔字段必须写 true**，它不检查任何权重。实测：

```python
import json,yaml,jsonschema,copy
c=json.load(open('docs/schemas/macao_config.schema.json'))
V=jsonschema.Draft7Validator(c)
base=yaml.safe_load(open('docs/schemas/fixtures/valid/macao_config.yaml'))
x=copy.deepcopy(base)
for r,w in zip(x['team']['reviewers'],[5,1,1]): r['vote_weight']=w   # W=7, 3*5=15 >= 2*7=14 → 违反独裁帽
print("weights=[5,1,1] ->", "ACCEPTED" if not list(V.iter_errors(x)) else "REJECTED")
y=copy.deepcopy(base)                                                 # N=3, W=3 → 公式要求 2 / 2
y['policy']['seat_quorum_required']=1; y['policy']['weight_quorum_required']=1
print("seat=1 weight=1 ->", "ACCEPTED" if not list(V.iter_errors(y)) else "REJECTED")
```

```
weights=[5,1,1] -> ACCEPTED
seat=1 weight=1 -> ACCEPTED
```

产品自身的校验器同样放行：`validate_config(权重[5,1,1])` 返回 `(True, None)`。

**代码侧同样没有兜住**：`src/macao/core/config.py:39-48` 的 `ConfigManager.load()` **只**把 `seat_quorum_required` 上调到 `⌈2N/3⌉`，既不校验独裁帽，也不校验或推导 `weight_quorum_required`。全库对 `weight_quorum_required` 的唯一计算在 `src/macao/consensus/vote.py:180`，写作 `math.ceil(2 * configured_reviewers / 3)`——分母用的是**席位数 N**，而 D-6 gate 3 要求的是**总权重 W**（`⌈2W/3⌉`）；权重不全为 1 时二者不等。（该点属 `src/`，仅作佐证，不计入 L1 定级。）

**为什么这是 P1**

- 申请 §1.2 的标题原文是「**D-6 反支配门禁 Schema 物理锁死**」。物理锁死的只有「旗子必须是 true」和「胜方席位下限 2」两项；D-6 五重门禁里的 gate 1、gate 2、gate 3 都不在契约里，也不在 Loader 里。
- 提案 `:410` 用的词是「**不满足则拒绝启动**」。现在一份权重 `[5,1,1]` 的配置可以顺利启动，而它正是 D-6 要禁的支配型配置。
- 这与我上一轮 A-P1-2 是**同一个 D-6 缺口的不同侧面**：上轮是「开关可以关掉」，本轮是「开关关不掉但从来没接线」。上轮的两个探针被堵住了，缺口本身没有。

**诚实边界**：`minimum_winning_seats >= 2` 已强制，所以我在前两轮构造的「单席位批准合并」路径确已被阻断，本条**不再**附带那个后果。本条的危害是 D-6 gate 1/2/3 作为「配置期拒启」门禁在机器层完全缺席——是 fail-open，不是已被证实的判定翻转。

**最小闭环**
1. Draft-07 表达不了跨项求和，故 gate 1/2/3 应落在 `ConfigManager.load()`：加载时计算 $W=\sum w_i$，逐一校验 $3w_i < 2W$，并把 `seat_quorum_required` / `weight_quorum_required` 分别强制为 $\lceil 2N/3 \rceil$ / $\lceil 2W/3 \rceil$（低于即上调或直接拒启）；
2. 修正 `vote.py:180` 的 `weight_quorum_required` 分母为总权重 $W$；
3. `docs/schemas/README.md` 写明「gate 1/2/3 由 Config Loader 保证，契约不校验」，避免申请再把 `const: true` 表述为「物理锁死」；
4. 新增反例：`macao_config_dominant_weight.yaml`（权重 `[5,1,1]`）与 `macao_config_quorum_below_formula.yaml`，进 Loader 层测试而非 Schema fixture。
   *验收*：两个反例被 `ConfigManager.load()` 拒绝并打印拒因；`weight_quorum_required` 的推导对权重不全为 1 的配置给出 $\lceil 2W/3 \rceil$。

**来源**：本条由 Codex `a0123e8` 报告 P1-1 提出，我本机复现后确认，并据此**推翻了自己初稿中「A-P1-2 完全闭环」的判定**（见 §0.1b）。

---

## 四、轨 A / 轨 B：P2（登记，Phase 1 前处理）

| ID | 轨 | 问题 |
|---|---|---|
| **P2-1** | A | **`aep_envelope.schema.json:72` 的 `$ref` 仍解析为网络 URL**。`"review_context": { "$ref": "review_context.schema.json" }` 相对 `$id`（`https://macao.dev/schemas/v2.5/aep_envelope.schema.json`）解析为 `https://macao.dev/schemas/v2.5/review_context.schema.json`。无 store 的 stock `Draft7Validator` 校验任一 `REVIEW_REQUEST` 信封会**抛 `RefResolutionError` 并发起对 `macao.dev` 的出站请求**（本机：`Failed to resolve 'macao.dev'`）。`src/macao/core/schema.py` 预置 store 故运行期正常，但**契约库仍不自包含**：申请 §3.3 的「10/10 + 16/16」在仓库外复现不出，而该 store 映射未见于 `docs/schemas/README.md`。上轮 A-P2-1 未闭环。建议改 `$defs` 内联或相对文件路径 |
| **P2-2** | A | **`aep_payload_oversized.json` 名不副实，且它是申请「16 KiB 预算」声明的唯一反例**。见 §0.2 与下方隔离输出。**16 KiB 整信封预算在契约层确实不拦**（80,456 字节信封被 ACCEPTED），但这是 Draft-07 的固有限制且 `msg/envelope.py:30/79/90` 已在运行时实现并接入，属正确分工——所以本条只针对 fixture 与申请措辞：一个未超标的样本不能作为预算门禁的证据 |
| **P2-3** | A | **`vote_result_ref` 加为 property 但未进 `required`**。`review_disposition.schema.json` 的 `required` 为 `[version, task_id, checkpoint_ref, review_round, executor, disposition_status, dispositions, full_document, issues_index_sha256]`——不含 `vote_result_ref`；`fixtures/valid/disposition.yml` 也不含该字段；删除该字段的实例被 **ACCEPTED**。而提案 `:193` 强制规则 6 明文「disposition **必须**反向引用冻结的 vote result 和 `issues_index` 哈希」。`issues_index_sha256` 这一半已必填，vote result 引用这一半未编码 |
| **P2-4** | A | **「8 类封闭 Payload」的「封闭」不成立**。`allOf` 现有 8 个分支覆盖全部 8 类（上轮仅 4 类，**实质进步**），但每个分支的 payload 均未设 `additionalProperties: false`，基础 `payload` 亦仅 `{"type":"object","minProperties":1}`——任意额外字段可通过。另 `protocol` 仍接受 `AEP/1.0`，而 `AEPEnvelope.PROTOCOL` 已升为 `AEP/1.1` |
| **P2-5** | B | **UC-8 §6 验收标准无纯本地模式断言**。`UC8-merge-signoff.md:78` 第 2 条仍只写「未推送或 `ls-remote` 失败时 fail-closed」，六条验收标准中没有一条覆盖本轮新增的纯本地分支。这是我上轮 B-P1-1 四项最小闭环里**唯一未落实的一项**。轨 B 申请诉求是把用例批准为「测试验收的官方操作基准」，新增分支应当同时新增断言 |
| **P2-6** | A | `schemas/README.md:26` 仍宣称 `review_context.schema.json`「禁止 base64 内联」，契约实际不拦：`code_changes.diff_policy` 仍是无枚举的 `{"type":"string"}`，置 `"inline_base64"` 并在 `diff_command` 放 base64 大块 → **ACCEPTED**。上轮 A-P2-4 未闭环 |
| **P2-7** | A | `macao_config.schema.json` 的 `policy` 与根级均未设 `additionalProperties: false`：把已删除的 `min_effective_votes` 塞回 `policy` → **ACCEPTED**，而 `src/macao/workflow/orchestrator.py:122` 仍会读取 `raw_config.get("min_effective_votes", ...)`。删键做得对，但没有关门 |
| **P2-8** | B | 用例中 5 处指向 PRD 不存在的小节：`UC2-task-create.md:6` **§11.4**（第十一部分只有 11.1/11.2）、`UC4-review-dispatch.md:6/32/57` **§12.5**（第十二部分只有 12.1/12.2；输出自愈实为 §17.2）、`UC8-merge-signoff.md:27`「§14.5 **三条件**」（§14.5 无此三条件）。`UC4:57` 那一处是备选流 A4 的行为定义，指向空锚点等于该分支无规范来源。已连续四轮未闭 |
| **P2-9** | B | `UC5-consensus-tally.md:29` 仍保留浮点「赞成加权占比 = Σ(approve 权重) / 有效权重」（2 处），与 D-6「严禁浮点数运算与静默四舍五入」抵触。诚实说明：我在 `6e35a71` 轮穷举 $E_W \le 5000$、约 1.25×10⁷ 组，未找到与纯整数门禁的数值分歧，故一直判 P2 而非 P1 |
| **P2-10** | B | D-9 明列 `init / doctor / reconcile / adopt` 四命令，`reconcile` 在 `docs/usercases/` 仍**零出现**（`grep -rl reconcile docs/usercases/` = 0）。采纳自 grok/qwen 历轮，未闭环 |
| **P2-11** | B | `UC1-init-gemini.md` 仍与其余 10 份用例不同构：验收标准 / 后置条件 / 异常流 / 实现落点 / 设计自审**五节全缺**（其余 10 份均为 1/1/1）。UC-1 由 `UC1-init-glm.md` 兜底承载完整结构，故不阻断 |

**P2-2 的隔离输出**（复现脚本见 §六）：

```
### 该 fixture 的实际尺寸
  specification_summary 长度 = 44 字符（maxLength=2048）
  整信封字节数 = 298 字节（声称预算 16384）
  拒绝原因 = ['[] is too short']
### 隔离：把 acceptance_criteria 补成合法，只留「超长」这一维
  errors = **ACCEPTED**
### 真正超 2048 的 specification_summary（3000 字符）
  -> REJECTED（per-field maxLength 有效 ✓）
### 真正超 16 KiB 的整信封（80,456 字节，每字段均 <=2048 合规）
  -> **ACCEPTED（契约层不拦；运行时 envelope.py 拦）**
```

---

## 五、P3：可延期（3 项）

| ID | 轨 | 问题 |
|---|---|---|
| **P3-1** | A | PRD §14.2 `role_view` 表仍缺「override APPROVED 且待 FINAL → `SHOULD_DISPOSE`」行（`CONSENSUS_CHECK` 相关仅 3 行），与 `UC1-init-glm.md:146` 不一致。两者语义不冲突（都投影 `SHOULD_DISPOSE`），方向是 PRD 补齐。已连续五轮登记 |
| **P3-2** | A | `STATUS.md` 登记表标题在 HEAD `3b60d3a` 上滞后：头部已更新为申请 **29** 份，表标题仍写 **26**。**被审基线 `a0123e8` 上二者一致（26/26），是 HEAD 提交新增三份申请后产生的差**，故仅记 P3。另申请 §2 第 8 行称 STATUS 记录「120 份结论报告」，实为 **124**（120 是 `review-result-*` 子集，另有 2 份 `review-2.5-*` 与 2 份 `REVIEW_METHODOLOGY_*`） |
| **P3-3** | A | 文档份数仍不可复现：申请 §3.2 称 188 份；本机 `git ls-tree -r a0123e8` = **184**、`git ls-files` = 187、`find docs` = 187、`find -L docs`（跟随 `docs/usecases` 软链）= 200。四份口径无一相符。「0 控制字符」结论复现为真。建议申请写明命令与口径而非写一个数——此项已连续四轮出现 |

---

## 六、GUIDELINES §6 反例库：11/11 可唯一推导（无回退）

前 4 项由五重门禁纯整数复算：

```python
import math
def tally(w,v,minwin=2):
    N=len(w);W=sum(w)
    if any(3*x>=2*W for x in w): return "CONFIG_REJECT"
    eff=[(a,b) for a,b in zip(w,v) if b!='ABSTAIN']
    EN=len(eff);EW=sum(a for a,_ in eff)
    if EN<math.ceil(2*N/3): return f"DEADLOCK(席位 {EN}<{math.ceil(2*N/3)})"
    if EW<math.ceil(2*W/3): return f"DEADLOCK(权重 {EW}<{math.ceil(2*W/3)})"
    aw=sum(a for a,b in eff if b=='YES');asz=sum(1 for a,b in eff if b=='YES')
    rw=sum(a for a,b in eff if b=='NO');rsz=sum(1 for a,b in eff if b=='NO')
    if 3*aw>=2*EW and asz>=minwin: return "APPROVED"
    if 3*rw>=2*EW and rsz>=minwin: return "REWORK_REQUIRED"
    return f"DEADLOCK(阈值 aw={aw} rw={rw} EW={EW})"
for n,w,v in [("S1 全弃权",[1,1],['ABSTAIN','ABSTAIN']),("S2 1超时+1批准",[1,1],['ABSTAIN','YES']),
              ("S3 1:1",[1,1],['YES','NO']),("S4 3人YES/NO/ABSTAIN",[1,1,1],['YES','NO','ABSTAIN']),
              ("S4b 3人YES/NO/NO",[1,1,1],['YES','NO','NO'])]:
    print(f"  {n:22s} -> {tally(w,v)}")
```

```
  S1 全弃权                 -> DEADLOCK(席位 0<2)
  S2 1超时+1批准             -> DEADLOCK(席位 1<2)
  S3 1:1                 -> DEADLOCK(阈值 aw=1 rw=1 EW=2)
  S4 3人YES/NO/ABSTAIN    -> DEADLOCK(阈值 aw=1 rw=1 EW=2)
  S4b 3人YES/NO/NO        -> REWORK_REQUIRED
```

| # | 场景 | 唯一推导来源 | 结果 |
|---|---|---|---|
| 1–4 | 全弃权 / 1超时+1批准 / 1:1 / 1:1:1 | 上表；`UC9:41`、`UC5:41` 决策表 | 唯一 |
| 5 | 崩溃重启重复投票 | `UC4:68` E5 幂等 | 唯一 |
| 6 | 同 reviewer 两份票 | `UC4:44` f4 + `:58` A5，审计 `REVIEW_DEDUP` | 唯一 |
| 7 | `.dev.yml` 缺字段但 `signal=EXPLICIT` | `UC3:53` d1 先于 d2；`dev_manifest` required 含核心引用 | 唯一（fail-closed） |
| 8 | 第二轮 `.review.yml` 是否覆盖第一轮 | ref+round 双匹配；`UC1-glm:152` STALE | 唯一（不覆盖） |
| 9 | 人工接管超时默认动作 | PRD §6.1 总则 + `UC7:53` §2.f | 唯一（HOLD + 升级告警） |
| 10 | Git 冲突致 checkpoint 与工作区不一致 | `UC8:64` E2 `CHECKPOINT_DRIFT`；PRD E4b 含「或 Git conflict」；UC-7 §1 边界说明剥离 | 唯一 |
| 11 | `review_context` diff 载体不一致 | PRD §5.2 `diff_policy: generate_locally` | 正文唯一；**契约层仍不拦，见 P2-6** |

**11/11 维持全通过，无回退。**

### 复发模式登记（第 7 轮，本轮首次转向）

我连续三轮登记「修复动作本身是新缺陷的成因」。**本轮该模式未再出现**：`a0123e8` 改动了 4 份契约、PRD 69 行、提案、变更清单与 6 个源文件，我逐项复跑后**未发现任何新引入的机器可证缺陷**——唯一的 P1 是旧项未改净，不是新开的口子。这是六轮以来第一次。

我仍要指出：本轮之所以没有复发，很可能是因为团队把「PRD 示例 × 契约」固化成了 `tests/test_prd_snippets_schema.py`（申请 §3.1 首项）——**这正是我连续三轮建议的三段门禁中的第一段**。另两段（「用例判据 × 配置契约」「`reviews/` 双向对账」）仍未入 CI，而本轮唯一的 P1（E7 四处只改两处）恰恰是第二段能自动捕获的类型。建议补齐。

---

## 七、与其他 Reviewer 的交叉核对（GUIDELINES §8）

同基线目前两份报告：**Codex `REJECT`（P1×3）**、本报告（轨 A `NO_APPROVE` / 轨 B `YES_APPROVE`）。其余 reviewer 尚未出具。

**Codex 提出、我复现后据以推翻自己判定的（1 项，本轮最重要的交叉收获）**

| Codex 项 | 我的处置 |
|---|---|
| **P1-1**「加权反支配与法定人数仍非机器硬约束」 | **成立，我采纳并推翻了自己的初稿判定**。我原判 A-P1-2「完全闭环」，只测了自己上轮写下的两个探针；Codex 指出那只是「布尔开关及一个局部下限，并没有验证 PRD 的五重公式」。本机复现：权重 `[5,1,1]`（$3\cdot5=15 \ge 2\cdot7=14$，违反独裁帽）被契约与 `validate_config()` 同时放行；`seat/weight_quorum_required` 可声明为低于公式的值。已作为 §三 A-P1-2 独立成条，轨 A 的 P1 计数由 1 更正为 2。详见 §0.1b |

**与 Codex 独立收敛（2 项）**

| 我的项 | Codex | 状态 |
|---|---|---|
| P2-3（`vote_result_ref` 未进 `required`，提案 `:193`「必须反向引用」未编码） | **P1-2**「disposition 的不可变 vote-result 绑定仍可被 Schema 和用例示例绕过」 | **独立收敛**（我在读到其报告前已写入）。我判 P2 他判 P1；分歧点：`issues_index_sha256` 这一半已必填，绑定链并非完全缺失，且 PRD 正文已明确要求——属「契约未编码文档已写明的规则」，与 A-P1-2 的「文档写明且契约与代码都没有」有强度差别 |
| P2-2 + P2-4（`aep_payload_oversized.json` 名不副实；8 类 payload 未设 `additionalProperties: false`；`protocol` 仍接受 `AEP/1.0`） | **P1-3**「AEP 的『8 类封闭 Payload + 2048 字节双向严格校验』不是实际契约」 | **收敛**，我判 P2 他判 P1；分歧点：16 KiB 与逐字段字节预算已在 `src/macao/msg/envelope.py:30/79/90` 实现并接入 `create()`/`parse()`，Draft-07 本就无法表达整文档字节长度，我认为落到运行时是正确分工（见 §0.1-2 我为此撤回的一条拟议 P1） |

**我提出、Codex 未涉及的（1 项，阻断级）**

| 我的项 | 依据 |
|---|---|
| **A-P1-1** E7 源态四处只改对两处 | `docs/PRD_CHANGE_PROPOSAL_v2.5.md:226` 与 `docs/v2.5_CODE_CHANGE_INVENTORY.md:85` 仍写 `CONSENSUS_CHECK 或 REWORK`，与 PRD `:881` 冲突；PRD `:889` 禁止实现表外路径。验收命令 `grep -rn '`CONSENSUS_CHECK` 或 `REWORK`' docs/ --include='*.md' \| grep -v '/reviews/'` 实测恰好命中这 2 处 |

**两方对轨 B 的分歧**

Codex 出具的是**合并结论**（`REJECT`，不分轨），其三条 P1 全部落在**契约库与运行时**（`macao_config` / `review_disposition` / `aep_envelope` 三份 Schema 与 `config.py`、`vote.py`、`envelope.py`），即轨 A 申请 §2 的交付物 #2；轨 B 申请 §2 列出的 13 份交付物**全部在 `docs/usercases/` 之内**，Codex 未指出其中任何一份与 PRD 或 D-1～D-9 不一致。

我对轨 B 投授予票的依据是：13 份用例与 PRD、契约、D-1～D-9 之间我未找出机器可证的不一致；3 处内嵌围栏对全部 8 份契约交叉验证后全部 PASS；§6 反例库 11/11 可唯一推导；UC-7 的 P1–P4 与 PRD `:881` 修正后的 E7 源态一致。**用例正确地写下了 D-6 的五重公式（UC-5 §2.b、UC-1 h0(3)、UC-10 §2.b），A-P1-2 的缺口在契约与 Loader，不在用例文本。**

**但我要明确记下这条跨轨依赖，不因分轨判定而回避**：轨 B 若获授予并被用作 Phase 1~5 的操作基准，UC-5 与 UC-10 所描述的独裁帽与双 quorum 检查在当前实现中**并不存在**（A-P1-2）。也就是说轨 B 的文档是对的，但照它验收会验不出这三道门禁。因此我在 §八 把 A-P1-2 的闭环列为 Phase 1 编码启动的前置条件——这是对定级结论的补充说明，不是对我这张票的附加条件（PRODUCT-FACTS F-17 不允许有条件通过）。

**关于我这轮转投授予票**：我是本工程连续六轮的反对方，本轮对轨 B 转为授予，依据是上文列出的可复跑证据，不是轮次疲劳。反过来，Codex 指出我判错时我也在同一轮内推翻了自己（§0.1b）——两个方向用的是同一把尺子。按 GUIDELINES §8，单张票不构成裁决，请专家委员会以各方**可复跑的探针**逐条裁定。

## 八、建议闭环顺序与验收标准

### 轨 A（唯一阻断，两行修改）

1. **A-P1-1**：`docs/PRD_CHANGE_PROPOSAL_v2.5.md:226` 与 `docs/v2.5_CODE_CHANGE_INVENTORY.md:85` 删去「或 `REWORK`」。
   *验收*：`grep -rn '`CONSENSUS_CHECK` 或 `REWORK`' docs/ --include='*.md' | grep -v '/reviews/'` 零命中。
   **这一项做完，我对轨 A 的反对即消除。**

2. **A-P1-2**：把 D-6 gate 1/2/3 落到 `ConfigManager.load()`（Draft-07 无法表达跨项求和），修正 `vote.py:180` 的权重 quorum 分母，并在 `schemas/README.md` 写明契约与运行时的分工。
   *验收*：权重 `[5,1,1]` 与 quorum 低于公式的两份配置被 Loader 拒绝并打印拒因。

### 门禁（连续第 4 轮登记，本轮已完成三分之一）

3. 已入 CI 的第一段（PRD 示例 × 契约）请**扩到用例与提案的全部围栏**；
4. 补第二段：**用例/提案声明的每个判据、分支、状态转移边** × 「是否可由契约表达 / 是否在 PRD §3.3 表中存在对应边」。本轮唯一的 P1 正是这一段能自动捕获的类型；
5. 补第三段：`docs/reviews/` 双向对账（脚本见我 `4027cce` 报告 §三 A-P1-4）；
6. **反例 fixture 必须断言拒因关键字**，而非只断言被拒——P2-2 就是缺这一条才让一个未超标的样本冒充预算门禁证据。

### P2 批次（不阻断定级，Phase 1 前处理）

7. `aep_envelope` 的 `$ref` 改内联或相对路径（P2-1）；`vote_result_ref` 进 `required` 并补进 valid fixture（P2-3）；8 类 payload 补 `additionalProperties: false`、裁定是否继续接受 `AEP/1.0`（P2-4）；`macao_config` 的 `policy` 与根级补 `additionalProperties: false`（P2-7）；`diff_policy` 收敛为枚举或改 `schemas/README.md:26` 措辞（P2-6）。
8. UC-8 §6 增纯本地模式断言（P2-5）；修 5 处悬空引用（P2-8）；删 UC-5 浮点旁注（P2-9）；补 `reconcile` 分册（P2-10）；`UC1-init-gemini.md` 补五节（P2-11）。

---

## 附：机器票与结构化 issue 索引

- **轨 A（PRD 设计同步）**：`vote`: **`NO_APPROVE`**　`opinion.status`: `CHANGES_REQUESTED`
- **轨 B（全量用例体系）**：`vote`: **`YES_APPROVE`**　`opinion.status`: `APPROVED`　→ **授予 L1 DOC-ALIGNED / PG-0**

| issue_id | 轨 | severity | disposition_class | 摘要 |
|---|---|---|---|---|
| `claude/A-P1-1` | A | major | `BLOCKING` | E7 源态四处只改两处：提案 `:226` 与变更清单 `:85` 仍写 `CONSENSUS_CHECK 或 REWORK`，与 PRD `:881` 冲突；PRD `:889` 禁止实现表外路径，而 `:85` 是 Phase 1 施工图 |
| `claude/A-P1-2` | A | major | `BLOCKING` | D-6 gate 1/2/3 无机器约束：权重 `[5,1,1]`（违反 $3w_i<2W$）被契约与 `validate_config()` 同时放行；`seat/weight_quorum_required` 可低于公式；`const: true` 只锁旗子不锁权重 |
| `claude/A-P2-1` | A | major | `ADVISORY` | `aep_envelope.schema.json:72` 的 `$ref` 解析为网络 URL，契约库不自包含，机验声明离线复现不出 |
| `claude/A-P2-2` | A | minor | `ADVISORY` | `aep_payload_oversized.json` 未超标（44 字符 / 298 字节），拒因是空数组；补齐该维后被接受。16 KiB 契约层不拦（运行时已实现，属正确分工） |
| `claude/A-P2-3` | A | minor | `ADVISORY` | `vote_result_ref` 未进 `required`，提案 `:193`「必须反向引用冻结的 vote result」未编码；valid fixture 亦不含 |
| `claude/A-P2-4` | A | minor | `ADVISORY` | 8 类 payload 均未设 `additionalProperties: false`，「封闭」不成立；`protocol` 仍接受 `AEP/1.0` |
| `claude/A-P2-6` | A | minor | `ADVISORY` | `schemas/README.md:26` 宣称禁 base64，`diff_policy` 无枚举实际接受 `inline_base64` + base64 载荷 |
| `claude/A-P2-7` | A | minor | `ADVISORY` | `macao_config` 的 `policy`/根级未设 `additionalProperties: false`，已删的 `min_effective_votes` 可塞回且 `orchestrator.py:122` 仍会读 |
| `claude/B-P2-5` | B | minor | `ADVISORY` | UC-8 §6 六条验收标准无纯本地模式断言，本轮新增分支无测试落点 |
| `claude/B-P2-8` | B | minor | `ADVISORY` | 悬空引用：UC-2 §11.4、UC-4 §12.5×3、UC-8「§14.5 三条件」 |
| `claude/B-P2-9` | B | minor | `ADVISORY` | UC-5 §2.b 残留浮点「赞成加权占比」，与 D-6 禁浮点抵触（未能构造数值分歧） |
| `claude/B-P2-10` | B | minor | `ADVISORY` | D-9 的 `reconcile` 在 `docs/usercases/` 零出现 |
| `claude/B-P2-11` | B | minor | `ADVISORY` | `UC1-init-gemini.md` 五个可验收小节全缺（由 `UC1-init-glm.md` 兜底，不阻断） |
| `claude/A-P3-1` | A | minor | `ADVISORY` | PRD §14.2 role_view 缺 override 后 `SHOULD_DISPOSE` 行（五轮未闭） |
| `claude/A-P3-2` | A | minor | `ADVISORY` | STATUS 表标题在 HEAD 滞后（26 vs 29，被审基线一致）；申请称 STATUS 记 120 份结论，实为 124 |
| `claude/A-P3-3` | A | minor | `ADVISORY` | 文档份数不可复现（申请 188；实测 184/187/187/200） |
