from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    data_dir: str = "./data"
    timezone: str = "Asia/Jakarta"
    dev_mode: bool = False
    app_version: str = "0.1.0"
    default_supplier_mode: str = "single"
    default_price_mode: str = "include_ppn"

    model_config = {"env_file": ".env"}


settings = Settings()
