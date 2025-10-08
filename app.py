import streamlit as st
from PIL import Image
from io import BytesIO
import boto3
import time

# --- Streamlit Config ---
st.set_page_config(page_title="🐱 → 🐶 Interpolation Viewer", layout="centered")
st.title("🐱 → 🐶  Image Interpolation Viewer")

# --- AWS Config ---
aws_cfg = st.secrets["aws"]
s3 = boto3.client(
    "s3",
    aws_access_key_id=aws_cfg["access_key_id"],
    aws_secret_access_key=aws_cfg["secret_access_key"],
    region_name=aws_cfg["region"],
)
BUCKET = aws_cfg["bucket"]
PREFIX = aws_cfg["prefix"]

# --- Load all images once and cache them ---
@st.cache_resource(show_spinner="Loading frames from S3...")
def load_all_images():
    """Fetch all PNG frames from S3 and keep them in memory."""
    response = s3.list_objects_v2(Bucket=BUCKET, Prefix=PREFIX)
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

frames = load_all_images()
if not frames:
    st.error(f"No frames found in s3://{BUCKET}/{PREFIX}")
    st.stop()

# --- Smooth fade transition via CSS ---
st.markdown("""
<style>
img {
  transition: opacity 0.25s ease-in-out;
}
</style>
""", unsafe_allow_html=True)

# --- UI controls ---
frame_idx = st.slider("Frame index", 0, len(frames) - 1, 0, 1)
autoplay = st.checkbox("Autoplay", value=False)
speed = st.slider("Speed (frames/sec)", 1, 20, 5) if autoplay else None

# --- Display area ---
placeholder = st.empty()
caption, img = frames[frame_idx]
placeholder.image(img, caption=caption, use_container_width=True)

# --- Autoplay loop ---
if autoplay:
    for caption, img in frames:
        placeholder.image(img, caption=caption, use_container_width=True)
        time.sleep(1 / speed)

