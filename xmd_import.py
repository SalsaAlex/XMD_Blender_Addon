from .xmdimport import xmd_base
from .xmdimport import xmd_info
from .xmdimport import xmd_bone
from .xmdimport import xmd_joint
from .xmdimport import xmd_geometry
from .xmdimport import xmd_polygonmesh
from .xmdimport import xmd_skin
from . import FileIO
from . import blenderutils

import string
import bpy
import bmesh
import bpy_extras
import mathutils

s_bones : list[xmd_bone.XMD_bone] = []
s_polymesh : list[xmd_polygonmesh.XMD_polygonmesh] = []
s_skins : list[xmd_skin.XMD_skin] = []
#s_anims : list[xmd_animcycle.XMD_animcycle] = []

s_blenderarmature : bpy.types.Armature = None
s_blenderarmature_object : bpy.types.Object = None

s_blendermeshes : list[bpy.types.Mesh] = []
s_blendermesh_objects : list[bpy.types.Object] = []

def parseAllXMDNodes(fileio : FileIO.TextFileIO):
    line = fileio.ReadLine()
    while line:
        if line != '\n':
            nodename = line.split(' ')[0]
            if nodename.count("BONE") == 1:
                s_bones.append(xmd_bone.XMD_bone(line.split(' '), fileio))
            elif nodename.count("JOINT") == 1:
                s_bones.append(xmd_joint.XMD_joint(line.split(' '), fileio))
            elif nodename.count("POLYGON_MESH") == 1:
                s_polymesh.append(xmd_polygonmesh.XMD_polygonmesh(line.split(' '), fileio))
            elif nodename.count("SKIN") == 1:
                s_skins.append(xmd_skin.XMD_skin(line.split(' '), fileio))
            #elif nodename.count("ANIM_CYCLE") == 1:
            #    s_anims.append(xmd_animcycle.XMD_animcycle(line.split(' '), fileio))
            else:
                xmd_base.skipNodeEntry(fileio)
        
        line = fileio.ReadLine()


#xmd lookup

def findXMDBoneByIndex(index : int):
    for bone in s_bones:
        if bone.nodeid == index:
            return bone
    
    return None

def findXMDMeshByIndex(index : int):
    for mesh in s_polymesh:
        if mesh.nodeid == index:
            return mesh
        
    return None

def findXMDBoneByName(name : str):
    for bone in s_bones:
        if bone.nodename == name:
            return bone
        
    return None

def getBoneLocalTransform(bone : xmd_bone.XMD_bone):
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
    result: list[xmd_bone.XMD_bone] = []

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

        new_bone.head = localtransform.to_translation()
        new_bone.tail = new_bone.head + localtransform.col[0].to_3d()
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
        ebone.tail = head + direction * 0.1

        if parent and bone.inherits_transform:
            ebone.parent = s_blenderarmature.edit_bones[parent.nodename]
            ebone.parent.tail = ebone.head
        

    blenderutils.ToggleObjectMode(blendercontext)
    s_blenderarmature_object.show_in_front = True
    


def createMeshes(blendercontext : bpy.types.Context):

    blenderutils.ToggleObjectMode(blendercontext)

    xmdmeshidmap : dict[int, int] = {}

    blendermeshiter = 0
    for xmdmesh in s_polymesh:

        blendermesh, blendermesh_object = blenderutils.CreateMeshObj(blendercontext, xmdmesh.nodename)
        
        s_blendermeshes.append(blendermesh)
        s_blendermesh_objects.append(blendermesh_object)

        xmdmeshidmap[xmdmesh.nodeid] = blendermeshiter
        blendermeshiter = blendermeshiter + 1

        blendercontext.scene.collection.objects.link(blendermesh_object)

        blenderutils.DeselectAllObjects(blendercontext)
        blenderutils.SetObjectAsActive(blendercontext, blendermesh_object)

        main_pointindex_set: xmd_polygonmesh.polymesh_indexset = None
        for pointindexset in xmdmesh.indexsets:
            if pointindexset.name == xmdmesh.default_pointindex_set:
                main_pointindex_set = pointindexset
                break
        
        editablemesh = bmesh.new()

        for point in xmdmesh.points:
            editablemesh.verts.new(point)
        
        editablemesh.verts.ensure_lookup_table()
        
        indexiter = 0
        for face in main_pointindex_set.faces:
            vertseq : list[bmesh.types.BMVert] = []
            for vertindex in face:
                vertseq.append(editablemesh.verts[vertindex])

            editablemesh.faces.new(vertseq)

        editablemesh.to_mesh(blendermesh)
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

            #undone: weights for verts
            vertgroups : list[bpy.types.VertexGroup] = []
            for influencerindex in skin.influences: 
                xmdbone = findXMDBoneByIndex(influencerindex)
                bone_vertgroup = blendermesh.vertex_groups.new(name=xmdbone.nodename)
                vertgroups.append(bone_vertgroup)
            
            for vertinfo in skin.vertweights:
                for weight in vertinfo.weightlist:
                    vertexgroup = vertgroups[weight.jointid]
                    vertexgroup.add([vertinfo.pointindex], weight.weightval, type='REPLACE')





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

    # draw the option panel
    def draw(_self, _blender_context):
        pass

    @staticmethod
    def menu_func(cls, _blender_context):
        cls.layout.operator_context = 'INVOKE_DEFAULT'
        cls.layout.operator(
                XMD_Import.bl_idname,
                text='XMD format (.xmd)',
                )

    def import_from_file(self, filepath, blender_context : bpy.types.Context):
        
        s_bones.clear()
        s_polymesh.clear()
        s_skins.clear()
        s_blendermesh_objects.clear()
        s_blendermeshes.clear()

        fileio = FileIO.TextFileIO(filepath, "r")
        xmd_info.parseXMDInfoEntry(fileio)

        parseAllXMDNodes(fileio)

        topological_sort_bones()

        createArmature(blender_context)

        createMeshes(blender_context)


    def execute(self, blender_context):
        self.import_from_file(self.filepath, blender_context)
        return {"FINISHED"}