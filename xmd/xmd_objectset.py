from .. import FileIO
from . import xmd_base

class XMD_objectset(xmd_base.XMD_basenodeinfo):
    def __init__(self):
        super().__init__("OBJECT_SET")

        self.items = []
        self.annotation = ""

    def from_textfile(self, nodeheader, fileio : FileIO.TextFileIO):
        super().from_textfile(nodeheader, fileio)
        numitems = fileio.ReadLine().split()[1]
        for i in range(numitems):
            self.items.append(int(fileio.ReadLine().split()[0]))
        self.annotation = fileio.ReadLine().split()[1].replace("\"", "")

    def setitems(self, itemlist : list[xmd_base.XMD_basenodeinfo]):
        for item in itemlist:
            self.items.append(item.getNodeID())

    def _textfile_write(self, fileio : FileIO.TextFileIO):
        fileio.WriteLine(f"\tnum_items {len(self.items)}")
        for item in self.items:
            fileio.WriteLine(f"\t\t{item}")
        fileio.WriteLine(f"\tannotation \"{self.annotation}\"")