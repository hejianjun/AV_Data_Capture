# Import all download functions from downloader module
from .downloader import (
    actor_photo_download,
    download_file_with_filename,
    download_one_file,
    extrafanart_download,
    extrafanart_download_one_by_one,
    extrafanart_download_threadpool,
    image_download,
    image_ext,
    parallel_download_files,
    trailer_download,
)

# Define __all__ to control what gets imported when using "from mdc.download import *"
__all__ = [
    "download_file_with_filename",
    "download_one_file",
    "parallel_download_files",
    "trailer_download",
    "actor_photo_download",
    "extrafanart_download",
    "extrafanart_download_one_by_one",
    "extrafanart_download_threadpool",
    "image_ext",
    "image_download",
]
