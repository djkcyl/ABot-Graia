from io import BytesIO


class Entry:
    def __init__(self, word: str, pinyin: list[str], _):
        self.word = word
        self.pinyin = pinyin


class SogouScel:
    @staticmethod
    def read_uint16(file):
        return int.from_bytes(file.read(2), byteorder="little")

    @staticmethod
    def read_uint32(file):
        return int.from_bytes(file.read(4), byteorder="little")

    @staticmethod
    def decode(data, encoding):
        return data.decode(encoding)

    @staticmethod
    def parse(scel: bytes) -> list[Entry]:
        with BytesIO(scel) as file:
            # 不展开的词条数
            file.seek(0x120)
            dict_len = SogouScel.read_uint32(file)

            # 拼音表偏移量
            file.seek(0x1540)

            # 前两个字节是拼音表长度，413
            py_table_len = SogouScel.read_uint16(file)
            py_table = [None] * py_table_len

            # 丢掉两个字节
            file.seek(2, 1)

            # 读拼音表
            for _ in range(py_table_len):
                # 索引，2字节
                idx = SogouScel.read_uint16(file)
                # 拼音长度，2字节
                py_len = SogouScel.read_uint16(file)
                # 拼音 utf-16le
                tmp = file.read(py_len)
                py = SogouScel.decode(tmp, "UTF-16LE")
                py_table[idx] = py

            # 读码表
            ret = []
            for _ in range(dict_len):
                # 重码数（同一串音对应多个词）
                repeat = SogouScel.read_uint16(file)

                # 索引数组长
                pinyin_size = SogouScel.read_uint16(file)

                # 读取编码
                pinyin = []
                for _ in range(pinyin_size // 2):
                    the_idx = SogouScel.read_uint16(file)
                    if the_idx >= py_table_len:
                        pinyin.append(chr(the_idx - py_table_len + 97))
                    else:
                        pinyin.append(py_table[the_idx])

                # 读取一个或多个词
                for _ in range(repeat):
                    # 词长
                    word_size = SogouScel.read_uint16(file)

                    # 读取词
                    tmp = file.read(word_size)
                    word = SogouScel.decode(tmp, "UTF-16LE")

                    # 末尾的补充信息，作用未知
                    ext_size = SogouScel.read_uint16(file)
                    file.read(ext_size)

                    ret.append(Entry(word, pinyin, 1))

            if file.tell() < 16:
                return ret

            # 黑名单
            file.seek(12, 1)
            black_len = SogouScel.read_uint16(file)
            black_list = []
            for _ in range(black_len):
                word_len = SogouScel.read_uint16(file)
                tmp = file.read(word_len * 2)
                word = SogouScel.decode(tmp, "UTF-16LE")
                black_list.append(word)

            return ret
