from .. import FileIO
import string
from . import xmd_base
import numpy
from .. import mathhelper
import sys
import mathutils

import bmesh

#this is a abstract node type
class XMD_geometry(xmd_base.XMD_basenodeinfo):
    def __init__(self, nodetypename):
        super().__init__(nodetypename)

        self.points : list[mathutils.Vector] = []
        self.deformerqueue : list[int] = []
        self.isintermediateobj = False

    def from_textfile(self, nodeheader, fileio : FileIO.TextFileIO, closenode : bool = True):
        super().from_textfile(nodeheader, fileio)

        num_points = int(fileio.ReadLine().split()[1])
        self.points : list[mathutils.Vector] = []

        pointiter = 0
        while pointiter < num_points:
            self.points.append(mathhelper.Vec3FromStrList(fileio.ReadLine().split()))
            pointiter += 1
        
        temp_deformerqueue_line = fileio.ReadLine().split()
        self.deformerqueue : list[int] = []
        deformerqueueiter = 0
        while deformerqueueiter < int(temp_deformerqueue_line[1]):
            self.deformerqueue.append(temp_deformerqueue_line[deformerqueueiter + 2])
            deformerqueueiter += 1
        
        self.isintermediateobj = bool(fileio.ReadLine().split()[1])

        if closenode: fileio.ReadLine()

    def from_blender(self, readablemesh : bmesh.types.BMesh, deformers : list[xmd_base.XMD_basenodeinfo]):
        for vert in readablemesh.verts:
            self.points.append(vert.co)
        for deformer in deformers:
            self.deformerqueue.append(deformer.getNodeID())
        

    def _textfile_write(self, fileio : FileIO.TextFileIO):
        fileio.WriteLine(f"\tpoints {len(self.points)}")
        for point in self.points:
            fileio.WriteLine(f"\t\t{point.x} {point.y} {point.z}")
        deformerqueueline = f"\tdeformer_queue {len(self.deformerqueue)}"
        for deformerqueue in self.deformerqueue:
            deformerqueueline += f" {deformerqueue}"
        fileio.WriteLine(deformerqueueline)
        fileio.WriteLine(f"\tintermediate_object {int(self.isintermediateobj)}")