import musicbrainzngs

# Initialize the client with a descriptive user-agent string
musicbrainzngs.set_useragent("MyCleanMetadataApp", "1.0", "contact@example.com")

def get_track_metadata(artist, title):
    # Search for the recording
    result = musicbrainzngs.search_recordings(artist=artist, recording=title, limit=1)
    
    if not result['recording-list']:
        return None
        
    track = result['recording-list'][0]
    
    # Process systematic variables
    metadata = {
        "title": track.get("title"),
        "artist": track.get("artist-credit", [{}])[0].get("artist", {}).get("name"),
        "duration_ms": int(track.get("length", 0)),  # Duration in milliseconds
        "release_id": track.get("release-list", [{}])[0].get("id")
    }
    
    # Fetch cover art URL if a release ID exists
    if metadata["release_id"]:
        metadata["cover_image"] = f"https://coverartarchive.org/release/{metadata['release_id']}/front"
    else:
        metadata["cover_image"] = None
        
    return metadata

# Usage
data = get_track_metadata("Ironmouse, Bibi", "Cry for Me (WA WA WA)")
print(data)