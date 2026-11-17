from typing import Annotated

from fastapi import APIRouter, Depends

from app.adapters.inbound.http.dependencies import get_weather_repository
from app.adapters.inbound.http.schemas import HealthResponse
from app.adapters.outbound.postgres.repository import PostgresWeatherRepository

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health(
    repository: Annotated[PostgresWeatherRepository, Depends(get_weather_repository)],
) -> HealthResponse:
    repository.check_health()
    return HealthResponse(status="ok", database="ok")
