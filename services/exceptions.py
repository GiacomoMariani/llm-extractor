class AppServiceError(Exception):
    pass


class NotFoundError(AppServiceError):
    pass