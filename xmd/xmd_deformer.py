from .. import FileIO
import string
from . import xmd_base
import numpy
from .. import mathhelper
import sys
import mathutils

#this is a abstract node type
class XMD_deformer(xmd_base.XMD_basenodeinfo):
    def __init__(self, nodetypename):
        super().__init__(nodetypename)

        self.affectednodes : list[int] = []
        self.envelope_weight : float = 1

    def from_textfile(self, nodeheader, fileio : FileIO.TextFileIO, closenode : bool = True):
        super().from_textfile(nodeheader, fileio)
        line_affectednodes = fileio.ReadLine().split()
        num_affectednodes = int(line_affectednodes[1])
        affectednodesiter = 0
        while affectednodesiter < num_affectednodes:
            self.affectednodes.append(int(line_affectednodes[affectednodesiter + 2]))
            affectednodesiter = affectednodesiter + 1
        
        self.envelope_weight = float(fileio.ReadLine().split()[1])

        if closenode: fileio.ReadLine()

    def from_blender(self, polymesh : xmd_base.XMD_basenodeinfo):
        self.affectednodes.append(polymesh.getNodeID())

    def _textfile_write(self, fileio):
        lineaffected = f"\taffected {len(self.affectednodes)} "
        for node in self.affectednodes:
            lineaffected += f"{node} "
        fileio.WriteLine(lineaffected)
        fileio.WriteLine(f"\tenvelope_weight {self.envelope_weight}")