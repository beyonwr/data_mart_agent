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
- **RAG (선택)**: ChromaDB/Qdrant (Vector DB), OpenAI/Gemini Embeddings

## 프로젝트 구조

```
data_mart_agent/
├── agent/          # Google Agent Development Kit 기반 에이전트 (개발 예정)
├── tools/          # FastMCP 기반 도구 서버 (개발 예정)
├── rag/            # RAG 시스템 (선택 사항)
│   ├── vectordb/   # Vector DB 데이터
│   ├── embeddings/ # 임베딩 모델 관련
│   └── indexing.py # 메타데이터 인덱싱 스크립트
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

- `authenticate`: 사용자 인증 및 토큰 발급
- `get_data`: 프로그램 데이터 조회
- `get_metadata`: 컬럼 메타데이터 조회
- `create_filter`: 동적 필터 생성

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

## RAG (Retrieval-Augmented Generation) 구성

### RAG 적용 목적

데이터 마트 에이전트는 다음 문제를 해결하기 위해 RAG를 활용합니다:

1. **컬럼명 모호성**: 사용자는 비즈니스 용어로 요청하지만 실제 컬럼명은 기술적 (예: "완료 시간" vs "lot_compt_date_time")
2. **스키마 복잡성**: 수백 개의 컬럼과 다양한 프로그램 ID별 스키마 차이
3. **쿼리 패턴 학습**: 자주 사용되는 필터 조합과 성공한 쿼리 재활용
4. **도메인 지식**: 컬럼 간 관계, 유효한 값 범위, 비즈니스 규칙

### RAG 아키텍처

```
┌──────────────┐
│   User       │
│   Query      │
└──────┬───────┘
       │
       v
┌──────────────────────────────────────────────────────┐
│                    Agent                              │
│  ┌────────────────────────────────────────────────┐  │
│  │  1. RAG: 관련 메타데이터/패턴 검색             │  │
│  │  2. LLM: 컨텍스트 기반 쿼리 생성              │  │
│  │  3. MCP: Tool 호출                            │  │
│  └────────────────────────────────────────────────┘  │
└───────────────┬──────────────────────────────────────┘
                │
       ┌────────┴────────┐
       v                 v
┌─────────────┐   ┌─────────────┐
│  Vector DB  │   │ Tool Server │
│  (RAG)      │   │  (MCP)      │
└─────────────┘   └─────────────┘
```

### RAG 데이터 소스

#### 1. 메타데이터 벡터 DB

**인덱싱 대상**:
```json
{
  "program_id": "JN00000",
  "column_name": "x.lot_compt_date_time",
  "data_type": "TIMESTAMP",
  "business_name": "로트 완료 시간",
  "description": "작업 로트가 완료된 날짜 및 시간",
  "sample_values": ["2026-01-01 00:00:00", "2026-01-01 00:05:00"],
  "related_columns": ["x.lot_start_date_time", "x.lot_id"],
  "common_filters": ["BETWEEN", "GT", "LT"]
}
```

**검색 예시**:
- 사용자 쿼리: "완료 시간이 1월 1일인 데이터"
- RAG 검색: "lot_compt_date_time" 메타데이터 반환
- Agent: TIMESTAMP 타입이므로 BETWEEN 필터 사용

#### 2. 쿼리 패턴 벡터 DB

**인덱싱 대상**:
```json
{
  "user_query": "지난주 완료된 로트 조회",
  "generated_filter": {
    "x.lot_compt_date_time": {
      "data_value": "2025-12-25 00:00:00|2025-12-31 23:59:59",
      "data_type": "TIMESTAMP",
      "data_operator": "BETWEEN"
    }
  },
  "program_id": "JN00000",
  "success": true,
  "result_count": 1500
}
```

**활용**:
- 유사한 과거 쿼리 검색
- 성공한 필터 패턴 재사용
- 컬럼 조합 패턴 학습

#### 3. 도메인 용어 매핑

**인덱싱 대상**:
```json
{
  "business_term": "로트",
  "technical_terms": ["lot_id", "lot_compt_date_time", "lot_start_date_time"],
  "context": "제조 공정에서 하나의 작업 단위",
  "synonyms": ["배치", "작업 단위"]
}
```

### 구현 방법

#### Option 1: Agent 레벨 RAG (권장)

Agent가 직접 Vector DB에 접근:

```python
from google.genai import Agent
from chromadb import Client

# Vector DB 초기화
vector_db = Client()
metadata_collection = vector_db.get_collection("datamart_metadata")

# Agent 설정
agent = Agent(
    model="gemini-2.0-flash",
    tools=[mcp_client.get_tools()],
    instruction="""
    사용자 쿼리를 받으면:
    1. Vector DB에서 관련 컬럼 메타데이터 검색
    2. 검색된 정보로 정확한 컬럼명과 데이터 타입 파악
    3. create_filter tool로 필터 생성
    4. get_data tool로 데이터 조회
    """
)

# 대화 시 RAG 컨텍스트 주입
user_query = "1월 1일 완료된 로트를 보여줘"
relevant_metadata = metadata_collection.query(user_query, n_results=3)
response = agent.run(f"컨텍스트: {relevant_metadata}\n\n쿼리: {user_query}")
```

**장점**:
- Agent가 컨텍스트를 직접 활용
- LLM이 메타데이터 기반으로 더 정확한 판단
- 쿼리 히스토리 학습 가능

#### Option 2: Tool Server에 RAG Tool 추가

Tool Server에 RAG 검색 tool 추가:

```python
# Tool Server (FastMCP)
@mcp.tool()
def search_metadata(query: str, top_k: int = 5) -> list:
    """
    사용자 쿼리와 관련된 컬럼 메타데이터를 검색합니다.

    Args:
        query: 검색 쿼리 (자연어)
        top_k: 반환할 결과 개수

    Returns:
        관련 컬럼 메타데이터 리스트
    """
    results = vector_db.query(query, n_results=top_k)
    return results

@mcp.tool()
def search_query_pattern(query: str, program_id: str) -> dict:
    """
    유사한 과거 쿼리 패턴을 검색합니다.
    """
    patterns = pattern_db.query(query, filter={"program_id": program_id})
    return patterns
```

**Agent 활용**:
```python
# Agent가 먼저 search_metadata tool 호출
metadata = mcp_client.call("search_metadata", {"query": "완료 시간"})

# 메타데이터 기반으로 필터 생성
filter_result = mcp_client.call("create_filter", {
    "column": metadata[0]["column_name"],
    "value": "2026-01-01",
    "operator": "EQ"
})
```

**장점**:
- Tool Server가 RAG 로직 캡슐화
- Agent는 tool 호출만 하면 됨
- 독립적으로 RAG 시스템 업데이트 가능

### 벡터 DB 선택

**추천 스택**:

1. **ChromaDB** (개발/테스트)
   - 간단한 설치 및 사용
   - 로컬 개발에 적합
   - Python 네이티브 지원

2. **Qdrant** (프로덕션)
   - 높은 성능 및 확장성
   - 필터링 기능 강력
   - 자체 호스팅 가능

3. **Pinecone** (클라우드)
   - 완전 관리형 서비스
   - 빠른 프로토타이핑

### 임베딩 모델

```python
# OpenAI Embeddings (다국어 지원 우수)
from openai import OpenAI
client = OpenAI()

embedding = client.embeddings.create(
    model="text-embedding-3-small",
    input="lot_compt_date_time: 로트 완료 시간"
)

# 또는 Gemini Embeddings
from google import genai
embedding = genai.embed_content(
    model="models/text-embedding-004",
    content="lot_compt_date_time: 로트 완료 시간"
)
```

### 메타데이터 수집 및 인덱싱

```python
# 메타데이터 수집 스크립트
def collect_metadata(program_id: str) -> list:
    """데이터 마트에서 메타데이터 수집"""
    token = authenticate(user_id)
    metadata = get_metadata(program_id, token)

    enriched = []
    for col in metadata:
        # 샘플 데이터 조회로 실제 값 확인
        sample_data = get_data(program_id, token, limit=10)

        enriched.append({
            "column_name": col["name"],
            "data_type": col["type"],
            "business_name": infer_business_name(col["name"]),  # 수동 매핑 또는 LLM 추론
            "sample_values": sample_data[col["name"]].tolist()[:5],
            "description": generate_description(col, sample_data)  # LLM으로 설명 생성
        })

    return enriched

# Vector DB에 인덱싱
def index_metadata(metadata_list: list):
    collection.add(
        documents=[json.dumps(m) for m in metadata_list],
        metadatas=metadata_list,
        ids=[m["column_name"] for m in metadata_list]
    )
```

### RAG 워크플로우 예시

**시나리오**: "지난주 완료된 로트 중 오류가 있는 것만 보여줘"

1. **RAG 검색**:
   - Query: "완료 시간" → 결과: `lot_compt_date_time` (TIMESTAMP)
   - Query: "오류" → 결과: `error_flag` (VARCHAR)

2. **Agent 판단**:
   - "지난주" → BETWEEN 필터 (7일 전 ~ 어제)
   - "오류가 있는" → error_flag = 'Y' 또는 IN ('ERROR', 'FAIL')

3. **Tool 호출**:
   ```python
   filter1 = create_filter("lot_compt_date_time", "2025-12-25|2026-01-01", "TIMESTAMP", "BETWEEN")
   filter2 = create_filter("error_flag", "Y", "VARCHAR", "EQ", filter1)
   data = get_data("JN00000", token, filter2)
   ```

### 지속적 개선

1. **쿼리 피드백 수집**:
   - 성공/실패한 쿼리 기록
   - 사용자 만족도 수집

2. **메타데이터 갱신**:
   - 주기적으로 데이터 마트 스키마 변경 감지
   - 새로운 컬럼/프로그램 ID 자동 인덱싱

3. **패턴 학습**:
   - 자주 사용되는 필터 조합 우선순위화
   - 도메인 용어 매핑 자동 확장

## TODO

### 1단계: Tool Server 개발
- [ ] FastMCP 프로젝트 초기화
- [ ] 데이터 마트 API 클라이언트 구현
- [ ] `authenticate` tool 구현
- [ ] `get_data` tool 구현
- [ ] `get_metadata` tool 구현
- [ ] `create_filter` tool 구현
- [ ] MCP Inspector로 각 tool 단독 테스트

### 2단계: Agent 개발
- [ ] Google Agent Development Kit 프로젝트 초기화
- [ ] MCP 클라이언트 구현 (Tool Server 연결)
- [ ] 기본 대화 흐름 구현
- [ ] 자연어에서 필터 조건 추출 로직
- [ ] 데이터 조회 결과 포맷팅

### 3단계: 통합 및 테스트
- [ ] Tool Server와 Agent 연동
- [ ] 다양한 쿼리 시나리오 테스트
- [ ] 에러 처리 및 사용자 피드백 개선

### 4단계: 문서화
- [ ] Tool Server API 문서 작성
- [ ] Agent 사용 가이드 작성
- [ ] 예시 쿼리 및 응답 문서화

### 선택: RAG 통합 (성능 개선)
- [ ] Vector DB 선택 및 설치 (ChromaDB/Qdrant)
- [ ] 메타데이터 수집 스크립트 작성
- [ ] 임베딩 모델 설정 (OpenAI/Gemini)
- [ ] 메타데이터 인덱싱
- [ ] Agent에 RAG 통합 (Option 1) 또는 Tool Server에 RAG tool 추가 (Option 2)
- [ ] 쿼리 패턴 수집 및 인덱싱
- [ ] 도메인 용어 매핑 구축
- [ ] RAG 성능 평가 및 개선
