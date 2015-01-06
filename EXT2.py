#----------------------------------

#DEBUG VARIABLES 

DEBUG = False
ERROR = "Incorrect Usage, Correct format is function, arg1, arg2 [, additional args]"
FUNCT = 0
FUNCTIONS = ["ext2_cp", "ext2_mkdir", "ext2_ln", "ext2_rm"]

#----------------------------------

#KEY VARIABLES

#INODE_SIZE = 128
INODE_SIZE = 0x80
#BLOCK_SIZE = 1024
BLOCK_SIZE = 0x400

#----------------------------------
#KEY ADDRESSES

#SuperBlock, hex 400, dec 1024
SUPERADDR = 0x400
#BlockDescriber, hex 800, dec 2048
BLOCKDESCADDR = 0x800
#BlockBitMap, hex c00, dec 3072
BLOCKBITMAP = 0xc00
#InodeBitMap, hex 1000, dec 4096
INODEBITMAP = 0x1000
#InodeTable, hex 1400, dec 5120
INODETABLE = 0x1400
#Current INDOETABLE refers to the block that is currently being filled with inodes
CURRINODETABLE = 0x1400
#DATASTART

#----------------------------------
           
import sys   
import os

def readSuper(version, disk):
    disk.seek(SUPERADDR)
    superBlock = disk.read(BLOCK_SIZE)
    
    #Populate the total Inodes
    totINodes = (superBlock[0:4])
    iNodes = totINodes[0] + (totINodes[1]*16) + (totINodes[2]*(16*16)) + (totINodes[3]*(16*16*16))
    TOTI = iNodes
    
    totBlocks = (superBlock[4:8])
    blocks = totBlocks[0] + (totBlocks[1]*16) + (totBlocks[2]*(16*16)) + (totBlocks[3]*(16*16*16)) 
    TOTB = blocks
    
    unAllocBlocks = (superBlock[12:16])
    unblocks = unAllocBlocks[0] + (unAllocBlocks[1]*16) + (unAllocBlocks[2]*(16*16)) + (unAllocBlocks[3]*(16*16*16)) 
    UNB = unblocks
    
    unAllocNodes = (superBlock[16:20])
    unNodes = unAllocNodes[0] + (unAllocNodes[1]*16) + (unAllocNodes[2]*(16*16)) + (unAllocNodes[3]*(16*16*16)) 
    UNN = unNodes
    
    if(version == 'TOTI'):
        return TOTI    
    if(version == 'TOTB'):
        return TOTB    
    if(version == 'UNB'):
        return UNB
    if(version == 'UNN'):
        return UNN

#Used to update the superBlock    
def writeSuper(num, version, disk):
    
    TOTI = readSuper('TOTI', disk)
    TOTB = readSuper('TOTB', disk)
    UNB = readSuper('UNB', disk)
    UNN = readSuper('UNN', disk)
    
    if(version == 'toti'):
        if(num+TOTI < 0):
            retur        
        w = (num*16 + TOTI).to_bytes(4, byteorder='little')
        disk.seek(SUPERADDR)
        disk.write(w)
    if(version == 'totb'):
        if(num+TOTB < 0):
            return        
        w = (num + TOTB).to_bytes(4, byteorder='little')
        disk.seek(SUPERADDR+4)
        disk.write(w)
    if(version == 'unb'): 
        if(num+UNB < 0):
            return        
        w = (num + UNB).to_bytes(4, byteorder='little')
        disk.seek(SUPERADDR+12)
        disk.write(w)
    if(version == 'unn'):
        #catch
        if(num+UNN < 0):
            return
        w = (num + UNN).to_bytes(4, byteorder='little')
        disk.seek(SUPERADDR+16)
        disk.write(w)
             
#Takes an Inode's address and returns the iBlocks Data Address
def jumpIntoIblocks(iNodeAddress, disk):
    #Bring up the iNode's iblocks
    disk.seek(iNodeAddress + 40)
    
    #jump to the i blocks
    val = disk.read(4)
    intval = int.from_bytes(val, byteorder="little")
    
    #Now jump to the iNodes's contents
    address = intval * BLOCK_SIZE
    return address    


def calcBlocks(size):
    blocks = 1
    tmp = size
    while(tmp > BLOCK_SIZE):
        tmp = size - BLOCK_SIZE
        blocks = blocks + 1 
    return blocks
        

#RETURNS THE INODE BLOCK THAT THE DESIRED DIRECTORY IS STORED IN
def getDirectory(path, disk):
    if(DEBUG):
        print("Getting the directory")
       
    #Root Directory found at Inode table + table header size
    ROOTDIRECTORY = INODETABLE + INODE_SIZE
    
    
    #Break the path into it's components
    sPath = path.split("/")
    if (sPath[len(sPath) - 1] == ''):
        sPath.pop(len(sPath) - 1)
        
    
    #Bring up the Root's iblocks
    address = jumpIntoIblocks(ROOTDIRECTORY, disk)
    
    #start the process on each path section
    for j in range(1, len(sPath)):
    
        disk.seek(address)
        val = disk.read(BLOCK_SIZE)
        
        #scan for the given name
        curr = 0
        #State machine time 
        #1, looking for inode
        #2, looking for total size
        #3, looking for name length
        #4, looking for type indicator
        #5, collecting the name characters
        #Make sure that we do not go above size
        
        while(curr<80):
            inodeTotal = 0
            inodeTotal = inodeTotal + val[curr]
            inodeTotal = inodeTotal + (val[curr + 1] * 16)
            inodeTotal = inodeTotal + (val[curr + 2] * (16*16))
            inodeTotal = inodeTotal + (val[curr + 3] * (16*16*16))
            if(DEBUG):
                print("The Inode found is: %d" % inodeTotal)
            
            totalSize = 0
            totalSize = totalSize + (val[curr + 4])
            totalSize = totalSize + (val[curr + 5] * 16)
            #totalSize = totalSize + (val[curr + 5])
            if(DEBUG):
                print("The Total size is: %d" % totalSize)
            
            nameLength = val[curr + 6]
            if(DEBUG):
                print("The name Length is: %d" % nameLength)
            
            typeInd = val[curr+7]
            if(DEBUG):
                print(val[curr+7])
            
            #Compile the name
            name = ''
            for i in range(0, nameLength):
                name = name + chr(val[ curr+ 8 + i ])
            if (nameLength %2 != 0):
                curr = curr+1
            if(DEBUG):
                print("The Compiled name is: %s" % name)
                       
            #Check if the name is a match to the target directory
            
            if (name == sPath[len(sPath) -1] and j == len(sPath)-1):
                #MATCH FOUND - SUCCESSFUL RETURN
                if(DEBUG):
                    print("Final destination Match Found")
                #USE -1 to offset the 0 start
                return (inodeTotal-1)
            elif(name == sPath[j]):
                if(DEBUG):
                    print("Intermediate directory Match Found")
                #This sPath[j] is the directory to jump into
                #jump into the directory and let j increment
                iNodeAddress = INODETABLE + (INODE_SIZE*(inodeTotal - 1))
                address = jumpIntoIblocks(iNodeAddress, disk)
                break
            
            
            #NO MATCH SO search the next
            curr = curr + 8 + nameLength + 2
    if(DEBUG):
        print("No resulting directory Found")
    return None

import math
def releaseBit(position, version, disk):
    #release the bit back into the bitMap
    if (version == 'i'):
        initval = INODEBITMAP
    elif (version == 'b'):
        initval = BLOCKBITMAP
    else:
        print("Invalid use: parameters are i or b")
        return None
    
    #calculate the skipping
    small = False
    seekDist = 0
    temp = position
    moves = temp // 16
    remainder = temp % 16
    
    if(remainder > 8):
        #second half
        remainder = remainder -8
        seekDist = 2
        #small = True

    disk.seek(initval + position + seekDist)
    val = disk.read(2)
    chosen = 0
    
    oVal = val[chosen]
    releaseNum = int(math.pow(2, remainder-1))
    
    result = int(oVal - releaseNum)
    
    bresult = (result).to_bytes(1, byteorder='little')
    
    if (not small):
        fin = (bresult + val[1].to_bytes(1, byteorder='little'))
    else:
        fin = (val[0].to_bytes(1, byteorder='little') + bresult)
    disk.seek(initval + position + seekDist)
    disk.write(fin)
    
    #----- ----- ----- -----INCREMENT NODES FREE IN THE SUPERBLOCK ----- ----- ----- -----
    writeSuper(1, 'unn', disk)
    
    
#def bitMapReserve(version, position, disk):
    #if(DEBUG): 
        #print("IN BITMAP RESERVE")
    ##release the bit back into the bitMap
    #if (version == 'i'):
        #initval = INODEBITMAP
    #elif (version == 'b'):
        #initval = BLOCKBITMAP
    #else:
        #print("Invalid use: parameters are i or b") 
        #return None
    
    ##calculate the skipping
    #small = False
    #seekDist = 0
    #temp = position
    #moves = temp // 16
    #remainder = temp % 16

    #print(version)
    #print(temp)
    #print(moves)
    #print(remainder)
    
    #if(remainder > 8):
        #remainder = remainder -8
        #seekDist = 1
        
    #disk.seek(initval + (moves*4) + seekDist)
    #val = disk.read(4)
    ##val = b'\x08\x00'
    #print(val)
    #chosen = 0
    #oVal = val[chosen]
    #print(oVal)
    #releaseNum = int(math.pow(2, remainder-1))
    #print(releaseNum)
    #result = int(oVal + releaseNum)    
    #print(result)
    #bresult = (result).to_bytes(1, byteorder='little')    
    #if (not small):
        #fin = (bresult + val[1].to_bytes(1, byteorder='little'))
    #else:
        #fin = (val[0].to_bytes(1, byteorder='little') + bresult)
    #disk.seek(initval + (moves*4) + seekDist)
    #disk.write(fin)
    #if(fin == b'\xff\xff' and version == 'i'):
        #print("Filled the section")
        #disk.seek(initval + (moves*4) + seekDist)
        #disk.write(b'\x00\x00')
    #print(version)
    #print("\n")
    #print(fin)
    #print("\n")
    
def bitMapReserve(version, position, disk):
    
    #set the version
    if (version == 'i'):
        initval = INODEBITMAP
    elif (version == 'b'):
        initval = BLOCKBITMAP
    else:
        print("Invalid use: parameters are i or b")
        return None

    #The limit is defined by the entire row in the bitmap
    #This is therefore 8 * 16
    limit = INODEBITMAP + 0x10
    
    fullChar = position // 16
    posLeft = position % 16
    
    #Check that we are not surpassing the bitmap, probably not necessary
    if (initval + fullChar >= limit):
        print("Exceeded memory, disk out of space")
        return None
    
    if(posLeft == 0):
        #filling case
        disk.seek(initval+(fullChar*2)-2)
        disk.write(b'\xff\xff')
        disk.seek(initval+(fullChar*2))
        disk.write(b'\x00\x00')
        #----- ----- ----- ----- ADD ANOTHER 16 bits to the superBlock ------ ------ ----- -----
        writeSuper(1, 'toti', disk)
        return 1
    
    disk.seek(initval+(fullChar*2))
    val = disk.read(2)
    
    #increment the byte, going to use an if block
    disk.seek(initval+(fullChar*2))
    #It's not elegant but it does the job
    #order (smallest lowest)= \21\43
    if(val == b'\x00\x00'):
        disk.write(b'\x01\x00')
    elif(val == b'\x01\x00'):
        disk.write(b'\x03\x00')
    elif(val == b'\x03\x00'):
        disk.write(b'\x07\x00')        
    elif(val == b'\x07\x00'):
        disk.write(b'\x0f\x00')
    elif(val == b'\x0f\x00'):
        disk.write(b'\x1f\x00')        
    elif(val == b'\x1f\x00'):
        disk.write(b'\x3f\x00')
    elif(val == b'\x3f\x00'):
        disk.write(b'\x7f\x00')
    elif(val == b'\x7f\x00'):
        disk.write(b'\xff\x00')
    elif(val == b'\xff\x00'):
        disk.write(b'\xff\x01')               

    elif(val == b'\xff\x01'):
        disk.write(b'\xff\x03')        
    elif(val == b'\xff\x03'):
        disk.write(b'\xff\x07')        
    elif(val == b'\xff\x07'):
        disk.write(b'\xff\x0f')
    elif(val == b'\xff\x0f'):
        disk.write(b'\xff\x1f')
    elif(val == b'\xff\x1f'):
        disk.write(b'\xff\x3f')
    elif(val == b'\xff\x3f' or val == b'\xff?'):
        disk.write(b'\xff\x7f')    
    elif(val == b'\xff\x7f'):
        disk.write(b'\xff\xff')
    elif (val == b'\xff\xff'):
        disk.write(b'\x01\x00')       
    else:
        print("Error: unrecognised bit format, Unstandard Fragmentation detected")
        return None
    
    if (version == 'i'):
        writeSuper(-1, 'unn', disk)    
    if (version == 'b'):
        writeSuper(-1, 'unb', disk)

def bitSplit(num):
    #used for bitmapping
    pos0 = 0
    pos1 = 0
    pos2 = 0
    pos3 = 0
    pos4 = 0
    pos5 = 0
    pos6 = 0
    pos7 = 0
    
    temp = num
    if (temp >= 128):
        pos0=1
        temp -= 128
    if (temp >= 64):
        pos1=1
        temp -= 64
    if (temp >= 32):
        pos2=1
        temp -= 32
    if (temp >= 16):
        pos3=1
        temp -= 16
    if (temp >= 8):
        pos4=1
        temp -= 8
    if (temp >= 4):
        pos5=1
        temp -= 4
    if (temp >= 2):
        pos6=1
        temp -= 2
    if (temp >= 1):
        pos7=1
        temp -= 1
    bits = []
    bits.append(pos7)
    bits.append(pos6)
    bits.append(pos5)
    bits.append(pos4)
    bits.append(pos3)
    bits.append(pos2)
    bits.append(pos1)
    bits.append(pos0)
    return bits

def scanFree(version, disk):
    
    #Scan through the bit map
    curr = 0
    retPos = 1
    found = False    
    
    #THE PLAN:
    # SEARCH THE BITMAP BYTE BY BYTE
    # IF THE BYTE IS NOT MAXED OUT, I.E. FF FF THEN WE CHECK IT
    # CHECK THE LEAST SIGNIFICANT NON 1 BIT. 
    # CALCULATE HOW FAR IN THE FREE BIT IS USING RETPOS
    # RETURN RETPOS AS AN INDEX TO THE FREE POSITION 
    
    # Initialise the location
    if (version == 'i'):
        initval = INODEBITMAP
    elif (version == 'b'):
        initval = BLOCKBITMAP
    else:
        print("Invalid use: peramiters are i or b")
        return None
    
    #Start the seach
    while (not found):
        disk.seek(initval+curr)
        
        val = disk.read(2)           
        intval = int.from_bytes(val, byteorder="little")

        # If not FF FF then there is a free bit
        if(val != b'\xff\xff'):    
            #found a free bit
            found = True
                        
            #CHECK THE BITS IN LEAST SIGNIFICANT ORDER FOR A FREE BIT
            stVal = str(val)
            
            #Need to case check 3f
            if (stVal[2] == '?'):
                firstCheck = 'f'
                secondCheck = '3'
                thirdCheck = stVal[4]
                fourthCheck = stVal[3]
                
            elif (stVal[6] == '?'):
                #4 5 are earliest
                firstCheck = stVal[5]
                secondCheck = stVal[4]                
                thirdCheck = 'f'
                fourthCheck = '3'
            else:
                if(len(stVal)>9):
                    firstCheck = stVal[5]
                    secondCheck = stVal[4]
                    thirdCheck = stVal[9]
                    fourthCheck = stVal[8]
                else:
                    return retPos+15
                
            
            if (firstCheck != 'f'):
                
                #Where is the first free bit
                check = firstCheck
                if (check == '0'):
                    return retPos
                elif (check == '1'):
                    return retPos+1                
                elif(check == '3'):
                    return retPos+2
                elif(check == '7'):
                    return retPos+3                    
                    
            elif (secondCheck != 'f'):
                
                #Where is the first free bit
                check = secondCheck
                if (check == '0'):
                    return retPos+4
                elif (check == '1'):
                    return retPos+5                
                elif(check == '3'):
                    return retPos+6
                elif(check == '7'):
                    return retPos+7
                    
            elif (thirdCheck != 'f'):          
                
                #Where is the first free bit
                check = thirdCheck
                if (check == '0'):
                    return retPos+8
                elif (check == '1'):
                    return retPos+9                
                elif(check == '3'):
                    return retPos+10
                elif(check == '7'):
                    return retPos+11
                
            elif (fourthCheck != 'f'):
                check = fourthCheck
                if (check == '0'):
                    return retPos+12
                elif (check == '1'):
                    return retPos+13                
                elif(check == '3'):
                    return retPos+14
                elif(check == '7'):
                    return retPos+15
            else:
                print("new block")
            
        
        #increment to the next byte
        retPos = retPos + 16
        curr = curr+2
        #testing to break the should end at the end of the block
        if(curr > 127):
            return None
        
    
    
def freeCheck(addr, freeNum, disk):
    #check that the first byte is zero-d, should not trigger, but for safety
    disk.seek(addr)
    
    val= disk.read(4)
    counter = 0
    while(1):
        if (val[0] == 0x00 and val[1] == 0x00 and val[2] == 0x00 and val[3] == 0x00):
            return freeNum
        else:
            #Should never get here
            #If for some reason this is taken take the next one
            freeNum = freeNum+1
            if(counter > 23):
                break
            addr = addr + INODE_SIZE
            disk.seek(addr)
            val= disk.read(4)
            counter = counter +1
            #recusive fix
            
            #return freeCheck(addr, freeNum+1, disk)
            return freeCheck(addr+0x80, freeNum+1, disk)
      

def readTillEnd(destDirBlocks, disk):
    if(DEBUG):
        print("Enter readTillEnd")
        
    header = 8
    nSize = 0
    pos = 0
    count = 0
    
    disk.seek(destDirBlocks)
    
    while(1):
        val = disk.read(8)
        nSize = val[6]
        
        if(nSize == 0):
            return (destDirBlocks)
        else:
            if(nSize%2 != 0):
                nSize = nSize +1
                
            destDirBlocks = destDirBlocks + nSize + header +2
            disk.seek(destDirBlocks)

            count=count+1
            
        if(count > 100):
            print("No end found: ")
            return None
    
    


def ext2_cp(*args):
    #ext2_cp: This program takes three command line arguments. The first is the name of an ext2 formatted virtual disk. The second is the path to a file on your
    #native operating system, and the third is an absolute path on your ext2 formatted disk. The program should work like cp, copying the file on your native file
    #system onto the specified location on the disk. If the specified file or target location does not exist, then your program should return the appropriate error.
    
    #ext2_cp("C:/Users/Adam/Documents/369/A3/onedirectory.img", "C:/Users/Adam/Documents/369/A3/b.txt", "/testdirectory")
    #copy paste for faster testing
    
    #Error check params
    if (len(args) != 3):
        print("Incorrect parameter numbers")
        return
    
    #Setup the args
    ext2 = args[0]
    filePath = args[1]
    ext2Path = args[2]

    #Open the image
    disk = open(ext2, "r+b") 
    
    #COPY PROCESS:
    # 1. Check that the file exists
    # 2. Check that the target exists
    # 3. Check that the specified location exists
    # 4. Find free Space
    # 5. Find destination
    # 6. Dump the file
    # 7. Consult the bitmap for an inode
    # 8. Aquire a dataSpace for the hexdumped data
    # 10. Write the Hexdump data into the dataSpace
    # 9. Write the iNode information into the iNode Block
    # 11. Write the iNode information into parent directory
    # 12. Get a D- in assignment 
    
    #1. 
    if ( not (os.path.isfile(filePath))):
        print("file not found: %s" % filePath)
        return None
    #2
    if(ext2Path[0] != "/"):
        print("Please format the ext2 path to start with a /")
        return None
    
    #3
    destDir = getDirectory(ext2Path, disk)
    if(destDir == None):
        print("Directory does not exist")
        return
    if(DEBUG):
        print("Destination directory is: ")
        print(destDir)
    
    #This is where the directory's information is held
    destDirLocation = ((destDir) * INODE_SIZE) + INODETABLE
    #This is where the directory's contents is held
    #i.e. this is where the completed information will be placed
    destDirBlocks = jumpIntoIblocks(destDirLocation, disk)
    if(DEBUG):    
        print("Destination for Directory information: ")
        print(destDirBlocks)    
    
    #4    
    freeBlock = scanFree('i', disk)
    if(DEBUG):    
        print("Found a free iNode, number: ") 
        print(freeBlock)
    
    freeAddress = ((freeBlock-1) * INODE_SIZE) + INODETABLE
    if(DEBUG):    
        print("Can start writing the INode at: ")
        print(freeAddress)
    
    #5
    startPos = readTillEnd(destDirBlocks, disk)
    if(DEBUG):    
        print("From this position can write the enter into the Parent: ")
        print(startPos)
  
    #6   
    with open(filePath, 'r') as content_file:
            content = content_file.read()    
    encoded = content.encode('utf-8')    
    if(DEBUG):
        print("Encoded Data: ")
        print(encoded)
    
    #7
    #Taken care of above
    if(DEBUG):    
        print("Found a free iNode, number2: ") 
        print(freeBlock)    
    
    
    #8
    # Acquire free Dataspace
    
    #res is the last used block so res+1 is free
    res = scanFree('b', disk)
       
    #Calculate the amount of blocks that are required
    dataLength = len(encoded)
    #Block amount calculator
    blocks = calcBlocks(dataLength)
    
    #For each block, get a space, reserve that space, add the space to the list
    spaces = []
    for i in range(0, blocks):
        #for each block get a dataspace from the bmap
        res = scanFree('b', disk)
        spaces.append(res+1)
        
        
        bitMapReserve('b', res+1, disk)
    #The spaces are now reserved    

    
    # 9. 
    
    #Write the data into the dataspace
    spacesData = []
    if(len(spaces) > 1):
        #have to break up the encoded into BLOCKSIZE
        for i in range (0, len(spaces)):
            encodedSeg = encoded[0+(i*BLOCK_SIZE):BLOCK_SIZE + (i*BLOCK_SIZE)]
            spacesData.append(encodedSeg)
    else:
        encodedSeg = encoded
        spacesData.append(encodedSeg)
     
    #Finally we can start writing
    for i in range(0, len(spaces)):
        wAddr = spaces[i] * BLOCK_SIZE
        disk.seek(wAddr)
        disk.write(spacesData[i])
                    
    #10
    
    # check iTable location is good
    freeBlockAddress = ((freeBlock - 1) * INODE_SIZE) + INODETABLE
    
    checked = freeCheck(freeBlockAddress, freeBlock, disk)
    if (checked != freeBlock):
        freeBlock = checked
    freeBlockAddress = ((freeBlock - 1) * INODE_SIZE) + INODETABLE

    #reserve the address
    #physically check free
    checked = freeCheck(freeBlockAddress, freeBlock, disk)
    
    
    #---------- ----- ----- ENSURE THAT THE BIT MAP RETURN IS NOT None ----- ----- -----  
    reserve = None
    reserve = bitMapReserve('i', freeBlock, disk)
    
    #Template for a file header with nothing in the iblocks
    headerl1 = b'\A4\x81\xea\x03\xf8\x0a\x00\x00\x99\xec\x62\x54\x99\xec\x62\x54'
    headerl2 = b'\x99\xec\x62\x54\x00\x00\x00\x00\xea\x03\x01\x00\x06\x00\x00\x00'
    headerl3 = b'\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' 
    headerl4 = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    headerl5 = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    headerl6 = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    headerl7 = b'\x00\x00\x00\x00\x49\x00\x2c\xfe\x00\x00\x00\x00\x00\x00\x00\x00'
    headerl8 = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    
    header = headerl1 + headerl2 + headerl3 + headerl4 + headerl5 + headerl6 + headerl7 + headerl8
    
    #write template
    disk.seek(freeBlockAddress)
    disk.write(header)
    #write the blocks
    disk.seek(freeBlockAddress)
      
    curr = 0
    for i in range(0, len(spaces)):
        disk.seek(freeBlockAddress + 40 + curr)
        
        #Write the Blocks used
        placement = (spaces[i]).to_bytes(4, byteorder='little')
        disk.write(placement)
        curr = curr + 4
            
           
    #11.
    #Write the information into the Parent  
    
    #inode
    inodeEntry = freeBlock.to_bytes(4, byteorder='little')
    
    sfp = filePath.split("/")

    #totalSize
    fileName = sfp[len(sfp)-1]
    totalSizeEntry = 8 + len(fileName)
    totalSizeEntry = totalSizeEntry.to_bytes(2, byteorder='little')  
    nameLenEntry = len(fileName).to_bytes(1, byteorder='little')
    typeEntry = (1).to_bytes(1, byteorder='little')
    #construct the bytes for the name
    nameEntry = b''
    for i in range(0, len(fileName)):
        letter = ord(fileName[i]).to_bytes(1, byteorder='little')
        nameEntry = nameEntry + letter
    
    
    dirHeader = inodeEntry + totalSizeEntry + nameLenEntry + typeEntry + nameEntry
    
    #Write the header into the slot
    if(startPos == None):
        print("Error too much information in destination blocks, Overflown limit")
        return
        
    disk.seek(startPos)
    disk.write(dirHeader)
   
    #It is over Finally copy is working
    disk.close()



def ext2_mkdir(*args):
    #ext2_mkdir: This program takes two command line arguments. The first is the name of an ext2 formatted virtual disk. The second is an absolute path on your ext2
    #formatted disk. The program should work like mkdir, creating the final directory on the specified path on the disk. If location where the final directory is to
    #be created does not exist or if the specified directory already exists, then your program should return the appropriate error.
    
    
    #ext2_mkdir("C:/Users/Adam/Documents/369/A3/onedirectory.img", "/testdirectory/test")
    #test paster
    
    #error check params
    
    if (len(args) != 2):
        print("Incorrect parameter numbers")
        return    
    #setup the args
    ext2 = args[0]
    ext2Path = args[1]
    
    #Open the image
    disk = open(ext2, "r+b")     
    
    #1. Check that the path exists
    #2. Check that the Name isnt already there?
    #3. Acquire a new Inode
    #4. Acquire a Block for the Data (write . and .. into it)
    #5. Write data Into the Inode
    #6. Write the data into the Parent

    #1
    #Cut the last from ext2Path to process
    if(ext2Path == '/'):
        print("Error, Will not overwrite /")
        return None
    
    pathNoCurr = ''
    split = ext2Path.split("/")
    for i in range (1, len(split)-1):
        pathNoCurr = pathNoCurr + '/' + split[i]
    
    destDir = getDirectory(pathNoCurr, disk)
    if(destDir == None):
        print("Directory does not exist")
        return
    if(DEBUG):
        print("Destination directory is: ")
        print(destDir) 
    
    #Get Directory Blocks
    destDirLocation = ((destDir) * INODE_SIZE) + INODETABLE
    destDirBlocks = jumpIntoIblocks(destDirLocation, disk)
    if(DEBUG):    
        print("\nDestination for Directory information: ")
        print(destDirBlocks)        
    #Get the Writing Position in Directory
    startPos = readTillEnd(destDirBlocks, disk)
    if(DEBUG):    
        print("\nFrom this position can write the enter into the Parent: ")
        print(startPos)    

    #2

    #----- ----- ----- ----- ----- Check that the Name isnt already there ---- ---- -----
    disk.seek(destDirBlocks)
    val = disk.read(400)

    while(curr<80):    
        inodeTotal = 0
        inodeTotal = inodeTotal + val[curr]
        inodeTotal = inodeTotal + (val[curr + 1] * 16)
        inodeTotal = inodeTotal + (val[curr + 2] * (16*16))
        inodeTotal = inodeTotal + (val[curr + 3] * (16*16*16))
        if(DEBUG):
            print("The Inode found is: %d" % inodeTotal)
        
        totalSize = 0
        totalSize = totalSize + (val[curr + 4])
        totalSize = totalSize + (val[curr + 5] * 16)
        #totalSize = totalSize + (val[curr + 5])
        if(DEBUG):
            print("The Total size is: %d" % totalSize)
        
        nameLength = val[curr + 6]
        if(DEBUG):
            print("The name Length is: %d" % nameLength)
        
        typeInd = val[curr+7]
        if(DEBUG):
            print(val[curr+7])
        #Compile the name
        name = ''
        for i in range(0, nameLength):
            name = name + chr(val[ curr+ 8 + i ])
        if (nameLength %2 != 0):
            curr = curr+1
        if(DEBUG):
            print("The Compiled name is: %s" % name)  
            
        if (name == split[len(split)-1]):
            print("Error: Duplicate File detected")
            return None   
    #----- ----- ----- ----- ----- Not sure if necessary ---- ---- -----
    
    #3
    
    #3. Acquire a new Inode
    freeBlock = scanFree('i', disk)
    if(DEBUG):    
        print("Found a free iNode, number: ") 
        print(freeBlock)
    
    freeAddress = ((freeBlock-1) * INODE_SIZE) + INODETABLE
    if(DEBUG):    
        print("Can start writing the INode at: ")
        print(freeAddress)   
    bitMapReserve('i', freeBlock, disk)
    
    
    #4. Acquire a Block for the Data (write . and .. into it)
    #Finding a free DataSpace
    spaces = []
    
    res = scanFree('b', disk)
    spaces.append(res+1)
    bitMapReserve('b', res+1, disk) 
    
    #5. Write data Into the Inode
    #Template for a file header with nothing in the iblocks
    headerl1 = b'\xc0\x41\xea\x03\xf8\x0a\x00\x00\x99\xec\x62\x54\x99\xec\x62\x54'
    headerl2 = b'\x99\xec\x62\x54\x00\x00\x00\x00\xea\x03\x01\x00\x06\x00\x00\x00'
    headerl3 = b'\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' 
    headerl4 = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    headerl5 = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    headerl6 = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    headerl7 = b'\x00\x00\x00\x00\x49\x00\x2c\xfe\x00\x00\x00\x00\x00\x00\x00\x00'
    headerl8 = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    
    
    header = headerl1 + headerl2 + headerl3 + headerl4 + headerl5 + headerl6 + headerl7 + headerl8
    freeBlockAddress = ((freeBlock - 1) * INODE_SIZE) + INODETABLE
    #write template
    disk.seek(freeBlockAddress)
    disk.write(header)
    #write the blocks
    disk.seek(freeBlockAddress)
      
    curr = 0
    for i in range(0, len(spaces)):
        disk.seek(freeBlockAddress + 40 + curr)
        
        #Write the Blocks used
        placement = (spaces[i]).to_bytes(4, byteorder='little')
        disk.write(placement)
        curr = curr + 4

    #7. Write the data into the Block
    wAddr = spaces[0] * BLOCK_SIZE  
       
    #Create the template with . and ..    
    #Inode  [4], total Size [2], nameLen[1], type[1]
    
    dot = b'\x0c\x00\x01\x02\x2e\x00\x00'
    dotdot = b'\x0c\x00\x02\x02\x2e\x2e\x00\x00'    
    
    dotInode = freeBlock.to_bytes(4, byteorder='little') 
    dotdotInode = destDir.to_bytes(4, byteorder='little') 
    
    dHeader = dotInode + dot + dotdotInode + dotdot         
    disk.seek(wAddr)
    disk.write(dHeader)

    
    #6. Write the data into the Parent 
    #inode
    inodeEntry = freeBlock.to_bytes(4, byteorder='little')
    
    sfp = ext2Path.split("/")

    #totalSize
    fileName = sfp[len(sfp)-1]
 
    totalSizeEntry = 8 + len(fileName)
    totalSizeEntry = totalSizeEntry.to_bytes(2, byteorder='little')  
    
    nameLenEntry = len(fileName).to_bytes(1, byteorder='little')
    
    typeEntry = (2).to_bytes(1, byteorder='little')
    
    
    ##construct the bytes for the name
    nameEntry = b''
    for i in range(0, len(fileName)):
        letter = ord(fileName[i]).to_bytes(1, byteorder='little')
        nameEntry = nameEntry + letter
    
    dirHeader = inodeEntry + totalSizeEntry + nameLenEntry + typeEntry + nameEntry
    
    ##Write the header into the slot
    disk.seek(startPos)
    disk.write(dirHeader)
    
    disk.close()

    
def ext2_ln(*args):
    #ext2_ln: This program takes three command line arguments. The first is the name of an ext2 formatted virtual disk. The other two are absolute paths on your ext2
    #formatted disk. The program should work like ln, creating a link from the first specified file to the second specified path. If the first location does not 
    #exist if the second location already exists, or if the first location refers to a directory, then your program should return the appropriate error.
    
    #testing copy
    #ext2_ln("C:/Users/Adam/Documents/369/A3/onedirectory.img", "/testdirectory/testfile.txt", "/lost+found/a.txt")
    
    #error check params
    if (len(args) != 3):
        print("Incorrect parameter numbers")
        return
    #setup the args
    ext2 = args[0]
    firstFilePath = args[1]
    destinationFilePath = args[2]
        
    #Open the image
    disk = open(ext2, "r+b") 
    
    # Get the Source parent - fileNamePath -
    if(firstFilePath[0] != "/" or destinationFilePath[0] != "/"):
        print("Please format the ext2 path to start with a /")
        return None
    
    
    sourceDir = getDirectory(firstFilePath, disk)
    if(sourceDir == None):
        print("Directory does not exist")
        return
    if(DEBUG):
        print("Destination directory is: ")
        print(sourceDir)
    
    # Get the destination parent - destinationFilePath -
    # Chop off the name
    dfp = ''
    sdfp = destinationFilePath.split("/")
    
    linkName = sdfp[len(sdfp)-1]    
    
    #chop off the source name
    ssfp = firstFilePath.split("/")
    sName = ssfp[len(sdfp)-1]

    for i in range(1, len(sdfp)-1):
        dfp = dfp + "/" + sdfp[i]

    #Get the destination directory
    destDir = getDirectory(dfp, disk)
    if(destDir == None):
        print("Directory does not exist")
        return
    if(DEBUG):
        print("Destination directory is: ")
        print(destDir)
        
        
    # Check that the actual file does not already exist, if it does return error
    sourceDirLocation = ((sourceDir-1) * INODE_SIZE) + INODETABLE
    #This is where the directory's contents is held
    sourceDirBlocks = jumpIntoIblocks(sourceDirLocation, disk)
    if(DEBUG):    
        print("Source for Directory information: ")
        print(sourceDirBlocks)    
    
    
    destDirLocation = ((destDir) * INODE_SIZE) + INODETABLE
    #This is where the directory's contents is held
    #i.e. this is where the completed information will be placed
    destDirBlocks = jumpIntoIblocks(destDirLocation, disk)
    if(DEBUG):    
        print("Destination for Directory information: ")
        print(destDirBlocks)    

    curr = 0
    found = False
    
    #disk.seek(destDirBlocks)
    disk.seek(sourceDirBlocks)
    val = disk.read(400)

    while(curr<80):    
        inodeTotal = 0
        inodeTotal = inodeTotal + val[curr]
        inodeTotal = inodeTotal + (val[curr + 1] * 16)
        inodeTotal = inodeTotal + (val[curr + 2] * (16*16))
        inodeTotal = inodeTotal + (val[curr + 3] * (16*16*16))
        if(DEBUG):
            print("The Inode found is: %d" % inodeTotal)
        
        totalSize = 0
        totalSize = totalSize + (val[curr + 4])
        totalSize = totalSize + (val[curr + 5] * 16)
        #totalSize = totalSize + (val[curr + 5])
        if(DEBUG):
            print("The Total size is: %d" % totalSize)
        
        nameLength = val[curr + 6]
        if(DEBUG):
            print("The name Length is: %d" % nameLength)
        
        typeInd = val[curr+7]
        if(DEBUG):
            print(val[curr+7])
        #Compile the name
        name = ''
        for i in range(0, nameLength):
            name = name + chr(val[ curr+ 8 + i ])
        if (nameLength %2 != 0):
            curr = curr+1
        if(DEBUG):
            print("The Compiled name is: %s" % name)  
            
        if (name == sName):
            foundINode = inodeTotal
            found = True
            break
        curr = curr + 8 + nameLength + 2
    
    if(not found):
        print("ERROR: The Source file requested does not exist")
        return
                
    sourceINode = ((foundINode-1) * INODE_SIZE) + INODETABLE
    #check that the source is actually a file
    disk.seek(sourceINode)
    val = disk.read(1)

    #only care about 4 (file), just if case it, not elegant, but works
    file = False
    if(val == b'\x04' or val == b'\x14' or val == b'\x24' or val == b'\x34' or val == b'\x44' or val == b'\x54' or val == b'\x64' or val == b'\x74' or val == b'\x84' or val == b'\x94' or val == b'\xa4' or val == b'\xb4' or val == b'\xc4' or val == b'\xd4' or val == b'\xe4' or val == b'\xf4'):
        file = True
    if (file == False):
        print("ERROR: Sourced target is not a file")
        return
        
    # The checks are now all made
    # Copy the Inode information
    disk.seek(sourceINode)
    linkInfo = disk.read(INODE_SIZE)
    # Make a new Inode with the information
    freeBlock = scanFree('i', disk)
    if(DEBUG):    
        print("Found a free iNode, number: ") 
        print(freeBlock)
    
    freeAddress = ((freeBlock-1) * INODE_SIZE) + INODETABLE
    if(DEBUG):    
        print("Can start writing the INode at: ")
        print(freeAddress)
    
    bitMapReserve('i', freeBlock, disk)
    
    disk.seek(freeBlock)
    disk.write(linkInfo)
    
    # Place it in the parent
    # place in parent the freeBlock as Inode and the name as linkName
    # Add the information to the destination's directory

    startPos = readTillEnd(destDirBlocks, disk)
    if(DEBUG):    
        print("From this position can write the enter into the Parent: ")
        print(startPos)    
        
    #inode
    inodeEntry = freeBlock.to_bytes(4, byteorder='little')

    #totalSize
    fileName = linkName
    totalSizeEntry = 8 + len(fileName)
    totalSizeEntry = totalSizeEntry.to_bytes(2, byteorder='little')  
    
    nameLenEntry = len(fileName).to_bytes(1, byteorder='little')
    
    typeEntry = (1).to_bytes(1, byteorder='little')
    
    
    #construct the bytes for the name
    nameEntry = b''
    for i in range(0, len(fileName)):
        letter = ord(fileName[i]).to_bytes(1, byteorder='little')
        nameEntry = nameEntry + letter
    
    dirHeader = inodeEntry + totalSizeEntry + nameLenEntry + typeEntry + nameEntry
    
    #Write the header into the slot
    disk.seek(startPos)
    disk.write(dirHeader)
    
    disk.close()
    
    

def ext2_rm(*args):
    #ext2_rm: This program takes two command line arguments. The first is the name of an ext2 formatted virtual disk, and the second is an absolute path to a file or
    #link (not a directory) on that disk. The program should work like rm, removing the specified file from the disk. If the file does not exist or if it is a
    #directory, then your program should return the appropriate error.
    
    #error check params
    if (len(args) != 2):
        print("Incorrect parameter numbers")
        return    
    #setup the args
    ext2 = args[0]
    filePath = args[1]
    
    #Open the image
    disk = open(ext2, "r+b") 
    
    #get the parent directory
    
    dfp = ''
    sdfp = filePath.split("/")
    
    linkName = sdfp[len(sdfp)-1]    


    for i in range(1, len(sdfp)-1):
        dfp = dfp + "/" + sdfp[i]

    #Get the destination directory
    destDir = getDirectory(dfp, disk)
    if(destDir == None):
        print("Directory does not exist")
        return
    if(DEBUG):
        print("Destination directory is: ")
        print(destDir)

    
    destDirLocation = ((destDir) * INODE_SIZE) + INODETABLE
    if(DEBUG): 
        print("Dest INode at")
        print(destDirLocation)
    
    destDirBlocks = jumpIntoIblocks(destDirLocation, disk)
    if(DEBUG):    
        print("Destination for Directory information: ")
        print(destDirBlocks)
        
    #check the the file exists
    
    curr = 0
    found = False
    
    disk.seek(destDirBlocks)
    val = disk.read(400)

    while(curr<80):    
        inodeTotal = 0
        inodeTotal = inodeTotal + val[curr]
        inodeTotal = inodeTotal + (val[curr + 1] * 16)
        inodeTotal = inodeTotal + (val[curr + 2] * (16*16))
        inodeTotal = inodeTotal + (val[curr + 3] * (16*16*16))
        if(DEBUG):
            print("The Inode found is: %d" % inodeTotal)
        
        totalSize = 0
        totalSize = totalSize + (val[curr + 4])
        totalSize = totalSize + (val[curr + 5] * 16)
        #totalSize = totalSize + (val[curr + 5])
        if(DEBUG):
            print("The Total size is: %d" % totalSize)
        
        nameLength = val[curr + 6]
        if(DEBUG):
            print("The name Length is: %d" % nameLength)
        
        typeInd = val[curr+7]
        if(DEBUG):
            print(val[curr+7])
        #Compile the name
        name = ''
        for i in range(0, nameLength):
            name = name + chr(val[ curr+ 8 + i ])
        if (nameLength %2 != 0):
            curr = curr+1
        if(DEBUG):
            print("The Compiled name is: %s" % name)  
            
        if (name == linkName):
            foundINode = inodeTotal
            found = True
            break
        curr = curr + 8 + nameLength + 2
    
    if(not found):
        print("ERROR: The file requested does not exist")
        return   
    
    #check the file is a file
    
    #Place inode location in here to file check
    disk.seek((foundINode-1) * INODE_SIZE + INODETABLE)
    val = disk.read(1)
    
    #only care about 4 (file), just if case it, not elegant, but works
    file = False
    if(val == b'\x04' or val == b'\x14' or val == b'\x24' or val == b'\x34' or val == b'\x44' or val == b'\x54' or val == b'\x64' or val == b'\x74' or val == b'\x84' or val == b'\x94' or val == b'\xa4' or val == b'\xb4' or val == b'\xc4' or val == b'\xd4' or val == b'\xe4' or val == b'\xf4'):
        file = True
    if (file == False):
        print("ERROR: target is not a file")
        return
        
    # get the blocks
    disk.seek((foundINode-1) * INODE_SIZE + INODETABLE+40)
    curr = 0
    maxR = 14* 4
    blocks = []
    blockR = disk.read(4)
    while(blockR != b'\x00\x00\x00\x00' or curr>maxR):
        blocks.append(blockR)
        curr = curr + 4
        disk.seek((foundINode-1) * INODE_SIZE + INODETABLE+40+curr)
        blockR = disk.read(4)
    if(DEBUG): 
        print("The blocks are: ")
        print(blocks)
    
    blockNums = []
    for i in range(0, len(blocks)):
        blockTotal = 0
        blockTotal = blockTotal + ord((blocks[i])[0:1])
        blockTotal = blockTotal + (ord((blocks[i])[1:2]) * 16)
        blockTotal = blockTotal + (ord((blocks[i])[2:3]) * (16*16))
        blockTotal = blockTotal + (ord((blocks[i])[3:4]) * (16*16*16))
        blockNums.append(blockTotal)
    #the blocks are now converted into their integer values
    if(DEBUG): 
        print(blockNums)
   
    #0 out the INode
    zeros = b''
    for i in range(0, INODE_SIZE):
        zeros = zeros + b'\x00'

    disk.seek(foundINode)
    disk.write(zeros)    
    
    #release the blocks to the bitmap
    for i in range(0, len(blockNums)):
        releaseBit(blockNums[i], 'b', disk)
    
    #release foundINode
    releaseBit(foundINode, 'i', disk)
    
    #clear the parent
    disk.seek(destDirBlocks)
    val = disk.read(400)

    while(curr<80):    
        inodeTotal = 0
        inodeTotal = inodeTotal + val[curr]
        inodeTotal = inodeTotal + (val[curr + 1] * 16)
        inodeTotal = inodeTotal + (val[curr + 2] * (16*16))
        inodeTotal = inodeTotal + (val[curr + 3] * (16*16*16))
        if(DEBUG):
            print("The Inode found is: %d" % inodeTotal)
        
        totalSize = 0
        totalSize = totalSize + (val[curr + 4])
        totalSize = totalSize + (val[curr + 5] * 16)
        #totalSize = totalSize + (val[curr + 5])
        if(DEBUG):
            print("The Total size is: %d" % totalSize)
        
        nameLength = val[curr + 6]
        if(DEBUG):
            print("The name Length is: %d" % nameLength)
        
        typeInd = val[curr+7]
        if(DEBUG):
            print(val[curr+7])
        #Compile the name
        name = ''
        for i in range(0, nameLength):
            name = name + chr(val[ curr+ 8 + i ])
        if (nameLength %2 != 0):
            curr = curr+1
        if(DEBUG):
            print("The Compiled name is: %s" % name)  
            
        if (name == linkName):
            #zero out the section
            for i in range(0,  (8 + nameLength + 2)):
                disk.seek(curr+destDirBlocks+i)
                disk.write(b'\x00')
        curr = curr + 8 + nameLength + 2    