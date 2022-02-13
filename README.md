# podcast_transcript

a .envrc is required to run locally

something like:
    export DATABASE_URL=postgres://localhost:5431
    export API_KEY=---REDACTED---
    export REDISTOGO_URL=redis://localhost:6379
    export env=development

after initiating the .envrc run `direnv allow`

Before starting it is also required to `brew install ffmpeg`

create python environment `make venv`

install dependencies `make deps-install`

The job queue requires a redis server to be running locally

run `python worker.py`for job queue in a separate terminal locally

run `make server` to dev locally. Any change to a python file will renew the server with changes made.

To run initial table migration visit `http://0.0.0.0:8080/transcripts:create_table` with the server running locally.
