from .. import FileIO
import string
from . import xmd_base
import numpy
from .. import mathhelper
import sys
import mathutils

def Vec2_from_limits(strlist : list[str]):
    returnvec = mathutils.Vector([sys.float_info.min, sys.float_info.max])
    if strlist[1].find("INF") == -1:
        returnvec.x = float(strlist[1])
    if strlist[2].find("INF") == -1:
        returnvec.y = float(strlist[2])
    return returnvec


class XMD_bone(xmd_base.XMD_basenodeinfo):
    def __init__(self, nodeheader, fileio : FileIO.TextFileIO, closenode : bool = True):
        super().__init__(nodeheader, fileio)

        debugvar = fileio.ReadLine()
        self.visible = bool(debugvar.split()[1])
        self.scale_pivot            =       mathhelper.Vec3FromStrList(fileio.ReadLine().split()[1:])
        self.rotate_pivot           =       mathhelper.Vec3FromStrList(fileio.ReadLine().split()[1:])
        self.min_bound              =       mathhelper.Vec3FromStrList(fileio.ReadLine().split()[1:])
        self.max_bound              =       mathhelper.Vec3FromStrList(fileio.ReadLine().split()[1:])
        self.scale                  =       mathhelper.Vec3FromStrList(fileio.ReadLine().split()[1:])
        self.translate              =       mathhelper.Vec3FromStrList(fileio.ReadLine().split()[1:])

        self.rotation_orient        =       mathhelper.Vec4FromStrList(fileio.ReadLine().split()[1:])
        self.rotation               =       mathhelper.Vec4FromStrList(fileio.ReadLine().split()[1:])
        self.joint_orient           =       mathhelper.Vec4FromStrList(fileio.ReadLine().split()[1:])


        assert fileio.ReadLine().split().count('bind_pose_matrix') == 1
        mcol1 = mathhelper.Vec4FromStrList(fileio.ReadLine().split())
        mcol2 = mathhelper.Vec4FromStrList(fileio.ReadLine().split())
        mcol3 = mathhelper.Vec4FromStrList(fileio.ReadLine().split())
        mcol4 = mathhelper.Vec4FromStrList(fileio.ReadLine().split())

        self.bind_pose_matrix       =       mathutils.Matrix([
                                                [mcol1.x, mcol1.y, mcol1.z, mcol4.x], #rot1x, rot1y, rot1z, transx
                                                [mcol2.x, mcol2.y, mcol2.z, mcol4.y], #rot2x, rot2y, rot2z, transy
                                                [mcol3.x, mcol3.y, mcol3.z, mcol4.z], #rot3x, rot3y, rot3z, transz
                                                [mcol4.x, mcol4.y, mcol4.z, mcol4.w]] #transx, transy, transz, transw
                                            )
        
        self.rotation_order         =       fileio.ReadLine().split()[1]
        self.inherits_transform     =       bool(fileio.ReadLine().split()[1])
        
        self.shearing               =       mathhelper.Vec3FromStrList(fileio.ReadLine().split()[1:])
        self.rotate_pivot_translate =       mathhelper.Vec3FromStrList(fileio.ReadLine().split()[1:])
        self.scale_pivot_translate  =       mathhelper.Vec3FromStrList(fileio.ReadLine().split()[1:])

        self.translate_limit_x      =       Vec2_from_limits(fileio.ReadLine().split())
        self.translate_limit_y      =       Vec2_from_limits(fileio.ReadLine().split())
        self.translate_limit_z      =       Vec2_from_limits(fileio.ReadLine().split())
        self.rotate_limit_x         =       Vec2_from_limits(fileio.ReadLine().split())
        self.rotate_limit_y         =       Vec2_from_limits(fileio.ReadLine().split())
        self.rotate_limit_z         =       Vec2_from_limits(fileio.ReadLine().split())
        self.scale_limit_x          =       Vec2_from_limits(fileio.ReadLine().split())
        self.scale_limit_y          =       Vec2_from_limits(fileio.ReadLine().split())
        self.scale_limit_z          =       Vec2_from_limits(fileio.ReadLine().split())

        self.parent                 =       int(fileio.ReadLine().split()[1])
        self.child_joints           =       int(fileio.ReadLine().split()[1])
        self.list_childjoints : list[int] = []
        if(self.child_joints != 0):
            for stringentry in fileio.ReadLine().split():
                self.list_childjoints.append(int(stringentry))
        

        self.world_transform = mathutils.Matrix.Identity(4) #is set up later



        #skip instance_list for now
        assert fileio.ReadLine().split()[0].count("INSTANCE_LIST") == 1
        xmd_base.skipNodeEntry(fileio)
        if closenode: fileio.ReadLine()