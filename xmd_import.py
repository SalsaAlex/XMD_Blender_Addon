from .xmd import xmd_include
from . import FileIO
from . import blenderutils
from . import mathhelper

import string
import bpy
import bpy_extras
import bmesh
import mathutils
import math

s_bones : list[xmd_include.XMD_bone] = []
s_polymesh : list[xmd_include.XMD_polygonmesh] = []
s_skins : list[xmd_include.XMD_skin] = []
s_animcycles : list[xmd_include.XMD_animcycle] = []
s_animationtakes : list[xmd_include.XMD_animationtake] = []

s_blenderarmature : bpy.types.Armature = None
s_blenderarmature_object : bpy.types.Object = None

s_blendermeshes : list[bpy.types.Mesh] = []
s_blendermesh_objects : list[bpy.types.Object] = []

def getstored_restpose(bb : bpy.types.Bone):
    v = bb.get("xmd_rest_world")
    if v is None:
        return None
    return mathutils.Matrix([v[0:4], v[4:8], v[8:12], v[12:16]])
def getTargetCorrection(bb : bpy.types.Bone):
    #W = getstored_restpose(bb)
    #if W is None:
    #    C = mathutils.Matrix.Identity(4)   # armature not made by this importer
    #else:
    #    C = (W.to_3x3().normalized().inverted() @ bb.matrix_local.to_3x3()).to_4x4()
    world_transform = (
        s_blenderarmature_object.matrix_world @
        bb.matrix_local
    )

    W = world_transform
    C = (W.to_3x3().normalized().inverted() @ bb.matrix_local.to_3x3()).to_4x4()
    
    return C

def skipNodeEntry(fileio : FileIO.TextFileIO):
    assert fileio.ReadLine().find("{") != -1
    bracketcount = 1
    while bracketcount != 0:
        curline = fileio.ReadLine()
        if curline.find("}") != -1:
            bracketcount = bracketcount - 1
        elif curline.find("{") != -1:
            bracketcount = bracketcount + 1
        
        if bracketcount == 0:
            break

def parseXMDInfoEntry(fileio : FileIO.TextFileIO):
    xmdobj = xmd_include.XMD_infoentry_info()
    xmdobj.from_textfile(fileio)
    return xmdobj

def parse_XMDNode(nodeclass : type[xmd_include.XMD_basenodeinfo], nodeheader, fileio : FileIO.TextFileIO):
    xmdobj = nodeclass()
    xmdobj.from_textfile(nodeheader, fileio)
    return xmdobj

s_nodeid_to_nodename : dict[int, str] = {}
nodename_classmap : dict[str, type[xmd_include.XMD_basenodeinfo]] = {
    "BONE":xmd_include.XMD_bone, 
    "JOINT":xmd_include.XMD_joint,
    "POLYGON_MESH":xmd_include.XMD_polygonmesh,
    "SKIN":xmd_include.XMD_skin,
    "ANIM_CYCLE":xmd_include.XMD_animcycle,
    "ANIMATION_TAKE":xmd_include.XMD_animationtake,
}

def parseAllXMDNodes(fileio : FileIO.TextFileIO):

    nodename_listmap : dict[str, list[xmd_include.XMD_basenodeinfo]] = {
        "BONE":s_bones,
        "JOINT":s_bones,
        "POLYGON_MESH":s_polymesh,
        "SKIN":s_skins,
        "ANIM_CYCLE":s_animcycles,
        "ANIMATION_TAKE":s_animationtakes,
    }

    line = fileio.ReadLine()
    while line:
        if line != '\n':
            nodename = line.split(' ')[0]
            node : xmd_include.XMD_basenodeinfo = None
            if nodename in nodename_classmap:
                node = parse_XMDNode(nodename_classmap[nodename], line.split(' '), fileio)
                s_nodeid_to_nodename[node.getNodeID()] = node.getNodeName()

            if nodename in nodename_listmap:
                list = nodename_listmap.get(nodename)
                list.append(node)
            else:
                skipNodeEntry(fileio)
        
        line = fileio.ReadLine()


#xmd lookup

def findXMDBoneByIndex(index : int):
    for bone in s_bones:
        if bone.nodeid == index: return bone
    return None

def findXMDMeshByIndex(index : int):
    for mesh in s_polymesh:
        if mesh.nodeid == index: return mesh
    return None

def findXMDBoneByName(name : str):
    for bone in s_bones:
        if bone.nodename == name: return bone
    return None

def getBoneLocalTransform(bone : xmd_include.XMD_bone):
        #   m_Local = translate * inversescale * jointorientation * rotation * rotationorientation * scale;

        parent_bone = findXMDBoneByIndex(bone.parent)

        translate = mathutils.Matrix.Translation(bone.translate)
        scale = mathutils.Matrix.Diagonal([bone.scale.x, bone.scale.y, bone.scale.z, 1])
        rotation = mathutils.Quaternion( [bone.rotation.w, bone.rotation.x, bone.rotation.y, bone.rotation.z] ).to_matrix().to_4x4()
        rotationorient = mathutils.Quaternion( [bone.rotation_orient.w, bone.rotation_orient.x, bone.rotation_orient.y, bone.rotation_orient.z] ).to_matrix().to_4x4()
        jointorient = mathutils.Quaternion( [bone.joint_orient.w, bone.joint_orient.x, bone.joint_orient.y, bone.joint_orient.z] ).to_matrix().to_4x4()

        inversescale = mathutils.Matrix.Identity(4)
        if parent_bone is not None:
            inversescale = inversescale @ mathutils.Matrix.Diagonal([parent_bone.scale.x, parent_bone.scale.y, parent_bone.scale.z, 1])
        
        inversescale = inversescale.inverted()

        localtransform = translate @ inversescale
        localtransform = localtransform @ (jointorient @ rotation) 
        localtransform = localtransform @ (rotationorient @ scale)
        return localtransform
    

def topological_sort_bones():
    global s_bones

    nodeid_to_bone = {bone.getNodeID(): bone for bone in s_bones}
    visited = set()
    result: list[xmd_include.XMD_bone] = []

    def visit(bone):
        node_id = bone.getNodeID()
        if node_id in visited:
            return

        parent_id = bone.parent
        if parent_id != -1 and parent_id in nodeid_to_bone:
            visit(nodeid_to_bone[parent_id])

        visited.add(node_id)
        result.append(bone)

    for bone in s_bones:
        visit(bone)

    s_bones = result

def createArmature(blendercontext : bpy.types.Context):
    blenderutils.ToggleObjectMode(blendercontext)

    global s_blenderarmature
    global s_blenderarmature_object

    s_blenderarmature, s_blenderarmature_object = blenderutils.CreateArmatureObj(blendercontext, "xmd skeleton")

    blendercontext.scene.collection.objects.link(s_blenderarmature_object)

    blenderutils.DeselectAllObjects(blendercontext)
    blenderutils.SetObjectAsActive(blendercontext, s_blenderarmature_object)

    blenderutils.ToggleEditMode(blendercontext)

    xmdbonemap: dict[int, int] = {} #gives the node id of the bone
    xmdparentbonemap: dict[int, int] = {} #gives the node id of the parent bone
    blenderbonemap: dict[int, int] = {} #gives the index of the armature bone

    boneindex = 0
    for bone in s_bones:
        parentbone = findXMDBoneByIndex(bone.parent)
        xmdbonemap[boneindex] = bone.getNodeID()
        xmdparentbonemap[boneindex] = parentbone.getNodeID() if parentbone is not None else -1
        blenderbonemap[bone.getNodeID()] = boneindex

        new_bone = s_blenderarmature.edit_bones.new(bone.nodename)
        s_blenderarmature.edit_bones.active = new_bone

        localtransform = getBoneLocalTransform(bone)

        axis = localtransform.col[0].to_3d()
        if axis.length < 1e-3: #dont want our bones to get deleted because its too small
            axis = mathutils.Vector((0, 1, 0))   # any non-zero fallback

        new_bone.head = localtransform.to_translation()
        new_bone.tail = new_bone.head + axis
        boneindex = boneindex + 1

    nodeid_to_bone = {bone.getNodeID(): bone for bone in s_bones}

    for bone in s_bones:
        parent = nodeid_to_bone.get(bone.parent)

        if parent:
            bone.world_transform = parent.world_transform @ getBoneLocalTransform(bone)
        else:
            bone.world_transform = getBoneLocalTransform(bone)

        ebone = s_blenderarmature.edit_bones[bone.nodename]

        head = bone.world_transform.to_translation()
        direction = bone.world_transform.col[1].to_3d().normalized()

        ebone.head = head
        ebone.tail = head + direction * 5

        if parent and bone.inherits_transform:
          ebone.parent = s_blenderarmature.edit_bones[parent.nodename]
        #  if (ebone.head - ebone.parent.head).length > 1e-2: #dont want our bones to get deleted because its too small
        #      ebone.parent.tail = ebone.head

        armature_inv = s_blenderarmature_object.matrix_world.inverted()

        ebone.matrix = armature_inv @ bone.world_transform
        

    blenderutils.ToggleObjectMode(blendercontext)
    s_blenderarmature_object.show_in_front = True

    #store rest pose
    for bone in s_bones:
        bb = s_blenderarmature.bones[bone.nodename]
        W = bone.world_transform
        bb["xmd_rest_world"] = [W[r][c] for r in range(4) for c in range(4)]

    


def createMeshes(blendercontext : bpy.types.Context):

    blenderutils.ToggleObjectMode(blendercontext)

    xmdmeshidmap : dict[int, int] = {}

    blendermeshiter = 0
    for xmdmesh in s_polymesh:

        blendermesh_object : bpy.types.Object
        blendermesh : bpy.types.Mesh

        blendermesh, blendermesh_object = blenderutils.CreateMeshObj(blendercontext, xmdmesh.nodename)
        
        s_blendermeshes.append(blendermesh)
        s_blendermesh_objects.append(blendermesh_object)

        xmdmeshidmap[xmdmesh.nodeid] = blendermeshiter
        blendermeshiter = blendermeshiter + 1

        blendercontext.scene.collection.objects.link(blendermesh_object)

        blenderutils.DeselectAllObjects(blendercontext)
        blenderutils.SetObjectAsActive(blendercontext, blendermesh_object)

        main_pointindex_set: xmd_include.polymesh_indexset = None
        for pointindexset in xmdmesh.indexsets:
            if pointindexset.name == xmdmesh.default_pointindex_set:
                main_pointindex_set = pointindexset
                break
        
        editablemesh = bmesh.new()

        #points
        for point in xmdmesh.points:
            editablemesh.verts.new(point)
        
        editablemesh.verts.ensure_lookup_table()

        #make the faces
        indexiter = 0
        for face in main_pointindex_set.faces:
            vertseq : list[bmesh.types.BMVert] = []
            for vertindex in face:
                vertseq.append(editablemesh.verts[vertindex])
            if editablemesh.faces.get(vertseq) is None:
                editablemesh.faces.new(vertseq)

        editablemesh.to_mesh(blendermesh)

        #smooth the mesh before applying our normals
        if "sharp_face" in blendermesh.attributes: blendermesh.attributes.remove(blendermesh.attributes["sharp_face"])

        #normals
        normals = xmdmesh.getNormals()
        if normals != None:
            floatlist : list[list[float]] = []
            for f in normals:
                for v in f:
                    floatlist.append(mathhelper.Vec3ToFloatList(v))
            blendermesh.normals_split_custom_set(floatlist)
            blendermesh.update(calc_edges=True, calc_edges_loose=True)

        editablemesh.free()


    for skin in s_skins:
        affectedmeshlist : list[bpy.types.Object] = []
        for affectedmeshindex in skin.affectednodes:
            objectindex = xmdmeshidmap[affectedmeshindex]
            affectedmeshlist.append(s_blendermesh_objects[objectindex])
        
        for blendermesh in affectedmeshlist:
            blendermesh.parent = s_blenderarmature_object
            skeleton_modifier : bpy.types.ArmatureModifier = blendermesh.modifiers.new('skeleton_modifier', 'ARMATURE')
            skeleton_modifier.show_expanded = False
            skeleton_modifier.use_bone_envelopes = False
            skeleton_modifier.use_vertex_groups = True
            skeleton_modifier.object = s_blenderarmature_object

            vertgroups : list[bpy.types.VertexGroup] = []
            for influencerindex in skin.influences: 
                xmdbone = findXMDBoneByIndex(influencerindex)
                bone_vertgroup = blendermesh.vertex_groups.new(name=xmdbone.nodename)
                vertgroups.append(bone_vertgroup)
            
            for vertinfo in skin.vertweights:
                for weight in vertinfo.weightlist:
                    vertexgroup = vertgroups[weight.jointid]
                    vertexgroup.add([vertinfo.pointindex], weight.weightval, type='REPLACE')

def applyLocalPoseToPoseBone(pbone : bpy.types.PoseBone, xmdbone : xmd_include.XMD_bone, loc, rot_xyzw, scl, frame_num : int):
    bone = pbone.bone
    assert xmdbone is not None
    C = getTargetCorrection(bone)

    if bone.parent:
        rest_local = bone.parent.matrix_local.inverted() @ bone.matrix_local
        C_parent_inv = getTargetCorrection(bone.parent).inverted()
    else:
        rest_local = bone.matrix_local
        C_parent_inv = mathutils.Matrix.Identity(4)

    def qmat(q):
        return mathutils.Quaternion((q.w, q.x, q.y, q.z)).normalized().to_matrix().to_4x4()

    x, y, z, w = rot_xyzw
    R = mathutils.Quaternion((w, x, y, z)).normalized().to_matrix().to_4x4()

    file_local = (mathutils.Matrix.Translation(loc)
                  @ qmat(xmdbone.joint_orient)
                  @ R
                  @ qmat(xmdbone.rotation_orient)
                  @ mathutils.Matrix.Diagonal([scl[0], scl[1], scl[2], 1]))

    pbone.matrix_basis = rest_local.inverted() @ C_parent_inv @ file_local @ C

    pbone.keyframe_insert("rotation_quaternion", frame=frame_num)
    pbone.keyframe_insert("location", frame=frame_num)
    pbone.keyframe_insert("scale", frame=frame_num)


def sampleAt(samples, default, frame : int):
    if not samples:
        return default
    return samples[min(frame, len(samples) - 1)]

def createAnimations(blendercontext : bpy.types.Context):
    blenderutils.SetObjectAsActive(blendercontext, s_blenderarmature_object)
    blenderutils.TogglePoseMode(blendercontext)
    
    pose_bones = s_blenderarmature_object.pose.bones

    if s_blenderarmature_object.animation_data is None:
        s_blenderarmature_object.animation_data_create()

    for anim in s_animcycles:
        action = bpy.data.actions.new(name=anim.getNodeName())
        action.use_fake_user = True              # keep it alive even if not assigned
        s_blenderarmature_object.animation_data.action = action   # keyframe_insert writes into the active action

        bpy.context.scene.render.fps = int(anim.fps)

        for bone_index in anim.listboneskey:
            pbone : bpy.types.PoseBone = pose_bones.get(s_nodeid_to_nodename[bone_index])
            if pbone == None: continue
            pbone.rotation_mode = 'QUATERNION'

            numframes = len(anim.listboneskey[bone_index].frames)
            for f in range(numframes):
                info = anim.getboneinfo_forframe(bone_index, f)
                frame_num = anim.start + f

                applyLocalPoseToPoseBone(pbone, findXMDBoneByIndex(bone_index), info["transkey"], info["rotkey"], info["scalekey"], frame_num)

        action.frame_range = (anim.start, anim.end)

        # Leave the first cycle active so it plays when you hit space
        if s_animcycles:
            s_blenderarmature_object.animation_data.action = bpy.data.actions[s_animcycles[0].getNodeName()]
            bpy.context.scene.frame_start = int(s_animcycles[0].start)
            bpy.context.scene.frame_end = int(s_animcycles[0].end)
    for take in s_animationtakes:
        action = bpy.data.actions.new(name=take.getNodeName())
        action.use_fake_user = True
        s_blenderarmature_object.animation_data.action = action

        bpy.context.scene.render.fps = int(take.fps)

        for node_id, animnode in take.animationnodes.items():
            bone_name = s_nodeid_to_nodename.get(node_id)
            if bone_name is None:
                continue                      # animated node that isn't a bone (dummy, mesh...)
            pbone : bpy.types.PoseBone = pose_bones.get(bone_name)
            if pbone is None: continue
            pbone.rotation_mode = 'QUATERNION'

            rot_samples   = animnode.getAttribSamples("rotation")
            scale_samples = animnode.getAttribSamples("scale")
            trans_samples = animnode.getAttribSamples("translate")

            # All-POSE_KEY nodes have 1 sample -> a single key at start_time.
            numframes = max(len(rot_samples or []), len(scale_samples or []),
                            len(trans_samples or []), 1)

            for f in range(numframes):
                rot   = sampleAt(rot_samples,   (0, 0, 0, 1), f)
                scl   = sampleAt(scale_samples, (1, 1, 1),    f)
                trans = sampleAt(trans_samples, (0, 0, 0),    f)

                applyLocalPoseToPoseBone(pbone, findXMDBoneByIndex(node_id), trans, rot, scl, take.start_time + f)

        action.frame_range = (take.start_time, take.end_time)





def DefaultImportXMD(blender_context : bpy.types.Context):
    topological_sort_bones()

    createArmature(blender_context)

    createMeshes(blender_context)

    createAnimations(blender_context)


def AppendAnimation(blender_context : bpy.types.Context):
    global s_blenderarmature_object
    global s_blenderarmature

    topological_sort_bones()

    s_blenderarmature_object = blenderutils.GetActiveObject(blender_context)
    if s_blenderarmature_object == None: return
    if s_blenderarmature_object.data == None: return
    if type(s_blenderarmature_object.data) != bpy.types.Armature: return
    
    s_blenderarmature = s_blenderarmature_object.data

    blenderutils.TogglePoseMode(blender_context)
    
    pose_bones = s_blenderarmature_object.pose.bones

    if s_blenderarmature_object.animation_data is None:
        s_blenderarmature_object.animation_data_create()

    for anim in s_animcycles:
        action = bpy.data.actions.new(name=anim.getNodeName())
        action.use_fake_user = True              # keep it alive even if not assigned
        s_blenderarmature_object.animation_data.action = action   # keyframe_insert writes into the active action

        bpy.context.scene.render.fps = int(anim.fps)

        for bone_index in anim.listboneskey:
            bone_name = s_nodeid_to_nodename.get(bone_index)
            if bone_name is None:
                continue                      # animated node that isn't a bone (dummy, mesh...)
            pbone : bpy.types.PoseBone = pose_bones.get(s_nodeid_to_nodename[bone_index])
            if pbone == None: continue
            pbone.rotation_mode = 'QUATERNION'

            numframes = len(anim.listboneskey[bone_index].frames)
            for f in range(numframes):
                info = anim.getboneinfo_forframe(bone_index, f)
                frame_num = anim.start + f

                applyLocalPoseToPoseBone(pbone, findXMDBoneByName(bone_name), info["transkey"], info["rotkey"], info["scalekey"], frame_num)

        action.frame_range = (anim.start, anim.end)

        if s_animcycles:
            s_blenderarmature_object.animation_data.action = bpy.data.actions[s_animcycles[0].getNodeName()]
            bpy.context.scene.frame_start = int(s_animcycles[0].start)
            bpy.context.scene.frame_end = int(s_animcycles[0].end)
    for take in s_animationtakes:
        action = bpy.data.actions.new(name=take.getNodeName())
        action.use_fake_user = True
        s_blenderarmature_object.animation_data.action = action

        bpy.context.scene.render.fps = int(take.fps)

        for node_id, animnode in take.animationnodes.items():
            bone_name = s_nodeid_to_nodename.get(node_id)
            if bone_name is None:
                continue                      # animated node that isn't a bone (dummy, mesh...)
            pbone : bpy.types.PoseBone = pose_bones.get(bone_name)
            if pbone is None: continue
            pbone.rotation_mode = 'QUATERNION'
        
            rot_samples   = animnode.getAttribSamples("rotation")
            scale_samples = animnode.getAttribSamples("scale")
            trans_samples = animnode.getAttribSamples("translate")
        
            # All-POSE_KEY nodes have 1 sample -> a single key at start_time.
            numframes = max(len(rot_samples or []), len(scale_samples or []),
                            len(trans_samples or []), 1)
        
            for f in range(numframes):
                rot   = sampleAt(rot_samples,   (0, 0, 0, 1), f)
                scl   = sampleAt(scale_samples, (1, 1, 1),    f)
                trans = sampleAt(trans_samples, (0, 0, 0),    f)
        
                applyLocalPoseToPoseBone(pbone, findXMDBoneByName(bone_name), trans, rot, scl, take.start_time + f)
            
        action.frame_range = (take.start_time, take.end_time)



class XMD_Import(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):

    bl_idname = 'import_model.xmd'
    bl_label = 'XMD importer'
    bl_description = 'Import xmd models.'
    bl_options = {'PRESET', }
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'

    filename_ext: bpy.props.StringProperty(
            default='.xmd',
            options={'HIDDEN', }
            )

    filter_glob: bpy.props.StringProperty(
            default='*.xmd',
            options={'HIDDEN', }
            )

    append_animation: bpy.props.BoolProperty(
        name="Append animation",
        description="Append imported animation to the selected armature.",
        default=True,
    )

    # draw the option panel
    def draw(_self, _blender_context):
        layout = _self.layout
        layout.use_property_split = True      # label on the left, checkbox on the right
        layout.use_property_decorate = False  # hides the animate-property dots

        layout.prop(_self, "append_animation")

    @staticmethod
    def menu_func(cls, _blender_context):
        cls.layout.operator_context = 'INVOKE_DEFAULT'
        cls.layout.operator(
                XMD_Import.bl_idname,
                text='XMD format (.xmd)',
                )

    def import_from_file(self, filepath, blender_context : bpy.types.Context):
        
        s_bones.clear()
        s_animcycles.clear()
        s_animationtakes.clear()
        s_polymesh.clear()
        s_skins.clear()
        s_blendermesh_objects.clear()
        s_blendermeshes.clear()

        fileio = FileIO.TextFileIO(filepath, "r")
        parseXMDInfoEntry(fileio)

        parseAllXMDNodes(fileio)

        if(self.append_animation == True):
            AppendAnimation(blender_context)
        else:
            DefaultImportXMD(blender_context)


    def execute(self, blender_context):
        self.import_from_file(self.filepath, blender_context)
        return {"FINISHED"}