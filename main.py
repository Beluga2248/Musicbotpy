import discord
from discord.ext import commands
import yt_dlp
import asyncio
import os # Import the os module
from dotenv import load_dotenv # Import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
# Get the token from the environment variable
TOKEN = os.getenv('DISCORD_TOKEN')
# Choose your bot's prefix (e.g., !play, ?play)
PREFIX = '!'
# --- End Configuration ---

# Ensure TOKEN is loaded
if TOKEN is None:
    print("Error: DISCORD_TOKEN not found in .env file. Please create a .env file and add DISCORD_TOKEN=YOUR_BOT_TOKEN_HERE")
    exit()

intents = discord.Intents.default()
intents.message_content = True  # Required for the bot to read message content
intents.voice_states = True     # Required for voice channel interactions

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# Suppress noise about console usage from errors
yt_dlp.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn' # no video
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=True):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    print('------')

@bot.command(name='join', help='Tells the bot to join the voice channel')
async def join(ctx):
    if not ctx.message.author.voice:
        await ctx.send(f"<a:Wrong:1017416697168269372>{ctx.message.author.name} is not connected to a voice channel.")
        return
    
    channel = ctx.message.author.voice.channel
    await channel.connect()
    await ctx.send(f"Joined {channel.name}!")

@bot.command(name='play', help='To play song')
async def play(ctx, url):
    if not ctx.voice_client:
        await ctx.send("<a:Wrong:1017416697168269372>I'm not in a voice channel. Use `!join` first.")
        return

    async with ctx.typing():
        try:
            player = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
            ctx.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)
            await ctx.send(f'<a:Playing_Audio:1011614261560221726>Now playing: {player.title}')
        except Exception as e:
            await ctx.send(f"<a:Wrong:1017416697168269372>Error playing song: {e}")
            print(f"Error playing song: {e}")

@bot.command(name='leave', help='To make the bot leave the voice channel')
async def leave(ctx):
    if ctx.voice_client:
        await ctx.send("<a:Yes:1011614293420150805>Leaving voice channel.")
        await ctx.voice_client.disconnect()
    else:
        await ctx.send("<a:Wrong:1017416697168269372>I'm not in a voice channel.")

@bot.command(name='stop', help='Stops the current song and clears the queue')
async def stop(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("Stopped playing.")
    elif ctx.voice_client:
        await ctx.send("<a:Wrong:1017416697168269372>No song is currently playing.")
    else:
        await ctx.send("<a:Wrong:1017416697168269372>I'm not in a voice channel.")

bot.run(TOKEN)
