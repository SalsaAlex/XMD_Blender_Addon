import io

class TextFileIO:
    
    #filepath : string
    #mode : string. options: "r", "w", "rb", "wb"
    def __init__(self, filepath, iomode):
        self.filePath = filepath
        self.fileIOHandle = io.open(self.filePath, iomode, encoding="utf-8")
        self.prevtell = self.fileIOHandle.tell()
    
    def __del__(self):
        self.fileIOHandle.close()

    def ReadLine(self):
        self.prevtell = self.fileIOHandle.tell()
        return self.fileIOHandle.readline()

    #move back 1 line
    def Rewind_Line(self):
        self.fileIOHandle.seek(self.prevtell)
    
    def WriteLine(self, string : str):
        self.fileIOHandle.write(string + "\n")
        

