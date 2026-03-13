# 📚 BookStack 연동 가이드 및 준비 사항

arti-ops v0.1.0은 사내 BookStack(위키)를 SSOT(Single Source of Truth)로 삼아 모든 에이전트의 룰셋을 관리합니다. 원활한 동기화(Sync)와 역문서화(Sync-Back)를 위해 BookStack 관리자 및 PM은 다음 사항들을 준비해야 합니다.

## 1. API Token 발급 및 환경설정

시스템이 위키 문서를 읽고 쓸 수 있도록 **API Token 발급**이 필요합니다.

1.  BookStack 관리자 페이지 > **사용자(Users)** 메뉴로 이동합니다.
2.  `arti-ops` 전용 서비스 계정(또는 본인 계정)을 선택한 뒤 **API Tokens** 섹션에서 새 토큰을 생성합니다.
3.  발급된 `Token ID`와 `Token Secret`을 로컬 환경의 `.env` 파일에 기재합니다.
    ```env
    # .env 파일 내 작성 예시
    BOOKSTACK_API_URL="https://wiki.your-company.com/api"
    BOOKSTACK_TOKEN_ID="your_bookstack_token_id"
    BOOKSTACK_TOKEN_SECRET="your_bookstack_token_secret"
    ```

## 2. BookStack 권장 페이지/구조 (Hierarchy)

arti-ops의 에이전트들은 다음 구조(L1, L2)의 문서를 기반으로 융합 배포를 진행합니다.

### 🌐 L1. Global Rule (전사 공통 정책)
*   **Book/Chapter 권장 이름:** `[Antigravity] Global Policy`
*   **목적:** 회사 전체에 강제되는 보안(Security), 네트워크, 공통 아키텍처 규칙.
*   **권한:** **일반 사용자 수정 불가** (인프라/보안 담당자만 Read/Write 가능하도록 권한 설정).
*   **예시 내용:**
    *   `결제 DB 접속 시 반드시 Vault를 경유해야 한다.`
    *   `모든 컨테이너 베이스 이미지는 사내 Harbor 레지스트리만 허용한다.`

### 🏗️ L2. Workspace Rule (프로젝트별 자율 정책)
*   **Book/Chapter 권장 이름:** `[Workspace] {프로젝트 명}` (예: `[Workspace] Project_Alpha`)
*   **목적:** 프로젝트 도메인에 특화된 스택, 프롬프트, 배포 단계 등을 기록. L1 정책의 위배되지 않는 선에서 최대한 자율성을 보장합니다.
*   **권한:** 프로젝트 PM 및 소속 개발자 모두 편집 접근 가능.
*   **예시 내용:**
    *   `우리 프로젝트의 데이터베이스는 PostgreSQL 15 버전을 사용한다.`
    *   `에이전트는 pytest로 최소 80% 커버리지의 유닛테스트를 유지할 것.`

### 📝 Release Notes (역문서화 전용)
*   arti-ops는 최종 병합 검증이 끝나 로컬(Local) 시스템에 적용이 되면, 당시의 **수정 내역(Diff)** 및 반영 상태를 해당 프로젝트 페이지 경로에 업데이트합니다(`publish_sync_report`).
*   따라서 프로젝트 계층 내에 변경 이력을 기록할 수 있는 하위 페이지 공간(`Release Notes` 또는 `Sync History`) 생성을 권장합니다.

## 3. TroubleShooting (HITL 승인 대기 발생)

로컬 `arti-ops sync` 명령 실행 도중, 위키에 작성된 정책 간에 심각한 논리적 모순이 있거나 치명적인 덮어쓰기가 우려될 경우, `CriticalVerifier` 에이전트가 로직을 일시정지(Pause) 합니다.
이때 `.env`에 등록된 `GWS Chat` 웹훅 룸으로 승인 대기 카드가 전송되오니, 내용을 확인하시고 피드백을 주시면 다시 파이프라인이 정상 구동됩니다.
