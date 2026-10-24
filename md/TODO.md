# TODOs for the Project

## --- Error handling and Fallback ---

- Use album/genre context in YouTube query (if available)

## --- Readability ---

pass

## --- Features ---

### TODO: Music Fingerprinting

```py
# After download, extract fingerprint
fingerprint = chromaprint(wav_file)
response = musicbrainzngs.get_fingerprints(fingerprint)
if response['fingerprint']['musicbrainz_id'] != METADATA['release_id']:
    logging.error("WRONG SONG! Fingerprint mismatch")
    retry_search()  # Search again with better query
```

idea2

```py
# Step 1: Generate fingerprint from downloaded file
from acoustid import Client  # OR chromaprint standalone library
client = Client('YOUR_AMAZING_ID', 'YOUR_SECRET')
fingerprint = client.fingerprint(wav_file)

# Step 2: Match against MusicBrainz database
matches = musicbrainzngs.get_fingerprints(fingerprint)

# Step 3: Verify it matches our expected recording
expected_id = METADATA['release_id'] or METADATA['recording_mbid']
if not any(m['musicbrainz_id'] == expected_id for m in matches):
    logging.error("WRONG SONG - fingerprint mismatch!")
```

requirements.txt

- acoustid (easier, handles MB API) or
- chromaprint / librosa + standalone chromaprint binary

### TODO: Classes

- Make main.py more readable by splitting it into classes

### TODO: Better Fallback & Loops

- Make Loops more useful and include a fallback variabe for many.
- Fix Loops into either functions that call themself or something entirely different

### TODO: Async downloads

- Update temp files to corresponding music file, split download list before into temp files that don't get removed, and also split logs or if possible a unified one but with Process ID.
