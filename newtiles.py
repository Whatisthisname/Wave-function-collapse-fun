from email.mime import image
from queue import Queue
from turtle import right, width
from typing import List
import numpy as np
import pygame


class Tile:
    sidePatterns : List = []

    def __init__(self, sidePatterns : List, **kws) -> None:
        for i in range(len(sidePatterns)):
            # check if side has length attribute
            # print("dab")
            if not hasattr(sidePatterns[i], '__len__'):
                sidePatterns[i] = [sidePatterns[i]]
        self.sidePatterns = sidePatterns
    
    def draw(self, screen : pygame.surface, coords : np.array, size : int) -> None:

        dirs = [np.array([0, -1]), np.array([1, 0]), np.array([0, 1]), np.array([-1, 0])]
        centerPos : np.array = (coords + np.ones(2)*0.5) * size

        for i, side in enumerate(self.sidePatterns):
            
            sideusage = 1 # in [0, 1]

            length = size * sideusage / len(side)
            lineDir = length * dirs[(i+1) % 4]
            lineWidth = size/5
            
            startPos = centerPos + dirs[i] * (size/2 - lineWidth/2) + dirs[(i-1)%4] * (size*sideusage/2)

            if i >= 2: # because we want to read from left to right and top to bottom
                side = reversed(side)

            for j, char in enumerate(side):
                col = (35 * hash(char)) % 128 + 127
                start = startPos + lineDir * j
                end = startPos + lineDir * (j+1)
                pygame.draw.line(screen, (np.cumsum(np.ones(3)*col)) % 256, start, end, int(lineWidth))

    def OnRotated(self) -> None:
        """override to make mutable state such as images rotate along"""
        pass

    def copy(self) -> 'Tile':
        return Tile(self.sidePatterns)

    def rot90(tile : "Tile") -> "Tile":
        tile.sidePatterns = [tile.sidePatterns[-1]] + tile.sidePatterns[:-1]
        tile.OnRotated()
        return tile


class ImageTile (Tile):

    image : pygame.surface

    def __init__(self, sidePatterns : List, image_surface : pygame.surface) -> None:
        super().__init__(sidePatterns)
        self.image = image_surface

    def draw(self, screen : pygame.surface, pos : np.array, size : int) -> None:
        screen.blit(pygame.transform.smoothscale(self.image, (size, size)), (pos[0] * size, pos[1] * size))

    def OnRotated(self) -> None:
        self.image = pygame.transform.rotate(self.image, -90)

    def copy(self) -> 'ImageTile':
        return ImageTile(self.sidePatterns, self.image.copy())


class TileCollection:

    tiles : List[Tile] = []

    def __init__(self, tiles : List[Tile]) -> None:
        self.tiles = tiles

    def draw(self, screen : pygame.surface, coords : np.array, size : int) -> None:
        grid = np.ceil(np.sqrt(len(self.tiles)))

        startPos = coords * size
        down = np.array([0, 1])
        right = np.array([1, 0])
        for i, tile in enumerate(self.tiles):
            _coords = coords * grid + down * (i // grid) + right * (i % grid)
            tile.draw(screen, _coords, size / grid)
        

class Manifold:

    collections : List[TileCollection] = []
    width, height = 0, 0

    def finished(self) -> bool:
        answer = True
        for collection in self.collections:
            if len(collection.tiles) > 1:
                answer = False
                break
        return answer

    def __init__(self, width, height) -> None:
        self.width, self.height = width, height

    @staticmethod
    def collapseRandom(manifold : "Manifold") -> "Manifold":
        
        if manifold.finished():
            print("Manifold is finished, no more collapses possible")
            return manifold


        # make shuffled index to iterate over so we collapse at a random place
        rand_index = list(range(len(manifold.collections)))
        np.random.shuffle(rand_index)

        # find complex with fewest possibilities greater than 1
        minAmount = 999999
        minIndex = 0
        for i in rand_index:
            tileAmount = len(manifold.collections[i].tiles)
            if tileAmount > 1 and len(manifold.collections[i].tiles) < minAmount:
                minIndex = i
                minAmount = tileAmount

        choice : TileCollection = manifold.collections[minIndex]
        
        choice.tiles = [choice.tiles[np.random.randint(len(choice.tiles))]]


        # print("--- collapsed index", minIndex, "---")

        # propagate the changes
        
        manifold = Manifold.Propagate(manifold, minIndex)

        return manifold


    @staticmethod
    def eliminateTiles(ourOptions : TileCollection, sideIdx : int, theirOptions : TileCollection) -> bool:
        """Takes in the changed tile `ourOptions`, the `sideIdx` of `ourOptions` that we are comparing compatibility along, and the `otherOptions`.
        
        Will return `True` if at least one tile was eliminated from `otherOptions`."""
        
        to_be_removed = np.zeros(len(theirOptions.tiles), dtype=bool)
        
        towardsOtherSideIdx = (sideIdx+2)%4
        # print("side:", sideIdx, "ourSideIdx:", sideIdx)
        # if any of their tiles don't fit ours, we will remove it from their set.
        for i, theirTile in enumerate(theirOptions.tiles):
            
            theirs_fits = False
            for ourTile in ourOptions.tiles:
                ourSide = ourTile.sidePatterns[sideIdx]
                
                theirSide = theirTile.sidePatterns[towardsOtherSideIdx]
                if ourSide == theirSide:
                    # print("our pattern:", ourSide, "compared to their pattern:", theirSide, "matching:", ourSide == theirSide)
                    theirs_fits = True
                    break

            if not theirs_fits:
                # mark their tile for removal
                to_be_removed[i] = True
            
        # remove the marked tiles
        theirOptions.tiles = [tile for i, tile in enumerate(theirOptions.tiles) if not to_be_removed[i]]
        
        # if we removed some, propagate the changes later
        # print("remove:", to_be_removed.astype(int).tolist())
        return to_be_removed.any()
                    


    @staticmethod
    def Propagate(manifold : "Manifold", index : int) -> "Manifold":
        """Given a `Manifold` and an index into a `TileCollection`, will ensure that all neighbouring `TileCollection`s are compatible with the change at the given index, by reducing their possible states."""
        
        # print("Propagated to", index)

        ourOptions = manifold.collections[index]
        changeList : List[TileCollection] = []

        # print("check left")
        # check left
        if (index % manifold.width) > 0:
            leftOptions = manifold.collections[index - 1]
            
            if len(leftOptions.tiles) <= 1: 
                pass
            elif Manifold.eliminateTiles(ourOptions, 3, leftOptions):
                    changeList.append(index - 1)
                
        # print("check right")
        # check right
        if (index % manifold.width) < manifold.width - 1:
            rightOptions = manifold.collections[index + 1]
            
            if len(rightOptions.tiles) <= 1:
                pass
            elif Manifold.eliminateTiles(ourOptions, 1, rightOptions):
                changeList.append(index + 1)
        
        # print("check above")
        # check above
        if index >= manifold.width:
            aboveOptions = manifold.collections[index - manifold.width]
            
            if len(aboveOptions.tiles) <= 1:
                pass
            elif Manifold.eliminateTiles(ourOptions, 0, aboveOptions):
                changeList.append(index - manifold.width)

        # print("check below")
        # check below
        if index < manifold.width * (manifold.height - 1):
            belowOptions = manifold.collections[index + manifold.width]
            
            if len(belowOptions.tiles) <= 1:
                pass
            elif Manifold.eliminateTiles(ourOptions, 2, belowOptions):
                changeList.append(index + manifold.width)


        # recursive call to propagate if necessary
        # print(f"changeList from {index}:", changeList)

        for tileCollection in changeList:
            manifold = Manifold.Propagate(manifold, tileCollection)


        return manifold
        