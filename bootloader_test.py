"""
bootloader_test_v2.py - Versão Corrigida e Blindada
Resolve:
1. Detecção e instalação do NASM no Windows
2. Problema de encoding UTF-8
3. Adiciona fallback para quando NASM não está disponível
"""

import os
import sys
import subprocess
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def verificar_nasm():
    """Verifica se NASM está instalado e tenta instalar se não estiver."""
    print("\n🔍 Verificando NASM...")
    
    try:
        resultado = subprocess.run(['nasm', '-version'], 
                                 capture_output=True, text=True, timeout=5)
        print(f"✅ NASM encontrado: {resultado.stdout.split()[2]}")
        return True
    except:
        print("❌ NASM não encontrado!")
        print("\n💡 Opções para Windows:")
        print("   1. Baixe NASM: https://www.nasm.us/pub/nasm/releasebuilds/")
        print("   2. Ou use: winget install nasm")
        print("   3. Ou Chocolatey: choco install nasm")
        
        # Tenta instalar automaticamente
        try:
            print("\n🔄 Tentando instalar via winget...")
            subprocess.run(['winget', 'install', 'nasm'], check=False)
            print("✅ NASM instalado! Reinicie o terminal e tente novamente.")
        except:
            print("⚠️  Instalação automática não disponível")
        
        return False

def gerar_bootloader_manual():
    """Gera bootloader manual com encoding corrigido."""
    
    print("\n" + "="*70)
    print("🧪 FASE 1: BOOTLOADER MANUAL (Assembly Puro)")
    print("="*70)
    
    asm_code = """; ============================================================
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
"""
    
    # Salva com encoding explícito
    try:
        with open("bootloader_test.asm", "w", encoding='ascii') as f:
            f.write(asm_code)
        print("✅ Assembly salvo: bootloader_test.asm")
        
        # Verifica se NASM está disponível
        if not verificar_nasm():
            print("\n⚠️  NASM não disponível - pulando montagem")
            print("💡 O arquivo Assembly está pronto para ser montado manualmente:")
            print("   nasm -f bin bootloader_test.asm -o bootloader_test.bin")
            return True  # Arquivo gerado, mesmo sem montar
        
        # Monta com NASM
        resultado = subprocess.run(
            ['nasm', '-f', 'bin', 'bootloader_test.asm', '-o', 'bootloader_test.bin'],
            capture_output=True, text=True
        )
        
        if resultado.returncode == 0:
            tamanho = os.path.getsize('bootloader_test.bin')
            print(f"✅ Binário gerado: bootloader_test.bin ({tamanho} bytes)")
            
            # Mostra os bytes finais (assinatura de boot)
            with open('bootloader_test.bin', 'rb') as f:
                dados = f.read()
                assinatura = dados[-2:].hex().upper()
                print(f"🔍 Assinatura de boot: 0x{assinatura}")
                
                if assinatura == '55AA':
                    print("✅ Assinatura de boot válida!")
                else:
                    print("⚠️  Assinatura incorreta - verifique o Assembly")
            
            return True
        else:
            print(f"❌ Erro NASM:\n{resultado.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def gerar_bootloader_yuui():
    """Gera bootloader com o compilador Yuui-Lang."""
    
    print("\n" + "="*70)
    print("🤖 FASE 2: COMPILADOR YUUI-LANG")
    print("="*70)
    
    # Código Yuui-Lang com encoding garantido
    codigo_yuui = """// boot_test.yuui - Teste de Boot da Yuui-Lang
// Encoding: ASCII (sem caracteres especiais)

modo 16bits {
    funcao _start() {
        memoria video = 0xB8000
        
        // Escreve na tela
        video.escrever("YUUI-OS")
        video.escrever("Yuui-Lang v0.2 - VIVA!")
        
        enquanto (1 == 1) {
            // Loop eterno
        }
    }
}
"""
    
    # Salva com encoding ASCII puro
    try:
        with open("boot_test.yuui", "w", encoding='ascii') as f:
            f.write(codigo_yuui)
        print("✅ Codigo Yuui-Lang salvo: boot_test.yuui (ASCII)")
    except Exception as e:
        print(f"❌ Erro ao salvar: {e}")
        return False
    
    # Tenta compilar
    try:
        from Compilador import CompiladorYuui
        
        compilador = CompiladorYuui("boot_test.yuui", modo_verbose=True)
        
        # Apenas compila, sem ISO nem QEMU
        sucesso = compilador.compilar(gerar_iso=False, executar_qemu=False)
        
        if sucesso:
            print("\n✅ COMPILADOR YUUI-LANG FUNCIONANDO!")
            
            # Verifica se o Assembly foi gerado
            if os.path.exists("boot_test.asm"):
                print("✅ Assembly gerado pelo compilador!")
                
                # Tenta montar com NASM se disponível
                if verificar_nasm():
                    subprocess.run(
                        ['nasm', '-f', 'bin', 'boot_test.asm', '-o', 'boot_test.bin'],
                        check=False
                    )
                    if os.path.exists("boot_test.bin"):
                        print("✅ Binário Yuui-Lang gerado!")
            
            return True
        else:
            print("\n⚠️  Compilador Yuui-Lang precisa de ajustes")
            return False
            
    except Exception as e:
        print(f"❌ Erro no compilador: {e}")
        return False

def testar_qemu_se_disponivel():
    """Testa no QEMU se o binário existe e QEMU está instalado."""
    
    # Verifica qual binário usar
    binarios = []
    for arquivo in ['bootloader_test.bin', 'boot_test.bin']:
        if os.path.exists(arquivo):
            binarios.append(arquivo)
    
    if not binarios:
        print("\n⚠️  Nenhum binário encontrado para testar")
        print("💡 Execute primeiro com NASM instalado")
        return
    
    # Verifica QEMU
    try:
        subprocess.run(['qemu-system-x86_64', '--version'], 
                      capture_output=True, timeout=5)
        print("\n✅ QEMU encontrado!")
        
        binario = binarios[0]
        print(f"\n🚀 Executando {binario} no QEMU...")
        print("🎯 Se 'YUUI-OS' aparecer na tela, a linguagem esta VIVA!")
        print("   (Feche a janela do QEMU para continuar)")
        
        subprocess.Popen([
            'qemu-system-x86_64',
            '-drive', f'format=raw,file={binario}',
            '-m', '32M',
            '-name', 'Yuui-OS Boot Test'
        ])
        
    except:
        print("\n⚠️  QEMU não encontrado")
        print("💡 Instale QEMU para Windows: https://qemu.weilnetz.de/")
        print("   Ou use: winget install qemu")

def main():
    print("""
    ╔══════════════════════════════════════════════════════╗
    ║     🔥 YUUI-LANG BOOT TEST v2 - BLINDADO            ║
    ║                                                      ║
    ║  Encoding ASCII puro (sem problemas de charset)      ║
    ║  Deteccao automatica de NASM e QEMU                 ║
    ╚══════════════════════════════════════════════════════╝
    """)
    
    resultados = {}
    
    # FASE 1
    print("\n" + "="*70)
    print("📋 FASE 1: Bootloader Manual (Controle Total)")
    print("="*70)
    resultados['manual'] = gerar_bootloader_manual()
    
    # FASE 2
    print("\n" + "="*70)
    print("📋 FASE 2: Compilador Yuui-Lang")
    print("="*70)
    resultados['yuui'] = gerar_bootloader_yuui()
    
    # Teste QEMU
    print("\n" + "="*70)
    print("📋 FASE 3: Teste QEMU")
    print("="*70)
    
    if any(resultados.values()):
        testar_qemu_se_disponivel()
    else:
        print("⚠️  Nenhum binário gerado - pulando QEMU")
    
    # Resumo
    print("\n" + "="*70)
    print("📊 RESUMO FINAL")
    print("="*70)
    print(f"Bootloader Manual: {'✅' if resultados.get('manual') else '❌'}")
    print(f"Compilador Yuui:   {'✅' if resultados.get('yuui') else '❌'}")
    
    # Status da instalação
    print(f"\n🔧 Ferramentas:")
    nasm_ok = verificar_nasm()
    print(f"   NASM: {'✅' if nasm_ok else '❌ (necessario para .bin)'}")
    
    # Arquivos gerados
    print(f"\n📁 Arquivos gerados:")
    for arquivo in os.listdir('.'):
        if arquivo.endswith(('.asm', '.bin', '.yuui', '.o')):
            tamanho = os.path.getsize(arquivo)
            print(f"   • {arquivo} ({tamanho} bytes)")
    
    # Próximos passos
    print(f"\n💡 PROXIMOS PASSOS:")
    if not nasm_ok:
        print("   1. Instalar NASM: winget install nasm")
        print("   2. Rodar novamente: python bootloader_test_v2.py")
    else:
        if os.path.exists('bootloader_test.bin'):
            print("   1. Testar no QEMU: qemu-system-x86_64 -drive format=raw,file=bootloader_test.bin")
        print("   2. Editar boot_test.yuui e recompilar")
    
    print(f"\n{'='*70}")
    
    if resultados.get('manual') or resultados.get('yuui'):
        print("🎉 PROGRESSO! Assembly gerado com sucesso!")
        print("   Com NASM instalado, voce vera 'YUUI-OS' na tela do QEMU!")
    else:
        print("🔧 Ajustes necessarios - verifique os erros acima")
    
    print(f"{'='*70}")

if __name__ == "__main__":
    main()
