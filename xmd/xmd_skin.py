from .. import FileIO
from . import xmd_deformer
from . import xmd_base
from . import xmd_bone
import bpy
import collections
from collections import defaultdict

class weightinfoentry:
    def __init__(self, jointid : int, weight : float):
        self.jointid = jointid
        self.weightval = weight

class skin_vertweights:

    def __init__(self):
        self.weightlist : list[weightinfoentry] = []
        self.pointindex = 0 #only used internally, for importing by blender

    def from_textfile(self, fileio : FileIO.TextFileIO, pointindex : int):
        self.pointindex = pointindex #only used internally, for importing by blender
        line = fileio.ReadLine().split()
        numweights = int(line[0])
        weightiter = 1
        while weightiter < (numweights * 2):
            self.weightlist.append(weightinfoentry(int(line[weightiter]), float(line[weightiter + 1])))
            weightiter += 2


class XMD_skin(xmd_deformer.XMD_deformer):
    def __init__(self):
        super().__init__("SKIN")

        self.influences : list[int] = []
        self.vertweights : list[skin_vertweights] = []

    def from_textfile(self, nodeheader, fileio : FileIO.TextFileIO):
            super().from_textfile(nodeheader, fileio, False)
    
            num_influences = int(fileio.ReadLine().split()[1])
            influencelist = fileio.ReadLine().split()
            for influence in influencelist:
                self.influences.append(int(influence))
            
            num_points = int(fileio.ReadLine().split()[1])
            assert fileio.ReadLine().split()[0].count('weights') is 1
            weightpointiter = 0
            while weightpointiter < num_points:
                vertweights = skin_vertweights()
                vertweights.from_textfile(fileio, weightpointiter)
                self.vertweights.append(vertweights)
                weightpointiter = weightpointiter + 1
            
            fileio.ReadLine()

    def from_blender(self, blendermesh : bpy.types.Object, polymesh : xmd_base.XMD_basenodeinfo, 
                     bones : list[xmd_bone.XMD_bone],
                     xmdbone_blenderbone_map : defaultdict[xmd_bone.XMD_bone, bpy.types.Bone]):
        super().from_blender(polymesh)

        

        name_to_influence : defaultdict[str, int] = defaultdict(int)
        for i, bone in enumerate(bones):
            self.influences.append(bone.getNodeID())
            if not bone in xmdbone_blenderbone_map: continue
            name_to_influence[xmdbone_blenderbone_map[bone].name] = i

        group_to_influence : dict[int, int] = {}
        for vg in blendermesh.vertex_groups:
            inf = name_to_influence.get(vg.name)
            if inf is not None:
                group_to_influence[vg.index] = inf
        
        unweighted = 0
        for vert in blendermesh.data.vertices:
            pairs = [(group_to_influence[g.group], g.weight)
                     for g in vert.groups
                     if g.group in group_to_influence]

            pairs.sort(key=lambda p: p[1], reverse=True)   # keep the strongest
            total = sum(w for _, w in pairs)

            entry = skin_vertweights()
            entry.pointindex = vert.index
            if total > 0.0:
                for inf, w in pairs:
                    entry.weightlist.append(weightinfoentry(inf, w / total))   # renormalize to 1
            else:
                unweighted += 1
                entry.weightlist.append(weightinfoentry(0, 1.0))               # fallback, see below
            self.vertweights.append(entry)


    def _textfile_write(self, fileio : FileIO.TextFileIO):
        super()._textfile_write(fileio)
        fileio.WriteLine(f"\tnum_influences {len(self.influences)}")
        lineinfluences = "\t\t"
        for influence in self.influences:
            lineinfluences += f"{influence} "
        fileio.WriteLine(lineinfluences)
        fileio.WriteLine(f"\tnum_points {len(self.vertweights)}")
        fileio.WriteLine(f"\tweights")
        for vertweight in self.vertweights:
            weightline = f"\t\t{len(vertweight.weightlist)}\t"
            for weight in vertweight.weightlist:
                weightline += f"{weight.jointid} {weight.weightval} "
            fileio.WriteLine(weightline)