"""
author: CkbltIsCoding
"""

import math
import os.path
from bisect import bisect_right
from tkinter import filedialog

import pygame
from pygame.locals import *
from pygame.math import Vector2 as Pt

from AdoPy import Level
from AdoPy.ease import ease


def deg2rad(deg):
    return deg * math.pi / 180


def move(deg):
    return math.cos(deg2rad(deg)), math.sin(deg2rad(deg))


class AdoPygame:
    def __init__(self):
        self.running = True
        self.dragging = False
        self.state = "SELECTING"
        self.screen = None
        self.size = self.width, self.height = 800, 600
        self.level = None
        self.camera_pos = Pt()
        self.camera_pos_no = Pt()
        self.camera_zoom = 200
        self.camera_rotation = 0
        self.camera_relative_to = "Player"
        self.timer = None
        self.offset = -30
        self.beat = None
        self.autoplay = True
        self.orig_planet_radius = 50
        self.pr = 50.0  # planet_radius
        self.FPS = 120
        self.now_tile = None
        self.player_tile = None
        self.active_tile = None
        self.fullscreen = False
        self.keys = K_TAB, K_q, K_w, K_e, K_SPACE, K_a, K_p, K_LEFTBRACKET, K_RIGHTBRACKET, K_BACKSLASH
        self.key_pressed_cnt = 0
        self.render_tiles_dict = {}
        self.cur = None

    def switch_fullscreen(self, fullscreen):
        self.fullscreen = fullscreen
        if fullscreen:
            self.size = self.width, self.height = pygame.display.list_modes()[0]
            self.screen = pygame.display.set_mode(self.size, pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF)
        else:
            self.size = self.width, self.height = 800, 600
            self.screen = pygame.display.set_mode(self.size, pygame.HWSURFACE | pygame.DOUBLEBUF)

    def on_init(self):
        pygame.init()
        pygame.mixer.init()
        self.switch_fullscreen(False)
        pygame.display.set_caption("A Dance of Pygame")
        self.running = True
        self.clock = pygame.time.Clock()
        self.font_ascii_debug = pygame.font.SysFont("Consolas", 18)
        self.font_debug = pygame.font.SysFont("SimHei", 18)  # 黑体
        return True

    def on_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.KEYDOWN:
            if self.state == "PLAYING" and event.dict["key"] in self.keys:
                self.key_pressed_cnt += 1
            match event.dict["key"]:
                case pygame.K_F11:
                    self.switch_fullscreen(not self.fullscreen)
                case pygame.K_RETURN:
                    if self.state == "CHARTING" or self.state == "SELECTING":
                        path = filedialog.askopenfilename()
                        if path != "":
                            self.load_level(path)
                case pygame.K_SPACE:
                    if self.state == "CHARTING":
                        self.state = "PLAYING"
                        self.player_tile = 0
                        pygame.mixer_music.play()
                        self.camera_pos = Pt(self.level.position)
                        self.cur = {
                            "TOO_EARLY": 0,
                            "EARLY": 0,
                            "EARLY_PERFECT": 0,
                            "PERFECT": 0,
                            "LATE_PERFECT": 0,
                            "LATE": 0,
                            "TOO_LATE": 0,
                        }
                case pygame.K_F12:
                    self.autoplay = not self.autoplay
                case pygame.K_ESCAPE:
                    if self.state == "PLAYING":
                        self.state = "CHARTING"
                        self.now_tile = None
                        self.beat = None
                        self.timer = None
                        pygame.mixer_music.stop()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.dragging = True
            pygame.mouse.get_rel()

    def on_loop(self):
        if self.state == "PLAYING":
            self.timer = pygame.mixer_music.get_pos()
            self.now_tile = bisect_right([tile.ms for tile in self.level.tiles[1:]], self.timer)
            if self.level.tiles[self.now_tile].is_placeholder():
                self.now_tile -= 1

            if self.autoplay:
                self.player_tile = self.now_tile

            tile = self.level.tiles[self.now_tile]
            self.beat = (tile.beat + (self.timer - tile.ms) / 1000 * tile.bpm / 60)

            camera_pos = Pt(self.level.position)
            self.camera_zoom = self.level.zoom
            self.camera_rotation = self.level.rotation
            player_offset_pos = [0, 0]
            for action in self.level.actions:
                action_tile = self.level.tiles[action["floor"]]
                if self.beat < action_tile.beat:
                    break
                if action["eventType"] == "MoveCamera":
                    if action["duration"] == 0 or action["ease"] == "OutFlash":
                        a = 1
                    else:
                        a = ease(action["ease"], (self.beat - action_tile.beat) / action["duration"])
                    if "zoom" in action:
                        self.camera_zoom += (action["zoom"] - self.camera_zoom) * a
                    if "rotation" in action:
                        self.camera_rotation += (action["rotation"] - self.camera_rotation) * a
                    if "relativeTo" in action:
                        self.camera_relative_to = action["relativeTo"]
                    if "position" in action:
                        x, y = action["position"]
                        if self.camera_relative_to == "Tile":
                            if x is not None:
                                # camera_pos += (Pt(action_tile.x, action_tile.y) + action["position"] - camera_pos) * a
                                camera_pos.x += (action_tile.x + x - camera_pos.x) * a
                            if y is not None:
                                camera_pos.y += (action_tile.y + y - camera_pos.y) * a
                        else:
                            if x is not None:
                                player_offset_pos[0] += (x - player_offset_pos[0]) * a
                            if y is not None:
                                player_offset_pos[1] += (y - player_offset_pos[1]) * a

            self.camera_zoom = max(10, self.camera_zoom)
            if self.camera_relative_to == "Player":
                pos = Pt(tile.x, tile.y)
                pos_x = pos.x - self.camera_pos_no.x >= 0
                pos_y = pos.y - self.camera_pos_no.y >= 0
                self.camera_pos_no.x += (pos_x * 2 - 1) * abs(pos.x - self.camera_pos_no.x) ** 1.4 * 0.125
                self.camera_pos_no.y += (pos_y * 2 - 1) * abs(pos.y - self.camera_pos_no.y) ** 1.4 * 0.125
                self.camera_pos = self.camera_pos_no + player_offset_pos
            else:
                self.camera_pos_no = camera_pos
                self.camera_pos = camera_pos

            if not self.autoplay:
                while self.level.judge(self.player_tile + 1, self.timer + self.offset) == "TOO_LATE":
                    self.player_tile += 1
                    self.cur["TOO_LATE"] += 1
                for _ in range(self.key_pressed_cnt):
                    judgement = self.level.judge(self.player_tile + 1, self.timer + self.offset)
                    if judgement != "TOO_EARLY":
                        self.player_tile += 1
                    self.cur[judgement] += 1

            self.key_pressed_cnt = 0

            self.level.update(self.beat)

        elif self.state == "CHARTING":
            if self.dragging and pygame.mouse.get_pressed()[0]:
                pos = Pt(pygame.mouse.get_rel())
                pos.y *= -1
                self.camera_pos -= pos * self.camera_zoom / 100 / (self.orig_planet_radius * 4)
            else:
                self.dragging = False

            self.level.update()

    def on_render(self):
        self.screen.fill("#000000")

        if self.level is not None:
            self.pr = self.orig_planet_radius * 100 / self.camera_zoom
            self.render_tiles()
            if self.state == "PLAYING":
                self.render_planets()

        self.render_text()
        pygame.display.flip()

    def render_planets(self):
        tile = self.level.tiles[self.player_tile]
        red = "#dd3333"
        blue = "#3366cc"
        if self.level.stickToFloors == "Enabled":
            x, y = tile.x, tile.y
        else:
            x, y = tile.orig_x, tile.orig_y
        pos = self.cnv2screen(Pt(x, y))
        pygame.draw.circle(self.screen, blue if self.player_tile % 2 else red, pos, self.pr)
        if self.player_tile == 0:
            angle = 0
        else:
            angle = tile.angle - 180
        if self.player_tile + 1 < len(self.level.tiles) \
                and self.level.tiles[self.player_tile + 1].is_midspin_placeholder():
            angle += 180
        offset_beat = 0 if self.autoplay else self.offset / 1000 / (60 / tile.bpm)
        if tile.orbit:
            angle -= (self.beat + offset_beat - tile.beat) * 180
        else:
            angle += (self.beat + offset_beat - tile.beat) * 180
        x += move(angle)[0]
        y += move(angle)[1]
        pos = self.cnv2screen(Pt(x, y))
        pygame.draw.circle(self.screen, red if self.player_tile % 2 else blue, pos, self.pr)

    def render_tiles(self):
        pr = self.pr
        br = self.pr * 21 / 20
        square = pygame.Surface((pr * 2, pr * 2), pygame.SRCALPHA)
        rect = pygame.Surface((pr * 4, pr * 2), pygame.SRCALPHA)
        half_square = pygame.Surface((pr, pr * 2), pygame.SRCALPHA)
        square_b = pygame.Surface((br * 2, br * 2), pygame.SRCALPHA)
        rect_b = pygame.Surface((br * 4, br * 2), pygame.SRCALPHA)
        half_square_b = pygame.Surface((br, br * 2), pygame.SRCALPHA)
        surf_tile_main = pygame.Surface((pr * 6, pr * 6), pygame.SRCALPHA)
        surf_tile_border = pygame.Surface((pr * 6, pr * 6), pygame.SRCALPHA)
        surf_tile_color = pygame.Surface((pr * 6, pr * 6), pygame.SRCALPHA)
        surf_tile = pygame.Surface((pr * 6, pr * 6), pygame.SRCALPHA)
        self.render_tiles_dict.clear()
        for index in range(len(self.level.tiles) - 1, -1, -1):
            tile = self.level.tiles[index]
            pre_tile = self.level.tiles[index - 1] if index > 0 else None
            next_tile = self.level.tiles[index + 1] if index < len(self.level.tiles) - 1 else None

            # 是否渲染
            if tile.is_placeholder():
                continue
            # continue
            screen_pos = self.cnv2screen(Pt(tile.x, tile.y))
            if not (-pr * 2 < screen_pos[0] < self.screen.get_width() + pr * 2
                    and -pr * 2 < screen_pos[1] < self.screen.get_height() + pr * 2):
                continue

            track_color = pygame.Color("#" + tile.trackColor)
            secondary_track_color = pygame.Color("#" + tile.secondaryTrackColor)

            if tile.opacity <= 0 or track_color.a == 0 and secondary_track_color.a == 0:
                continue

            match tile.style:
                case "Standard":
                    main_color = track_color
                    border_color = track_color // pygame.Color(2, 2, 2, 1)
                case "Neon":
                    main_color = pygame.Color("#000000")
                    border_color = track_color
                case "NeonLight":
                    main_color = track_color // pygame.Color(2, 2, 2, 1)
                    border_color = track_color
                case "Basic" | "Minimal" | "Gems":
                    main_color = track_color
                    border_color = pygame.Color("#00000000")
                case _:
                    raise Exception(tile.style)

            angle = tile.angle
            next_angle = next_tile.angle if next_tile else tile.angle
            key = (angle, next_angle,
                   main_color.normalize(),
                   border_color.normalize())

            if key in self.render_tiles_dict:
                surf_tile = self.render_tiles_dict[key].copy()
            else:
                square.fill("#ffffff")
                square_b.fill("#ffffff")
                half_square.fill("#ffffff")
                half_square_b.fill("#ffffff")
                rect.fill("#ffffff")
                rect_b.fill("#ffffff")
                surf_tile_main.fill("#00000000")
                surf_tile_border.fill("#00000000")
                surf_tile.fill("#00000000")

                if (angle - next_angle) % 360 == 180:  # 发卡砖块
                    pygame.draw.circle(surf_tile_main, "#ffffff", (pr * 3, pr * 3), round(pr))
                    pygame.draw.circle(surf_tile_border, "#ffffff", (pr * 3, pr * 3), round(br))
                    new_half_square = pygame.transform.rotate(half_square, angle)
                    pos = -Pt(move(angle)) * (pr // 2)
                    pos.y *= -1
                    surf_tile_main.blit(new_half_square, new_half_square.get_rect(center=pos + (pr * 3, pr * 3)))
                    new_half_square_b = pygame.transform.rotate(half_square_b, angle)
                    surf_tile_border.blit(new_half_square_b, new_half_square_b.get_rect(center=pos + (pr * 3, pr * 3)))
                elif angle == next_angle:  # 180° 砖块
                    new_rect = pygame.transform.rotate(rect, angle)
                    surf_tile_main.blit(new_rect, new_rect.get_rect(center=(pr * 3, pr * 3)))
                    new_rect_b = pygame.transform.rotate(rect_b, angle)
                    surf_tile_border.blit(new_rect_b, new_rect_b.get_rect(center=(pr * 3, pr * 3)))
                else:  # 普通砖块
                    pygame.draw.circle(surf_tile_main, "#ffffff", (pr * 3, pr * 3), round(pr))
                    pygame.draw.circle(surf_tile_border, "#ffffff", (pr * 3, pr * 3), round(br))
                    new_square = pygame.transform.rotate(square, angle)
                    new_square_b = pygame.transform.rotate(square_b, angle)
                    pos = -Pt(move(angle)) * pr
                    pos.y *= -1
                    surf_tile_main.blit(new_square, new_square.get_rect(center=pos + (pr * 3, pr * 3)))
                    surf_tile_border.blit(new_square_b, new_square_b.get_rect(center=pos + (pr * 3, pr * 3)))

                    if next_tile and next_tile.is_placeholder():
                        next_angle = self.level.tiles[index + 2].angle
                    new_square = pygame.transform.rotate(square, next_angle)
                    new_square_b = pygame.transform.rotate(square_b, next_angle)
                    pos = Pt(move(next_angle)) * pr
                    pos.y *= -1
                    surf_tile_main.blit(new_square, new_square.get_rect(center=pos + (pr * 3, pr * 3)))
                    surf_tile_border.blit(new_square_b, new_square_b.get_rect(center=pos + (pr * 3, pr * 3)))

                if main_color.a == 255:
                    surf_tile_color.fill(border_color)
                    surf_tile_color.blit(surf_tile_border, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                    surf_tile.blit(surf_tile_color, (0, 0))
                else:
                    mask = pygame.mask.from_surface(surf_tile_main)
                    surf_tile_color.fill(border_color)
                    surf_tile_color.blit(surf_tile_border, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                    mask.to_surface(surf_tile_border, setcolor="#00000000", unsetcolor=None)
                    surf_tile.blit(surf_tile_border, (0, 0))
                surf_tile_color.fill(main_color)
                surf_tile_color.blit(surf_tile_main, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                surf_tile.blit(surf_tile_color, (0, 0))

                self.render_tiles_dict[angle, next_angle, main_color.normalize(),
                border_color.normalize()] = surf_tile.copy()

            if pre_tile is not None and tile.bpm != pre_tile.bpm:
                pygame.draw.circle(surf_tile, "#ff0000" if tile.bpm > pre_tile.bpm else "#0000ff",
                                   (pr * 3, pr * 3), pr * 2 / 3)
            if pre_tile is not None and tile.orbit != pre_tile.orbit:
                pygame.draw.circle(surf_tile, "#ff66ff", (pr * 3, pr * 3), pr * 2 / 3,
                                   round(pr / 5))
            new_surf_tile = pygame.transform.rotate(surf_tile, -self.camera_rotation)
            if tile.w == 0 or tile.h == 0:
                continue
            if tile.w != 100 or tile.h != 100:
                tile_scale = max(pr * 6 * tile.w / 100, 0), max(pr * 6 * tile.h / 100, 0)
                new_surf_tile = pygame.transform.scale(new_surf_tile, tile_scale)
            new_surf_tile.set_alpha(round(tile.opacity * 255 / 100))
            self.screen.blit(new_surf_tile,
                             new_surf_tile.get_rect(
                                 center=self.cnv2screen(
                                     Pt(tile.x, tile.y)
                                 )
                             )
                             )

    def render_text(self):
        text_list = [f"FPS: {self.clock.get_fps():.2f}/{self.FPS}"]
        if self.state == "SELECTING":
            text_list.append("按 Enter 键选取谱面")
        elif self.state == "CHARTING":
            text_list.append(f"Tiles: {len(self.level.tiles) - 1}")
            text_list.append("按空格键开始")
        elif self.state == "PLAYING":
            text_list.extend([f"Tiles: {self.player_tile}/{len(self.level.tiles) - 1}",
                              f"{tuple(self.cur.values())}",
                              "按 Esc 键返回",
                              f"按 F12 键{'关闭' if self.autoplay else '开启'}自动播放"])
        for i in range(len(text_list)):
            font = self.font_ascii_debug if text_list[i].isascii() else self.font_debug
            text_debug = font.render(text_list[i], True, "#ffffff")
            self.screen.blit(text_debug, (20, 20 + i * 20))

    def cnv2screen(self, pos: Pt, camera=True, screen=True) -> Pt:
        pos = pos.copy()
        if camera:
            pos -= self.camera_pos
        pos = pos.rotate(-self.camera_rotation)
        pos.x *= self.pr * 4
        pos.y *= -self.pr * 4
        if screen:
            pos += (self.width / 2, self.height / 2)
        return pos

    def on_cleanup(self):
        pygame.quit()

    def on_execute(self):
        if not self.on_init():
            self.running = False

        while self.running:
            for event in pygame.event.get():
                self.on_event(event)
            self.on_loop()
            self.on_render()
            self.clock.tick(self.FPS)
        self.on_cleanup()

    def load_level(self, path):
        self.level = Level.from_file(path)
        self.level.calc()
        pygame.mixer_music.load(os.path.join(os.path.dirname(self.level.path), self.level.song_filename))
        self.state = "CHARTING"


if __name__ == '__main__':
    app = AdoPygame()
    app.on_execute()
