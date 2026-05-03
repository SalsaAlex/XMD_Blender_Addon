from .xmdexport import xmd_info
from .xmdexport import xmd_polygonmesh
from .xmdexport import xmd_bone
from .xmdexport import xmd_objectset
from .xmdexport import xmd_animcycle
from . import blenderutils

from . import FileIO
import bpy
import bpy_extras
import bmesh

blenderobj_toexport : bpy.types.Object = None

nextnodeid : int = 1
def increment_nodeid(): 
    global nextnodeid
    nextnodeid = nextnodeid + 1

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
        nextnodeid = 1

        blenderobj_toexport = blenderutils.GetActiveObject(blender_context)
        if blenderobj_toexport is None:
            return
        

        fileio = FileIO.TextFileIO(filepath, 'w')        

        xmd_info.WriteInfo(fileio)
        if isinstance(blenderobj_toexport.data, bpy.types.Mesh):
            blenderutils.ToggleEditMode(blender_context)
            blendermesh : bpy.types.Mesh = blenderobj_toexport.data
            readablemesh = bmesh.from_edit_mesh(blendermesh)
            xmd_polygonmesh.WriteMesh(fileio, blenderobj_toexport, blendermesh, readablemesh, [], nextnodeid)
            readablemesh.free()
            increment_nodeid()
        
        if isinstance(blenderobj_toexport.parent.data, bpy.types.Armature):
            nextnodeid = xmd_bone.WriteBones(fileio, blenderobj_toexport.parent.data, nextnodeid, 1) #hardcoded polymeshid to be 1, it always is in this case

        xmd_objectset.WriteObjectSet(fileio, [nextnodeid - 1], nextnodeid)
        increment_nodeid()
        xmd_animcycle.WriteDummyAnim(fileio)

        blenderutils.ToggleObjectMode(blender_context)


    def execute(self, blender_context):
        self.export_to_file(self.filepath, blender_context)
        return {"FINISHED"}