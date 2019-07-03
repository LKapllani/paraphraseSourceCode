from editPairs import *
import os
import errno
import shutil


def newSolutions(file1,file2,dirName,combinationNumber):

    filePhraseDict = {}

    fileNumber = 1

    f1sentences = getFileLines(file1)
    f2sentences = getFileLines(file2)

    #Identify the paraphrase pairs for each file combination calling the sharedSmallestLevenshteinPairs.
    pairs = sharedSmallestLevenshteinPairs(f1sentences, f2sentences)

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
