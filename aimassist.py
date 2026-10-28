"""Screen-only Windows prototype. F8 exits globally."""
import argparse
import logging
from pathlib import Path
import ctypes
from ctypes import wintypes
import sys
import time

from targeting import select_target
from friction import MouseFriction


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--radius', type=int, default=25, help='Proximity radius in screen pixels')
    parser.add_argument('--slowdown', type=float, default=0.20, help='Mouse sensitivity multiplier near target')
    parser.add_argument('--aim-point', choices=['head', 'torso'], default='head', help='Estimated reference inside person box; not a head detector')
    parser.add_argument('--confidence', type=float, default=0.35)
    parser.add_argument('--monitor', type=int, default=1)
    parser.add_argument('--model', default='yolov8n.pt', help='COCO-compatible YOLO weights; downloaded on first use')
    parser.add_argument('--window-title', default='RedM', help='Required substring of foreground window title')
    parser.add_argument('--observe', action='store_true', help='Show detections without moving the mouse')
    args = parser.parse_args()
    if sys.platform != 'win32':
        parser.error('This application requires Windows 10/11.')
    if not (args.radius > 0 and 0 < args.slowdown <= 1 and 0 < args.confidence <= 1):
        parser.error('Use positive radius, slowdown and confidence in (0, 1].')
    if not args.window_title.strip():
        parser.error('--window-title must not be empty.')

    user32 = ctypes.WinDLL('user32', use_last_error=True)
    try:
        user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    except AttributeError:
        user32.SetProcessDPIAware()
    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
    user32.GetAsyncKeyState.restype = ctypes.c_short

    class MouseInput(ctypes.Structure):
        _fields_ = [('dx', wintypes.LONG), ('dy', wintypes.LONG),
                    ('mouseData', wintypes.DWORD), ('dwFlags', wintypes.DWORD),
                    ('time', wintypes.DWORD), ('dwExtraInfo', ctypes.c_size_t)]

    class KeyboardInput(ctypes.Structure):
        _fields_ = [('wVk', wintypes.WORD), ('wScan', wintypes.WORD),
                    ('dwFlags', wintypes.DWORD), ('time', wintypes.DWORD),
                    ('dwExtraInfo', ctypes.c_size_t)]

    class HardwareInput(ctypes.Structure):
        _fields_ = [('uMsg', wintypes.DWORD), ('wParamL', wintypes.WORD), ('wParamH', wintypes.WORD)]

    class InputUnion(ctypes.Union):
        _fields_ = [('mi', MouseInput), ('ki', KeyboardInput), ('hi', HardwareInput)]

    class Input(ctypes.Structure):
        _anonymous_ = ('value',)
        _fields_ = [('type', wintypes.DWORD), ('value', InputUnion)]

    user32.SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(Input), ctypes.c_int]
    user32.SendInput.restype = wintypes.UINT

    import cv2
    import mss
    import numpy as np
    from ultralytics import YOLO

    model = YOLO(args.model)
    print('Ativo automaticamente. F8 encerra. Apenas atua na janela indicada em primeiro plano.', flush=True)
    last_report = 0.0
    with mss.MSS() as capture:
        if args.monitor < 1 or args.monitor >= len(capture.monitors):
            parser.error('Monitor inválido; use um índice entre 1 e o número de monitores.')
        screen = capture.monitors[args.monitor]
        # A wider crop retains context for small/distant people.
        half = max(320, args.radius + 160)
        width, height = min(half * 2, screen['width']), min(half * 2, screen['height'])
        region = dict(left=screen['left'] + (screen['width'] - width) // 2,
                      top=screen['top'] + (screen['height'] - height) // 2,
                      width=width, height=height)
        center = (screen['left'] + screen['width'] / 2 - region['left'],
                  screen['top'] + screen['height'] / 2 - region['top'])
        friction = MouseFriction(user32, Input, MouseInput, args.slowdown)
        if not args.observe:
            friction.start()
        try:
            while True:
                if user32.GetAsyncKeyState(0x77) & 0x8000:
                    logging.warning('Encerramento: Windows reportou F8 premido (GetAsyncKeyState).')
                    break
                title = ctypes.create_unicode_buffer(1024)
                user32.GetWindowTextW(user32.GetForegroundWindow(), title, len(title))
                if args.window_title.casefold() not in title.value.casefold():
                    friction.activate(False)
                    time.sleep(0.05)
                    continue
                frame = np.asarray(capture.grab(region))[:, :, :3].copy()
                result = model.predict(frame, classes=[0], conf=args.confidence, verbose=False, imgsz=640)[0]
                boxes = result.boxes.data.cpu().tolist()
                target = select_target(boxes, center, args.radius, args.confidence, args.aim_point)
                # Recheck focus and emergency key after potentially slow inference.
                current = ctypes.create_unicode_buffer(1024)
                user32.GetWindowTextW(user32.GetForegroundWindow(), current, len(current))
                if user32.GetAsyncKeyState(0x77) & 0x8000:
                    logging.warning('Encerramento: Windows reportou F8 premido depois da inferência.')
                    break
                if friction.error:
                    raise friction.error
                friction.activate(not args.observe and target is not None and
                                  args.window_title.casefold() in current.value.casefold())
                if args.observe:
                    cv2.circle(frame, tuple(map(round, center)), args.radius, (0, 200, 255), 1)
                    if target:
                        cv2.circle(frame, (round(target.x), round(target.y)), 5, (0, 255, 0), -1)
                    cv2.imshow('Detecao — F8 encerra', frame)
                    cv2.waitKey(1)
                if time.monotonic() - last_report > 2:
                    print('Alvo detetado' if target else 'Sem alvo no centro', flush=True)
                    last_report = time.monotonic()
                time.sleep(0.005)
        finally:
            friction.close()
            cv2.destroyAllWindows()


if __name__ == '__main__':
    log_path = Path(__file__).with_name('aimassist.log')
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(message)s',
        handlers=[logging.FileHandler(log_path, encoding='utf-8'), logging.StreamHandler()],
    )
    logging.info('Arranque do programa. Registo: %s', log_path.name)
    try:
        main()
    except KeyboardInterrupt:
        logging.warning('Encerramento: Python recebeu KeyboardInterrupt (normalmente Ctrl+C/Ctrl+Break).')
        sys.exit(130)
    except SystemExit as exc:
        logging.info('Encerramento: SystemExit, código %s.', exc.code)
        raise
    except Exception:
        logging.exception('Encerramento por erro inesperado:')
        sys.exit(1)
    else:
        logging.info('Programa terminou normalmente após o pedido de saída registado acima.')
