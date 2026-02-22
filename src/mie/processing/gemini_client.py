"""Thin wrapper around the Google Gemini API.

This module isolates *every* external Gemini call behind simple functions,
making it the single seam where tests inject mocks.
"""

from __future__ import annotations

import time

from google import genai
from google.genai import types


def get_client(api_key: str) -> genai.Client:
    """Create and return a Gemini API client."""
    return genai.Client(api_key=api_key)


def upload_file(client: genai.Client, path: str) -> types.File:
    """Upload a local file to Gemini and return the resulting File object.

    Raises:
        RuntimeError: If the upload response is missing the file name.
    """
    uploaded: types.File = client.files.upload(file=path)
    if not uploaded.name:
        raise RuntimeError("Upload failed: file name is missing from the response.")
    return uploaded


def wait_for_processing(
    client: genai.Client,
    file: types.File,
    poll_interval: float = 2.0,
) -> types.File:
    """Poll until the uploaded file finishes server-side processing.

    Args:
        client: An authenticated Gemini client.
        file: The file object returned by :func:`upload_file`.
        poll_interval: Seconds between polling requests.

    Returns:
        The updated :class:`types.File` once processing is complete.
    """
    while file.state is not None and file.state == types.FileState.PROCESSING:
        print("Waiting for audio file processing...")
        time.sleep(poll_interval)
        if file.name:
            file = client.files.get(name=file.name)
    return file


def generate_summary(
    client: genai.Client,
    model: str,
    audio_file: types.File,
    user_prompt: str,
    system_prompt: str,
) -> str:
    """Send a prompt + audio file to Gemini and return the generated text.

    Args:
        client: An authenticated Gemini client.
        model: Model identifier (e.g. ``gemini-2.5-flash``).
        audio_file: A processed Gemini File object containing audio.
        user_prompt: The user-facing prompt to accompany the audio.
        system_prompt: System instruction for the model.

    Returns:
        The model's generated text response.
    """
    response = client.models.generate_content(
        model=model,
        contents=[audio_file, user_prompt],
        config=types.GenerateContentConfig(system_instruction=system_prompt),
    )
    return response.text or ""
