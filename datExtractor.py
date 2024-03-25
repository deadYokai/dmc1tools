from binary import BinaryStream
from pathlib import Path
import os
import argparse

import textureRepack
from contextlib import chdir

def o(fff):
    fn = fff.stem
    ff = str(fff)
    os.makedirs(f"_{fn}", exist_ok=True)
    with open(ff, "rb") as f:
        reader = BinaryStream(f)
        f.seek(0, os.SEEK_END)
        fileSize = f.tell()

        reader.seek(0)

        head = reader.readInt32()
        # head2 = reader.readInt32()

        fOffset = reader.readUInt32()
        fSize = reader.readUInt32()
        offsetLsit = []
        offsetLsit.append(fOffset)
        sizeList = []
        sizeList.append(fSize)
        while(reader.offset() < fOffset):
            data = reader.readUInt32()
            data2 = reader.readUInt32()
            if data != 0:
                offsetLsit.append(data)
                if data2 == 0:
                    reader.seek(data)
                    pos1 = reader.offset()
                    data2 = fileSize - pos1
                sizeList.append(data2)

        # offsetLsit.sort()

        for a in range(len(offsetLsit)):
            key = hex(offsetLsit[a])
            reader.seek(offsetLsit[a])
            size = sizeList[a]
            stringData = reader.readBytes(size)
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
            with open(f"_{fn}/{key}", "wb") as out:
                out.write(stringData)

            if toE:
                with chdir(f"_{fn}"):
                    textureRepack.process_file(Path(f"{key}"), "u")

            print(f"Extracted: {key}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = 'DAT/ITM Extractor (DMC1)', epilog = 'Work in progress')
    parser.add_argument("filename", help = "File")
    args = parser.parse_args()
    fp = Path(args.filename)
    o(fp)
