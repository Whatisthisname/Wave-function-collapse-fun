import ast
from distutils.dir_util import copy_tree
import os
from typing import Any, Dict, List
import numpy as np
import pygame
import pandas as pd
import json


class Tile:

    id : str = ""

    sidePatterns : List = []

    graph : "TileGraph"
    graphRule = None
    attrDict : Dict[str, Any] = {}

    def __init__(self, sidePatterns : List, **kws) -> None:
        for i in range(len(sidePatterns)):
            # check if side has length attribute
            # print("dab")
            if not hasattr(sidePatterns[i], '__len__'):
                sidePatterns[i] = [sidePatterns[i]]
        self.sidePatterns = sidePatterns
    
    def draw(self, screen : pygame.surface, coords : np.array, size : int) -> None:
        "default draw method, draws the side patterns"
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

    def draw_attrs(self, screen : pygame.surface, coords : np.array, size : int) -> None:

        text = str.replace(self.attrDict.__str__(), ",", "\n")
        text = self.attrDict.__str__()
        my_font = pygame.font.SysFont('Comic Sans MS', 30)
        text_surface = my_font.render(text, True, (0, 0, 0))
        screen.blit(text_surface, (coords[0] * size, coords[1] * size))

    def OnRotated(self) -> None:
        """override to make mutable state such as images rotate along"""
        pass

    def copy(self) -> 'Tile':
        newtile = Tile(self.sidePatterns.copy())
        newtile.id = self.id
        newtile.attrDict = self.attrDict.copy()
        return newtile

    def rot90(tile : "Tile") -> "Tile":
        tile.sidePatterns = [tile.sidePatterns[-1]] + tile.sidePatterns[:-1]
        tile.OnRotated()
        return tile



    @staticmethod
    def dataToTiles(dataRow : pd.Series, tileFolderPath : str = "") -> List["Tile"]:
        "Takes a row from a data.csv and an image folder, and returns a list of the rotated tiles, with the attributes of the data"
        if int(dataRow["amount"]) == 0: return []

        pattern = list(dataRow["pattern"])
        surface = pygame.image.load(os.path.join(tileFolderPath, dataRow['name'])).convert_alpha()   
        rotations = str(dataRow["rotations"])
        attributes : Dict = ast.literal_eval(dataRow["attributes"])
        id = ".".join(dataRow['name'].split(".")[:-1]) # the name without the file extension
        
        if rotations is None or rotations == "": # auto rotate all and remove versions that are the same
            tile : ImageTile = ImageTile(pattern, surface)
            output : List[Tile] = [tile, tile.copy().rot90(), tile.copy().rot90().rot90(), tile.copy().rot90().rot90().rot90()]
            to_be_removed = [False] * 4
            for t1 in range(4):
                if to_be_removed[t1]: continue

                for t2 in range(t1+1, 4):
                    to_be_removed[t2] |= output[t1].sidePatterns == output[t2].sidePatterns 
            
            output = [output[i] for i in range(4) if not to_be_removed[i]]

        else:
            output = []
            for rot in rotations:
                newtile = ImageTile(pattern,surface)
                for num in range(int(rot)):
                    newtile.rot90()
                output.append(newtile)
                

        for tile in output:
            tile.id = id
            tile.attrDict = attributes.copy()

        return output

class ImageTile (Tile):

    image : pygame.Surface
    imageRotation : int = 0

    def __init__(self, sidePatterns : List, image_surface : pygame.Surface) -> None:
        super().__init__(sidePatterns)
        self.image = image_surface
        self.imageRotation = 0

    def draw(self, screen : pygame.Surface, pos : np.array, size : int) -> None:
        screen.blit(pygame.transform.rotate(pygame.transform.smoothscale(self.image, (size, size)), -90 * self.imageRotation), (pos[0] * size, pos[1] * size))

    def OnRotated(self) -> None:
        self.imageRotation = (self.imageRotation + 1 ) % 4

    def copy(self) -> 'ImageTile':
        newtile = ImageTile(self.sidePatterns.copy(), self.image)
        newtile.imageRotation = self.imageRotation
        newtile.id = self.id
        newtile.attrDict = self.attrDict.copy()
        return newtile


class TileCollection:

    tiles : List[Tile] = []

    def __init__(self, tiles : List[Tile]) -> None:
        self.tiles = tiles

    def draw(self, screen : pygame.Surface, coords : np.array, size : int) -> None:
        grid = np.ceil(np.sqrt(len(self.tiles)))

        startPos = coords * size
        down = np.array([0, 1])
        right = np.array([1, 0])
        for i, tile in enumerate(self.tiles):
            _coords = coords * grid + down * (i // grid) + right * (i % grid)
            tile.draw(screen, _coords, size / grid)
        if len(self.tiles) == 0:
            topleft = coords * size
            right = np.array([1, 0]) * size
            down = np.array([0, 1]) * size
            pygame.draw.line(screen, (255, 0, 0), topleft, topleft + right + down, width=int(size/30) )
            pygame.draw.line(screen, (255, 0, 0), topleft+down, topleft + right, width=int(size/30) )

    def draw_attrs(self, screen : pygame.Surface, coords: np.array, size : int) -> None:
        if self.tiles.__len__() != 1 and False:
            return
        elif False:
            # startPos = coords * size
            # down = np.array([0, 1])
            # right = np.array([1, 0])
            self.tiles[0].draw_attrs(screen, coords, size)
        else:
            text = [x.attrDict.__str__() for x in self.tiles]
            fontsize = 10
            my_font = pygame.font.SysFont('Comic Sans MS', fontsize)
            for i, line in enumerate(text):
                text_surface = my_font.render(line, True, (0, 0, 0))
                screen.blit(text_surface, (coords[0] * size, coords[1] * size + i * fontsize))
        

class TileGraph:
    checkPoints : List[TileCollection] = []
    "A List of the points that should be updated whenever something changes"



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

    def __init__(self, height, width) -> None:
        self.width, self.height = width, height


    @staticmethod
    def PropagateAll(manifold : "Manifold") -> "Manifold":
        for x in range(manifold.width):
            for y in range(manifold.height):
                manifold = manifold.Propagate(manifold, y * manifold.width + x)
        return manifold

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
        # if any of their tiles don't fit ours, we will remove it from their set.
        for i, theirTile in enumerate(theirOptions.tiles):
            
            theirs_fits = False
            for ourTile in ourOptions.tiles:
                ourSide = ourTile.sidePatterns[sideIdx]
                

                # compare side-patterns
                theirSide = theirTile.sidePatterns[towardsOtherSideIdx]
                sidePatternFits = ourSide == theirSide
                if not sidePatternFits: continue

                # check custom rule if we have it
                ourColor = ourTile.attrDict.get("color")
                if ourColor is not None:
                    if ourColor[1] not in ourSide:
                        theirs_fits = True
                        break
                    else:
                        theirColor = theirTile.attrDict.get("color")
                        if theirColor is not None:
                            if theirColor[2] == ourColor[2]:
                                theirs_fits = True
                                break
                            else: continue
                        else: # if theirColor is None
                            theirTile.attrDict["color"] = ourColor
                            theirs_fits = True
                            break
                else:
                    theirs_fits = True
                    break

            if not theirs_fits:
                # mark their tile for removal
                to_be_removed[i] = True


        # # invoke custom tile elimination rule
        # if ourTile.customRule is not None:
        #     ourTile.customRule(their)
            
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

        # check left
        if (index % manifold.width) > 0:
            leftOptions = manifold.collections[index - 1]
            
            # if len(leftOptions.tiles) <= 1: 
            #     pass
            if Manifold.eliminateTiles(ourOptions, 3, leftOptions):
                    changeList.append(index - 1)
                
        # check right
        if (index % manifold.width) < manifold.width - 1:
            rightOptions = manifold.collections[index + 1]
            
            # if len(rightOptions.tiles) <= 1:
            #     pass
            if Manifold.eliminateTiles(ourOptions, 1, rightOptions):
                changeList.append(index + 1)
        
        # check above
        if index >= manifold.width:
            aboveOptions = manifold.collections[index - manifold.width]
            
            # if len(aboveOptions.tiles) <= 1:
            #     pass
            if Manifold.eliminateTiles(ourOptions, 0, aboveOptions):
                changeList.append(index - manifold.width)

        # check below
        if index < manifold.width * (manifold.height - 1):
            belowOptions = manifold.collections[index + manifold.width]
            
            # if len(belowOptions.tiles) <= 1:
            #     pass
            if Manifold.eliminateTiles(ourOptions, 2, belowOptions):
                changeList.append(index + manifold.width)


        # check dependencies

        # recursive call to propagate if necessary
        # print(f"changeList from {index}:", changeList)

        for tileCollection in changeList:
            manifold = Manifold.Propagate(manifold, tileCollection)


        return manifold

class TileSetupFile:

    manifold : Manifold
    width, height = 0, 0
    alltiles = List[Tile]

    mapIdx : int
    tileDict : Dict[str, Tile]
    fileLines : List[str]

    tileDataFrame : pd.DataFrame
    tileDataFolder : str

    @staticmethod
    def read_tsf(filepath : str) -> "TileSetupFile":

        with (open(filepath) as f):
            
            # construct dictionairy
            tileDict : Dict[str, Tile] = {}
            fileLines = f.readlines()

            tileDataFolder = fileLines[0].split(":")[1].strip()
            tileDataName = fileLines[1].split(":")[1].strip()
            tileDataFrame = pd.read_csv(os.path.join(tileDataFolder, tileDataName) , header=0, dtype=str, sep="\t")
            

            assert(fileLines[2]=="\n")
            
            # scroll past tiledict definitions
            for i in range(3, len(fileLines)):
                if fileLines[i] == "\n": break

            assert(fileLines[i]=="\n")
            i += 1

            # read board size:
            height, width = fileLines[i].split("x")
            height, width = int(height), int(width)
            i+=1


            tsf : "TileSetupFile" = TileSetupFile()
            tsf.mapIdx = i
            tsf.tileDict = tileDict
            tsf.manifold = None
            tsf.width = width
            tsf.height = height
            tsf.alltiles = []
            tsf.fileLines = fileLines
            tsf.tileDataFrame = tileDataFrame
            tsf.tileDataFolder = tileDataFolder
            return tsf

    def construct_manifold(self) -> Manifold:
        # make all tiles
        alltiles : List[Tile] = []
        for row in range(len(self.tileDataFrame)):    
            alltiles.extend(Tile.dataToTiles(self.tileDataFrame.iloc[row], self.tileDataFolder))

        # make manifold with full entropy
        manifold : "Manifold" = Manifold(self.height, self.width)
        for y in range(self.height):
            for x in range(self.width):
                manifold.collections.append(TileCollection([tile.copy() for tile in alltiles]))

        # make tileDict
        for i in range(3, len(self.fileLines)):
            if self.fileLines[i] == "\n": break
            
            # parse declaration of the form "[key:name rotation]"
            key, description = self.fileLines[i].split(":")
            name, rotation = description.split(" ")

            foundReference = False
            for j, row in self.tileDataFrame.iterrows():
                if "".join(str(row["name"]).split(".")[:-1]) == name:
                    foundReference = True
                    dataRow = row.copy(deep = True)
                    dataRow["rotation"] = rotation
                    self.tileDict[key] = Tile.dataToTiles(dataRow, self.tileDataFolder)[0]
                    break
            if not foundReference:
                    print("Could not find the reference of line " + f"'{line}'. Skipped it.")

        # reduce entropy as in startfile
        for y, line in enumerate(self.fileLines[self.mapIdx:self.mapIdx+self.height]):
            line = line.replace("\n", "")[:self.width]
            for x, charKey in enumerate(line):
                if charKey == " ": continue
                # print(f"({x},{y}), line:{line}")
                manifold.collections[y * self.width + x] = TileCollection([self.tileDict[charKey].copy()])

        self.manifold = manifold
        return manifold