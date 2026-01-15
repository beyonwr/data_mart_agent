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
├── agent/          # Google Agent Development Kit 기반 에이전트 (개발 예정)
├── tools/          # FastMCP 기반 도구 서버 (✅ 이미 구현됨)
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

### 개발 전제

- **Tool Server**: ✅ 이미 구현 완료 (동료 작업)
  - FastMCP 기반 MCP 서버로 데이터 마트 API 래핑
  - MCP 프로토콜로 tool 노출
  - 독립 프로세스로 실행 가능

- **Agent**: 🔄 개발 예정 (현재 작업)
  - Tool Server의 MCP 인터페이스를 활용
  - 구현 세부사항 몰라도 됨 (MCP 프로토콜만 준수)

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

### Tool Server (이미 구현됨)

Tool Server는 동료가 이미 구현 완료했으며, 다음 기능을 MCP tool로 제공합니다:

- `authenticate`: 사용자 인증 및 토큰 발급
- `get_data`: 프로그램 데이터 조회
- `get_metadata`: 컬럼 메타데이터 조회
- `create_filter`: 동적 필터 생성

**사용법**: Tool Server를 독립 프로세스로 실행하고 MCP 프로토콜로 연결

### Agent 개발 (현재 작업)

**목표**: Tool Server를 활용하여 데이터 마트 쿼리를 처리하는 AI Agent 구현

#### 핵심 요구사항

1. **Google Agent Development Kit 활용**
   - Agent 초기화 및 설정
   - 대화 흐름 관리

2. **MCP 클라이언트 구현**
   - Tool Server와 MCP 프로토콜로 통신
   - 사용 가능한 tool 목록 조회
   - Tool 호출 및 결과 처리

3. **자연어 이해 및 응답**
   - 사용자 요청을 적절한 tool 호출로 변환
   - 데이터 조회 결과를 사용자 친화적으로 포맷팅
   - 필터 조건을 자연어에서 추출

#### 구현 단계

```python
# 1. MCP 클라이언트 초기화
mcp_client = MCPClient(server_url="...")

# 2. Google Agent 설정
agent = Agent(
    model="gemini-2.0-flash",
    tools=[mcp_client.get_tools()]  # Tool Server의 tool 연결
)

# 3. 대화 처리
response = agent.run("2026년 1월 1일부터 5일까지 데이터를 조회해줘")
```

#### 예시 시나리오

**사용자**: "JN00000 프로그램의 2026년 1월 1일 데이터를 보여줘"

**Agent 처리 과정**:
1. 요청 분석: program_id=JN00000, 날짜 필터 필요
2. `create_filter` tool로 시간 필터 생성
3. `get_data` tool로 데이터 조회
4. 결과를 테이블 형식으로 포맷팅하여 응답

### 통합 및 실행

```bash
# Terminal 1: Tool Server 실행 (이미 구현됨)
cd tools/
python server.py

# Terminal 2: Agent 실행 (개발 예정)
cd agent/
python main.py
```

Agent와 Tool Server는 각각 독립 프로세스로 실행되며 MCP 프로토콜로 통신합니다.

## TODO

### Agent 개발
- [ ] Google Agent Development Kit 프로젝트 초기화
- [ ] MCP 클라이언트 구현 (Tool Server 연결)
- [ ] 기본 대화 흐름 구현
- [ ] 자연어 → 필터 변환 로직
- [ ] 데이터 조회 결과 포맷팅

### 통합 및 테스트
- [ ] Tool Server와 연동 테스트
- [ ] 다양한 쿼리 시나리오 테스트
- [ ] 에러 처리 및 사용자 피드백 개선

### 문서화
- [ ] Agent 사용 가이드 작성
- [ ] 예시 쿼리 및 응답 문서화
