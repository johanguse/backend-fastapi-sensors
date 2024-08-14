import os
from typing import Union

from dotenv import load_dotenv
from fastapi import Query
from fastapi_pagination import Page as BasePage
from fastapi_pagination.customization import CustomizedPage, UseParamsFields
from pydantic import PostgresDsn
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    PROJECT_NAME: str = os.getenv('PROJECT_NAME', 'Sensor Data API')
    API_V1_STR: str = os.getenv('API_V1_STR', '/api/v1')

    DEFAULT_PAGE_SIZE: int = os.getenv('DEFAULT_PAGE_SIZE', '30')

    SECRET_KEY: str = os.getenv('SECRET_KEY')
    ALGORITHM: str = os.getenv('ALGORITHM', 'HS256')
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '30')
    )

    DATABASE_URL: Union[str, PostgresDsn]

    class Config:
        case_sensitive = True
        env_file = '.env'


settings = Settings()

Page = CustomizedPage[
    BasePage,
    UseParamsFields(
        size=Query(settings.DEFAULT_PAGE_SIZE, ge=0),
    ),
]
