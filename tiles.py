# a tile has:
# navigation maps:
#   city, field, road
# rotation:
#   0, 1, 2, 3 <-> up right down left
# render(position) method
#

from enum import IntFlag

class Connections(IntFlag):
    none = 0
    UP = 1
    RIGHT = 2
    DOWN = 4
    LEFT = 8

import pygame
import numpy as np


flagToPoly = {
    Connections.UP: np.array([(0, 0), (1, 0), (0.5, 0.5)]).reshape((-1, 2)),
    Connections.RIGHT: np.array([(0, 1), (0, 0), (0.5, 0.5)]).reshape((-1, 2)),
    Connections.DOWN: np.array([(0, 1), (1, 1), (0.5, 0.5)]).reshape((-1, 2)),
    Connections.LEFT: np.array([(1, 0), (1, 1), (0.5, 0.5)]).reshape((-1, 2))
}

flagToLine = {
    Connections.UP: np.array([(0.5, 0), (0.5, 0.5)]).reshape((-1, 2)),
    Connections.RIGHT: np.array([(0, 0.5), (0.5, 0.5)]).reshape((-1, 2)),
    Connections.DOWN: np.array([(0.5, 1), (0.5, 0.5)]).reshape((-1, 2)),
    Connections.LEFT: np.array([(1, 0.5), (0.5, 0.5)]).reshape((-1, 2))
}

roadCol = np.array((255, 255, 255))
cityCol = np.array((255, 0, 0))
fieldCol = np.array((0, 255, 0))

class Tile:
    
    roadflags   = Connections.none
    cityflags   = Connections.none
    fieldflags  = Connections.none
    

    def __init__(self):
        self.roadflags = 2 ** np.random.randint(0, 4)
        self.cityflags = 2 ** np.random.randint(0, 4)
        self.fieldflags = ~(self.roadflags | self.cityflags)
        

    def draw(self, screen : pygame.surface, pos : np.array, size : int):

        # print(flagToPoly[Connections.UP].shape)

        for flag in Connections:
            if flag == 0: continue
            
            poly = (flagToPoly[flag] + pos) * size 
            line = (flagToLine[flag] + pos) * size

            if flag & self.fieldflags:
                pygame.draw.polygon(screen, fieldCol, poly, 0)
                # pygame.draw.line(screen, fieldCol * 0.8, line[0], line[1], size // 3)
            if flag & self.roadflags:
                pygame.draw.polygon(screen, roadCol, poly, 0)
                pygame.draw.line(screen, roadCol * 0.8, line[0], line[1], size // 3)
            if flag & self.cityflags:
                pygame.draw.polygon(screen, cityCol, poly, 0)
                pygame.draw.line(screen, cityCol * 0.8, line[0], line[1], size // 10)
            


        
