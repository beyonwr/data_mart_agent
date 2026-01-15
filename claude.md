# Data Mart Agent 프로젝트

## 프로젝트 개요

사내 데이터 마트에서 데이터를 수집하는 AI Agent 시스템입니다.
Google Agent Development Kit를 활용한 Agent와 FastMCP를 활용한 Tool을 분리하여 개발합니다.

## 기술 스택

- **Agent**: Google Agent Development Kit
- **Tool Server**: FastMCP
- **언어**: Python
- **데이터 처리**: pandas, parquet

## 프로젝트 구조

```
data_mart_agent/
├── agent/          # Google Agent Development Kit 기반 에이전트
├── tools/          # FastMCP 기반 도구 서버
├── reference.py    # 데이터 마트 API 레퍼런스
└── claude.md       # 이 파일
```

## 데이터 마트 API

### 인증
- 엔드포인트: `POST /v1/signin`
- 필요 정보: `user_id`
- 반환: Bearer 토큰

### 데이터 조회
- **파일 방식**: `GET /v1/info/join_file/{program_id}` → Parquet 파일 다운로드
- **동적 조회**: `POST /v1/datas/join/dynamic/exporter` → 필터링된 데이터 직접 반환
- **메타데이터**: 컬럼 정보 조회 가능

### 필터링
필터는 다음 형식으로 구성:
```python
{
    "column_name": {
        "data_value": "값",
        "data_type": "VARCHAR|DOUBLE|BIGINT|DATE|TIMESTAMP",
        "data_operator": "EQ|IN|BETWEEN|GT|LT|LIKE 등"
    }
}
```

## 환경 변수

```
DATA_MART_URL=      # 데이터 마트 포털 URL
USER_ID=            # 사용자 ID
PROGRAM_ID=         # 프로그램 ID
JOB_ID=             # 작업 ID
```

## 개발 가이드

### Agent 개발 (예정)
- Google Agent Development Kit 사용
- 사용자 요청 해석 및 처리
- Tool 서버 호출

### Tool 개발 (예정)
- FastMCP로 MCP 서버 구현
- 데이터 마트 API를 MCP 툴로 래핑
- 주요 기능:
  - 인증 토큰 관리
  - 데이터 조회
  - 메타데이터 조회
  - 필터 생성 및 적용

## TODO

- [ ] FastMCP 기반 Tool 서버 구현
- [ ] Google Agent Development Kit 기반 Agent 구현
- [ ] Agent와 Tool 연결
- [ ] 테스트 및 문서화
