from .. import FileIO
import string
from . import xmd_base
import numpy
from .. import mathhelper
import sys
import mathutils

class XMD_deformer(xmd_base.XMD_basenodeinfo):
    def __init__(self, nodeheader, fileio : FileIO.TextFileIO, closenode : bool = True):
        super().__init__(nodeheader, fileio)

        self.affectednodes : list[int] = []

        line_affectednodes = fileio.ReadLine().split()
        num_affectednodes = int(line_affectednodes[1])
        affectednodesiter = 0
        while affectednodesiter < num_affectednodes:
            self.affectednodes.append(int(line_affectednodes[affectednodesiter + 2]))
            affectednodesiter = affectednodesiter + 1
        
        self.envelope_weight = float(fileio.ReadLine().split()[1])

        if closenode: fileio.ReadLine()