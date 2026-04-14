# ── sprite_manager.py ─────────────────────────────────────────────────────────
# Loads the sprite sheet and slices it into animation frames.
# Characters are selected by swapping the spritesheet path.

from PIL import Image, ImageTk
import config


class SpriteManager:
    """
    Loads a spritesheet PNG and slices it into frames.

    Sheet layout (each cell = SPRITE_SIZE × SPRITE_SIZE):
        Row 0: walk_right  (4 frames)
        Row 1: walk_left   (4 frames)
        Row 2: idle        (4 frames)
        Row 3: play        (4 frames)
        Row 4: stopped     (4 frames)
    """

    def __init__(self, scale: float = 1.0):
        self._scale   = scale
        self._size    = config.SPRITE_SIZE
        self._display = int(self._size * scale)
        self._frames: dict[str, list[ImageTk.PhotoImage]] = {}
        self._load(config.SPRITESHEET)

    def reload(self, path: str):
        """Hot-swap to a different spritesheet PNG."""
        self._frames.clear()
        self._load(path)

    def get_frame(self, anim: str, frame_idx: int) -> ImageTk.PhotoImage:
        frames = self._frames.get(anim)
        if not frames:
            raise ValueError(f"Unknown animation: {anim}")
        return frames[frame_idx % len(frames)]

    def frame_count(self, anim: str) -> int:
        return len(self._frames.get(anim, []))

    def _load(self, path: str):
        sheet = Image.open(path).convert("RGBA")
        for anim, row in config.ANIM_ROW.items():
            self._frames[anim] = []
            for col in range(config.ANIM_FRAMES):
                S  = self._size
                frame = sheet.crop((col*S, row*S, (col+1)*S, (row+1)*S))
                if self._display != S:
                    frame = frame.resize(
                        (self._display, self._display), Image.LANCZOS)
                self._frames[anim].append(ImageTk.PhotoImage(frame))
        print(f"[sprite] loaded: {path}")
