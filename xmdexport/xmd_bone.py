from .. import FileIO

import bpy
import mathutils

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
    



def WriteBones(fileio : FileIO.TextFileIO, armaturedata : bpy.types.Armature, nodeiditer : int, polymeshid : int):
    boneidmap : dict[bpy.types.Bone, int] = {}
    for bone in armaturedata.bones:
        boneidmap[bone] = nodeiditer
        nodeiditer = nodeiditer + 1

    boneindex = 0

    for bone in armaturedata.bones:
        mins, maxs = BoundsFromBone(bone)
        parent = bone.parent

        bonelocaltrans = bone.matrix
        if parent is not None:
            bonelocaltrans = bone.parent.matrix.inverted() @ bonelocaltrans

        bonelocalpos = bone.head
        if parent is not None:
            bonelocalpos = bonelocalpos - parent.head
        bonelocalrot = bonelocaltrans.to_quaternion()


        if boneindex is 0:
            fileio.WriteLine("BONE " + bone.name + "\n")
        else:
            fileio.WriteLine("JOINT " + bone.name + "\n")
        fileio.WriteLine("{\n")
        fileio.WriteLine("\tid " + str(boneidmap[bone]) + "\n")
        fileio.WriteLine("\tvisible 0\n")
        fileio.WriteLine("\tscale_pivot 0 0 0\n")
        fileio.WriteLine("\trotate_pivot 0 0 0\n")
        fileio.WriteLine("\tmin_bound " + str(mins.x) + " " + str(mins.y) + " " + str(mins.z) + "\n")
        fileio.WriteLine("\tmax_bound " + str(maxs.x) + " " + str(maxs.y) + " " + str(maxs.z) + "\n")
        fileio.WriteLine("\tscale 1 1 1\n")
        fileio.WriteLine("\ttranslate " + str(bonelocalpos.x) + " " + str(bonelocalpos.y) + " " + str(bonelocalpos.z) + "\n")
        fileio.WriteLine("\trotation_orient 0 0 0 1\n")
        fileio.WriteLine("\trotation " +  str(bonelocalrot.x) + " " + str(bonelocalrot.y) + " " + str(bonelocalrot.z) + str(bonelocalrot.w) + "\n")
        fileio.WriteLine("\tjoint_orient 0 0 0 1\n")
        fileio.WriteLine("\tbind_pose_matrix\n")
        fileio.WriteLine("\t\t1 0 0 0\n")
        fileio.WriteLine("\t\t0 1 0 0\n")
        fileio.WriteLine("\t\t0 0 1 0\n")
        fileio.WriteLine("\t\t0 0 0 1\n")
        fileio.WriteLine("\trotation_order xyz\n")
        fileio.WriteLine("\tinherits_transform 1\n")
        fileio.WriteLine("\tshearing 0 0 0\n")
        fileio.WriteLine("\trotate_pivot_translate 0 0 0\n")
        fileio.WriteLine("\tscale_pivot_translate 0 0 0\n")
        fileio.WriteLine("\ttranslate_limit_x -INF +INF\n")
        fileio.WriteLine("\ttranslate_limit_y -INF +INF\n")
        fileio.WriteLine("\ttranslate_limit_z -INF +INF\n")
        fileio.WriteLine("\trotate_limit_x -INF +INF\n")
        fileio.WriteLine("\trotate_limit_y -INF +INF\n")
        fileio.WriteLine("\trotate_limit_z -INF +INF\n")
        fileio.WriteLine("\tscale_limit_x -INF +INF\n")
        fileio.WriteLine("\tscale_limit_y -INF +INF\n")
        fileio.WriteLine("\tscale_limit_z -INF +INF\n")
        if parent is not None:
            fileio.WriteLine("\tparent " + str(boneidmap[parent]) + "\n")
        else:
            fileio.WriteLine("\tparent 0\n")
        fileio.WriteLine("\tchild_joints 0\n") #fix, dunno what this is for
        fileio.WriteLine("\tINSTANCE_LIST\n")
        fileio.WriteLine("\t{\n")
        if boneindex is 0:
            fileio.WriteLine("\t\tINSTANCE mesh {\n")
            fileio.WriteLine("\t\t\tobject_id " + str(polymeshid) + "\n")
            fileio.WriteLine("\t\t\tnum_uv_sets 0\n")
            fileio.WriteLine("\t\t\tmaterial 0\n")
            fileio.WriteLine("\t\t}\n")
        fileio.WriteLine("\t}\n")
        if boneindex is not 0:
            fileio.WriteLine("\tsegment_scale_compensate 1\n")
        fileio.WriteLine("}\n")

        return nodeiditer #weird ass language