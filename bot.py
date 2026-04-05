import discord
from discord.ext import tasks
import requests
import os

DISCORD_TOKEN = os.environ['DISCORD_TOKEN']
CHANNEL_ID = int(os.environ['CHANNEL_ID'])
YOUTUBE_API_KEY = os.environ['YOUTUBE_API_KEY']
YOUTUBE_CHANNEL_ID = os.environ['YOUTUBE_CHANNEL_ID']

intents = discord.Intents.default()
client = discord.Client(intents=intents)

already_notified = False

def get_live_info():
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "channelId": YOUTUBE_CHANNEL_ID,
        "type": "video",
        "eventType": "live",
        "key": YOUTUBE_API_KEY
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        items = data.get("items", [])
        print(f"Live check: {len(items)} stream(s) found")
        if items:
            item = items[0]
            video_id = item["id"]["videoId"]
            title = item["snippet"]["title"]
            thumbnail = item["snippet"]["thumbnails"]["high"]["url"]
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            return {"title": title, "thumbnail": thumbnail, "url": video_url}
    except Exception as e:
        print(f"Error checking live status: {e}")
    return None

@tasks.loop(seconds=60)
async def check_live():
    global already_notified
    channel = client.get_channel(CHANNEL_ID)
    if not channel:
        print("Channel not found!")
        return
    try:
        info = get_live_info()
        print(f"Is live: {info is not None} | Already notified: {already_notified}")
        if info and not already_notified:
            embed = discord.Embed(
                title=info["title"],
                url=info["url"],
                description="🔴 We're live on YouTube! Come watch!",
                color=0xFF0000
            )
            embed.set_image(url=info["thumbnail"])
            embed.set_footer(text="Click the title to watch!")
            await channel.send(content="@everyone", embed=embed)
            already_notified = True
            print("Notification sent!")
        elif not info:
            if already_notified:
                print("Stream ended, cooling down...")
                import asyncio
                await asyncio.sleep(300)
            already_notified = False
    except Exception as e:
        print(f"Error in check_live: {e}")

@check_live.before_loop
async def before_check_live():
    await client.wait_until_ready()
    global already_notified
    print("Bot ready, starting live check loop...")
    info = get_live_info()
    if info:
        already_notified = True
        print("Already live on startup, skipping first notification.")

@client.event
async def on_ready():
    print(f"Bot is online as {client.user}")
    if not check_live.is_running():
        check_live.start()

@client.event
async def on_resumed():
    print("Bot resumed connection successfully!")
    if not check_live.is_running():
        check_live.start()
        print("Restarted check_live loop after resume!")

@client.event
async def on_disconnect():
    print("Bot disconnected - will auto reconnect...")

client.run(DISCORD_TOKEN, reconnect=True)
