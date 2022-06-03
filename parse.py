import argparse
import os
import re
from InputStream import InputStream

from PCKFile import PCKFile

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pck_file", type=str)
    parser.add_argument("-d", type=str, dest="dump", help="Dumps all files of a pck file into the provided folder")
    parser.add_argument("-l", action="store_true", dest="list", help="List PCK content")
    args = parser.parse_args()

    if not os.path.exists(args.pck_file): raise FileNotFoundError("file does not exist")
    with open(args.pck_file, "rb") as pck:
        pck_file = PCKFile()
        pck_file.parse(InputStream(pck.read()))
    
    if args.list:
        print(pck_file)
    if args.dump:
        path = f"dump/{args.dump}"
        if not os.path.exists(path): os.makedirs(path)
        pck_file.dump(path)

if __name__ == "__main__":
    main()