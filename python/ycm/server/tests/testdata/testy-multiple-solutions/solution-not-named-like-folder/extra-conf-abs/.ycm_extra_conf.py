
import os

def CSharpSolutionFile(path):
  #remove '.ycm_extra_conf.py' and 'extra-conf-abs' from filename
  location=os.path.dirname(__file__)
  location=os.path.dirname(location)
  return os.path.join(location,'testy2.sln')

