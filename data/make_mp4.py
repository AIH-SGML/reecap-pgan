import imageio.v2 as imageio
from PIL import Image
import os
from os.path import join
import glob
import pdb

def make_mp4(direction_path, output_path="animation.mp4", fps=5):
    files = sorted(
        [f for f in os.listdir(direction_path) if f.endswith(".png")],
        key=lambda x: int(os.path.splitext(x)[0])
    )

    images = [imageio.imread(os.path.join(direction_path, f)) for f in files]
    imageio.mimsave(output_path, images, fps=fps, codec="libx264")
    print(f"✅ MP4 saved to {output_path}")

pdb.set_trace()
outdir = 'mp4s'
folders = glob.glob('*seed2025')
os.makedirs(outdir, exist_ok=True)
for i, folder in enumerate(folders):
    make_mp4(folder, output_path=join(outdir, 'direction_%.4d.mp4' % i), fps=5)

