import discord
from discord.ext import commands
import yt_dlp
import os
import asyncio
import shutil

# Tworzenie obiektu bota
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Dodanie uprawnienia do śledzenia członków serwera
bot = commands.Bot(command_prefix=".", intents=intents)

def download_youtube_audio(url, download_folder, filename):
    try:
        # Ustawienia yt-dlp do pobierania tylko audio w formacie WebM (Opus)
        ydl_opts = {
            'outtmpl': os.path.join(download_folder, filename),  # Ścieżka do folderu z nazwą pliku
            'format': 'bestaudio[ext=webm]/best[ext=webm]',  # Pobierz najlepszy plik audio w WebM
            'noplaylist': True,  # Brak pobierania playlisty
            'postprocessors': [],  # Brak postprzetwarzania (brak FFmpeg)
            'extractaudio': True,  # Pobieraj tylko audio
            'audioquality': 1,  # Najlepsza jakość audio
            'prefer_free_formats': True,  # Preferuj darmowe formaty
            'audioext': 'webm',  # Zmień rozszerzenie na webm
            'forceaudio': True,  # Wymuszaj audio, nawet jeśli dostępny jest video
            'geo_bypass': True,  # Obejście geo-blocking, jeśli jest
            'quiet': False  # Umożliwia widoczność postępu pobierania
        }

        # Utworzenie obiektu downloadera
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Pobieranie audio
            ydl.download([url])
        return True

    except Exception as e:
        return False, f"Wystąpił błąd: {e}"

@bot.event
async def on_ready():
    print(f"Bot zalogowany jako {bot.user}")

@bot.command()
async def play(ctx, url: str):
    playlist_folder = r'..\bot\playlist'

    if 'list=' in url:
        for filename in os.listdir(playlist_folder):
            file_path = os.path.join(playlist_folder, filename)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"Nie udało się usunąć pliku/folderu: {file_path}. Błąd: {e}")

        # Ustawienia yt-dlp do pobierania tylko audio z playlisty
        ydl_opts = {
            'outtmpl': os.path.join(playlist_folder, '%(title)s.%(ext)s'),  # Format nazwy na podstawie tytułu piosenki
            'format': 'bestaudio[ext=webm]/best[ext=webm]',  # Tylko audio w WebM
            'extractaudio': True,  # Pobieramy tylko audio
            'audioext': 'webm',  # Format WebM
            'noplaylist': False,  # Pobierz całą playlistę
            'geo_bypass': True,  # Obejście geo-blocking, jeśli jest
            'quiet': False,  # Umożliwia widoczność postępu pobierania
            'prefer_free_formats': True,  # Preferuj darmowe formaty
        }

        # Pobieranie playlisty
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(url, download=True)
            if 'entries' in result:
                await ctx.send(f"Odpalono {len(result['entries'])} piosenek z playlisty.")
                voice_channel = ctx.author.voice.channel
                voice_client = await voice_channel.connect()

                # Odtwarzanie każdego utworu z playlisty
                for entry in result['entries']:
                    song_path = os.path.join(playlist_folder, f"{entry['title']}.webm")
                    source = discord.FFmpegPCMAudio(song_path)
                    voice_client.play(source, after=lambda e: print('done', e))
                    await ctx.send(f"Odtwarzam {entry['title']}")

                    # Czekamy, aż utwór się skończy
                    while voice_client.is_playing():
                        await asyncio.sleep(1)

                # Po zakończeniu playlisty, disconnect
                await voice_client.disconnect()
                await ctx.send("Playlist zakończona!")
            else:
                await ctx.send("Wystąpił problem przy pobieraniu playlisty.")
    else:
        # Obsługa pojedynczego utworu
        audio_file_path = os.path.join(playlist_folder, 'audio.webm')

        # Usuwamy poprzedni plik audio, jeśli istnieje
        if os.path.exists(audio_file_path):
            os.remove(audio_file_path)

        await ctx.send('Rozpoczynam ładowanie audio...')

        # Pobieramy pojedynczy utwór w formacie webm
        success, message = download_youtube_audio(url, playlist_folder, 'audio.webm')

        if not success:
            await ctx.send(message)
            return

        # Sprawdzenie, czy użytkownik jest na kanale głosowym
        if ctx.author.voice:
            voice_channel = ctx.author.voice.channel
            voice_client = await voice_channel.connect()

            source = discord.FFmpegPCMAudio(audio_file_path)
            voice_client.play(source, after=lambda e: print('done', e))

            await ctx.send(f"Dołączono do kanału {voice_channel.name}")

            # Czekamy, aż utwór się skończy
            while voice_client.is_playing():
                await asyncio.sleep(1)

            await voice_client.disconnect()
            os.remove(audio_file_path)  # Usuwamy plik audio po odtworzeniu

        else:
            await ctx.send("Aby włączyć muzykę, musisz być na kanale głosowym. Dołącz do kanału, a następnie użyj tej komendy.")

# Komenda opuszczenia kanału głosowego
@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Bot opuścił kanał głosowy.")
    else:
        await ctx.send("Bot nie jest połączony z żadnym kanałem głosowym.")

# Komenda skip - pominięcie aktualnie odtwarzanego utworu
@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()  # Zatrzymuje odtwarzanie utworu
        await ctx.send("Utwór został pominięty.")
    else:
        await ctx.send("Bot nie odtwarza żadnej muzyki.")


bot.run('MTMxMjUxOTgzMjEzODI4OTI0Mg.GnjMmJ.wlILUpU48aoKLYf7BZNjM829-JdONh_zCCRtCM')