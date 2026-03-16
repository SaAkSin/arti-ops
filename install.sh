#!/usr/bin/env bash
# arti-ops installer script
# Usage: curl -sL https://raw.githubusercontent.com/SaAkSin/arti-ops/main/install.sh | bash

set -e

echo "================================================================="
echo " ▶ arti-ops (ARTGRAMMER Internal Prototype) 설치 마법사"
echo " ⚠ 주의: 본 도구는 Google DeepMind의 'antigravity' 에이전트 전용입니다."
echo "================================================================="
echo ""

# 1. uv 설치 여부 확인 및 설치
    if ! command -v uv &> /dev/null; then
        echo "➜ 파이썬 패키지 매니저 'uv'가 설치되어 있지 않습니다. 설치를 진행합니다..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        
        # 공식 설치 스크립트로 설치 시 경로를 현 세션에 임시로 강제 반영
        export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
        
        if ! command -v uv &> /dev/null; then
            echo "✖ 'uv' 설치에 실패했거나 환경 변수(PATH)에 추가되지 않았습니다."
            echo "다음 명령을 수동으로 실행하여 환경 변수를 적용한 뒤 다시 시도해주세요:"
            echo "source \$HOME/.cargo/env"
            exit 1
        fi
        echo "✔ 'uv' 패키지 매니저 설치 완료!"
    else
        echo "✔ 'uv' 패키지 매니저가 이미 설치되어 있습니다. ($(which uv))"
    fi

# 2. arti-ops 전역 설치 (최신 main 브랜치 기준으로 설치 및 업데이트)
# 시스템(homebrew 등)에 사전 설치된 경우를 대비하여 PATH 덮어쓰기를 생략하거나 가장 뒤로 미룸.
export PATH="$PATH:$HOME/.local/bin:$HOME/.cargo/bin"
echo "➜ 'arti-ops' CLI 도구를 시스템 전역에 설치(또는 업데이트)합니다..."
uv tool install --force "git+https://github.com/SaAkSin/arti-ops.git@main"

# PATH 환경 변수 영구 등록 (uv 내부 기능 호출)
uv tool update-shell > /dev/null 2>&1 || true

# 3. 설치 가이드 및 다음 단계 안내
echo ""
echo "★ 'arti-ops' 설치가 모두 완료되었습니다!"
echo ""
echo "다음 단계:"
echo " 1. 터미널을 재시작하거나 새 탭을 여세요."
echo " 2. 아무 디렉토리에서나 'arti-ops init' 명령어를 실행하여"
echo "    초기 환경(워크스페이스 및 글로벌 인증)을 설정하세요."
echo ""
echo "사용 예시:"
echo " $ arti-ops init"
echo " $ arti-ops       # 대화형 프롬프트 진입"
echo ""
