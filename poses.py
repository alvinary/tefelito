from math import sqrt
import ursina
import ffmpeg_loader

BONE_THICKNESS = 4

# Pairs of body part names and indices
parts = '''
nose : 0
left eye : 1
right eye : 2
left ear : 3
right ear : 4
left shoulder : 5
right shoulder : 6
left elbow : 7
right elbow : 8
left wrist : 9
right wrist : 10
left hip : 11
right hip : 12
left knee : 13
right knee : 14
left ankle : 15
right ankle : 16
'''.strip()

# Reference distances between body parts
distances = '''
left hip : right hip : 36
left shoulder : right shoulder : 42
right shoulder : right elbow : 31
right elbow : right writs : 28
right shoulder : right hip : 42
right hip : right knee : 42
right knee : right ankle : 42
left shoulder : left elbow : 31
left elbow : left wrist : 28
left shoulder : left hip : 42
left hip : left knee : 42
left knee : left ankle : 42
'''.strip()

distance_triples = [l for l in distances.split("\n")]
distance_triples = [l.split(":") for l in distance_triples]
distance_triples = [[e.strip() for e in l] for l in distance_triples]
distance_triples = [tuple(l) for l in distance_triples]
distance_triples = [(p1, p2, int(d)) for p1, p2, d in distance_triples]

part_distances = {}
for p1, p2, d in distance_triples:
    part_distances[p1, p2] = d

# Pairs of connected body parts, sorted so that the first 
# body part in  every pair has a well-defined coordinate 
# in the z axis, provided one sets an arbitrary z-axis
# value for the left shoulder to begin with, and assigns 
# a value to the z-axis of the second component of each
# pair in order using get_z, starting from the first pair

sorted_part_pairs = '''
left shoulder, right shoulder
left shoulder, left hip
left shoulder, left elbow
left elbow, left wrist
left hip, left knee
left knee, left ankle
right shoulder, right hip
right shoulder, right elbow
right elbow, right wrist
right hip, right knee
right knee, right ankle
left hip, right hip
'''.strip()

sorted_part_pairs = sorted_part_pairs.split("\n")
sorted_part_pairs = [l.split(",") for l in sorted_part_pairs]
sorted_part_pairs = [tuple(p) for p in sorted_part_pairs]
sorted_part_pairs = [(s1.strip(), s2.strip()) for (s1, s2) in sorted_part_pairs]

# Map body part names to keypoint indices
part_indices = parts.split("\n")
part_indices = [tuple(s.split(":")) for s in part_indices]
part_indices = [(s1.strip(), s2.strip()) for (s1, s2) in part_indices]
part_indices = [(s1, int(s2)) for (s1, s2) in part_indices]
part_indices = dict(part_indices)

# Map keypoint indices to body part names
index_parts = {}
for k, v in part_indices.items():
    index_parts[v] = k

sorted_pair_parts = []
part_pair_distances = []

# parameters:
#   - scale
#   - hip distance
#   - shoulder distance
#   - longification
#   - which neg, which pos

# Given a 3d vector v1 = (x1, y1, z1), a 2d vector v2 = (x2, y2)
# and a distance d, find a z2 such that the euclidean distance
# between v1 and (x2, y2, z2) is d.

def solve_z(v1, v2, d):
    x1, y1, z1 = v1
    x2, y2 = v2
    z_diff = sqrt(d ** 2 - (x1 - x2) ** 2 - (y1 - y2) ** 2)
    z2 = z_diff - z1
    # How about returning just abs?
    return (z2, -z2)

def dot(v, w):
    return sum([v_i * w_i for (v_i, w_i) in zip(v, w)])

def _sum(v,w):
    return tuple([v[i] + w[i] for i, _ in enumerate(zip(v, w))])

def ortho(vec, length):
    '''Return a vector orthogonal to v1 with norm 'length' '''
    first_component = vec.pop()
    tail_sum = -sum([v_i for v_i in vec])
    _ortho = [tail_sum] + [first_component for v_i in vec]
    scalar = (length / dot(_ortho, _ortho)) ** 1/2
    _ortho = [scalar * v_i for v_i in vec]
    return tuple(_ortho)

def ortho_other(vec, length):
    a, b = vec[0], vec[1]
    return (-b*(1/(a*b)+1), a, 1/b)

class Bone(ursina.Entity):
    def __init__(self, parentPose, highIndex, lowIndex, **kwargs):
        verts = [(0, 0, 0), (0, 0, 1),
                 (0, 0, 1), (1, 0, 0),
                 (0, 1, 1), (1, 0, 1),
                 (1, 1, 0), (1, 1, 1)]
        tris = [(0, 1, 2), (0, 3, 2), (0, 1, 4), (1, 4, 2)]
        super().__init__(model=ursina.Mesh(vertices=verts, triangles=tris,
                        mode='line', thickness=4),
                        color=ursina.color.cyan, z=-1, **kwargs)
        self.pose = parentPose
        self.highTip = highIndex
        self.lowTip = lowIndex

    def update_position(self, x1, y1, z1, x2, y2, z2):
        tip = (x2 - x1, y2 - y1, z2 - z1)
        _ortho1 = ortho(tip, BONE_THICKNESS)
        _ortho2 = ortho_other(_ortho1, BONE_THICKNESS)
        low_tip = (x1, y1, z1)
        high_tip = (x2, y2, z2)
        side_tip = _sum(low_tip, _ortho1)
        interior_tip = _sum(low_tip, _ortho2)
        verts = [low_tip, high_tip, side_tip, interior_tip]
        tris = [(low_tip, side_tip, interior_tip),
                (low_tip, side_tip, high_tip),
                (low_tip, interior_tip, high_tip),
                (interior_tip, side_tip, high_tip)]
        self.model = ursina.Mesh(vertices=verts, triangles=tris,
                                 mode='line', thickness=4)
        self.color = ursina.color.cyan
        self.z=-1

    def update(self):
        self.counter += ursina.time.dt
        headBone = self.lowTip == 5 and self.highTip == 6
        if headBone:
            self.pose.currentIndex += 1
            poseSize = len(self.pose.frames_3d)
            self.pose.currentIndex %= poseSize
        if self.counter >= 0.05:
            self.counter = 0
            frameIndex = self.pose.current_frame
            x1, y1, z1 = self.pose.frames_3d[frameIndex][self.lowTip]
            x2, y2, z2 = self.pose.frames_3d[frameIndex][self.highTip]
            self.update_position(x1, y1, z1, x2, y2, z2)

class Pose:
    def __init__(self):

        self.bar_axes = [(5, 6), (11, 12), (5, 7),
                         (7, 9), (6, 8), (8, 10),
                         (12, 14), (14, 16), (11, 13),
                         (13, 15), (5, 11), (6, 12),
                         (3, 4), (3, 5), (4, 6)]

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

    def on_key_press(self, symbol, modifiers):
        self.current_frame += 1
        self.update_bones(self.frames[self.current_frame])

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
    video_pose.frames_from_mp4("./inputs/input.mp4", 0, 12)
    video_pose.to3D()
    ursina.app.run()
