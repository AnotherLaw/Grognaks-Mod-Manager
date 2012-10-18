import zipfile as zf # This is included in GMM as well, no need to include when merging.
import os
import StringIO
import urllib

def openModDescription():
  # Get the mod that was clicked.
  pathToClickedMod = "/Users/Minh/dev/FTLDev/Freeze Missiles/Freeze Missiles.zip"#Whatever value it is when clicked#
  data = urllib.urlopen(pathToClickedMod).read()
  ss = zf.ZipFile(StringIO.StringIO(data))
  fP = ss.open("ModReadme")
  return fP
# read the lines.

words = openModDescription().readlines()
print words
