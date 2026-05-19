# kis-mcp

한국투자증권 Open API를 Claude Desktop에 연결하는 MCP 서버

## 파일 구성

| 파일 | 설명 |
|------|------|
| `kis_mcp_server.py` | stdio 방식 — 로컬 비상용 (claude_desktop_config.json 등록) |
| `kis_mcp_server_sse.py` | SSE 방식 — 클램쉘 메인 서버용 (Cloudflare Tunnel + HTTPS 예정) |
| `kis-enable.sh` | Claude Desktop에 KIS MCP 활성화 |
| `kis-disable.sh` | Claude Desktop에서 KIS MCP 비활성화 |

## 사전 준비

- WSL Ubuntu + Python 3.12
- [koreainvestment/open-trading-api](https://github.com/koreainvestment/open-trading-api) 클론 및 `uv sync` 완료
- `~/KIS/config/kis_devlp.yaml` — KIS API 키 설정

## 사용법 (로컬 비상용)

**활성화**
```bash
~/open-trading-api/kis-enable.sh
# → Claude Desktop 재시작
```

**비활성화**
```bash
~/open-trading-api/kis-disable.sh
# → Claude Desktop 재시작
```

## 제공 기능

해외주식 전용 (`function` 파라미터로 지정)

| 카테고리 | function |
|----------|----------|
| 시세 조회 | `price`, `price_detail`, `dailyprice` |
| 차트 분석 | `chart_daily`, `chart_minute` |
| 계좌/잔고 | `balance`, `present_balance`, `period_trans`, `period_profit` |
| 시장 분석 | `volume_surge`, `price_fluct`, `updown_rate`, `market_cap` |
| 종목 정보 | `search_info`, `news` |

거래소 코드: `NAS`(나스닥), `NYS`(뉴욕), `AMS`(아멕스)

## 관련 경로 (ASUS Zenbook WSL)

```
~/open-trading-api/          ← 모든 파일 통합 폴더
├── kis_mcp_server.py
├── kis_mcp_server_sse.py
├── kis-enable.sh
├── kis-disable.sh
├── examples_llm/            ← KIS API 모듈
└── .venv/                   ← Python 패키지

~/KIS/config/kis_devlp.yaml  ← API 키 (git 제외)
```
