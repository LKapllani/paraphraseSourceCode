from newSolutions import *
import itertools
import glob
import sys
import os

path = str(os.getcwd())+'/'+str(sys.argv[1])+'/'+str(sys.argv[2])+'/*'
dirpath = str(os.getcwd())+'/'+str(sys.argv[1])+'/'+str(sys.argv[2])

files = glob.glob(path)

firstFile = []
for name in files:
    firstFile.append(name)
secondFile = firstFile

combinedFiles = list(itertools.product(firstFile, secondFile))
#Create a combination of two C++ files, given the list of all solutions for a problem.

for i in combinedFiles:
    if i[0] == i[1]:
        combinedFiles.remove(i)
#Remove combinations of C++ files with itself.

for i, pair in enumerate(combinedFiles):
	try:
		newSolutions(pair[0],pair[1],dirpath +'combination'+str(i+1)+'/',i+1)
	except:
		print('error -- '+str(pair))
	print(i)
#For each pair call the newSolutions fuction. 