import bpy

def ToggleObjectMode(blendercontext : bpy.types.Context):
    if blendercontext.mode.count('OBJECT') is not 1:
        bpy.ops.object.mode_set(mode='OBJECT')

def ToggleEditMode(blendercontext : bpy.types.Context):
    if blendercontext.mode.count('EDIT') is not 1:
        bpy.ops.object.mode_set(mode='EDIT')

def SetObjectAsActive(blendercontext : bpy.types.Context, blenderobj : bpy.types.Object):
    blenderobj.select_set(state=True)
    blendercontext.view_layer.objects.active = blenderobj

def GetActiveObject(blendercontext : bpy.types.Context):
    return blendercontext.view_layer.objects.active

def DeselectAllObjects(blendercontext : bpy.types.Context):
    for i in blendercontext.selected_objects: i.select_set(False)

def CreateArmatureObj(blendercontext : bpy.types.Context, objname : str):
    armature = blendercontext.blend_data.armatures.new(objname)
    armature_object = blendercontext.blend_data.objects.new(objname, armature)
    return armature, armature_object

def CreateMeshObj(blendercontext : bpy.types.Context, objname : str):
    mesh = blendercontext.blend_data.meshes.new(objname)
    mesh_object = blendercontext.blend_data.objects.new(objname, mesh)
    return mesh, mesh_object

