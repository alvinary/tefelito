import pyglet

HEIGHT_2D = 700
WIDTH_2D = 700

class Environment2D:
    def __init__(self):
        self.window = pyglet.window.Window(WIDTH_2D, HEIGHT_2D)
        self.bones_batch = pyglet.graphics.Batch()

    def set_pose(self):
        pass

    def run(self):
        pass

class Bone2D:
    def __init__(self, owner_batch):
        self.line = pyglet.shapes.Line(0, 0, 0, 0, 
                                       color=(255,255,255),
                                       width=1, batch=owner_batch)

    def update_position(self, _x, _y, _x2, _y2):
        self.line.x, self.line.y, self.line.x2, self.line.y2 = _x, 700 - _y, _x2, 700 - _y2