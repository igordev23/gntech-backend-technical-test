from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query

from app.adapters.inbound.http.dependencies import get_weather_service
from app.adapters.inbound.http.schemas import (
    WeatherListQuery,
    WeatherListResponse,
    WeatherReadingResponse,
    WeatherSyncRequest,
)
from app.application.weather_service import WeatherService

router = APIRouter()


@router.post("/api/v1/weather/sync", response_model=WeatherReadingResponse)
def sync_weather(
    payload: WeatherSyncRequest,
    service: Annotated[WeatherService, Depends(get_weather_service)],
) -> WeatherReadingResponse:
    return WeatherReadingResponse.model_validate(
        service.sync_weather(payload.city, payload.country)
    )


@router.get("/api/v1/weather", response_model=WeatherListResponse)
def list_weather(
    query: Annotated[WeatherListQuery, Query()],
    service: Annotated[WeatherService, Depends(get_weather_service)],
) -> WeatherListResponse:
    readings, total = service.list_readings(query.city, query.country, query.page, query.page_size)
    return WeatherListResponse(
        items=[WeatherReadingResponse.model_validate(reading) for reading in readings],
        total=total,
        page=query.page,
        page_size=query.page_size,
    )


@router.get("/api/v1/weather/{id}", response_model=WeatherReadingResponse)
def get_weather(
    reading_id: Annotated[UUID, Path(alias="id")],
    service: Annotated[WeatherService, Depends(get_weather_service)],
) -> WeatherReadingResponse:
    return WeatherReadingResponse.model_validate(service.get_reading(reading_id))
