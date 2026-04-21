import os
import re
import yaml
from pathlib import Path
from typing import List, Dict, Union

class PolicyDocument:
    """단일 마크다운 정책 문서를 파싱하고 관리하는 데이터 모델"""
    def __init__(self, filepath: Union[str, Path], source_origin: str = "Unknown"):
        self.filepath = Path(filepath)
        self.source_origin = source_origin
        self.metadata: Dict = {}
        self.content: str = ""
        self.category: str = "general"
        self._parse()

    def _parse(self):
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                raw_text = f.read()

            # YAML Frontmatter 추출 정규식
            match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', raw_text, re.DOTALL)
            if match:
                self.metadata = yaml.safe_load(match.group(1)) or {}
                self.content = match.group(2).strip()
            else:
                self.metadata = {}
                self.content = raw_text.strip()

            # 메타데이터에 type이 없다면 디렉토리 구조에서 유추
            parts = self.filepath.parts
            if "rules" in parts:
                self.category = "rule"
            elif "skills" in parts:
                self.category = "skill"
            elif "workflows" in parts:
                self.category = "workflow"
            else:
                self.category = self.metadata.get("type", "general").lower()

        except Exception as e:
            print(f"[Warning] Failed to parse {self.filepath}: {e}")

    def is_match(self, target_version: str, target_purposes: List[str]) -> bool:
        """현재 문서가 요청된 버전과 용도에 부합하는지 검증"""
        if not self.metadata:
            return True  # 메타데이터가 없는 파일은 기본적으로 공통(all) 정책으로 취급

        # 1. 버전 필터링
        doc_versions = self.metadata.get("version", self.metadata.get("versions", ["latest"]))
        if isinstance(doc_versions, str):
            doc_versions = [doc_versions]
        
        # 'all', 'latest'가 명시되어 있거나, 타겟 버전이 포함되어 있으면 통과
        version_match = "all" in doc_versions or "latest" in doc_versions or target_version in doc_versions

        # 2. 용도(Purpose) 필터링
        doc_purposes = self.metadata.get("purpose", self.metadata.get("purposes", ["all"]))
        if isinstance(doc_purposes, str):
            doc_purposes = [doc_purposes]
            
        purpose_match = "all" in doc_purposes or any(p in doc_purposes for p in target_purposes)

        return version_match and purpose_match

class PolicyComposer:
    """조건에 따라 마크다운 정책들을 필터링하고 하나로 조합하는 조합기"""
    def __init__(self, agents_dir: str = ".agents", auto_sync: bool = False):
        self.agents_dir = Path(agents_dir)
        self.global_policies_dir = Path.home() / ".arti-ops" / "policies"
        self.documents: List[PolicyDocument] = []
        
        if auto_sync:
            from arti_ops.tools.github_sync import GithubPolicySync
            sync_engine = GithubPolicySync()
            sync_engine.sync()
            
        self._load_documents()

    def _load_documents(self):
        # 1. 로컬 경로 로드
        if self.agents_dir.exists():
            for md_file in self.agents_dir.rglob("*.md"):
                if any(exclude in md_file.parts for exclude in ["board", "6-done", "raw", ".git"]):
                    continue
                self.documents.append(PolicyDocument(md_file, source_origin="Local"))
                
        # 2. 글로벌 경로 로드 (단일 워크트리)
        if self.global_policies_dir.exists():
            for md_file in self.global_policies_dir.rglob("*.md"):
                if ".git" in md_file.parts:
                    continue
                self.documents.append(PolicyDocument(md_file, source_origin="Global"))

    def compose(self, target_version: str = "latest", target_purposes: List[str] = None) -> str:
        """버전과 용도에 맞게 문서를 병합하여 하나의 컨텍스트(프롬프트)로 반환합니다."""
        if target_purposes is None:
            target_purposes = ["all"]
            
        matched_docs = [doc for doc in self.documents if doc.is_match(target_version, target_purposes)]

        # 카테고리 우선순위 정렬 (규칙 ➔ 워크플로우 ➔ 스킬 순으로 AI에게 인지시킴)
        priority = {"rule": 1, "workflow": 2, "skill": 3, "general": 4}
        matched_docs.sort(key=lambda d: (
            priority.get(d.category, 99),
            str(d.metadata.get("scope", "Z")).upper(), # G1 -> G2 -> L1 순 정렬
            d.filepath.stem
        ))

        # 최종 프롬프트 문자열 조립
        composed = [f"# Aggregated Policy Profile"]
        composed.append(f"> **Target Version**: {target_version} | **Applied Purposes**: {', '.join(target_purposes)}\n")

        if not matched_docs:
            composed.append("적용 가능한 정책 문서가 없습니다.")
            return "\n".join(composed)

        for doc in matched_docs:
            scope = str(doc.metadata.get("scope", "GLOBAL")).upper()
            title = doc.metadata.get("title", doc.filepath.stem)
            category_label = doc.category.upper()
            
            composed.append(f"## [{scope}] {title} ({category_label}) - Origin: {doc.source_origin}")
            composed.append(doc.content)
            composed.append("\n" + "-" * 50 + "\n")

        return "\n".join(composed)
