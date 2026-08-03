"""
Kreiraj .ico fajl sa DeepSeek chatbot ikonom.
32x32, 32-bitna boja (BGRA).
"""
import struct
import os

def create_ico(filepath="deepseek.ico", size=32):
    """Kreira jednostavnu .ico datoteku sa plavom pozadinom i belim 'D' slovom."""
    
    w, h = size, size
    
    # Pravimo pixel data (BGRA format)
    pixels = []
    
    # Boje
    BLUE = (0x4A, 0x90, 0xD9, 0xFF)      # #4A90D9 - DeepSeek plava
    WHITE = (0xFF, 0xFF, 0xFF, 0xFF)      # bela
    DARK_BLUE = (0x2A, 0x70, 0xB9, 0xFF)  # tamnija plava za ivice
    
    for y in range(h):
        for x in range(w):
            # Normalizujemo koordinate u -1..1
            cx, cy = (x - w/2) / (w/2), (y - h/2) / (h/2)
            dist = (cx*cx + cy*cy) ** 0.5
            
            # Krug
            if dist > 0.95:
                # Van kruga - transparentno
                pixels.append((0, 0, 0, 0))
            elif dist > 0.85:
                # Ivica kruga - tamnija plava
                pixels.append(DARK_BLUE)
            else:
                # Unutrašnjost kruga
                # Crtamo slovo "D"
                # D je napravljeno od vertikalne linije i polukruga
                
                # Vertikalna linija (levo)
                v_line = (cx < -0.45)
                
                # Horizontalna linija (gore)
                h_top = (cy < -0.7 and cx > -0.2)
                
                # Horizontalna linija (dole)
                h_bot = (cy > 0.7 and cx > -0.2)
                
                # Polukrug sa desne strane
                right_circle = ((cx - 0.15)**2 + cy**2) ** 0.5 < 0.55 and cx > -0.1
                
                # Unutrašnji izrez polukruga
                inner_hole = ((cx - 0.15)**2 + cy**2) ** 0.5 < 0.35 and cx > 0.0
                
                if v_line or h_top or h_bot or (right_circle and not inner_hole):
                    pixels.append(WHITE)
                else:
                    pixels.append(BLUE)
    
    # ICO header
    ico_header = struct.pack('<HHH', 0, 1, 1)  # reserved=0, type=1(ico), count=1
    
    # XOR mask (BGRA pixel data)
    xor_data = b''
    for r, g, b, a in pixels:
        xor_data += struct.pack('BBBB', b, g, r, a)  # BGRA format
    
    # AND mask (1 bit per pixel, 1=transparent)
    and_data = b''
    for i in range(0, len(pixels), 32):
        row_bits = 0
        for j in range(32):
            px = pixels[i + j]
            if px[3] == 0:  # transparent
                row_bits |= (1 << (31 - j))
        and_data += struct.pack('>I', row_bits)
    
    # Ukupna veličina slike
    bmp_info_size = 40
    xor_size = len(xor_data)
    and_size = len(and_data)
    image_size = bmp_info_size + xor_size + and_size
    
    # Directory entry
    # w, h, colors, reserved, planes, bpp, size, offset
    offset = 6 + 16  # header + directory entry
    dir_entry = struct.pack('<BBBBHHII', 
        w if w < 256 else 0, 
        h if h < 256 else 0, 
        0, 0,  # colors, reserved
        1,  # planes
        32,  # bpp
        image_size,
        offset
    )
    
    # BITMAPINFOHEADER
    bmp_header = struct.pack('<IiiHHIIiiII',
        40,  # biSize
        w,
        h * 2,  # XOR + AND visina
        1,  # planes
        32,  # bitCount
        0,  # compression (BI_RGB)
        xor_size + and_size,  # sizeImage
        0, 0,  # biXPelsPerMeter, biYPelsPerMeter
        0, 0  # biClrUsed, biClrImportant
    )
    
    # Spojimo sve
    with open(filepath, 'wb') as f:
        f.write(ico_header)
        f.write(dir_entry)
        f.write(bmp_header)
        f.write(xor_data)
        f.write(and_data)
    
    print(f"✅ Ikonica kreirana: {filepath} ({os.path.getsize(filepath)} bytes)")

if __name__ == "__main__":
    create_ico()
