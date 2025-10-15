import streamlit as st
from PIL import Image
from io import BytesIO
import boto3
import time

# -------------------------------------------------
# Streamlit Configuration
# -------------------------------------------------
st.set_page_config(page_title="REECAP Backprojection Explorer", layout="centered")
st.title("🔬 REECAP Backprojection Explorer")
st.caption("Visualizing interpolated retinal reconstructions along learned latent axes")

# -------------------------------------------------
# AWS Configuration
# -------------------------------------------------
aws_cfg = st.secrets["aws"]
s3 = boto3.client(
    "s3",
    aws_access_key_id=aws_cfg["access_key_id"],
    aws_secret_access_key=aws_cfg["secret_access_key"],
    region_name=aws_cfg["region"],
)
BUCKET = aws_cfg["bucket"]
PREFIX = aws_cfg["prefix"]

# -------------------------------------------------
# Utility Functions
# -------------------------------------------------
@st.cache_resource(show_spinner="Scanning available directions from S3…")
def list_directions():
    """Return sorted list of subfolder prefixes under the main prefix."""
    response = s3.list_objects_v2(Bucket=BUCKET, Prefix=PREFIX, Delimiter="/")
    prefixes = [p["Prefix"] for p in response.get("CommonPrefixes", [])]
    dirs = [p.rstrip("/").split("/")[-1] for p in prefixes]
    return sorted(dirs)

@st.cache_resource(show_spinner="Loading images from selected direction…")
def load_images(direction):
    """Fetch all PNG frames from a given direction subfolder."""
    dir_prefix = f"{PREFIX}{direction}/"
    response = s3.list_objects_v2(Bucket=BUCKET, Prefix=dir_prefix)
    keys = sorted(
        [obj["Key"] for obj in response.get("Contents", []) if obj["Key"].endswith(".png")],
        key=lambda x: int("".join(filter(str.isdigit, x)) or 0),
    )

    frames = []
    for key in keys:
        obj = s3.get_object(Bucket=BUCKET, Key=key)
        img = Image.open(BytesIO(obj["Body"].read())).copy()
        frames.append((key.split("/")[-1], img))
    return frames

# -------------------------------------------------
# Discover available directions
# -------------------------------------------------
dirs = list_directions()
if not dirs:
    st.error(f"No subfolders found in s3://{BUCKET}/{PREFIX}")
    st.stop()

anon_map = {f"Direction {i+1}": d for i, d in enumerate(dirs)}

# -------------------------------------------------
# Sidebar: Direction navigation
# -------------------------------------------------
st.sidebar.header("Directions")
selected_label = st.sidebar.radio(
    "Select direction",
    list(anon_map.keys()),
    index=0,
    label_visibility="collapsed"
)
selected_dir = anon_map[selected_label]

# -------------------------------------------------
# Load frames for the selected direction
# -------------------------------------------------
frames = load_images(selected_dir)
if not frames:
    st.error(f"No PNG images found in s3://{BUCKET}/{PREFIX}{selected_dir}/")
    st.stop()

# -------------------------------------------------
# Initialize session state for zoom
# -------------------------------------------------
if "zoom" not in st.session_state:
    st.session_state.zoom = 800  # starting width in pixels

# -------------------------------------------------
# Display image + frame slider
# -------------------------------------------------
placeholder = st.empty()
frame_idx = st.slider(
    "Frame index",
    0,
    len(frames) - 1,
    0,
    1,
    key="frame_slider",
    label_visibility="visible",
)
caption, img = frames[frame_idx]
placeholder.image(
    img,
    caption=f"{selected_label} | Frame {frame_idx+1}/{len(frames)}",
    width=st.session_state.zoom,
)

# -------------------------------------------------
# Playback + Zoom controls
# -------------------------------------------------
col1, col2, col3, col4 = st.columns([2.5, 1, 1, 1.5])
with col1:
    play = st.button("▶ Play sequence", use_container_width=True)
with col2:
    zoom_out = st.button("🔍 –", use_container_width=True)
with col3:
    zoom_in = st.button("🔍 +", use_container_width=True)
with col4:
    speed = st.slider("Speed (fps)", 1, 20, 5, label_visibility="collapsed")

# -------------------------------------------------
# Handle zoom clicks with instant refresh
# -------------------------------------------------
if zoom_in:
    st.session_state.zoom = min(st.session_state.zoom + 100, 1600)
    st.rerun()
elif zoom_out:
    st.session_state.zoom = max(st.session_state.zoom - 100, 400)
    st.rerun()

# -------------------------------------------------
# Run the animation once when Play is pressed
# -------------------------------------------------
if play:
    progress = st.progress(0)
    for i, (caption, img) in enumerate(frames):
        placeholder.image(
            img,
            caption=f"{selected_label} | Frame {i+1}/{len(frames)}",
            width=st.session_state.zoom,
        )
        progress.progress((i + 1) / len(frames))
        time.sleep(1 / speed)
    progress.empty()

# -------------------------------------------------
# Footer
# -------------------------------------------------
st.markdown("---")
st.markdown(
    "<p style='text-align:center; color:gray;'>"
    "REECAP – Representation learning for Eye Embedding Contrastive Age Phenotypes<br>"
    "Helmholtz Zentrum München · FAU Erlangen-Nürnberg · Broad Institute"
    "</p>",
    unsafe_allow_html=True,
)

