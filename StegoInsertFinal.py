import gradio as gr
from PIL import Image
import hashlib, base64
from cryptography.fernet import Fernet, InvalidToken

# Key derivation using SHA256-based Fernet key
def derive_key(password: str) -> bytes:
    digest = hashlib.sha256(password.encode('utf-8')).digest()
    return base64.urlsafe_b64encode(digest)

# Encrypt/decrypt payload

def encrypt_payload(data: bytes, password: str) -> bytes:
    return Fernet(derive_key(password)).encrypt(data)

def decrypt_payload(token: bytes, password: str) -> bytes:
    return Fernet(derive_key(password)).decrypt(token)

# Prepare the bit list: [flag][32-bit length][payload bits]
def prepare_bits(text: str, password: str) -> list:
    payload = text.encode('utf-8')
    flag = 1 if password else 0
    if password:
        payload = encrypt_payload(payload, password)
    length = len(payload)
    bits = []
    # flag bit
    bits.append(flag)
    # length bits (32-bit big-endian)
    for i in range(32):
        bits.append((length >> (31 - i)) & 1)
    # payload bits
    for byte in payload:
        for i in range(8):
            bits.append((byte >> (7 - i)) & 1)
    return bits

# Embed LSB
def embed_data(img: Image.Image, bits: list) -> Image.Image:
    img = img.convert('RGB')
    flat = [channel for pixel in img.getdata() for channel in pixel]
    if len(bits) > len(flat):
        raise ValueError(f"Not enough capacity: need {len(bits)} bits, have {len(flat)} bits")
    for idx, bit in enumerate(bits):
        flat[idx] = (flat[idx] & ~1) | bit
    stego = Image.new('RGB', img.size)
    stego.putdata([tuple(flat[i:i+3]) for i in range(0, len(flat), 3)])
    return stego

# Extract bits and reconstruct message
def extract_data(img: Image.Image):
    flat = [channel for pixel in img.convert('RGB').getdata() for channel in pixel]
    # flag
    flag = flat[0] & 1
    # length
    length = 0
    for i in range(1, 33):
        length = (length << 1) | (flat[i] & 1)
    # payload bits
    start = 33
    payload_bytes = bytearray()
    for i in range(start, start + length * 8, 8):
        byte = 0
        for j in range(8):
            byte = (byte << 1) | (flat[i + j] & 1)
        payload_bytes.append(byte)
    return flag, bytes(payload_bytes)

# Handlers for Gradio
def hide_handler(img, text, pwd):
    bits = prepare_bits(text or "", pwd or "")
    return embed_data(img, bits)

def extract_handler(img, pwd):
    flag, data = extract_data(img)
    if flag:
        try:
            data = decrypt_payload(data, pwd or "")
        except InvalidToken:
            return "ERROR: wrong password"
    return data.decode('utf-8', errors='ignore')

# Gradio Interfaces
iface_hide = gr.Interface(
    fn=hide_handler,
    inputs=[gr.Image(type="pil", label="Input Image"),
            gr.Textbox(lines=2, label="Text to Hide"),
            gr.Textbox(type="password", label="Password (optional)")],
    outputs=gr.Image(type="pil", label="Stego Image"),
    title="Hide Text"
)

iface_extract = gr.Interface(
    fn=extract_handler,
    inputs=[gr.Image(type="pil", label="Stego Image"),
            gr.Textbox(type="password", label="Password (if encrypted)")],
    outputs=gr.Textbox(lines=2, label="Extracted Text"),
    title="Extract Text"
)

demo = gr.TabbedInterface([iface_hide, iface_extract], ["Hide", "Extract"])

demo.launch()
