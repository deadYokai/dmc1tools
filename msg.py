import io
import os
import sys
import struct
from wand.image import Image
import ast
content = []

with open("charindex.txt", "r") as chi:
    charTableEngText = chi.read()
    charTableEng = ast.literal_eval(charTableEngText)

msgIn = sys.argv[1]

string = ''
with open(msgIn, 'rb') as mf:
    mf.seek(0, os.SEEK_END)
    fs = mf.tell()
    mf.seek(0)
    headerCount = struct.unpack("i", mf.read(4))[0] 

    ig = 0
    for i in range(headerCount):
        mf.seek(4 + 8*i)
        off = struct.unpack('i', mf.read(4))[0]
        size = struct.unpack('i', mf.read(4))[0]
        mf.seek(off)
        data = mf.read(size)

        d = io.BytesIO(data)
        while d.tell() < size:
            dat = d.read(1)
            if dat == b'\x7E' or dat == b'\x77':
                q = d.read(1)
                if q == b'\x09' or q == b'\x0A' or q == b'\x0B':
                    a = d.read(1)
                    string += f"[{q.hex()}:{a.hex()}]"
                elif q == b'\x0E':
                    string += f"[ENDSTRING:{d.read(size - d.tell()).hex()}]\n\n"
                    break
                elif q == b'\x05':
                    string += " "
                    # with Image(width=16,height=32) as img:
                    #     img.save(filename=f"test/{i}/{ig}_space.dds")
                else:
                    string += f"[{q.hex()}]"
                continue
            itm = struct.unpack("B", dat)[0]
            try:
                string += charTableEng[itm]
            except:
                string += f"[unk({itm})]"
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
            ig += 1

with open(f"{msgIn}.txt", "w") as msgText:
    msgText.write(";;;CHARTABLE\n")
    msgText.write(charTableEngText)
    msgText.write(";;;ENDCHARTABLE\n\n")
    msgText.write(string)



