import os
import sys

DELIMITER = b'\0'

inFd = None # File descriptor for reading input files
outFd = 1   # File descriptor for writing output buffer to file

# Set up the global variables
inbuf = bytearray()           # Input buffer for reading input files
outbuf = bytearray()  # Output buffer for writing to stdout
bytesRemaining = 0    # Number of bytes remaining in the output buffer

# Placeholder startMsg function to print header length
def startMsg(length):
    sendBytes(length)

# Write the encoded data to the output buffer
def sendBytes(data):
    global outbuf
    outbuf.extend(data)

# Empty the output buffer to stdout
def endMsg():
    global outbuf
    global outFd
    os.write(outFd, outbuf)
    os.close(outFd)

# Implement the create mode
def createMode(filenames, archive):
    global inFd, outFd, inbuf, outbuf
    inFd = None
    outFd = os.open(archive, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o666)
    inbuf = bytearray()
    outbuf = bytearray()

    for filename in filenames:
        inFd = os.open(filename, os.O_RDONLY)
        inbuf = bytearray()
        readBytes()
        sendBytes(filename.encode() + DELIMITER)
        fileSize = getFileSize(inFd)
        header = fileSize.to_bytes(8, byteorder='little')
        sendBytes(header)
        sendBytes(inbuf)
        os.close(inFd)
    endMsg()

def readBytes():
    global inFd, inbuf
    while True:
        data = os.read(inFd, 1000)
        if not data:
            break
        inbuf.extend(data)

def getFileSize(inFd):
    return os.fstat(inFd).st_size

def extractMode():
    global inFd, outFd, inbuf, outbuf
    inFd = os.open(sys.argv[2], os.O_RDONLY)
    inbuf = bytearray()
    readBytes()
    while inbuf:
        filename_end = inbuf.find(DELIMITER)
        if filename_end == -1:
            break
        filename = inbuf[:filename_end].decode()
        inbuf = inbuf[filename_end+1:]
        fileSize = int.from_bytes(inbuf[:8], byteorder='little')
        inbuf = inbuf[8:]
        outFd = os.open(filename, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o666)
        while fileSize > 0:
            write_size = min(fileSize, len(inbuf))
            os.write(outFd, inbuf[:write_size])
            inbuf = inbuf[write_size:]
            fileSize -= write_size
        os.close(outFd)
    os.close(inFd)

if len(sys.argv) < 2:
    sys.stderr.write("Usage: mytar.py c <file1> <file2> .. <archive> \n")
    sys.stderr.write("       mytar.py x \n")
    sys.exit(1)

if sys.argv[1] == 'c':
    # Create an archive
    if len(sys.argv) < 3:
        sys.stderr.write("Error: no input files specified\n")
        sys.exit(1)

    archive = sys.argv[-1]
    # Call the create_archive function with the list of input files
    createMode(sys.argv[2:-1], sys.argv[-1])

elif sys.argv[1] == 'x':
    # Extract from archive
    if len(sys.argv) < 3:
        sys.stderr.write("Error: No input files specified\n")
        sys.exit(1)
        # Read the file name, header block, and extract the file data
    extractMode()
else:
    sys.stderr.write("Error: invalid command")
