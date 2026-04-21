import os
import subprocess
import urllib.parse
from pathlib import Path
import logging
from arti_ops.config import get_config, get_project_id

logger = logging.getLogger(__name__)

class GithubPolicySync:
    """GitHub 저장소의 정책 문서를 글로벌 디렉토리로 동기화(GitOps)하는 엔진"""
    def __init__(self):
        self.repo = get_config("github_policy_repo")
        self.token = get_config("github_token")
        self.target_dir = Path.home() / ".arti-ops" / "policies"
        self.workspace_name = get_project_id() or Path.cwd().name
        self.is_empty_repo = False
        
    def _mask_url(self, url: str) -> str:
        """토큰을 ***TOKEN***으로 마스킹하여 반환"""
        if not self.token:
            return url
        return url.replace(self.token, "***TOKEN***")

    def _get_auth_url(self) -> str:
        if not self.repo:
            return ""
        if not self.token:
            return self.repo
            
        try:
            parsed = urllib.parse.urlparse(self.repo)
            if not parsed.scheme:
                parsed = urllib.parse.urlparse(f"https://{self.repo}")
                
            netloc = f"{self.token}@{parsed.netloc}"
            return urllib.parse.urlunparse((parsed.scheme, netloc, parsed.path, parsed.params, parsed.query, parsed.fragment))
        except Exception:
            return self.repo

    def sync(self) -> bool:
        """Git 저장소를 clone 하거나 최신 상태로 강제 갱신합니다."""
        if not self.repo:
            logger.info("[PolicySync] GitHub 저장소 설정이 없어 동기화를 건너뜁니다.")
            return False

        auth_url = self._get_auth_url()
        masked_url = self._mask_url(auth_url)
        
        self.target_dir.mkdir(parents=True, exist_ok=True)
        git_dir = self.target_dir / ".git"

        try:
            if not git_dir.exists():
                logger.info(f"[PolicySync] 원격 정책 저장소 클론 중... ({masked_url})")
                cmd = ["git", "clone", auth_url, "."]
                subprocess.run(cmd, cwd=str(self.target_dir), check=True, capture_output=True, text=True)
            else:
                logger.info(f"[PolicySync] 원격 정책 저장소 동기화 중...")
                subprocess.run(["git", "fetch", "--all"], cwd=str(self.target_dir), check=True, capture_output=True, text=True)
                
            # 빈 저장소(Cold Start) 검사
            try:
                subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(self.target_dir), check=True, capture_output=True, text=True)
                self.is_empty_repo = False
            except subprocess.CalledProcessError:
                self.is_empty_repo = True
                logger.info("[PolicySync] 커밋이 없는 빈 저장소(Empty Repo)가 감지되었습니다. G1 정책 초기화(Cold Start)를 대기합니다.")
                # 빈 저장소이므로 branch checkout을 시도하지 않고 즉시 성공 반환
                return True
                
            # Branch Switching Logic
            if self.workspace_name:
                try:
                    subprocess.run(["git", "checkout", self.workspace_name], cwd=str(self.target_dir), check=True, capture_output=True, text=True)
                    subprocess.run(["git", "reset", "--hard", f"origin/{self.workspace_name}"], cwd=str(self.target_dir), check=True, capture_output=True, text=True)
                    logger.info(f"[PolicySync] {self.workspace_name}(G2) 브랜치로 전환 및 동기화 성공.")
                except subprocess.CalledProcessError:
                    logger.info(f"[PolicySync] {self.workspace_name} 브랜치가 없어 기본 main(G1) 브랜치로 Fallback 합니다.")
                    subprocess.run(["git", "checkout", "main"], cwd=str(self.target_dir), check=True, capture_output=True, text=True)
                    subprocess.run(["git", "reset", "--hard", "origin/main"], cwd=str(self.target_dir), check=True, capture_output=True, text=True)
            else:
                subprocess.run(["git", "checkout", "main"], cwd=str(self.target_dir), check=True, capture_output=True, text=True)
                subprocess.run(["git", "reset", "--hard", "origin/main"], cwd=str(self.target_dir), check=True, capture_output=True, text=True)
            
            logger.info("[PolicySync] 전체 정책 동기화가 완료되었습니다.")
            return True
            
        except subprocess.CalledProcessError as e:
            err_msg = self._mask_url(e.stderr or e.stdout or str(e))
            logger.error(f"[PolicySync] 동기화 실패: {err_msg}")
            return False
        except Exception as e:
            err_msg = self._mask_url(str(e))
            logger.error(f"[PolicySync] 동기화 중 예외 발생: {err_msg}")
            return False
