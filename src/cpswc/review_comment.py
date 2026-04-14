"""
review_comment.py — CPSWC v0 ReviewComment

宪法必做项 #13: "手工录入，绑定 field_id / narrative_node_id / obligation_id"

v0 实现:
  - ReviewComment dataclass: 结构化审查意见对象
  - 每条 comment 绑定到一个 target (field / narrative section / obligation)
  - 支持 load / save JSON
  - 不接入 runtime (runtime 不消费 review comments)

完成判定:
  - 有正式对象层 ✓
  - 有 loader / serializer ✓
  - 至少一个样本 comment 文件可运行验证 ✓

v1 升级路径:
  - 接入 ModificationReport (审查意见 → 修改对照追踪)
  - 接入 SubmissionLifecycle.review_round
  - 审查意见自动匹配 obligation / field 变更
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any


# ============================================================
# 对象层
# ============================================================

@dataclass
class ReviewComment:
    """结构化审查意见对象。

    target_type + target_ref 绑定到具体的审查对象:
      - "field"      + "field.fact.land.total_area"
      - "narrative"   + "sec.evaluation.earthwork_balance"
      - "obligation"  + "ob.disposal_site.geology_report"
      - "artifact"    + "art.table.investment.total_summary"
      - "general"     + "" (整体意见, 不绑定具体对象)
    """
    comment_id: str
    round: int                      # 审查轮次 (1 = 首次审查)
    target_type: str                # "field" | "narrative" | "obligation" | "artifact" | "general"
    target_ref: str                 # 具体引用 id
    comment_text: str               # 审查意见文本
    reviewer: str                   # 审查人
    status: str = "open"            # "open" | "resolved" | "deferred"
    resolution_note: str = ""       # 处理说明
    created_at: str = ""            # ISO 时间戳
    resolved_at: str = ""           # ISO 时间戳


VALID_TARGET_TYPES = {"field", "narrative", "obligation", "artifact", "general"}
VALID_STATUSES = {"open", "resolved", "deferred"}


# ============================================================
# Loader / Serializer
# ============================================================

def load_comments(path: str | Path) -> list[ReviewComment]:
    """从 JSON 文件加载审查意见列表。"""
    path = Path(path)
    with path.open(encoding="utf-8") as f:
        data = json.load(f)

    comments_data = data.get("comments") or data  # 支持顶层 list 或 {comments: [...]}
    if isinstance(comments_data, dict):
        comments_data = comments_data.get("comments") or []

    result = []
    for item in comments_data:
        rc = ReviewComment(
            comment_id=item.get("comment_id", ""),
            round=item.get("round", 1),
            target_type=item.get("target_type", "general"),
            target_ref=item.get("target_ref", ""),
            comment_text=item.get("comment_text", ""),
            reviewer=item.get("reviewer", ""),
            status=item.get("status", "open"),
            resolution_note=item.get("resolution_note", ""),
            created_at=item.get("created_at", ""),
            resolved_at=item.get("resolved_at", ""),
        )
        result.append(rc)
    return result


def save_comments(comments: list[ReviewComment], path: str | Path) -> None:
    """将审查意见列表保存为 JSON。"""
    path = Path(path)
    data = {
        "$schema": "CPSWC_ReviewComment_v0",
        "comments": [asdict(c) for c in comments],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def resolve_comment(comment: ReviewComment, note: str,
                    resolved_at: str = "") -> ReviewComment:
    """标记审查意见为已处理。"""
    comment.status = "resolved"
    comment.resolution_note = note
    if resolved_at:
        comment.resolved_at = resolved_at
    return comment


# ============================================================
# 校验
# ============================================================

def validate_comments(comments: list[ReviewComment]) -> list[str]:
    """校验审查意见列表，返回错误信息列表。"""
    errors = []
    seen_ids: set[str] = set()

    for i, c in enumerate(comments):
        prefix = f"comment[{i}] ({c.comment_id})"

        if not c.comment_id:
            errors.append(f"{prefix}: comment_id 不能为空")
        elif c.comment_id in seen_ids:
            errors.append(f"{prefix}: comment_id 重复")
        else:
            seen_ids.add(c.comment_id)

        if c.target_type not in VALID_TARGET_TYPES:
            errors.append(f"{prefix}: target_type '{c.target_type}' 不合法")

        if c.status not in VALID_STATUSES:
            errors.append(f"{prefix}: status '{c.status}' 不合法")

        if not c.comment_text.strip():
            errors.append(f"{prefix}: comment_text 不能为空")

    return errors
