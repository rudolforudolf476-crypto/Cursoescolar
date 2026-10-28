"""Pure target selection, independent of Windows and the detector."""
from dataclasses import dataclass
from math import hypot


@dataclass(frozen=True)
class Target:
    x: float
    y: float
    distance: float


def sensitivity_factor(distance, radius, minimum):
    """Smoothly blend centre resistance into full sensitivity at the edge."""
    if radius <= 0 or not 0 < minimum <= 1:
        raise ValueError('Use positive radius and minimum in (0, 1].')
    if distance is None:
        return 1.0
    ratio = max(0.0, min(1.0, distance / radius))
    blend = ratio * ratio * (3.0 - 2.0 * ratio)
    return minimum + (1.0 - minimum) * blend


def select_target(boxes, center, radius, confidence=0.35, aim_point="head"):
    """Boxes contain x1, y1, x2, y2, score, class; COCO person is class 0.

    Estimate head (12% down the box) or upper torso (30%) as reference. Exclude large boxes reaching the bottom of the view (local character heuristic).
    """
    if aim_point not in ("head", "torso"):
        raise ValueError("aim_point must be head or torso")
    offset = 0.12 if aim_point == "head" else 0.30
    cx, cy = center
    candidates = []
    for x1, y1, x2, y2, score, class_id in boxes:
        if int(class_id) != 0 or score < confidence or x2 <= x1 or y2 <= y1:
            continue
        if y2 >= cy * 1.8 and y2 - y1 >= cy * 0.8:
            continue
        x, y = (x1 + x2) / 2, y1 + (y2 - y1) * offset
        distance = hypot(x - cx, y - cy)
        if distance <= radius:
            candidates.append(Target(x, y, distance))
    return min(candidates, key=lambda target: target.distance, default=None)

