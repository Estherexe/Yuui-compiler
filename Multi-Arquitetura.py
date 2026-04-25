# Para ARM (Raspberry Pi)
def _montar_binario_arm(self, arquivo_asm):
    subprocess.run(['arm-linux-gnueabi-as', ...])

# Para WebAssembly
def _montar_wasm(self, arquivo_asm):
    subprocess.run(['wat2wasm', ...])