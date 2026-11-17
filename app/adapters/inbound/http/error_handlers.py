from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.domain.errors import (
    CityNotFound,
    DatabaseUnavailable,
    ProviderAuthError,
    ProviderInvalidResponse,
    ProviderNotConfigured,
    ProviderRateLimited,
    ProviderTimeout,
    ProviderUnavailable,
    ReadingNotFound,
)


def _error_response(code: str, status: int, details: dict[str, Any] | None = None) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={"error": code, "details": details or {}},
    )


def _validation_reason(error: dict[str, Any], field: str) -> str:
    error_type = error.get("type")
    if error_type == "missing":
        return "required"
    if error_type == "string_too_short" and field == "city":
        return "blank"
    if error_type == "string_too_long":
        return "too_long"
    if error_type == "string_pattern_mismatch":
        return "invalid_format"
    if error_type in {"int_parsing", "int_type", "string_type"}:
        return "invalid_format"
    if field == "page" and error_type == "greater_than_equal":
        return "must_be_positive"
    if field == "page_size" and error_type in {
        "greater_than_equal",
        "less_than_equal",
    }:
        return "out_of_range"
    if field == "id" and error_type == "uuid_parsing":
        return "invalid_uuid"
    return "invalid_format"


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, error: RequestValidationError
    ) -> JSONResponse:
        fields = []
        for item in error.errors():
            location = item.get("loc", ())
            field = str(location[-1]) if location else "request"
            fields.append({"name": field, "reason": _validation_reason(item, field)})
        return _error_response(
            "validation_error",
            HTTPStatus.UNPROCESSABLE_ENTITY,
            {"fields": fields},
        )

    @app.exception_handler(CityNotFound)
    async def city_not_found_handler(request: Request, error: CityNotFound) -> JSONResponse:
        return _error_response(
            "city_not_found",
            HTTPStatus.NOT_FOUND,
            {"city": error.city, "country": error.country},
        )

    @app.exception_handler(ProviderNotConfigured)
    async def provider_not_configured_handler(
        request: Request, error: ProviderNotConfigured
    ) -> JSONResponse:
        return _error_response("provider_not_configured", HTTPStatus.SERVICE_UNAVAILABLE)

    @app.exception_handler(ProviderAuthError)
    async def provider_auth_error_handler(
        request: Request, error: ProviderAuthError
    ) -> JSONResponse:
        return _error_response("provider_auth_error", HTTPStatus.SERVICE_UNAVAILABLE)

    @app.exception_handler(ProviderRateLimited)
    async def provider_rate_limited_handler(
        request: Request, error: ProviderRateLimited
    ) -> JSONResponse:
        return _error_response("provider_rate_limited", HTTPStatus.TOO_MANY_REQUESTS)

    @app.exception_handler(ProviderTimeout)
    async def provider_timeout_handler(request: Request, error: ProviderTimeout) -> JSONResponse:
        return _error_response("provider_timeout", HTTPStatus.GATEWAY_TIMEOUT)

    @app.exception_handler(ProviderInvalidResponse)
    async def provider_invalid_response_handler(
        request: Request, error: ProviderInvalidResponse
    ) -> JSONResponse:
        return _error_response("provider_invalid_response", HTTPStatus.BAD_GATEWAY)

    @app.exception_handler(ProviderUnavailable)
    async def provider_unavailable_handler(
        request: Request, error: ProviderUnavailable
    ) -> JSONResponse:
        return _error_response("provider_unavailable", HTTPStatus.BAD_GATEWAY)

    @app.exception_handler(ReadingNotFound)
    async def reading_not_found_handler(request: Request, error: ReadingNotFound) -> JSONResponse:
        return _error_response(
            "reading_not_found",
            HTTPStatus.NOT_FOUND,
            {"id": str(error.reading_id)},
        )

    @app.exception_handler(DatabaseUnavailable)
    async def database_unavailable_handler(
        request: Request, error: DatabaseUnavailable
    ) -> JSONResponse:
        return _error_response("database_unavailable", HTTPStatus.SERVICE_UNAVAILABLE)
