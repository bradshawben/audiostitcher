import streamlit as st
import subprocess
import re

from pytube import YouTube


st.title('Audio stitcher')

url = st.text_input('Select a youtube URL')

if url:
    try:
        st.video(url)
    except Exception as e:
        st.error(f'Invalid url: {url}. Is this a valid Youtube video url?')
        raise

    with st.expander('Select a video', expanded=True):

        try:
            yt = YouTube(url)
        except Exception as e:
            raise e

        path = (
            yt.streams
            .filter(only_audio=True).filter(file_extension='mp4')
            .first()
            .download(filename='raw_yt.mp4'))
        c1, c2 = st.columns(2)

        index_pattern = re.compile(r'^[0-9]{2}:[0-9]{2}$')

        with c1:
            start = st.text_input('Start MM\:SS', '00:00')
            
            try:
                assert index_pattern.match(start)
            except:
                st.warning('start must be of the form "SS\:MM"')
                start = '00:00'

            tempo = st.slider('Tempo', 0.2, 1.0, 1.0, 0.05)

        with c2:
            end = st.text_input('End MM\\:SS', '00:10')

            try:
                assert index_pattern.match(end)
            except:
                st.warning('start must be of the form "SS\:MM"')
                end = '00:10'

            loop = st.slider('N Loops', 1, 10, 1, 1)

        # Cut the audio to the segment of interest
        ffmpeg_cut = f"ffmpeg -i raw_yt.mp4 -c copy -ss 00:{start} -to 00:{end} -y cut.mp4"
        subprocess.call(ffmpeg_cut, shell=True)

        # Loop the audio the desired number of times
        ffmpeg_loop = f'ffmpeg -stream_loop {int(loop)-1} -i cut.mp4 -c copy -y looped.mp4'
        subprocess.call(ffmpeg_loop, shell=True)

        # Scale to the desired tempo. Note a scale factor of X in Rubberband 
        # implies the segment is x times longer: X < 1 is faster, X > 1 slower.
        # It's more intuitive to have X < 1 => slower.
        scale = 2 - tempo
        assert float(tempo)
        ffmpeg_mp4_to_mp3 = "ffmpeg -i looped.mp4 -ab 160k -ac 2 -ar 44100 -vn -y looped.wav"
        subprocess.call(ffmpeg_mp4_to_mp3, shell=True)

        stretch = f'rubberband -t {scale} looped.wav scaled.wav'
        subprocess.call(stretch, shell=True)

        st.audio('scaled.wav', format="wav")
