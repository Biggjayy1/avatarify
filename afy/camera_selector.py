import cv2
import numpy as np
import yaml

from afy.utils import log


g_selected_cam = None


def query_cameras(n_cams):
    cam_frames = {}
    cap = None
    for camid in range(n_cams):
        log(f"Trying camera with id {camid}")
        cap = cv2.VideoCapture(camid)

        if not cap.isOpened():
            log(f"Camera with id {camid} is not available")
            continue

        ret, frame = cap.read()

        if not ret or frame is None:
            log(f"Could not read from camera with id {camid}")
            cap.release()
            continue

        for i in range(10):
            ret, frame = cap.read()

        cam_frames[camid] = frame.copy()

        cap.release()

    return cam_frames


def make_grid(images, cell_size=(320, 240), cols=2):
    w0, h0 = cell_size
    grid = np.zeros((h0 * max(1, (len(images) // cols)), w0 * min(len(images), cols), 3), dtype=np.uint8)
    for i, (camid, img) in enumerate(images.items()):
        img = cv2.resize(img, (w0, h0))
        # add rect
        img = cv2.rectangle(img, (1, 1), (w0 - 1, h0 - 1), (0, 0, 255), 2)
        # add id
        img = cv2.putText(img, f'{camid}', (10, 30), 0, 1, (0, 255, 0), 2)
        c = i % cols
        r = i // cols
        grid[r * h0:(r + 1) * h0, c * w0:(c + 1) * w0] = img[..., :3]
    return grid


def mouse_callback(event, x, y, flags, userdata):
    global g_selected_cam
    if event == 1:
        cell_size, grid_cols = userdata
        c = x // cell_size[0]
        r = y // cell_size[1]
        camid = r * grid_cols + c
        g_selected_cam = camid


def select_camera(cam_frames, window="cameras"):
    cell_size = 320, 240
    grid_cols = 2
    grid = make_grid(cam_frames, cols=grid_cols)

    cv2.namedWindow(window)
    cv2.setMouseCallback(window, mouse_callback, (cell_size, grid_cols))
    cv2.imshow(window, grid)

    while True:
        key = cv2.waitKey(10)

        if g_selected_cam is not None:
            break
        
        if key == 27:
            break

    cv2.destroyAllWindows()

    return list(cam_frames)[g_selected_cam]


if __name__ == '__main__':
    with open('config.yaml', 'r') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    cam_frames = query_cameras(config['query_n_cams'])

    if cam_frames:
        selected_cam = select_camera(cam_frames)
        print(f"Selected camera {selected_cam}")
    else:
        log("No cameras are available")
