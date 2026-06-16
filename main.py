import glob
import json
import logging
import os
import random
import time
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps
import requests
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import textwrap
import wget
from youtube_search import YoutubeSearch
from moviepy.editor import ImageClip, VideoFileClip, AudioFileClip, CompositeAudioClip
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from instagrapi import Client
from instagrapi.types import StoryLink

# Set up clean logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Constants
REDIRECT_URI = "https://example.com/"
AUTHORIZE_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"

# Try to get LANCZOS resampling attribute
try:
    LANCZOS = Image.Resampling.LANCZOS
except AttributeError:
    LANCZOS = Image.LANCZOS

def change_image_size(max_width, max_height, img):
    """Resizes PIL image keeping the aspect ratio."""
    width_ratio = max_width / img.size[0]
    height_ratio = max_height / img.size[1]
    new_width = int(width_ratio * img.size[0])
    new_height = int(height_ratio * img.size[1])
    return img.resize((new_width, new_height), LANCZOS)

def generate_thumbnail(title, artist, duration, release, download_path, save_path):
    """Generates the 'Now Playing' thumbnail image."""
    logger.info("Generating thumbnail image...")
    with Image.open(download_path) as youtube_img:
        # Resize background
        bg_img = change_image_size(1080, 1920, youtube_img).convert("RGBA")
        
        # Apply blur and dimming to background
        background = bg_img.filter(ImageFilter.BoxBlur(30))
        enhancer = ImageEnhance.Brightness(background)
        background = enhancer.enhance(0.6)
        
        # Create logo/album cover overlay
        logo = youtube_img.copy()
        logo.thumbnail((800, 800), LANCZOS)
        logo = ImageOps.expand(logo, border=15, fill="white")
        logo = change_image_size(800, 800, logo)
        
        # Paste cover overlay
        background.paste(logo, (140, 560), logo.convert("RGBA") if logo.mode == "RGBA" else None)
        
        # Draw text overlays
        draw = ImageDraw.Draw(background)
        
        # Load fonts with fallback
        def get_font(name, size):
            try:
                return ImageFont.truetype(name, size)
            except IOError:
                return ImageFont.load_default()
        
        name_font = get_font("font.ttf", 90)
        title_font = get_font("font2.ttf", 60)
        header_font = get_font("font2.ttf", 70)
        meta_font = get_font("font2.ttf", 60)
        
        # User name header
        display_name = os.environ.get("NAME", "User")
        draw.text((5, 5), f"{display_name}'s Spotify", fill=(30, 215, 96), font=name_font)
        
        # "NOW PLAYING"
        draw.text((140, 290), "NOW PLAYING", fill="white", stroke_width=4, stroke_fill="white", font=header_font)
        
        # Wrapped Title
        lines = textwrap.wrap(title, width=32)
        y_offset = 380
        for line in lines[:2]:  # Draw up to 2 lines of title
            draw.text(
                (140, y_offset),
                line,
                fill="white",
                stroke_width=4,
                stroke_fill=(216, 0, 39),
                font=title_font,
            )
            y_offset += 70
            
        # Metadata: Artist, Duration, Release Date
        draw.text((140, 1510), f"By {artist}", fill="white", stroke_width=4, stroke_fill=(255, 191, 0), font=meta_font)
        draw.text((140, 1560), f"Duration: {duration}", fill="white", stroke_width=3, stroke_fill=(255, 191, 0), font=meta_font)
        draw.text((140, 1610), f"Released on: {release}", fill="white", stroke_width=4, stroke_fill=(255, 191, 0), font=meta_font)
        
        # Save output
        if os.path.exists(save_path):
            os.remove(save_path)
        background.save(save_path)

def get_currently_playing_song(refresh_token, client_id, client_secret):
    """Fetches currently playing song info from Spotify API."""
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'redirect_uri': REDIRECT_URI,
        'client_id': client_id,
        'client_secret': client_secret
    }
    try:
        resp = requests.post(TOKEN_URL, data=data, timeout=15)
        resp.raise_for_status()
        token_data = resp.json()
        access_token = token_data.get('access_token')
        if not access_token:
            logger.error("Failed to parse access_token from Spotify token response.")
            return None
        
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }
        r = requests.get('https://api.spotify.com/v1/me/player/currently-playing', headers=headers, timeout=15)
        return r
    except Exception as e:
        logger.error(f"Error in Spotify API connection: {e}")
        return None

def clean_temp_files():
    """Removes leftover media files in cwd."""
    for ext in ["*.jpg", "*.png", "*.mp3", "*.mp4"]:
        for f in glob.glob(ext):
            try:
                os.remove(f)
            except Exception:
                pass

def generate_video_clip(img_path, output_mp4, duration=30):
    """Creates a static video clip from the image."""
    logger.info("Rendering video clip from image...")
    clip = ImageClip(img_path).set_duration(duration)
    clip.write_videofile(output_mp4, fps=1, codec="libx264")
    clip.close()

def search_and_download_youtube(track_name, artist_name, save_mp3):
    """Searches YouTube for the track and downloads the audio."""
    query = f"{track_name} {artist_name}"
    logger.info(f"Searching YouTube for: {query}")
    try:
        results = YoutubeSearch(query, max_results=1).to_json()
        yt_data = json.loads(results)
        if not yt_data.get('videos'):
            logger.warning("No YouTube videos found.")
            return False
        
        suf = yt_data['videos'][0]['url_suffix']
        link = 'https://youtube.com' + suf
        
        try:
            import yt_dlp as youtube_dl
        except ImportError:
            import youtube_dl
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': save_mp3,
            'restrictfilenames': True,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'quiet': True,
            'no_warnings': True,
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([link])
        return True
    except Exception as e:
        logger.error(f"YouTube search or download failed: {e}")
        return False

def combine_video_audio(video_mp4, audio_mp3, final_mp4, duration=30):
    """Combines video and audio, then clips it to duration."""
    logger.info("Combining audio and video...")
    try:
        videoclip = VideoFileClip(video_mp4)
        audioclip = AudioFileClip(audio_mp3)
        
        composite_audio = CompositeAudioClip([audioclip])
        videoclip.audio = composite_audio
        
        temp_merged = "temp_merged.mp4"
        videoclip.write_videofile(temp_merged, codec="libx264", audio_codec="aac")
        
        videoclip.close()
        audioclip.close()
        
        # Trim to 30 seconds
        ffmpeg_extract_subclip(temp_merged, 0, duration, targetname=final_mp4)
        
        if os.path.exists(temp_merged):
            os.remove(temp_merged)
        return True
    except Exception as e:
        logger.error(f"Failed to combine video and audio: {e}")
        return False

def upload_to_instagram_story(video_path, track_url):
    """Logs into Instagram and uploads story."""
    ig_user = os.environ.get("IG_USERNAME")
    ig_pass = os.environ.get("IG_PASSWORD")
    if not ig_user or not ig_pass:
        logger.error("Instagram username or password environment variables missing.")
        return
        
    logger.info("Uploading video to Instagram story...")
    cl = Client()
    try:
        cl.login(ig_user, ig_pass)
        cl.video_upload_to_story(Path(video_path), links=[StoryLink(webUri=track_url)])
        logger.info("Story successfully updated on Instagram.")
    except Exception as e:
        logger.error(f"Instagram story upload failed: {e}")
    finally:
        try:
            cl.logout()
        except Exception:
            pass

def run_cycle():
    """Runs a single polling cycle of the bot."""
    clean_temp_files()
    
    refresh_token = os.environ.get("SPOTIFY_TOKEN")
    client_id = os.environ.get("CLIENT_ID")
    client_secret = os.environ.get("CLIENT_SECRET")
    
    if not refresh_token or not client_id or not client_secret:
        logger.error("Spotify configurations missing in environment variables.")
        return
        
    resp = get_currently_playing_song(refresh_token, client_id, client_secret)
    if resp is None:
        return
        
    if resp.status_code == 204 or not resp.text.strip():
        logger.info("No song is currently playing on Spotify.")
        return
        
    try:
        track_info = resp.json()
    except Exception as e:
        logger.error(f"Failed to parse Spotify response JSON: {e}")
        return
        
    if not track_info or 'item' not in track_info or track_info['item'] is None:
        logger.info("Currently playing endpoint returned empty item.")
        return

    # Parse details
    title = track_info['item']['name']
    artists_list = track_info['item']['artists']
    artists_str = " and ".join([a['name'] for a in artists_list])
    release = track_info['item']['album']['release_date']
    track_url = track_info['item']['external_urls']['spotify']
    img_url = track_info['item']['album']['images'][0]['url']
    
    logger.info(f"Currently playing: {title} by {artists_str}")

    # Generate unique ID for this run's temp files
    run_id = str(random.randint(1000, 9999))
    img_temp = f"downloaded_{run_id}.png"
    img_output = f"thumbnail_{run_id}.png"
    video_temp = f"temp_video_{run_id}.mp4"
    audio_temp = f"temp_audio_{run_id}.mp3"
    final_video = "video.mp4"

    try:
        # Search duration on YouTube
        search_res = YoutubeSearch(title, max_results=1).to_json()
        yt_search_data = json.loads(search_res)
        duration = yt_search_data['videos'][0]['duration'] if yt_search_data.get('videos') else "0:00"
    except Exception:
        duration = "3:00"

    try:
        # Download album art
        logger.info(f"Downloading album art from {img_url}...")
        wget.download(img_url, out=img_temp)
        print() # Add newline after wget progress bar
        
        # Generate card
        generate_thumbnail(
            title=title,
            artist=artists_str,
            duration=duration,
            release=release,
            download_path=img_temp,
            save_path=img_output
        )
        
        # Download audio from YouTube
        if not search_and_download_youtube(title, artists_str, audio_temp):
            return
            
        # Generate Video
        generate_video_clip(img_output, video_temp)
        
        # Merge Video and Audio
        if not combine_video_audio(video_temp, audio_temp, final_video):
            return
            
        # Upload
        upload_to_instagram_story(final_video, track_url)
        
    except Exception as e:
        logger.error(f"Error during cycle processing: {e}")
    finally:
        # Cleanup
        for f in [img_temp, img_output, video_temp, audio_temp, final_video]:
            try:
                if os.path.exists(f):
                    os.remove(f)
            except Exception:
                pass

def main():
    logger.info("Starting Spotify to Instagram Stories bot...")
    while True:
        try:
            run_cycle()
        except Exception as e:
            logger.error(f"Unhandled error in main loop: {e}")
        
        # Poll every 2 minutes
        logger.info("Waiting 2 minutes before checking again...")
        time.sleep(120)

if __name__ == "__main__":
    main()
