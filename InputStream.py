from dataclasses import dataclass
import sys

class InputStream: ...

class EndOfStreamException(Exception): ...

@dataclass(init=False, slots=True)
class InputStream:
    __pos: int
    __data: bytes
    __dataSize: int

    def __init__(self, data: bytes) -> None:
        self.__data = data
        self.__dataSize = len(data)
        self.__pos = 0

    def __increment(self, amount: int) -> None:
        if not self.__hasEnoughSpace(self.__pos, amount): raise EndOfStreamException("not enough space to set buffer position")
        self.__pos += amount
    
    def __read(self, pos: int, size: int) -> bytes:
        # print(f"[{self.__class__.__name__}] {pos = } {size = } {self.__dataSize = }", file=sys.stderr)
        if not self.__hasEnoughSpace(pos, size): raise EndOfStreamException(f"not enough space to read {size} bytes")
        return self.__data[pos:pos+size]

    def readWithPos(self, pos: int, size: int) -> bytes:
        return self.__read(pos=pos, size=size)

    def read(self, size: int) -> bytes:
        data = self.__read(pos=self.__pos, size=size)
        self.__increment(size)
        return data

    def getSubStream(self, size: int) -> InputStream:
        return InputStream(self.read(size))

    def __isValidPosition(self, pos: int) -> bool:
        return pos <= self.__dataSize

    def __hasEnoughSpace(self, pos: int, size: int) -> bool:
        return self.__isValidPosition(pos+size)

    def atEnd(self) -> bool:
        return not self.__isValidPosition(self.__pos+1)

    def hasNext(self) -> bool:
        return self.__hasEnoughSpace(self.__pos, 1)