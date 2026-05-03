from .. import FileIO
from . import xmd_deformer

class weightinfoentry:
    def __init__(self, jointid : int, weight : float):
        self.jointid = jointid
        self.weightval = weight

class skin_vertweights:

    def __init__(self, fileio : FileIO.TextFileIO, pointindex : int):
        self.weightlist : list[weightinfoentry] = []
        self.pointindex = pointindex

        line = fileio.ReadLine().split()
        numweights = int(line[0])
        weightiter = 1
        while weightiter < (numweights * 2):
            self.weightlist.append(weightinfoentry(int(line[weightiter]), float(line[weightiter + 1])))
            weightiter = weightiter + 2


class XMD_skin(xmd_deformer.XMD_deformer):
    def __init__(self, nodeheader, fileio : FileIO.TextFileIO):
        super().__init__(nodeheader, fileio, False)

        self.influences : list[int] = []
        self.vertweights : list[skin_vertweights] = []

        num_influences = int(fileio.ReadLine().split()[1])
        influencelist = fileio.ReadLine().split()
        for influence in influencelist:
            self.influences.append(int(influence))
        
        num_points = int(fileio.ReadLine().split()[1])
        assert fileio.ReadLine().split()[0].count('weights') is 1
        weightiter = 0
        while weightiter < num_points:
            self.vertweights.append(skin_vertweights(fileio, weightiter))
            weightiter = weightiter + 1
        
        fileio.ReadLine()