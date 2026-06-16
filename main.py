import requests
import json
import spotipy
import os
from PIL import (Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps)
import textwrap
import wget
from youtube_search import YoutubeSearch
import moviepy
import ffmpeg
import instagrapi
from time import sleep
import glob
import random
from spotipy.oauth2 import SpotifyClientCredentials
from moviepy.editor import *
from instagrapi import Client
from instagrapi.types import StoryMention, StoryMedia, StoryLink
import time
from youtube_search import YoutubeSearch
import json
import youtube_dl


#Environmental Variables
client_id=os.environ.get("CLIENT_ID")
client_secret=os.environ.get("CLIENT_SECRET")
redirect_uri="https://example.com/"
authorize_url = "https://accounts.spotify.com/authorize"
token_url = "https://accounts.spotify.com/api/token"


#Creating Spotify CLient
auth_manager = SpotifyClientCredentials(client_id,client_secret)
sp = spotipy.Spotify(auth_manager=auth_manager)

#Image Change size for Instagram
def changeImageSize(maxWidth, maxHeight, image):
    widthRatio = maxWidth / image.size[0]
    heightRatio = maxHeight / image.size[1]
    newWidth = int(widthRatio * image.size[0])
    newHeight = int(heightRatio * image.size[1])
    newImage = image.resize((newWidth, newHeight))
    return newImage

#Generating thumbnail
def thumbnail(title,artist,time,release,download_location,save_location):
        youtube = Image.open(download_location)
        image1 = changeImageSize(1080, 1920, youtube)
        image2 = image1.convert("RGBA")
        background = image2.filter(filter=ImageFilter.BoxBlur(30))
        enhancer = ImageEnhance.Brightness(background)
        background = enhancer.enhance(0.6)
        Xcenter = youtube.width / 2
        Ycenter = youtube.height /2
        x1 = Xcenter - 700
        y1 = Ycenter - 700
        x2 = Xcenter + 700
        y2 = Ycenter + 700
        logo = youtube#.crop((x1, y1, x2, y2))
        logo.thumbnail((800, 800), Image.ANTIALIAS)
        logo = ImageOps.expand(logo, border=15, fill="white")
        logo=changeImageSize(800,800,logo)
        background.paste(logo, (140,560))
        draw = ImageDraw.Draw(background)
        font = ImageFont.truetype("font2.ttf", 40)
        font3 = ImageFont.truetype("font2.ttf", 60)
        font2 = ImageFont.truetype("font2.ttf", 70)
        arial = ImageFont.truetype("font2.ttf", 60)
        name_font = ImageFont.truetype("font.ttf", 30)
        name_font2 = ImageFont.truetype("font.ttf", 90)
        para = textwrap.wrap(title, width=32)
        j = 0

#Drawing My name        
        draw.text(
            (5, 5),
            os.environ.get("NAME") + "'s Spotify",
            fill=(30, 215, 96),
            font=name_font2
        )
#drawing "NOW Playing"
        draw.text(
            (140, 290),
            "NOW PLAYING",
            fill="white",
            stroke_width=4,
            stroke_fill="white",
            font=font2,
        )
        for line in para:
          if j == 1:
            j += 1
            draw.text(
                (140, 380),
                f"{line}",
                fill="white",
                stroke_width=4,
                stroke_fill=(216,0,39),
                font=font3,
            )
            if j == 0:
              j += 1
              draw.text(
                  (140, 380),
                  f"{line}",
                  fill="white",
                  stroke_width=4,
                  stroke_fill=(216,0,39),
                  font=font3,
              )
#drawing Artist Name
        draw.text(
            (140, 1510),
            f"By {artist}",
            #(255, 255, 255),
            fill="white",
            stroke_width=4,
            stroke_fill=(255, 191, 0),
            font=arial,
        )
#Draw the duration
        draw.text(
            (140, 1560),
            f"Duration: {time}",
            #(255, 255, 255),
            fill="white",
            stroke_width=3,
            stroke_fill=(255, 191, 0),
            font=arial,
        )
#Draw the release date
        draw.text(
            (140, 1610),
            f"Released on: {release}",
            #(255, 255, 255),
            fill="white",
            stroke_width=4,
            stroke_fill=(255, 191, 0),
            font=arial,
        )
        
        try:
          #trying to delete the loacation if already exists
            os.remove(save_location)
        except:
            pass
        background.save(save_location)
        
        

q=""
save=random.randint(999,827428)

def getCurrentyPlayingSong(refreshToken):
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refreshToken,
            'redirect_uri': redirect_uri,
            'client_id': client_id,
            'client_secret': client_secret
        }
        token = requests.post(token_url, data=data).json()
        print(token['access_token'])
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + token['access_token']
        }
        r = requests.get(
            'https://api.spotify.com/v1/me/player/currently-playing', headers=headers)

        return r
    


#Removes all the useless files in current working directory
def clean():
  for i in glob.glob("*.jpg"):
    os.remove(i)
  for i in glob.glob("*.png"):
    os.remove(i)
  for i in glob.glob("*.mp3"):
    os.remove(i)
  for i in glob.glob("*.mp4"):
    os.remove(i)
#generatte Video


#This method takes the spotify picture and composes into a 30 second clip.
def generate():
  for i in range(15):
    clips = [ImageClip(f"{save}.png").set_duration(30)]
  video = concatenate(clips, method='compose')
  video.write_videofile(f'{save}.mp4',fps=1)


#this method searches for the song details on youtube with the name and also downloads the music.
def search(name):
   results = YoutubeSearch(r['item']['name'], max_results=1).to_json()
   yt=json.loads(results)
   suf=(yt['videos'][0]['url_suffix'])
   link='https://youtube.com'+suf
   ydl_opts = {
    'format': 'bestaudio/best',
    'outtmpl': f'{save}.mp3',
    'reactrictfilenames': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': False,
    'no_warnings': False,
   }
   with youtube_dl.YoutubeDL(ydl_opts) as ydl:
     ydl.download([link])


#This method concates the video file and audio file together.
def video():
   videoclip = VideoFileClip(f"{save}.mp4")
   audioclip = AudioFileClip(f"{save}.mp3")
   new_audioclip = CompositeAudioClip([audioclip])
   videoclip.audio = new_audioclip
   videoclip.write_videofile("new_filename.mp4")
   from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
# ffmpeg_extract_subclip("full.mp4", start_seconds, end_seconds, targetname="cut.mp4")
   ffmpeg_extract_subclip("new_filename.mp4", 00, 30, targetname="video.mp4")
   

#Logs into instagram and then posts the picure+song as story
def instagram():
  print(r)
#print(r['item']['preview_url'])
  cl=Client()
#media_pk=cl.media_pk_from_url(r['item']['preview_url'])
  cl.login(os.environ.get("IG_USERNAME"), os.environ.get("IG_PASSWORD"))
#ffmpeg.input(f'1514909.png',pattern_type='glob',framerate=25).output('movie.mp4').run()
  print(url)
  cl.video_upload_to_story(f'video.mp4',
                         links=[StoryLink(webUri=url)],
                         #medias=[StoryMedia(media_pk=media_pk,x=0.5,y=0.5,width=0.6,height=0.8)
                         )
  

#MAIN method
while True:
  #Cleaning first
  clean()
 #try:
  r=getCurrentyPlayingSong(os.environ.get("SPOTIFY_TOKEN"))
  if (r.text) != "None":
    #if some song is playing
    r=json.loads(r.text)
    title=r['item']['name']
    search(title)
    track=sp.track(r['item']['id'])
    track=json.dumps(track)
    t=json.loads(track)
    for i in t['artists']:
      q+=(i['name'])+" and "
    size = len(q)
    q=q[:size - 4]

    img_url=(r['item']['album']['images'][0]['url'])
    release=r['item']['album']['release_date']
#time=str(int(time[0]))+":"+str(int(time[1]))+""
    results = YoutubeSearch(r['item']['name'], max_results=1).to_json()
    yt=json.loads(results)
    time=(yt['videos'][0]['duration'])
    file=wget.download(img_url)
  
    thumbnail(title=title,artist=q,time=time,release=release,download_location=file,save_location=f'{save}.png')
    try:
     os.remove(file)
    except:
        pass
    url=r['item']['external_urls']['spotify']
    generate()
    video()
    instagram()
    print("Updated Story")

 #except Exception as e:
    #print(e)
  sleep(60*2)
  #Lets check after 2 minutes


