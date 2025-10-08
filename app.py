import streamlit as st
from PIL import Image
from io import BytesIO
import boto3
import time

# --- Streamlit Config ---
st.set_page_config(page_title="Cat → Dog Interpolation Viewer", layout="centered")
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

# --- Load frame keys from S3 ---
response = s3.list_objects_v2(Bucket=BUCKET, Prefix=PREFIX)
contents = response.get("Contents", [])
if not contents:
    st.error(f"No frames found in s3://{BUCKET}/{PREFIX}")
    st.stop()

frame_keys = [obj["Key"] for obj in contents if obj["Key"].endswith(".png")]
frame_keys = sorted(frame_keys, key=lambda x: int("".join(filter(str.isdigit, x)) or 0))

# --- UI ---
frame_idx = st.slider(
    "Frame index",
    min_value=0,
    max_value=len(frame_keys) - 1,
    value=0,
    step=1,
)

# --- Load selected frame ---
key = frame_keys[frame_idx]
obj = s3.get_object(Bucket=BUCKET, Key=key)
img = Image.open(BytesIO(obj["Body"].read()))
st.image(img, caption=key.split("/")[-1], use_container_width=True)

# --- Optional autoplay ---
autoplay = st.checkbox("Autoplay", value=False)
speed = st.slider("Speed (frames/sec)", 1, 20, 5) if autoplay else None

if autoplay:
    placeholder = st.empty()
    for i, key in enumerate(frame_keys):
        obj = s3.get_object(Bucket=BUCKET, Key=key)
        img = Image.open(BytesIO(obj["Body"].read()))
        placeholder.image(img, caption=key.split("/")[-1], use_container_width=True)
        time.sleep(1 / speed)

