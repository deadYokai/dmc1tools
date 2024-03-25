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
        header = reader.readBytes(4)
        if mode == "u":
            os.makedirs(f"_{name}", exist_ok=True)

        if mode == "p":
            if not os.path.isdir(f"_{name}"):
                print("No data to pack")
                exit()

        if header == b'\x002MT':
            count = reader.readInt32()
            dataOff = reader.readInt32()
            blockSize = reader.readInt32()
            reader.readInt32()
            crc = reader.readBytes(4).hex()
            countArr = []
            sizeArr = []
            sizeOArr = []
            crcArr = []
            crcArr.append(crc)
            countArr.append(count)
            reader.readBytes(36)
            sizeOArr.append(reader.offset())
            sizeArr.append(reader.readUInt32())
            reader.readBytes(120)
            checkOff = reader.readInt32()
            reader.seek(reader.offset()-4)
            if checkOff != 0:
                while checkOff < 10 and checkOff != 0:
                    if(reader.offset() >= dataOff):
                        break;
                    countArr.append(reader.readInt32())
                    crcArr.append(reader.readBytes(4).hex())
                    reader.readBytes(36)
                    sizeOArr.append(reader.offset())
                    sizeArr.append(reader.readUInt32())
                    reader.readBytes(120)
                    checkOff = reader.readInt32()
                    reader.seek(reader.offset()-4)

            reader.seek(dataOff)
            index = 0
            if mode == "p":
                nn = f"{name}_new.{tafs_checker}"
                newFile = open(nn, "wb")
                r = BinaryStream(newFile)
                reader.seek(0)
                r.writeBytes(reader.readBytes(dataOff))

            fileData = []
            for count in countArr:
                sizeR = []
                for e in range(count):
                    crcN = crcArr[index]
                    dname = os.path.join(f"_{name}", f"{crcN}.{e}.dds")
                    if mode == "u":
                        with open(dname, "wb") as tFile:
                            tFile.write(reader.readBytes(sizeArr[index]))
                            print(f"Extracted: {dname}")
                    elif mode == "p":
                        with open(dname, "rb") as tFile:
                            tFile.seek(0, os.SEEK_END)
                            size = tFile.tell()
                            sizeR.append(size)
                            tFile.seek(0)
                            fileData.append(tFile.read())
                            print(f"Packing: {dname}")

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
                r.seek(dataOff)
                for i in range(len(fileData)):
                    r.writeBytes(fileData[i])

            if mode == "p":
                newFile.close()

        elif header == b'ipum':
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
                tName = os.path.join(f"_{name}", f"{name}.{f}.dds")
                if mode == "u":
                    with open(tName, "wb") as tF:
                        tF.write(reader.readBytes(size))
                        print(f"Extracted: {tName}")
                elif mode == "p":
                    with open(tName, "rb") as tF:
                        tF.seek(0, os.SEEK_END)
                        mSize = tF.tell()
                        tF.seek(0)
                        print(f"Packing: {tName}")

                        r.writeUInt32(somedata)
                        r.writeUInt32(mSize)
                        r.writeBytes(tF.read())
                    reader.readBytes(size) # add offset to reader
            if mode == "p":
                moddedFile.close()

        elif header == b'\x0023T':
            os.makedirs(f"_{name}", exist_ok=True)
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
                    dname = os.path.join(f"_{name}", f"{crcN}.{e}.dds")
                    if mode == "u":
                        with open(dname, "wb") as tFile:
                            tFile.write(reader.readBytes(sizeArr[index]))
                            print(f"Extracted: {dname}")
                    elif mode == "p":
                        with open(dname, "rb") as tFile:
                            tFile.seek(0, os.SEEK_END)
                            size = tFile.tell()
                            sizeR.append(size)
                            tFile.seek(0)
                            fileData.append(tFile.read())
                            print(f"Packing: {dname}")

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

        else:
            if mode == "u":
                os.removedirs(f"_{name}")
                print(f"Header '{header}' not supported")

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
