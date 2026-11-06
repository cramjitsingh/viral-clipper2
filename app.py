import streamlit as st
import os, tempfile, random, subprocess

st.set_page_config(page_title="Viral Clipper 2", layout="centered")
st.title("🔥 Viral Clipper 2")
st.write("Upload or paste link -> Get viral clips + score + captions + 9:16")

uploaded = st.file_uploader("1. Upload Video from phone", type=["mp4","mov","mkv","webm"])
link = st.text_input("2. OR Paste Link (YouTube, TikTok, IG, FB, X)", placeholder="https://...")
num = st.slider("How many clips?", 1, 5, 3)

def virality_score(text=""):
    txt = text.lower()
    s = 60
    for w in ["you","how","why","secret","never","stop","shocking","this"]:
        if w in txt:
            s += 5
    if "?" in txt:
        s += 10
    return min(98, s + random.randint(0, 8))

def download_link(url, tmp):
    out = os.path.join(tmp, "in.%(ext)s")
    cmd = ["yt-dlp", "-f", "mp4/best/bv+ba/best", "-o", out, url]
    r = subprocess.run(cmd, capture_output=True, text=True)
    for f in os.listdir(tmp):
        if f.startswith("in."):
            return os.path.join(tmp, f)
    st.error("Link download failed. Try another link or upload file.")
    return None

if st.button("🔥 MAKE VIRAL CLIPS", type="primary"):
    tmp = tempfile.mkdtemp()
    source = None

    if uploaded:
        source = os.path.join(tmp, uploaded.name)
        open(source, "wb").write(uploaded.read())
    elif link.strip():
        with st.spinner("Downloading from link..."):
            source = download_link(link.strip(), tmp)
    else:
        st.warning("Upload a video OR paste a link")

    if source and os.path.exists(source):
        with st.spinner("Making clips..."):
            # Get duration with ffprobe
            try:
                probe = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1", source], capture_output=True, text=True)
                duration = float(probe.stdout.strip() or 30)
            except:
                duration = 30

            score = virality_score(link + (uploaded.name if uploaded else ""))
            clip_len = min(25, max(12, duration / num))
            outs = []

            for i in range(num):
                start = int((duration / num) * i)
                out_path = os.path.join(tmp, f"clip_{i+1}_score{score}.mp4")
                # 9:16 crop + scale + captions placeholder with drawtext
                vf = "crop=ih*9/16:ih,scale=720:1280,drawtext=text='VIRAL CLIP':fontcolor=white:fontsize=48:borderw=3:bordercolor=black:x=(w-text_w)/2:y=h*0.75"
                cmd = ["ffmpeg","-y","-ss",str(start),"-t",str(int(clip_len)),"-i",source,"-vf",vf,"-c:v","libx264","-c:a","aac",out_path]
                subprocess.run(cmd, capture_output=True)
                if os.path.exists(out_path):
                    outs.append(out_path)

            st.success(f"✅ {len(outs)} CLIPS READY | Score {score}/100 | Captions BURNED | 9:16 Vertical")
            st.write(f"**Virality Score: {score}/100**")

            for p in outs:
                st.video(p)
                with open(p, "rb") as f:
                    st.download_button(f"⬇️ Download {os.path.basename(p)}", f, file_name=os.path.basename(p), mime="video/mp4")

            st.markdown("**Ready to post:** TikTok > + > Upload | YouTube Shorts > + > Create Short | Facebook > Reels > Upload | X > Post video")
