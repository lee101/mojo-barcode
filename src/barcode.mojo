from std.sys.info import simd_width_of


comptime BPtr = UnsafePointer[UInt8, AnyOrigin[mut=True]]
comptime IPtr = UnsafePointer[Int64, AnyOrigin[mut=True]]
comptime SIMD_WIDTH = simd_width_of[DType.float64]()

comptime EAN_A = String(
    "0001101001100100100110111101010001101100010101111011101101101110001011"
)
comptime EAN_B = String(
    "0100111011001100110110100001001110101110010000101001000100010010010111"
)
comptime EAN_C = String(
    "1110010110011011011001000010101110010011101010000100010010010001110100"
)
comptime EAN_PARITY = String(
    "AAAAAAAABABBAABBABAABBBAABAABBABBAABABBBAAABABABABABBAABBABA"
)
comptime CODE39_RECORDS = String(
    "01010001110111010111010001010111010111000101011101110111000101010101000111010111"
    "01110100011101010101110001110101010100010111011101110100010111010101110001011101"
    "01110101000101110101110100010111011101110100010101010111000101110111010111000101"
    "01011101110001010101010001110111011101010001110101011101000111010101011100011101"
    "01110101010001110101110101000111011101110101000101010111010001110111010111010001"
    "01011101110100010101010111000111011101010111000101011101011100010101011101110001"
    "01110001010101110100011101010111011100011101010101000101110101110111000101110101"
    "01000111011101010100010101110111011100010101110101000111010111010100010001000101"
    "010001000101000101000101000100010101000100010001"
)
comptime CODE39_EDGE = String("100010111011101")
comptime CODE128 = String(
    "1101100110011001101100110011001101001001100010010001100100010011001001100100010011000100"
    "1000110010011001001000110010001001100010010010110011100100110111001001100111010111001100"
    "1001110110010011100110110011100101100101110011001001110110111001001100111010011101101110"
    "1110100110011100101100111001001101110110010011100110100111001100101101101100011011000110"
    "1100011011010100011000100010110001000100011010110001000100011010001000110001011010001000"
    "1100010100011000100010101101110001011000111010001101110101110110001011100011010001110110"
    "1110111011011010001110110001011101101110100011011100010110111011101110101100011101000110"
    "1110001011011101101000111011000101110001101011101111010110010000101111000101010100110000"
    "1010000110010010110000100100001101000010110010000100110101100100001011000010010011010000"
    "1001100001010000110100100001100101100001001011001010000111101110101100001010010001111010"
    "1010011110010010111100100100111101011110010010011110100100111100101111010010011110010100"
    "1111001001011011011110110111101101111011011010101111000101000111101000101111010111101000"
    "1011110001011110101000111101000101011101111010111101110111010111101111010111011010000100"
    "1101001000011010011100"
)
comptime CODE128_STOP = String("1100011101011")
comptime ITF = String(
    "NNWWNWNNNWNWNNWWWNNNNNWNWWNWNNNWWNNNNNWWWNNWNNWNWN"
)
comptime CODABAR_CODES = String(
    "NnNnNwWNnNnWwNNnNwNnWWwNnNnNNnWnNwNWnNnNwNNwNnNnW"
    "NwNnWnNNwWnNnNWnNwNnNNnNwWnNNnWwNnNWnNnWnWWnWnNnW"
    "WnWnWnNNnWnWnW"
)
comptime CODABAR_START = String("NnWwNwNNwNwNnWNnNwNwWNnNwWwN")


def put_string(src: UnsafePointer[UInt8, _], width: Int, dst: BPtr, pos: Int) -> Int:
    var i = 0
    while i + SIMD_WIDTH <= width:
        dst.store(pos + i, src.load[width=SIMD_WIDTH](i))
        i += SIMD_WIDTH
    while i < width:
        dst[pos + i] = src[i]
        i += 1
    return pos + width


def put_table(
    table: UnsafePointer[UInt8, _], index: Int, width: Int, dst: BPtr, pos: Int
) -> Int:
    var base = index * width
    for i in range(width):
        dst[pos + i] = table[base + i]
    return pos + width


def put_table_simd(
    table: UnsafePointer[UInt8, _], index: Int, width: Int, dst: BPtr, pos: Int
) -> Int:
    var base = index * width
    var i = 0
    while i + SIMD_WIDTH <= width:
        dst.store(pos + i, table.load[width=SIMD_WIDTH](base + i))
        i += SIMD_WIDTH
    while i < width:
        dst[pos + i] = table[base + i]
        i += 1
    return pos + width


def digit(src: BPtr, i: Int) -> Int:
    return Int(src[i]) - 48


def ean(src: BPtr, n: Int, dst: BPtr, guard: Bool) -> Int:
    var edge = String("101").unsafe_ptr()
    var middle = String("01010").unsafe_ptr()
    var a = EAN_A.unsafe_ptr()
    var b = EAN_B.unsafe_ptr()
    var c = EAN_C.unsafe_ptr()
    var parity = EAN_PARITY.unsafe_ptr()
    var pos = 0
    for i in range(3):
        dst[pos] = UInt8(71) if guard and edge[i] == UInt8(49) else edge[i]
        pos += 1
    var lead = digit(src, 0)
    for i in range(6):
        var d = digit(src, i + 1)
        if parity[lead * 6 + i] == UInt8(65):
            pos = put_table(a, d, 7, dst, pos)
        else:
            pos = put_table(b, d, 7, dst, pos)
    for i in range(5):
        dst[pos] = UInt8(71) if guard and middle[i] == UInt8(49) else middle[i]
        pos += 1
    for i in range(7, n):
        pos = put_table(c, digit(src, i), 7, dst, pos)
    for i in range(3):
        dst[pos] = UInt8(71) if guard and edge[i] == UInt8(49) else edge[i]
        pos += 1
    return pos


def ean8(src: BPtr, dst: BPtr, guard: Bool) -> Int:
    var edge = String("101").unsafe_ptr()
    var middle = String("01010").unsafe_ptr()
    var a = EAN_A.unsafe_ptr()
    var c = EAN_C.unsafe_ptr()
    var pos = 0
    for i in range(3):
        dst[pos] = UInt8(71) if guard and edge[i] == UInt8(49) else edge[i]
        pos += 1
    for i in range(4):
        pos = put_table(a, digit(src, i), 7, dst, pos)
    for i in range(5):
        dst[pos] = UInt8(71) if guard and middle[i] == UInt8(49) else middle[i]
        pos += 1
    for i in range(4, 8):
        pos = put_table(c, digit(src, i), 7, dst, pos)
    for i in range(3):
        dst[pos] = UInt8(71) if guard and edge[i] == UInt8(49) else edge[i]
        pos += 1
    return pos


def code39_index(ch: Int) -> Int:
    if ch >= 48 and ch <= 57:
        return ch - 48
    if ch >= 65 and ch <= 90:
        return ch - 55
    if ch == 45:
        return 36
    if ch == 46:
        return 37
    if ch == 32:
        return 38
    if ch == 36:
        return 39
    if ch == 47:
        return 40
    if ch == 43:
        return 41
    return 42


def encode_code39(src: BPtr, n: Int, dst: BPtr) -> Int:
    var table = CODE39_RECORDS.unsafe_ptr()
    var edge = CODE39_EDGE.unsafe_ptr()
    _ = put_string(edge, 15, dst, 0)

    @parameter
    def encode_character(i: Int):
        var pos = 15 + i * 16
        _ = put_table_simd(table, code39_index(Int(src[i])), 16, dst, pos)

    for i in range(n):
        encode_character(i)
    var end = 15 + n * 16
    dst[end] = UInt8(48)
    return put_string(edge, 15, dst, end + 1)


def code128_a(ch: Int) -> Int:
    if ch >= 32 and ch <= 95:
        return ch - 32
    if ch <= 31:
        return ch + 64
    if ch == 243:
        return 96
    if ch == 242:
        return 97
    if ch == 244:
        return 101
    return 102


def code128_b(ch: Int) -> Int:
    if ch >= 32 and ch <= 127:
        return ch - 32
    if ch == 243:
        return 96
    if ch == 242:
        return 97
    if ch == 244:
        return 100
    return 102


def valid_a(ch: Int) -> Bool:
    return ch <= 95 or ch >= 241


def valid_b(ch: Int) -> Bool:
    return (ch >= 32 and ch <= 127) or ch >= 241


def digit_run(src: BPtr, n: Int, pos: Int) -> Bool:
    var count = 0
    var stop = min(n, pos + 10)
    for i in range(pos, stop):
        var ch = Int(src[i])
        if ch < 48 or ch > 57:
            break
        count += 1
    return count > 3


def encode_code128(
    src: BPtr, n: Int, dst: BPtr, codes: IPtr, fnc1_special: Bool
) -> Int:
    var charset = 2
    var buffered = -1
    var count = 1
    codes[1] = 105
    for i in range(n):
        var ch = Int(src[i])
        if charset == 2 and (ch < 48 or ch > 57):
            if not (fnc1_special and ch == 241 and buffered < 0):
                if valid_b(ch):
                    codes[count + 1] = 100
                    charset = 1
                else:
                    codes[count + 1] = 101
                    charset = 0
                count += 1
                if buffered >= 0:
                    codes[count + 1] = Int64(
                        code128_b(buffered) if charset == 1 else code128_a(buffered)
                    )
                    count += 1
                    buffered = -1
        elif charset == 1:
            if digit_run(src, n, i):
                codes[count + 1] = 99
                count += 1
                charset = 2
            elif not valid_b(ch) and valid_a(ch):
                codes[count + 1] = 101
                count += 1
                charset = 0
        elif charset == 0:
            if digit_run(src, n, i):
                codes[count + 1] = 99
                count += 1
                charset = 2
            elif not valid_a(ch) and valid_b(ch):
                codes[count + 1] = 100
                count += 1
                charset = 1

        if charset == 2:
            if ch == 241:
                codes[count + 1] = 102
                count += 1
            elif buffered < 0:
                buffered = ch
            else:
                codes[count + 1] = Int64((buffered - 48) * 10 + ch - 48)
                count += 1
                buffered = -1
        elif charset == 1:
            codes[count + 1] = Int64(code128_b(ch))
            count += 1
        else:
            codes[count + 1] = Int64(code128_a(ch))
            count += 1

    if buffered >= 0:
        codes[count + 1] = 100
        count += 1
        codes[count + 1] = Int64(code128_b(buffered))
        count += 1
    if codes[1] == 105 and count > 1 and (codes[2] == 100 or codes[2] == 101):
        codes[1] = 104 if codes[2] == 100 else 103
        for i in range(2, count):
            codes[i] = codes[i + 1]
        count -= 1

    var checksum = Int(codes[1])
    for i in range(2, count + 1):
        checksum += (i - 1) * Int(codes[i])
    checksum %= 103
    codes[count + 1] = Int64(checksum)
    count += 1
    codes[0] = Int64(count - 1)

    var table = CODE128.unsafe_ptr()
    var pos = 0
    for i in range(1, count + 1):
        pos = put_table_simd(table, Int(codes[i]), 11, dst, pos)
    return put_string(CODE128_STOP.unsafe_ptr(), 13, dst, pos)


def expand_widths(data: BPtr, n: Int, narrow: Int, wide: Int, dst: BPtr) -> Int:
    var pos = 0
    for i in range(n):
        var ch = Int(data[i])
        var width = wide if ch == 87 or ch == 119 else narrow
        var value = UInt8(49) if ch == 87 or ch == 78 else UInt8(48)
        for _ in range(width):
            dst[pos] = value
            pos += 1
    return pos


def encode_itf(src: BPtr, n: Int, narrow: Int, wide: Int, dst: BPtr) -> Int:
    var patterns = ITF.unsafe_ptr()
    var pos = 0
    var start = String("NnNn").unsafe_ptr()
    for i in range(4):
        var ch = start[i]
        var width = narrow
        var value = UInt8(49) if ch == UInt8(78) else UInt8(48)
        for _ in range(width):
            dst[pos] = value
            pos += 1
    for i in range(0, n, 2):
        var bars = digit(src, i) * 5
        var spaces = digit(src, i + 1) * 5
        for j in range(5):
            var bw = wide if patterns[bars + j] == UInt8(87) else narrow
            var sw = wide if patterns[spaces + j] == UInt8(87) else narrow
            for _ in range(bw):
                dst[pos] = UInt8(49)
                pos += 1
            for _ in range(sw):
                dst[pos] = UInt8(48)
                pos += 1
    var stop = String("WnN").unsafe_ptr()
    for i in range(3):
        var ch = stop[i]
        var width = wide if ch == UInt8(87) else narrow
        var value = UInt8(49) if ch == UInt8(87) or ch == UInt8(78) else UInt8(48)
        for _ in range(width):
            dst[pos] = value
            pos += 1
    return pos


def codabar_data_index(ch: Int) -> Int:
    if ch >= 48 and ch <= 57:
        return ch - 48
    if ch == 45:
        return 10
    if ch == 36:
        return 11
    if ch == 58:
        return 12
    if ch == 47:
        return 13
    if ch == 46:
        return 14
    return 15


def encode_codabar(src: BPtr, n: Int, narrow: Int, wide: Int, dst: BPtr) -> Int:
    var patterns = CODABAR_CODES.unsafe_ptr()
    var starts = CODABAR_START.unsafe_ptr()
    var pos = 0
    var start_idx = (Int(src[0]) - 65) * 7
    for j in range(7):
        var ch = Int(starts[start_idx + j])
        var width = wide if ch == 87 or ch == 119 else narrow
        var value = UInt8(49) if ch == 87 or ch == 78 else UInt8(48)
        for _ in range(width):
            dst[pos] = value
            pos += 1
    for i in range(1, n - 1):
        for _ in range(narrow):
            dst[pos] = UInt8(48)
            pos += 1
        var base = codabar_data_index(Int(src[i])) * 7
        for j in range(7):
            var ch = Int(patterns[base + j])
            var width = wide if ch == 87 or ch == 119 else narrow
            var value = UInt8(49) if ch == 87 or ch == 78 else UInt8(48)
            for _ in range(width):
                dst[pos] = value
                pos += 1
    for _ in range(narrow):
        dst[pos] = UInt8(48)
        pos += 1
    var end_idx = (Int(src[n - 1]) - 65) * 7
    for j in range(7):
        var ch = Int(starts[end_idx + j])
        var width = wide if ch == 87 or ch == 119 else narrow
        var value = UInt8(49) if ch == 87 or ch == 78 else UInt8(48)
        for _ in range(width):
            dst[pos] = value
            pos += 1
    return pos
