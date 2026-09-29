"""에이전트 편집 폴더 경계 검사.

사용법:
    python scripts/check_scope.py snapshot <run-id> <agent>   # 에이전트 호출 전
    python scripts/check_scope.py verify   <run-id> <agent>   # 에이전트 호출 후

verify 출력: stdout에 JSON {"agent", "result", "outside", "inside"}
종료 코드: 0 = pass, 1 = fail (폴더 밖 변경 있음), 2 = 입력 오류

에이전트별 허용 폴더 (docs/r6-roles.md):
  researcher → runs/<id>/research/
  planner    → runs/<id>/spec/
  designer   → runs/<id>/design/
  judge      → 없음 (예외: design/s5-report.json, 판정 스크립트가 생성)
"""

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".scope"}
# Claude Code가 권한 "항상 허용" 선택을 기록하는 파일. 에이전트가 아니라 하네스가 바꾼다.
SKIP_FILES = {".claude/settings.local.json"}

ALLOWED = {
    "researcher": ["research/"],
    "planner": ["spec/"],
    "designer": ["design/"],
    "judge": [],
}
EXCEPTIONS = ["design/s5-report.json"]


def snapshot_files(base):
    result = {}
    for p in base.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(base)
        if any(part in SKIP_DIRS for part in rel.parts) or rel.as_posix() in SKIP_FILES:
            continue
        result[rel.as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    return result


def main(argv):
    if len(argv) != 4 or argv[1] not in ("snapshot", "verify") or argv[3] not in ALLOWED:
        print("사용법: python scripts/check_scope.py <snapshot|verify> <run-id> <"
              + "|".join(ALLOWED) + ">", file=sys.stderr)
        return 2
    mode, run_id, agent = argv[1:]
    # 보통은 프로젝트 전체를 검사한다. 절대 경로를 주면 그 폴더만 검사한다 (테스트용).
    if Path(run_id).is_absolute():
        scan_root = run_dir = Path(run_id)
    else:
        scan_root, run_dir = ROOT, ROOT / "runs" / run_id
    if not run_dir.is_dir():
        print(json.dumps({"result": "error", "reason": f"run 폴더 없음: {run_dir}"}, ensure_ascii=False))
        return 2
    scope_dir = run_dir / ".scope"
    snap_path = scope_dir / f"{agent}.json"

    if mode == "snapshot":
        scope_dir.mkdir(exist_ok=True)
        snap_path.write_text(json.dumps(snapshot_files(scan_root)), encoding="utf-8")
        print(json.dumps({"agent": agent, "result": "snapshot", "path": str(snap_path)}, ensure_ascii=False))
        return 0

    if not snap_path.exists():
        print(json.dumps({"result": "error", "reason": f"snapshot 없음: {snap_path}"}, ensure_ascii=False))
        return 2
    before = json.loads(snap_path.read_text(encoding="utf-8"))
    after = snapshot_files(scan_root)
    changed = sorted(k for k in set(before) | set(after)
                     if before.get(k) != after.get(k) and k not in SKIP_FILES)

    run_prefix = run_dir.relative_to(scan_root).as_posix()
    run_prefix = "" if run_prefix == "." else run_prefix + "/"
    allowed = [run_prefix + a for a in ALLOWED[agent]]
    exceptions = [run_prefix + e for e in EXCEPTIONS]

    inside, outside = [], []
    for path in changed:
        if path in exceptions or any(path.startswith(a) for a in allowed):
            inside.append(path)
        else:
            outside.append(path)

    result = "fail" if outside else "pass"
    print(json.dumps({"agent": agent, "result": result, "outside": outside, "inside": inside},
                     ensure_ascii=False))
    return 0 if result == "pass" else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # pyright: ignore[reportAttributeAccessIssue]
    sys.exit(main(sys.argv))
