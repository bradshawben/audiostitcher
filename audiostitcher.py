import os
import re
import subprocess
import tempfile

import streamlit as st
import yt_dlp

st.title("Audio Stitcher")

url = st.text_input("Enter a YouTube URL")

if not url:
    st.stop()

st.video(url)


@st.cache_data(show_spinner="Downloading audio from YouTube...")
def download_audio(video_url):
    tmp_dir = tempfile.mkdtemp(prefix="audiostitcher_")
    ydl_opts = {
        "format": "bestaudio[ext=m4a]/bestaudio/best",
        "outtmpl": os.path.join(tmp_dir, "source.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=True)
        return ydl.prepare_filename(info), tmp_dir


TIME_PATTERN = re.compile(r"^(?:(\d{1,2}):)?([0-5]?\d):([0-5]\d)$")


def validate_time(time_str):
    """Validate and normalize a time string in MM:SS or HH:MM:SS format."""
    match = TIME_PATTERN.match(time_str.strip())
    if not match:
        return None
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2))
    seconds = int(match.group(3))
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


try:
    source_path, tmp_dir = download_audio(url)
except Exception as e:
    st.error(f"Failed to download audio: {e}")
    st.stop()

with st.expander("Get stitchin'", expanded=True):
    c1, c2 = st.columns(2)

    with c1:
        start = st.text_input("Start (MM:SS)", "00:00")
        tempo = st.slider(
            "Tempo", 0.5, 2.0, 1.0, 0.05,
            help="1.0 = original speed, >1 = faster, <1 = slower",
        )

    with c2:
        end = st.text_input("End (MM:SS)", "00:10")
        loop = st.slider("Loops", 1, 10, 1, 1)

    start_fmt = validate_time(start)
    end_fmt = validate_time(end)

    if not start_fmt:
        st.warning(f'Invalid start time "{start}". Use MM:SS or HH:MM:SS format.')
    if not end_fmt:
        st.warning(f'Invalid end time "{end}". Use MM:SS or HH:MM:SS format.')

    if not (start_fmt and end_fmt):
        st.stop()

    if st.button("Stitch!", type="primary"):
        cut_path = os.path.join(tmp_dir, "cut.mp4")
        looped_path = os.path.join(tmp_dir, "looped.wav")
        output_path = os.path.join(tmp_dir, "output.wav")

        try:
            with st.spinner("Cutting audio segment..."):
                subprocess.run(
                    ["ffmpeg", "-i", source_path, "-ss", start_fmt,
                     "-to", end_fmt, "-c", "copy", "-y", cut_path],
                    capture_output=True, check=True,
                )

            with st.spinner("Looping and converting audio..."):
                subprocess.run(
                    ["ffmpeg", "-stream_loop", str(loop - 1), "-i", cut_path,
                     "-ab", "160k", "-ac", "2", "-ar", "44100", "-vn",
                     "-y", looped_path],
                    capture_output=True, check=True,
                )

            if tempo != 1.0:
                with st.spinner("Adjusting tempo..."):
                    scale = 1.0 / tempo
                    subprocess.run(
                        ["rubberband", "-t", str(scale),
                         looped_path, output_path],
                        capture_output=True, check=True,
                    )
            else:
                output_path = looped_path

            st.audio(output_path, format="audio/wav")
            st.success("Done!")

        except subprocess.CalledProcessError as e:
            st.error(f"Audio processing failed: {e.stderr.decode()}")
        except FileNotFoundError as e:
            st.error(
                f"Required tool not found: {e}. "
                "Ensure ffmpeg and rubberband-cli are installed."
            )
