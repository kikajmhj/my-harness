# R6 — 역할

## 에이전트와 편집 폴더

| 에이전트 | 맡는 단계 | 편집 폴더 |
|---|---|---|
| `researcher` | S1, S2 | `runs/<id>/research/` |
| `planner` | S3 | `runs/<id>/spec/` |
| `designer` | S4, S5 제작 | `runs/<id>/design/` (Figma 쓰기 포함) |
| `judge` | G1~G3, G5 판정 | 없음 (읽기전용) |
| 오케스트레이터 (메인 세션) | 진행 관리 | `runs/<id>/state.json`만 |

## 판정자 (judge)

- 쓸 수 있는 도구: Read, Grep, `scripts/` 안의 판정 스크립트 실행
- 막는 도구: Edit, Write, Figma 쓰기
- 돌려주는 것: `pass` / `fail`과 fail 사유 목록 (기록은 오케스트레이터가 함)

## Figma 값을 스크립트로 넘기는 방법

- `designer`가 S4, S5 끝에 `design/figma-nodes.json`을 내보냄 (색, 모서리, 간격, 폰트, 효과, 텍스트)
- `scripts/gate.py <G1|G2|G3|G5> <run-id>`가 이 파일을 `rules/design-rules.json`과 비교 (Python)

## 자연어 트리거

| 이렇게 말하면 | 동작 |
|---|---|
| "화면 작업 시작: <화면들> / 키워드: <키워드>" | 새 run을 만들고 S1부터 |
| "이어서 해줘" | `state.json`을 보고 이어서 |
| "G4 승인" / "G4 반려: <사유>" | 기록한 뒤 S5로 가거나 S3로 돌아감 |
| "검토만 돌려줘" | G5 판정만 실행 |
