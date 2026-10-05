from .. import FileIO
from . import xmd_bone
from . import xmd_base

import bpy

class XMD_joint(xmd_bone.XMD_bone):
    def __init__(self):
        super().__init__("JOINT")

        self.segment_scale_compensate = False

    def from_textfile(self, nodeheader, fileio : FileIO.TextFileIO):
        super().from_textfile(nodeheader, fileio, False)
        self.segment_scale_compensate = bool(fileio.ReadLine().split()[1])
        fileio.ReadLine()

    def from_blender(self, 
                     parent : xmd_base.XMD_basenodeinfo, 
                     childs : list[xmd_base.XMD_basenodeinfo], 
                     blenderbone : bpy.types.Bone, 
                     polymeshnode : xmd_base.XMD_basenodeinfo):
        super().from_blender(parent, childs, blenderbone, polymeshnode, True)

    def _textfile_write(self, fileio : FileIO.TextFileIO):
        super()._textfile_write(fileio)
        fileio.WriteLine(f"\tsegment_scale_compensate {int(self.segment_scale_compensate)}")