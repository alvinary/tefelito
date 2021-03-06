from math import sqrt

import ursina
import ffmpeg_loader

from constants import (part_indices, 
                      sorted_part_pairs,
                      index_parts,
                      distance_triples,
                      part_distances)

BONE_THICKNESS = 4
OPENGL_SCALING = 0.001

app = ursina.Ursina()

# parameters:
#   - scale
#   - hip distance
#   - shoulder distance
#   - longification
#   - which neg, which pos

def map_coordinates(x, y, z):
    small_x = -1.0 + (2.0 * x / SCREEN_WIDTH)
    small_y = -1.0 + (2.0 * y / SCREEN_HEIGHT)
    small_z = 0.0 - (z / DEPTH_RATIO)
    return (small_x, small_y, small_z)

# Given a 3d vector v1 = (x1, y1, z1), a 2d vector v2 = (x2, y2)
# and a distance d, find a z2 such that the euclidean distance
# between v1 and (x2, y2, z2) is d.

def solve_z(v1, v2, d):
    x1, y1, z1 = v1
    x2, y2 = v2
    squared_z_difference = d ** 2 - (x1 - x2) ** 2 - (y1 - y2) ** 2
    z_difference = sqrt(abs(squared_z_difference))
    z2 = z_difference - z1
    return z2

def scalar_product(v, w):
    return sum([v_i * w_i for (v_i, w_i) in zip(v, w)])

def vector_sum(v, w):
    return tuple([v[i] + w[i] for i, _ in enumerate(zip(v, w))])

def ortho(vec, length):
    '''Return a vector orthogonal to v1 with norm 'length' '''
    vec = list(vec)
    first_component = vec.pop()
    tail_sum = -sum([v_i for v_i in vec])
    _ortho = [tail_sum] + [first_component for v_i in vec]
    scalar = (length / scalar_product(_ortho, _ortho)) ** 1/2
    _ortho = [scalar * v_i for v_i in _ortho]
    return tuple(_ortho)

def ortho_other(vec, length):
    nonzero_elements = [c for c in vec if c != 0]
    
    if len(nonzero_elements) == 0:
        return (0, 0, 0)
    
    if len(nonzero_elements) == 1 and vec[0] != 0:
        nonzero_component = nonzero_elements.pop()
        return (0, nonzero_component, 0)

    if len(nonzero_elements) == 1 and vec[0] == 0:
        nonzero_component = nonzero_elements.pop()
        return (nonzero_component, 0, 0)

    if len(nonzero_elements) >= 2:
        a, b = nonzero_elements[:2]
        return (-b*(1/(a*b)+1), a, 1/b)

def vector(x, y, z, scaling=1, translation=0):
    return ursina.Vec3(x * scaling + translation,
                       y * scaling + translation,
                       z * scaling + translation)

class Bone(ursina.Entity):

    def __init__(self, parent_pose, high_index, low_index, **kwargs):
        verts = [vector(0, 0, 0), vector(0, 0, 1)]
        tris = [(0, 1, 2), (0, 3, 2), (0, 1, 4), (1, 4, 2)]
        super().__init__(model=ursina.Mesh(vertices=verts,
                         mode='line',
                         thickness=4),
                         color=ursina.color.cyan,
                         z=0,
                         **kwargs)
        self.pose = parent_pose
        self.high_tip = high_index
        self.low_tip = low_index
        self.counter = 0
        self.scale = ursina.Vec3(4, 4, 4)
        self.x -= 0.3
        self.y -= 0.4

    def update_position(self, x1, y1, z1, x2, y2, z2):
        tip = (x2 - x1, y2 - y1, z2 - z1)
        
        _ortho1 = ortho(tip, BONE_THICKNESS)
        _ortho2 = ortho_other(_ortho1, BONE_THICKNESS)
        
        gl_vector = lambda x, y, z: vector(x, y, z,
                                           scaling=0.001,
                                           translation=-0.5)

        low_tip = (x1, y1, z1)
        high_tip = (x2, y2, z2)
        side_tip = vector_sum(low_tip, _ortho1)
        interior_tip = vector_sum(low_tip, _ortho2)
        
        low_tip = gl_vector(low_tip)
        high_tip = gl_vector(high_tip)
        side_tip = gl_vector(side_tip)
        interior_tip = gl_vector(interior_tip)
        
        verts = [low_tip, high_tip, side_tip, interior_tip]
        
        tris = [(low_tip, side_tip, interior_tip),
                (low_tip, side_tip, high_tip),
                (low_tip, interior_tip, high_tip),
                (interior_tip, side_tip, high_tip)]

        self.model = ursina.Mesh(vertices=verts,
                                 mode='line',
                                 thickness=4)
        
        self.color = ursina.color.cyan
        self.z = -1

    def update(self):
        self.counter += ursina.time.dt
        headBone = self.lowTip == 5 and self.highTip == 6

        if headBone:
            self.pose.current_frame += 1
            pose_sequence_size = len(self.pose.frames_3d)
            self.pose.current_frame %= pose_sequence_size

        if self.counter >= 0.05:
            self.counter = 0
            frame_index = self.pose.current_frame
            x1, y1, z1 = self.pose.frames_3d[frame_index][self.low_tip]
            x2, y2, z2 = self.pose.frames_3d[frame_index][self.high_tip]
            self.update_position(x1, y1, z1, x2, y2, z2)

class Pose:
    def __init__(self):

        self.bar_axes = [(6, 5), (11, 12), (6, 8), (8, 10),
                         (11, 13), (13, 15), (12, 14), (14, 16),
                         (5, 7), (7, 9), (6, 11), (5, 12)]

        self.bones = [Bone(self, i, j) for (i, j) in self.bar_axes]
        
        self.frames = []
        self.frames_3d = []

        self.current_frame = 0

        self.scale = 1
        self.hip_scale = 1
        self.shoulder_scale = 1
        self.long_scale = 1

    def frames_from_mp4(self, path, start, end):
        self.frames = ffmpeg_loader.read_video(path, start, end)
        self.frames = list(self.frames)

    def to3D(self):
        self.frames_3d = []
        for f in self.frames:
            extended_pose = self.get_3d_pose(f)
            self.frames_3d.append(extended_pose)

    def get_3d_pose(self, pose_2d):
        
        # Set up a frame with dummy values
        tridimensional_pose = [0 for i in range(17)]

        keypoint_z = {}
        keypoint_z["left shoulder"] = 0

        x1, y1, z1 = pose_2d[5][0], pose_2d[5][1], 0
        tridimensional_pose[5] = (x1, y1, z1)

        # use that z to find values
        # return a 3d frame
        # (3d frame have 17 3-tuples, one for each keypoint)

        for p1, p2 in sorted_part_pairs:
            v1 = pose_2d[part_indices[p1]]
            v2 = pose_2d[part_indices[p2]]
            x1, y1 = v1
            x2, y2 = v2
            z1 = keypoint_z[p1]
            v1_3d = (x1, y1, z1)
            z2 = solve_z(v1_3d, v2, part_distances[p1, p2])
            keypoint_z[p2] = z2
            p2_index = part_indices[p2]
            tridimensional_pose[p2_index] = (x2, y2, z2)

        return tridimensional_pose

    def apply_scalars(self):
        pass

    def estimate_scalars(self):
        pass

    def smooth_3d_frames(self):
        pass


if __name__ == '__main__':
    video_pose = Pose()
    video_pose.frames_from_mp4("./inputs/input.mp4", 0, 120)
    video_pose.to3D()
    app.run()
