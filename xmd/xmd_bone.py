from .. import FileIO
import string
from . import xmd_base
import numpy
import mathutils
from .. import mathhelper
import sys
import mathutils

import bpy

def Vec2_from_limits(strlist : list[str]):
    returnvec = mathutils.Vector([sys.float_info.min, sys.float_info.max])
    if strlist[1].find("INF") == -1:
        returnvec.x = float(strlist[1])
    if strlist[2].find("INF") == -1:
        returnvec.y = float(strlist[2])
    return returnvec

def BoundsFromPoints(pointlist : mathutils.Vector):
    mins = mathutils.Vector([99999, 99999, 99999])
    maxs = mathutils.Vector([-99999, -99999, -99999])
    for point in pointlist:
        if point.x < mins.x: mins.x = point.x
        if point.y < mins.y: mins.y = point.y
        if point.z < mins.z: mins.z = point.z

        if point.x > maxs.x: maxs.x = point.x
        if point.y > maxs.y: maxs.y = point.y
        if point.z > maxs.z: maxs.z = point.z
    
    return mins, maxs


def BoundsFromBone(bone : bpy.types.Bone):
    return BoundsFromPoints([bone.head, bone.tail])


class XMD_bone(xmd_base.XMD_basenodeinfo):
    def __init__(self, nodetypename = "BONE"):
        super().__init__(nodetypename)

        self.visible = True
        self.scale_pivot = mathutils.Vector([0, 0, 0])
        self.rotate_pivot = mathutils.Vector([0, 0, 0])
        self.min_bound = mathutils.Vector([0, 0, 0])
        self.max_bound = mathutils.Vector([0, 0, 0])
        self.scale = mathutils.Vector([1, 1, 1])
        self.translate = mathutils.Vector([0, 0, 0])

        self.rotation_orient = mathutils.Quaternion([1, 0, 0, 0])
        self.rotation = mathutils.Quaternion([1, 0, 0, 0])
        self.joint_orient = mathutils.Quaternion([1, 0, 0, 0])

        self.bind_pose_matrix = mathutils.Matrix.Identity(4)

        self.rotation_order = "xyz"
        self.inherits_transform = True
        
        self.shearing = mathutils.Vector([0, 0, 0])
        self.rotate_pivot_translate = mathutils.Vector([0, 0, 0])
        self.scale_pivot_translate = mathutils.Vector([0, 0, 0])

        self.translate_limit_x = mathutils.Vector([0, 0])
        self.translate_limit_y = mathutils.Vector([0, 0])
        self.translate_limit_z = mathutils.Vector([0, 0])
        self.rotate_limit_x = mathutils.Vector([0, 0])
        self.rotate_limit_y = mathutils.Vector([0, 0])
        self.rotate_limit_z = mathutils.Vector([0, 0])
        self.scale_limit_x = mathutils.Vector([0, 0])
        self.scale_limit_y = mathutils.Vector([0, 0])
        self.scale_limit_z = mathutils.Vector([0, 0])

        self.parent = 0
        self.childjoints : list[int] = []
        

        self.world_transform = mathutils.Matrix.Identity(4) #is set up later

        #{"name":"", "object_id":0, "num_uv_sets":0, "material":0}
        self.instancelist = []

    def from_textfile(self, nodeheader, fileio : FileIO.TextFileIO, closenode : bool = True):
        super().from_textfile(nodeheader, fileio)
        self.visible                =       bool(fileio.ReadLine().split()[1])
        self.scale_pivot            =       mathhelper.Vec3FromStrList(fileio.ReadLine().split()[1:])
        self.rotate_pivot           =       mathhelper.Vec3FromStrList(fileio.ReadLine().split()[1:])
        self.min_bound              =       mathhelper.Vec3FromStrList(fileio.ReadLine().split()[1:])
        self.max_bound              =       mathhelper.Vec3FromStrList(fileio.ReadLine().split()[1:])
        self.scale                  =       mathhelper.Vec3FromStrList(fileio.ReadLine().split()[1:])
        self.translate              =       mathhelper.Vec3FromStrList(fileio.ReadLine().split()[1:])

        rot_orient = mathhelper.Vec4FromStrList(fileio.ReadLine().split()[1:])
        rot = mathhelper.Vec4FromStrList(fileio.ReadLine().split()[1:])
        j_orient = mathhelper.Vec4FromStrList(fileio.ReadLine().split()[1:])
    
        self.rotation_orient        =       mathutils.Quaternion([rot_orient.w, rot_orient.x, rot_orient.y, rot_orient.z])
        self.rotation               =       mathutils.Quaternion([rot.w, rot.x, rot.y, rot.z])
        self.joint_orient           =       mathutils.Quaternion([j_orient.w, j_orient.x, j_orient.y, j_orient.z])
    
    
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
        num_childjoints           =       int(fileio.ReadLine().split()[1])
        if(num_childjoints != 0):
            for stringentry in fileio.ReadLine().split():
                self.childjoints.append(int(stringentry))
        
    
        self.world_transform = mathutils.Matrix.Identity(4) #is set up later
    
    
    
        #skip instance_list for now
        if fileio.ReadLine().split()[0].count("INSTANCE_LIST") == 1:
            xmd_base.skipNodeEntry(fileio)
        else:
            fileio.Rewind_Line()
        if fileio.ReadLine().split()[0].count("EXTRA_ATTRIBUTES") == 1:
            xmd_base.skipNodeEntry(fileio)
        else:
            fileio.Rewind_Line()

        if closenode: fileio.ReadLine()

    def dummy(self, polymeshnode : xmd_base.XMD_basenodeinfo):
        assert polymeshnode is not None
        self.instancelist.append({
                "name":polymeshnode.getNodeName(), 
                "object_id":polymeshnode.getNodeID(),
                "num_uv_sets":0,
                "material":0
                })
        self.rotation

    def from_blender(self, 
                     parent : xmd_base.XMD_basenodeinfo, 
                     childs : list[xmd_base.XMD_basenodeinfo], 
                     blenderbone : bpy.types.Bone, 
                     polymeshnode : xmd_base.XMD_basenodeinfo,
                     joint : bool = False):

        def world(bb : bpy.types.Bone) -> mathutils.Matrix:
            # Blender rest matrix with the import axes convention undone -> XMD-space world matrix
            M = bb.matrix_local
            W = (M.to_3x3() @ mathutils.Matrix.Identity(3).inverted()).to_4x4()
            W.translation = M.translation
            return W

        W = world(blenderbone)
        L = world(blenderbone.parent).inverted() @ W if blenderbone.parent else W
        loc, rot, _ = L.decompose()
        rot.normalize()

        ident = mathutils.Quaternion((1, 0, 0, 0))

        if parent != None: self.parent = parent.getNodeID()

        self.inherits_transform = blenderbone.use_inherit_rotation
        self.rotation_order = "xyz"

        self.translate = loc
        self.rotation_orient = ident.copy()

        if joint == False:
            self.rotation = rot
            self.joint_orient = ident.copy()
        else:
            self.rotation = ident.copy()
            self.joint_orient = rot

        mins, maxs = BoundsFromBone(blenderbone)
        self.min_bound = mins
        self.max_bound = maxs

        #self.bind_pose_matrix = L.transposed()

        for child in childs:
            self.childjoints.append(child.getNodeID())

        if polymeshnode != None:
            self.instancelist.append({
                "name":polymeshnode.getNodeName(), 
                "object_id":polymeshnode.getNodeID(),
                "num_uv_sets":0,
                "material":0
                })
        return


    def _textfile_write(self, fileio : FileIO.TextFileIO):
        fileio.WriteLine(f"\tvisible {int(self.visible)}")
        fileio.WriteLine(f"\tscale_pivot {self.scale_pivot.x} {self.scale_pivot.y} {self.scale_pivot.z}")
        fileio.WriteLine(f"\trotate_pivot {self.rotate_pivot.x} {self.rotate_pivot.y} {self.rotate_pivot.z}")
        fileio.WriteLine(f"\tmin_bound {self.min_bound.x} {self.min_bound.y} {self.min_bound.z}")
        fileio.WriteLine(f"\tmax_bound {self.max_bound.x} {self.max_bound.y} {self.max_bound.z}")
        fileio.WriteLine(f"\tscale {self.scale.x} {self.scale.y} {self.scale.z}")
        fileio.WriteLine(f"\ttranslate {self.translate.x} {self.translate.y} {self.translate.z}")

        fileio.WriteLine(f"\trotation_orient {self.rotation_orient.x} {self.rotation_orient.y} {self.rotation_orient.z} {self.rotation_orient.w}")
        fileio.WriteLine(f"\trotation {self.rotation.x} {self.rotation.y} {self.rotation.z} {self.rotation.w}")
        fileio.WriteLine(f"\tjoint_orient	{self.joint_orient.x} {self.joint_orient.y} {self.joint_orient.z} {self.joint_orient.w}")

        fileio.WriteLine(f"\tbind_pose_matrix")
        for row in self.bind_pose_matrix:
            fileio.WriteLine(f"\t\t{row[0]} {row[1]} {row[2]} {row[3]}")
        fileio.WriteLine(f"\trotation_order {self.rotation_order}")
        fileio.WriteLine(f"\tinherits_transform {int(self.inherits_transform)}")
        fileio.WriteLine(f"\tshearing {self.shearing.x} {self.shearing.y} {self.shearing.z}")
        fileio.WriteLine(f"\trotate_pivot_translate {self.rotate_pivot_translate.x} {self.rotate_pivot_translate.y} {self.rotate_pivot_translate.z}")
        fileio.WriteLine(f"\tscale_pivot_translate {self.scale_pivot_translate.x} {self.scale_pivot_translate.y} {self.scale_pivot_translate.z}")
        fileio.WriteLine("\ttranslate_limit_x -INF +INF")
        fileio.WriteLine("\ttranslate_limit_y -INF +INF")
        fileio.WriteLine("\ttranslate_limit_z -INF +INF")
        fileio.WriteLine("\trotate_limit_x -INF +INF")
        fileio.WriteLine("\trotate_limit_y -INF +INF")
        fileio.WriteLine("\trotate_limit_z -INF +INF")
        fileio.WriteLine("\tscale_limit_x -INF +INF")
        fileio.WriteLine("\tscale_limit_y -INF +INF")
        fileio.WriteLine("\tscale_limit_z -INF +INF")
        fileio.WriteLine(f"\tparent {self.parent}")
        fileio.WriteLine(f"\tchild_joints {len(self.childjoints)}")
        if len(self.childjoints) > 0:
            linewrite = "\t\t"
            for i in self.childjoints:
                linewrite += f"{i} "
            fileio.WriteLine(linewrite)

        fileio.WriteLine("\tINSTANCE_LIST")
        fileio.WriteLine("\t{")
        for instance in self.instancelist:
            fileio.WriteLine(f"\t\tINSTANCE {instance['name']} {{")
            fileio.WriteLine(f"\t\t\tobject_id {instance['object_id']}")
            fileio.WriteLine(f"\t\t\tnum_uv_sets {instance['num_uv_sets']}")
            fileio.WriteLine(f"\t\t\tmaterial {instance['material']}")
            fileio.WriteLine(f"\t\t}}")
        fileio.WriteLine("\t}")