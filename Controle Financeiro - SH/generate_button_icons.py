import os
import struct

p = r'D:\Repositorios\DaVita\Controle Financeiro - SH\imagens'
os.makedirs(p, exist_ok=True)
icons = [
    ('icon_add.bmp', [(14, 6, 18, 26), (6, 14, 26, 18)]),
    ('icon_remove.bmp', [(6, 14, 26, 18)]),
    ('icon_edit.bmp', None),
]

for name, rects in icons:
    w, h = 32, 32
    row_bytes = ((w * 3 + 3) // 4) * 4
    pixel_data = bytearray(row_bytes * h)

    def set_pixel(x, y, color):
        if 0 <= x < w and 0 <= y < h:
            idx = (h - 1 - y) * row_bytes + x * 3
            pixel_data[idx:idx + 3] = bytes(color)

    for y in range(h):
        for x in range(w):
            set_pixel(x, y, (255, 255, 255))

    if rects is None:
        for i in range(16):
            set_pixel(8 + i, 24 - i, (0, 0, 0))
            set_pixel(12 + i, 28 - i, (0, 0, 0))
        for x in range(8, 25):
            set_pixel(x, 24, (0, 0, 0))
        for y in range(8, 25):
            set_pixel(24, y, (0, 0, 0))
    else:
        for x0, y0, x1, y1 in rects:
            for x in range(x0, x1):
                for y in range(y0, y1):
                    set_pixel(x, y, (0, 0, 0))

    filesize = 54 + len(pixel_data)
    with open(os.path.join(p, name), 'wb') as f:
        f.write(b'BM')
        f.write(struct.pack('<IHHI', filesize, 0, 0, 54))
        f.write(struct.pack('<IiiHHIIiiII', 40, w, h, 1, 24, 0, len(pixel_data), 0, 0, 0, 0))
        f.write(pixel_data)

    print('created', name)
