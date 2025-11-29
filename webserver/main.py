import gevent.monkey
gevent.monkey.patch_all()

from flask import Flask, Response, send_from_directory
import numpy as np
from turbojpeg import TurboJPEG
import os
from flask_socketio import SocketIO, emit
import select

app = Flask(__name__)
jpeg_encoder = TurboJPEG()
socketio = SocketIO(app, async_mode="gevent")

PIPE_VIDEO_PATH = "/tmp/doom_video_pipe"
PIPE_INPUT_PATH = "/tmp/doom_input_pipe"
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
if not os.path.exists(PIPE_VIDEO_PATH):
    os.mkfifo(PIPE_VIDEO_PATH)

if not os.path.exists(PIPE_INPUT_PATH):
    os.mkfifo(PIPE_INPUT_PATH)

def get_latest_frame():
    """Read the latest frame from Doom video pipe, non-blocking."""
    if not os.path.exists(PIPE_VIDEO_PATH):
        os.mkfifo(PIPE_VIDEO_PATH)
    while True:
        with open(PIPE_VIDEO_PATH, "rb") as f:
            while True:
                rlist, _, _ = select.select([f], [], [], 0.1)  # 0.1 sec timeout
                if not rlist:
                    break  # No data ready, yield to server
                data = f.read(WIDTH * HEIGHT)
                if len(data) != WIDTH * HEIGHT:
                    break
                rgb = PALETTE[np.frombuffer(data, dtype=np.uint8)].reshape((HEIGHT, WIDTH, 3))
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


def send_to_doom(action, state):
    try:
        with open(PIPE_INPUT_PATH, "w") as pipe:
            pipe.write(f"{action}:{state}\n")
            pipe.flush()
    except Exception as e:
        print("Failed to write to Doom input pipe:", e)
        
# Handle messages from the client
@socketio.on("input_event")
def handle_input(data):
    action = data.get("action")
    state = data.get("state")
    if action and state:
        send_to_doom(action, state)

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
@app.route('/')
def serve_index():
    return send_from_directory(STATIC_DIR, "index.html")

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(STATIC_DIR, filename)

if __name__ == "__main__":
    print("Starting web server on http://0.0.0.0:5000/")
    socketio.run(app, host="0.0.0.0", port=5000)
