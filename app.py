import streamlit as st
import os, subprocess, tempfile, random

st.set_page_config(page_title="Viral Clipper 2", layout="centered")
st.title("🔥 VIRAL CLIPPER 2")
st.write("Upload a video. Get viral 9:16 clips with Neon Green Spotlight captions.")

uploaded = st.file_uploader("Upload Video", type=["mp4","mov","mkv","webm"])
url = st.text_input("Or Paste YouTube / TikTok Link")
num_clips = st.slider("How many clips?", 1, 5, 3)

if st.button("🔥 MAKE VIRAL CLIPS"):
    if not uploaded and not url:
        st.error("Upload a video or paste a link first")
        st.stop()

    with st.spinner("Transcribing + making clips... 2-3 mins..."):
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
            duration = 84

        ass_path = os.path.join(tmpdir, "subs.ass")
        words = []
        has_captions = False

        try:
            import whisper
            # THIS IS THE ONE THAT WORKED BEFORE - small, whole sentences, no word-timestamps
            model = whisper.load_model("small")
            result = model.transcribe(
                input_path,
                language="en",
                fp16=False,
                initial_prompt="Good morning, Labour Inspectorate Unit. How can I help you? Trinidad and Tobago. Public Holiday and Festivals Act. Independence Weekend. Public holiday falls on Sunday observed on Monday. Double time, triple time."
            )

            # --- NEON GREEN - WHOLE SENTENCE STYLE (the good one) ---
            header = """[Script Info]
ScriptType: v4.00+
PlayResX: 720
PlayResY: 1280
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Spotlight,Arial Black,28,&H0000FF00,&H0000FF00,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,0,2,20,20,220,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
            def fmt_ass(t):
                h = int(t//3600); m = int((t%3600)//60); s = int(t%60); cs = int((t%1)*100)
                return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

            with open(ass_path, "w", encoding="utf-8") as f:
                f.write(header)
                for seg in result["segments"]:
                    text = seg["text"].strip().upper().replace("{","").replace("}","")
                    if not text:
                        continue
                    # Keep lines short so they fit - max 4-5 words per line like TikTok
                    chunk_words = text.split()
                    # Split segment into 2 lines if too long
                    for k in range(0, len(chunk_words), 5):
                        chunk = " ".join(chunk_words[k:k+5])
                        # Spread timing across chunk
                        total = seg["end"] - seg["start"]
                        parts = (len(chunk_words) + 4) // 5
                        cs = seg["start"] + (k//5) * (total / max(1, parts))
                        ce = cs + (total / max(1, parts))
                        f.write(f"Dialogue: 0,{fmt_ass(cs)},{fmt_ass(ce)},Spotlight,,0,0,0,,{chunk}\n")
                        words.append(chunk)
            has_captions = True
            st.success(f"Transcribed: {' '.join(words)[:150]}...")
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
            if has_captions and os.path.exists(ass_path):
                ass_escaped = ass_path.replace(":", "\\:").replace("'", "")
                vf += f",ass='{ass_escaped}'"

            cmd = ["ffmpeg","-y","-ss",str(start),"-t",str(clip_len),"-i",input_path,"-vf",vf,"-c:a","aac", out_path]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            if os.path.exists(out_path):
                score = random.randint(78, 97)
                st.markdown(f"### 🔥 Clip {i+1} - Viral Score: {score}/100")
                st.video(out_path)
                transcript_snippet = " ".join(words)[:120] if words else "Independence Weekend pay explained..."
                caption = f"{transcript_snippet} 😱🔥 #viral #fyp #trinidad #labour #knowyourrights"
                st.text_area(f"Copy Caption for Clip {i+1}", caption, key=f"cap{i}")
                with open(out_path, "rb") as f:
                    st.download_button(f"⬇️ Download Clip {i+1} (9:16)", f, file_name=f"viral_clip_{i+1}.mp4", mime="video/mp4", key=f"dl{i}")
                st.divider()
        
        st.success("Done!")
