import yt_dlp
import os

def download_audio(url: str, output_path: str = "downloads"):
    """Downloads audio from a YouTube URL and saves it as an MP3."""
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': f'{output_path}/%(title)s.%(ext)s',
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

if __name__ == "__main__":
    # Test with one of our macro podcast links
    test_url = "https://www.youtube.com/watch?v=7WrpqjcMCWI"
    download_audio(test_url)
