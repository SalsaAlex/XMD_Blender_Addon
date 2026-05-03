from .. import FileIO
import string
from . import xmd_base
import numpy
from .. import mathhelper
import sys
import mathutils

class XMD_geometry(xmd_base.XMD_basenodeinfo):
    def __init__(self, nodeheader, fileio : FileIO.TextFileIO, closenode : bool = True):
        super().__init__(nodeheader, fileio)

        self.num_points = int(fileio.ReadLine().split()[1])
        self.points : list[mathutils.Vector] = []

        pointiter = 0
        while pointiter < self.num_points:
            self.points.append(mathhelper.Vec3FromStrList(fileio.ReadLine().split()))
            pointiter = pointiter + 1
        
        temp_deformerqueue_line = fileio.ReadLine().split()
        self.deformerqueue : list[int] = []
        deformerqueueiter = 0
        while deformerqueueiter < int(temp_deformerqueue_line[1]):
            self.deformerqueue.append(temp_deformerqueue_line[deformerqueueiter + 2])
            deformerqueueiter = deformerqueueiter + 1
        
        self.isintermediateobj = fileio.ReadLine().split()[1]

        if closenode: fileio.ReadLine()