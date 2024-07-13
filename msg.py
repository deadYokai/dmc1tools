import io
import os
import sys
import struct
from wand.image import Image
import ast

def extract(msgIn, charsFile = None, out = None):
    print(f"\n---- Extracting  {msgIn}")
    dir_path = os.path.dirname(os.path.realpath(__file__))
    if charsFile == None:
        charsFile = f"{dir_path}/charindex.txt"
    with open(charsFile, "r", encoding="utf-8") as chi:
        charTableEngText = chi.read()
        charTableEng = ast.literal_eval(charTableEngText)

    if out == None:
        out = f"{msgIn}.txt"
    print(f"---- Output      {out}")
    print(f"---- Charset     {os.path.basename(charsFile)}")
    stringData = ''
    with open(msgIn, 'rb') as mf:
        mf.seek(0, os.SEEK_END)
        fs = mf.tell()
        mf.seek(0)
        headerCount = struct.unpack("i", mf.read(4))[0]
        mfoff = 0
        pointer = 0

        # ig = 0
        cmdByte = "7e"
        for i in range(headerCount):
            mf.seek(4 + 8*i)
            off = struct.unpack('i', mf.read(4))[0]
            if i == 0:
                mfoff = off
            size = struct.unpack('i', mf.read(4))[0]
            pointer = mf.tell()
            mf.seek(off)
            data = mf.read(size)
            string = ''
            d = io.BytesIO(data)
            while d.tell() < size:
                dat = d.read(1)
                if dat == b'\x7E' or dat == b'\x77':
                    cmdByte = dat.hex()
                    q = d.read(1)
                    if q == b'\x09' or q == b'\x0A' or q == b'\x0B':
                        a = d.read(1)
                        string += f"{{{q.hex()}:{a.hex()}}}"
                    elif q == b'\x0E':
                        string += f"\n{{ENDSTRING:{d.read(size - d.tell()).hex()}}}"
                        break
                    elif q == b'\x0d':
                        a = d.read(1).hex()
                        b = d.read(1).hex()
                        string += f"{{{q.hex()}:[{a},{b}]}}"
                    elif q == b'\x05':
                        string += " "
                        # with Image(width=16,height=32) as img:
                        #     img.save(filename=f"test/{i}/{ig}_space.dds")
                    elif q == b'\x0c':
                        string += "\n"
                    else:
                        string += f"{{{q.hex()}}}"
                    continue
                if dat == b'\x72':
                    itm = struct.unpack("B", d.read(1))[0]
                else:  
                    itm = struct.unpack("B", dat)[0]
                try:
                    string += charTableEng[itm]
                except:
                    string += f"{{?{itm}}}"

                # x = int(itm * 16)
                # yc = 0
                # while x > (256-16):
                #     x = x - 256
                #     if x < 0:
                #         x = 0
                #     yc += 1
                # y = yc * 32
                # ii = 0
                # if x > 256-16:
                #     ii = 1
                #     x = x - 256 - 16
                # print(f"x: {x} :: y: {y}")
                # if (x < 256-15) and (y < 512-32):
                #     with Image(filename=f"_msg_tex/f096e34f.{ii}.dds") as img:
                #         with img[x:x+16, y:y+32] as ci:
                #             ci.save(filename=f"test/{i}/{ig}.dds")
                # ig += 1
            stringData += ";;;STR\n" + string + "\n;;;ENDSTR\n\n"
        stringData += f";;;CMDBYTE:{cmdByte}\n"
        if pointer != 0 and mfoff != 0:
            endDataFile = mf.read(fs - mf.tell()).hex()
            mf.seek(pointer)
            endDataHeader = mf.read(mfoff - mf.tell()).hex()
            stringData += ";;;ENDHEADERBYTES:"+endDataHeader
            if len(endDataFile) != 0:
                stringData += "\n;;;ENDBYTES:"+endDataFile
        
        stringData += "\n" #EOF

    with open(out, "w", encoding='utf-8') as msgText:
        msgText.write(";;;CHARTABLE\n")
        msgText.write(charTableEngText)
        msgText.write(";;;ENDCHARTABLE\n\n")
        msgText.write(stringData)

    print("\n---- Done")
def pack(txtIn, out = None):
    print(f"\n---- Packing {txtIn}")
    if out == None:
        out = txtIn.replace('.txt', '')
    print(f"---- Output  {out}")
    chartable = None
    endFileData = None
    endHeaderData = None
    cmdByte = None
    strings = []
    with open(txtIn, "r", encoding='utf-8') as msg:
        args = msg.read().split(';;;')
        for i in range(len(args)):
            if args[i] == "ENDCHARTABLE\n\n":
                chartable = ast.literal_eval(args[i-1].rstrip().replace('CHARTABLE', ''))
            if args[i] == "ENDSTR\n\n":
                strings.append(args[i-1].replace("STR\n", ''))
            if args[i].startswith("CMDBYTE"):
                cmdByte = bytes.fromhex(args[i].rstrip().replace("CMDBYTE:", ''))
            if args[i].startswith("ENDHEADERBYTES"):
                endHeaderData = bytes.fromhex(args[i].rstrip().replace("ENDHEADERBYTES:", '')) 
            if args[i].startswith("ENDBYTES"):
                endFileData = bytes.fromhex(args[i].rstrip().replace("ENDBYTES:",''))

    if chartable == None:
        dir_path = os.path.dirname(os.path.realpath(__file__))
        charsFile = f"{dir_path}/charindex.txt"
        with open(charsFile, "r", encoding='utf-8') as chi:
            chartable = ast.literal_eval(chi.read())

    if cmdByte == None or endHeaderData == None or strings == []:
        raise ValueError("Something wrong")

    invCharTable = {v: k for k, v in chartable.items()}
    cc = len(strings)
    msgBytes = struct.pack("I", cc)
    msgBytes += bytes(cc * 8)
    msgBytes += endHeaderData
    strData = []
    for i in range(len(strings)):
        strEnd = b''
        strBytes = b''
        string = strings[i].replace('\n{ENDSTRING', '{ENDSTRING').rstrip()
        dat = io.StringIO(string)
        d = dat.read(1)
        while d:
            if d == "{":
                p = dat.tell()
                if dat.read(10) == "ENDSTRING:":
                    cmdEnd = string.find("}", dat.tell())
                    end = dat.read(cmdEnd-dat.tell())
                    strEnd = cmdByte + b'\x0e' + bytes.fromhex(end)
                    dat.seek(cmdEnd+1) 
                else:
                    dat.seek(p+2)
                    ff = dat.read(1)
                    if ff == ":":
                        arg = dat.read(1)
                        if arg == "[":
                            arrEnd = string.find("]", dat.tell())
                            arr = dat.read(arrEnd - dat.tell()).split(',')
                            dat.seek(p)
                            arg = ''.join(arr)
                        else:
                            arg += dat.read(1)
                        dat.seek(p)
                        cmd = dat.read(2)
                        strBytes += cmdByte + bytes.fromhex(cmd+arg)
                        cmdEnd = string.find("}", dat.tell())
                        dat.seek(cmdEnd+1)
                    elif ff == "}":
                        e = dat.tell()
                        dat.seek(p)
                        strBytes += cmdByte + bytes.fromhex(dat.read(2))
                        dat.seek(e)
                    else:
                        dat.seek(p)
                        if dat.read(1) == "?":
                            cmdEnd = string.find("}", dat.tell())
                            s = dat.read(cmdEnd-dat.tell())
                            strBytes += struct.pack("B", int(s))
                            dat.seek(cmdEnd+1)
                        else:
                            dat.seek(p)
            elif d == ' ':
                strBytes += cmdByte + b'\x05'
            elif d == '\n':
                strBytes += cmdByte + b'\x0c'
            else:
                try:
                    if invCharTable[d] >= 112:
                        strBytes += b'\x72'
                    strBytes += struct.pack("B", invCharTable[d])
                except KeyError:
                    raise ValueError(f"Symbol '{d}'({ord(d)}) not found in CHARTABLE")
            d = dat.read(1)
        strBytes += strEnd
        da = len(strBytes) & 1
        while da != 0:
            strBytes += b'\x00'
            da = len(strBytes) & 1
            
        strData.append(strBytes)
        
    with io.BytesIO(msgBytes) as mb:
        for a in range(len(strData)):
            mb.seek(0, os.SEEK_END)
            off = mb.tell()
            offBytes = struct.pack("I", off)
            size = len(strData[a])
            sizeBytes = struct.pack("I", size)
            mb.write(strData[a])
            mb.seek(4 + (a*8))
            mb.write(offBytes)
            mb.write(sizeBytes)
        mb.seek(0)
        msgBytes = mb.read()

    if endFileData != None:
        msgBytes += endFileData

    with open(out, "wb") as nm:
        nm.write(msgBytes)
    

    print("\n---- Done")

def printHelp():
    print(f"\n---- Usage: python3 {sys.argv[0]} [options] <filename>\n")
    print(f"---- Options:")
    print(f"     -e      Extract msg to txt (default option)")
    print(f"     -p      Pack txt to msg")
    print(f"     -c      Charset file (default: charindex.txt)")
    exit()

if __name__ == "__main__":
    print("---- MSG Repacker (DMC 1) ----")
    print("---- by deadYokai         ----")
    isExtract = None
    charset = None
    out = None
    name = None
    indx = []
    args = sys.argv[1::]
    for i in range(len(args)):
        arg = args[i]
        if arg.startswith("-"):
            if arg == "-p":
                if isExtract != None:
                    printHelp()
                isExtract = False
            elif arg == "-e":
                if isExtract != None:
                    printHelp()
                isExtract = True
            elif arg == "-c":
                if i+1 <= len(args)-2 and charset == None:
                    charset = args[i+1]
                    indx.append(i+1)
                else:
                    printHelp()
            elif arg == "-o":
                if i+1 <= len(args)-2 and out == None:
                    out = args[i+1]
                    indx.append(i+1)
                else:
                    printHelp()
            else:
                printHelp()
        else:
            if not i in indx and name == None:
                name = arg
            elif name != None:
                printHelp()

    if isExtract == None:
        isExtract = True

    if name == None:
        printHelp()

    if isExtract:
        extract(name, charset, out)
    else:
        pack(name, out)
