"""
Backend.py - O Maestro Brutal do Mecha Yuui-Lang
Sistema Nervoso Central que orquestra TODO o pipeline.
Agora com: Tratamento de erros estilo Yuui, Montagem automática, e Boot-Sequence!
"""

import subprocess
import os
import time
from datetime import datetime
from pathlib import Path

class BackendYuui:
    """
    O Maestro. O Regente. O Sistema Nervoso Central.
    Este backend é "brutal" porque:
    1. Não esconde erros - ele os explica com precisão cirúrgica
    2. Gera binários executáveis automaticamente
    3. Prepara o terreno para múltiplas arquiteturas (x86, ARM...)
    """
    
    def __init__(self, nome_projeto="kernel"):
        self.nome_projeto = nome_projeto
        self.codigo_assembly = ""
        self.erros = []
        self.avisos = []
        self.binario_gerado = None
        
        # Metadados do "Mecha"
        self.versao_compilador = "0.2.0-beta"
        self.data_compilacao = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    def compilar(self, arquivo_fonte: str, gerar_binario: bool = True) -> bool:
        """
        O GRANDE MÉTODO. Orquestra tudo do início ao fim.
        
        Fluxo completo:
        1. Lê o arquivo .yuui
        2. Análise Léxica (Lexer.py)
        3. Análise Sintática + Semântica (Parser.py + Tipos.py)
        4. Geração de Assembly (GeradorCodigo.py)
        5. Montagem do binário (NASM)
        6. (Futuro) Boot-Sequence ISO
        """
        
        print(f"\n{'='*70}")
        print(f"🤖 YUUI-LANG MECHA BACKEND v{self.versao_compilador}")
        print(f"{'='*70}")
        print(f"📅 Data: {self.data_compilacao}")
        print(f"📂 Projeto: {self.nome_projeto}")
        print(f"📄 Fonte: {arquivo_fonte}")
        print(f"{'='*70}")
        
        tempo_inicio = time.time()
        
        try:
            # =================================================
            # FASE 1: LEITURA DO ARQUIVO FONTE
            # =================================================
            print(f"\n📖 [FASE 1] Lendo código fonte...")
            with open(arquivo_fonte, 'r', encoding='utf-8') as f:
                codigo_fonte = f.read()
            print(f"   ✅ {len(codigo_fonte)} caracteres lidos")
            
            # =================================================
            # FASE 2: ANÁLISE LÉXICA
            # =================================================
            print(f"\n🔍 [FASE 2] Análise Léxica (Os Olhos do Mecha)...")
            
            from Lexer import Lexer
            lexer = Lexer(codigo_fonte, arquivo_fonte)
            tokens = lexer.tokenizar()
            
            if not tokens:
                self.erros.append("Falha na análise léxica - nenhum token gerado")
                return self._falhar("Análise Léxica")
            
            print(f"   ✅ {len(tokens)} tokens identificados")
            
            # =================================================
            # FASE 3: ANÁLISE SINTÁTICA + SEMÂNTICA
            # =================================================
            print(f"\n🌳 [FASE 3] Análise Sintática + Verificação de Tipos...")
            print(f"         (O Esqueleto e o Juízo do Mecha)")
            
            from Parser_V2 import ParserComTipos
            
            parser = ParserComTipos(tokens, arquivo_fonte)
            ast = parser.parse()
            
            if not ast:
                self.erros.append("Falha na análise sintática - AST não gerada")
                return self._falhar("Parser")
            
            # Verifica erros de tipo capturados pelo Parser
            if parser.erros_tipo:
                print(f"\n   ❌ ERROS DE TIPO ENCONTRADOS:")
                for erro in parser.erros_tipo:
                    print(f"      • {erro}")
                    self.erros.append(str(erro))
                return self._falhar("Verificação de Tipos")
            
            # Exibe avisos se houver
            if parser.avisos_tipo:
                print(f"\n   ⚠️  AVISOS DO JUIZ SEMÂNTICO:")
                for aviso in parser.avisos_tipo:
                    print(f"      • {aviso}")
                    self.avisos.append(str(aviso))
            
            print(f"   ✅ AST construída e validada com sucesso!")
            print(f"   ✅ Tabela de símbolos: {len(parser.tabela_simbolos.escopos[0])} símbolos globais")
            
            # =================================================
            # FASE 4: GERAÇÃO DE CÓDIGO ASSEMBLY
            # =================================================
            print(f"\n⚙️  [FASE 4] Geração de Assembly (Os Músculos do Mecha)...")
            
            from GeradorCodigo import GeradorCodigo
            
            gerador = GeradorCodigo(parser.tabela_simbolos, f"{self.nome_projeto}.asm")
            self.codigo_assembly = gerador.gerar_codigo(ast)
            
            if not self.codigo_assembly:
                self.erros.append("Falha na geração de código Assembly")
                return self._falhar("Gerador de Código")
            
            num_linhas = self.codigo_assembly.count('\n') + 1
            print(f"   ✅ Assembly gerado: {num_linhas} linhas")
            
            # Salva o Assembly em arquivo
            arquivo_asm = f"{self.nome_projeto}.asm"
            with open(arquivo_asm, 'w') as f:
                f.write(self.codigo_assembly)
            print(f"   ✅ Salvo em: {arquivo_asm}")
            
            # =================================================
            # FASE 5: MONTAGEM DO BINÁRIO (OPCIONAL)
            # =================================================
            if gerar_binario:
                print(f"\n🔨 [FASE 5] Montagem do Binário (Forjando o Corpo)...")
                
                sucesso_montagem = self._montar_binario(arquivo_asm)
                
                if sucesso_montagem:
                    print(f"   ✅ Binário pronto: {self.binario_gerado}")
                else:
                    print(f"   ⚠️  Montagem pulada (NASM não encontrado)")
                    print(f"   💡 O Assembly está pronto em: {arquivo_asm}")
            
            # =================================================
            # SUCESSO!
            # =================================================
            tempo_total = time.time() - tempo_inicio
            return self._triunfar(tempo_total)
            
        except FileNotFoundError as e:
            self.erros.append(f"Arquivo não encontrado: {e}")
            return self._falhar("Leitura de Arquivo")
            
        except ImportError as e:
            self.erros.append(f"Módulo não encontrado: {e}")
            print(f"\n   💡 Verifique se todos os arquivos estão na mesma pasta:")
            print(f"      • Lexer.py")
            print(f"      • Parser_V2.py")
            print(f"      • Tipos.py")
            print(f"      • GeradorCodigo.py")
            print(f"      • Backend.py")
            return self._falhar("Importação de Módulos")
            
        except Exception as e:
            self.erros.append(f"Erro inesperado: {e}")
            return self._falhar("Execução")
    
    def _montar_binario(self, arquivo_asm: str) -> bool:
        """
        FASE 5: Chama o NASM para gerar o binário executável.
        
        Futuramente, este método será substituído/expandido para:
        - ARM Assembly (para Raspberry Pi)
        - RISC-V Assembly
        - WebAssembly
        
        Basta trocar este método, não o Mecha inteiro!
        """
        arquivo_bin = f"{self.nome_projeto}.bin"
        
        try:
            # Verifica se NASM está disponível
            resultado_check = subprocess.run(
                ['which', 'nasm'], 
                capture_output=True, 
                text=True
            )
            
            if resultado_check.returncode != 0:
                print(f"   ⚠️  NASM não está instalado no sistema")
                print(f"   💡 Para instalar: sudo apt-get install nasm")
                return False
            
            # Comando de montagem
            comando_nasm = [
                'nasm',
                '-f', 'bin',           # Formato binário puro
                '-o', arquivo_bin,     # Arquivo de saída
                arquivo_asm            # Arquivo Assembly fonte
            ]
            
            print(f"   🔧 Executando: {' '.join(comando_nasm)}")
            
            resultado = subprocess.run(
                comando_nasm,
                capture_output=True,
                text=True
            )
            
            if resultado.returncode != 0:
                print(f"   ❌ Erro do NASM:")
                print(f"   {resultado.stderr}")
                self.erros.append(f"Erro NASM: {resultado.stderr}")
                return False
            
            # Verifica se o binário foi gerado
            if os.path.exists(arquivo_bin):
                tamanho = os.path.getsize(arquivo_bin)
                self.binario_gerado = arquivo_bin
                print(f"   ✅ Binário gerado: {arquivo_bin} ({tamanho} bytes)")
                
                # Verifica se é um binário válido (tem cabeçalho de boot)
                with open(arquivo_bin, 'rb') as f:
                    primeiros_bytes = f.read(4)
                print(f"   🔍 Magic bytes: {primeiros_bytes.hex()}")
                
                return True
            else:
                self.erros.append("Binário não foi gerado pelo NASM")
                return False
                
        except subprocess.TimeoutExpired:
            self.erros.append("Timeout na montagem com NASM")
            return False
        except Exception as e:
            self.erros.append(f"Erro ao executar NASM: {str(e)}")
            return False
    
    def _triunfar(self, tempo_total: float) -> bool:
        """Exibe a mensagem de vitória do Mecha!"""
        print(f"\n{'='*70}")
        print(f"🎉 MECHA YUUI-LANG ATIVADO COM SUCESSO!")
        print(f"{'='*70}")
        print(f"⏱️  Tempo total: {tempo_total:.2f} segundos")
        print(f"📊 Resultados:")
        print(f"   • Assembly: {self.nome_projeto}.asm ✅")
        
        if self.binario_gerado:
            tamanho = os.path.getsize(self.binario_gerado)
            print(f"   • Binário:  {self.binario_gerado} ({tamanho} bytes) ✅")
        
        if self.avisos:
            print(f"   • Avisos: {len(self.avisos)} ⚠️")
        
        print(f"   • Erros: 0 ❌ (Nenhum!)")
        
        print(f"\n💡 PRÓXIMOS COMANDOS:")
        print(f"   Ver Assembly:  cat {self.nome_projeto}.asm")
        
        if self.binario_gerado:
            print(f"   Executar:      qemu-system-x86_64 -drive format=raw,file={self.binario_gerado}")
            print(f"   Hexdump:       hexdump -C {self.binario_gerado} | head -20")
        
        print(f"{'='*70}\n")
        return True
    
    def _falhar(self, fase: str) -> bool:
        """Exibe mensagem de falha com detalhes."""
        print(f"\n{'='*70}")
        print(f"💀 MECHA FALHOU NA FASE: {fase}")
        print(f"{'='*70}")
        
        if self.erros:
            print(f"\n📋 RELATÓRIO DE ERROS:")
            for i, erro in enumerate(self.erros, 1):
                print(f"   {i}. {erro}")
        
        print(f"\n🔧 DIAGNÓSTICO:")
        print(f"   A falha ocorreu durante: {fase}")
        print(f"   Verifique os arquivos gerados até este ponto")
        
        print(f"\n💡 SUGESTÕES:")
        print(f"   1. Revise a sintaxe do arquivo fonte")
        print(f"   2. Verifique se o NASM está instalado (para fases finais)")
        print(f"   3. Consulte a documentação da Yuui-Lang")
        
        print(f"{'='*70}\n")
        return False
    
    def limpar_artefatos(self):
        """Remove arquivos intermediários (mantém apenas o fonte)."""
        artefatos = [
            f"{self.nome_projeto}.asm",
            f"{self.nome_projeto}.bin",
            f"{self.nome_projeto}.o",
            "linker.ld"
        ]
        
        for artefato in artefatos:
            if os.path.exists(artefato):
                os.remove(artefato)
                print(f"   🧹 Removido: {artefato}")


# ============================================
# EXEMPLO DE USO
# ============================================

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════╗
    ║           YUUI-LANG MECHA BACKEND                    ║
    ║     "O Sistema Nervoso Central do Compilador"        ║
    ╚══════════════════════════════════════════════════════╝
    """)
    
    # Verifica se existe um arquivo kernel.yuui
    if os.path.exists("kernel.yuui"):
        print("📂 Arquivo kernel.yuui encontrado!")
        print("🚀 Iniciando compilação...\n")
        
        backend = BackendYuui("kernel")
        sucesso = backend.compilar("kernel.yuui", gerar_binario=True)
        
        if sucesso:
            print("✅ Compilação concluída! Seu Mecha está pronto para dominar o hardware! 🤖")
        else:
            print("❌ Compilação falhou. Verifique os erros acima e ajuste o código.")
    else:
        print("📝 Nenhum arquivo kernel.yuui encontrado.")
        print("💡 Crie um arquivo kernel.yuui com seu código Yuui-Lang!")
        print("\nExemplo mínimo:\n")
        print("""
modo 64bits {
    funcao kernel_principal() {
        memoria video = 0xB8000
        video.limpar()
        video.escrever("Yuui-OS rodando!")
    }
}
        """)