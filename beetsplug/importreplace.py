from __future__ import annotations

import re
from functools import reduce, singledispatchmethod
from re import Pattern
from typing import TYPE_CHECKING, Any, List

from beets.plugins import BeetsPlugin

if TYPE_CHECKING:
    import beets
    from beets.autotag import AlbumInfo, TrackInfo

Replacement = tuple[Pattern, str]


class ImportReplace(BeetsPlugin):
    def __init__(self) -> None:
        super().__init__()
        self._item_replacements: dict[str, list[Replacement]] = {}
        self._album_replacements: dict[str, list[Replacement]] = {}
        self._read_config()
        self.register_listener("trackinfo_received", self._trackinfo_received)
        self.register_listener("albuminfo_received", self._albuminfo_received)

    def _read_config(self) -> None:
        replacements = self.config["replacements"]
        for replacement in replacements:
            if patterns := self._extract_patterns(replacement):
                if "item_fields" in replacement:
                    self._extract_item_fields(
                        patterns, replacement["item_fields"].as_str_seq()
                    )
                if "album_fields" in replacement:
                    self._extract_album_fields(
                        patterns, replacement["album_fields"].as_str_seq()
                    )

    @staticmethod
    def _extract_patterns(
        replacement: beets.IncludeLazyConfig,
    ) -> list[Replacement]:
        return [
            (re.compile(pattern), repl)
            for pattern, repl in replacement["replace"].get(dict).items()
        ]

    def _extract_item_fields(
        self, patterns: list[Replacement], fields: list[str]
    ) -> None:
        for field in fields:
            if field in self._item_replacements:
                self._item_replacements[field].extend(patterns)
            else:
                self._item_replacements[field] = patterns

    def _extract_album_fields(
        self, patterns: list[Replacement], fields: list[str]
    ) -> None:
        for field in fields:
            if field in self._album_replacements:
                self._album_replacements[field].extend(patterns)
            else:
                self._album_replacements[field] = patterns

    def _trackinfo_received(self, info: TrackInfo) -> None:
        for field, replacements in self._item_replacements.items():
            if field in info and (value := getattr(info, field)):
                replaced = self._replace_field(value, replacements)
                setattr(info, field, replaced)

    def _albuminfo_received(self, info: AlbumInfo) -> None:
        for field, replacements in self._album_replacements.items():
            if field in info and (value := getattr(info, field)):
                replaced = self._replace_field(value, replacements)
                setattr(info, field, replaced)
        for track in info.tracks:
            self._trackinfo_received(track)

    def _replace_field(self, text: str, replacements: list[Replacement]) -> str:
        return reduce(self._replace, replacements, text)

    @singledispatchmethod
    @classmethod
    def _replace(cls, value: Any, replacement: Replacement) -> Any:
        raise NotImplementedError

    @_replace.register(str)
    @classmethod
    def _replace_str(cls, value: str, replacement: Replacement) -> str:
        return replacement[0].sub(repl=replacement[1], string=value)

    @_replace.register(list)
    @classmethod
    def _replace_list(cls, value: list[str], replacement: Replacement) -> list[str]:
        return [cls._replace(item, replacement) for item in value]
