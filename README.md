# audiostitcher
A streamlit app that allows you to download, slow down, and loop audio segments downloaded from YouTube. I use this when learning new guitar licks to slow down tricky bits, and to loop them for practice.

# Setup
This has been (minimally) tested on OSX. Caveat emptor.

1. `brew install ffmpeg`
2. `brew install rubberband`
3. `pip install -e requirements.txt`
4. `git clone https://github.com/bradshawben/audiostitcher.git`
5. `cd audiostitcher`
6. `streamlit run audiostitcher.py`

Note that when using the app several versions of the video will be downloaded into the directory from which the app is running. Subsequent videos will simply overwrite these statically named files.
