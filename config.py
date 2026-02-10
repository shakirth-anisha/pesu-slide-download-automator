import os
from pathlib import Path
from dotenv import load_dotenv, set_key


ENV_FILE = ".env"
ENV_EXAMPLE_FILE = ".env.example"

# Load .env file if it exists
if os.path.exists(ENV_FILE):
    load_dotenv(ENV_FILE)


class Config:    
    @staticmethod
    def get_env_file() -> str:
        return ENV_FILE
    
    @staticmethod
    def ensure_env_exists() -> None:
        if not os.path.exists(ENV_FILE):
            with open(ENV_FILE, "w") as f:
                f.write("# PESU Academy Automator Configuration\n")
            print(f"Created new {ENV_FILE} file")
    
    @staticmethod
    def load_env() -> None:
        if os.path.exists(ENV_FILE):
            load_dotenv(ENV_FILE, override=True)
    
    @staticmethod
    def get(key: str, default=None):
        return os.getenv(key, default)
    
    @staticmethod
    def set_env(key: str, value: str) -> None:
        Config.ensure_env_exists()
        set_key(ENV_FILE, key, value)
        os.environ[key] = value
    
    @staticmethod
    def validate_required(keys: list) -> bool:
        for key in keys:
            value = os.getenv(key)
            if not value or value == "NOT_SET":
                return False
        return True
    
    # Credentials
    @staticmethod
    def get_username() -> str:
        return Config.get("USERNAME", "")
    
    @staticmethod
    def get_password() -> str:
        return Config.get("PASSWORD", "")
    
    @staticmethod
    def set_credentials(username: str, password: str) -> None:
        Config.set_env("USERNAME", username)
        Config.set_env("PASSWORD", password)
    
    @staticmethod
    def clear_credentials() -> None:
        Config.set_env("USERNAME", "NOT_SET")
        Config.set_env("PASSWORD", "NOT_SET")
    
    # Settings
    @staticmethod
    def get_dont_ask_again() -> bool:
        return Config.get("DONT_ASK_AGAIN", "0") == "1"
    
    @staticmethod
    def set_dont_ask_again(value: bool) -> None:
        Config.set_env("DONT_ASK_AGAIN", "1" if value else "0")
    
    @staticmethod
    def get_merge_pdfs_preference() -> str:
        return Config.get("MERGE_PDFS")
    
    @staticmethod
    def set_merge_pdfs_preference(preference: str) -> None:
        if preference not in ("1", "0", "-1"):
            raise ValueError("Preference must be '1', '0', or '-1'")
        Config.set_env("MERGE_PDFS", preference)
    
    @staticmethod
    def get_download_dir() -> str:
        download_dir = Config.get("DOWNLOAD_DIR", "").strip()
        if download_dir:
            # Create directory if it doesn't exist
            os.makedirs(download_dir, exist_ok=True)
            return download_dir
        return os.getcwd()
    
    @staticmethod
    def set_download_dir(path: str) -> None:
        if not os.path.isdir(path):
            raise ValueError(f"Directory does not exist: {path}")
        Config.set_env("DOWNLOAD_DIR", path)
    
    @staticmethod
    def is_debug_enabled() -> bool:
        return Config.get("DEBUG", "0") == "1"
    
    @staticmethod
    def set_debug(enabled: bool) -> None:
        Config.set_env("DEBUG", "1" if enabled else "0")
