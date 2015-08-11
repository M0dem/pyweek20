
import os


dataPy = os.path.abspath(os.path.dirname(__file__))
dataDir = os.path.normpath(os.path.join(dataPy, "..", "data"))

# Determine the path to a file in the data directory.
def getPath(fName):
    return os.path.join(dataDir, fName)
