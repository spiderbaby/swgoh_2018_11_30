import os
import re
import urllib.request
import PIL
from PIL import Image
import binascii

# Step 1. Go to https://goo.gl/4HXR42 amd download madness.jpg
# Thanks to: jeffnorth86, Mrtops, CrimsonBadger for the initial work and
# newershadow for the cleaned up hex translation

# Step 2. Convert the binary codes in the ASCII file madness.jpg to
# ASCII characters (double ASCII encoding o.O) 
if not os.path.exists('input_text.txt'):
    input_text = ''
    with open('madness.jpg') as f:
        input_text = ''.join([chr(int(t, 2)) for t in f.read().split()])
    with open('input_text.txt', 'w') as f:
        f.write(input_text)
input_text = open('input_text.txt').read()

# Pull out the characters we care about (after the '///' and before the 'x/')
input_text = re.match('^.*///(.*?)x/.*$', input_text).group(1)

# Clean up the text to make it easier to read by eye and to tokenize later.
# Add spaces between z (rests) and notes
# Remove commas
input_text = re.sub(r'(z\d*)([.A-G])', r'\1 \2', input_text)
input_text = input_text.replace(',', '').replace('z ', 'z1 ')

# Step 3. NaFakCha and newershadow worked out that the §12/14 was a Solfa key represented
# as a date. 2018-12-14 corresponds to the A Dorian scale. The first degree in that
# scale is B so we sing Do Re Mi Fa So La Ti as B, C, D, E, F, G, A (ignoring accidentals) 
# A Dorian so B is the 1st degree (we count starting from B)
a_dorian_map = dict(B='D', C='R', D='M', E='F', F='S', G='L', A='T')
# Convert the notes A to G to their degree (Do Re Fa etc.)
solfa_notation_text = ''.join([a_dorian_map.get(_,_) for _ in input_text])  # hidden bum

# The website https://www.wmich.edu/mus-theo/solfa-cipher/ deciphers Solfa ciphers but
# I found it did not work well for me with copying and pasting - I wasn't getting
# integers back. Here is the character mapping on the site:
mapping = {
    'D1': 'T', 'R1': 'I', 'M1': 'A', 'F1': 'S',  'S1': 'E', 'L1': 'N', 'T1': 'O',
    'D2': 'K', 'R2': 'Z', 'M2': 'X', 'F2': 'QØ', 'S2': 'J', 'L2': 'Å', 'T2': 'Æ',
    'D3': 'R', 'R3': 'C', 'M3': 'H', 'F3': 'M',  'S3': 'D', 'L3': 'L', 'T3': 'U',
    'D4': 'F', 'R4': 'Y', 'M4': 'G', 'F4': 'P',  'S4': 'W', 'L4': 'B', 'T4': 'V',    
    '.D1': '1', '.R1': '9', '.M1': '3', '.S1': '5', '.T1': '7',
    '.D3': '8', '.R3': '2', '.M3': '0', '.F3': '4', '.L3': '6',
}

# Step 4. Decipher
cipher_text = ''
plain_text = ''
counter = 1
rgx = re.compile('(?:[.]?[DRMFSLT]\d)|z\d')
tokens = solfa_notation_text.split()
tokens[-1] = '.M3'  # this is '.M.3' for some annoying reason
for t in tokens:
    assert rgx.match(t)
    if t[0] != 'z':
        cipher_char = '{0}{1}'.format(t[:-1], counter)
        assert cipher_char in mapping
        cipher_text += cipher_char + ' '
        plain_text += mapping[cipher_char] + ''
    # Keep count (snaps fingers)
    duration = int(t[-1])
    counter = ((counter + duration) % 4) or 4

# Step 5. Break the plain text into [number] X HEXRGB
# First, a sanity check...
blocks = re.findall(r'\d+X[0-9A-F]{6}', plain_text)
assert len(plain_text) == sum([len(b) for b in blocks])
# We did not leave any characters out. Decompress the image representation
# Thanks to newershadow for working out the the n x hexstring encoding
blocks = re.findall(r'(\d+)X([0-9A-F]{6})', plain_text)
pixels = []
for b in blocks:
    pixels += int(b[0]) * [b[1]]  # yeah, yeah, yeah terrible memory allocation
# Group into lines of 17 pixels wide (thanks to newershadow for working this out)
assert len(pixels) % 17 == 0
w, h = 17, int(len(pixels) / 17)  # determine height
# You can print this out to see the grid of colors...
lines = [pixels[i : i+17] for i in range(0, len(pixels), 17)]
#for l in lines:
#    print(l)

# ... but we do not need to since we know the dimensions
# Step 6. Reconstruct the image. Finally, the fun part!
# Use the binascii module (useful module) to convert the hex strings to bytes
image_bytes = binascii.unhexlify(''.join(pixels))
# Create the image from the array of bytes...
left_side = Image.frombytes('RGB', (w, h), image_bytes)
# but newershadow realized this was half of a mirrored image. Create the right side:
right_side = left_side.transpose(Image.FLIP_LEFT_RIGHT)
# Stitch the sides together
result = Image.new('RGB', (w * 2, h))
result.paste(left_side, (0, 0))
result.paste(right_side, (w, 0))
result.save("answer.png", "PNG")
print('Done!')
