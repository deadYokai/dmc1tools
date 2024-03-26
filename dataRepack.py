from binary import BinaryStream
from pathlib import Path
import os
import argparse

import textureRepack
from contextlib import chdir

def repackData(fff, mode):
    fn = fff.stem
    ff = str(fff)
    os.makedirs(f"_{fn}", exist_ok=True)
    fsd = False
    itm = False
    if  ff.split('.')[1][:3] == "itm":
        itm = True
    with open(ff, "rb") as f:

        index_path = os.path.join(f"_{fn}", f"{ff}.index")

        if mode == "u":
            if os.path.exists(index_path):
                if os.path.isfile(index_path):
                    os.remove(index_path)
                else:
                    os.rmdir(index_path)

        reader = BinaryStream(f)
        f.seek(0, os.SEEK_END)
        fileSize = f.tell()

        reader.seek(0)

        head = reader.readInt32()
        fOffset = reader.readUInt32() # get a first offset and header size

        if fOffset ==  3435973836: # check for 'CCCCCCCC' bytes
            fsd = True
            itm = False
            fOffset = reader.readUInt32() # reassign a true first offset for FSD files

        print(f"Processing file {ff}")

        offsetList = []
        sizeList = []
        keyList = []
        offset4offset = {}

        if mode == "u":
            offset4offset[fOffset] = reader.offset()-4
            offsetList.append(fOffset)

            if itm:
                fSize = reader.readUInt32()
                sizeList.append(fSize)

            while(reader.offset() < fOffset):
                data = reader.readUInt32()

                if data != 0:
                    offset4offset[data] = reader.offset()-4
                    offsetList.append(data)

                    if itm:
                        data2 = reader.readUInt32()
                        if data2 == 0:
                            reader.seek(data)
                            pos1 = reader.offset()
                            data2 = fileSize - pos1
                        sizeList.append(data2)

            if fsd:
                offsetList.sort()

            for a in range(len(offsetList)):
                key = hex(offsetList[a])
                reader.seek(offsetList[a])

                if itm:
                    size = sizeList[a]
                    stringData = reader.readBytes(size)
                else:
                    if a+1 == len(offsetList):
                        nextItm = fileSize
                    else:
                        nextItm = offsetList[a+1]
                    stringData = reader.readBytes(nextItm - offsetList[a])

                toE = False
                if stringData[:4] == b'ipum':
                    key += ".ip2"
                    toE = True
                if stringData[:4] == b'\x002MT':
                    key += ".tm2"
                    toE = True
                if stringData[:4] == b'\x0023T':
                    key += ".t32"
                    toE = True

                with open(index_path, "a") as indexFile:
                    indexFile.write(key + '\t' + str(offsetList[a]) + '\t' + str(offset4offset[offsetList[a]]) + '\n')

                with open(os.path.join(f"_{fn}", f"{key}"), "wb") as out:
                    out.write(stringData)

                if toE:
                    with chdir(f"_{fn}"):
                        textureRepack.process_file(Path(f"{key}"), "u")

                print(f"Extracted: {key}")
        elif mode == "p":
            with open(index_path, "r") as indexFile:
                iLine = indexFile.readline()
                while iLine:
                    dat = iLine.split('\t')
                    keyList.append(dat[0])
                    off = int(dat[1].replace('\n', ''))
                    offsetList.append(off)
                    offset4offset[off] = int(dat[2])
                    iLine = indexFile.readline()

            with open(f"{ff}_new", "wb+") as modFile:
                reader.seek(0)
                modFile.write(reader.readBytes(fOffset))

                modReader = BinaryStream(modFile)
                modReader.seek(0)
                modReader.readInt32()
                if fsd:
                    modReader.readInt32()
                pointer = modReader.offset()

                ps = fOffset
                for a in range(len(offsetList)):
                    key = keyList[a]
                    with open(os.path.join(f"_{fn}", f"{key}"), "rb") as keyFile:
                        keyFile.seek(0, os.SEEK_END)
                        fileSize = keyFile.tell()
                        keyFile.seek(0)

                        modReader.seek(offset4offset[offsetList[a]])
                        modReader.writeUInt32(offsetList[a])

                        if itm:
                            modReader.writeUInt32(fileSize)

                        modReader.seek(ps)
                        modReader.writeBytes(keyFile.read())
                        ps = modReader.offset()



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = 'FSD/DAT/ITM Extractor (DMC1)', epilog = 'Work in progress')
    parser.add_argument("filename", help = "File")
    parser.add_argument("-p", "--pack", help = "Pack file", default=False, action = argparse.BooleanOptionalAction)
    args = parser.parse_args()
    fp = Path(args.filename)

    if args.pack:
        process = "p"
    else:
        process = "u"

    repackData(fp, process)
