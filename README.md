# spotiinsta

A Python bot that watches the song you're **currently playing on Spotify**,
generates a stylized "Now Playing" thumbnail and a short video clip, and posts it
to your **Instagram story** automatically — refreshing every couple of minutes.

> ⚠️ Educational / hobby project. Use responsibly and in line with Spotify's and
> Instagram's Terms of Service.

## How it works

1. Polls the Spotify "currently playing" endpoint using a refresh token.
2. Looks the track up on YouTube and downloads the audio.
3. Builds a 1080×1920 "Now Playing" image (album art + title/artist/duration/
   release date) with Pillow, then renders a 30-second video with MoviePy.
4. Logs into Instagram via [instagrapi](https://github.com/subzeroid/instagrapi)
   and uploads the clip as a story linking back to the Spotify track.

`authurl.py` is a small helper to generate the Spotify authorization URL you use
once to obtain your `SPOTIFY_TOKEN` (refresh token).

## Requirements

- Python 3.x
- `ffmpeg` available on your `PATH`
- The packages in [`requirements.txt`](./requirements.txt)

```bash
pip install -r requirements.txt
```

## Configuration

Copy the example env file and fill in your own values:

```bash
cp .env.example .env
# edit .env
```

| Variable | Description |
|----------|-------------|
| `CLIENT_ID` | Spotify app client id |
| `CLIENT_SECRET` | Spotify app client secret |
| `SPOTIFY_TOKEN` | Spotify OAuth refresh token (see `authurl.py`) |
| `IG_USERNAME` | Instagram username |
| `IG_PASSWORD` | Instagram password |
| `NAME` | Display name drawn on the thumbnail (e.g. "Alex's Spotify") |

## Running

```bash
python main.py
```

## License

[MIT](./LICENSE)
