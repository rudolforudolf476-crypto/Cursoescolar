"""Pure target selection, independent of Windows and the detector."""
from dataclasses import dataclass
from math import hypot


@dataclass(frozen=True)
class Target:
    x: float
    y: float
    distance: float


def select_target(boxes, center, radius, confidence=0.35):
    """Boxes contain x1, y1, x2, y2, score, class; COCO person is class 0.

    Use upper torso, not box centre, as the aiming point. Exclude large boxes reaching the bottom of the view (local character heuristic).
    """
    cx, cy = center
    candidates = []
    for x1, y1, x2, y2, score, class_id in boxes:
        if int(class_id) != 0 or score < confidence or x2 <= x1 or y2 <= y1:
            continue
        if y2 >= cy * 1.8 and y2 - y1 >= cy * 0.8:
            continue
        x, y = (x1 + x2) / 2, y1 + (y2 - y1) * 0.30
        distance = hypot(x - cx, y - cy)
        if distance <= radius:
            candidates.append(Target(x, y, distance))
    return min(candidates, key=lambda target: target.distance, default=None)

