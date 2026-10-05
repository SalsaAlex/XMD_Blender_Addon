from .. import FileIO
from . import xmd_base
from . import xmd_bone
import mathutils
import math
from .. import mathhelper

import collections
from collections import defaultdict
import bpy

#returns loc, rot_xyzw, scale
def extractLocalPoseFromPoseBone(pbone: bpy.types.PoseBone, xmdbone: xmd_bone.XMD_bone,
                                 prev_quat=None):
    bone = pbone.bone

    if bone.parent: rest_local = bone.parent.matrix_local.inverted() @ bone.matrix_local
    else:           rest_local = bone.matrix_local

    file_local = rest_local @ pbone.matrix_basis @ mathutils.Matrix.Identity(4).inverted()

    loc = file_local.to_translation()

    L = file_local.to_3x3()
    cols = [L.col[i].copy() for i in range(3)]
    scl = [c.length for c in cols]

    Q = mathutils.Matrix.Identity(3)
    for i in range(3):
        Q.col[i] = cols[i] / scl[i] if scl[i] > 1e-12 else mathutils.Vector((0, 0, 0))

    if Q.determinant() < 0:
        scl[0] = -scl[0]
        Q.col[0] = -Q.col[0]

    J_inv  = xmdbone.joint_orient.inverted().to_matrix()
    Ro_inv = xmdbone.rotation_orient.inverted().to_matrix()
    R = J_inv @ Q @ Ro_inv

    q = R.to_quaternion().normalized()
    if prev_quat is not None: q.make_compatible(prev_quat)   # avoid sign flips between frames
    return loc, mathutils.Vector([q.x, q.y, q.z, q.w]), mathhelper.Vec3FromFloatList(scl)

class boneanim_info:
    def __init__(self):
        self.frames : list = []

    def from_textfile(self, numframes : int, fileio : FileIO.TextFileIO):
        assert fileio.ReadLine().count("{") == 1 #opening bracket
        for i in range(numframes):
            keyinfo = fileio.ReadLine().split()
            self.frames.append({
                "rotkey":mathhelper.Vec4FromStrList(keyinfo[0:4]),
                "transkey":mathhelper.Vec3FromStrList(keyinfo[4:7]),
                "scalekey":mathhelper.Vec3FromStrList(keyinfo[7:10])
                })
        assert fileio.ReadLine().count("}") == 1 #closing bracket

    def set_manual(self, framesinfo : list):
        for frameinfo in framesinfo:
            self.frames.append(frameinfo)

    def to_textfile(self, numframes : int, fileio : FileIO.TextFileIO):
        fileio.WriteLine("\t{")
        for i in range(numframes):
            frame = self.frames[i]
            linestr = "\t\t"
            for element in frame["rotkey"]:     linestr += (f"{element} ")
            for element in frame["transkey"]:   linestr += (f"{element} ")
            for element in frame["scalekey"]:   linestr += (f"{element} ")

            fileio.WriteLine(linestr)
        fileio.WriteLine("\t}")

class XMD_animcycle(xmd_base.XMD_basenodeinfo):
    def __init__(self):
        super().__init__("ANIM_CYCLE", False)

        self.numbones = 0
        self.start = 0.0
        self.end = 0.0
        self.numframes = 0
        self.fps = 0.0
        self.listboneskey : defaultdict[int, boneanim_info] = defaultdict(boneanim_info)

    def from_textfile(self, nodeheader, fileio : FileIO.TextFileIO):
        super().from_textfile(nodeheader, fileio)
        self.num_bones = int(fileio.ReadLine().split()[1])
        self.start = float(fileio.ReadLine().split()[1])
        self.end = float(fileio.ReadLine().split()[1])
        self.num_frames = int(fileio.ReadLine().split()[1])
        self.fps = float(fileio.ReadLine().split()[1])
        for _ in range(self.num_bones):
            boneindex = int(fileio.ReadLine().split()[1])
            boneinfo = boneanim_info()
            boneinfo.from_textfile(self.num_frames, fileio)
            self.listboneskey[boneindex] = boneinfo
        assert fileio.ReadLine().count("}") != 0

    #dummy animation
    def from_single_keyframe(self, 
                             bonelist : list[xmd_bone.XMD_bone], 
                             posebonelist : list[bpy.types.PoseBone],
                             blenderbonelist : list[bpy.types.Bone], 
                             blender_to_xmdbone : dict[bpy.types.Bone, xmd_bone.XMD_bone]):
        self.num_bones = len(bonelist)
        self.start = 0
        self.end = 1
        self.num_frames = 2
        self.fps = 30

        for blenderbone in blenderbonelist:
            xmdbone = blender_to_xmdbone[blenderbone]
            boneindex = xmdbone.getNodeID()
            boneinfo = boneanim_info()

            loc, rot_xyzw, scale = extractLocalPoseFromPoseBone(posebonelist[blenderbone.name], xmdbone)

            boneinfo.set_manual([
                {"rotkey":rot_xyzw,"transkey":loc,"scalekey":scale},
                {"rotkey":rot_xyzw,"transkey":loc,"scalekey":scale}])
            self.listboneskey[boneindex] = boneinfo

    def from_animation(self, 
                        blendercontext : bpy.types.Context,
                        action : bpy.types.Action,
                        bonelist : list[xmd_bone.XMD_bone], 
                        posebonelist : list[bpy.types.PoseBone],
                        blenderbonelist : list[bpy.types.Bone], 
                        blender_to_xmdbone : dict[bpy.types.Bone, xmd_bone.XMD_bone]):
        self.num_bones = len(bonelist)
        self.start = bpy.context.scene.frame_start
        self.end = bpy.context.scene.frame_end
        self.num_frames = self.end - self.start + 1
        self.fps = bpy.context.scene.render.fps

        perbone_frameinfo : defaultdict[bpy.types.Bone, list] = defaultdict(list)

        for frameindex in range(self.num_frames):
            bpy.context.scene.frame_set(frameindex)
            for blenderbone in blenderbonelist:
                xmdbone = blender_to_xmdbone[blenderbone]
                boneindex = xmdbone.getNodeID()
                boneinfo = boneanim_info()
                posebone = posebonelist[blenderbone.name]

                loc, rot_xyzw, scale = extractLocalPoseFromPoseBone(posebone, xmdbone)

                perbone_frameinfo[blenderbone].append({"rotkey":rot_xyzw,"transkey":loc,"scalekey":scale})

        for blenderbone in blenderbonelist:
            xmdbone = blender_to_xmdbone[blenderbone]
            self.listboneskey[xmdbone.getNodeID()].set_manual(perbone_frameinfo[blenderbone])

    #def from_blender(self, )

    #returns {"rotkey":mathutils.Quaternion, "transkey":mathutils.Vector, "scalekey":mathutils.Vector}
    def getboneinfo_forframe(self, boneindex : int, frameindex : int):
        assert boneindex in self.listboneskey, "boneindex out of bounds!"
        assert frameindex < len(self.listboneskey[boneindex].frames), "frameindex out of bounds!"
        return self.listboneskey[boneindex].frames[frameindex]
        

    def _textfile_write(self, fileio : FileIO.TextFileIO):
        fileio.WriteLine(f"\tnum_bones {self.num_bones}")
        fileio.WriteLine(f"\tstart {self.start}")
        fileio.WriteLine(f"\tend {self.end}")
        fileio.WriteLine(f"\tnum_frames {self.num_frames}")
        fileio.WriteLine(f"\tfps {self.fps}")
        for bone in self.listboneskey:
            fileio.WriteLine(f"\tBONE_ANIM {bone}")
            self.listboneskey[bone].to_textfile(self.num_frames, fileio)
