from dataclasses import dataclass, field
import os
import pprint
import struct

from InputStream import InputStream
from PCKFileEntry import PCKFileEntry

PCKProperties = list[tuple[str, str]]
PCKMeta = dict[int, str]

@dataclass
class PCKFileData:
    info: PCKFileEntry
    data: bytes = field(default_factory=bytes, repr=False)
    properties: PCKProperties = field(default_factory=PCKProperties)

@dataclass(slots=True, repr=False)
class PCKFile:
    
    pck_type: int = -1
    fmt: str = field(default=">", repr=False)
    meta: PCKMeta = field(default_factory=PCKMeta)
    file_entries: list[PCKFileEntry] = field(default_factory=list)
    data: list[PCKFileData] = field(default_factory=list, repr=False)

    def parse(self, stream: InputStream) -> None:
        self.pck_type = self.readInt(stream)
        self.readMetaEntries(stream)
        self.readFileEntries(stream)
        for file_entry in self.file_entries:
            property_count = self.readInt(stream)
            file_properties = PCKProperties()
            for _ in range(property_count):
                entry_index = self.readInt(stream)
                value = self.readString(stream)
                stream.read(4)
                key = self.getEntryNameFromIndex(entry_index)
                file_properties.append((key,value))
            self.data.append(PCKFileData(file_entry, stream.read(file_entry.size), file_properties))

    def readMetaEntries(self, stream: InputStream) -> None:
        has_xmlversio_tag = False
        meta_entry_count = self.readInt(stream)
        for _ in range(meta_entry_count):
            index = self.readInt(stream)
            name = self.readString(stream)
            if name == "XMLVERSION": has_xmlversio_tag = True
            self.meta[index] = name
            stream.read(4)

        if has_xmlversio_tag:
            xml_version = self.readInt(stream) # do useless read
            print(f"{xml_version = }")

    def writeMetaEntries(self) -> bytes:
        outdata: bytes() = bytes()
        for index, name in self.meta.items():
            outdata += struct.pack(f"{self.fmt}i{len(name)*2}s", index, name.encode("UTF-16BE"))
        if "XMLVERSION" in self.meta.values(): outdata += bytes(4)
        return outdata

    def writeFileEntries(self) -> bytes:
        outdata = bytes()
        outdata += struct.pack(self.fmt+"i", len(self.file_entries))


    def readFileEntries(self, stream: InputStream) -> None:
        file_entry_count = self.readInt(stream)
        for _ in range(file_entry_count):
            file_size, file_type = self.readInts(stream, 2)
            file_name = self.readString(stream)
            self.file_entries.append(PCKFileEntry(file_size, file_type, file_name))
            stream.read(4)

    def getEntryNameFromIndex(self, index: int) -> str:
        return self.meta[index]

    def dump(self, folder: str) -> None:
        if self.pck_type != 3: raise ValueError("pck cant be dumped")
        for data_info in self.data:
            path = f"{folder}/{os.path.dirname(data_info.info.name)}"
            if not os.path.exists(path): os.makedirs(path)
            with open(f"{folder}/{data_info.info.name}", "wb") as output:
                output.write(data_info.data)

    def readInts(self, stream: InputStream, count: int) -> tuple[int]:
        return struct.unpack(f"{self.fmt}{count}i", stream.read(count*4))

    def readInt(self, stream: InputStream) -> int:
        return self.readInts(stream, 1)[0]
    
    def readString(self, stream: InputStream) -> str:
        return stream.read(self.readInt(stream)*2).decode("UTF-16BE")

    def __repr__(self) -> str:
        return f"""{self.pck_type = }

{pprint.pformat(self.file_entries)}

{pprint.pformat(self.data)}"""