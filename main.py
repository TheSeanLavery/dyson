#!/usr/bin/env python3
################################################################################
#                                                                              #
#   DYSON RING VISUALIZATION SYSTEM                                           #
#   --------------------------------                                           #
#                                                                              #
#   DATE:       2025-12-06                                                     #
#   VERSION:    v0.1                                                           #
#   AUTHOR:     Dave Plummer and AI Assists                                    #
#                                                                              #
#   DESCRIPTION:                                                               #
#   Render a partial Dyson ring in a 3/4 orbital view with wireframe           #
#   segments and city-light speckles.                                          #
#                                                                              #
################################################################################

import math, random, colorsys
from typing import List, Tuple
import numpy as np
import pygame

# ----------------- Config -----------------
WIDTH, HEIGHT, FPS = 1200, 900, 60
BACKGROUND = (0, 0, 0)

# Ring Geometry
N_SEGMENTS, ARC_SPAN = 12, math.radians(360)            # Fewer, wider segments; Full ring
ARC_START = math.radians(-85)                           # Gap at bottom-left (approx -135 degrees)
R_INNER, R_OUTER, SEG_HEIGHT = 4.5, 7.5, 2.5
ANGLE_SPAN = (ARC_SPAN / N_SEGMENTS) * 0.90             # Small gaps between segments

# Detail
SUBDIVISIONS, BEVEL_SIZE = 6, 0.15                      # More subdivisions for smoother curves
LIGHTS_PER_SEGMENT = 200

# Camera / View
SCALE, TILT = 52.5, math.radians(38)                    # Orthographic projection (no perspective)
INITIAL_YAW, BASE_AZIM = math.radians(42), math.radians(45)
ROT_SPEED = 2 * math.pi / 600.0

EDGE_WIDTH, STAR_RADIUS, STAR_GLOW_RADIUS = 1, 8, 30
BG_STAR_COUNT = 600

# Face rendering
FACE_EDGE_FRONT = (0, 255, 0)
FACE_EDGE_BACK = (0, 200, 255)
FACE_FILL_FRONT = (0, 255, 0, 80)
FACE_FILL_BACK = (0, 200, 255, 45)
DOUBLE_FACE_Z_OFFSET = 1e-4

def generate_bg_stars(width: int, height: int, count: int) -> List[List[float]]:
    """Generate random background stars."""
    stars = []
    for _ in range(count):
        hue = random.random()
        rgb = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
        stars.append([
            random.randint(0, width), random.randint(0, height),    # x, y
            random.uniform(0.5, 2.0), random.randint(100, 255),     # size, brightness
            (int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255))     # color
        ])
    return stars

def rotation_matrix_z(theta: float) -> np.ndarray:
    c, s = math.cos(theta), math.sin(theta)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]], dtype=float)

def rotation_matrix_x(theta: float) -> np.ndarray:
    c, s = math.cos(theta), math.sin(theta)
    return np.array([[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]], dtype=float)

def rotation_matrix_y(theta: float) -> np.ndarray:
    c, s = math.cos(theta), math.sin(theta)
    return np.array([[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]], dtype=float)

def make_curved_beveled_segment(angle_center: float, angle_span: float, r_inner: float, r_outer: float, height: float, subdivs: int = 4, bevel: float = 0.1) -> Tuple[np.ndarray, List[Tuple[int, int]], List[Tuple[List[int], List[bool]]]]:
    """Generate a curved segment (simple box cross-section). Returns: vertices, edges, faces (indices, edge_flags)"""
    half_span = angle_span * 0.5
    rs, zs = [r_inner, r_outer, r_outer, r_inner], [-height/2, -height/2, height/2, height/2]
    theta_steps = np.linspace(angle_center - half_span, angle_center + half_span, subdivs + 1)
    verts, faces_with_flags = [], []
    n_rings, points_per_ring = len(theta_steps), 4
    
    for i, theta in enumerate(theta_steps):
        c, s = math.cos(theta), math.sin(theta)
        for j in range(points_per_ring): verts.append([rs[j] * c, rs[j] * s, zs[j]])
        
        if i > 0:
            base, prev_base = i * points_per_ring, (i - 1) * points_per_ring
            for j in range(points_per_ring):
                next_j = (j + 1) % points_per_ring
                draw_flags = [True, i == n_rings - 1, True, i == 1] # Long, Ring i, Long, Ring i-1
                faces_with_flags.append(([prev_base + j, base + j, base + next_j, prev_base + next_j], draw_flags))

    # End caps: Start cap (i=0) and End cap (i=n_rings-1)
    faces_with_flags.append(([0, 1, 2, 3], [True]*4))
    last_base = (n_rings - 1) * points_per_ring
    faces_with_flags.append(([last_base+3, last_base+2, last_base+1, last_base], [True]*4))
    return np.array(verts, dtype=float), [], faces_with_flags

def sample_point_on_quad(verts: np.ndarray, face: List[int]) -> np.ndarray:
    """Sample a random point on a quad face."""
    if len(face) != 4: return verts[face[0]]
    a, b, c, d = (verts[idx] for idx in face)
    u, v = np.random.rand(2)
    return (1-u)*(1-v)*a + u*(1-v)*b + u*v*c + (1-u)*v*d

def generate_lights_for_face(verts: np.ndarray, face_indices: List[int], count: int) -> List[Tuple[np.ndarray, float, Tuple[int, int, int]]]:
    """Generate random lights on a single face."""
    lights = []
    for _ in range(count):
        pt = sample_point_on_quad(verts, face_indices)
        size = random.uniform(3.0, 8.0) if random.random() < 0.1 else random.uniform(0.15, 2.5)
        lights.append((pt, size, (random.randint(100, 200), random.randint(0, 30), random.randint(0, 30))))
    return lights

def reverse_edge_flags(edge_flags: List[bool]) -> List[bool]:
    """Re-map edge draw flags for a polygon whose winding has been reversed."""
    if len(edge_flags) <= 1: return list(edge_flags)
    return list(reversed(edge_flags[:-1])) + [edge_flags[-1]]

def draw_translucent_polygon(surface: pygame.Surface, points: List[Tuple[float, float]], color: Tuple[int, int, int, int]) -> None:
    """Draw a translucent polygon by rasterizing to a temporary alpha surface."""
    if len(points) < 3: return
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    width = max(1, int(math.ceil(max_x - min_x)) + 4)
    height = max(1, int(math.ceil(max_y - min_y)) + 4)
    offset_x = int(math.floor(min_x)) - 2
    offset_y = int(math.floor(min_y)) - 2
    poly_surface = pygame.Surface((width, height), pygame.SRCALPHA)
    offset_points = [(x - offset_x, y - offset_y) for x, y in points]
    pygame.draw.polygon(poly_surface, color, offset_points)
    surface.blit(poly_surface, (offset_x, offset_y))

def project_points(points: np.ndarray):
    """Project 3D points to 2D screen space using Orthographic projection."""
    if len(points) == 0: return np.array([]), np.array([]), np.array([]), np.array([])
    scaled = points * SCALE
    # Orthographic projection: No perspective divide, just map x, y directly to screen coordinates
    return WIDTH * 0.5 + scaled[:, 0], HEIGHT * 0.5 - scaled[:, 1], np.ones_like(scaled[:, 0], dtype=bool), np.ones_like(scaled[:, 0])

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Dyson Ring - 3/4 Orbital View")
    clock, font = pygame.time.Clock(), pygame.font.SysFont("Glass TTY VT220", 18)

    segments = [] 
    for i in range(N_SEGMENTS):
        step = ARC_SPAN / N_SEGMENTS
        v, e, f = make_curved_beveled_segment(ARC_START + step * (i + 0.5), ANGLE_SPAN, R_INNER, R_OUTER, SEG_HEIGHT, SUBDIVISIONS, BEVEL_SIZE)
        face_lights = [[] for _ in range(len(f))]
        if len(f) > 0 and LIGHTS_PER_SEGMENT > 0:
            for _ in range(LIGHTS_PER_SEGMENT):
                f_idx = random.randrange(len(f))
                face_lights[f_idx].extend(generate_lights_for_face(v, f[f_idx][0], 1))
        segments.append((v, e, f, face_lights)) 

    frame, view_pitch, view_yaw = 0, TILT, INITIAL_YAW
    dragging, last_mouse_pos = False, (0, 0)
    bg_stars = generate_bg_stars(WIDTH, HEIGHT, BG_STAR_COUNT)
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE): running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: dragging, last_mouse_pos = True, event.pos
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1: dragging = False
            elif event.type == pygame.MOUSEMOTION and dragging:
                dx, dy = event.pos[0] - last_mouse_pos[0], event.pos[1] - last_mouse_pos[1]
                last_mouse_pos = event.pos
                view_yaw += dx * 0.005; view_pitch += dy * 0.005

        screen.fill(BACKGROUND)
        
        for s in bg_stars: # Draw Background Stars
            if random.random() < 0.02: s[3] = random.randint(100, 255) # Twinkle
            b = s[3] / 255.0
            pygame.draw.circle(screen, (int(s[4][0] * b), int(s[4][1] * b), int(s[4][2] * b)), (s[0], s[1]), s[2])

        theta = frame * ROT_SPEED + BASE_AZIM
        mat = rotation_matrix_y(view_yaw) @ rotation_matrix_x(view_pitch) @ rotation_matrix_z(theta)
        
        center = (WIDTH // 2, HEIGHT // 2)
        for r in range(STAR_GLOW_RADIUS, 0, -5): # Glow
            s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 255, 255, 15), (r, r), r)
            screen.blit(s, (center[0]-r, center[1]-r))
        pygame.draw.circle(screen, (255, 255, 255), center, STAR_RADIUS)

        render_list = []
        light_draw_queue = []
        for verts_local, edges, faces_local, lights_local in segments:
            v_world = verts_local @ mat.T
            x2d, y2d, mask_v, _ = project_points(v_world)
            if len(x2d) == 0: continue
            
            for i, (face_indices, edge_flags) in enumerate(faces_local):
                if not all(mask_v[idx] for idx in face_indices): continue
                points_2d = [(x2d[idx], y2d[idx]) for idx in face_indices]
                avg_z = sum(v_world[idx][2] for idx in face_indices) / len(face_indices)
                
                proj_lights = []
                if lights_local[i]:
                    pts_world = np.array([l[0] for l in lights_local[i]]) @ mat.T
                    lx, ly, _, _ = project_points(pts_world)
                    for j in range(len(lx)): proj_lights.append((lx[j], ly[j], lights_local[i][j][1], lights_local[i][j][2]))
                
                edge_flags_front = list(edge_flags)
                render_list.append((avg_z, 'face', points_2d, FACE_EDGE_FRONT, edge_flags_front, proj_lights, False))
                back_points = list(reversed(points_2d))
                back_edge_flags = reverse_edge_flags(edge_flags_front)
                render_list.append((avg_z - DOUBLE_FACE_Z_OFFSET, 'face', back_points, FACE_EDGE_BACK, back_edge_flags, proj_lights, True))
                light_draw_queue.extend(proj_lights)

        render_list.sort(key=lambda x: x[0]) # Sort by depth
        
        for _, type_, points, edge_color, edge_flags, lights, is_back in render_list:
            if type_ == 'face':
                fill_color = FACE_FILL_BACK if is_back else FACE_FILL_FRONT
                draw_translucent_polygon(screen, points, fill_color)
                edge_count = min(len(points), len(edge_flags))
                for k in range(edge_count):
                    if edge_flags[k]: pygame.draw.line(screen, edge_color, points[k], points[(k + 1) % len(points)], 1)

        for lx, ly, lsize, lcolor in light_draw_queue:
            pygame.draw.circle(screen, lcolor, (int(lx), int(ly)), max(1, int(lsize)))

        info_text = [f"Rot X (Pitch): {math.degrees(view_pitch):.1f}°", f"Rot Y (Yaw):   {math.degrees(view_yaw):.1f}°", f"Rot Z (Spin):  {math.degrees(theta):.1f}°"]
        for i, line in enumerate(info_text): screen.blit(font.render(line, True, (0, 255, 255)), (10, 10 + i * 20))

        pygame.display.flip()
        frame += 1
        clock.tick(FPS)
    pygame.quit()

if __name__ == "__main__":
    main()
