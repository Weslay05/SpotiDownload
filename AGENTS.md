# Information for AI Agents

Dear AI (Maybe even Human), here's some information, because im lazy and my code is a mess.

## Introduction

This is a Program that doesn't really download from Spotify but roughly:

1. Downloads metadata from musicbrainz
2. searches for song on youtube
3. downloads and merges metadata and youtube download
Pretty primitive

Outputs are:

- `assets/song_downloader.log` for logs
- `output/song.[flac, opus]` i think for songs

Tools used are specified in `requirements.txt` or more detailed in `flake.nix`.
Right now `.env` is pretty useless, but could get useful later.

## Instructions

`AGENTS.md` is information about the project that isn't found as easily or just useful things for AI/Agents.
`CHANGES.md` should contain everything uncommitted/changed/added/removed and so on.
`TODO.md` is pretty useful for future TODO's but also for current ones

To make it easier, write temporary files in the folder `.ai` (maybe non existing, if so just create it), for example like `.ai/current_todos.md` or in general `.ai/TODO.md` because no human will ever want to look into `.ai`.
These Files are useful for when the context length is not enough or do strengthen Attention across the whole project to focus on these main things, include everything that is important for your current work, delete the files ONLY EVER AFTER asking the User or to don't disrupt the flow just create another folder in there or add things depending on what's best.

### The .ai folder (Your Personal Workspace)

Create/use `.ai` folder - this is ignored by `.gitignore`. Use it for:

- Your own notes and planning during a session
- Information about what you don't want to forget or your goals
- Tracking changes, TODOs, decisions made in context

Example files: `.ai/TODO.md`, `.ai/CHANGES.md`, `.ai/GOAL.md`, `.ai/INFO.md` (any .log/.txt also fine)

**Workflow:** Set up `.ai` first to establish context. After making any changes, report what you changed and why in `CHANGES.md`.
