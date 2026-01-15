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
- **RAG**:
  - Vector DB: ChromaDB (Docker 별도 실행, HTTP Client)
  - Embedding: DNA (Qwen 14B 기반 한글 특화 모델, 별도 서버)

## 프로젝트 구조

```
data_mart_agent/
├── agent/                  # Google Agent Development Kit 기반 에이전트
│   ├── main.py            # Agent 메인 진입점
│   └── requirements.txt   # Agent 의존성
├── tools/                  # FastMCP 기반 도구 서버 (RAG 포함)
│   ├── server.py          # FastMCP 서버 메인
│   ├── datamart_client.py # 데이터 마트 API 클라이언트
│   ├── rag_manager.py     # RAG 관리 (ChromaDB HTTP Client)
│   └── requirements.txt   # Tool Server 의존성
├── scripts/                # 유틸리티 스크립트
│   └── indexing.py        # 메타데이터 인덱싱 스크립트
├── reference.py           # 데이터 마트 API 레퍼런스
└── claude.md              # 이 파일
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

### 개발 전략

1. **Tool Server 개발** (우선)
   - FastMCP로 독립 실행 가능한 MCP 서버 구현
   - 데이터 마트 REST API를 MCP tool로 래핑
   - MCP Inspector 또는 CLI로 단독 테스트

2. **Agent 개발** (후속)
   - Google Agent Development Kit 기반
   - Tool Server의 MCP 인터페이스 활용
   - Tool Server 구현 세부사항 몰라도 됨 (MCP 프로토콜만 준수)

3. **통합 테스트**
   - Agent에서 Tool Server 연결
   - 실제 데이터 마트 시나리오 테스트

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
CHROMADB_URL=       # ChromaDB HTTP 서버 URL (예: http://localhost:8000)
EMBEDDING_URL=      # DNA 임베딩 모델 서버 URL
```

## 코딩 스타일

### 일반 원칙
- **PEP 8** 준수
- **타입 힌팅** 필수 사용 (`typing` 모듈)
- **명확한 변수명** 사용 (축약 지양)
- **한 함수는 한 가지 일만** (Single Responsibility)
- **이모지 사용 금지** (코드, 주석, 문서, 커밋 메시지 모두)

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

### Tool Server 개발 (1단계)

**목표**: 데이터 마트 API를 MCP tool로 래핑한 독립 서버 구현

#### 구현할 Tool 목록

**데이터 마트 Tool**:
- `authenticate`: 사용자 인증 및 토큰 발급
- `get_data`: 프로그램 데이터 조회 (필터는 선택 사항)
- `get_metadata`: 컬럼 메타데이터 조회
- `create_filter`: 동적 필터 생성 (다양한 연산자 지원)

**RAG Tool**:
- `search_metadata`: 자연어로 컬럼 메타데이터 검색
- `search_query_pattern`: 과거 성공한 쿼리 패턴 검색

#### 독립 테스트

Tool Server는 Agent 없이도 단독으로 테스트 가능:
- MCP Inspector 사용
- `mcp dev` CLI로 tool 호출 테스트
- 각 tool의 입력/출력 검증

```bash
# Tool Server 단독 실행 및 테스트
cd tools/
mcp dev server.py
```

### Agent 개발 (2단계)

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

#### RAG를 활용한 Agent 워크플로우

Agent가 RAG Tool을 활용하는 처리 흐름:

```python
# Agent가 자동으로 수행하는 작업 (예시)

# 사용자 쿼리: "완료 시간이 1월 1일인 로트를 보여줘"

# 1. RAG Tool로 컬럼 검색
metadata = mcp_client.call_tool("search_metadata", {
    "query": "완료 시간",
    "program_id": "JN00000"
})
# 결과: [{"column_name": "x.lot_compt_date_time", "data_type": "TIMESTAMP", ...}]

# 2. 메타데이터 기반으로 필터 생성
filter_dict = mcp_client.call_tool("create_filter", {
    "column_name": "x.lot_compt_date_time",
    "value": "2026-01-01 00:00:00|2026-01-01 23:59:59",
    "data_type": "TIMESTAMP",
    "operator": "BETWEEN"
})

# 3. 데이터 조회
token = mcp_client.call_tool("authenticate", {"user_id": "..."})
data = mcp_client.call_tool("get_data", {
    "program_id": "JN00000",
    "token": token,
    "filters": filter_dict
})

# 4. 결과 포맷팅 및 사용자에게 응답
```

**Agent 설정 예시** (RAG Tool 활용):
```python
agent = Agent(
    model="gemini-2.0-flash",
    tools=[mcp_client.get_tools()],
    instruction="""
    사용자가 데이터를 요청하면:

    1. 먼저 search_metadata tool로 관련 컬럼을 검색하세요
       - 사용자의 비즈니스 용어를 기술 컬럼명으로 변환
       - 데이터 타입 확인

    2. (선택) search_query_pattern tool로 유사한 과거 쿼리 확인
       - 성공한 필터 패턴이 있으면 참고

    3. create_filter tool로 필터 생성
       - 검색된 컬럼명과 데이터 타입 사용
       - 사용자가 요청한 조건 반영

    4. authenticate tool로 토큰 발급

    5. get_data tool로 데이터 조회

    6. 결과를 사용자 친화적으로 포맷팅하여 응답
    """
)
```

#### 예시 시나리오

**사용자**: "JN00000 프로그램의 2026년 1월 1일 데이터를 보여줘"

**Agent 처리 과정**:
1. 요청 분석: program_id=JN00000, 날짜 필터 필요
2. `create_filter` tool로 시간 필터 생성
3. `get_data` tool로 데이터 조회
4. 결과를 테이블 형식으로 포맷팅하여 응답

### 통합 및 실행 (3단계)

Tool Server와 Agent를 각각 독립 프로세스로 실행:

```bash
# Terminal 1: Tool Server 실행
cd tools/
python server.py

# Terminal 2: Agent 실행
cd agent/
python main.py
```

**핵심**: 두 컴포넌트는 MCP 프로토콜로만 통신하며, 서로의 구현 세부사항을 알 필요 없음

## RAG 구성

### RAG 적용 목적

비즈니스 용어와 기술 컬럼명 간 매핑, 복잡한 스키마 이해, 과거 성공 쿼리 재사용을 위해 RAG를 활용합니다.

### RAG 데이터 소스

**1. 메타데이터 벡터 DB**: 컬럼명, 데이터 타입, 비즈니스명, 설명, 샘플값
**2. 쿼리 패턴 벡터 DB**: 과거 성공한 쿼리, 생성된 필터, 결과 건수
**3. 도메인 용어 매핑**: 비즈니스 용어와 기술 컬럼명 매핑

### Tool Server에 RAG 통합

#### ChromaDB HTTP Client 사용

**rag_manager.py**:
```python
import chromadb
import requests
from typing import List, Dict
import os

class RAGManager:
    def __init__(self):
        # ChromaDB HTTP Client (Docker 별도 실행)
        self.chroma_client = chromadb.HttpClient(
            host=os.getenv("CHROMADB_URL", "http://localhost:8000")
        )

        # DNA 임베딩 모델 서버 URL
        self.embedding_url = os.getenv("EMBEDDING_URL")

        self.metadata_collection = self.chroma_client.get_or_create_collection(
            name="datamart_metadata",
            metadata={"hnsw:space": "cosine"}
        )

        self.pattern_collection = self.chroma_client.get_or_create_collection(
            name="query_patterns",
            metadata={"hnsw:space": "cosine"}
        )

    def get_embedding(self, text: str) -> List[float]:
        """DNA 임베딩 모델 서버 호출"""
        response = requests.post(
            f"{self.embedding_url}/embed",
            json={"text": text},
            timeout=30
        )
        response.raise_for_status()
        return response.json()["embedding"]

    def search_metadata(self, query: str, program_id: str = None, top_k: int = 5) -> List[Dict]:
        embedding = self.get_embedding(query)
        where = {"program_id": program_id} if program_id else None

        results = self.metadata_collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
            where=where
        )

        return [
            {
                "column_name": meta["column_name"],
                "data_type": meta["data_type"],
                "business_name": meta["business_name"],
                "description": meta["description"]
            }
            for meta in results['metadatas'][0]
        ]

    def search_query_pattern(self, query: str, program_id: str, top_k: int = 3) -> List[Dict]:
        embedding = self.get_embedding(query)

        results = self.pattern_collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
            where={"program_id": program_id}
        )

        return results['metadatas'][0] if results['metadatas'] else []
```

**server.py (FastMCP)**:
```python
from fastmcp import FastMCP
from rag_manager import RAGManager
from datamart_client import DataMartClient

mcp = FastMCP("DataMart Tool Server")
rag = RAGManager()
datamart = DataMartClient()

@mcp.tool()
def search_metadata(query: str, program_id: str = None, top_k: int = 5) -> list:
    """
    사용자 쿼리와 관련된 컬럼 메타데이터를 검색합니다.

    Args:
        query: 검색 쿼리 (자연어, 예: "완료 시간")
        program_id: 프로그램 ID (선택)
        top_k: 반환할 결과 개수

    Returns:
        관련 컬럼 메타데이터 리스트
    """
    return rag.search_metadata(query, program_id, top_k)

@mcp.tool()
def search_query_pattern(query: str, program_id: str, top_k: int = 3) -> list:
    """유사한 과거 쿼리 패턴 검색"""
    return rag.search_query_pattern(query, program_id, top_k)

@mcp.tool()
def authenticate(user_id: str) -> str:
    """사용자 인증"""
    return datamart.get_token(user_id)

@mcp.tool()
def get_data(program_id: str, token: str, filters: dict = None) -> dict:
    """데이터 조회 (필터는 선택 사항)"""
    return datamart.get_data(program_id, token, filters)

@mcp.tool()
def create_filter(column_name: str, value: str, data_type: str, operator: str, base_filter: dict = None) -> dict:
    """
    동적 필터 생성

    Args:
        column_name: 컬럼명
        value: 필터 값 (BETWEEN, IN 등은 "|"로 구분)
        data_type: VARCHAR, DOUBLE, BIGINT, DATE, TIMESTAMP
        operator: EQ, IN, NOT_IN, BETWEEN, GT, LT, LIKE 등
        base_filter: 기존 필터에 추가할 경우

    Returns:
        생성된 필터 딕셔너리
    """
    # reference.py의 make_filter 로직 구현
    pass
```

**requirements.txt**:
```
fastmcp
chromadb
requests
pandas
python-dotenv
```

#### DNA 임베딩 모델

Qwen 14B 기반 한글 특화 모델을 별도 서버로 실행하여 사용합니다.

## TODO

### 1단계: Tool Server 개발
- [ ] FastMCP 프로젝트 초기화
- [ ] 데이터 마트 API 클라이언트 (datamart_client.py)
- [ ] 기본 tool: authenticate, get_data, get_metadata, create_filter
- [ ] RAG 시스템 (rag_manager.py):
  - [ ] ChromaDB HTTP Client 연동
  - [ ] DNA 임베딩 모델 연동
  - [ ] search_metadata, search_query_pattern tool
- [ ] 메타데이터 인덱싱 스크립트 (scripts/indexing.py)
- [ ] MCP Inspector로 단독 테스트

### 2단계: Agent 개발
- [ ] Google Agent Development Kit 초기화
- [ ] MCP 클라이언트 구현
- [ ] Agent instruction 작성 (RAG Tool 우선 사용)
- [ ] 대화 흐름 및 에러 처리

### 3단계: 통합 및 테스트
- [ ] Tool Server와 Agent 연동
- [ ] RAG 기능 검증 (비즈니스 용어 → 기술 컬럼명 변환)
- [ ] 다양한 쿼리 시나리오 테스트

### 4단계: 문서화
- [ ] Tool Server API 문서
- [ ] Agent 사용 가이드
- [ ] 예시 쿼리 및 응답
