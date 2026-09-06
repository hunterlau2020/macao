"""Interactive Setup Wizard & Auto-Discovery Engine (Phase 3 / PRD §14)."""

import os
import sys
import time
import math
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml
import click
from rich.panel import Panel

from macao.cli.ui import console
from macao.core.schema import validate_config
from macao.adapter.integ_harness import CLI_ADAPTER_MAP


def probe_available_clis() -> List[Dict[str, Any]]:
    """Probes system PATH to find installed AI Agent CLIs and their versions."""
    found = []
    candidates = [
        ("opencode", "opencode", "1.18.25"),
        ("agy", "agy", "1.1.22"),
        ("cursor", "agent", "2026.08"),
        ("claude-code", "claude", "2.1.251"),
        ("codex", "codex", "2.1.0"),
        ("kimi", "kimi", "1.0.0"),
    ]

    for key, binary, default_ver in candidates:
        exe = shutil.which(binary)
        if exe:
            try:
                res = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=3)
                ver = res.stdout.strip() or default_ver
            except Exception:
                ver = default_ver
            found.append({
                "id": key,
                "cli": key,
                "binary": exe,
                "version": ver
            })
    return found


def detect_git_context(project_root: Path) -> Dict[str, Optional[str]]:
    """Detects Git repository branch and remote defaults accurately."""
    branch = "main"
    remote = None

    # 1. Detect remote
    try:
        res = subprocess.run(["git", "remote"], cwd=project_root, capture_output=True, text=True)
        if res.returncode == 0 and res.stdout.strip():
            remotes = res.stdout.strip().split()
            remote = "origin" if "origin" in remotes else remotes[0]
    except Exception:
        pass

    # 2. Detect default target branch:
    detected_branch = None
    if remote:
        try:
            res = subprocess.run(["git", "symbolic-ref", f"refs/remotes/{remote}/HEAD"], cwd=project_root, capture_output=True, text=True)
            if res.returncode == 0 and res.stdout.strip():
                detected_branch = res.stdout.strip().split("/")[-1]
        except Exception:
            pass

    # Fallback to local 'main'
    if not detected_branch:
        try:
            res = subprocess.run(["git", "rev-parse", "--verify", "refs/heads/main"], cwd=project_root, capture_output=True, text=True)
            if res.returncode == 0:
                detected_branch = "main"
        except Exception:
            pass

    # Fallback to local 'master'
    if not detected_branch:
        try:
            res = subprocess.run(["git", "rev-parse", "--verify", "refs/heads/master"], cwd=project_root, capture_output=True, text=True)
            if res.returncode == 0:
                detected_branch = "master"
        except Exception:
            pass

    # Fallback to current checked-out branch
    if not detected_branch:
        try:
            res = subprocess.run(["git", "branch", "--show-current"], cwd=project_root, capture_output=True, text=True)
            if res.returncode == 0 and res.stdout.strip():
                detected_branch = res.stdout.strip()
        except Exception:
            pass

    branch = detected_branch or "main"
    return {"branch": branch, "remote": remote}


def detect_ci_command(project_root: Path) -> Optional[str]:
    """Infers testing command from project build files (optional hint)."""
    if (project_root / "pytest.ini").exists() or (project_root / "pyproject.toml").exists():
        return "pytest -q"
    if (project_root / "package.json").exists():
        return "npm test"
    if (project_root / "Cargo.toml").exists():
        return "cargo test"
    if (project_root / "go.mod").exists():
        return "go test ./..."
    return None


import math


def ensure_gitignore_isolation(project_root: Path) -> bool:
    """Ensures all MACAO runtime worktree, review, archive and DB paths are in .gitignore."""
    gi_path = project_root / ".gitignore"
    required_rules = [
        ".macao/worktrees/",
        ".macao/.reviews/",
        ".macao/.dev.yml",
        ".macao/vote_result.json",
        ".macao/archive/",
        ".macao/logs/",
        ".macao/*.log",
        ".macao/*.db",
        ".macao/*.db-journal",
        ".macao/*.db-wal",
        ".macao/*.db-shm",
    ]
    content = gi_path.read_text(encoding="utf-8") if gi_path.exists() else ""
    lines = [line.strip() for line in content.splitlines()]
    missing_rules = [r for r in required_rules if r not in lines]

    if missing_rules:
        new_content = content
        if new_content and not new_content.endswith("\n"):
            new_content += "\n"
        if "# MACAO Runtime Worktrees & State Store (Auto-added)" not in new_content:
            new_content += "\n# MACAO Runtime Worktrees & State Store (Auto-added)\n"
        for r in missing_rules:
            new_content += f"{r}\n"
        gi_path.write_text(new_content, encoding="utf-8")
        return True
    return False


def remove_gitignore_isolation(project_root: Path) -> bool:
    """Removes the auto-added MACAO section and rules from .gitignore."""
    gi_path = project_root / ".gitignore"
    if not gi_path.exists():
        return False
    content = gi_path.read_text(encoding="utf-8")
    lines = content.splitlines()
    header = "# MACAO Runtime Worktrees & State Store (Auto-added)"
    rules_set = {
        ".macao/worktrees/",
        ".macao/.reviews/",
        ".macao/.dev.yml",
        ".macao/vote_result.json",
        ".macao/archive/",
        ".macao/logs/",
        ".macao/*.log",
        ".macao/*.db",
        ".macao/*.db-journal",
        ".macao/*.db-wal",
        ".macao/*.db-shm",
    }
    new_lines = []
    modified = False
    for line in lines:
        stripped = line.strip()
        if stripped == header or stripped in rules_set:
            modified = True
            continue
        new_lines.append(line)

    if modified:
        new_content = "\n".join(new_lines).strip()
        if new_content:
            new_content += "\n"
        gi_path.write_text(new_content, encoding="utf-8")
        return True
    return False


def get_canonical_agent_info(cli_id: str, role: str = "dev") -> Dict[str, Any]:
    """Returns canonical ID (dev-<cli> / rev-<cli>), CLI binary/name, and adapter."""
    short_names = {
        "claude-code": "claude",
        "claude": "claude",
        "cursor": "cursor",
        "agent": "cursor",
        "opencode": "opencode",
        "agy": "agy",
        "antigravity": "agy",
        "codex": "codex",
        "kimi": "kimi",
        "mock-cli": "mock",
    }
    short = short_names.get(cli_id, cli_id)
    agent_id = f"{role}-{short}"
    cli_name = "claude-code" if cli_id in ("claude", "claude-code") else ("agent" if cli_id in ("cursor", "agent") else cli_id)
    adapter = "claude-hook" if cli_name in ("claude", "claude-code") else "pty-wrapper"
    return {
        "id": agent_id,
        "cli": cli_name,
        "adapter": adapter
    }


def format_annotated_macao_yaml(
    project_name: str,
    workspace_path: str,
    remote_name: Optional[str],
    default_branch: str,
    executor: Dict[str, Any],
    reviewers: List[Dict[str, Any]],
    ci_gate_command: Optional[str] = None
) -> str:
    """Formats a macao.yaml document with rich Chinese inline comments for every field."""
    rev_count = len(reviewers)
    total_w = sum(r.get("vote_weight", 1) for r in reviewers)
    min_wq = math.ceil(2 * total_w / 3) if total_w > 0 else 1
    min_seats = max(2, min_wq)

    rev_entries = []
    for r in reviewers:
        r_id = r["id"]
        r_cli = r["cli"]
        r_adp = r["adapter"]
        r_w = r.get("vote_weight", 1)
        r_model = r.get("model")
        model_comment = f"\n      # model: \"{r_model}\"" if r_model else ""
        rev_entries.append(f"""    - id: "{r_id}"            # 审查员席位唯一标识符 (rev-<cli>)
      cli: "{r_cli}"               # 调用的底层 AI 命令行工具
      adapter: "{r_adp}"     # 隔离适配器类型 (pty-wrapper 伪终端隔离)
      vote_weight: {r_w}             # 审查席位投票权重{model_comment}""")

    reviewers_yaml_str = "\n\n".join(rev_entries)

    ci_repr = f'"{ci_gate_command}"' if ci_gate_command else "null"
    remote_repr = f'"{remote_name}"' if remote_name else "null"
    exec_model_line = f'\n    # model: "{executor["model"]}"' if executor.get("model") else ""

    content = f"""# ==============================================================================
# MACAO 多 Agent 协同编排配置文件 (macao.yaml)
# 遵循规范: Draft-07 Strict Schema (PRD §13)
# ==============================================================================

# 配置规范版本号（固定为 2.5）
version: "2.5"

# ------------------------------------------------------------------------------
# 1. 项目基础信息与仓库设置
# ------------------------------------------------------------------------------
project:
  # 项目名称（默认取项目根目录名）
  name: "{project_name}"
  repository:
    # 工作区路径（相对路径，. 代表当前根目录）
    workspace_path: "{workspace_path}"
    # Git 远端名称（通常为 origin，无远端设为 null）
    remote_name: {remote_repr}
    # 主干分支名称（代码审查通过后的合并目标分支，通常为 main 或 master）
    default_branch: "{default_branch}"

# ------------------------------------------------------------------------------
# 2. 多 Agent 团队配置（开发执行者与独立审查团）
# ------------------------------------------------------------------------------
team:
  # 主开发执行者：负责根据任务需求编写代码、运行自测并提交就绪检查点
  executor:
    id: "{executor['id']}"             # 执行者唯一标识符（统一命名: dev-<cli>）
    cli: "{executor['cli']}"           # 调用的底层 AI 命令行工具
    adapter: "{executor['adapter']}"   # 通信适配器类型 (claude-hook / pty-wrapper){exec_model_line}

  # 独立审查团：在隔离工作树（Git Worktree）中并发独立审查代码并投票
  reviewers:
{reviewers_yaml_str}

# ------------------------------------------------------------------------------
# 3. 共识仲裁与审查策略
# ------------------------------------------------------------------------------
policy:
  # 仲裁规则：weighted_2/3_v1 表示加权赞成票需达到或超过有效总票数的 2/3
  consensus_rule: "weighted_2/3_v1"
  # 独裁者上限保护：若单个审查员权重达到或超过法定人数，自动封顶防止一人专断
  dictator_cap_enabled: true
  # 最少获胜席位数：达成通过至少需要的赞成票数量
  minimum_winning_seats: {min_seats}
  # 法定有效席位法定人数：参与有效投票（非超时弃权）的最少席位数
  seat_quorum_required: {min_wq}
  # 法定有效权重法定人数：参与有效投票的最少权重之和
  weight_quorum_required: {min_wq}
  # 最大返工轮次：审查打回后，最多允许执行者修复并重新提审的轮次（超限进入人工干预）
  max_rework_rounds: 3
  # 审查策略：delta_plus_focus 表示重点审查增量 Diff 及执行者关注点
  review_strategy: "delta_plus_focus"

# ------------------------------------------------------------------------------
# 4. 代码合并管道与发布门禁
# ------------------------------------------------------------------------------
merge:
  # 合并策略：ff_only 仅允许快速前进合并（Fast-Forward），保证线性干净的 Git 历史
  strategy: "ff_only"
  # CI 自动化门禁测试命令：合并前在隔离环境中执行（如 pytest -q、npm test，无则为 null）
  ci_gate_command: {ci_repr}
  # 人工签字放行：达成 2/3 评审共识后，是否仍需人类在终端执行 'macao merge approve' 显式确认
  require_human_signoff: true
  # 合并前是否自动对齐变基到最新目标分支
  rebase_before_merge: false

# ------------------------------------------------------------------------------
# 5. 各环节超时 SLA 兜底控制
# ------------------------------------------------------------------------------
timeouts:
  # 开发阶段超时上限（超时自动发出告警）
  development: "2h"
  # 检查点合规性校验超时
  checkpoint_validation: "1m"
  # 评审派发与工作树初始化超时
  review_request: "30m"
  # 每个审查员在独立 Worktree 中的分析与响应超时（超时自动降级为 ABSTAIN 弃权）
  per_reviewer: "10m"
  # 共识计票与仲裁阶段超时
  consensus_check: "1m"

# ------------------------------------------------------------------------------
# 6. 推理分析与诊断阈值
# ------------------------------------------------------------------------------
thresholds:
  # 是否仅在日志中记录第二层反思与推理链
  layer2_inference_log_only: true
  # 模型自诊断置信度阈值（低于此值可触发人工干预）
  llm_diagnosis_override_below: 0.7

# ------------------------------------------------------------------------------
# 7. 成本计量与控制
# ------------------------------------------------------------------------------
cost:
  # 是否开启各 Agent Token 用量与成本计量
  usage_metering: true
  # 月度预算上限（美元，null 表示不设硬限制）
  monthly_budget_usd: null

# ------------------------------------------------------------------------------
# 8. 安全沙箱与白名单控制
# ------------------------------------------------------------------------------
security:
  # 允许由系统唤起调用的 AI CLI 绝对白名单，防止命令注入风险
  allowed_clis:
    - "claude-code"
    - "claude"
    - "codex"
    - "opencode"
    - "agy"
    - "antigravity"
    - "agent"
    - "cursor"
    - "kimi"
    - "mock-cli"
  # 是否将开发者的终端执行交互日志发送给审查员（通常设为 false 避免提示词偏见）
  send_terminal_logs_to_reviewers: false
  # 是否自动在日志、信封中掩码敏感密钥与 API Token
  secrets_masking: true

# ------------------------------------------------------------------------------
# 9. 不可变审计日志归档保留
# ------------------------------------------------------------------------------
audit:
  # 审计事件记录（SQLite state.db）在归档中的保留天数
  retention_days: 90
"""
    return content


def generate_smart_config(
    project_root: Path,
    executor_cli: Optional[str] = None,
    executor_model: Optional[str] = None,
    reviewers: Optional[List[Dict[str, Any]]] = None,
    detected_clis: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Generates a valid, customized macao.yaml dictionary based on detected environment."""
    git_info = detect_git_context(project_root)
    ci_cmd = detect_ci_command(project_root)
    proj_name = project_root.name or "macao-project"

    if detected_clis is None:
        detected_clis = probe_available_clis()

    detected_ids = [c["id"] for c in detected_clis] if detected_clis else []

    # Choose Executor from detected CLIs if not explicitly specified
    if not executor_cli:
        if "claude-code" in detected_ids or "claude" in detected_ids:
            executor_cli = "claude-code"
            executor_model = executor_model or "claude-3-7-sonnet"
        elif "opencode" in detected_ids:
            executor_cli = "opencode"
            executor_model = executor_model or "GLM 5.3 max"
        elif "codex" in detected_ids:
            executor_cli = "codex"
            executor_model = executor_model or "o3-mini"
        elif detected_ids:
            executor_cli = detected_ids[0]
            executor_model = executor_model or "default"
        else:
            executor_cli = "opencode"
            executor_model = executor_model or "GLM 5.3 max"

    exec_info = get_canonical_agent_info(executor_cli, role="dev")
    if executor_model:
        exec_info["model"] = executor_model

    if not reviewers:
        # Build reviewers from remaining detected CLIs if available
        available_rev_candidates = [c for c in detected_ids if c != executor_cli]
        if len(available_rev_candidates) >= 2:
            reviewers = []
            for r_id in available_rev_candidates:
                r_info = get_canonical_agent_info(r_id, role="rev")
                r_info["vote_weight"] = 1
                reviewers.append(r_info)
        else:
            reviewers = [
                {"id": "rev-cursor", "cli": "agent", "adapter": "pty-wrapper", "vote_weight": 1, "model": "claude-3-5-sonnet"},
                {"id": "rev-codex", "cli": "codex", "adapter": "pty-wrapper", "vote_weight": 1, "model": "o3-mini"},
                {"id": "rev-agy", "cli": "agy", "adapter": "pty-wrapper", "vote_weight": 1, "model": "gemini-2.0-pro"}
            ]

    rev_count = len(reviewers)
    total_w = sum(r.get("vote_weight", 1) for r in reviewers)
    quorum_votes = math.ceil(2 * total_w / 3) if total_w > 0 else 1

    for r in reviewers:
        r.setdefault("vote_weight", 1)

    config_data = {
        "version": "2.5",
        "project": {
            "name": proj_name,
            "repository": {
                "workspace_path": ".",
                "remote_name": git_info["remote"],
                "default_branch": git_info["branch"]
            }
        },
        "team": {
            "executor": exec_info,
            "reviewers": reviewers
        },
        "policy": {
            "consensus_rule": "weighted_2/3_v1",
            "dictator_cap_enabled": True,
            "minimum_winning_seats": max(2, quorum_votes),
            "seat_quorum_required": quorum_votes,
            "weight_quorum_required": quorum_votes,
            "max_rework_rounds": 3,
            "review_strategy": "delta_plus_focus"
        },
        "merge": {
            "strategy": "ff_only",
            "ci_gate_command": ci_cmd,
            "require_human_signoff": True,
            "rebase_before_merge": False
        },
        "timeouts": {
            "development": "2h",
            "checkpoint_validation": "1m",
            "review_request": "30m",
            "per_reviewer": "10m",
            "consensus_check": "1m"
        },
        "security": {
            "allowed_clis": ["claude-code", "claude", "codex", "opencode", "agy", "antigravity", "agent", "cursor", "kimi", "mock-cli"],
            "send_terminal_logs_to_reviewers": False,
            "secrets_masking": True
        }
    }

    # Validate against Schema
    is_val, err = validate_config(config_data)
    if not is_val:
        raise ValueError(f"Generated configuration failed schema validation: {err}")

    return config_data


def run_interactive_init(
    project_root: Path,
    target_path: str = "macao.yaml",
    non_interactive: bool = False,
    force: bool = False,
    custom_executor: Optional[str] = None,
    custom_model: Optional[str] = None
) -> Dict[str, Any]:
    """Interactive & intelligent setup wizard to configure macao.yaml with Chinese comments."""
    console.print(Panel.fit(
        "[bold cyan]MACAO 智能项目初始化[/bold cyan]\n"
        "[dim]自动环境探查 · 多 Agent 团队配置 · 详尽中文注释[/dim]",
        border_style="cyan"
    ))

    target_file = (project_root / target_path).resolve()
    if target_file.exists() and not force:
        if non_interactive or not sys.stdin.isatty():
            console.print(f"[yellow]提示: 配置文件 '{target_path}' 已存在 (already exists)。使用 --force 可强制重新生成。[/yellow]")
            return yaml.safe_load(target_file.read_text(encoding="utf-8")) or {}

        overwrite = click.confirm(f"配置文件 '{target_path}' 已存在，是否重新配置并覆盖？", default=False)
        if not overwrite:
            console.print("[yellow]已取消初始化，保持现有配置不变。[/yellow]")
            return yaml.safe_load(target_file.read_text(encoding="utf-8")) or {}

        backup_file = target_file.parent / f"{target_file.name}.bak.{int(time.time())}"
        shutil.copy(target_file, backup_file)
        console.print(f"[dim]已将原有配置备份至: {backup_file.name}[/dim]")

    # 1. Project Name
    default_name = project_root.name or "my-project"
    if non_interactive or not sys.stdin.isatty():
        proj_name = default_name
    else:
        proj_name = click.prompt("1. 请输入项目名称", default=default_name)

    # 2. Probe AI Agent CLIs
    detected_clis = probe_available_clis()
    console.print(f"\n[bold green]✓ 探查到本机已安装 {len(detected_clis)} 款 AI Agent CLI 工具:[/bold green]")
    for idx, c in enumerate(detected_clis, 1):
        console.print(f"  [{idx}] [bold white]{c['cli']}[/bold white] ({c['version']}) -> [dim]{c['binary']}[/dim]")

    if not detected_clis:
        detected_clis = [
            {"id": "claude-code", "cli": "claude-code", "version": "2.1.263", "binary": "claude"},
            {"id": "opencode", "cli": "opencode", "version": "1.18.29", "binary": "opencode"},
            {"id": "codex", "cli": "codex", "version": "2.1.0", "binary": "codex"},
            {"id": "agy", "cli": "agy", "version": "1.1.27", "binary": "agy"},
            {"id": "cursor", "cli": "agent", "version": "2026.09.02", "binary": "agent"},
            {"id": "kimi", "cli": "kimi", "version": "0.41.0", "binary": "kimi"}
        ]

    # 3. Choose Executor
    if custom_executor:
        exec_cand = next((c for c in detected_clis if c["id"] == custom_executor or c["cli"] == custom_executor), {"id": custom_executor, "cli": custom_executor})
    elif non_interactive or not sys.stdin.isatty():
        exec_cand = next((c for c in detected_clis if c["id"] in ("claude-code", "claude")), detected_clis[0])
    else:
        default_idx = "1"
        for idx, c in enumerate(detected_clis, 1):
            if c["id"] in ("claude-code", "claude"):
                default_idx = str(idx)
                break
        choice_idx = click.prompt(f"\n2. 请选择主开发执行者 (Executor) 序号 [1-{len(detected_clis)}]", default=default_idx)
        try:
            sel_i = int(choice_idx) - 1
            exec_cand = detected_clis[sel_i] if 0 <= sel_i < len(detected_clis) else detected_clis[0]
        except Exception:
            exec_cand = detected_clis[0]

    executor_info = get_canonical_agent_info(exec_cand["id"], role="dev")
    if custom_model:
        executor_info["model"] = custom_model
    console.print(f"  [cyan]✓ 已选定主开发执行者:[/cyan] [bold]{executor_info['id']}[/bold] (调取命令: {executor_info['cli']}, 适配器: {executor_info['adapter']})")

    # 4. Reviewers
    rem_candidates = [c for c in detected_clis if c["id"] != exec_cand["id"]]
    if len(rem_candidates) < 2:
        rem_candidates.append({"id": "codex", "cli": "codex"})
        rem_candidates.append({"id": "opencode", "cli": "opencode"})

    recommended_reviewers = [get_canonical_agent_info(c["id"], role="rev") for c in rem_candidates]
    for r in recommended_reviewers:
        r["vote_weight"] = 1

    if non_interactive or not sys.stdin.isatty():
        final_reviewers = recommended_reviewers
    else:
        console.print(f"\n[bold green]3. 推荐独立代码审查团队 (Reviewers，共 {len(recommended_reviewers)} 位专家席位):[/bold green]")
        for idx, r in enumerate(recommended_reviewers, 1):
            console.print(f"  • [bold white]{r['id']}[/bold white] (调取命令: {r['cli']}, 适配器: {r['adapter']}, 投票权重: 1)")

        use_default = click.confirm("是否采用上述推荐的全部独立审查专家席位？", default=True)
        if use_default:
            final_reviewers = recommended_reviewers
        else:
            sel_str = click.prompt("请输入需要的审查员序号（逗号分隔，如 1,2,3，至少需 2 位）", default=",".join(str(i) for i in range(1, len(recommended_reviewers)+1)))
            chosen_revs = []
            for part in sel_str.split(","):
                try:
                    idx = int(part.strip()) - 1
                    if 0 <= idx < len(recommended_reviewers):
                        chosen_revs.append(recommended_reviewers[idx])
                except Exception:
                    pass
            if len(chosen_revs) < 2:
                console.print("[yellow]至少需要 2 位审查员才能满足法定仲裁席位，已自动补齐推荐席位。[/yellow]")
                final_reviewers = recommended_reviewers
            else:
                final_reviewers = chosen_revs

    # 5. Git & CI
    git_info = detect_git_context(project_root)
    ci_cmd = detect_ci_command(project_root)

    if not (non_interactive or not sys.stdin.isatty()):
        console.print(f"\n[bold green]4. Git 仓库合并主干与远端设置:[/bold green]")
        console.print(f"  • 目标主干分支 (default_branch): [bold white]{git_info['branch']}[/bold white]")
        console.print(f"  • Git 远端名称 (remote_name): [bold white]{git_info['remote'] or '无 (null)'}[/bold white]")
        use_git = click.confirm("是否采用探查到的 Git 主干分支与远端设置？", default=True)
        if not use_git:
            git_info["branch"] = click.prompt("请输入主干合并目标分支名称", default=git_info["branch"])
            user_remote = click.prompt("请输入 Git 远端名称 (若为纯本地仓库请留空)", default=git_info["remote"] or "")
            git_info["remote"] = user_remote.strip() if user_remote.strip() else None

    # 6. Format annotated YAML
    yaml_str = format_annotated_macao_yaml(
        project_name=proj_name,
        workspace_path=".",
        remote_name=git_info["remote"],
        default_branch=git_info["branch"],
        executor=executor_info,
        reviewers=final_reviewers,
        ci_gate_command=ci_cmd
    )

    # 7. Validate
    dict_data = yaml.safe_load(yaml_str)
    is_val, err = validate_config(dict_data)
    if not is_val:
        raise ValueError(f"生成的配置未通过 Draft-07 Schema 校验: {err}")

    # 8. Write file
    target_file.write_text(yaml_str, encoding="utf-8")
    console.print(f"\n[bold green]✓ 成功生成带详尽中文注释的配置文件: {target_path}[/bold green]")

    # 9. Update .gitignore
    isolated = ensure_gitignore_isolation(project_root)
    if isolated:
        console.print("[green]✓ 已向 .gitignore 自动追加 .macao/ 运行时隔离规则[/green]")

    # 10. Summary
    console.print(Panel.fit(
        f"[bold cyan]MACAO 项目初始化配置完成[/bold cyan]\n\n"
        f"• 项目名称: [bold white]{proj_name}[/bold white]\n"
        f"• 开发执行者: [bold green]{executor_info['id']}[/bold green] (CLI: {executor_info['cli']})\n"
        f"• 独立审查团: [bold yellow]{', '.join(r['id'] for r in final_reviewers)}[/bold yellow] (共 {len(final_reviewers)} 个席位)\n"
        f"• 仲裁机制: [magenta]加权 2/3 共识仲裁 (通过最少需要 {dict_data['policy']['seat_quorum_required']} 票)[/magenta]\n\n"
        f"[dim]后续操作: 运行 'macao doctor' 自诊断，或 'macao task create' 发起开发任务[/dim]",
        border_style="green"
    ))

    return dict_data
