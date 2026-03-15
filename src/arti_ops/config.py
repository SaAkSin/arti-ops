import os
import shutil
import subprocess
import configparser
from pathlib import Path
import toml
import logging

logger = logging.getLogger(__name__)

class Configurator:
    """arti-ops 계층적 설정 모듈
    Global Auth: ~/.arti-ops/credentials (INI)
    Local Config: <cwd>/.artiops.toml (TOML)
    """
    _instance = None
    
    def __init__(self):
        self.global_config = {}
        self.local_config = {}
        self.project_id = None
        self.db_path = None
        
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
            cls._instance.load()
        return cls._instance

    def load(self):
        # 1. Load Global Auth
        home_dir = Path.home()
        arti_ops_dir = home_dir / ".arti-ops"
        arti_ops_dir.mkdir(parents=True, exist_ok=True)
        
        credentials_file = arti_ops_dir / "credentials"
        if credentials_file.exists():
            parser = configparser.ConfigParser()
            parser.read(credentials_file)
            if 'default' in parser:
                self.global_config = dict(parser['default'])
                
        # 2. Setup Global DB Path
        self.db_path = f"sqlite:///{arti_ops_dir}/arti_ops_session.db"

        # 3. Load Local Project Config
        local_file = Path.cwd() / ".artiops.toml"
        if local_file.exists():
            try:
                self.local_config = toml.load(local_file)
                self.project_id = self.local_config.get("current_project_id")
            except Exception as e:
                logger.error(f"Failed to parse .artiops.toml: {e}")
                
        # 4. Fallback Project ID
        if not self.project_id:
            self.project_id = Path.cwd().name

        # 5. GWS Validation if enabled
        if str(self.get("USE_GWS_CLI", "false")).lower() == "true":
            self._validate_gws()
            
        # 6. Inject SDK required env variables
        api_key = self.get("GEMINI_API_KEY")
        if api_key:
            os.environ["GEMINI_API_KEY"] = api_key
            
    def _validate_gws(self):
        if not shutil.which("gws"):
            logger.warning("[WARNING] USE_GWS_CLI is enabled, but 'gws' binary is not found in PATH.")
            return
            
        try:
            res = subprocess.run(["gws", "--version"], capture_output=True, text=True, check=False)
            if res.returncode != 0:
                logger.warning("[WARNING] 'gws' CLI returned non-zero exit code. Validation failed.")
        except Exception as e:
            logger.warning(f"[WARNING] Failed to execute 'gws' CLI: {e}")

    def get(self, key: str, default=None):
        # 1. Local first
        if key in self.local_config:
            return self.local_config[key]
        # 2. Global second (configparser uses lowercase keys by default)
        return self.global_config.get(key.lower(), default)
        
    def get_db_url(self):
        return self.db_path

def get_config(key: str, default=None):
    return Configurator.get_instance().get(key, default)

def get_db_url():
    return Configurator.get_instance().get_db_url()

def get_project_id():
    return Configurator.get_instance().project_id
