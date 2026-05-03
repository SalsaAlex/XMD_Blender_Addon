import io

class TextFileIO:
    
    #filepath : string
    #mode : string. options: "r", "w", "rb", "wb"
    def __init__(self, filepath, iomode):
        self.filePath = filepath
        self.fileIOHandle = io.open(self.filePath, iomode, encoding="utf-8")
    
    def __del__(self):
        self.fileIOHandle.close()

    def ReadLine(self):
        return self.fileIOHandle.readline()
    
    def WriteLine(self, string : str):
        self.fileIOHandle.write(string)
        

