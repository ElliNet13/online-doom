from flask import Flask, Response, send_from_directory
import numpy as np
from turbojpeg import TurboJPEG
import os

app = Flask(__name__)
jpeg_encoder = TurboJPEG()

PIPE_PATH = "/tmp/doom_pipe"
WIDTH, HEIGHT = 320, 200

# Wait for palette
palette_path = "/tmp/doom_palette.txt"
hasSaidWaiting = False
while not os.path.exists(palette_path):
    if not hasSaidWaiting:
        print("Waiting for palette...")
        hasSaidWaiting = True
PALETTE = np.loadtxt(palette_path, dtype=np.uint8)

# Doom palette is often 0–63, scale to 0–255
if PALETTE.max() <= 63:
    PALETTE = (PALETTE * 4).clip(0, 255).astype(np.uint8)

# Create named pipe if it doesn't exist
if not os.path.exists(PIPE_PATH):
    os.mkfifo(PIPE_PATH)

def get_latest_frame():
    """Read the latest frame from Doom pipe, dropping old ones."""
    while True:
        if os.path.exists(PIPE_PATH):
            with open(PIPE_PATH, "rb") as f:
                # Drop everything except latest frame
                while True:
                    data = f.read(WIDTH * HEIGHT)
                    if len(data) != WIDTH * HEIGHT:
                        break
                    rgb = PALETTE[np.frombuffer(data, dtype=np.uint8)].reshape((HEIGHT, WIDTH, 3))
                    # We need BGR for jpeg
                    bgr = rgb[:, :, ::-1]
                    yield bgr

def generate_mjpeg():
    for frame in get_latest_frame():

        jpeg = jpeg_encoder.encode(frame, quality=80)

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_mjpeg(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
@app.route('/')
def serve_index():
    return send_from_directory(STATIC_DIR, "index.html")

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(STATIC_DIR, filename)

if __name__ == '__main__':
    print("Starting web server on http://0.0.0.0:5000/")
    app.run(host='0.0.0.0', port=5000)
