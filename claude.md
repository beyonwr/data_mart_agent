# Data Mart Agent 프로젝트

## 프로젝트 개요

사내 데이터 마트에서 데이터를 수집하는 AI Agent 시스템입니다.

**핵심 설계 원칙**: Agent와 Tool Server는 **완전히 독립적인 컴포넌트**로 개발되며, MCP(Model Context Protocol)를 통해 느슨하게 결합됩니다.

- **Agent**: Google Agent Development Kit 기반, 사용자 요청 해석 및 응답 생성
- **Tool Server**: FastMCP 기반, 데이터 마트 API 래핑 및 MCP 프로토콜 구현
- **통신**: MCP 프로토콜을 통한 표준화된 인터페이스

## 기술 스택

- **Agent**: Google Agent Development Kit
- **Tool Server**: FastMCP
- **언어**: Python
- **데이터 처리**: pandas, parquet

## 프로젝트 구조

```
data_mart_agent/
├── agent/          # Google Agent Development Kit 기반 에이전트 (독립 실행)
├── tools/          # FastMCP 기반 도구 서버 (독립 실행)
├── reference.py    # 데이터 마트 API 레퍼런스
└── claude.md       # 이 파일
```

## 아키텍처

```
┌─────────────────┐         MCP Protocol        ┌──────────────────┐
│                 │◄──────────────────────────►│                  │
│  Agent          │   (표준 인터페이스)          │  Tool Server     │
│  (Google ADK)   │                             │  (FastMCP)       │
│                 │                             │                  │
└─────────────────┘                             └────────┬─────────┘
                                                          │
                                                          │ REST API
                                                          │
                                                   ┌──────▼─────────┐
                                                   │  Data Mart     │
                                                   │  Portal        │
                                                   └────────────────┘
```

### 독립적 개발 전략

1. **Tool Server 우선 개발**
   - 데이터 마트 API 클라이언트 구현
   - MCP 프로토콜로 tool 노출
   - 독립적으로 테스트 가능

2. **Agent 개발**
   - Tool Server와 무관하게 개발
   - MCP 클라이언트만 구현하면 연결 가능

3. **통합**
   - MCP 표준 프로토콜로 연결
   - 각 컴포넌트는 독립적으로 실행 및 배포

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

## 코딩 스타일

### 일반 원칙
- **PEP 8** 준수
- **타입 힌팅** 필수 사용 (`typing` 모듈)
- **명확한 변수명** 사용 (축약 지양)
- **한 함수는 한 가지 일만** (Single Responsibility)

### 네이밍 컨벤션
```python
# 변수, 함수: snake_case
user_id = "12345"
def get_token(user_id: str) -> str:
    pass

# 클래스: PascalCase
class DataMartClient:
    pass

# 상수: UPPER_SNAKE_CASE
DEFAULT_TIMEOUT = 30
API_VERSION = "v1"

# Enum: PascalCase (클래스), UPPER_SNAKE_CASE (멤버)
class DataOperator(Enum):
    EQUAL = "EQ"
    GREATER_THAN = "GT"
```

### 타입 힌팅
```python
from typing import Dict, List, Optional, Literal

# 함수 시그니처는 반드시 타입 명시
def get_data(
    program_id: str,
    token: str,
    filters: Optional[Dict[str, Dict[str, str]]] = None
) -> pd.DataFrame:
    pass

# 복잡한 타입은 TypeAlias 사용
FilterDict = Dict[str, Dict[str, str]]
```

### 에러 핸들링
```python
# 명시적인 예외 처리
try:
    response = requests.post(url, json=data, timeout=30)
    response.raise_for_status()
except requests.HTTPError as e:
    logger.error(f"API request failed: {e}")
    raise
except requests.Timeout:
    logger.error("Request timeout")
    raise

# API 응답은 항상 검증
if response.json().get("code") != 200:
    raise DataMartAPIError(response.json().get("message"))
```

### 데이터 처리
```python
# Pandas DataFrame은 타입 명시
import pandas as pd

def process_data(df: pd.DataFrame) -> pd.DataFrame:
    # 컬럼 존재 여부 검증
    required_columns = ["col1", "col2"]
    missing = set(required_columns) - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    return df

# Parquet 파일은 메타데이터 명시
df.to_parquet("output.parquet", compression="snappy", index=False)
```

### API 클라이언트
```python
# 세션 재사용
class DataMartClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.session.close()

# 타임아웃 필수 설정
response = self.session.get(url, timeout=30)
```

### MCP Tool 정의
```python
# Tool은 명확한 이름과 설명 작성
@mcp.tool()
def get_datamart_data(
    program_id: str,
    start_date: str,
    end_date: str
) -> dict:
    """
    데이터 마트에서 특정 기간의 데이터를 조회합니다.

    Args:
        program_id: 프로그램 ID (예: "JN00000")
        start_date: 시작일 (ISO 8601 형식)
        end_date: 종료일 (ISO 8601 형식)

    Returns:
        조회된 데이터 레코드 딕셔너리
    """
    pass
```

### 문서화
```python
# 모듈 docstring 필수
"""
Data Mart API 클라이언트 모듈.

사내 데이터 마트와 통신하여 데이터를 조회하고 필터링하는 기능을 제공합니다.
"""

# 복잡한 로직에는 주석 추가
# 단, 코드만으로 명확하면 주석 생략
```

## 개발 가이드

### Tool Server 개발 (우선 개발)

**목표**: Agent와 독립적으로 동작하는 MCP Tool Server 구현

- FastMCP로 독립 실행 가능한 MCP 서버 구현
- 데이터 마트 REST API를 MCP tool로 래핑
- 주요 기능:
  - `authenticate`: 사용자 인증 및 토큰 발급
  - `get_data`: 프로그램 데이터 조회
  - `get_metadata`: 컬럼 메타데이터 조회
  - `create_filter`: 동적 필터 생성
- **독립 테스트**: MCP Inspector 또는 CLI로 단독 테스트 가능

### Agent 개발 (후속 개발)

**목표**: Tool Server와 독립적으로 동작하는 Agent 구현

- Google Agent Development Kit 사용
- 사용자 자연어 요청을 해석하여 적절한 tool 호출
- MCP 클라이언트 통해 Tool Server와 통신
- Tool Server의 구현 세부사항 몰라도 됨 (MCP 인터페이스만 알면 됨)

### 통합

- Agent와 Tool Server는 각각 독립 프로세스로 실행
- MCP 프로토콜로 통신 (stdio 또는 HTTP)
- 각 컴포넌트는 독립적으로 업데이트/배포 가능

## TODO

- [ ] FastMCP 기반 Tool 서버 구현
- [ ] Google Agent Development Kit 기반 Agent 구현
- [ ] Agent와 Tool 연결
- [ ] 테스트 및 문서화
