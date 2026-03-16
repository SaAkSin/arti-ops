import sqlite3
import time
import logging

logger = logging.getLogger(__name__)

_TABLE = "policy_cache"


class PolicyCache:
    """
    l 뷰어 세션 동안 BookStack L1/L2 정책을 SQLite에 캐싱한다.
    뷰어 진입 시 초기화, 종료 시 clear()로 전체 삭제.
    """

    def __init__(self, db_url: str):
        # "sqlite:///path/to/file.db" → 파일 경로 추출
        db_path = db_url.replace("sqlite:///", "")
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._create_table()

    def _create_table(self):
        """캐시 테이블이 없으면 생성한다."""
        self._conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {_TABLE} (
                scope      TEXT NOT NULL,
                project_id TEXT NOT NULL DEFAULT '',
                content    TEXT NOT NULL,
                fetched_at REAL NOT NULL,
                PRIMARY KEY (scope, project_id)
            )
        """)
        self._conn.commit()

    def get(self, scope: str, project_id: str = "") -> str | None:
        """캐시에서 정책 내용을 조회한다. 없으면 None 반환."""
        row = self._conn.execute(
            f"SELECT content FROM {_TABLE} WHERE scope=? AND project_id=?",
            (scope, project_id)
        ).fetchone()
        if row:
            logger.debug(f"[PolicyCache] HIT — scope={scope}, project_id={project_id!r}")
        return row[0] if row else None

    def set(self, scope: str, content: str, project_id: str = ""):
        """정책 내용을 캐시에 저장한다."""
        self._conn.execute(
            f"INSERT OR REPLACE INTO {_TABLE} VALUES (?, ?, ?, ?)",
            (scope, project_id, content, time.time())
        )
        self._conn.commit()
        logger.debug(f"[PolicyCache] SET — scope={scope}, project_id={project_id!r}")

    def clear(self):
        """l 뷰어 종료 시 세션 캐시 전체 삭제."""
        self._conn.execute(f"DELETE FROM {_TABLE}")
        self._conn.commit()
        logger.debug("[PolicyCache] 세션 캐시 전체 삭제 완료")

    def close(self):
        """DB 연결을 닫는다."""
        self._conn.close()
