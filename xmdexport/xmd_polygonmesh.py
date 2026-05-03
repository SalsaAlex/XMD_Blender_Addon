import bpy
import bmesh

from .. import FileIO
from .. import mathhelper

def vertindex_invertlist(meshvert : bmesh.types.BMVert, vertlist : list[bmesh.types.BMVert]):
    vertiter = 0
    for vert in vertlist:
        if meshvert == vert:
            return vertiter
        vertiter = vertiter + 1
    return -1

def WriteMesh(fileio : FileIO.TextFileIO,
                blenderobj : bpy.types.Object,
                blendermesh : bpy.types.Mesh, 
                readablemesh : bmesh.types.BMesh,
                deformernodes : list[int],
                nodeid : int):
    fileio.WriteLine("POLYGON_MESH " + blenderobj.name + "\n")
    fileio.WriteLine("{\n")
    fileio.WriteLine("\tid " + str(nodeid) + "\n")
    fileio.WriteLine("\tpoints " + str(len(readablemesh.verts)) + "\n")
    for vert in readablemesh.verts:
        fileio.WriteLine("\t\t" + str(vert.co.x) + " " + str(vert.co.y) + " " + str(vert.co.z) + "\n")
    
    fileio.WriteLine("\tdeformer_queue " + str(len(deformernodes)))
    for deformernodeindex in deformernodes:
        fileio.WriteLine(" " + str(deformernodeindex))
    fileio.WriteLine("\n")
    fileio.WriteLine("\tintermediate_object 0\n")
    fileio.WriteLine("\tpoint_index_set \"points\"\n")
    fileio.WriteLine("\tPOLY_COUNTS " + str(len(readablemesh.faces)) + "\n")
    fileio.WriteLine("\t{\n")
    for face in readablemesh.faces:
        fileio.WriteLine("\t\t" + str(len(face.verts)) + "\n")
    fileio.WriteLine("\t}\n")

    fileio.WriteLine("\tnum_index_sets " + str(1) + "\n")
    fileio.WriteLine("\tINDEX_SET \"points\"\n")
    fileio.WriteLine("\t{\n")
    for face in readablemesh.faces:
        fileio.WriteLine("\t\t")
        for vert in face.verts:
            vertindex = vertindex_invertlist(vert, readablemesh.verts)
            fileio.WriteLine(str(vertindex) + " ")
        fileio.WriteLine("\n")
    fileio.WriteLine("\t}\n")

    fileio.WriteLine("\tnum_vertex_sets 0\n")

    fileio.WriteLine("}\n")