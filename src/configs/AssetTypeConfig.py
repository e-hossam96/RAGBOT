from enum import Enum


class AssetTypeConfig(Enum):
    TEXT: str = ".txt"
    PDF: str = ".pdf"
    CSV: str = ".csv"
    DOC: str = ".doc"
    DOCX: str = ".docx"
