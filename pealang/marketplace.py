"""PeaLang Extension Marketplace (v2.38.0).

Provides a curated marketplace interface for discovering, rating, and reviewing
PeaLang libraries. Integrates with the registry server to provide:

* Library discovery with search and filtering
* Rating and review system
* Trending and featured libraries
* Author profiles and provenance tracking
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import time


@dataclass
class LibraryRating:
    """A rating for a library."""

    library_name: str
    version: str
    rating: int  # 1-5 stars
    reviewer: str
    comment: str
    timestamp: int


@dataclass
class MarketplaceEntry:
    """A marketplace listing for a library."""

    name: str
    version: str
    description: str
    author: str
    downloads: int
    rating: float  # 0.0-5.0
    rating_count: int
    tags: List[str]
    homepage: Optional[str] = None
    repository: Optional[str] = None
    license: Optional[str] = None
    created_at: int = 0
    updated_at: int = 0


class ExtensionMarketplace:
    """Marketplace for discovering and rating PeaLang libraries.

    Integrates with the registry server to provide discovery, ratings,
    and reviews for published libraries.
    """

    def __init__(self, storage_dir: str = "./marketplace-storage") -> None:
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.libraries: Dict[str, MarketplaceEntry] = {}
        self.ratings: Dict[str, List[LibraryRating]] = {}  # key: "name@version"
        self._load()

    def _load(self) -> None:
        """Load marketplace data from disk."""
        libraries_file = self.storage_dir / "libraries.json"
        ratings_file = self.storage_dir / "ratings.json"

        if libraries_file.exists():
            try:
                data = json.loads(libraries_file.read_text())
                for entry in data:
                    self.libraries[entry["name"]] = MarketplaceEntry(**entry)
            except Exception:
                pass

        if ratings_file.exists():
            try:
                data = json.loads(ratings_file.read_text())
                for key, ratings_data in data.items():
                    self.ratings[key] = [LibraryRating(**r) for r in ratings_data]
            except Exception:
                pass

    def _save(self) -> None:
        """Save marketplace data to disk."""
        libraries_file = self.storage_dir / "libraries.json"
        ratings_file = self.storage_dir / "ratings.json"

        libraries_file.write_text(
            json.dumps([e.__dict__ for e in self.libraries.values()], indent=2)
        )

        ratings_data = {
            key: [r.__dict__ for r in ratings]
            for key, ratings in self.ratings.items()
        }
        ratings_file.write_text(json.dumps(ratings_data, indent=2))

    def register_library(
        self,
        name: str,
        version: str,
        description: str,
        author: str,
        tags: List[str],
        homepage: Optional[str] = None,
        repository: Optional[str] = None,
        license: Optional[str] = None,
    ) -> MarketplaceEntry:
        """Register a library in the marketplace."""
        entry = MarketplaceEntry(
            name=name,
            version=version,
            description=description,
            author=author,
            downloads=0,
            rating=0.0,
            rating_count=0,
            tags=tags,
            homepage=homepage,
            repository=repository,
            license=license,
            created_at=int(time.time()),
            updated_at=int(time.time()),
        )
        self.libraries[name] = entry
        self._save()
        return entry

    def get_library(self, name: str) -> Optional[MarketplaceEntry]:
        """Get a library entry by name."""
        return self.libraries.get(name)

    def list_libraries(
        self,
        tag: Optional[str] = None,
        author: Optional[str] = None,
        sort_by: str = "downloads",
    ) -> List[MarketplaceEntry]:
        """List libraries with optional filtering and sorting."""
        entries = list(self.libraries.values())

        if tag:
            entries = [e for e in entries if tag in e.tags]

        if author:
            entries = [e for e in entries if e.author == author]

        if sort_by == "downloads":
            entries.sort(key=lambda e: e.downloads, reverse=True)
        elif sort_by == "rating":
            entries.sort(key=lambda e: e.rating, reverse=True)
        elif sort_by == "name":
            entries.sort(key=lambda e: e.name)

        return entries

    def search_libraries(self, query: str) -> List[MarketplaceEntry]:
        """Search libraries by name or description."""
        query_lower = query.lower()
        results = []
        for entry in self.libraries.values():
            if query_lower in entry.name.lower() or query_lower in entry.description.lower():
                results.append(entry)
        return results

    def rate_library(
        self,
        name: str,
        version: str,
        rating: int,
        reviewer: str,
        comment: str = "",
    ) -> LibraryRating:
        """Rate a library (1-5 stars)."""
        if rating < 1 or rating > 5:
            raise ValueError("Rating must be between 1 and 5")

        key = f"{name}@{version}"
        rating_obj = LibraryRating(
            library_name=name,
            version=version,
            rating=rating,
            reviewer=reviewer,
            comment=comment,
            timestamp=int(time.time()),
        )

        if key not in self.ratings:
            self.ratings[key] = []
        self.ratings[key].append(rating_obj)
        self._save()

        # Update library rating
        if name in self.libraries:
            lib = self.libraries[name]
            all_ratings = [r.rating for r in self.ratings[key]]
            lib.rating = sum(all_ratings) / len(all_ratings)
            lib.rating_count = len(all_ratings)
            self._save()

        return rating_obj

    def download_library(self, name: str) -> None:
        """Record a download for a library."""
        if name in self.libraries:
            self.libraries[name].downloads += 1
            self.libraries[name].updated_at = int(time.time())
            self._save()

    def get_library_ratings(self, name: str, version: str) -> List[LibraryRating]:
        """Get all ratings for a library version."""
        key = f"{name}@{version}"
        return self.ratings.get(key, [])

    def get_trending(self, limit: int = 10) -> List[MarketplaceEntry]:
        """Get trending libraries (high downloads, recent activity)."""
        entries = list(self.libraries.values())
        # Score = downloads * 0.7 + rating_count * 0.3
        for e in entries:
            e._score = e.downloads * 0.7 + e.rating_count * 0.3
        entries.sort(key=lambda e: getattr(e, "_score", 0), reverse=True)
        return entries[:limit]


def create_marketplace(storage_dir: str = "./marketplace-storage") -> ExtensionMarketplace:
    """Factory function to create an ExtensionMarketplace."""
    return ExtensionMarketplace(storage_dir)
