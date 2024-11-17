class Tile:
    def __init__(self, angle):
        self.angle = angle
        self.orig_x, self.orig_y = 0.0, 0.0
        self.x, self.y = 0.0, 0.0
        self.orig_rotation, self.rotation = 0, 0
        self.orig_opacity, self.opacity = 100, 100
        self.orig_scale = 100
        self.w, self.h = 100, 100
        self.orig_trackStyle, self.style = None, None
        self.bpm = 0.0
        self.beat = 0.0
        self.ms = 0.0
        self.orbit = True
        self.pause = 0.0
        self.actions_start, self.actions_stop = None, None
        self.orig_trackColor, self.trackColor = None, None
        self.orig_secondaryTrackColor, self.secondaryTrackColor = None, None

    def is_placeholder(self):
        return self.angle in (555, 666, 777, 888, 999)

    def is_midspin_placeholder(self):
        return self.angle == 999
