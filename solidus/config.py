import json
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # default value is dev
    # for UAT and PROD the value will be provided via environment variable at the time
    #  of application service start.
    '''
    envi:str = 'dev'
    config:str = From Azure secrets
    '''
    envi: str = "dev"  # environment
    config: str = "config.json"


settings = Settings()

# To check if the config is available from the environment variable
assert settings.config, 'config_environment_variable_missing'

config = json.loads(settings.config)
