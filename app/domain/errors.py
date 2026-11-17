from uuid import UUID


class CityNotFound(Exception):
    def __init__(self, city: str | None = None, country: str | None = None) -> None:
        self.city = city
        self.country = country
        super().__init__()


class ProviderNotConfigured(Exception):
    pass


class ProviderAuthError(Exception):
    pass


class ProviderRateLimited(Exception):
    pass


class ProviderTimeout(Exception):
    pass


class ProviderInvalidResponse(Exception):
    pass


class ProviderUnavailable(Exception):
    pass


class ReadingNotFound(Exception):
    def __init__(self, reading_id: UUID) -> None:
        self.reading_id = reading_id
        super().__init__()


class DatabaseUnavailable(Exception):
    pass
