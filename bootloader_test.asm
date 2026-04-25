; ============================================================
; bootloader.asm - Bootloader Manual Yuui-OS
; Escreve "YUUI-OS" na tela via memoria VGA
; ============================================================

[BITS 16]
[ORG 0x7C00]

start:
    ; Configura segmentos
    xor ax, ax
    mov ds, ax
    mov es, ax
    mov ss, ax
    mov sp, 0x7C00
    
    ; Limpa a tela
    mov ax, 0x0720
    mov cx, 2000
    mov di, 0xB800
    mov es, di
    xor di, di
    rep stosw
    
    ; Escreve "YUUI-OS" na tela
    mov si, msg
    mov di, 0xB800
    mov es, di
    mov di, 0
    mov ah, 0x0A

.print:
    lodsb
    test al, al
    jz .done
    stosw
    jmp .print

.done:
    cli
    hlt
    jmp .done

msg: db 'YUUI-OS', 0

times 510-($-$$) db 0
dw 0xAA55
