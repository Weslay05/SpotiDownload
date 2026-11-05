import musicbrainzngs
import logging

musicbrainzngs.set_useragent("SongDownloader", "2.0", "contact@example.com")

class Metadata:
    """Class for Metadata"""
    def __init__(self, logger: object) -> None:
        self.logger = logger

    def get_metadata_musicbrainz(self, title: str, artist: str):
        """Searches and gets Metadata of a song"""
        logging = self.logger

            # : Search for the Song Metadata
        if artist == "Unknown Artist":
            logging.info("No Artist defined, searching using title only")
            common: dict[str, str] = {}
        else:
            common: dict[str, str] = { "artist": artist }
        result = musicbrainzngs.search_recordings(**common, recording=title, limit=1)
        if not result['recording-list']:
            return None
        track = result['recording-list'][0] # TODO: Improve search

            # : Add Genres and Tags
        GENRES = [
            g["name"]
            for g in track.get("genre-list", [])
            if "name" in g
        ]
        if not GENRES:
            GENRES = [
                t["name"]
                for t in track.get("tag-list", [])
                if "name" in t
            ]

        metadata = {
            "title": track.get("title"),
            "artist": track.get("artist-credit", [{}])[0].get("artist", {}).get("name"),
            "duration_ms": int(track.get("length", 0)),  # Duration in milliseconds
            "release_id": track.get("release-list", [{}])[0].get("id"),
            "album": track.get("release-list", [{}])[0].get("title"),
            "date": track.get("release-list", [{}])[0].get("date"),
            "genres": GENRES
        }

            # : Fetch cover art URL if a release ID exists
        if metadata["release_id"]:
            metadata["cover_url"] = f"https://coverartarchive.org/release/{metadata['release_id']}/front"
            metadata["cover_url_fallback"] = f"https://coverartarchive.org/release-group/{metadata['release_id']}/front"
        else:
            metadata["cover_url"] = 'https://None'
            logging.critical(
                "No Song Cover found using '%s' return: '%s'",
                metadata['release_id'], metadata["cover_url"]
            )
        return metadata