"""허들링 디자인 하네스 판정 스크립트.

사용법:
    python scripts/gate.py <G1|G2|G3|G5> <run-id 또는 run 폴더 경로>

출력: stdout에 JSON 한 개 {"gate", "result", "reasons", "stats"}
종료 코드: 0 = pass, 1 = fail, 2 = 입력 오류

입력 형식 (에이전트가 지켜야 함):
  state.json                 {"screens": ["home", "my-assets"], ...}
  research/s1-references.md  - [R-01] screen: home | app: Toss | url: https://uibowl.io/... | note: ...
  research/s2-analysis.md    - [A-01] screen: home | refs: R-01, R-03 | story: 2 | item: ...
  spec/s3-spec.md            ## screen: home  /  - component: button-primary
                             "판매 신청"이 들어간 줄은 같은 줄에 "role: seller"가 있어야 함 (★A)
  design/figma-nodes.json    {"frames": [{id,name,width,height}],
                              "nodes": [{id,frame,name,type,component,width,height,fills,strokes,
                                         cornerRadius,itemSpacing,padding,fontFamily,fontWeight,
                                         letterSpacing,effects,characters}]}
G5는 결과를 design/s5-report.json에도 쓴다.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RULES_PATH = ROOT / "rules" / "design-rules.json"
STORY_PATH = ROOT / "docs" / "story-service.md"

REF_LINE = re.compile(
    r"^- \[(R-\d+)\]\s*screen:\s*(\S+)\s*\|\s*app:\s*(.+?)\s*\|\s*url:\s*(\S*)"
)
ANALYSIS_LINE = re.compile(
    r"^- \[(A-\d+)\]\s*screen:\s*(\S+)\s*\|\s*refs:\s*([^|]*)\|\s*story:\s*([^|]*)\|"
)
SPEC_SECTION = re.compile(r"^## screen:\s*(\S+)")
SPEC_COMPONENT = re.compile(r"^- component:\s*(\S+)")
RGBA = re.compile(r"rgba?\(([^)]*)\)")


class InputError(Exception):
    pass


def load_json(path):
    if not path.exists():
        raise InputError(f"파일 없음: {path}")
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def read_text(path):
    if not path.exists():
        raise InputError(f"파일 없음: {path}")
    return path.read_text(encoding="utf-8")


def resolve_run(arg):
    p = Path(arg)
    if p.is_dir():
        return p.resolve()
    p = ROOT / "runs" / arg
    if p.is_dir():
        return p
    raise InputError(f"run 폴더 없음: {arg}")


def target_screens(run):
    screens = load_json(run / "state.json").get("screens") or []
    if not screens:
        raise InputError("state.json에 screens가 비어 있음")
    return screens


def story_numbers():
    nums = set()
    in_table = False
    for line in read_text(STORY_PATH).splitlines():
        if line.startswith("## "):
            in_table = line.strip() == "## 유저스토리"
            continue
        m = re.match(r"^\|\s*(\d+)\s*\|", line)
        if in_table and m:
            nums.add(int(m.group(1)))
    if not nums:
        raise InputError("story-service.md에서 유저스토리 번호를 찾지 못함")
    return nums


def parse_references(run):
    refs = []
    for line in read_text(run / "research" / "s1-references.md").splitlines():
        m = REF_LINE.match(line.strip())
        if m:
            refs.append({"id": m.group(1), "screen": m.group(2), "url": m.group(4)})
    return refs


# ---------------------------------------------------------------- G1

def gate_g1(run, rules):
    cfg = rules["gates"]["G1"]
    screens = target_screens(run)
    refs = parse_references(run)
    reasons = []

    ids = [r["id"] for r in refs]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        reasons.append(f"레퍼런스 ID 중복: {', '.join(dupes)}")

    per_screen = {s: 0 for s in screens}
    for r in refs:
        if r["screen"] in per_screen:
            per_screen[r["screen"]] += 1
        if cfg["url_must_contain"] not in r["url"]:
            reasons.append(f"{r['id']}: uibowl 링크 없음")
    for s, n in per_screen.items():
        if n < cfg["min_references_per_screen"]:
            reasons.append(f"{s}: 레퍼런스 {n}개 (최소 {cfg['min_references_per_screen']}개)")

    return reasons, {"references": len(refs), "per_screen": per_screen}


# ---------------------------------------------------------------- G2

def gate_g2(run, rules):
    cfg = rules["gates"]["G2"]
    screens = target_screens(run)
    ref_ids = {r["id"] for r in parse_references(run)}
    valid_stories = story_numbers()
    reasons = []
    per_screen = {s: 0 for s in screens}
    orphans = 0
    items = 0

    for line in read_text(run / "research" / "s2-analysis.md").splitlines():
        m = ANALYSIS_LINE.match(line.strip())
        if not m:
            continue
        items += 1
        aid, screen, refs_raw, story_raw = m.groups()
        if screen in per_screen:
            per_screen[screen] += 1
        refs = [x.strip() for x in refs_raw.split(",") if x.strip()]
        missing = [x for x in refs if x not in ref_ids]
        story = story_raw.strip()
        broken = []
        if not refs:
            broken.append("레퍼런스 연결 없음")
        if missing:
            broken.append(f"s1에 없는 레퍼런스 {', '.join(missing)}")
        if not story.isdigit() or int(story) not in valid_stories:
            broken.append(f"유효하지 않은 유저스토리 번호 '{story}'")
        if broken:
            orphans += 1
            reasons.append(f"{aid}: {'; '.join(broken)}")

    for s, n in per_screen.items():
        if n < cfg["min_items_per_screen"]:
            reasons.append(f"{s}: 반영 항목 {n}개 (최소 {cfg['min_items_per_screen']}개)")

    return reasons, {"items": items, "orphans": orphans, "per_screen": per_screen}


# ---------------------------------------------------------------- G3

def gate_g3(run, rules):
    cfg = rules["gates"]["G3"]
    screens = target_screens(run)
    allowed = set(rules["components"])
    reasons = []
    sections = {}
    current = None
    sale_lines = 0
    sale_ok = 0

    for no, line in enumerate(read_text(run / "spec" / "s3-spec.md").splitlines(), 1):
        m = SPEC_SECTION.match(line.strip())
        if m:
            current = m.group(1)
            sections.setdefault(current, [])
            continue
        m = SPEC_COMPONENT.match(line.strip())
        if m and current:
            sections[current].append(m.group(1))
            if m.group(1) not in allowed:
                reasons.append(f"{current}: 규칙에 없는 컴포넌트 '{m.group(1)}' ({no}행)")
        if cfg["sale_keyword"] in line:
            sale_lines += 1
            if cfg["seller_marker"] in line:
                sale_ok += 1
            else:
                reasons.append(f"★A {no}행: '{cfg['sale_keyword']}'에 '{cfg['seller_marker']}' 조건 없음")

    for s in screens:
        if s not in sections:
            reasons.append(f"{s}: 설계 섹션 없음 ('## screen: {s}')")
        elif not sections[s]:
            reasons.append(f"{s}: 컴포넌트가 하나도 없음")

    return reasons, {"sections": list(sections), "sale_lines": sale_lines, "sale_with_seller": sale_ok}


# ---------------------------------------------------------------- G5

def norm_color(value):
    v = str(value).strip().lower().replace(" ", "")
    m = RGBA.fullmatch(v)
    if m:
        parts = m.group(1).split(",")
        if len(parts) == 4 and float(parts[3]) >= 1:
            parts = parts[:3]
        if len(parts) == 3:
            return "#" + "".join(f"{int(float(p)):02x}" for p in parts)
        a = f"{float(parts[3]):g}"
        return f"rgba({int(float(parts[0]))},{int(float(parts[1]))},{int(float(parts[2]))},{a})"
    if re.fullmatch(r"#[0-9a-f]{3}", v):
        v = "#" + "".join(c * 2 for c in v[1:])
    return v


def check_node(node, rules, violations):
    nid = node.get("id", "?")
    comp = node.get("component")
    allowed_colors = {norm_color(c) for c in rules["colors"].values()}
    accent = norm_color(rules["colors"]["accent"])

    def add(kind, detail):
        violations.append({"node": nid, "frame": node.get("frame"), "kind": kind, "detail": detail})

    for key in ("fills", "strokes"):
        for c in node.get(key) or []:
            nc = norm_color(c)
            if nc not in allowed_colors:
                add("color", f"{key} {c}")
            if nc == accent and comp in rules["accent"]["forbidden_components"]:
                add("accent", f"{comp}에 accent 사용")

    r = node.get("cornerRadius")
    if r is not None:
        rc = rules["radius"]
        ok = r in rc["allowed"]
        if not ok and comp == rc["squircle_component"] and node.get("width"):
            ok = abs(r - node["width"] * rc["squircle_ratio"]) <= rc["squircle_tolerance"]
        if not ok:
            add("radius", f"cornerRadius {r}")

    spacing = []
    if node.get("itemSpacing") is not None:
        spacing.append(node["itemSpacing"])
    spacing.extend(node.get("padding") or [])
    for s in spacing:
        if s not in rules["spacing"]["allowed"]:
            add("spacing", f"간격 {s}")

    if node.get("type") == "TEXT":
        f = rules["font"]
        if node.get("fontFamily") not in f["families"]:
            add("font", f"폰트 {node.get('fontFamily')}")
        if node.get("fontWeight") not in f["weights"]:
            add("font", f"굵기 {node.get('fontWeight')}")
        if (node.get("letterSpacing") or 0) not in f["letter_spacing"]:
            add("font", f"자간 {node.get('letterSpacing')}")
        text = node.get("characters") or ""
        for name, pat in rules["pii_patterns"].items():
            if re.search(pat, text):
                add("pii", f"★B {name} 형식 발견")

    for e in node.get("effects") or []:
        etype = e.get("type") if isinstance(e, dict) else e
        if etype in rules["shadow"]["effect_types"] and comp not in rules["shadow"]["allowed_components"]:
            add("shadow", f"{etype}")


def gate_g5(run, rules):
    screens = target_screens(run)
    data = load_json(run / "design" / "figma-nodes.json")
    frames = data.get("frames") or []
    nodes = data.get("nodes") or []
    reasons = []
    violations = []

    fw, fh = rules["frame"]["width"], rules["frame"]["height"]
    if len(frames) != len(screens):
        reasons.append(f"프레임 {len(frames)}개, 대상 화면 {len(screens)}개")
    frame_names = {f.get("name") for f in frames}
    for s in screens:
        if s not in frame_names:
            reasons.append(f"{s}: 프레임 없음")
    for f in frames:
        if (f.get("width"), f.get("height")) != (fw, fh):
            reasons.append(f"프레임 {f.get('name')}: {f.get('width')}×{f.get('height')} ({fw}×{fh} 아님)")

    for n in nodes:
        check_node(n, rules, violations)

    accent = norm_color(rules["colors"]["accent"])
    per_frame = {}
    for n in nodes:
        if any(norm_color(c) == accent for c in n.get("fills") or []):
            per_frame[n.get("frame")] = per_frame.get(n.get("frame"), 0) + 1
    for fr, cnt in per_frame.items():
        if cnt > rules["accent"]["max_per_frame"]:
            violations.append({"node": None, "frame": fr, "kind": "accent",
                               "detail": f"accent {cnt}개 (최대 {rules['accent']['max_per_frame']}개)"})

    kinds = {}
    for v in violations:
        kinds[v["kind"]] = kinds.get(v["kind"], 0) + 1
    for k, cnt in sorted(kinds.items()):
        reasons.append(f"{k} 위반 {cnt}건")

    stats = {"frames": len(frames), "nodes": len(nodes), "violations": len(violations), "by_kind": kinds}
    report = {"stats": stats, "reasons": reasons, "violations": violations}
    (run / "design" / "s5-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return reasons, stats


GATES = {"G1": gate_g1, "G2": gate_g2, "G3": gate_g3, "G5": gate_g5}


def main(argv):
    if len(argv) != 3 or argv[1] not in GATES:
        print("사용법: python scripts/gate.py <G1|G2|G3|G5> <run-id|run 경로>", file=sys.stderr)
        return 2
    gate = argv[1]
    try:
        run = resolve_run(argv[2])
        rules = load_json(RULES_PATH)
        reasons, stats = GATES[gate](run, rules)
    except (InputError, json.JSONDecodeError) as e:
        print(json.dumps({"gate": gate, "result": "error", "reasons": [str(e)]}, ensure_ascii=False))
        return 2
    result = "fail" if reasons else "pass"
    print(json.dumps({"gate": gate, "result": result, "reasons": reasons, "stats": stats},
                     ensure_ascii=False))
    return 0 if result == "pass" else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # pyright: ignore[reportAttributeAccessIssue]
    sys.exit(main(sys.argv))
