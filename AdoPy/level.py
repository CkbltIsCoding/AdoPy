import json
import math
import re
from bisect import bisect_left, bisect_right
from functools import cmp_to_key

from .ease import ease
from .tile import Tile


def deg2rad(deg):
    return deg * math.pi / 180


class Level:
    path_data_dict = {'R': 0, 'p': 15, 'J': 30, 'E': 45, 'T': 60, 'o': 75,
                      'U': 90, 'q': 105, 'G': 120, 'Q': 135, 'H': 150, 'W': 165,
                      'L': 180, 'orig_x': 195, 'N': 210, 'Z': 225, 'F': 240, 'V': 255,
                      'D': 270, 'Y': 285, 'B': 300, 'C': 315, 'M': 330, 'A': 345,
                      '5': 555, '6': 666, '7': 777, '8': 888, '!': 999}

    def __init__(self, data, path=None):
        self.tiles: [Tile] = []
        s = data["settings"]
        self.song = s["song"]
        self.path = path
        self.song_filename = s["songFilename"]
        self.offset = s["offset"]
        self.bpm = s["bpm"]
        self.trackColor = s["trackColor"]
        self.secondaryTrackColor = s["secondaryTrackColor"]
        self.position = s["position"]
        self.rotation = s["rotation"]
        self.zoom = s["zoom"]
        self.stickToFloors = s["stickToFloors"]
        self.trackStyle = s["trackStyle"]
        self.orig_trackAnimation, self.trackAnimation = s["trackAnimation"], None
        self.orig_beatsAhead, self.beatsAhead = s["beatsAhead"], None
        self.orig_trackDisappearAnimation, self.trackDisappearAnimation = s["trackDisappearAnimation"], None
        self.orig_beatsBehind, self.beatsBehind = s["beatsBehind"], None

        #
        if "angleData" in data:
            type_data = "angleData"
        elif "pathData" in data:
            type_data = "pathData"
        else:
            raise Exception()
        self.tiles.append(Tile(0, self.trackStyle, self.trackColor, self.secondaryTrackColor))
        for direction in data[type_data]:
            if type_data == "angleData":
                angle = direction
            else:
                angle = Level.path_data_dict[direction]
            self.tiles.append(Tile(angle, self.trackStyle, self.trackColor, self.secondaryTrackColor))

        self.actions = data["actions"]

        cmp = (lambda a, b:
               a["floor"] - b["floor"] if a["floor"] != b["floor"]
               else a["duration"] - b["duration"]
               if "duration" in a and "duration" in b
               else 0)
        self.actions.sort(key=cmp_to_key(cmp))

        self.update()

    @classmethod
    def from_file(cls, path):
        with open(
                path, "r", encoding="utf-8-sig"
        ) as f:
            string = f.read()
        string = re.sub(",(?=\\s*?[}\\]])", "", string)  # 删除尾随逗号
        return cls(json.loads(string, strict=False), path)

    def calc(self):
        self.calc_tiles_actions()
        self.calc_pos()
        self.calc_beat()

    def calc_tiles_actions(self):
        for i in range(len(self.tiles)):
            tile = self.tiles[i]
            tile.actions_start = bisect_left(self.actions, i, key=lambda action: action["floor"])
            tile.actions_stop = bisect_right(self.actions, i, key=lambda action: action["floor"])

    def calc_pos(self):
        for i in range(len(self.tiles)):
            tile = self.tiles[i]
            pre_tile = self.tiles[i - 1] if i != 0 else None
            next_tile = self.tiles[i + 1] if i != len(self.tiles) - 1 else None

            if pre_tile is None:
                tile.orig_x = tile.orig_y = 0
                continue
            tile.orig_x, tile.orig_y = pre_tile.orig_x, pre_tile.orig_y
            if ((next_tile is None or not next_tile.is_midspin_placeholder())
                    and not tile.is_placeholder()):
                tile.orig_x += math.cos(deg2rad(tile.angle))
                tile.orig_y += math.sin(deg2rad(tile.angle))

            for action in self.actions[tile.actions_start:tile.actions_stop]:
                if action["eventType"] == "PositionTrack":
                    index = self.find_tile_index(i, action["relativeTo"])
                    x, y = action["positionOffset"]
                    tile.orig_x = self.tiles[index].orig_x + x
                    tile.orig_y = self.tiles[index].orig_y + y

    def calc_beat(self, start=0):
        for i in range(start, len(self.tiles)):
            tile = self.tiles[i]
            pre_tile = self.tiles[i - 1] if i != 0 else None
            next_tile = self.tiles[i + 1] if i != len(self.tiles) - 1 else None
            actions = self.actions[tile.actions_start:tile.actions_stop]

            tile.orbit = pre_tile.orbit if pre_tile is not None else True

            for action in actions:
                if action["eventType"] == "Twirl":
                    tile.orbit = not tile.orbit
                elif action["eventType"] == "Pause":
                    tile.pause = action["duration"]

            if pre_tile is None:
                tile.beat = 0
                tile.ms = self.offset
                tile.bpm = self.bpm
                continue

            tile.bpm = pre_tile.bpm
            for action in actions:
                if action["eventType"] == "SetSpeed":
                    if action.get("speedType", "Bpm") == "Multiplier":
                        tile.bpm *= action["bpmMultiplier"]
                    else:
                        tile.bpm = action["beatsPerMinute"]
                    break

            if tile.is_midspin_placeholder():
                tile.beat = pre_tile.beat
                tile.ms = pre_tile.ms
                continue
            if pre_tile.is_midspin_placeholder():
                angle = self.tiles[i - 2].angle - tile.angle
            else:
                angle = pre_tile.angle - 180 - tile.angle
            if not pre_tile.orbit:
                angle *= -1
            angle %= 360
            if angle == 0:
                angle = 360
            if i == 1:
                angle -= 180
            tile.beat = angle / 180 + pre_tile.pause

            tile.ms = pre_tile.ms + tile.beat / (pre_tile.bpm / 60) * 1000

            tile.beat += pre_tile.beat

    def judge(self, tile_index, timer, difficulty="NORMAL"):
        tile = self.tiles[tile_index]
        max_bpm = (220 if difficulty == "LENIENT" else
                   310 if difficulty == "NORMAL" else
                   500)
        ms = 60 / min(max_bpm, tile.bpm) * 1000
        perfect = max(ms / 6, 25.0)
        late_early_perfect = max(ms / 4, 30.0)
        late_early = max(ms / 3, 40.0)

        timing = timer - tile.ms
        if abs(timing) < perfect:
            return "PERFECT"
        elif abs(timing) < late_early_perfect:
            if timing > 0:
                return "LATE_PERFECT"
            else:
                return "EARLY_PERFECT"
        elif abs(timing) < late_early:
            if timing > 0:
                return "LATE"
            else:
                return "EARLY"
        else:
            if timing > 0:
                return "TOO_LATE"
            else:
                return "TOO_EARLY"

    def find_tile_index(self, index, relative_to):
        if relative_to[1] == "ThisTile":
            return index + relative_to[0]
        elif relative_to[1] == "Start":
            return relative_to[0]
        elif relative_to[1] == "End":
            return len(self.tiles) - 1 - relative_to[0]
        else:
            raise Exception()

    def update(self, beat=None):
        self.trackAnimation, self.beatsAhead, self.trackDisappearAnimation, self.beatsBehind =\
        self.orig_trackAnimation, self.orig_beatsAhead, self.orig_trackDisappearAnimation, self.orig_beatsBehind
        for tile in self.tiles:
            tile.x, tile.y = tile.orig_x, tile.orig_y
            tile.rotation = tile.orig_rotation
            tile.opacity = tile.orig_opacity
            tile.w, tile.h = tile.orig_scale, tile.orig_scale
            tile.trackColor = self.trackColor
            tile.secondaryTrackColor = self.secondaryTrackColor

        if beat is None:
            return

        for action in self.actions:
            action_tile = self.tiles[action["floor"]]
            if beat < action_tile.beat:
                break
            match action["eventType"]:
                case "ColorTrack":
                    for tile in self.tiles:
                        tile.trackColor = action["trackColor"]
                        tile.secondaryTrackColor = action["secondaryTrackColor"]
                        tile.style = action["trackStyle"]

                case "RecolorTrack":
                    start = self.find_tile_index(action["floor"], action["startTile"])
                    stop = self.find_tile_index(action["floor"], action["endTile"]) + 1
                    for tile in self.tiles[start:stop]:
                        tile.trackColor = action["trackColor"]
                        tile.secondaryTrackColor = action["secondaryTrackColor"]
                        tile.style = action["trackStyle"]

                case "MoveTrack":
                    start = self.find_tile_index(action["floor"], action["startTile"])
                    stop = self.find_tile_index(action["floor"], action["endTile"]) + 1
                    for tile in self.tiles[start:stop]:
                        if action["duration"] == 0:
                            a = 1
                        else:
                            a = ease(action["ease"], (beat - action_tile.beat) / action["duration"])
                        if "positionOffset" in action:
                            x, y = action["positionOffset"]
                            if x is None or y is None:
                                continue
                            tile.x += (tile.orig_x + x - tile.x) * a
                            tile.y += (tile.orig_y + y - tile.y) * a
                        if action.get("scale", None) is not None:
                            if isinstance(action["scale"], int):
                                tile.w += (action["scale"] - tile.w) * a
                                tile.h += (action["scale"] - tile.h) * a
                            else:
                                tile.w += (action["scale"][0] - tile.w) * a
                                tile.h += (action["scale"][1] - tile.h) * a
                        if action.get("opacity", None) is not None:
                            tile.opacity += (action["opacity"] - tile.opacity) * a

                case "AnimateTrack":
                    if "trackAnimation" in action:
                        self.trackAnimation = action["trackAnimation"]
                    if "beatsAhead" in action:
                        self.beatsAhead = action["beatsAhead"]
                    if "trackDisappearAnimation" in action:
                        self.trackDisappearAnimation = action["trackDisappearAnimation"]
                    if "beatsBehind" in action:
                        self.beatsBehind = action["beatsBehind"]

        for i in range(len(self.tiles)):
            tile = self.tiles[i]
            pre_tile = self.tiles[i - 1] if i > 0 else None
            next_tile = self.tiles[i + 1] if i < len(self.tiles) - 1 else None
            if self.trackAnimation == "Fade" and pre_tile is not None:
                if pre_tile.beat - self.beatsAhead - beat > 0:
                    tile.opacity = tile.opacity - 100 * (pre_tile.beat - self.beatsAhead - beat)
                    tile.opacity = max(0, tile.opacity)
            if self.trackDisappearAnimation == "Fade" and next_tile is not None:
                if beat - next_tile.beat - self.beatsBehind > 0:
                    tile.opacity = tile.opacity - 100 * (beat - next_tile.beat - self.beatsBehind)
                    tile.opacity = max(0, tile.opacity)
