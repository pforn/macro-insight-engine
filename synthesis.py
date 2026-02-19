import glob
import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types

from prompts import SYSTEM_PROMPT

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Using the most modern stable flash model from your list
MODEL_ID = "gemini-2.5-flash"


def test_connection():
    """
    Tests the connection to the Google Gemini API.

    Sends a simple text prompt to the model to verify authentication
    and model availability.
    """
    try:
        response = client.models.generate_content(
            model=MODEL_ID, contents="Say 'System online with Gemini 2.5 Flash'"
        )
        print(f"✅ {response.text}")
    except Exception as e:
        print(f"❌ Connection Failed: {e}")


def summarize_latest_audio(directory="downloads"):
    """
    Orchestrates the audio summarization pipeline.

    1. Identifies the most recently created MP3 file in the specified directory.
    2. Renames the file temporarily to ensure ASCII compatibility for upload.
    3. Uploads the file to Gemini and waits for processing to complete.
    4. Generates a content summary using the defined SYSTEM_PROMPT.
    5. Cleans up by restoring the original filename.

    Args:
        directory (str): Path to the directory containing audio files. Defaults to "downloads".
    """
    # Find the most recently created MP3 file
    files = glob.glob(os.path.join(directory, "*.mp3"))
    if not files:
        print("No MP3 files found to process.")
        return

    latest_file = max(files, key=os.path.getctime)
    print(f"Processing: {latest_file}")

    # Rename to safe filename to avoid encoding issues with special characters
    file_ext = os.path.splitext(latest_file)[1]
    safe_path = os.path.join(directory, f"temp_processing{file_ext}")
    os.rename(latest_file, safe_path)

    try:
        print("Uploading to Gemini...")
        audio_file: types.File = client.files.upload(file=safe_path)

        if not audio_file.name:
            raise RuntimeError("Upload failed: file name is missing from the response.")

        safe_file_name = audio_file.name

        while (
            audio_file.state is not None
            and audio_file.state == types.FileState.PROCESSING
        ):
            print("Waiting for audio file processing...")
            time.sleep(2)
            audio_file = client.files.get(name=safe_file_name)

        print("Generating summary...")
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=[
                audio_file,
                f"Please provide a comprehensive summary of this audio recording. Original title: {os.path.basename(latest_file)}",
            ],
            config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
        )
        print(f"\n✅ Summary:\n{response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        # Restore original filename
        if os.path.exists(safe_path):
            os.rename(safe_path, latest_file)


if __name__ == "__main__":
    summarize_latest_audio()
