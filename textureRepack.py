from binary import BinaryStream
from pathlib import Path
import shutil
import os
import argparse

def process_file(filepath, mode):
    if not filepath.is_file():
        raise Exception("File not found")
    file_path = str(filepath)
    tafs_checker = file_path.split('.')[-1]
    name = file_path.split('.')[-2]
    with open(file_path, 'rb') as file:
        reader = BinaryStream(file)
        os.makedirs(name, exist_ok=True)
        if tafs_checker == "tm2":
            header = reader.readUInt32()
            if header == 1414345216:
                count = reader.readInt32()
                dataOff = reader.readInt32()
                reader.readBytes(28)
                crc = reader.readBytes(4).hex()
                reader.readBytes(16)
                for f in range(count):
                    sizeOff = reader.offset()
                    size = reader.readUInt32()
                    reader.seek(dataOff)
                    name2 = name + "_" +str(f)
                    tName = f"{name}/{name2}.dds"
                    if mode == "u":
                        with open(tName, "wb") as tF:
                            tF.write(reader.readBytes(size))
                    elif mode == "p":
                        with open(tName, "rb") as tF:
                            moddedFile = open(f"{name}_new.{tafs_checker}", "wb")
                            r = BinaryStream(moddedFile)
                            o = reader.offset()
                            reader.seek(0)
                            r.writeBytes(reader.readBytes(dataOff))
                            reader.seek(o)
                            tF.seek(0, os.SEEK_END)
                            mSize = tF.tell()
                            tF.seek(0)
                            r.writeBytes(tF.read())
                            r.seek(sizeOff)
                            r.writeUInt32(mSize)
                            moddedFile.close()

        elif tafs_checker == "ip2":
            headerName = reader.readBytes(4).decode("utf-8")
            if headerName == "ipum":
                reader.readBytes(8)
                count = reader.readInt32()
                if mode == "p":
                    moddedFile = open(f"{name}_new.{tafs_checker}", "wb")
                    r = BinaryStream(moddedFile)
                    o = reader.offset()
                    reader.seek(0)
                    r.writeBytes(reader.readBytes(16))
                    reader.seek(o)
                for f in range(count):
                    somedata = reader.readInt32()
                    sizeOff = reader.offset()
                    size = reader.readUInt32()
                    tName = f"{name}/{name}.{f}.dds"
                    if mode == "u":
                        with open(tName, "wb") as tF:
                            tF.write(reader.readBytes(size))
                    elif mode == "p":
                        with open(tName, "rb") as tF:
                            tF.seek(0, os.SEEK_END)
                            mSize = tF.tell()
                            tF.seek(0)

                            r.writeUInt32(somedata)
                            r.writeUInt32(mSize)
                            r.writeBytes(tF.read())
                        reader.readBytes(size) # add offset to reader
                if mode == "p":
                    moddedFile.close()
            else:
                os.removedirs(name)

        elif tafs_checker == "t32":
            header = reader.readUInt32()
            if header == 1412641280:
                os.makedirs(name, exist_ok=True)
                reader.readInt32() ## Unknown 1
                dataOffset = reader.readInt32() #and header size
                reader.readInt32() ## Unknown
                reader.readInt32() ## Unknown
                crc = reader.readBytes(4)

                countArr = []
                sizeArr = []
                sizeOArr = []
                crcArr = []
                crcArr.append(crc)
                # Data header structure
                countArr.append(reader.readInt32()) ## Same as Unknown 1, maybe ID, or COUNT
                reader.readBytes(32) ## Unknown
                sizeOArr.append(reader.offset())
                sizeArr.append(reader.readUInt32())
                reader.readBytes(120)
                checkOff = reader.readInt32()
                reader.seek(reader.offset()-4)
                if checkOff != 0:
                    while checkOff < 10 and checkOff != 0:
                        if(reader.offset() >= dataOffset):
                            break;
                        reader.readInt32() ## Unknown 2
                        crcArr.append(reader.readBytes(4))
                        countArr.append(reader.readInt32()) ## Same as Unknown 2, maybe ID, or COUNT
                        reader.readBytes(32) ## Unknown
                        sizeOArr.append(reader.offset())
                        sizeArr.append(reader.readUInt32())
                        reader.readBytes(120)
                        checkOff = reader.readInt32()
                        reader.seek(reader.offset()-4)
                print(sizeArr)
                reader.seek(dataOffset)
                index = 0
                if mode == "p":
                    nn = f"{name}_new.{tafs_checker}"
                    newFile = open(nn, "wb")
                    r = BinaryStream(newFile)
                    reader.seek(0)
                    r.writeBytes(reader.readBytes(dataOffset))

                fileData = []
                for count in countArr:
                    sizeR = []
                    for e in range(count):
                        crcN = crcArr[index].hex()
                        dname = f"{name}/{crcN}.{e}.dds"
                        if mode == "u":
                            with open(dname, "wb") as tFile:
                                tFile.write(reader.readBytes(sizeArr[index]))
                        elif mode == "p":
                            with open(dname, "rb") as tFile:
                                tFile.seek(0, os.SEEK_END)
                                size = tFile.tell()
                                sizeR.append(size)
                                tFile.seek(0)
                                fileData.append(tFile.read())

                    for i in range(len(sizeR)):
                        s = sizeR[i]
                        maxSize = max(sizeR)
                        if maxSize != s:
                            for a in range(maxSize-s):
                                fileData[i] += b'\x00'

                    if mode == "p":
                        r.seek(sizeOArr[index])
                        r.writeUInt32(maxSize)

                    index += 1

                if mode == "p":
                    r.seek(dataOffset)
                    for i in range(len(fileData)):
                        r.writeBytes(fileData[i])

                if mode == "p":
                    newFile.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = 'Texture Repacker (DMC1)', epilog = 'Work in progress')
    parser.add_argument("filename", help = "File")
    parser.add_argument("-p", "--pack", help = "Pack file", default=False, action = argparse.BooleanOptionalAction)
    args = parser.parse_args()
    fp = Path(args.filename)

    if args.pack:
        process = "p"
    else:
        process = "u"

    process_file(fp, process)
