from .. import FileIO
from . import xmd_geometry
from .. import mathhelper
import mathutils

import bmesh

class polymesh_indexset:
    def __init__(self):
        self.name = ""
        self.faces : list[list[int]] = []

    def set_manual(self, name : str, indexlist : list[list[int]]):
        self.name = name
        self.faces = indexlist

    def from_textfile(self, fileio : FileIO.TextFileIO):
        self.name = fileio.ReadLine().split()[1].replace('\"', "")
    
        assert fileio.ReadLine().count('{') is 1 #opening bracket
        line = fileio.ReadLine()
    
        while line.count('}') is not 1:
            indexseq : list[int] = []
            indexes = line.split()
            for index in indexes:
                indexseq.append(int(index))
            self.faces.append(indexseq)
            line = fileio.ReadLine()


class polymesh_vertexset:
    def __init__(self, fileio : FileIO.TextFileIO):
        self.name = fileio.ReadLine().split()[1].replace('\"', "")
        self.elements : list[mathutils.Vector] = []
        
        assert fileio.ReadLine().count('{') is 1 #opening bracket
        
        num_elements = int(fileio.ReadLine().split()[1])
        element_size = int(fileio.ReadLine().split()[1])
        self.usage = fileio.ReadLine().split()[1]
        self.default_indexset = fileio.ReadLine().split()[1].replace('\"', "")
        fileio.ReadLine() #elements

        if element_size == 4:
            while num_elements > 0:
                self.elements.append(mathhelper.Vec4FromStrList(fileio.ReadLine().split()))
                num_elements = num_elements -1
        elif element_size == 3:
            while num_elements > 0:
                self.elements.append(mathhelper.Vec3FromStrList(fileio.ReadLine().split()))
                num_elements = num_elements -1
        else:
            assert element_size == 2
            while num_elements > 0:
                self.elements.append(mathhelper.Vec2FromStrList(fileio.ReadLine().split()))
                num_elements = num_elements -1

        assert fileio.ReadLine().count('}') is 1 # closing bracket

def WriteMesh(fileio : FileIO.TextFileIO,
                readablemesh : bmesh.types.BMesh,
                deformernodes : list[int],
                nodeid : int):
    fileio.WriteLine("{\n")
    fileio.WriteLine("\tid " + str(nodeid) + "\n")
    fileio.WriteLine("\tpoints " + str(len(readablemesh.verts)) + "\n")
    
    linesbuffer : list[str] = []
    vertindexmap : dict[bmesh.types.BMVert, int] = {}
    vertiter = 0
    for vert in readablemesh.verts:
        vertpos = vert.co
        vertindexmap[vert] = vertiter
        vertiter = vertiter + 1
        linesbuffer.append(f"\t\t{vertpos.x} {vertpos.y} {vertpos.z}\n")
    fileio.WriteLine(''.join(linesbuffer))
    linesbuffer.clear()

    
    fileio.WriteLine("\tdeformer_queue " + str(len(deformernodes)))
    for deformernodeindex in deformernodes:
        fileio.WriteLine(" " + str(deformernodeindex))
    fileio.WriteLine("\n")
    fileio.WriteLine("\tintermediate_object 0\n")
    fileio.WriteLine("\tpoint_index_set \"points\"\n")
    fileio.WriteLine("\tPOLY_COUNTS " + str(len(readablemesh.faces)) + "\n")
    fileio.WriteLine("\t{\n")

    for face in readablemesh.faces:
        linesbuffer.append(f"\t\t{len(face.verts)}\n")
    fileio.WriteLine(''.join(linesbuffer))
    linesbuffer.clear()

    fileio.WriteLine("\t}\n")

    fileio.WriteLine("\tnum_index_sets " + str(1) + "\n")
    fileio.WriteLine("\tINDEX_SET \"points\"\n")
    fileio.WriteLine("\t{\n")
    for face in readablemesh.faces:
        fileio.WriteLine("\t\t")
        for vert in face.verts:
            vertindex = vertindexmap[vert]
            fileio.WriteLine(f"{vertindex} ")
        fileio.WriteLine("\n")
    fileio.WriteLine("\t}\n")

    fileio.WriteLine("\tnum_vertex_sets 0\n")

    fileio.WriteLine("}\n")



class XMD_polygonmesh(xmd_geometry.XMD_geometry):
    def __init__(self):
        super().__init__("POLYGON_MESH")

        self.polycounts : list[int] = []
        self.indexsets : list[polymesh_indexset] = []
        self.vertexsets : list[polymesh_vertexset] = []
        self.default_pointindex_set = ""

    def from_textfile(self, nodeheader, fileio : FileIO.TextFileIO):
        super().from_textfile(nodeheader, fileio, False)
        self.default_pointindex_set = fileio.ReadLine().split()[1].replace('\"', "")
    
        fileio.ReadLine() # numpolycount
        fileio.ReadLine() # opening bracket
    
        
        while True:
            line = fileio.ReadLine()
            if line.count('}') is 1:
                break
    
            self.polycounts.append(int(line.split()[0]))
    
        num_indexsets = int(fileio.ReadLine().split()[1])
        while num_indexsets > 0:
            indexset = polymesh_indexset()
            indexset.from_textfile(fileio)
            self.indexsets.append(indexset)
            num_indexsets = num_indexsets - 1
    
    
        num_vertexsets = int(fileio.ReadLine().split()[1])
        while num_vertexsets > 0:
            self.vertexsets.append(polymesh_vertexset(fileio))
            num_vertexsets = num_vertexsets - 1
    
    
        fileio.ReadLine() # closing bracket for this node

    def from_blender(self, readablemesh : bmesh.types.BMesh, deformers : list[xmd_geometry.xmd_base.XMD_basenodeinfo]):
        super().from_blender(readablemesh, deformers)
        self.default_pointindex_set = "points"

        vertindexmap : dict[bmesh.types.BMVert, int] = {}
        vertiter = 0
        for vert in readablemesh.verts:
            vertindexmap[vert] = vertiter
            vertiter += 1

        mainmesh_indexes : list[list[int]] = []

        for face in readablemesh.faces:
            self.polycounts.append(len(face.verts))
            face_vertindexes : list[int] = []
            for vert in face.verts:
                face_vertindexes.append(vertindexmap[vert])
            mainmesh_indexes.append(face_vertindexes)

        mainmesh_indexset = polymesh_indexset()
        mainmesh_indexset.set_manual("points", mainmesh_indexes)
        self.indexsets.append(mainmesh_indexset)
        

    def _textfile_write(self, fileio):
        super()._textfile_write(fileio)
        fileio.WriteLine(f"\tpoint_index_set \"{self.default_pointindex_set}\"")

        fileio.WriteLine(f"\tPOLY_COUNTS {len(self.polycounts)}")
        fileio.WriteLine("\t{")
        for polycount in self.polycounts:
            fileio.WriteLine(f"\t\t{polycount}")
        fileio.WriteLine("\t}")

        fileio.WriteLine(f"\tnum_index_sets {len(self.indexsets)}")
        for indexset in self.indexsets:
            fileio.WriteLine(f"\tINDEX_SET \"{indexset.name}\"")
            fileio.WriteLine("\t{")
            for indexseq in indexset.faces:
                indexline = "\t\t"
                for index in indexseq:
                    indexline += f" {index}"
                fileio.WriteLine(indexline)
            fileio.WriteLine("\t}")
        fileio.WriteLine(f"\tnum_vertex_sets {len(self.vertexsets)}")
        for vertexset in self.vertexsets:
            fileio.WriteLine(f"\tVERTEX_SET \"{vertexset.name}\"")
            fileio.WriteLine("\t{")
            fileio.WriteLine(f"\t\tnum_elements {len(vertexset.elements)}")
            fileio.WriteLine(f"\t\telement_size {len(vertexset.elements[0])}")
            fileio.WriteLine(f"\t\tusage {vertexset.usage}")
            fileio.WriteLine(f"\t\tindex_set \"{vertexset.default_indexset}\"")
            fileio.WriteLine(f"\t\telements")
            for element in vertexset.elements:
                elementline = "\t\t\t"
                for value in element:
                    elementline += f"{value} "
                fileio.WriteLine(elementline)
            fileio.WriteLine("\t}")

    def getIndexSet(self, name) -> polymesh_indexset:
        for set in self.indexsets:
            if set.name == name:
                return set
        return None

    def getNormals(self) -> list[mathutils.Vector]:
        for vertset in self.vertexsets:
            if vertset.usage == "kNormal":
                normalindexset = self.getIndexSet(vertset.default_indexset)
                normallist : list[list[mathutils.Vector]] = []
                for face in normalindexset.faces:
                    facevertlist : list[mathutils.Vector] = []
                    for vertindice in face:
                        facevertlist.append(vertset.elements[vertindice])
                    normallist.append(facevertlist)
                return normallist
        return None