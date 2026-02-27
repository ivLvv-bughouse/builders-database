from pydantic import BaseSettings, SettingConfigDict

class Settings(BaseSettings):
    model_config = SettingConfigDict(env_file=".env")
    
settings = Settings()