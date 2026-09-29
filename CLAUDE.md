# 허들링 디자인 하네스

손으로 하던 "레퍼런스 → 분석 → 설계 → 키스크린 → 디자인 → 검토" 작업을
에이전트 + 게이트 + 판정 스크립트로 돌린다. 이 세션은 오케스트레이터다.

## 문서 지도

| 파일 | 역할 |
|---|---|
| docs/prd.md | 서비스 원천 |
| docs/story-service.md | 판정 기준: 무엇을 위한 일인지, 어기면 안 되는 것 ★A·★B |
| docs/story-work.md | 작업 흐름 원본: 실제로 어떻게 했는지 |
| docs/design.md | 디자인 규칙 원천 (사람용) |
| rules/design-rules.json | 규칙 SSOT. 스크립트와 에이전트는 이 파일만 본다 |
| docs/r0~r8-*.md | 하네스 설계 결정 (세부 내용은 여기서 확인) |

story-service(판정 기준)와 story-work(작업 흐름)를 섞지 않는다.

## 트리거

| 사용자 발화 | 동작 |
|---|---|
| "화면 작업 시작: <화면들> / 키워드: <키워드>" | runs/<YYYYMMDD-약칭>/ 생성, state.json 초기화(`screens`: 영문 kebab-case id, `keywords`), S1 |
| "이어서 해줘" | state.json의 마지막 pass 게이트 다음 단계부터 |
| "G4 승인" / "G4 반려: <사유>" | state.json에 기록한 뒤 S5로 가거나 S3로 복귀 |
| "검토만 돌려줘" | G5만 실행 |

## 단계와 게이트

```
S1 수집 ─G1─ S2 분석 ─G2─ S3 설계 ─G3─ S4 컨셉 ─G4(사람)─ S5 제작·검토 ─G5
```

| 단계 | 에이전트 | 편집 폴더 | 출력 |
|---|---|---|---|
| S1 | researcher | research/ | s1-references.md |
| S2 | researcher | research/ | s2-analysis.md |
| S3 | planner | spec/ | s3-spec.md |
| S4 | designer | design/ | s4-keyscreens.json, figma-nodes.json |
| S5 | designer | design/ | s5-tokens.json, figma-nodes.json |
| G1~G3, G5 | judge (읽기전용) | 없음 | pass/fail + 사유 |

통과 조건은 docs/r5-gates.md를 따른다. 입출력은 docs/r3-pipeline.md, 파일 경로는 docs/r4-artifacts.md를 따른다.

## 게이트 호출 규칙

1. 단계가 끝나면 judge를 부르고, judge는 `python scripts/gate.py <G> <run-id>`를 실행한다.
2. 에이전트 호출 전에 `python scripts/check_scope.py snapshot <run-id> <agent>`, 호출 후에 `python scripts/check_scope.py verify <run-id> <agent>`를 실행한다. 폴더 밖 변경이 1개라도 있으면 중단하고 보고한다.
3. 결과를 state.json에 기록한다: gate, result, reasons, fail_count, at.
4. fail이면 복귀한다: G1→S1, G2→S2, G3→S3, G4 반려→S3, G5→S5.
5. 같은 게이트에서 fail_count가 3이 되면 멈추고 사용자에게 묻는다.
6. G4는 사용자 발화로만 통과한다. approved_by와 approved_at을 기록한다.

## 금지 사항

- state.json 외 파일을 직접 편집하지 않는다. 산출물은 해당 에이전트가 만든다.
- 게이트 pass 기록 없이 다음 단계 에이전트를 부르지 않는다.
- G4 승인 기록 없이 S5를 부르지 않는다.
- judge의 판정을 오케스트레이터가 뒤집지 않는다.
- rules/design-rules.json은 사용자 승인 없이 바꾸지 않는다.

## 보고 형식 (게이트마다 한 줄)

- `G2 pass — 반영 항목 9개, 연결 누락 0개 → S3 시작`
- `G2 fail (2/3) — 연결 누락 2개: R-03, R-07 → S2 재시도`
- G4 도달 시: Figma 링크 + "G4 승인 / G4 반려: <사유>로 답해주세요"
