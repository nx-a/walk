class ShelterError(Exception):
    status_code = 400

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(ShelterError):
    status_code = 404


class ConflictError(ShelterError):
    status_code = 409


class ValidationError(ShelterError):
    status_code = 422
