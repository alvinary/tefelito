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
left hip : right hip : 360
left shoulder : right shoulder : 840
right shoulder : right elbow : 620
right elbow : right wrist : 560
right shoulder : right hip : 840
right hip : right knee : 840
right knee : right ankle : 840
left shoulder : left elbow : 620
left elbow : left wrist : 560
left shoulder : left hip : 840
left hip : left knee : 840
left knee : left ankle : 840
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
