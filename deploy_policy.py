import os
import re

# ==========================================
# 1. 정책 데이터 (L1 + L2)
# ==========================================

POLICY_CONTENT = """
## [GLOBAL_RULES]
### develop-guide
1. artifact 생성시 반드시 한국어로 작성한다.
2. 코드의 주석은 반드시 한국어로 작성한다.
3. git commit 메시지는 한국어로 작성한다.
4. git commit 은 특별한 지시가 없는한 사용자가 직접 실행하여야한다.

### update-architecture
(생략 가능하나 원본 유지 권장 - 실제 fetch 된 내용 삽입)
... (생략된 세부내용)

## [WORKSPACE_RULES]
### maintain-architecture
당신은 `arti-ops` 프로젝트의 아키텍처와 디렉토리 구조를 엄격하게 수호하는 관리자입니다.
... (생략된 세부내용)
"""

# (실제로는 fetch_policies의 결과를 그대로 이어붙임)

# Tags for non-destructive update
BEGIN_TAG = "### [ARTI-OPS-POLICY-START]"
END_TAG = "### [ARTI-OPS-POLICY-END]"

def apply_policy(file_path, content):
    print(f"[*] Target: {file_path}")
    
    # 디렉토리 보장
    os.makedirs(os.path.dirname(file_path), exist_ok=True) if os.path.dirname(file_path) else None
    
    current_content = ""
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            current_content = f.read()
    
    new_block = f"{BEGIN_TAG}\\n{content.strip()}\\n{END_TAG}"
    
    # 멱등성 검사 (Idempotency)
    pattern = re.compile(f"{re.escape(BEGIN_TAG)}.*?{re.escape(END_TAG)}", re.DOTALL)
    match = pattern.search(current_content)
    
    if match:
        if match.group(0) == new_block:
            print(f"[SKIP] {file_path}: Policy is already up-to-date.")
            return False
        updated_content = pattern.sub(new_block, current_content)
    else:
        # 신규 삽입 (기본 내용 보존)
        updated_content = (current_content + "\\n\\n" + new_block).strip()
    
    # 백업 생성 (단일 .bak 관리)
    if os.path.exists(file_path):
        with open(file_path + ".bak", "w", encoding="utf-8") as f:
            f.write(current_content)
        print(f"[BACKUP] Created: {file_path}.bak")
    
    # 최종 쓰기
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(updated_content)
    
    print(f"[SUCCESS] Updated: {file_path}")
    return True

if __name__ == "__main__":
    # Fetch된 실제 내용을 여기에 변수로 주입 (시뮬레이션)
    # 실제 실행 시에는 fetch_policies를 통해 가져온 string을 사용함.
    
    full_policy = \"\"\"
# [ARTI-OPS] INTEGRATED POLICY (L1 + L2)

## Global Rules
- artifact 생성시 반드시 한국어로 작성한다.
- 코드의 주석은 반드시 한국어로 작성한다.

## Workspace Rules (arti-ops)
- `src/arti_ops/` 구조를 엄격히 준수한다.
- `uv`를 통해 의존성을 관리한다.
\"\"\"
    
    changed = False
    changed |= apply_policy(".cursorrules", full_policy)
    changed |= apply_policy(".agents/policy.md", full_policy)
    
    if changed:
        print("RESULT: DEPLOYED")
    else:
        print("RESULT: NO_CHANGE")
