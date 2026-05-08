import io
import logging
from pathlib import Path

from minio import Minio
from minio.error import S3Error

from bot.config import settings

logger = logging.getLogger(__name__)


class MinIOClient:
    def __init__(self):
        self.client = Minio(
            f"{settings.minio_host}:{settings.minio_port}",
            access_key=settings.minio_user,
            secret_key=settings.minio_password,
            secure=settings.minio_secure,
        )
        self.bucket = settings.minio_bucket

    def ensure_bucket(self) -> None:
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)
            logger.info("MinIO bucket yaratildi: %s", self.bucket)

    def upload_file(self, file_path: str, object_name: str) -> str:
        self.ensure_bucket()
        self.client.fput_object(self.bucket, object_name, file_path)
        logger.info("Fayl yuklandi: %s", object_name)
        return object_name

    def upload_bytes(
        self, data: bytes, object_name: str, content_type: str = "application/octet-stream"
    ) -> str:
        self.ensure_bucket()
        stream = io.BytesIO(data)
        self.client.put_object(
            self.bucket, object_name, stream, len(data), content_type=content_type
        )
        return object_name

    def download_file(self, object_name: str, file_path: str) -> str:
        self.client.fget_object(self.bucket, object_name, file_path)
        return file_path

    def get_file_bytes(self, object_name: str) -> bytes:
        response = self.client.get_object(self.bucket, object_name)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    def delete_file(self, object_name: str) -> None:
        self.client.remove_object(self.bucket, object_name)
        logger.info("Fayl o'chirildi: %s", object_name)

    def file_exists(self, object_name: str) -> bool:
        try:
            self.client.stat_object(self.bucket, object_name)
            return True
        except S3Error:
            return False

    def list_files(self, prefix: str = "") -> list[str]:
        objects = self.client.list_objects(self.bucket, prefix=prefix, recursive=True)
        return [obj.object_name for obj in objects]


minio_client = MinIOClient()
