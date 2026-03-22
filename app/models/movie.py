import ast
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional

@dataclass
class Movie:
    title: str
    original_title: str
    original_language: str
    status: Optional[str] = None
    budget: Optional[int] = None
    revenue: Optional[int] = None
    runtime: Optional[int] = None
    release_date: Optional[datetime] = None
    year: Optional[int] = None
    overview: Optional[str] = None
    homepage: Optional[str] = None
    vote_average: Optional[float] = None
    vote_count: Optional[int] = None
    production_company_id: Optional[int] = None
    genre_id: Optional[int] = None
    primary_language: Optional[str] = None
    languages: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @staticmethod
    def _safe_int(val) -> Optional[int]:
        if val is None or str(val).strip() == "":
            return None
        try:
            return int(float(str(val).strip()))
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _safe_float(val) -> Optional[float]:
        if val is None or str(val).strip() == "":
            return None
        try:
            return float(str(val).strip())
        except (ValueError, TypeError):
            return None

    @classmethod
    def validate_and_transform(cls, data: dict):
        # Title guard
        title = str(data.get("title", "")).strip()
        if not title:
            return None
        
        original_title = str(data.get("original_title", "")).strip()
        if not original_title:
            original_title = title

        # Parsing dates
        raw_date = data.get("release_date")
        clean_date, year = None, None
        if raw_date and str(raw_date).strip():
            try:
                clean_date = datetime.strptime(str(raw_date).strip(), "%m/%d/%Y")
                year = clean_date.year
            except (ValueError, TypeError):
                clean_date, year = None, None

        # Parsing language
        raw_langs = data.get("languages", "[]")
        try:
            parsed_langs = ast.literal_eval(raw_langs) if isinstance(raw_langs, str) else raw_langs
            if not isinstance(parsed_langs, list):
                parsed_langs = []
        except (ValueError, SyntaxError):
            parsed_langs = []
        
        # Clean the languages
        clean_langs = [str(l).strip().lower() for l in parsed_langs if str(l).strip()]
        primary_lang = clean_langs[0] if clean_langs else None

        # Return cls instance
        return cls(
            title=title,
            original_title=original_title,
            original_language=str(data.get("original_language", "en")).strip().lower(),
            status=data.get("status"),
            year=year,
            budget=cls._safe_int(data.get("budget")),
            revenue=cls._safe_int(data.get("revenue")),
            runtime=cls._safe_int(data.get("runtime")),
            release_date=clean_date,
            overview=data.get("overview"),
            homepage=data.get("homepage"),
            vote_average=cls._safe_float(data.get("vote_average")),
            vote_count=cls._safe_int(data.get("vote_count")),
            production_company_id=cls._safe_int(data.get("production_company_id")),
            genre_id=cls._safe_int(data.get("genre_id")),
            primary_language=primary_lang,
            languages=clean_langs
        )

    def to_dict(self) -> dict:
        raw = asdict(self)
        clean_dict = {}
        for key, val in raw.items():
            if val is None:
                continue
            if isinstance(val, datetime):
                clean_dict[key] = val.isoformat()
            else:
                clean_dict[key] = val
        return clean_dict