# 🐳 Docker 샌드박스 환경 세팅 가이드 (`SandboxTool`)

`arti-ops` v2.0의 진단 및 반영 파이프라인 중 **최종 배포 집행관(`DeploymentExecutor`)** 에이전트는 작성된 파이썬 스크립트나 쉘 스크립트를 로컬 호스트(작업자의 PC 혹은 서버)에 바로 일괄 적용하기 전에, 격리된 가상 환경(Sandbox) 내에서 1차로 Dry-Run(시범 운용)을 진행합니다.

이를 위해 `arti-ops`는 Google ADK의 `ContainerCodeExecutor` 모듈을 통한 Docker 컨테이너 연동 로직(`src/arti_ops/tools/sandbox.py`)을 내장하고 있습니다. 하지만 파이프라인 구동 환경에 해당 의존성이 만족되지 않을 경우, 샌드박스 검증 절차가 스킵(또는 오류가 발생)될 수 있으므로 아래 절차에 따라 필수 구성 요소를 시스템에 구축해야 합니다.

---

## 1. 운영체제 레벨 Docker 엔진 설치 (Rocky Linux 9 기준)

ADK의 컨테이너 실행기는 내부적으로 호스트 시스템의 Docker 데몬(`dockerd`)과 소켓 통신을 하여 격리된 작업 컨테이너를 스핀업(Spin-Up) 시킵니다. 따라서 서버에 Docker 엔진 설치가 선행되어야 합니다.

### 1-1. 기존 캐시 및 구버전 삭제 (선택)
```bash
sudo dnf remove docker docker-client docker-client-latest docker-common docker-latest docker-latest-logrotate docker-logrotate docker-engine
```

### 1-2. Docker CE 레포지토리 추가 및 패키지 설치
Rocky Linux 9의 기본 레포지토리에는 원활한 최신 Docker-CE 패키지가 없을 수 있으므로 공식 저장소를 등록합니다.

```bash
sudo dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

### 1-3. 서비스 구동 및 권한 설정
Docker 데몬을 시작하고, 터미널 세션을 맺은 현재 시스템 사용자(예: `artgrammer`)가 `sudo` 권한 없이도 Docker 제어 소켓에 접근할 수 있도록 권한 그룹을 부여합니다. (이 과정이 없으면 파이썬 스크립트에서 컨테이너를 띄우지 못합니다.)

```bash
# Docker 서비스 자동 시작 등록 및 시작
sudo systemctl enable --now docker

# 현재 OS 사용자를 docker 그룹에 포함 (명령어 실행 후 로그아웃 후 다시 로그인 필요)
sudo usermod -aG docker $USER
```

---

## 2. Python 가상 환경 내 ADK 확장 의존성 보강

현재 `arti-ops` 프로젝트는 기본 `google-adk` 경량 코어 모듈 위에 구축되어 있습니다.
그러나 `SandboxTool`이 의존하고 있는 `ContainerCodeExecutor` 모듈은 내부적으로 `docker` 파이썬 패키지를 호출합니다. 따라서 `uv` 혹은 `pip`를 사용해 추가 확장 패키지를 주입해야 합니다.

### 2-1. 필수 ADK 확장(Extensions) 라이브러리 설치

로컬 프로젝트 레포지토리 경로(`/home/artgrammer/SaAkSin/arti-ops`)로 이동하여 아래 명령어를 통해 의존성을 업데이트합니다.

```bash
# uv 패키지 매니저를 사용하는 경우
uv add "google-adk[extensions]"

# 혹은, 범용 docker SDK 패키지를 단일로 설치할 수도 있습니다.
# uv add docker
```

위 명령어를 실행하면 `.venv/` 가상 환경에 `google.adk.code_executors` 모듈군과 `docker` 파이프라인 모듈이 정상적으로 활성화됩니다. 이후 파이프라인(`arti-ops sync`)이 가동될 때 `import docker` 에러 없이 에이전트가 샌드박스로 코드를 테스트할 수 있게 됩니다.

---

## 3. SandboxTool 테스트 검증

모든 데몬 및 패키지 설정이 완료된 후, 로컬에서 통합 파이프라인 라이브 테스트를 가동하여 Docker 컨테이너 생성과 삭제 루프가 정상 동작하는지 테스트합니다.

```bash
uv run pytest -v -s tests/test_sandbox_live.py
```

만약 `SKIPPED (docker 모듈 부족...)` 이라는 메시지가 출력되지 않고 `PASSED`로 통과한다면, `arti-ops`의 백그라운드 샌드박싱 시스템이 완벽하게 가동 중인 것입니다! 🎉
