import unittest

import beets
from beets.autotag.hooks import AlbumInfo, TrackInfo

from beetsplug.importreplace import ImportReplace


class ImportReplaceTest(unittest.TestCase):
    def setUp(self):
        beets.config["importreplace"] = {"replacements": []}

    def tearDown(self):
        beets.config["importreplace"] = {"replacements": []}

    def _create_track_info(
        self,
        title: str = None,
        artist: str = None,
        artist_sort: str = None,
        artist_credit: str = None,
    ):
        return TrackInfo(
            title=title,
            artist=artist,
            artist_sort=artist_sort,
            artist_credit=artist_credit,
        )

    def _create_album_info(
        self,
        tracks: [TrackInfo] = None,
        album: str = None,
        artist: str = None,
        artist_sort: str = None,
        artist_credit: str = None,
    ):
        return AlbumInfo(
            tracks=tracks or [],
            album=album,
            artist=artist,
            artist_sort=artist_sort,
            artist_credit=artist_credit,
        )

    def _add_replacement(
        self,
        item_fields: [str] = None,
        album_fields: [str] = None,
        replace: {str: str} = None,
    ) -> None:
        replacement = {}
        if item_fields:
            replacement["item_fields"] = item_fields
        if album_fields:
            replacement["album_fields"] = album_fields
        if replace:
            replacement["replace"] = replace

        beets.config["importreplace"]["replacements"].get(list).append(replacement)

    def test_replaces_only_config_fields(self):
        """Check if plugin replaces text in only the specified fields."""
        self._add_replacement(
            item_fields=["title"], album_fields=["album"], replace={"The": "A"}
        )
        tracks = [self._create_track_info(title="The Piece", artist="The Dude")]
        album_info = self._create_album_info(
            tracks=tracks, album="The Album", artist="The Dude"
        )
        subject = ImportReplace()
        subject._albuminfo_received(album_info)
        assert album_info.album == "A Album"
        assert album_info.artist == "The Dude"
        assert album_info.tracks[0].title == "A Piece"
        assert album_info.tracks[0].artist == "The Dude"

    def test_replaces_only_config_fields_multiple(self):
        """Check if plugin replaces text in only the specified fields when
        multiple replacements given.
        """
        self._add_replacement(
            item_fields=["title"], album_fields=["album"], replace={"The": "A"}
        )
        self._add_replacement(
            item_fields=["artist"], album_fields=["artist"], replace={"This": "That"}
        )
        tracks = [self._create_track_info(title="The Piece", artist="The This")]
        album_info = self._create_album_info(
            tracks=tracks, album="The Album", artist="The This"
        )
        subject = ImportReplace()
        subject._albuminfo_received(album_info)
        assert album_info.album == "A Album"
        assert album_info.artist == "The That"
        assert album_info.tracks[0].title == "A Piece"
        assert album_info.tracks[0].artist == "The That"

    def test_handles_empty_fields(self):
        """Verify that plugin works when field marked for replacement
        is absent.
        """
        self._add_replacement(
            item_fields=["title", "artist"],
            album_fields=["album", "artist"],
            replace={"This": "That"},
        )
        tracks = [self._create_track_info(title="This Piece", artist=None)]
        album_info = self._create_album_info(
            tracks=tracks, album="This Album", artist=None
        )
        subject = ImportReplace()
        subject._albuminfo_received(album_info)
        assert album_info.album == "That Album"
        assert album_info.artist is None
        assert album_info.tracks[0].title == "That Piece"
        assert album_info.tracks[0].artist is None

    def test_replaces_in_order(self):
        """Verify that the plugin replaces fields in the order given in the
        config.
        """
        self._add_replacement(
            item_fields=["title"], album_fields=["album"], replace={"The": "This"}
        )
        self._add_replacement(
            item_fields=["title"], album_fields=["album"], replace={"This": "That"}
        )
        tracks = [self._create_track_info(title="The Piece", artist="The Dude")]
        album_info = self._create_album_info(
            tracks=tracks, album="The Album", artist="The Dude"
        )
        subject = ImportReplace()
        subject._albuminfo_received(album_info)
        assert album_info.album == "That Album"
        assert album_info.artist == "The Dude"
        assert album_info.tracks[0].title == "That Piece"
        assert album_info.tracks[0].artist == "The Dude"

    def test_incorrect_field(self):
        """Verify the plugin works when a non-existent field is specified."""
        self._add_replacement(
            item_fields=["asdf"], album_fields=["asdf"], replace={"This": "That"}
        )
        tracks = [self._create_track_info(title="The Piece", artist="The Dude")]
        album_info = self._create_album_info(
            tracks=tracks, album="The Album", artist="The Dude"
        )
        subject = ImportReplace()
        subject._albuminfo_received(album_info)
        assert album_info.album == "The Album"
        assert album_info.artist == "The Dude"
        assert album_info.tracks[0].title == "The Piece"
        assert album_info.tracks[0].artist == "The Dude"

    def test_no_fields(self):
        """Verify the plugin works when item_fields or album_fields not
        given.
        """
        self._add_replacement(item_fields=["title"], replace={"The": "A"})
        self._add_replacement(album_fields=["artist"], replace={"This": "That"})
        tracks = [self._create_track_info(title="The Piece", artist="The This")]
        album_info = self._create_album_info(
            tracks=tracks, album="The Album", artist="The This"
        )
        subject = ImportReplace()
        subject._albuminfo_received(album_info)
        assert album_info.album == "The Album"
        assert album_info.artist == "The That"
        assert album_info.tracks[0].title == "A Piece"
        assert album_info.tracks[0].artist == "The This"
