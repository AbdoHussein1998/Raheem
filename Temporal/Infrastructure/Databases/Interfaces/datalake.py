"""Legacy interface documentation only; concrete implementations use composition.

Kept for external-import compatibility, but not inherited by infrastructure classes.
"""

from collections.abc import AsyncIterator
from typing import BinaryIO


class DataLakeController:

    # ==========================================
    # Initialization
    # ==========================================

    @classmethod
    async def init_class(cls, *args, **kwargs) -> "DataLakeController":
        """
        Initialize the storage controller and
        establish required resources.
        """
        ...

    # ==========================================
    # Bucket Operations
    # ==========================================

    async def create_bucket(
        self,
        bucket_name: str,
    ) -> None:
        """Create a new bucket."""
        ...

    async def delete_bucket(
        self,
        bucket_name: str,
    ) -> None:
        """Delete an empty bucket."""
        ...

    async def bucket_exists(
        self,
        bucket_name: str,
    ) -> bool:
        """Check whether a bucket exists."""
        ...

    async def list_buckets(self) -> list[str]:
        """List accessible buckets."""
        ...

    # ==========================================
    # Object Operations
    # ==========================================

    async def upload_file(
        self,
        bucket_name: str,
        object_name: str,
        file_path: str,
    ) -> None:
        """Upload a local file to object storage."""
        ...

    async def download_file(
        self,
        bucket_name: str,
        object_name: str,
        destination_path: str,
    ) -> None:
        """Download an object to a local file."""
        ...

    async def put_object(
        self,
        bucket_name: str,
        object_name: str,
        data: BinaryIO,
        length: int,
    ) -> None:
        """Upload binary data or a binary stream."""
        ...

    async def get_object(
        self,
        bucket_name: str,
        object_name: str,
    ) -> bytes:
        """
        Retrieve an object as bytes.

        Intended for relatively small objects.
        """
        ...

    async def delete_object(
        self,
        bucket_name: str,
        object_name: str,
    ) -> None:
        """Delete a single object."""
        ...

    async def object_exists(
        self,
        bucket_name: str,
        object_name: str,
    ) -> bool:
        """Check whether an object exists."""
        ...

    def list_objects(
        self,
        bucket_name: str,
        prefix: str = "",
        recursive: bool = True,
    ) -> AsyncIterator[str]:
        """
        Lazily list object names.

        The returned asynchronous iterator
        supports async for.
        """
        ...

    # ==========================================
    # Object Metadata
    # ==========================================

    async def get_object_metadata(
        self,
        bucket_name: str,
        object_name: str,
    ) -> dict:
        """
        Retrieve object metadata such as
        size, content type, and ETag.
        """
        ...

    # ==========================================
    # Object Management
    # ==========================================

    async def copy_object(
        self,
        source_bucket: str,
        source_object: str,
        destination_bucket: str,
        destination_object: str,
    ) -> None:
        """Copy an object to another location."""
        ...

    async def move_object(
        self,
        source_bucket: str,
        source_object: str,
        destination_bucket: str,
        destination_object: str,
    ) -> None:
        """
        Move an object to another location.

        Depending on the provider, this may
        require copying and then deleting.
        The operation may not be atomic.
        """
        ...

    # ==========================================
    # Bulk Operations
    # ==========================================

    async def delete_objects(
        self,
        bucket_name: str,
        object_names: list[str],
    ) -> None:
        """Delete multiple objects."""
        ...

    # ==========================================
    # Lifecycle
    # ==========================================

    async def close(self) -> None:
        """Release resources owned by the controller."""
        ...
