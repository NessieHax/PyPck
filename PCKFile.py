from dataclasses import dataclass, field
import os
import pprint
import struct
from typing import overload

from InputStream import InputStream
from PCKFileEntry import PCKFileEntry
from PCKMetaEntry import PCKMetaEntry

def getEntryNameFromIndex(meta_data: list[PCKMetaEntry], index: int) -> str:
    for meta_entry in meta_data:
        if meta_entry.index == index:
            return meta_entry.name
    raise ValueError(f"ERROR: entry not found ({index = :08x})")

@dataclass
class PCKProperty:
    key: str
    value: str

    @overload
    def __init__(self, stream: InputStream, meta_data: list[PCKMetaEntry]) -> None: ...
    def __init__(self, stream: InputStream, meta_data: list[PCKMetaEntry]) -> None:
        entry_index, strlen = struct.unpack(">2i", stream.read(8))
        self.value = stream.read(strlen*2).decode("UTF-16BE")
        stream.read(4)
        self.key = getEntryNameFromIndex(meta_data, entry_index)

@dataclass
class PCKDataEntry:
    info: PCKFileEntry
    data: bytes = field(default_factory=bytes)
    properties: list[PCKProperty] = field(default_factory=list)

@dataclass(init=False, slots=True, repr=False)
class PCKFile:
    
    pck_type: int = 3
    meta_data: list[PCKMetaEntry] = field(default_factory=list)
    file_entries: list[PCKFileEntry] = field(default_factory=list)
    data: list[PCKDataEntry] = field(default_factory=list, repr=False)

    def __init__(self, stream: InputStream) -> None:
        self.pck_type, entry_count = struct.unpack(">2i", stream.read(8))
        self.meta_data = list()
        self.file_entries = list()
        self.data = list()
        has_xmlversio_tag = False
        for _ in range(entry_count):
            index, strlen = struct.unpack(">2i", stream.read(8))
            name = stream.read(strlen*2).decode("UTF-16BE")
            if name == "XMLVERSION": has_xmlversio_tag = True
            self.meta_data.append(PCKMetaEntry(index, name))
            stream.read(4)

        if has_xmlversio_tag:
            unk_val = struct.unpack(">i", stream.read(4))[0] # do useless read
            print(f"{unk_val = }")
        file_entry_count = struct.unpack(">i", stream.read(4))[0]
        for _ in range(file_entry_count):
            file_size, file_type, strlen = struct.unpack(">3i", stream.read(12))
            file_name = stream.read(strlen*2).decode("UTF-16BE")
            self.file_entries.append(PCKFileEntry(file_size, file_type, file_name))
            stream.read(4)

        for file_entry in self.file_entries:
            tag_count = struct.unpack(">i", stream.read(4))[0]
            tag_properties: list = list[PCKProperty]()
            for _ in range(tag_count):
                _property = PCKProperty(stream, self.meta_data)
                tag_properties.append(_property)

            self.data.append(PCKDataEntry(file_entry, stream.read(file_entry.size), tag_properties))

    def getEntryNameFromIndex(self, index: int) -> str:
        return getEntryNameFromIndex(self.meta_data, index)

    def dump(self, folder: str) -> None:
        if not os.path.exists(folder):
            os.mkdir(folder)
        for data_info in self.data:
            if "/" in data_info.info.name:
                path = "/".join(data_info.info.name.split("/")[:-1])
                if not os.path.exists(f"{folder}/{path}"):
                    os.makedirs(f"{folder}/{path}")
            with open(f"{folder}/{data_info.info.name}", "wb") as output:
                output.write(data_info.data)

    def __repr__(self) -> str:
        file_properties = ""
        for data_entry in self.data:
            file_properties += data_entry.info.name+"\n"
            file_properties += "\n".join([f">{_property.key}: {_property.value}" for _property in data_entry.properties])
            file_properties += "\n\n"
        return f"""{self.pck_type = }
{pprint.pformat(self.meta_data)}

{pprint.pformat(self.file_entries)}

{file_properties}"""