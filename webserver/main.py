from flask import Flask, Response
import numpy as np
import os
import time
from io import BytesIO
from PIL import Image

app = Flask(__name__)

# Wait for palette file
palette_path = "/tmp/doom_palette.txt"
while not os.path.exists(palette_path):
    print(f"Waiting for {palette_path}...")
    time.sleep(0.1)

# Load palette
PALETTE = np.loadtxt(palette_path, dtype=np.uint8)  # shape (256,3)

# Doom resolution (adjust if needed)
WIDTH, HEIGHT = 320, 200
PIPE_PATH = "/tmp/doom_pipe"

def frame_generator():
    while True:
        if os.path.exists(PIPE_PATH):
            with open(PIPE_PATH, "rb") as f:
                data = f.read(WIDTH * HEIGHT)
                if len(data) != WIDTH * HEIGHT:
                    continue
                # Map 8-bit indices to RGB
                rgb = PALETTE[np.frombuffer(data, dtype=np.uint8)].reshape((HEIGHT, WIDTH, 3))
                # Convert to JPEG in memory
                img = Image.fromarray(rgb, mode="RGB")
                buf = BytesIO()
                img.save(buf, format="JPEG")
                frame_bytes = buf.getvalue()
                # Yield MJPEG frame
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        time.sleep(0.01)

@app.route("/stream")
def stream():
    return Response(frame_generator(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
