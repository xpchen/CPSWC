#!/usr/bin/env python3
"""
submission_package_builder.py — CPSWC v0 Submission Package Builder

Step 13A: 把 RuntimeSnapshot + FrozenSubmissionInput + SubmissionPackageVersion +
Workbench HTML 打成一个确定性的可导出、可归档、可回放的 submission package。

输出结构:
    <package_dir>/
    ├── PACKAGE_MANIFEST.json       # 顶层清单: 文件列表 + SHA256 + 版本关系
    ├── runtime_snapshot.json       # 完整 RuntimeSnapshot
    ├── frozen_submission_input.json # FrozenSubmissionInput (含 content_hash)
    ├── submission_package_version.json
    ├── workbench.html              # 可视化工作台 (单文件)
    ├── manifests/
    │   ├── artifact_manifest.json  # required artifact id 列表
    │   ├── assurance_manifest.json
    │   ├── calculator_manifest.json
    │   └── obligation_manifest.json # triggered obligation id 列表
    └── calculator_results/
        ├── cal.compensation.fee.json
        ├── cal.target.weighted_comprehensive.json
        └── cal.disposal_site.level_assessment.json

设计边界:
    - 纯 Python, 不涉及 UI
    - 确定性: 相同输入 → 相同文件内容 (时间戳除外)
    - 不做文档渲染 (留给 Step 13B)
    - 不做 zip (先做目录; zip 是未来 2 行代码的事)

使用方式:
    from cpswc.renderers.package_builder import build_package
    pkg_path = build_package(project_input, output_dir="/tmp/pkg")

CLI:
    python submission_package_builder.py <facts.json> -o <output_dir>
"""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cpswc.paths import REGISTRIES_DIR, SAMPLES_DIR, GOVERNANCE_DIR, PROJECT_ROOT  # noqa
SPECS_DIR = REGISTRIES_DIR  # backward compat alias


def _sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _write_json(path: Path, data: Any, sort_keys: bool = True) -> str:
    """写 JSON 并返回内容的 SHA256"""
    content = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=sort_keys,
                         default=str)
    path.write_text(content, encoding="utf-8")
    return _sha256(content)


def build_package(
    project_input: dict,
    output_dir: str | Path,
    *,
    ruleset: str | None = None,
    lifecycle: str | None = None,
    previous_version_id: str | None = None,
) -> Path:
    """
    构建完整的 submission package 目录。

    参数:
        project_input: sample/project JSON dict (含 facts / derived / sample_meta)
        output_dir: 输出目录路径
        ruleset: 规则集标识 (默认 v2026_gd_package)
        lifecycle: 生命周期阶段 (默认 pre_submission)
        previous_version_id: 上一个版本 id (用于版本链)

    返回:
        Path 到生成的 package 目录
    """
    # ---- Step 1: Run project ----
    from cpswc.runtime import (  # type: ignore
        run_project,
        freeze_submission,
        create_version,
        load_all_registries,
        _serialize_snapshot,
    )
    from cpswc.renderers.workbench import render_workbench  # type: ignore

    snapshot = run_project(project_input, ruleset=ruleset, lifecycle=lifecycle)
    frozen = freeze_submission(snapshot)
    version = create_version(frozen, previous_version_id=previous_version_id)

    # ---- Step 2: Create output directory ----
    pkg_dir = Path(output_dir)
    pkg_dir.mkdir(parents=True, exist_ok=True)
    manifests_dir = pkg_dir / "manifests"
    manifests_dir.mkdir(exist_ok=True)
    calc_dir = pkg_dir / "calculator_results"
    calc_dir.mkdir(exist_ok=True)

    # ---- Step 3: Write files ----
    file_hashes: dict[str, str] = {}

    # runtime_snapshot.json
    snapshot_json = _serialize_snapshot(snapshot)
    (pkg_dir / "runtime_snapshot.json").write_text(snapshot_json, encoding="utf-8")
    file_hashes["runtime_snapshot.json"] = _sha256(snapshot_json)

    # frozen_submission_input.json
    frozen_dict = {
        "content_hash": frozen.content_hash,
        "fact_snapshot_hash": frozen.fact_snapshot_hash,
        "frozen_at": frozen.frozen_at,
        "artifact_manifest": frozen.artifact_manifest,
        "assurance_manifest": frozen.assurance_manifest,
        "calculator_manifest": frozen.calculator_manifest,
        "obligation_manifest": frozen.obligation_manifest,
    }
    file_hashes["frozen_submission_input.json"] = _write_json(
        pkg_dir / "frozen_submission_input.json", frozen_dict)

    # submission_package_version.json
    version_dict = {
        "version_id": version.version_id,
        "frozen_input_hash": version.frozen_input_hash,
        "timestamp": version.timestamp,
        "previous_version_id": version.previous_version_id,
        "diff_summary": version.diff_summary,
    }
    file_hashes["submission_package_version.json"] = _write_json(
        pkg_dir / "submission_package_version.json", version_dict)

    # workbench.html
    registries = load_all_registries()
    snapshot_dict = json.loads(snapshot_json)
    snapshot_dict["_original_facts"] = project_input.get("facts") or {}
    html = render_workbench(snapshot_dict, frozen_dict, version_dict, registries)
    (pkg_dir / "workbench.html").write_text(html, encoding="utf-8")
    file_hashes["workbench.html"] = _sha256(html)

    # manifests/
    file_hashes["manifests/artifact_manifest.json"] = _write_json(
        manifests_dir / "artifact_manifest.json",
        {"artifacts": frozen.artifact_manifest, "count": len(frozen.artifact_manifest)})

    file_hashes["manifests/assurance_manifest.json"] = _write_json(
        manifests_dir / "assurance_manifest.json",
        {"assurances": frozen.assurance_manifest, "count": len(frozen.assurance_manifest)})

    file_hashes["manifests/calculator_manifest.json"] = _write_json(
        manifests_dir / "calculator_manifest.json",
        {"calculators": frozen.calculator_manifest, "count": len(frozen.calculator_manifest)})

    file_hashes["manifests/obligation_manifest.json"] = _write_json(
        manifests_dir / "obligation_manifest.json",
        {"obligations": frozen.obligation_manifest, "count": len(frozen.obligation_manifest)})

    # calculator_results/ (per-calculator detail)
    for cr in snapshot.calculator_results:
        if cr.status != "ok":
            continue
        safe_name = cr.calculator_id.replace(".", "_")
        cr_data = {
            "calculator_id": cr.calculator_id,
            "output_field_id": cr.output_field_id,
            "value": cr.value,
            "unit": cr.unit,
            "status": cr.status,
        }
        fname = f"calculator_results/{safe_name}.json"
        file_hashes[fname] = _write_json(
            calc_dir / f"{safe_name}.json", cr_data)

    # ---- Step 3.5: Render formal DOCX (Step 13B-1) ----
    rendered_dir = pkg_dir / "rendered"
    rendered_dir.mkdir(exist_ok=True)

    try:
        from cpswc.renderers.document import render_formal_tables, render_narrative_skeleton  # type: ignore
        snapshot_d = json.loads(snapshot_json)
        # Attach original facts for narrative projection + workbench
        snapshot_d["_original_facts"] = project_input.get("facts") or {}

        # 13B-1: formal tables
        docx_paths = render_formal_tables(
            snapshot=snapshot_d,
            frozen=frozen_dict,
            calc_results_dir=calc_dir,
            output_dir=rendered_dir,
        )
        for dp in docx_paths:
            rel = f"rendered/{dp.name}"
            content = dp.read_bytes()
            file_hashes[rel] = hashlib.sha256(content).hexdigest()

        # 13B-2: narrative skeleton
        skel_path = render_narrative_skeleton(
            snapshot=snapshot_d,
            frozen=frozen_dict,
            calc_results_dir=calc_dir,
            output_dir=rendered_dir,
        )
        rel = f"rendered/{skel_path.name}"
        file_hashes[rel] = hashlib.sha256(skel_path.read_bytes()).hexdigest()

    except Exception as e:
        import sys
        print(f"WARNING: DOCX rendering failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)

    # ---- Step 4: Write PACKAGE_MANIFEST.json ----
    package_manifest = {
        "_schema": "cpswc_submission_package_v0",
        "version_id": version.version_id,
        "frozen_input_hash": frozen.content_hash,
        "package_generated_at": datetime.now(timezone.utc).isoformat(),
        "project_summary": snapshot.project_input_summary,
        "ruleset": snapshot.ruleset,
        "lifecycle": snapshot.lifecycle,
        "files": {
            fname: {
                "sha256": fhash,
                "role": _file_role(fname),
            }
            for fname, fhash in sorted(file_hashes.items())
        },
        "file_count": len(file_hashes),
        "integrity_check": {
            "method": "sha256_per_file",
            "note": "Each file's sha256 is independently computed. "
                    "Verify by re-hashing the file content.",
        },
    }
    manifest_content = json.dumps(package_manifest, ensure_ascii=False,
                                  indent=2, sort_keys=False)
    (pkg_dir / "PACKAGE_MANIFEST.json").write_text(manifest_content, encoding="utf-8")

    return pkg_dir


def _file_role(fname: str) -> str:
    """给 PACKAGE_MANIFEST 里的每个文件标注角色"""
    roles = {
        "runtime_snapshot.json": "core_snapshot",
        "frozen_submission_input.json": "freeze_record",
        "submission_package_version.json": "version_record",
        "workbench.html": "visual_workbench",
    }
    if fname.startswith("manifests/"):
        return "manifest"
    if fname.startswith("calculator_results/"):
        return "calculator_detail"
    if fname.startswith("rendered/"):
        return "rendered_document"
    return roles.get(fname, "unknown")


# ============================================================
# CLI
# ============================================================

def _cli() -> int:
    import argparse
    parser = argparse.ArgumentParser(
        description="CPSWC v0 Submission Package Builder")
    parser.add_argument("input", nargs="?",
                        default=str(SAMPLES_DIR / "huizhou_housing_v0.json"),
                        help="项目 facts JSON 文件路径")
    parser.add_argument("-o", "--output", default=None,
                        help="输出目录 (默认: /tmp/cpswc_pkg_<hash>)")
    parser.add_argument("--previous-version", default=None,
                        help="上一个 version_id (用于版本链)")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: {input_path} not found", file=sys.stderr)
        return 2

    with input_path.open(encoding="utf-8") as f:
        project_input = json.load(f)

    # Default output dir
    if args.output:
        output_dir = Path(args.output)
    else:
        project_code = (project_input.get("facts") or {}).get(
            "field.fact.project.code", "unknown")
        safe_code = project_code.replace("/", "_").replace(" ", "_")[:40]
        output_dir = Path(f"/tmp/cpswc_pkg_{safe_code}")

    pkg_path = build_package(
        project_input,
        output_dir,
        previous_version_id=args.previous_version,
    )

    # Print summary
    manifest_path = pkg_path / "PACKAGE_MANIFEST.json"
    with manifest_path.open() as f:
        manifest = json.load(f)

    print("=" * 72)
    print(f" CPSWC Submission Package Built")
    print(f" Directory: {pkg_path}")
    print(f" Version:   {manifest['version_id']}")
    print(f" Hash:      {manifest['frozen_input_hash']}")
    print(f" Files:     {manifest['file_count']}")
    print("=" * 72)
    for fname, finfo in manifest["files"].items():
        print(f"  [{finfo['role']:20s}] {fname}")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
