#!/usr/bin/env python3
"""Inventory a pinned CCGS commit; never rewrite or execute its contents.

This is a migration-design audit, not a Claude-to-Codex converter. It uses only
Python's standard library and Git. Marker matches are lexical candidates;
comments, examples, and historical documentation can legitimately match.
"""

import argparse
import collections
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess


DEFAULT_BASE = "be8993bbc5a1f016bc770b2846ce06272d284526"
PATTERNS = {
    "claude_path": r"\.claude/",
    "claude_instruction_file": r"CLAUDE(?:\.local)?\.md",
    "claude_environment": r"\bCLAUDE_[A-Z0-9_]+",
    "shell_preprocessing_candidate": r"^\s*!`",
    "argument_macro": r"\$ARGUMENTS|\$\{ARGUMENTS\}",
    "task_tool_name": r"\bTask(?:Create|Get|List|Update)\b",
    "ask_user_tool_name": r"\bAskUserQuestion\b",
    "subagent_type": r"\bsubagent_type\b",
    "at_path_import_candidate": r"^@(?:\.claude/|docs/|design/|src/)",
}


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args])


def disposition(path):
    """Return proposed targets only; no paths are created by this function."""
    p = PurePosixPath(path)
    if p.name == "CLAUDE.md":
        return "add_codex_entry", [str(p.with_name("AGENTS.md"))], "D01"
    if path == ".claude/settings.json":
        return "split_configuration", [
            ".codex/config.toml", ".codex/hooks.json", ".codex/rules/studio.rules"
        ], "D06"
    if path.startswith(".claude/agents/"):
        return "convert_agent", [".codex/agents/" + p.stem + ".toml"], "D02"
    if path.startswith(".claude/skills/"):
        return "port_skill_bundle", [path.replace(".claude/skills/", ".agents/skills/", 1)], "D03"
    if path.startswith(".claude/rules/"):
        return "port_scoped_guidance", [path.replace(".claude/rules/", "docs/studio/rules/", 1)], "D04"
    if path.startswith(".claude/hooks/"):
        if p.name in ("notify.sh", "log-instructions.sh"):
            return "retain_claude_only_document_gap", [], "D05"
        if p.name == "yaml-helper.sh":
            return "port_config_helper", ["scripts/studio/yaml-helper.sh"], "D07"
        return "port_hook_contract", [".codex/hooks/" + p.name], "D05"
    if path.startswith(".claude/scripts/"):
        return "reuse_helper_adapt_paths", [path.replace(".claude/scripts/", "scripts/studio/", 1)], "D07"
    if path == ".claude/statusline.sh":
        return "adapt_to_explicit_status_command", ["scripts/studio/status.sh"], "D06"
    if path.startswith(".claude/docs/"):
        renames = {
            ".claude/docs/CLAUDE-local-template.md": "docs/studio/codex-local-preferences.md",
            ".claude/docs/settings-local-template.md": "docs/studio/codex-settings-guide.md",
        }
        return "reuse_reference_adapt_semantics", [renames.get(path, path.replace(".claude/docs/", "docs/studio/", 1))], "D08"
    if path.startswith("CCGS Skill Testing Framework/"):
        return "keep_spec_adapt_host_assertions", [path], "D10"
    if path in ("project.yaml",) or path.startswith(("production/", "design/", "src/")):
        return "keep_project_asset", [path], "D09"
    if path.startswith("docs/"):
        return "keep_document_review_cross_references", [path], "D09"
    if path in (".gitignore", ".gitattributes") or path.startswith(".github/"):
        return "review_repository_metadata", [path], "D11"
    if path == "LICENSE":
        return "preserve_license", [path], "D11"
    if path == "CHANGELOG.md":
        return "preserve_history_append_migration", [path], "D11"
    return "review_root_documentation", [path], "D11"


def inventory(repo, baseline):
    commit = git(repo, "rev-parse", "--verify", baseline + "^{commit}").decode().strip()
    raw_tree = git(repo, "ls-tree", "-rz", "--full-tree", commit)
    entries = []
    for record in raw_tree.split(b"\0"):
        if not record:
            continue
        metadata, name = record.split(b"\t", 1)
        mode, kind, oid = metadata.decode().split()
        if kind != "blob":
            raise ValueError("Unsupported source entry type: " + kind)
        entries.append((name.decode("utf-8"), mode, oid))
    entries.sort()

    # One Git process, framed by byte length; avoids shell interpolation and
    # supports filenames containing spaces (the existing test framework does).
    queries = "".join(oid + "\n" for _, _, oid in entries).encode()
    proc = subprocess.run(["git", "-C", str(repo), "cat-file", "--batch"],
                          input=queries, capture_output=True, check=True)
    cursor = 0
    rows = []
    marker_files = collections.Counter()
    marker_lines = collections.Counter()
    for path, mode, oid in entries:
        end = proc.stdout.index(b"\n", cursor)
        got_oid, kind, size = proc.stdout[cursor:end].decode().split()
        if got_oid != oid or kind != "blob":
            raise ValueError("Unexpected Git batch response for " + path)
        cursor = end + 1
        data = proc.stdout[cursor:cursor + int(size)]
        cursor += int(size) + 1
        content = data.decode("utf-8-sig")
        action, targets, section = disposition(path)
        markers = {}
        for label, regex in PATTERNS.items():
            hits = [i for i, line in enumerate(content.splitlines(), 1)
                    if re.search(regex, line)]
            if hits:
                markers[label] = hits
                marker_files[label] += 1
                marker_lines[label] += len(hits)
        row = {
            "source": path, "git_mode": mode, "git_blob": oid,
            "sha256": hashlib.sha256(data).hexdigest(),
            "action": action, "proposed_targets": targets,
            "design_section": section,
            "status": "planned_not_implemented",
        }
        if content.startswith("---\n"):
            # Preserve raw metadata values; do not pretend to be a YAML parser.
            fm = content.split("---", 2)[1]
            fields = dict(re.findall(r"^([A-Za-z][\w-]*):[ \t]*(.*)$", fm, re.M))
            row["frontmatter_fields_raw"] = fields
        if markers:
            row["lexical_marker_lines"] = markers
        rows.append(row)

    def count(prefix, suffix=""):
        return sum(r["source"].startswith(prefix) and r["source"].endswith(suffix) for r in rows)

    settings = json.loads(git(repo, "show", commit + ":.claude/settings.json"))
    return {
        "schema_version": 1,
        "purpose": "Proposed directory migration inventory; not an executable converter or runtime compatibility result.",
        "source_repository": "https://github.com/Donchitos/Claude-Code-Game-Studios",
        "target_repository": "https://github.com/flybirdxx/Claude-Code-Game-Studios",
        "baseline_commit": commit,
        "baseline_tree": git(repo, "rev-parse", commit + "^{tree}").decode().strip(),
        "scope": "Every tracked blob at the baseline commit; no generated migration files or local user state.",
        "transition_policy": "Add Codex counterparts and preserve Claude source until explicit cutover; shared assets remain in place.",
        "marker_warning": "Lexical candidates include comments, code examples, and history. They are not confirmed defects or automatic replacement instructions.",
        "counts": {
            "tracked_files": len(rows),
            "agents": count(".claude/agents/", ".md"),
            "skills": count(".claude/skills/", "/SKILL.md"),
            "skill_bundle_files": count(".claude/skills/"),
            "scoped_rules": count(".claude/rules/"),
            "hook_directory_files": count(".claude/hooks/"),
            "registered_hook_events": len(settings["hooks"]),
            "registered_hook_handlers": sum(len(g["hooks"]) for groups in settings["hooks"].values() for g in groups),
            "helper_scripts": count(".claude/scripts/"),
            "framework_reference_files": count(".claude/docs/"),
            "skill_test_framework_files": count("CCGS Skill Testing Framework/"),
            "nested_and_root_instruction_files": sum(PurePosixPath(r["source"]).name == "CLAUDE.md" for r in rows),
        },
        "action_counts": dict(sorted(collections.Counter(r["action"] for r in rows).items())),
        "lexical_marker_counts": {k: {"files": marker_files[k], "lines": marker_lines[k]} for k in PATTERNS},
        "registered_hook_events": list(settings["hooks"]),
        "files": rows,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--baseline", default=DEFAULT_BASE)
    parser.add_argument("--output", type=Path, help="Write JSON here; otherwise print to stdout.")
    args = parser.parse_args()
    result = inventory(args.repo, args.baseline)
    encoded = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8", newline="\n")
        print(json.dumps(result["counts"], ensure_ascii=False))
    else:
        print(encoded, end="")


if __name__ == "__main__":
    main()
