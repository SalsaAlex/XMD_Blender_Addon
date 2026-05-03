from .. import FileIO
from . import xmd_bone

class XMD_joint(xmd_bone.XMD_bone):
    def __init__(self, nodeheader, fileio : FileIO.TextFileIO):
        super().__init__(nodeheader, fileio, False)

        self.segment_scale_compensate = bool(fileio.ReadLine().split()[1])
        fileio.ReadLine()