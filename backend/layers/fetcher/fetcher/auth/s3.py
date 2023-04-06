from .base import Auth


class S3Auth(Auth):
    _TYPE = 's3'

    def __init__(self, bucket: str, prefix: str) -> None:
        self.bucket = bucket
        self.prefix = prefix

    def authorize(self, params: dict) -> bool:
        return True

    def validate(self) -> bool:
        return super().validate() and self.bucket and self.prefix
    