# R4 — 산출물

## 실행 폴더

`runs/<YYYYMMDD-화면약칭>/`

| 파일 | 단계 | 형식 |
|---|---|---|
| research/s1-references.md | S1 | Markdown + frontmatter (예: `reference_count`) |
| research/s2-analysis.md | S2 | Markdown + frontmatter |
| spec/s3-spec.md | S3 | Markdown + frontmatter |
| design/s4-keyscreens.json | S4 | Figma 파일 키, 프레임 node id |
| design/figma-nodes.json | S4, S5 | Figma 노드 값 (판정 스크립트 입력) |
| design/s5-tokens.json | S5 | 디자인 토큰 |
| design/s5-report.json | S5 | 위반 리포트 (판정 스크립트가 생성) |
| state.json | 전체 | 현재 단계, 게이트 통과 기록, 게이트별 실패 횟수 |

하위 폴더는 R6 에이전트별 편집 폴더와 1:1로 대응합니다.

## 규칙 SSOT

- `rules/design-rules.json` 하나만 기준으로 삼음
- `r0-context.md`의 허용값 목록을 JSON으로 옮긴 것
- `design.md`는 사람이 읽는 원천이고, 스크립트와 에이전트는 JSON만 봄

## 이어서 하기

- 가능함. 다시 실행하면 `state.json`을 보고 마지막으로 통과한 게이트 다음 단계부터 시작
