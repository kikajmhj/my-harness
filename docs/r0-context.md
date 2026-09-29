# R0 — 준비물과 판정 기준 확인

## 컨텍스트 문서

| 파일 | 역할 |
|---|---|
| docs/prd.md | 서비스 원천 |
| docs/story-service.md | 판정 기준 (무엇을 위한 일인지) |
| docs/story-work.md | 작업 흐름 (실제로 어떻게 했는지) |
| docs/design.md | 디자인 규칙 원천 |

## 도구

- 하네스: Claude Code (CLAUDE.md)
- 레퍼런스: uibowl MCP
- 디자인: 공식 Figma MCP (use_figma), 새 파일

## design.md 해석 결정

- 그림자(box-shadow/effect)는 `segmented-control-active`에서만 허용하고, 그 밖의 곳은 위반
- Examples(`ex-*`) 섹션은 설명용이라 판정 기준에서 제외
- `{colors.on-primary}` = `#ffffff`

## 허용값 목록 (목록 밖의 값은 위반)

- 색: `#141414` `#262626` `#0066ff` `#ffffff` `#f3f3f3` `#f0f0f0` `#e0e0e0` `#707070` `#adadad` `rgba(115,115,115,0.56)`
- 모서리: `0` / `16` / `24` / `9999`px, 아이콘 squircle 30%
- 간격: `4` / `8` / `12` / `16` / `24` / `32` / `48` / `64`px
- 폰트: Pretendard만, 굵기 `300` / `400` / `600` / `700`, 자간 `0`
