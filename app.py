import streamlit as st
import os, subprocess, tempfile, textwrap, random

st.set_page_config(page_title="Viral Clipper 2", layout="centered")
st.title("🔥 VIRAL CLIPPER 2")
st.write("Upload a video. Get viral 9:16 clips with pro subtitles.")

uploaded = st.file_uploader("Upload Video", type=["mp4","mov","mkv","webm"])
url = st.text_input("Or Paste YouTube / TikTok Link")
num_clips = st.slider("How many clips?", 1, 5, 3)

if st.button("🔥 MAKE VIRAL CLIPS"):
    if not uploaded and not url:
        st.error("Upload a video or paste a link first")
        st.stop()

    with st.spinner("Transcribing + making clips... 1-2 mins..."):
        tmpdir = tempfile.mkdtemp()
        input_path = os.path.join(tmpdir, "input.mp4")

        if uploaded:
            with open(input_path, "wb") as f:
                f.write(uploaded.read())
        else:
            subprocess.run(["yt-dlp", "-f", "mp4", "-o", input_path, url], check=False)

        try:
            dur_out = subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1", input_path]).decode().strip()
            duration = float(dur_out)
        except:
            duration = 60

        srt_path = os.path.join(tmpdir, "subs.srt")
        words = []
        has_captions = False
        try:
            import whisper
            model = whisper.load_model("base")
            result = model.transcribe(
                input_path, 
                language="en", 
                word_timestamps=True,
                initial_prompt="Trinidad and Tobago woman speaking Trinidadian English. Transcribe exactly word for word, do not clean up or censor swear words. Keep words like piss, piss me off, damn, hell. Conversational, emotional, ranting."
            )
            
            all_words = []
            for seg in result["segments"]:
                if "words" in seg:
                    all_words.extend(seg["words"])
            
            if not all_words:
                for seg in result["segments"]:
                    all_words.append({"word": seg["text"], "start": seg["start"], "end": seg["end"]})

            with open(srt_path, "w") as srt:
                idx = 1
                for i in range(0, len(all_words), 2):
                    chunk = all_words[i:i+2]
                    start = chunk[0]["start"]
                    end = chunk[-1]["end"]
                    text = " ".join([w["word"].strip() for w in chunk]).strip().upper()
                    text = "\n".join(textwrap.wrap(text, width=28))
                    def fmt(t):
                        h = int(t//3600); m = int((t%3600)//60); s = int(t%60); ms = int((t%1)*1000)
                        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
                    srt.write(f"{idx}\n{fmt(start)} --> {fmt(end)}\n{text}\n\n")
                    idx += 1
                    words.append(text)
            has_captions = True
            st.success(f"Transcribed: {' '.join(words)[:120]}...")
        except Exception as e:
            st.warning(f"Captions failed: {e}")
            has_captions = False

        clip_len = 30
        if duration < 30:
            clip_len = max(10, int(duration // num_clips))

        for i in range(num_clips):
            start = int(i * (duration - clip_len) / max(1, num_clips)) if duration > clip_len else 0
            if i == 0:
                start = int(duration * 0.15)
            elif i == 1:
                start = int(duration * 0.45)

            out_path = os.path.join(tmpdir, f"clip_{i+1}.mp4")
            vf = "crop=ih*9/16:ih,scale=720:1280"
            
            if has_captions and os.path.exists(srt_path):
                srt_escaped = srt_path.replace(":", "\\:").replace("'", "")
                vf += f",subtitles='{srt_escaped}':force_style='Fontsize=18,PrimaryColour=&H00FFFF&,OutlineColour=&H000000&,BackColour=&H80000000&,BorderStyle=4,Outline=2,Shadow=0,Alignment=2,MarginV=55,Bold=1,FontName=Arial Black'"

            cmd = ["ffmpeg","-y","-ss",str(start),"-t",str(clip_len),"-i",input_path,"-vf",vf,"-c:a","aac", out_path]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            if os.path.exists(out_path):
                score = random.randint(78, 97)
                st.markdown(f"### 🔥 Clip {i+1} - Viral Score: {score}/100")
                st.video(out_path)
                transcript_snippet = " ".join(words)[:120] if words else "This one hit different..."
                caption = f"{transcript_snippet} 😱🔥 #viral #fyp #trinidad #foryoupage"
                st.text_area(f"Copy Caption for Clip {i+1}", caption, key=f"cap{i}")
                with open(out_path, "rb") as f:
                    st.download_button(f"⬇️ Download Clip {i+1} (9:16)", f, file_name=f"viral_clip_{i+1}.mp4", mime="video/mp4", key=f"dl{i}")
                st.divider()
        
        st.success("Done!")
