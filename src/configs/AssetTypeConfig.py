from enum import Enum


class AssetTypeConfig(Enum):
    TEXT: str = ".txt"
    PDF: str = ".pdf"
    CSV: str = ".csv"
    DOCX: str = ".docx"
