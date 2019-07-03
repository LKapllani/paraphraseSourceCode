import re
import numpy as np
import os
import errno
import shutil
import itertools
import glob
import sys


#Tokenizing the paraphrases using regular expression.
def init_scanner():
    kwlist = ["asm","if","else","new","this","auto","enum","operator","throw","bool","explicit","private","true","break","export","protected","try","case","extern","public","typedef","catch","false","register","typeid","char","float","reinterpret_cast","typename","class","for","return","union","const","friend","short","unsigned","const_cast","goto","signed","using","continue","if","sizeof","virtual","default","inline","static","void","delete","int","static_cast","volatile","do","long","struct","wchar_t","double","mutable","switch","while","dynamic_cast","namespace","template","And","bitor","not_eq","xor","and_eq","compl","or","xor_eq","bitand","not","or_eq"]
    s = re.Scanner([
    (r"\"[^\"]*?\"", lambda scanner, token:("String",token)),
    (r"'[^']*?'", lambda scanner, token:("String",token)),
    (r"#.*\n", lambda scanner, token:("Preprocessor Statement",token.strip())),
    (r"//.*(\n|\Z)", lambda scanner, token:("Comment",token.strip())),
    (r"/\*.*\*/", lambda scanner, token:("Comment",token.strip())),
    (r".*\?.*\:.*", lambda scanner, token:("Ternary",token.strip())),
    (r"\s*({})".format('|'.join(kwlist)), lambda scanner, token:("Keyword",token.strip())),
	(r"#.*", lambda scanner, token: ("Keyword", token.strip())),
    (r"[a-zA-Z_\.]+[0-9]*", lambda scanner, token:("String Literal",token)),
    (r"[0-9]+\.[0-9]+", lambda scanner, token:("Float Literal", token)),
    (r"[0-9]+", lambda scanner, token:("Integer literal", token)),
    (r"\@.*(\s|\n)", lambda scanner, token:("Annotation", token)),
    (r"\(",lambda scanner, token:("Open Parentheses",token)),
    (r"\)",lambda scanner, token:("Close Parentheses",token)),
    (r"\[",lambda scanner, token:("Open Bracket",token)),
    (r"\]",lambda scanner, token:("Close Bracket",token)),
    (r"\{",lambda scanner, token:("Open Curly Brace",token)),
    (r"\}",lambda scanner, token:("Close Curly Brace",token)),
    (r"(\+=|-=|/=|\*=|>>=|<<=|\|=|\&=)", lambda scanner, token:("Assignment Operator",token)),
    (r"(==|>|<|>=|<=|!=|!)", lambda scanner, token:("Comparator",token)),
    (r"=", lambda scanner, token:("Assignment",token)),
    (r"(\+|\-|/|\*|\%)+", lambda scanner, token:("Operation",token)),
    (r"\s+", lambda scanner, token:("Whitespace",token)),
    (r"(,|:|;|\\)", lambda scanner, token:("Punctuation",token)),
    (r"(\&|\||>>|<<|\^=)", lambda scanner, token:("Bit Operation",token))
    ])
    
    return s
    

def getFileLines(fname):
    with open(fname) as f:#, encoding="utf-8") as f:
        content = f.readlines()

    #Remove comments and white space
    new_content = []
    for line in content:
        line = line.strip()
        if len(line)>2:
            #cpp
            if fname[-4:]=='.cpp' and line[0] != '/' and line[1] != '/':
                new_content.append(line)
            #python
            if fname[-3:]=='.py' and line[0] != '#' and line[:3] != "'''":
                new_content.append(line)

    return new_content


#Determine the edit distance between two strings.
def levenshtein(s1, s2):

    if len(s1) < len(s2):
        return levenshtein(s2, s1)

    if len(s2) == 0:
        return len(s1)

    d = []
    s = []
    ins = []
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            # j+1 instead of j since previous_row and current_row are one character longer than s2
            insertions = previous_row[j + 1] + 1 
            deletions = current_row[j] + 1       
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]
    


def sharedSmallestLevenshteinPairs(f1sentences,f2sentences):
	pairs1 = []
	for s1 in f1sentences:
		p = []
		min_diff = float('Inf')
		for s2 in f2sentences:
			diff = levenshtein(s1,s2)
			if diff < min_diff:
				min_diff = diff
				p = [s1,s2]
		pairs1.append(p)
	#Find the minimum edit distance between the each line of file 1 to file 2.

	pairs2 = []
	for s2 in f2sentences:
		p = []
		min_diff = float('Inf')
		for s1 in f1sentences:
			diff = levenshtein(s1,s2)
			if diff < min_diff:
				min_diff = diff
				p = [s2,s1]
		pairs2.append(p)
	#Find the minimum edit distance between the each line of file 2 to file 1.
	
	sharedPairs = [pair for pair in pairs1 if pair[::-1] in pairs2]
	#CrossCheckedPairs are pairs that are in both pairs1 and pairs2

	
	pairs_temp = []
	for p in sharedPairs:
		if p[0] != p[1]:
			pairs_temp.append(p)
	sharedPairs = pairs_temp
	#Check that pairs are not identical
	
	return sharedPairs

def getVars(pair):

	'''
	varlist=[]
	for tok in p1:
		if tok[0] == 'String Literal':
			varlist.append(tok[1])
	return varlist
	'''
	return [pair[1] for pair in pair if pair[0] == 'String Literal']
	#This does the same as above, but leaving it for readablity.


def newPhrases(s1,s2):
    s = init_scanner()
    p1 = s.scan(s1)[0]
    p2 = s.scan(s2)

    s = init_scanner()
    p1 = s.scan(s1)[0]
    p2 = s.scan(s2)[0]
    #Get a tokenized (key,value) tuple for each token in a paraphrase line.

    vars1 = getVars(p1)
    vars2 = getVars(p2)
    #Get the variables from each paraphrase line.

    p1Value = [x[1] for x in p1]
    p2Value = [x[1] for x in p2]
    #Get the values for each paraphrase line.

    if len(vars1) == len(vars2) and len(np.unique(vars1)) == len(np.unique(vars1)) and len(vars1) != 0:
    	#Check that the paraphrase pair has the same number of variables/function names.
        varPairs = list(zip(vars1, vars2))
        varPairs = list(set(varPairs))

        newPOneValues = swap(p2Value, varPairs)
        newPTwoValues = swap(p1Value, varPairs)

        return newPOneValues, newPTwoValues
    else:
        print('empty???')
        return [],[]


def swap(pValue,varPairs):
#Given a phrase and pairs of variables swap their variables to create two new phrases.
    newPhrase = [''] * len(pValue)
    modifiedFlag = np.zeros(len(pValue))

    for (var1,var2) in varPairs:
        for i,token in enumerate(pValue):
            if modifiedFlag[i] != 1:
                if token == var1:
                    newPhrase[i] = var2
                    modifiedFlag[i] = 1
                elif token == var2:
                    newPhrase[i] = var1
                    modifiedFlag[i] = 1
                else:
                    newPhrase[i] = token
    if newPhrase == []:
        return pValue
    return newPhrase

def newSolutions(file1,file2): #,dirName,combinationNumber):

    testDatafile='A-small-practice.in'
    os.system('$(g++ '+file1+' -w -o'+file1+'.works)')
    os.system('$(./'+file1+'.works < '+testDatafile+' > '+file1+'.out & sleep 5; kill $!;)')
    os.system('$(rm '+file1+'.works)')
    os.system('$(g++ '+file2+' -w -o'+file2+'.works)')
    os.system('$(./'+file2+'.works < '+testDatafile+' > '+file2+'.out & sleep 5; kill $!;)')
    os.system('$(rm '+file2+'.works)')

    filePhraseDict={}
    workingParaphrases=[]
    fileNumber=1

    f1sentences = getFileLines(file1)
    f2sentences = getFileLines(file2)

    #Identify the paraphrase pairs for each file combination calling the sharedSmallestLevenshteinPairs.
    pairs = sharedSmallestLevenshteinPairs(f1sentences, f2sentences)

    for pair in pairs:

        #Keeping track of the file name a certain phrase comes from.
        filePhraseDict[pair[0]] = file1
        filePhraseDict[pair[1]] = file2
        
        #Generating new paraphrases by calling the newPhrases function.
        newPOneValues, newPTwoValues =  newPhrases(pair[0],pair[1])
        phrases = [newPOneValues, newPTwoValues]

        #Non-empty
        if newPOneValues != []:
            for i,phrase in enumerate(phrases):

                newPhase = ''.join(map(str, phrase)).replace(" ", "")
                currentPhase = pair[i].replace(" ", "")

                #Not syntatically equivilant paraphrases.
                if newPhase != currentPhase :
                    print(currentPhase, 'becomes' ,newPhase)

                    currentFile = filePhraseDict[pair[i]];

                    newFile=''.join(currentFile.split('.')[:-1])+'_' + str(fileNumber)+".cpp"

                    #Generate new .cpp files using the new generated paraphrases.
                    with open(currentFile) as f:
                        with open(newFile, "w") as f1:
                            for line in f:
                                if line.lstrip().strip('\n') == pair[i]:
                                    f1.write(' '.join(map(str, phrase)) + '\n')
                                else:
                                    f1.write(line)


                        fileNumber += 1
                        f1.close()
                        f.close()

                    #print('$(g++ '+newFile+' -o '+newFile+'.works)')
                    os.system('$(g++ '+newFile+' -w -o'+newFile+'.works)')

                    exists = os.path.isfile(newFile+'.works')
                    if exists:
                        print()
                        print('Compiles [Syntatically Correct]')
                        print()
                        #test that that file is correct
                        testDatafile='A-small-practice.in'
                        os.system('$(./'+newFile+'.works < '+testDatafile+' > '+newFile+'.out & sleep 5; kill $!;)')
                        os.system('$(rm '+newFile+'.works)')

                        exists = os.path.isfile(newFile+'.out')
                        if exists:

                            print()
                            print('Gives output in given time. [Reasonable Runtime]')
                            print()

                            with open(str(newFile+'.out')) as f:#, encoding="utf-8") as f:
                                content = f.readlines()

                            with open(str(currentFile+'.out')) as f_correct:
                                correct_content =  f_correct.readlines()


                            correctOutput=True
                            for j in range(len(correct_content)):
                                if(str(correct_content[j].replace(" ", ""))!=str(content[j].replace(" ", ""))):
                                    correctOutput=False
                                    break
                            
                            
                            if correctOutput:
                                workingParaphrases.append((i,pair[i],' '.join(map(str, phrase))))
                            
                            os.system('$(rm '+newFile+'.out)')



                        else:
                            print()
                            print('runtime failure')
                            print()


                    else:
                        print()
                        print('does not compile')
                        print()
                        # Keep presets

                    os.system('$(rm '+newFile+'.cpp)')

    print('end')
    for w in workingParaphrases:
        print(w)

    #make new copy of originals to edit
    newFile1 = ''.join(file1.split('.')[:-1])+'_combined.cpp'
    newFile2 = ''.join(file2.split('.')[:-1])+'_combined.cpp'

    os.system('$(cp '+file1+' '+newFile1+')')
    os.system('$(cp '+file2+' '+newFile2+')')


    #instead do each file and add each 
    with open(file1) as f:
        with open(newFile1, "w") as f1:
            for line in f:
                subbed=False
                for w in workingParaphrases:
                    if w[0]==0 and line.lstrip().strip('\n') == w[1] and subbed==False:
                        f1.write(w[2] + '\n')
                        subbed=True
                if subbed==False:
                    f1.write(line)

    f1.close()
    f.close()


    with open(file2) as f:
        with open(newFile2, "w") as f1:
            for line in f:
                subbed=False
                for w in workingParaphrases:
                    if w[0]==1 and line.lstrip().strip('\n') == w[1] and subbed==False:
                        f1.write(w[2] + '\n')
                        subbed=True
                if subbed==False:
                    f1.write(line)
    f1.close()
    f.close()


    '''
    #make all the swaps
    for w in workingParaphrases:
        if w[0]==0:
            with open(newFile1, "w") as f1:
                for line in f1:
                    if line.lstrip().strip('\n') == w[1]:
                        f1.write(w[2] + '\n')
                    else:
                        f1.write(line)

            f1.close()

        if w[0]==1:
            with open(file2) as f:
            with open(newFile2, "w") as f2:
                for line in f2:
                    if line.lstrip().strip('\n') == w[1]:
                        f2.write(w[2] + '\n')
                    else:
                        f2.write(line)

            f2.close()



    '''


    '''
    #Generate new .cpp files using the new generated paraphrases.
    currentFile = filePhraseDict[pair[i]];
    with open(currentFile) as f:
        with open(newFile, "w") as f1:
            for line in f:
                if line.lstrip().strip('\n') == pair[i]:
                    f1.write(' '.join(map(str, phrase)) + '\n')
                else:
                    f1.write(line)


        fileNumber += 1
        f1.close()
        f.close()
    '''

        



    '''
    try:
        os.mkdir(dirName)
    except OSError as exc:
        if exc.errno != errno.EEXIST:
            raise
        pass

    for pair in pairs:

        #Keeping track of the file name a certain phrase comes from.
        filePhraseDict[pair[0]] = file1
        filePhraseDict[pair[1]] = file2
        
        #Generating new paraphrases by calling the newPhrases function.
        newPOneValues, newPTwoValues =  newPhrases(pair[0],pair[1])
        phrases = [newPOneValues, newPTwoValues]

        #Non-empty
        if newPOneValues != []:
            for i,phrase in enumerate(phrases):

                newPhase = ''.join(map(str, phrase)).replace(" ", "")
                currentPhase = pair[i].replace(" ", "")

                #Not syntatically equivilant paraphrases.
                if newPhase != currentPhase :
                    currentFile = filePhraseDict[pair[i]];
                    shutil.copy(currentFile, dirName)

                    #Save the edited pairs in a txt file.
                    filename = 'solution' + str(combinationNumber) + '-' + str(fileNumber)+"_pairs.txt"
                    filepath = os.path.join(dirName, filename)
                    with open(filepath, "w") as f1:
                        for token in pair[i]:
                            f1.write(str(token))
                        f1.write(' ')
                        for token in phrase:
                            f1.write(str(token))
                        f1.write('\n')


                    #Generate new .cpp files using the new generated paraphrases.
                    with open(currentFile) as f:
                        filename = 'solution' + str(combinationNumber) + '-' + str(fileNumber)+".cpp"
                        filepath = os.path.join(dirName, filename)
                        with open(filepath, "w") as f1:
                            for line in f:
                                if line.lstrip().strip('\n') == pair[i]:
                                    f1.write(' '.join(map(str, phrase)) + '\n')
                                else:
                                    f1.write(line)


                        fileNumber += 1
                        f1.close()
                        f.close()
    '''
                       
''' 
def automaticSolutions():
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
'''


if __name__ == '__main__':
    newSolutions(sys.argv[1],sys.argv[2])



