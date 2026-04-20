---
name: graphify
description: "모든 입력(코드, 문서, 논문, 이미지) - 지식 그래프 - 클러스터링된 커뮤니티 - HTML + JSON + 감사 보고서"
---

# graphify

파일이 포함된 어떤 폴더든 커뮤니티 감지 기능, 투명한 감사 추적(audit trail), 그리고 세 가지 출력물(대화형 HTML, GraphRAG용 JSON, 쉬운 언어로 작성된 GRAPH_REPORT.md)을 갖춘 탐색 가능한 지식 그래프로 변환합니다.

## 사용법 (Usage)

```bash
/graphify                                             # 현재 디렉토리에서 전체 파이프라인 실행 → Obsidian 볼트
/graphify <경로>                                      # 특정 경로에서 전체 파이프라인 실행
/graphify <경로> --mode deep                          # 철저한 추출, 더 풍부한 INFERRED(추론된) 엣지 생성
/graphify <경로> --update                             # 증분 업데이트 - 새롭거나 변경된 파일만 다시 추출
/graphify <경로> --directed                           # 방향성 그래프 빌드 (소스→대상 엣지 방향 보존)
/graphify <경로> --whisper-model medium               # 더 나은 전사(transcription) 정확도를 위해 더 큰 Whisper 모델 사용
/graphify <경로> --cluster-only                       # 기존 그래프에서 클러스터링만 다시 실행
/graphify <경로> --no-viz                             # 시각화 생략, 보고서와 JSON만 생성
/graphify <경로> --html                               # (HTML은 기본으로 생성됨 - 이 플래그는 아무 동작도 하지 않음)
/graphify <경로> --svg                                # graph.svg 추가 내보내기 (Notion, GitHub 임베드용)
/graphify <경로> --graphml                            # graph.graphml 내보내기 (Gephi, yEd용)
/graphify <경로> --neo4j                              # Neo4j용 graphify-out/cypher.txt 생성
/graphify <경로> --neo4j-push bolt://localhost:7687   # Neo4j로 직접 푸시
/graphify <경로> --mcp                                # 에이전트 접근을 위한 MCP stdio 서버 시작
/graphify <경로> --watch                              # 폴더 감시, 코드 변경 시 자동 재빌드 (LLM 불필요)
/graphify <경로> --wiki                               # 에이전트가 크롤링할 수 있는 위키 빌드 (index.md + 커뮤니티당 문서 1개)
/graphify <경로> --obsidian --obsidian-dir ~/vaults/my-project  # 사용자 지정 경로에 볼트 생성 (예: 기존 볼트)
/graphify add <url>                                   # URL 내용을 가져와 ./raw에 저장하고 그래프 업데이트
/graphify add <url> --author "이름"                   # 작성자 태그 지정
/graphify add <url> --contributor "이름"              # 코퍼스에 추가한 사람 태그 지정
/graphify query "<질문>"                              # BFS 탐색 - 넓은 문맥 파악
/graphify query "<질문>" --dfs                        # DFS - 특정 경로 추적
/graphify query "<질문>" --budget 1500                # 답변을 N개 토큰으로 제한
/graphify path "AuthModule" "Database"                # 두 개념 간의 최단 경로 찾기
/graphify explain "SwinTransformer"                   # 특정 노드에 대한 쉬운 언어의 설명
```

## graphify의 용도

graphify는 Andrej Karpathy의 `/raw` 폴더 워크플로우를 중심으로 설계되었습니다. 논문, 트윗, 스크린샷, 코드, 노트 등 무엇이든 폴더에 넣기만 하면, 서로 연결되어 있는지조차 몰랐던 것들을 보여주는 구조화된 지식 그래프를 얻을 수 있습니다.

Claude 단독으로는 할 수 없는 세 가지 기능:

1. **영구적인 그래프 (Persistent graph)** - 관계 데이터는 `graphify-out/graph.json`에 저장되어 세션 간에 유지됩니다. 모든 것을 다시 읽을 필요 없이 몇 주 뒤에도 질문할 수 있습니다.
2. **투명한 감사 추적 (Honest audit trail)** - 모든 엣지에는 EXTRACTED(추출됨), INFERRED(추론됨) 또는 AMBIGUOUS(모호함)가 태그로 지정됩니다. 무엇이 실제로 발견된 것이고 무엇이 추측된 것인지 명확히 알 수 있습니다.
3. **교차 문서 간의 놀라운 발견 (Cross-document surprise)** - 커뮤니티 감지 기능은 당신이 직접 질문할 생각조차 하지 못했던, 서로 다른 파일에 있는 개념들 간의 연결성을 찾아냅니다.

다음과 같은 용도로 사용하세요:

- 처음 접하는 코드베이스 (코드를 건드리기 전에 아키텍처 이해하기)
- 읽기 목록 (논문 + 트윗 + 노트 → 탐색 가능한 하나의 그래프로)
- 연구 코퍼스 (인용 그래프 + 개념 그래프를 하나로 통합)
- 개인용 `/raw` 폴더 (모든 것을 넣고, 내용이 채워지도록 두고, 쿼리하기)

## 호출 시 반드시 수행해야 할 작업 (What You Must Do When Invoked)

경로가 주어지지 않은 경우 `.` (현재 디렉토리)를 사용하세요. 사용자에게 경로를 묻지 마세요.

다음 단계들을 순서대로 따르세요. 단계를 건너뛰지 마세요.

### 1단계 - graphify 설치 확인

```bash
# 올바른 Python 인터프리터 감지 (pipx, venv, 시스템 설치 처리)
GRAPHIFY_BIN=$(which graphify 2>/dev/null)
if [ -n "$GRAPHIFY_BIN" ]; then
    PYTHON=$(head -1 "$GRAPHIFY_BIN" | tr -d '#!')
    case "$PYTHON" in
        *[!a-zA-Z0-9/_.-]*) PYTHON="python3" ;;
    esac
else
    PYTHON="python3"
fi
"$PYTHON" -c "import graphify" 2>/dev/null || "$PYTHON" -m pip install graphifyy -q 2>/dev/null || "$PYTHON" -m pip install graphifyy -q --break-system-packages 2>&1 | tail -3
# 이후 모든 단계를 위해 인터프리터 경로 쓰기 (호출 간에 유지됨)
mkdir -p graphify-out
"$PYTHON" -c "import sys; open('graphify-out/.graphify_python', 'w').write(sys.executable)"
```

임포트(import)에 성공하면 아무것도 출력하지 말고 곧바로 2단계로 넘어가세요.

**이후의 모든 bash 블록에서는 `python3`를 `$(cat graphify-out/.graphify_python)`로 대체하여 올바른 인터프리터를 사용해야 합니다.**

### 2단계 - 파일 감지

```bash
$(cat graphify-out/.graphify_python) -c "
import json
from graphify.detect import detect
from pathlib import Path
result = detect(Path('INPUT_PATH'))
print(json.dumps(result))
" > graphify-out/.graphify_detect.json
```

`INPUT_PATH`를 사용자가 제공한 실제 경로로 교체하세요. JSON을 `cat`으로 출력하거나 화면에 표시하지 마세요. 조용히 읽은 뒤 다음과 같이 깔끔한 요약만 제시하세요:

```text
코퍼스: X개 파일 · 약 Y개 단어
  코드:     N개 파일 (.py .ts .go ...)
  문서:     N개 파일 (.md .txt ...)
  논문:     N개 파일 (.pdf ...)
  이미지:   N개 파일
  비디오:   N개 파일 (.mp4 .mp3 ...)
```

파일 수가 0인 카테고리는 요약에서 생략하세요.

그런 다음 분석 결과에 따라 행동하세요:

- `total_files`가 0인 경우: "[경로]에서 지원되는 파일을 찾을 수 없습니다."라고 안내하고 중지하세요.
- `skipped_sensitive`가 비어 있지 않은 경우: 건너뛴 파일 수를 언급하되, 파일 이름은 나열하지 마세요.
- `total_words` > 2,000,000 이거나 `total_files` > 200인 경우: 경고를 표시하고 파일 수 기준 상위 5개의 하위 디렉토리를 보여준 다음, 어떤 하위 폴더에서 실행할지 사용자에게 물어보세요. 사용자의 답변을 기다린 후 진행하세요.
- 그 외의 경우: 비디오 파일이 감지되었다면 2.5단계로, 감지되지 않았다면 3단계로 바로 진행하세요.

### 2.5단계 - 비디오 / 오디오 파일 전사 (비디오 파일이 감지된 경우에만)

`detect`에서 비디오 파일이 0개로 반환되었다면 이 단계를 완전히 건너뛰세요.

비디오 및 오디오 파일은 직접 읽을 수 없습니다. 먼저 텍스트로 전사(transcribe)한 다음, 3단계에서 이 전사본을 문서(doc) 파일로 취급합니다.

**전략:** `graphify-out/.graphify_detect.json`에서 최상위 노드(god nodes) 레이블을 읽으세요(또는 이전 실행의 분석 파일이 있다면 거기서 읽으세요). 당신은 언어 모델입니다 — 해당 레이블들을 바탕으로 직접 한 문장짜리 도메인 힌트를 작성하세요. 그런 다음 이를 Whisper의 초기 프롬프트로 전달하세요. 별도의 API 호출은 필요하지 않습니다.

**단,** 코퍼스에 다른 문서나 코드가 없고 오직 비디오 파일만 있는 경우, 일반적인 폴백 프롬프트를 사용하세요: `"Use proper punctuation and paragraph breaks.(적절한 문장 부호와 단락 구분을 사용하세요.)"`

**1단계 - Whisper 프롬프트 직접 작성하기.**

감지 출력이나 분석에서 상위 신 노드(god node) 레이블을 읽고, 짧은 도메인 힌트 문장을 구성하세요. 예:

- 레이블: `transformer, attention, encoder, decoder` → `"Machine learning research on transformer architectures and attention mechanisms. Use proper punctuation and paragraph breaks."`
- 레이블: `kubernetes, deployment, pod, helm` → `"DevOps discussion about Kubernetes deployments and Helm charts. Use proper punctuation and paragraph breaks."`

작성한 문장을 다음 명령에서 사용할 수 있도록 `WHISPER_PROMPT`로 설정하세요.

**2단계 - 전사(Transcribe):**

```bash
GRAPHIFY_WHISPER_MODEL=base  # 또는 사용자가 전달한 --whisper-model 값
$(cat graphify-out/.graphify_python) -c "
import json, os
from pathlib import Path
from graphify.transcribe import transcribe_all

detect = json.loads(Path('graphify-out/.graphify_detect.json').read_text())
video_files = detect.get('files', {}).get('video', [])
prompt = os.environ.get('GRAPHIFY_WHISPER_PROMPT', 'Use proper punctuation and paragraph breaks.')

transcript_paths = transcribe_all(video_files, initial_prompt=prompt)
print(json.dumps(transcript_paths))
" > graphify-out/.graphify_transcripts.json
```

전사 후:

- `graphify-out/.graphify_transcripts.json`에서 전사본 경로들을 읽으세요.
- 3B단계에서 의미론적 하위 에이전트를 디스패치하기 전에, 문서 목록(docs list)에 이 경로들을 추가하세요.
- 생성된 전사본의 개수를 출력하세요: `비디오 파일 N개 전사 완료 -> 문서로 취급됨(Transcribed N video file(s) -> treating as docs)`
- 파일 전사에 실패할 경우, 경고를 출력하고 나머지 파일의 전사를 계속 진행하세요.

**Whisper 모델:** 기본값은 `base`입니다. 사용자가 `--whisper-model <이름>`을 전달했다면, 위 명령을 실행하기 전에 환경 변수에 `GRAPHIFY_WHISPER_MODEL=<이름>`을 설정하세요.

### 3단계 - 엔티티 및 관계 추출

**시작하기 전에:** `--mode deep`이 주어졌는지 확인하세요. 주어졌다면 3B2단계의 모든 하위 에이전트(subagent)에게 `DEEP_MODE=true`를 전달해야 합니다. 원래 호출 시점부터 이 상태를 추적하고, 절대 잃어버리지 마세요.

이 단계는 **구조적 추출(structural extraction)** (결정론적, 무료)과 **의미론적 추출(semantic extraction)** (Claude 사용, 토큰 비용 발생)의 두 부분으로 나뉩니다.

**파트 A (AST)와 파트 B (의미론적 추출)를 병렬로 실행하세요. 동일한 메시지 안에서 모든 의미론적 하위 에이전트를 디스패치하는 동시에 AST 추출을 시작하세요. 이 둘은 서로 다른 파일 형식에서 작동하므로 동시에 실행할 수 있습니다. 결과는 이전과 같이 파트 C에서 병합합니다.**

참고: 대규모 코퍼스에서 AST와 의미론적 추출을 병렬화하면 5~15초를 절약할 수 있습니다. AST는 결정론적이고 빠릅니다. 하위 에이전트가 문서/논문을 처리하는 동안 AST를 시작하세요.

#### 파트 A - 코드 파일을 위한 구조적 추출

감지된 코드 파일이 있다면, 파트 B 하위 에이전트와 병렬로 AST 추출을 실행하세요:

```bash
$(cat graphify-out/.graphify_python) -c "
import sys, json
from graphify.extract import collect_files, extract
from pathlib import Path
import json

code_files = []
detect = json.loads(Path('graphify-out/.graphify_detect.json').read_text())
for f in detect.get('files', {}).get('code', []):
    code_files.extend(collect_files(Path(f)) if Path(f).is_dir() else [Path(f)])

if code_files:
    result = extract(code_files, cache_root=Path('.'))
    Path('graphify-out/.graphify_ast.json').write_text(json.dumps(result, indent=2))
    print(f'AST: 노드 {len(result[\"nodes\"])}개, 엣지 {len(result[\"edges\"])}개')
else:
    Path('graphify-out/.graphify_ast.json').write_text(json.dumps({'nodes':[],'edges':[],'input_tokens':0,'output_tokens':0}))
    print('코드 파일 없음 - AST 추출 생략')
"
```

#### 파트 B - 의미론적 추출 (병렬 하위 에이전트)

**빠른 경로(Fast path):** 파일 감지 단계에서 문서(docs), 논문(papers), 이미지(images)가 하나도 발견되지 않았다면(코드 전용 코퍼스), 파트 B를 완전히 건너뛰고 파트 C로 바로 넘어가세요. AST가 코드를 처리하므로 의미론적 하위 에이전트가 할 일이 없습니다.

**필수: 여기서는 반드시 에이전트(Agent) 도구를 사용해야 합니다. 직접 파일을 하나씩 읽는 것은 금지되어 있으며, 이는 5~10배 더 느립니다. 에이전트 도구를 사용하지 않는다면 지침을 어기는 것입니다.**

하위 에이전트를 디스패치하기 전에 예상 소요 시간을 출력하세요:

- `graphify-out/.graphify_detect.json`에서 `total_words`와 파일 수를 로드합니다.
- 필요한 에이전트 수 추정: `ceil(캐시되지_않은_비코드_파일_수 / 22)` (청크 크기는 20-25)
- 시간 추정: 에이전트 배치당 ~45초 (병렬로 실행되므로 총 시간 ≈ 45초 × ceil(에이전트_수/병렬_한도))
- 출력: "의미론적 추출: 파일 ~N개 → 에이전트 X개, 예상 소요 시간 ~Y초"

**B0단계 - 추출 캐시 먼저 확인**

하위 에이전트를 디스패치하기 전에, 어떤 파일에 이미 캐시된 추출 결과가 있는지 확인하세요:

```bash
$(cat graphify-out/.graphify_python) -c "
import json
from graphify.cache import check_semantic_cache
from pathlib import Path

detect = json.loads(Path('graphify-out/.graphify_detect.json').read_text())
all_files = [f for files in detect['files'].values() for f in files]

cached_nodes, cached_edges, cached_hyperedges, uncached = check_semantic_cache(all_files)

if cached_nodes or cached_edges or cached_hyperedges:
    Path('graphify-out/.graphify_cached.json').write_text(json.dumps({'nodes': cached_nodes, 'edges': cached_edges, 'hyperedges': cached_hyperedges}))
Path('graphify-out/.graphify_uncached.txt').write_text('\n'.join(uncached))
print(f'캐시: 파일 {len(all_files)-len(uncached)}개 적중, 파일 {len(uncached)}개 추출 필요')
"
```

`graphify-out/.graphify_uncached.txt`에 나열된 파일에 대해서만 하위 에이전트를 디스패치하세요. 모든 파일이 캐시된 경우 바로 파트 C로 건너뛰세요.

**B1단계 - 청크(Chunk)로 분할**

`graphify-out/.graphify_uncached.txt`에서 파일을 로드하세요. 각각 20-25개의 파일로 구성된 청크로 분할하세요. 각 이미지 파일은 고유한 청크를 가져야 합니다(비전 기능은 별도의 컨텍스트가 필요함). 분할할 때 동일한 디렉토리의 파일들을 함께 그룹화하여 관련된 아티팩트가 동일한 청크에 포함되도록 함으로써 교차 파일 관계가 추출될 가능성을 높이세요.

**B2단계 - 단일 메시지에서 모든 하위 에이전트 디스패치**

동일한 응답(IN THE SAME RESPONSE) 내에서 에이전트(Agent) 도구를 여러 번 호출하세요 (청크당 1회 호출). 이것이 이들을 병렬로 실행시키는 유일한 방법입니다. 에이전트를 한 번 호출하고, 결과를 기다린 다음, 다시 호출한다면 순차적으로 실행하는 것이며 병렬 처리의 목적에 어긋납니다.

**중요 - 하위 에이전트 유형:** 항상 `subagent_type="general-purpose"`를 사용하세요. `Explore` 유형은 사용하지 마세요 - 읽기 전용이므로 디스크에 청크 파일을 쓸 수 없어 추출 결과가 조용히 누락됩니다. general-purpose는 하위 에이전트에 필요한 쓰기(Write) 및 Bash 권한을 가지고 있습니다.

3개 청크에 대한 구체적인 예:

```text
[Agent 도구 호출 1: 파일 1-15, subagent_type="general-purpose"]
[Agent 도구 호출 2: 파일 16-30, subagent_type="general-purpose"]
[Agent 도구 호출 3: 파일 31-45, subagent_type="general-purpose"]
```

이 세 가지 호출을 개별 메시지가 아닌 하나의 메시지에 모두 담으세요.

각 하위 에이전트는 정확히 다음 프롬프트를 받아야 합니다 (FILE_LIST, CHUNK_NUM, TOTAL_CHUNKS, DEEP_MODE 치환 필요):

```text
당신은 graphify 추출 하위 에이전트(subagent)입니다. 나열된 파일을 읽고 지식 그래프의 일부분(fragment)을 추출하세요.
설명, 마크다운 코드 블록(fences), 서문 없이 아래 스키마와 일치하는 유효한 JSON만을 출력하세요.

파일 (전체 TOTAL_CHUNKS 중 청크 CHUNK_NUM):
FILE_LIST

규칙:
- EXTRACTED: 소스에 명시적인 관계 (import, 호출, 인용, "§3.2 참조")
- INFERRED: 합리적인 추론 (공유 데이터 구조, 암묵적인 종속성)
- AMBIGUOUS: 불확실함 - 검토를 위해 플래그 표시, 생략하지 말 것

코드 파일: AST가 찾을 수 없는 의미론적 엣지(호출 관계, 공유 데이터, 아키텍처 패턴 등)에 집중하세요.
  AST가 이미 import 구문을 추출하므로 다시 추출하지 마세요.
문서/논문 파일: 명명된 개념, 엔티티, 인용을 추출하세요. 의사결정을 내린 이유, 선택된 트레이드오프, 설계 의도를 설명하는 섹션 등 '이유(rationale)'도 함께 추출하세요. 이들은 설명하는 개념을 가리키는 `rationale_for` 엣지를 가진 노드가 됩니다.
이미지 파일: 단순 OCR이 아닌 비전(vision)을 사용하여 이미지가 '무엇'인지 파악하세요.
  UI 스크린샷: 레이아웃 패턴, 디자인 결정, 핵심 요소, 목적.
  차트: 지표, 트렌드/인사이트, 데이터 출처.
  트윗/게시물: 주장(claim)을 노드로, 작성자, 언급된 개념.
  다이어그램: 구성 요소 및 연결.
  연구 도표: 무엇을 증명하는지, 방법론, 결과.
  손글씨/화이트보드: 아이디어 및 화살표, 불확실한 판독은 AMBIGUOUS로 표시.

DEEP_MODE (--mode deep이 주어진 경우): 간접적인 종속성, 공유된 가정, 잠재적인 결합(latent couplings) 등 INFERRED 엣지를 적극적으로 찾으세요. 불확실한 것은 생략하는 대신 AMBIGUOUS로 표시하세요.

의미론적 유사성(Semantic similarity): 이 청크 내의 두 개념이 구조적 연결(import, 호출, 인용 등) 없이 동일한 문제를 해결하거나 동일한 아이디어를 나타낸다면, 얼마나 유사한지(0.6-0.95)를 반영하는 `confidence_score`와 함께 `semantically_similar_to` 엣지를 추가하고 INFERRED로 표시하세요. 예:
- 서로를 호출하지는 않지만 둘 다 사용자 입력을 검증하는 두 함수
- 동일한 알고리즘을 설명하는 코드의 클래스와 논문의 개념
- 동일한 실패 모드를 다르게 처리하는 두 오류 유형
이는 유사성이 진정으로 명확하지 않고(non-obvious) 교차 영역적(cross-cutting)일 때만 추가하세요. 사소하게 비슷한 것들에는 추가하지 마세요.

하이퍼엣지(Hyperedges): 3개 이상의 노드가 쌍방향 엣지(pairwise edges)만으로는 포착되지 않는 공유 개념, 흐름 또는 패턴에 명확하게 함께 참여하는 경우 최상위 `hyperedges` 배열에 하이퍼엣지를 추가하세요. 예:
- 공통 프로토콜이나 인터페이스를 구현하는 모든 클래스
- 인증 흐름의 모든 함수 (서로를 직접 호출하지 않더라도)
- 하나의 일관된 아이디어를 형성하는 논문 섹션의 모든 개념
신중하게 사용하세요 — 그룹 관계가 쌍방향 엣지를 넘어선 추가 정보를 제공할 때만 사용하세요. 청크당 최대 3개의 하이퍼엣지로 제한.

파일에 YAML 프런트매터(--- ... ---)가 있는 경우, 해당 파일의 모든 노드에 source_url, captured_at, author, contributor를 복사하세요.

모든 엣지에서 confidence_score는 필수(REQUIRED)입니다 - 절대 생략하지 말고, 기본값으로 0.5를 사용하지 마세요:
- EXTRACTED 엣지: 항상 confidence_score = 1.0
- INFERRED 엣지: 각 엣지에 대해 개별적으로 추론하세요.
  직접적인 구조적 증거 (공유 데이터 구조, 명확한 종속성): 0.8-0.9.
  약간의 불확실성이 있는 합리적인 추론: 0.6-0.7.
  약하거나 추측성: 0.4-0.5. 대부분의 엣지는 0.5가 아닌 0.6-0.9여야 합니다.
- AMBIGUOUS 엣지: 0.1-0.3

노드 ID 형식: 소문자, 오직 `[a-z0-9_]`만 사용, 점이나 슬래시 없음. 형식: `{stem}_{entity}`. 여기서 stem은 확장자가 없는 파일 이름이고 entity는 심볼 이름이며, 둘 다 정규화됩니다(소문자화, 영숫자가 아닌 문자는 `_`로 교체됨). 예: `src/auth/session.py` + `ValidateToken` → `session_validatetoken`. 이는 코드 노드와 의미론적 노드 간의 상호 참조가 올바르게 연결되도록 AST 추출기가 생성하는 ID와 반드시 일치해야 합니다.

정확히 이 JSON만 출력하세요 (다른 텍스트 없음):
{"nodes":[{"id":"session_validatetoken","label":"Human Readable Name","file_type":"code|document|paper|image","source_file":"relative/path","source_location":null,"source_url":null,"captured_at":null,"author":null,"contributor":null}],"edges":[{"source":"node_id","target":"node_id","relation":"calls|implements|references|cites|conceptually_related_to|shares_data_with|semantically_similar_to|rationale_for","confidence":"EXTRACTED|INFERRED|AMBIGUOUS","confidence_score":1.0,"source_file":"relative/path","source_location":null,"weight":1.0}],"hyperedges":[{"id":"snake_case_id","label":"Human Readable Label","nodes":["node_id1","node_id2","node_id3"],"relation":"participate_in|implement|form","confidence":"EXTRACTED|INFERRED","confidence_score":0.75,"source_file":"relative/path"}],"input_tokens":0,"output_tokens":0}
```

**B3단계 - 수집, 캐시 및 병합**

모든 하위 에이전트의 작업이 끝날 때까지 기다리세요. 각 결과에 대해:

- 디스크에 `graphify-out/.graphify_chunk_NN.json`이 존재하는지 확인하세요 — 이것이 성공 신호입니다.
- 파일이 존재하고 `nodes`와 `edges`가 포함된 유효한 JSON이라면, 이를 포함시키고 캐시에 저장하세요.
- 파일이 누락되었다면, 하위 에이전트가 읽기 전용(Explore 유형)으로 디스패치되었을 가능성이 큽니다 — 다음과 같이 경고를 출력하세요: "디스크에서 청크 N이 누락됨 — 하위 에이전트가 읽기 전용이었을 수 있습니다. general-purpose 에이전트로 다시 실행하세요." 조용히 건너뛰지 마세요.
- 하위 에이전트가 실패하거나 유효하지 않은 JSON을 반환한 경우, 경고를 출력하고 해당 청크를 건너뛰세요 - 중단(abort)하지 마세요.

절반 이상의 청크가 실패하거나 누락된 경우, 작업을 중지하고 사용자에게 다시 실행하도록 지시하며 `subagent_type="general-purpose"`가 사용되었는지 확인하라고 알려주세요.

새 결과를 캐시에 저장:

```bash
$(cat graphify-out/.graphify_python) -c "
import json
from graphify.cache import save_semantic_cache
from pathlib import Path

new = json.loads(Path('graphify-out/.graphify_semantic_new.json').read_text()) if Path('graphify-out/.graphify_semantic_new.json').exists() else {'nodes':[],'edges':[],'hyperedges':[]}
saved = save_semantic_cache(new.get('nodes', []), new.get('edges', []), new.get('hyperedges', []))
print(f'파일 {saved}개 캐시됨')
"
```

캐시된 결과와 새 결과를 `graphify-out/.graphify_semantic.json`으로 병합:

```bash
$(cat graphify-out/.graphify_python) -c "
import json
from pathlib import Path

cached = json.loads(Path('graphify-out/.graphify_cached.json').read_text()) if Path('graphify-out/.graphify_cached.json').exists() else {'nodes':[],'edges':[],'hyperedges':[]}
new = json.loads(Path('graphify-out/.graphify_semantic_new.json').read_text()) if Path('graphify-out/.graphify_semantic_new.json').exists() else {'nodes':[],'edges':[],'hyperedges':[]}

all_nodes = cached['nodes'] + new.get('nodes', [])
all_edges = cached['edges'] + new.get('edges', [])
all_hyperedges = cached.get('hyperedges', []) + new.get('hyperedges', [])
seen = set()
deduped = []
for n in all_nodes:
    if n['id'] not in seen:
        seen.add(n['id'])
        deduped.append(n)

merged = {
    'nodes': deduped,
    'edges': all_edges,
    'hyperedges': all_hyperedges,
    'input_tokens': new.get('input_tokens', 0),
    'output_tokens': new.get('output_tokens', 0),
}
Path('graphify-out/.graphify_semantic.json').write_text(json.dumps(merged, indent=2))
print(f'추출 완료 - 노드 {len(deduped)}개, 엣지 {len(all_edges)}개 (캐시에서 {len(cached[\"nodes\"])}개, 새로 추가된 {len(new.get(\"nodes\",[]))}개)')
"
```

임시 파일 정리: `rm -f graphify-out/.graphify_cached.json graphify-out/.graphify_uncached.txt graphify-out/.graphify_semantic_new.json`

#### 파트 C - AST와 의미론적 결과를 최종 추출본으로 병합

```bash
$(cat graphify-out/.graphify_python) -c "
import sys, json
from pathlib import Path

ast = json.loads(Path('graphify-out/.graphify_ast.json').read_text())
sem = json.loads(Path('graphify-out/.graphify_semantic.json').read_text())

# 병합: AST 노드를 먼저 넣고, 의미론적 노드는 id를 기준으로 중복 제거
seen = {n['id'] for n in ast['nodes']}
merged_nodes = list(ast['nodes'])
for n in sem['nodes']:
    if n['id'] not in seen:
        merged_nodes.append(n)
        seen.add(n['id'])

merged_edges = ast['edges'] + sem['edges']
merged_hyperedges = sem.get('hyperedges', [])
merged = {
    'nodes': merged_nodes,
    'edges': merged_edges,
    'hyperedges': merged_hyperedges,
    'input_tokens': sem.get('input_tokens', 0),
    'output_tokens': sem.get('output_tokens', 0),
}
Path('graphify-out/.graphify_extract.json').write_text(json.dumps(merged, indent=2))
total = len(merged_nodes)
edges = len(merged_edges)
print(f'병합 완료: 노드 {total}개, 엣지 {edges}개 (AST {len(ast[\"nodes\"])}개 + 의미론적 {len(sem[\"nodes\"])}개)')
"
```

### 4단계 - 그래프 빌드, 클러스터링, 분석, 출력 생성

**시작하기 전에:** `--directed` 플래그가 주어졌는지 확인하세요. 주어졌다면, 아래 코드 블록의 `build_from_json()`에 `directed=True`를 전달하세요. 이는 엣지 방향(소스→대상)을 보존하는 `DiGraph`를 빌드합니다(기본값은 무방향 `Graph`임).

```bash
mkdir -p graphify-out
$(cat graphify-out/.graphify_python) -c "
import sys, json
from graphify.build import build_from_json
from graphify.cluster import cluster, score_all
from graphify.analyze import god_nodes, surprising_connections, suggest_questions
from graphify.report import generate
from graphify.export import to_json
from pathlib import Path

extraction = json.loads(Path('graphify-out/.graphify_extract.json').read_text())
detection  = json.loads(Path('graphify-out/.graphify_detect.json').read_text())

G = build_from_json(extraction)
communities = cluster(G)
cohesion = score_all(G, communities)
tokens = {'input': extraction.get('input_tokens', 0), 'output': extraction.get('output_tokens', 0)}
gods = god_nodes(G)
surprises = surprising_connections(G, communities)
labels = {cid: 'Community ' + str(cid) for cid in communities}
# 임시 질문 - 5단계에서 실제 레이블과 함께 재생성됨
questions = suggest_questions(G, communities, labels)

report = generate(G, communities, cohesion, labels, gods, surprises, detection, tokens, 'INPUT_PATH', suggested_questions=questions)
Path('graphify-out/GRAPH_REPORT.md').write_text(report)
to_json(G, communities, 'graphify-out/graph.json')

analysis = {
    'communities': {str(k): v for k, v in communities.items()},
    'cohesion': {str(k): v for k, v in cohesion.items()},
    'gods': gods,
    'surprises': surprises,
    'questions': questions,
}
Path('graphify-out/.graphify_analysis.json').write_text(json.dumps(analysis, indent=2))
if G.number_of_nodes() == 0:
    print('오류: 그래프가 비어 있습니다 - 추출 결과 노드가 생성되지 않았습니다.')
    print('가능한 원인: 모든 파일을 건너뛰었거나, 바이너리 전용 코퍼스이거나, 추출이 실패했습니다.')
    raise SystemExit(1)
print(f'그래프: 노드 {G.number_of_nodes()}개, 엣지 {G.number_of_edges()}개, 커뮤니티 {len(communities)}개')
"
```

이 단계에서 `ERROR: Graph is empty`가 출력되면, 중지하고 사용자에게 무슨 일이 발생했는지 알리세요 - 레이블 지정이나 시각화로 진행하지 마세요.

`INPUT_PATH`를 실제 경로로 교체하세요.

### 5단계 - 커뮤니티 레이블 지정

`graphify-out/.graphify_analysis.json`을 읽으세요. 각 커뮤니티 키에 대해 노드 레이블을 살펴보고, 쉬운 언어로 된 2~5단어 분량의 이름(예: "Attention Mechanism", "Training Pipeline", "Data Loading")을 작성하세요.

그런 다음 보고서를 재생성하고 시각화 도구를 위해 레이블을 저장하세요:

```bash
$(cat graphify-out/.graphify_python) -c "
import sys, json
from graphify.build import build_from_json
from graphify.cluster import score_all
from graphify.analyze import god_nodes, surprising_connections, suggest_questions
from graphify.report import generate
from pathlib import Path

extraction = json.loads(Path('graphify-out/.graphify_extract.json').read_text())
detection  = json.loads(Path('graphify-out/.graphify_detect.json').read_text())
analysis   = json.loads(Path('graphify-out/.graphify_analysis.json').read_text())

G = build_from_json(extraction)
communities = {int(k): v for k, v in analysis['communities'].items()}
cohesion = {int(k): v for k, v in analysis['cohesion'].items()}
tokens = {'input': extraction.get('input_tokens', 0), 'output': extraction.get('output_tokens', 0)}

# LABELS - 이 부분을 위에서 선택한 이름으로 교체하세요
labels = LABELS_DICT

# 실제 커뮤니티 레이블을 사용하여 질문 재생성 (레이블은 질문의 표현에 영향을 줍니다)
questions = suggest_questions(G, communities, labels)

report = generate(G, communities, cohesion, labels, analysis['gods'], analysis['surprises'], detection, tokens, 'INPUT_PATH', suggested_questions=questions)
Path('graphify-out/GRAPH_REPORT.md').write_text(report)
Path('graphify-out/.graphify_labels.json').write_text(json.dumps({str(k): v for k, v in labels.items()}))
print('커뮤니티 레이블로 보고서가 업데이트되었습니다.')
"
```

`LABELS_DICT`를 당신이 구성한 실제 딕셔너리(예: `{0: "Attention Mechanism", 1: "Training Pipeline"}`)로 교체하세요.
`INPUT_PATH`를 실제 경로로 교체하세요.

### 6단계 - Obsidian 볼트 (선택 사항) + HTML 생성

**HTML은 항상 생성합니다** (`--no-viz`가 지정되지 않은 한). **Obsidian 볼트는 `--obsidian` 플래그가 명시적으로 주어진 경우에만 생성합니다** — 그렇지 않으면 건너뛰세요. 이 작업은 노드당 하나의 파일을 생성합니다.

`--obsidian`이 주어진 경우:

- `--obsidian-dir <경로>`도 함께 주어졌다면, 해당 경로를 볼트 디렉토리로 사용합니다. 그렇지 않으면 기본값 `graphify-out/obsidian`을 사용합니다.

```bash
$(cat graphify-out/.graphify_python) -c "
import sys, json
from graphify.build import build_from_json
from graphify.export import to_obsidian, to_canvas
from pathlib import Path

extraction = json.loads(Path('graphify-out/.graphify_extract.json').read_text())
analysis   = json.loads(Path('graphify-out/.graphify_analysis.json').read_text())
labels_raw = json.loads(Path('graphify-out/.graphify_labels.json').read_text()) if Path('graphify-out/.graphify_labels.json').exists() else {}

G = build_from_json(extraction)
communities = {int(k): v for k, v in analysis['communities'].items()}
cohesion = {int(k): v for k, v in analysis['cohesion'].items()}
labels = {int(k): v for k, v in labels_raw.items()}

obsidian_dir = 'OBSIDIAN_DIR'  # --obsidian-dir 값으로 교체하거나, 없으면 'graphify-out/obsidian' 사용

n = to_obsidian(G, communities, obsidian_dir, community_labels=labels or None, cohesion=cohesion)
print(f'Obsidian 볼트: 노트 {n}개가 {obsidian_dir}/ 에 작성되었습니다.')

to_canvas(G, communities, f'{obsidian_dir}/graph.canvas', community_labels=labels or None)
print(f'캔버스: {obsidian_dir}/graph.canvas - 구조화된 커뮤니티 레이아웃을 보려면 Obsidian에서 여세요.')
print()
print(f'Obsidian에서 {obsidian_dir}/ 를 볼트로 여세요.')
print('  그래프 뷰(Graph view) - 노드가 커뮤니티별로 색칠됨 (자동 설정됨)')
print('  graph.canvas         - 커뮤니티를 그룹으로 하는 구조화된 레이아웃')
print('  _COMMUNITY_*         - 응집도 점수와 dataview 쿼리가 포함된 개요 노트')
"
```

HTML 그래프 생성 (`--no-viz`가 없는 한 항상 생성):

```bash
$(cat graphify-out/.graphify_python) -c "
import sys, json
from graphify.build import build_from_json
from graphify.export import to_html
from pathlib import Path

extraction = json.loads(Path('graphify-out/.graphify_extract.json').read_text())
analysis   = json.loads(Path('graphify-out/.graphify_analysis.json').read_text())
labels_raw = json.loads(Path('graphify-out/.graphify_labels.json').read_text()) if Path('graphify-out/.graphify_labels.json').exists() else {}

G = build_from_json(extraction)
communities = {int(k): v for k, v in analysis['communities'].items()}
labels = {int(k): v for k, v in labels_raw.items()}

if G.number_of_nodes() > 5000:
    print(f'그래프의 노드가 {G.number_of_nodes()}개입니다 - HTML 시각화로는 너무 큽니다. 대신 Obsidian 볼트를 사용하세요.')
else:
    to_html(G, communities, 'graphify-out/graph.html', community_labels=labels or None)
    print('graph.html 생성됨 - 서버 없이 어떤 브라우저에서든 열 수 있습니다.')
"
```

### 6b단계 - 위키 (--wiki 플래그가 있는 경우에만)

**원래 명령에 `--wiki`가 명시적으로 주어진 경우에만 이 단계를 실행하세요.**

`.graphify_labels.json`을 계속 사용할 수 있도록 9단계(정리) 전에 이것을 실행하세요.

```bash
$(cat graphify-out/.graphify_python) -c "
import json
from graphify.build import build_from_json
from graphify.wiki import to_wiki
from graphify.analyze import god_nodes
from pathlib import Path

extraction = json.loads(Path('graphify-out/.graphify_extract.json').read_text())
analysis   = json.loads(Path('graphify-out/.graphify_analysis.json').read_text())
labels_raw = json.loads(Path('graphify-out/.graphify_labels.json').read_text()) if Path('graphify-out/.graphify_labels.json').exists() else {}

G = build_from_json(extraction)
communities = {int(k): v for k, v in analysis['communities'].items()}
cohesion = {int(k): v for k, v in analysis['cohesion'].items()}
labels = {int(k): v for k, v in labels_raw.items()}
gods = god_nodes(G)

n = to_wiki(G, communities, 'graphify-out/wiki', community_labels=labels or None, cohesion=cohesion, god_nodes_data=gods)
print(f'위키: 문서 {n}개가 graphify-out/wiki/ 에 작성되었습니다.')
print('  graphify-out/wiki/index.md  ->  에이전트 진입점')
"
```

### 7단계 - Neo4j 내보내기 (--neo4j 또는 --neo4j-push 플래그가 있는 경우에만)

**`--neo4j`인 경우** - 수동 임포트를 위한 Cypher 파일을 생성합니다:

```bash
$(cat graphify-out/.graphify_python) -c "
import sys, json
from graphify.build import build_from_json
from graphify.export import to_cypher
from pathlib import Path

G = build_from_json(json.loads(Path('graphify-out/.graphify_extract.json').read_text()))
to_cypher(G, 'graphify-out/cypher.txt')
print('cypher.txt 생성됨 - 다음 명령으로 임포트하세요: cypher-shell < graphify-out/cypher.txt')
"
```

**`--neo4j-push <uri>`인 경우** - 실행 중인 Neo4j 인스턴스로 직접 푸시합니다. 자격 증명이 제공되지 않았다면 사용자에게 물어보세요:

```bash
$(cat graphify-out/.graphify_python) -c "
import sys, json
from graphify.build import build_from_json
from graphify.cluster import cluster
from graphify.export import push_to_neo4j
from pathlib import Path

extraction = json.loads(Path('graphify-out/.graphify_extract.json').read_text())
analysis   = json.loads(Path('graphify-out/.graphify_analysis.json').read_text())
G = build_from_json(extraction)
communities = {int(k): v for k, v in analysis['communities'].items()}

result = push_to_neo4j(G, uri='NEO4J_URI', user='NEO4J_USER', password='NEO4J_PASSWORD', communities=communities)
print(f'Neo4j에 푸시 완료: 노드 {result[\"nodes\"]}개, 엣지 {result[\"edges\"]}개')
"
```

`NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`를 실제 값으로 교체하세요. 기본 URI는 `bolt://localhost:7687`이며, 기본 사용자는 `neo4j`입니다. MERGE를 사용하므로 중복을 생성하지 않고 안전하게 다시 실행할 수 있습니다.

### 7b단계 - SVG 내보내기 (--svg 플래그가 있는 경우에만)

```bash
$(cat graphify-out/.graphify_python) -c "
import sys, json
from graphify.build import build_from_json
from graphify.export import to_svg
from pathlib import Path

extraction = json.loads(Path('graphify-out/.graphify_extract.json').read_text())
analysis   = json.loads(Path('graphify-out/.graphify_analysis.json').read_text())
labels_raw = json.loads(Path('graphify-out/.graphify_labels.json').read_text()) if Path('graphify-out/.graphify_labels.json').exists() else {}

G = build_from_json(extraction)
communities = {int(k): v for k, v in analysis['communities'].items()}
labels = {int(k): v for k, v in labels_raw.items()}

to_svg(G, communities, 'graphify-out/graph.svg', community_labels=labels or None)
print('graph.svg 생성됨 - Obsidian, Notion, GitHub README에 임베드 가능')
"
```

### 7c단계 - GraphML 내보내기 (--graphml 플래그가 있는 경우에만)

```bash
$(cat graphify-out/.graphify_python) -c "
import json
from graphify.build import build_from_json
from graphify.export import to_graphml
from pathlib import Path

extraction = json.loads(Path('graphify-out/.graphify_extract.json').read_text())
analysis   = json.loads(Path('graphify-out/.graphify_analysis.json').read_text())

G = build_from_json(extraction)
communities = {int(k): v for k, v in analysis['communities'].items()}

to_graphml(G, communities, 'graphify-out/graph.graphml')
print('graph.graphml 생성됨 - Gephi, yEd 또는 아무 GraphML 도구에서 열 수 있습니다.')
"
```

### 7d단계 - MCP 서버 (--mcp 플래그가 있는 경우에만)

```bash
python3 -m graphify.serve graphify-out/graph.json
```

이는 다른 에이전트가 실시간으로 그래프를 쿼리할 수 있도록 `query_graph`, `get_node`, `get_neighbors`, `get_community`, `god_nodes`, `graph_stats`, `shortest_path` 도구를 노출하는 stdio MCP 서버를 시작합니다. Claude Desktop이나 MCP 호환 에이전트 오케스트레이터에 추가하세요.

Claude Desktop에서 구성하려면, `claude_desktop_config.json`에 다음을 추가하세요:

```json
{
  "mcpServers": {
    "graphify": {
      "command": "python3",
      "args": ["-m", "graphify.serve", "/absolute/path/to/graphify-out/graph.json"]
    }
  }
}
```

### 8단계 - 토큰 감소 벤치마크 (total_words > 5000인 경우에만)

`graphify-out/.graphify_detect.json`의 `total_words`가 5,000보다 크면 다음을 실행하세요:

```bash
$(cat graphify-out/.graphify_python) -c "
import json
from graphify.benchmark import run_benchmark, print_benchmark
from pathlib import Path

detection = json.loads(Path('graphify-out/.graphify_detect.json').read_text())
result = run_benchmark('graphify-out/graph.json', corpus_words=detection['total_words'])
print_benchmark(result)
"
```

채팅창에 출력을 직접 인쇄하세요. `total_words <= 5000`인 경우 조용히 건너뛰세요 - 소규모 코퍼스에 대한 그래프의 가치는 구조적 명확성에 있지 토큰 압축에 있지 않습니다.

---

### 9단계 - 매니페스트 저장, 비용 추적기 업데이트, 정리 및 보고

```bash
$(cat graphify-out/.graphify_python) -c "
import json
from pathlib import Path
from datetime import datetime, timezone
from graphify.detect import save_manifest

# --update를 위한 매니페스트 저장
detect = json.loads(Path('graphify-out/.graphify_detect.json').read_text())
save_manifest(detect['files'])

# 누적 비용 추적기 업데이트
extract = json.loads(Path('graphify-out/.graphify_extract.json').read_text())
input_tok = extract.get('input_tokens', 0)
output_tok = extract.get('output_tokens', 0)

cost_path = Path('graphify-out/cost.json')
if cost_path.exists():
    cost = json.loads(cost_path.read_text())
else:
    cost = {'runs': [], 'total_input_tokens': 0, 'total_output_tokens': 0}

cost['runs'].append({
    'date': datetime.now(timezone.utc).isoformat(),
    'input_tokens': input_tok,
    'output_tokens': output_tok,
    'files': detect.get('total_files', 0),
})
cost['total_input_tokens'] += input_tok
cost['total_output_tokens'] += output_tok
cost_path.write_text(json.dumps(cost, indent=2))

print(f'이번 실행: 입력 토큰 {input_tok:,}개, 출력 토큰 {output_tok:,}개')
print(f'전체 누적: 입력 {cost[\"total_input_tokens\"]:,}개, 출력 {cost[\"total_output_tokens\"]:,}개 (총 {len(cost[\"runs\"])}회 실행)')
"
rm -f graphify-out/.graphify_detect.json graphify-out/.graphify_extract.json graphify-out/.graphify_ast.json graphify-out/.graphify_semantic.json graphify-out/.graphify_analysis.json graphify-out/.graphify_labels.json
rm -f graphify-out/.needs_update 2>/dev/null || true
```

사용자에게 다음과 같이 알리세요 (`--obsidian` 플래그가 주어진 경우에만 obsidian 줄을 포함하세요):

```text
그래프가 완성되었습니다. 출력 결과는 PATH_TO_DIR/graphify-out/ 에 있습니다.

  graph.html            - 대화형 그래프, 브라우저에서 엽니다
  GRAPH_REPORT.md       - 감사 보고서(audit report)
  graph.json            - 원시 그래프 데이터
  obsidian/             - Obsidian 볼트 (--obsidian이 주어진 경우에만)
```

graphify가 귀하의 시간을 절약해 주었다면 후원을 고려해 보세요: <https://github.com/sponsors/safishamsi>

`PATH_TO_DIR`을 처리된 디렉토리의 실제 절대 경로로 교체하세요.

그런 다음 `GRAPH_REPORT.md`의 다음 섹션들을 채팅에 직접 붙여넣으세요:

- God Nodes (최상위 노드)
- Surprising Connections (놀라운 연결)
- Suggested Questions (추천 질문)

보고서 전체를 붙여넣지 마세요 - 위 세 섹션만 붙여넣으세요. 간결하게 유지하세요.

그런 다음 즉시 탐색을 제안하세요. 보고서의 추천 질문 중 가장 흥미로운 질문(가장 많은 커뮤니티 경계를 넘나들거나 가장 놀라운 브릿지 노드가 있는 질문) 하나를 선택하여 다음과 같이 질문하세요:

> "이 그래프가 대답할 수 있는 가장 흥미로운 질문: **[질문]**. 제가 이 경로를 추적해 볼까요?"

사용자가 동의하면, 그래프에서 `/graphify query "[질문]"`을 실행하고 그래프 구조(어떤 노드가 연결되는지, 어떤 커뮤니티 경계가 교차되는지, 경로가 무엇을 드러내는지)를 사용하여 사용자에게 답변 과정을 안내하세요. 사용자가 탐색을 원할 때까지 계속 진행하세요. 세션이 일회성 보고서가 아닌 내비게이션(탐색)처럼 느껴지도록 각 답변은 자연스러운 후속 질문("이것은 X와 연결됩니다 - 더 깊이 들어가 볼까요?")으로 끝나야 합니다.

그래프는 지도입니다. 파이프라인이 완료된 후 당신의 역할은 안내자(가이드)가 되는 것입니다.

---

## 하위 명령어를 위한 인터프리터 가드 (Interpreter guard for subcommands)

아래의 하위 명령어(`--update`, `--cluster-only`, `query`, `path`, `explain`, `add`)를 실행하기 전에, `.graphify_python`이 존재하는지 확인하세요. 누락된 경우(예: 사용자가 `graphify-out/`을 삭제함) 인터프리터를 먼저 다시 설정하세요:

```bash
if [ ! -f graphify-out/.graphify_python ]; then
    GRAPHIFY_BIN=$(which graphify 2>/dev/null)
    if [ -n "$GRAPHIFY_BIN" ]; then
        PYTHON=$(head -1 "$GRAPHIFY_BIN" | tr -d '#!')
        case "$PYTHON" in *[!a-zA-Z0-9/_.-]*) PYTHON="python3" ;; esac
    else
        PYTHON="python3"
    fi
    mkdir -p graphify-out
    "$PYTHON" -c "import sys; open('graphify-out/.graphify_python', 'w').write(sys.executable)"
fi
```

## --update 용도 (증분 재추출)

마지막 실행 이후 파일을 추가하거나 수정한 경우 사용합니다. 변경된 파일만 다시 추출하여 토큰과 시간을 절약합니다.

```bash
$(cat graphify-out/.graphify_python) -c "
import sys, json
from graphify.detect import detect_incremental, save_manifest
from pathlib import Path

result = detect_incremental(Path('INPUT_PATH'))
new_total = result.get('new_total', 0)
print(json.dumps(result, indent=2))
Path('graphify-out/.graphify_incremental.json').write_text(json.dumps(result))
if new_total == 0:
    print('마지막 실행 이후 변경된 파일이 없습니다. 업데이트할 내용이 없습니다.')
    raise SystemExit(0)
print(f'재추출할 새롭거나 변경된 파일이 {new_total}개 있습니다.')
"
```

새 파일이 있는 경우, 먼저 변경된 모든 파일이 코드 파일인지 확인합니다:

```bash
$(cat graphify-out/.graphify_python) -c "
import json
from pathlib import Path

result = json.loads(open('graphify-out/.graphify_incremental.json').read()) if Path('graphify-out/.graphify_incremental.json').exists() else {}
code_exts = {'.py','.ts','.js','.go','.rs','.java','.cpp','.c','.rb','.swift','.kt','.cs','.scala','.php','.cc','.cxx','.hpp','.h','.kts','.lua','.toc'}
new_files = result.get('new_files', {})
all_changed = [f for files in new_files.values() for f in files]
code_only = all(Path(f).suffix.lower() in code_exts for f in all_changed)
print('code_only:', code_only)
"
```

`code_only`가 True인 경우: `[graphify update] 코드 전용 변경 감지됨 - 의미론적 추출 생략 (LLM 불필요)`를 출력하고, 변경된 파일에 대해 파트 3A(AST)만 실행하며 파트 3B(하위 에이전트 작업 없음)는 완전히 건너뛰고 바로 병합 및 4~8단계로 넘어갑니다.

`code_only`가 False인 경우 (변경된 파일 중 문서/논문/이미지가 하나라도 있는 경우): 평소와 같이 3A~3C 파이프라인 전체를 실행합니다.

그런 다음:

```bash
$(cat graphify-out/.graphify_python) -c "
import sys, json
from graphify.build import build_from_json
from graphify.export import to_json
from networkx.readwrite import json_graph
import networkx as nx
from pathlib import Path

# 기존 그래프 로드
existing_data = json.loads(Path('graphify-out/graph.json').read_text())
G_existing = json_graph.node_link_graph(existing_data, edges='links')

# 새 추출본 로드
new_extraction = json.loads(Path('graphify-out/.graphify_extract.json').read_text())
G_new = build_from_json(new_extraction)

# 삭제된 파일의 노드 가지치기(Prune)
incremental = json.loads(Path('graphify-out/.graphify_incremental.json').read_text())
deleted = set(incremental.get('deleted_files', []))
if deleted:
    to_remove = [n for n, d in G_existing.nodes(data=True) if d.get('source_file') in deleted]
    G_existing.remove_nodes_from(to_remove)
    print(f'{len(deleted)}개의 삭제된 파일에서 {len(to_remove)}개의 고스트 노드(유령 노드)를 제거했습니다.')

# 병합: 기존 그래프에 새 노드/엣지 병합
G_existing.update(G_new)
print(f'병합 완료: 노드 {G_existing.number_of_nodes()}개, 엣지 {G_existing.number_of_edges()}개')

# 4단계에서 전체 그래프를 읽을 수 있도록 병합된 결과를 .graphify_extract.json에 다시 씀
merged_out = {
    'nodes': [{'id': n, **d} for n, d in G_existing.nodes(data=True)],
    'edges': [{'source': u, 'target': v, **d} for u, v, d in G_existing.edges(data=True)],
    'hyperedges': new_extraction.get('hyperedges', []),
    'input_tokens': new_extraction.get('input_tokens', 0),
    'output_tokens': new_extraction.get('output_tokens', 0),
}
Path('graphify-out/.graphify_extract.json').write_text(json.dumps(merged_out))
print(f'[graphify update] 병합된 추출본 작성 완료 (노드 {len(merged_out[\"nodes\"])}개, 엣지 {len(merged_out[\"edges\"])}개)')
" 
```

그 후 병합된 그래프에 대해 평소와 같이 4~8단계를 실행합니다.

4단계 이후 그래프 변경점(diff)을 보여주세요:

```bash
$(cat graphify-out/.graphify_python) -c "
import json
from graphify.analyze import graph_diff
from graphify.build import build_from_json
from networkx.readwrite import json_graph
import networkx as nx
from pathlib import Path

# 병합 전에 작성된 백업에서 이전 그래프(업데이트 전) 로드
old_data = json.loads(Path('graphify-out/.graphify_old.json').read_text()) if Path('graphify-out/.graphify_old.json').exists() else None
new_extract = json.loads(Path('graphify-out/.graphify_extract.json').read_text())
G_new = build_from_json(new_extract)

if old_data:
    G_old = json_graph.node_link_graph(old_data, edges='links')
    diff = graph_diff(G_old, G_new)
    print(diff['summary'])
    if diff['new_nodes']:
        print('새 노드:', ', '.join(n['label'] for n in diff['new_nodes'][:5]))
    if diff['new_edges']:
        print('새 엣지:', len(diff['new_edges']))
"
```

병합 단계 전에 이전 그래프를 저장하세요: `cp graphify-out/graph.json graphify-out/.graphify_old.json`
종료 후 정리: `rm -f graphify-out/.graphify_old.json`

---

## --cluster-only 용도

1~3단계를 건너뜁니다. `graphify-out/graph.json`에서 기존 그래프를 로드하고 클러스터링을 다시 실행합니다:

```bash
$(cat graphify-out/.graphify_python) -c "
import sys, json
from graphify.cluster import cluster, score_all
from graphify.analyze import god_nodes, surprising_connections
from graphify.report import generate
from graphify.export import to_json
from networkx.readwrite import json_graph
import networkx as nx
from pathlib import Path

data = json.loads(Path('graphify-out/graph.json').read_text())
G = json_graph.node_link_graph(data, edges='links')

detection = {'total_files': 0, 'total_words': 99999, 'needs_graph': True, 'warning': None,
             'files': {'code': [], 'document': [], 'paper': []}}
tokens = {'input': 0, 'output': 0}

communities = cluster(G)
cohesion = score_all(G, communities)
gods = god_nodes(G)
surprises = surprising_connections(G, communities)
labels = {cid: 'Community ' + str(cid) for cid in communities}

report = generate(G, communities, cohesion, labels, gods, surprises, detection, tokens, '.')
Path('graphify-out/GRAPH_REPORT.md').write_text(report)
to_json(G, communities, 'graphify-out/graph.json')

analysis = {
    'communities': {str(k): v for k, v in communities.items()},
    'cohesion': {str(k): v for k, v in cohesion.items()},
    'gods': gods,
    'surprises': surprises,
}
Path('graphify-out/.graphify_analysis.json').write_text(json.dumps(analysis, indent=2))
print(f'재클러스터링 완료: 커뮤니티 {len(communities)}개')
"
```

그런 다음 평소와 같이 5~9단계를 실행합니다(커뮤니티 레이블 지정, 시각화 생성, 벤치마크, 정리, 보고서 생성).

---

## /graphify query 용도

두 가지 탐색 모드가 있습니다 - 질문에 따라 선택하세요:

| 모드 | 플래그 | 가장 적합한 경우 |
|------|------|----------|
| BFS (기본) | *(없음)* | "X는 무엇과 연결되어 있나요?" - 넓은 문맥, 가장 가까운 이웃부터 탐색 |
| DFS | `--dfs` | "X는 Y에 어떻게 도달하나요?" - 특정 체인이나 종속성 경로 추적 |

먼저 그래프가 존재하는지 확인합니다:

```bash
$(cat graphify-out/.graphify_python) -c "
from pathlib import Path
if not Path('graphify-out/graph.json').exists():
    print('오류: 그래프를 찾을 수 없습니다. 그래프를 빌드하려면 먼저 /graphify <경로> 를 실행하세요.')
    raise SystemExit(1)
"
```

실패하면 사용자에게 중지하고 `/graphify <경로>`를 먼저 실행하라고 알리세요.

`graphify-out/graph.json`을 로드한 후:

1. 질문의 주요 핵심 용어와 레이블이 가장 잘 일치하는 1~3개의 노드를 찾습니다.
2. 각 시작 노드에서 적절한 탐색을 실행합니다.
3. 서브그래프를 읽습니다 - 노드 레이블, 엣지 관계, 신뢰도(confidence) 태그, 소스 위치.
4. **오직** 그래프에 포함된 내용만을 사용하여 답변하세요. 특정 사실을 인용할 때는 `source_location`을 인용하세요.
5. 그래프에 충분한 정보가 없다면 그렇다고 말하세요 - 엣지를 지어내어 환각(hallucinate)하지 마세요.

```bash
$(cat graphify-out/.graphify_python) -c "
import sys, json
from networkx.readwrite import json_graph
import networkx as nx
from pathlib import Path

data = json.loads(Path('graphify-out/graph.json').read_text())
G = json_graph.node_link_graph(data, edges='links')

question = 'QUESTION'
mode = 'MODE'  # 'bfs' 또는 'dfs'
terms = [t.lower() for t in question.split() if len(t) > 3]

# 가장 잘 일치하는 시작 노드 찾기
scored = []
for nid, ndata in G.nodes(data=True):
    label = ndata.get('label', '').lower()
    score = sum(1 for t in terms if t in label)
    if score > 0:
        scored.append((score, nid))
scored.sort(reverse=True)
start_nodes = [nid for _, nid in scored[:3]]

if not start_nodes:
    print('쿼리 용어와 일치하는 노드를 찾을 수 없습니다:', terms)
    sys.exit(0)

subgraph_nodes = set()
subgraph_edges = []

if mode == 'dfs':
    # DFS: 역추적하기 전에 하나의 경로를 가능한 한 깊게 따라갑니다.
    # 전체 그래프 탐색을 피하기 위해 깊이를 6으로 제한합니다.
    visited = set()
    stack = [(n, 0) for n in reversed(start_nodes)]
    while stack:
        node, depth = stack.pop()
        if node in visited or depth > 6:
            continue
        visited.add(node)
        subgraph_nodes.add(node)
        for neighbor in G.neighbors(node):
            if neighbor not in visited:
                stack.append((neighbor, depth + 1))
                subgraph_edges.append((node, neighbor))
else:
    # BFS: 최대 깊이 3까지 모든 이웃을 계층별로 탐색합니다.
    frontier = set(start_nodes)
    subgraph_nodes = set(start_nodes)
    for _ in range(3):
        next_frontier = set()
        for n in frontier:
            for neighbor in G.neighbors(n):
                if neighbor not in subgraph_nodes:
                    next_frontier.add(neighbor)
                    subgraph_edges.append((n, neighbor))
        subgraph_nodes.update(next_frontier)
        frontier = next_frontier

# 토큰 예산을 고려한 출력: 관련성 순위 지정, 예산에서 자르기 (토큰당 ~4자)
token_budget = BUDGET  # 기본값 2000
char_budget = token_budget * 4

# 순위가 매겨진 출력을 위해 각 노드의 용어 일치도로 점수 계산
def relevance(nid):
    label = G.nodes[nid].get('label', '').lower()
    return sum(1 for t in terms if t in label)

ranked_nodes = sorted(subgraph_nodes, key=relevance, reverse=True)

lines = [f'탐색: {mode.upper()} | 시작 노드: {[G.nodes[n].get(\"label\",n) for n in start_nodes]} | 노드 {len(subgraph_nodes)}개']
for nid in ranked_nodes:
    d = G.nodes[nid]
    lines.append(f'  NODE {d.get(\"label\", nid)} [src={d.get(\"source_file\",\"\")} loc={d.get(\"source_location\",\"\")}]')
for u, v in subgraph_edges:
    if u in subgraph_nodes and v in subgraph_nodes:
        d = G.edges[u, v]
        lines.append(f'  EDGE {G.nodes[u].get(\"label\",u)} --{d.get(\"relation\",\"\")} [{d.get(\"confidence\",\"\")}]--> {G.nodes[v].get(\"label\",v)}')

output = '\n'.join(lines)
if len(output) > char_budget:
    output = output[:char_budget] + f'\n... (~{token_budget} 토큰 예산에서 잘림 - 더 보려면 --budget N 사용)'
print(output)
"
```

`QUESTION`을 사용자의 실제 질문으로, `MODE`를 `bfs` 또는 `dfs`로, `BUDGET`을 토큰 예산(기본값 `2000` 또는 `--budget N`에 지정된 값)으로 교체하세요. 그런 다음 위의 서브그래프 출력을 기반으로 답변하세요.

답변을 작성한 후, 향후 쿼리 성능 향상을 위해 이를 그래프에 다시 저장하세요:

```bash
$(cat graphify-out/.graphify_python) -m graphify save-result --question "QUESTION" --answer "ANSWER" --type query --nodes NODE1 NODE2
```

`QUESTION`을 질문으로, `ANSWER`를 전체 답변 텍스트로, `SOURCE_NODES`를 인용한 노드 레이블 목록으로 교체하세요. 이것은 피드백 루프를 완성합니다: 다음 `--update` 실행 시 이 질의응답(Q&A)이 그래프의 노드로 추출될 것입니다.

---

## /graphify path 용도

그래프에서 두 개의 명명된 개념 사이의 최단 경로를 찾습니다.

먼저 그래프가 존재하는지 확인합니다:

```bash
$(cat graphify-out/.graphify_python) -c "
from pathlib import Path
if not Path('graphify-out/graph.json').exists():
    print('오류: 그래프를 찾을 수 없습니다. 그래프를 빌드하려면 먼저 /graphify <경로> 를 실행하세요.')
    raise SystemExit(1)
"
```

실패하면 사용자에게 중지하고 `/graphify <경로>`를 먼저 실행하라고 알리세요.

```bash
$(cat graphify-out/.graphify_python) -c "
import json, sys
import networkx as nx
from networkx.readwrite import json_graph
from pathlib import Path

data = json.loads(Path('graphify-out/graph.json').read_text())
G = json_graph.node_link_graph(data, edges='links')

a_term = 'NODE_A'
b_term = 'NODE_B'

def find_node(term):
    term = term.lower()
    scored = sorted(
        [(sum(1 for w in term.split() if w in G.nodes[n].get('label','').lower()), n)
         for n in G.nodes()],
        reverse=True
    )
    return scored[0][1] if scored and scored[0][0] > 0 else None

src = find_node(a_term)
tgt = find_node(b_term)

if not src or not tgt:
    print(f'다음과 일치하는 노드를 찾을 수 없습니다: {a_term!r} 또는 {b_term!r}')
    sys.exit(0)

try:
    path = nx.shortest_path(G, src, tgt)
    print(f'최단 경로 ({len(path)-1} 홉):')
    for i, nid in enumerate(path):
        label = G.nodes[nid].get('label', nid)
        if i < len(path) - 1:
            edge = G.edges[nid, path[i+1]]
            rel = edge.get('relation', '')
            conf = edge.get('confidence', '')
            print(f'  {label} --{rel}--> [{conf}]')
        else:
            print(f'  {label}')
except nx.NetworkXNoPath:
    print(f'{a_term!r}와(과) {b_term!r} 사이의 경로를 찾을 수 없습니다.')
except nx.NodeNotFound as e:
    print(f'노드를 찾을 수 없음: {e}')
"
```

`NODE_A`와 `NODE_B`를 사용자가 제시한 실제 개념 이름으로 교체하세요. 그런 다음 각 홉(hop)이 무엇을 의미하고 왜 중요한지 이해하기 쉬운 언어로 경로를 설명하세요.

설명을 작성한 후 다시 저장하세요:

```bash
$(cat graphify-out/.graphify_python) -m graphify save-result --question "Path from NODE_A to NODE_B" --answer "ANSWER" --type path_query --nodes NODE_A NODE_B
```

---

## /graphify explain 용도

단일 노드와 그 노드에 연결된 모든 것에 대해 쉬운 언어로 설명을 제공합니다.

먼저 그래프가 존재하는지 확인합니다:

```bash
$(cat graphify-out/.graphify_python) -c "
from pathlib import Path
if not Path('graphify-out/graph.json').exists():
    print('오류: 그래프를 찾을 수 없습니다. 그래프를 빌드하려면 먼저 /graphify <경로> 를 실행하세요.')
    raise SystemExit(1)
"
```

실패하면 사용자에게 중지하고 `/graphify <경로>`를 먼저 실행하라고 알리세요.

```bash
$(cat graphify-out/.graphify_python) -c "
import json, sys
import networkx as nx
from networkx.readwrite import json_graph
from pathlib import Path

data = json.loads(Path('graphify-out/graph.json').read_text())
G = json_graph.node_link_graph(data, edges='links')

term = 'NODE_NAME'
term_lower = term.lower()

# 가장 잘 일치하는 노드 찾기
scored = sorted(
    [(sum(1 for w in term_lower.split() if w in G.nodes[n].get('label','').lower()), n)
     for n in G.nodes()],
    reverse=True
)
if not scored or scored[0][0] == 0:
    print(f'{term!r}과(와) 일치하는 노드가 없습니다')
    sys.exit(0)

nid = scored[0][1]
data_n = G.nodes[nid]
print(f'노드(NODE): {data_n.get(\"label\", nid)}')
print(f'  소스: {data_n.get(\"source_file\",\"unknown\")}')
print(f'  유형: {data_n.get(\"file_type\",\"unknown\")}')
print(f'  차수(degree): {G.degree(nid)}')
print()
print('연결(CONNECTIONS):')
for neighbor in G.neighbors(nid):
    edge = G.edges[nid, neighbor]
    nlabel = G.nodes[neighbor].get('label', neighbor)
    rel = edge.get('relation', '')
    conf = edge.get('confidence', '')
    src_file = G.nodes[neighbor].get('source_file', '')
    print(f'  --{rel}--> {nlabel} [{conf}] ({src_file})')
"
```

`NODE_NAME`을 사용자가 질문한 개념으로 교체하세요. 그런 다음 이 노드가 무엇인지, 어떤 것과 연결되어 있는지, 그리고 그 연결들이 왜 중요한지에 대해 3~5문장으로 설명을 작성하세요. 소스 위치를 인용 구문으로 사용하세요.

설명을 작성한 후 다시 저장하세요:

```bash
$(cat graphify-out/.graphify_python) -m graphify save-result --question "Explain NODE_NAME" --answer "ANSWER" --type explain --nodes NODE_NAME
```

---

## /graphify add 용도

URL을 가져와서 코퍼스에 추가한 다음, 그래프를 업데이트합니다.

```bash
$(cat graphify-out/.graphify_python) -c "
import sys
from graphify.ingest import ingest
from pathlib import Path

try:
    out = ingest('URL', Path('./raw'), author='AUTHOR', contributor='CONTRIBUTOR')
    print(f'저장됨: {out}')
except ValueError as e:
    print(f'오류: {e}', file=sys.stderr)
    sys.exit(1)
except RuntimeError as e:
    print(f'오류: {e}', file=sys.stderr)
    sys.exit(1)
"
```

`URL`을 실제 URL로 바꾸고, `AUTHOR`는 제공된 경우 사용자의 이름으로, `CONTRIBUTOR` 역시 동일하게 변경하세요. 명령어가 에러와 함께 종료된다면 사용자에게 무엇이 잘못되었는지 알리세요 - 조용히 넘어가지 마세요. 성공적으로 저장한 후에는, 새로운 파일을 기존 그래프에 병합하기 위해 `./raw` 폴더에 대해 `--update` 파이프라인을 자동으로 실행하세요.

지원되는 URL 유형 (자동 감지됨):

- YouTube / 모든 비디오 URL → yt-dlp를 통해 다운로드된 오디오, 다음 실행 시 `.txt`로 전사됨 (`pip install 'graphifyy[video]'` 필요)
- Twitter/X → oEmbed를 통해 가져오고 트윗 텍스트와 작성자와 함께 `.md`로 저장됨
- arXiv → 초록(abstract) + 메타데이터가 `.md`로 저장됨
- PDF → `.pdf`로 다운로드됨
- 이미지 (.png/.jpg/.webp) → 다운로드 후, 다음 실행 시 Claude 비전이 추출함
- 모든 웹페이지 → html2text를 통해 마크다운으로 변환됨

---

## --watch 용도

폴더를 모니터링하다 파일이 변경되면 그래프를 자동 업데이트하는 백그라운드 감시자(watcher)를 시작합니다.

```bash
python3 -m graphify.watch INPUT_PATH --debounce 3
```

`INPUT_PATH`를 감시할 폴더로 변경하세요. 변경된 사항에 따라 동작이 달라집니다:

- **코드 파일만 변경됨 (.py, .ts, .go 등):** 즉시 AST 추출 + 재빌드 + 클러스터링을 다시 실행하며, LLM은 필요하지 않습니다. `graph.json`과 `GRAPH_REPORT.md`가 자동으로 업데이트됩니다.
- **문서, 논문 또는 이미지 변경됨:** `graphify-out/needs_update` 플래그 파일을 작성하고 `/graphify --update`를 실행하라는 알림을 인쇄합니다 (LLM 의미론적 재추출 필요).

디바운스 (기본값 3초): 병렬 에이전트 쓰기 작업의 물결이 파일마다 재빌드를 트리거하지 않도록 모든 파일 작업이 멈출 때까지 기다렸다가 트리거합니다.

정지하려면 Ctrl+C를 누르세요.

에이전트 주도 워크플로우의 경우: 백그라운드 터미널에서 `--watch`를 실행하세요. 에이전트 작업 웨이브(wave) 사이에 발생하는 코드 변경 사항은 자동으로 반영됩니다. 에이전트가 문서나 메모도 작성하는 경우에는 작업 웨이브 이후에 수동으로 `/graphify --update`를 실행해야 합니다.

---

## git commit hook 용도

모든 커밋 후에 그래프를 자동 재빌드하는 post-commit 훅을 설치합니다. 백그라운드 프로세스가 필요하지 않으며 - 커밋당 한 번씩 트리거되고, 어떤 에디터와도 잘 작동합니다.

```bash
graphify hook install    # 설치
graphify hook uninstall  # 제거
graphify hook status     # 상태 확인
```

모든 `git commit` 후, 훅은 어떤 코드 파일이 변경되었는지 감지하고(`git diff HEAD~1`를 통해), 해당 파일들에 대해 AST 추출을 재실행한 다음 `graph.json`과 `GRAPH_REPORT.md`를 재빌드합니다. 문서/이미지 변경 사항은 훅에서 무시되므로, 이러한 변경 사항에 대해서는 수동으로 `/graphify --update`를 실행하세요.

post-commit 훅이 이미 존재하는 경우, graphify는 기존 내용을 덮어쓰지 않고 뒤에 덧붙입니다(append).

---

## 정직성 규칙 (Honesty Rules)

- 절대로 엣지를 지어내지(invent) 마세요. 불확실한 경우 AMBIGUOUS를 사용하세요.
- 코퍼스 확인 경고(corpus check warning)를 절대 건너뛰지 마세요.
- 보고서에 항상 토큰 비용을 표시하세요.
- 응집도(cohesion) 점수를 기호 뒤에 숨기지 마세요 - 원시 숫자(raw number) 그대로 보여주세요.
- 사용자에게 경고하지 않고 노드가 5,000개가 넘는 그래프에서 HTML 시각화를 실행하지 마세요.
