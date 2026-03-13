#!/bin/bash

# ==============================================================================
# Generate llms.txt for AI Context
# ==============================================================================
# 프로젝트 내 Git에 커밋된 소스 코드 파일(텍스트 데이터)만 모아서 
# AI 시스템이 이해할 수 있는 단일 컨텍스트 파일(docs/llms.txt)로 병합합니다.
# 민감한 환경 설정 파일 및 로그, AI 부속물, 패키지 락 파일 등은 철저히 제외됩니다.
# ==============================================================================

# 작업 디렉토리가 항상 루트가 되도록 보장
cd "$(dirname "$0")" || exit 1

OUTPUT_FILE="docs/llms.txt"
TMP_FILE="docs/llms_tmp.txt"

# docs 폴더가 없으면 생성
mkdir -p docs

# 출력 파일이 있으면 초기화(비우기)
> "$OUTPUT_FILE"

echo "================================================================================" >> "$OUTPUT_FILE"
echo " Project Context Aggregation for LLM" >> "$OUTPUT_FILE"
echo " Generated on: $(date)" >> "$OUTPUT_FILE"
echo "================================================================================" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# 정규식 패턴을 사용하여 제외(Exclude)할 파일 지정
# 1. ^docs/ : 문서 관련 폴더 제외 (llms.txt 생성 시 순수 코드 위주)
# 2. ^\.agents/|^\\.cursor/|^GEMINI\.md$|llms.*\.txt$ : AI 프롬프트 지시자 및 스크립트, 기존 텍스트 산출물
# 3. ^\.env(\..+)?$ : 환경 변수 데이터 유출 방지 (모든 .env 관련)
# 4. .*\.lock : 거대한 패키지 락킹 파일 제외 (uv.lock, package-lock.json 등)
# 5. \.(png|jpg|jpeg|gif|svg|ico|ttf|woff|woff2|eot|pdf|mp4|webm|zip|tar|gz|db|sqlite3)$ : 텍스트 이외의 정적 파일/DB 자산 제외
EXCLUDE_PATTERN="^docs/|^\.agents/|^\.cursor/|^GEMINI\.md$|llms.*\.txt$|^\.env(\..+)?$|.*\.lock$|\.(png|jpeg|jpg|gif|svg|ico|ttf|woff|woff2|eot|pdf|mp4|webm|zip|tar|gz|db|sqlite|sqlite3)$"

echo "[Info] Gathering Git tracked files..."

# git ls-files를 통해 변경내역에 있는 소스만을 가져옴 (빌드 폴더 node_modules 등 제외됨)
# egrep -v -E 로 블랙리스트 필터를 거침
git ls-files | grep -vE "$EXCLUDE_PATTERN" > "$TMP_FILE"

FILE_COUNT=$(wc -l < "$TMP_FILE" | tr -d ' ')
echo "[Info] Total $FILE_COUNT files will be combined into $OUTPUT_FILE"

# 각 파일을 순회하며 내용을 추출
while IFS= read -r file; do
    # 파일이 실제로 존재하고 일반 파일인지 확인
    if [ -f "$file" ]; then
        # 파일 내용을 llms.txt 끝에 병합. 각 파일마다 경계 마커(Delimiter)를 삽입.
        echo "================================================================================" >> "$OUTPUT_FILE"
        echo "File: $file" >> "$OUTPUT_FILE"
        echo "================================================================================" >> "$OUTPUT_FILE"
        cat "$file" >> "$OUTPUT_FILE"
        # 줄바꿈 충돌 방지를 위한 엔터 삽입
        echo "" >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
    else
        echo "[Warn] File not found or not a regular file: $file"
    fi
done < "$TMP_FILE"

# 임시 파일 삭제
rm -f "$TMP_FILE"

echo "[Success] llms.txt generated at $OUTPUT_FILE"