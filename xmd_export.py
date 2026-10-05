from .xmd import xmd_include
from . import blenderutils
import mathutils

from . import FileIO
import bpy
import bpy_extras
import bmesh

from collections import defaultdict

blenderobj_toexport : bpy.types.Object = None

nextnodeid : int = 1
def increment_nodeid(): 
    global nextnodeid
    nextnodeid = nextnodeid + 1

def export_model(blender_context : bpy.types.Context,fileio : FileIO.TextFileIO):
    xmdpolymesh = xmd_include.XMD_polygonmesh()
    xmd_skinmodifier = xmd_include.XMD_skin()
    xmd_skinmodifier.setNodeID(nextnodeid)
    increment_nodeid()

    blenderutils.ToggleEditMode(blender_context)
    blendermesh : bpy.types.Mesh = blenderobj_toexport.data
    readablemesh = bmesh.from_edit_mesh(blendermesh)


    xmdpolymesh.setNodeID(nextnodeid)
    xmdpolymesh.setNodeName(blenderobj_toexport.name)
    xmdpolymesh.from_blender(readablemesh, [xmd_skinmodifier])
    xmdpolymesh.to_textfile(fileio)
    
    readablemesh.free()
    increment_nodeid()

    bonelist : list[xmd_include.XMD_bone] = []
    xmdbone_child_map : defaultdict[xmd_include.XMD_bone, list[xmd_include.XMD_bone]] = defaultdict(list)
    blenderbone_xmdbone_map : defaultdict[bpy.types.Bone, xmd_include.XMD_bone] = defaultdict(xmd_include.XMD_bone)
    xmdbone_blenderbone_map : defaultdict[xmd_include.XMD_bone, bpy.types.Bone] = defaultdict(bpy.types.Bone)
    blenderbone_parent_map : defaultdict[bpy.types.Bone, bpy.types.Bone] = defaultdict(bpy.types.Bone)
    
    if isinstance(blenderobj_toexport.parent.data, bpy.types.Armature):
        armature_obj = blenderobj_toexport.parent
        armature : bpy.types.Armature = armature_obj.data
        #set the node ids first
        for bone in armature.bones:
            if bone.parent == None:
                xmdbone = xmd_include.XMD_bone()
                xmdbone.setNodeID(nextnodeid)
                xmdbone.setNodeName(bone.name)
                bonelist.append(xmdbone)
                blenderbone_xmdbone_map[bone] = xmdbone
                xmdbone_blenderbone_map[xmdbone] = bone
                blenderbone_parent_map[bone] = None
            else:
                xmdjoint = xmd_include.XMD_joint()
                xmdjoint.setNodeID(nextnodeid)
                xmdjoint.setNodeName(bone.name)
                bonelist.append(xmdjoint)
                blenderbone_xmdbone_map[bone] = xmdjoint
                xmdbone_blenderbone_map[xmdjoint] = bone
                blenderbone_parent_map[bone] = bone.parent
            increment_nodeid()

        #setup the child map
        for bone in armature.bones:
            parent = blenderbone_parent_map[bone]
            if parent != None:
                xmdbone_child_map[blenderbone_xmdbone_map[parent]].append(blenderbone_xmdbone_map[bone])



        #then construct & write them
        already_added_xmdpolymesh = False
        for bone in armature.bones:
            parent = blenderbone_parent_map[bone]
            curxmdbone = blenderbone_xmdbone_map[bone]
            childlist = xmdbone_child_map[curxmdbone]
            if parent != None:
                curxmdbone.from_blender(blenderbone_xmdbone_map[parent], childlist, bone, None)
            else:
                curxmdbone.from_blender(None, childlist, bone, None)
            curxmdbone.to_textfile(fileio)

        dummybone = xmd_include.XMD_bone()
        dummybone.setNodeID(nextnodeid)
        dummybone.setNodeName("_dummy")
        dummybone.dummy(xmdpolymesh)
        dummybone.to_textfile(fileio)
        increment_nodeid()

        xmd_skinmodifier.setNodeName(f"{blenderobj_toexport.name}_skinmodifier")
        xmd_skinmodifier.from_blender(blenderobj_toexport, xmdpolymesh, bonelist, xmdbone_blenderbone_map)
        xmd_skinmodifier.to_textfile(fileio)
        increment_nodeid()

        xmdobjset = xmd_include.XMD_objectset()
        xmdobjset.setNodeName("skinobject_set")
        xmdobjset.setNodeID(nextnodeid)
        xmdobjset.setitems([xmdpolymesh, xmd_skinmodifier])
        xmdobjset.to_textfile(fileio)
        increment_nodeid()

        blenderutils.SetObjectAsActive(blender_context, armature_obj)
        blenderutils.TogglePoseMode(blender_context)

        dummyanimcycle = xmd_include.XMD_animcycle()
        dummyanimcycle.from_single_keyframe(bonelist, armature_obj.pose.bones, armature.bones, blenderbone_xmdbone_map)
        dummyanimcycle.to_textfile(fileio)

def export_animation(blender_context : bpy.types.Context, fileio : FileIO.TextFileIO):
    global nextnodeid

    bonelist : list[xmd_include.XMD_bone] = []
    xmdbone_child_map : defaultdict[xmd_include.XMD_bone, list[xmd_include.XMD_bone]] = defaultdict(list)
    blenderbone_xmdbone_map : dict[bpy.types.Bone, xmd_include.XMD_bone] = {}
    blenderbone_parent_map : dict[bpy.types.Bone, bpy.types.Bone] = {}

    armature_obj = blenderobj_toexport
    armature : bpy.types.Armature = armature_obj.data
    #set the node ids first
    for bone in armature.bones:
        if bone.parent == None:
            xmdbone = xmd_include.XMD_bone()
            xmdbone.setNodeID(nextnodeid)
            xmdbone.setNodeName(bone.name)
            bonelist.append(xmdbone)
            blenderbone_xmdbone_map[bone] = xmdbone
            blenderbone_parent_map[bone] = None
        else:
            xmdjoint = xmd_include.XMD_joint()
            xmdjoint.setNodeID(nextnodeid)
            xmdjoint.setNodeName(bone.name)
            bonelist.append(xmdjoint)
            blenderbone_xmdbone_map[bone] = xmdjoint
            blenderbone_parent_map[bone] = bone.parent
        increment_nodeid()

    #setup the child map
    for bone in armature.bones:
        parent = blenderbone_parent_map[bone]
        if parent != None:
            xmdbone_child_map[blenderbone_xmdbone_map[parent]].append(blenderbone_xmdbone_map[bone])



    #then construct & write them
    already_added_xmdpolymesh = False
    for bone in armature.bones:
        parent = blenderbone_parent_map[bone]
        curxmdbone = blenderbone_xmdbone_map[bone]
        childlist = xmdbone_child_map[curxmdbone]
        if parent != None:
            curxmdbone.from_blender(blenderbone_xmdbone_map[parent], childlist, bone, None)
        else:
            curxmdbone.from_blender(None, childlist, bone, None)
        curxmdbone.to_textfile(fileio)

    blenderutils.SetObjectAsActive(blender_context, armature_obj)
    blenderutils.TogglePoseMode(blender_context)

    dummyanimcycle = xmd_include.XMD_animcycle()
    dummyanimcycle.from_animation(blender_context, armature_obj.animation_data.action, bonelist, armature_obj.pose.bones, armature.bones, blenderbone_xmdbone_map)
    dummyanimcycle.to_textfile(fileio)

class XMD_Export(bpy.types.Operator, bpy_extras.io_utils.ExportHelper):

    bl_idname = 'export_model.xmd'
    bl_label = 'XMD exporter'
    bl_description = 'Export objects to a xmd format'
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
                XMD_Export.bl_idname,
                text='XMD format (.xmd)',
                )

    def export_to_file(self, filepath, blender_context : bpy.types.Context):
        global nextnodeid
        global blenderobj_toexport

        nextnodeid = 1

        blenderobj_toexport = blenderutils.GetActiveObject(blender_context)
        if blenderobj_toexport is None:
            return
        

        fileio = FileIO.TextFileIO(filepath, 'w')        

        xmdinfo = xmd_include.XMD_infoentry_info()
        xmdinfo.construct()
        xmdinfo.to_textfile(fileio)

        if type(blenderobj_toexport.data) == bpy.types.Mesh:
            export_model(blender_context, fileio)
        elif type(blenderobj_toexport.data) == bpy.types.Armature and blenderobj_toexport.animation_data != None:
            if blenderobj_toexport.animation_data.action != None:
                export_animation(blender_context, fileio)

        blenderutils.ToggleObjectMode(blender_context)


    def execute(self, blender_context):
        self.export_to_file(self.filepath, blender_context)
        return {"FINISHED"}