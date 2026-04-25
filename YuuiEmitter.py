"""
GeradorCodigo.py - Gerador de Código Assembly NASM da Yuui-Lang
Transforma a AST validada em código Assembly x86_64 executável.
Suporta múltiplos modos de CPU (16/32/64 bits).
"""

from enum import Enum, auto
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
import os

# Importa do nosso sistema
from Parser_V2 import (
    TipoNo, NoAST, NoPrograma, NoBloco,
    NoDeclaracaoFuncao, NoDeclaracaoInterrupcao, NoDeclaracaoModo,
    NoDeclaracaoVariavel, NoAtribuicaoMemoria, NoAtribuicao,
    NoChamadaMetodo, NoChamadaFuncao, NoRetorno,
    NoSe, NoEnquanto, NoPara,
    NoExpressaoBinaria, NoExpressaoUnaria, NoAcessoPorta, NoLiteral
)
from Tipos import (
    BYTE, WORD, DWORD, QWORD, INTEIRO, INTEIRO64,
    TipoPrimitivo, TipoPonteiro, TipoString, TipoFuncao, VOID,
    TabelaSimbolos, Simbolo
)


class ModoCPU(Enum):
    """Modos de operação da CPU."""
    REAL_MODE = 16      # Modo real 16 bits
    PROTECTED_MODE = 32 # Modo protegido 32 bits
    LONG_MODE = 64      # Modo longo 64 bits


class SecaoAssembly(Enum):
    """Seções do código Assembly."""
    BSS = auto()    # Variáveis não inicializadas
    DATA = auto()   # Dados inicializados (strings, constantes)
    TEXT = auto()   # Código executável
    BOOT = auto()   # Setor de boot (modo real)


@dataclass
class InstrucaoAssembly:
    """Representa uma instrução Assembly."""
    rotulo: Optional[str] = None
    mnemonico: str = ""
    operandos: List[str] = field(default_factory=list)
    comentario: str = ""
    eh_diretiva: bool = False
    
    def gerar_linha(self) -> str:
        """Gera a linha Assembly formatada."""
        partes = []
        
        # Rótulo (label)
        if self.rotulo:
            partes.append(f"{self.rotulo}:")
        
        # Mnemônico ou diretiva
        if self.eh_diretiva:
            partes.append(f"{self.mnemonico}")
        else:
            partes.append(f"    {self.mnemonico}")
        
        # Operandos
        if self.operandos:
            partes.append(" " + ", ".join(self.operandos))
        
        # Comentário
        if self.comentario:
            partes.append(f"  ; {self.comentario}")
        
        return "".join(partes)


class GeradorCodigo:
    """
    Gerador de código Assembly NASM.
    Transforma a AST em Assembly executável.
    """
    
    def __init__(self, tabela_simbolos: TabelaSimbolos, nome_arquivo: str = "output.asm"):
        self.tabela = tabela_simbolos
        self.nome_arquivo = nome_arquivo
        self.modo_atual = ModoCPU.LONG_MODE  # Default: 64 bits
        self.secao_atual = SecaoAssembly.TEXT
        
        # Buffers para cada seção
        self.secao_bss: List[InstrucaoAssembly] = []
        self.secao_data: List[InstrucaoAssembly] = []
        self.secao_text: List[InstrucaoAssembly] = []
        self.secao_boot: List[InstrucaoAssembly] = []
        
        # Controle de labels únicos
        self.contador_labels = 0
        self.labels = set()
        
        # Memória de strings
        self.strings_geradas = set()
    
    def gerar_codigo(self, ast: NoPrograma) -> str:
        """
        Gera o código Assembly completo a partir da AST.
        
        Returns:
            str: Código Assembly NASM completo
        """
        print("\n" + "="*70)
        print("🔧 GERADOR DE CÓDIGO ASSEMBLY (NASM)")
        print("="*70)
        
        # Cabeçalho NASM
        self._gerar_cabecalho()
        
        # Processa cada declaração
        for declaracao in ast.declaracoes:
            print(f"[Gerador] Processando: {declaracao.tipo.name}")
            self._gerar_declaracao(declaracao)
        
        # Finaliza o código
        self._gerar_footer()
        
        # Monta o código completo
        codigo_completo = self._montar_codigo()
        
        # Salva em arquivo
        self._salvar_arquivo(codigo_completo)
        
        return codigo_completo
    
    def _gerar_cabecalho(self):
        """Gera o cabeçalho do arquivo Assembly."""
        cabecalho = [
            "; ============================================================",
            "; Yuui-OS Kernel - Gerado pelo Compilador Yuui-Lang",
            "; Arquivo Assembly NASM (x86_64)",
            "; ============================================================",
            "",
            "BITS 64",
            "ORG 0x100000  ; Endereço de carga do kernel (1MB)",
            "",
        ]
        
        for linha in cabecalho:
            self.secao_text.append(InstrucaoAssembly(
                mnemonico=linha if linha.startswith(";") else "",
                comentario=linha if linha.startswith(";") else "",
                eh_diretiva=not linha.startswith(";") and not linha.startswith(" ")
            ))
    
    def _gerar_footer(self):
        """Gera o rodapé do arquivo Assembly."""
        footer = [
            "",
            "; ============================================================",
            "; Fim do Kernel Yuui-OS",
            "; ============================================================",
            "",
            "times 512 - ($ - $$) db 0  ; Padding (se necessário)",
        ]
        
        for linha in footer:
            if linha.startswith(";"):
                continue  # Comentários já estão implícitos
    
    def _gerar_declaracao(self, no: NoAST):
        """Roteia a geração de código baseado no tipo do nó."""
        if isinstance(no, NoDeclaracaoModo):
            self._gerar_modo(no)
        elif isinstance(no, NoDeclaracaoFuncao):
            self._gerar_funcao(no)
        elif isinstance(no, NoDeclaracaoInterrupcao):
            self._gerar_interrupcao(no)
        elif isinstance(no, NoAtribuicaoMemoria):
            self._gerar_atribuicao_memoria(no)
        elif isinstance(no, NoBloco):
            self._gerar_bloco(no)
        elif isinstance(no, NoChamadaMetodo):
            self._gerar_chamada_metodo(no)
        elif isinstance(no, NoChamadaFuncao):
            self._gerar_chamada_funcao(no)
        elif isinstance(no, NoAtribuicao):
            self._gerar_atribuicao(no)
        elif isinstance(no, NoSe):
            self._gerar_condicional(no)
        elif isinstance(no, NoEnquanto):
            self._gerar_loop_enquanto(no)
        elif isinstance(no, NoRetorno):
            self._gerar_retorno(no)
        elif isinstance(no, NoAcessoPorta):
            self._gerar_acesso_porta(no)
        elif isinstance(no, NoExpressaoBinaria):
            self._gerar_expressao_binaria(no)
    
    def _gerar_modo(self, no: NoDeclaracaoModo):
        """Gera código para mudança de modo de CPU."""
        print(f"  [Modo] Configurando CPU para {no.modo} bits")
        
        if no.modo == 16:
            self.modo_atual = ModoCPU.REAL_MODE
            self._adicionar_instrucao("BITS 16", [], "Modo Real 16 bits", SecaoAssembly.BOOT)
        elif no.modo == 32:
            self.modo_atual = ModoCPU.PROTECTED_MODE
            self._adicionar_instrucao("BITS 32", [], "Modo Protegido 32 bits")
        elif no.modo == 64:
            self.modo_atual = ModoCPU.LONG_MODE
            self._adicionar_instrucao("BITS 64", [], "Modo Longo 64 bits")
        
        # Processa o bloco do modo
        if no.bloco:
            self._gerar_bloco(no.bloco)
    
    def _gerar_funcao(self, no: NoDeclaracaoFuncao):
        """Gera código para declaração de função."""
        print(f"  [Função] {no.nome}")
        
        # Label da função
        self._adicionar_instrucao("", [], "", rotulo=no.nome)
        
        # Prólogo da função (stack frame)
        self._adicionar_instrucao("push", ["rbp"], "Salva base pointer")
        self._adicionar_instrucao("mov", ["rbp", "rsp"], "Novo stack frame")
        
        # Aloca espaço para variáveis locais
        simbolo = self.tabela.obter(no.nome)
        if simbolo and hasattr(simbolo, 'tamanho_frame'):
            self._adicionar_instrucao("sub", ["rsp", str(simbolo.tamanho_frame)], 
                                     "Espaço para variáveis locais")
        
        # Corpo da função
        if no.corpo:
            self._gerar_bloco(no.corpo)
        
        # Epílogo da função
        self._adicionar_instrucao("mov", ["rsp", "rbp"], "Restaura stack pointer")
        self._adicionar_instrucao("pop", ["rbp"], "Restaura base pointer")
        self._adicionar_instrucao("ret", [], "Retorna da função")
    
    def _gerar_interrupcao(self, no: NoDeclaracaoInterrupcao):
        """Gera código para rotina de interrupção (ISR)."""
        print(f"  [ISR] {no.nome}")
        
        # Label da ISR
        self._adicionar_instrucao("", [], "", rotulo=no.nome)
        
        # Salva registradores (pushad no modo 32 bits, manual no 64)
        self._adicionar_instrucao("push", ["rax"], "Salva registradores")
        self._adicionar_instrucao("push", ["rbx"])
        self._adicionar_instrucao("push", ["rcx"])
        self._adicionar_instrucao("push", ["rdx"])
        
        # Corpo da ISR
        if no.corpo:
            self._gerar_bloco(no.corpo)
        
        # Restaura registradores
        self._adicionar_instrucao("pop", ["rdx"], "Restaura registradores")
        self._adicionar_instrucao("pop", ["rcx"])
        self._adicionar_instrucao("pop", ["rbx"])
        self._adicionar_instrucao("pop", ["rax"])
        
        # Retorno de interrupção
        self._adicionar_instrucao("iretq", [], "Retorna da interrupção (64 bits)")
    
    def _gerar_atribuicao_memoria(self, no: NoAtribuicaoMemoria):
        """
        Gera código para mapeamento de memória absoluta.
        Ex: memoria video = 0xB8000
        """
        simbolo = self.tabela.obter(no.nome)
        if not simbolo:
            return
        
        endereco = simbolo.endereco_memoria
        print(f"  [Memória Absoluta] {no.nome} @ 0x{endereco:X}")
        
        # Declara o símbolo como externo ou constante
        self.secao_data.append(InstrucaoAssembly(
            mnemonico="",
            operandos=[],
            comentario=f"Mapeamento de memória: {no.nome} = 0x{endereco:X}"
        ))
        
        self.secao_data.append(InstrucaoAssembly(
            mnemonico=f"{no.nome}_addr",
            operandos=["equ", f"0x{endereco:X}"],
            comentario=f"Endereço absoluto de {no.nome}",
            eh_diretiva=True
        ))
    
    def _gerar_bloco(self, no: NoBloco):
        """Gera código para um bloco de comandos."""
        for comando in no.comandos:
            self._gerar_declaracao(comando)  # Recursivo para cada comando
    
    def _gerar_chamada_metodo(self, no: NoChamadaMetodo):
        """
        Gera código para chamada de método.
        Ex: video.escrever("texto")
        """
        print(f"  [Chamada Método] {no.objeto}.{no.metodo}()")
        
        # Mapeamento de métodos built-in para rotinas Assembly
        metodos_builtin = {
            'escrever': self._gerar_metodo_escrever,
            'limpar': self._gerar_metodo_limpar,
            'ler': self._gerar_metodo_ler,
        }
        
        if no.metodo in metodos_builtin:
            metodos_builtin[no.metodo](no)
        else:
            # Método não built-in - tentar chamada indireta
            self._adicionar_instrucao(";", [f"Chamada de método: {no.objeto}.{no.metodo}"])
    
    def _gerar_metodo_escrever(self, no: NoChamadaMetodo):
        """Gera código para escrever na tela (modo texto VGA)."""
        simbolo = self.tabela.obter(no.objeto)
        
        if simbolo and isinstance(simbolo.tipo, TipoPonteiro) and simbolo.tipo.eh_absoluto:
            endereco = simbolo.endereco_memoria
            
            # Se for memória de vídeo VGA (0xB8000)
            if endereco == 0xB8000:
                self._gerar_escrita_vga(no, endereco)
            else:
                self._gerar_escrita_generica(no, endereco)
    
    def _gerar_escrita_vga(self, no: NoChamadaMetodo, endereco_video: int):
        """Gera código para escrever no buffer de vídeo VGA (modo texto)."""
        for arg in no.argumentos:
            if isinstance(arg, NoLiteral) and arg.tipo == TipoNo.LITERAL_STRING:
                # String literal - vamos escrever caractere por caractere
                texto = arg.valor
                self._adicionar_instrucao(";", [f"Escrevendo string no VGA: '{texto}'"])
                
                # Carrega endereço da string
                label_string = self._adicionar_string_data(texto)
                self._adicionar_instrucao("mov", ["rsi", label_string], "Fonte: string")
                self._adicionar_instrucao("mov", ["rdi", f"0x{endereco_video:X}"], 
                                         "Destino: buffer VGA")
                
                # Chama rotina de escrita
                self._adicionar_instrucao("call", ["escrever_string_vga"], 
                                         "Escreve string no VGA")
    
    def _gerar_metodo_limpar(self, no: NoChamadaMetodo):
        """Gera código para limpar a tela VGA."""
        simbolo = self.tabela.obter(no.objeto)
        
        if simbolo and simbolo.endereco_memoria == 0xB8000:
            self._adicionar_instrucao(";", ["Limpando tela VGA (80x25)"])
            self._adicionar_instrucao("mov", ["rdi", "0xB8000"], "Buffer VGA")
            self._adicionar_instrucao("mov", ["rcx", "80*25"], "Total de caracteres")
            self._adicionar_instrucao("mov", ["ax", "0x0720"], "Espaço + atributo cinza")
            self._adicionar_instrucao("rep", ["stosw"], "Preenche tela")
    
    def _gerar_metodo_ler(self, no: NoChamadaMetodo):
        """Gera código para ler entrada (teclado, porta serial, etc.)."""
        self._adicionar_instrucao(";", ["Leitura de dispositivo"])
        # Implementação específica dependeria do dispositivo
    
    def _gerar_chamada_funcao(self, no: NoChamadaFuncao):
        """Gera código para chamada de função."""
        print(f"  [Chamada Função] {no.nome}()")
        
        # Prepara argumentos (convenção System V AMD64)
        registradores_arg = ["rdi", "rsi", "rdx", "rcx", "r8", "r9"]
        
        for i, arg in enumerate(no.argumentos):
            if i < len(registradores_arg):
                reg = registradores_arg[i]
                if isinstance(arg, NoLiteral):
                    self._adicionar_instrucao("mov", [reg, str(arg.valor)], 
                                             f"Argumento {i+1}")
        
        # Chama a função
        self._adicionar_instrucao("call", [no.nome], f"Chama {no.nome}")
    
    def _gerar_atribuicao(self, no: NoAtribuicao):
        """Gera código para atribuição de variável."""
        simbolo = self.tabela.obter(no.nome)
        if not simbolo:
            return
        
        print(f"  [Atribuição] {no.nome} = {no.valor_expressao.valor if no.valor_expressao else '?'}")
        
        if no.valor_expressao and isinstance(no.valor_expressao, NoLiteral):
            valor = no.valor_expressao.valor
            
            # Escolhe o registrador baseado no tipo
            reg = self._registrador_para_tipo(simbolo.tipo)
            
            # Carrega o valor
            if isinstance(valor, str) and not valor.startswith('0x'):
                # String - carrega endereço
                label = self._adicionar_string_data(valor)
                self._adicionar_instrucao("lea", [reg, f"[{label}]"], 
                                         f"{no.nome} = &'{valor}'")
            else:
                # Número
                self._adicionar_instrucao("mov", [reg, str(valor)], 
                                         f"{no.nome} = {valor}")
            
            # Salva na memória
            self._adicionar_instrucao("mov", [f"[{no.nome}]", reg], 
                                     f"Salva em {no.nome}")
    
    def _gerar_condicional(self, no: NoSe):
        """Gera código para estrutura condicional se/senao."""
        label_else = self._novo_label("else")
        label_fim = self._novo_label("fim_se")
        
        print(f"  [Condicional] se (condição)")
        
        # Avalia condição
        if no.condicao:
            self._gerar_expressao_binaria(no.condicao)
        
        # Pula para else se falso
        self._adicionar_instrucao("cmp", ["rax", "0"])
        self._adicionar_instrucao("je", [label_else], "Pula se falso")
        
        # Bloco verdadeiro
        if no.bloco_verdadeiro:
            self._gerar_bloco(no.bloco_verdadeiro)
        
        self._adicionar_instrucao("jmp", [label_fim], "Pula fim")
        
        # Bloco falso (se existir)
        self._adicionar_instrucao("", [], "", rotulo=label_else)
        if no.bloco_falso:
            self._gerar_bloco(no.bloco_falso)
        
        # Fim
        self._adicionar_instrucao("", [], "", rotulo=label_fim)
    
    def _gerar_loop_enquanto(self, no: NoEnquanto):
        """Gera código para loop enquanto."""
        label_inicio = self._novo_label("loop")
        label_fim = self._novo_label("fim_loop")
        
        print(f"  [Loop] enquanto (condição)")
        
        # Início do loop
        self._adicionar_instrucao("", [], "", rotulo=label_inicio)
        
        # Avalia condição
        if no.condicao:
            self._gerar_expressao_binaria(no.condicao)
        
        # Sai se falso
        self._adicionar_instrucao("cmp", ["rax", "0"])
        self._adicionar_instrucao("je", [label_fim], "Sai do loop")
        
        # Corpo do loop
        if no.corpo:
            self._gerar_bloco(no.corpo)
        
        # Volta ao início
        self._adicionar_instrucao("jmp", [label_inicio], "Próxima iteração")
        
        # Fim
        self._adicionar_instrucao("", [], "", rotulo=label_fim)
    
    def _gerar_retorno(self, no: NoRetorno):
        """Gera código para retorno de função."""
        if no.expressao:
            self._gerar_declaracao(no.expressao)
        self._adicionar_instrucao("ret", [], "Retorno")
    
    def _gerar_acesso_porta(self, no: NoAcessoPorta):
        """Gera código para acesso a portas I/O."""
        print(f"  [Port I/O] {no.tipo_operacao}")
        
        if no.tipo_operacao.startswith('in'):
            # Leitura de porta
            tamanho = no.tipo_operacao[-1]  # 'b', 'w', 'd'
            self._adicionar_instrucao("mov", ["dx", str(no.porta.valor)], 
                                     f"Porta {no.porta.valor}")
            self._adicionar_instrucao(f"in al, dx" if tamanho == 'b' else 
                                     f"in ax, dx" if tamanho == 'w' else
                                     f"in eax, dx", [], 
                                     f"Lê {tamanho} bits da porta")
        
        elif no.tipo_operacao.startswith('out'):
            # Escrita em porta
            tamanho = no.tipo_operacao[-1]
            self._adicionar_instrucao("mov", ["dx", str(no.porta.valor)],
                                     f"Porta {no.porta.valor}")
            if no.valor_enviar:
                self._adicionar_instrucao("mov", ["al", str(no.valor_enviar.valor)],
                                         f"Valor {no.valor_enviar.valor}")
            self._adicionar_instrucao(f"out dx, al" if tamanho == 'b' else
                                     f"out dx, ax" if tamanho == 'w' else
                                     f"out dx, eax", [],
                                     f"Escreve {tamanho} bits na porta")
    
    def _gerar_expressao_binaria(self, no: NoExpressaoBinaria):
        """Gera código para expressões binárias."""
        # Mapeamento de operadores para instruções Assembly
        mapa_operadores = {
            '+': 'add',
            '-': 'sub',
            '*': 'imul',
            '/': 'idiv',
            '&': 'and',
            '|': 'or',
            '^': 'xor',
            '<<': 'shl',
            '>>': 'shr',
            '==': 'sete',
            '!=': 'setne',
            '<': 'setl',
            '>': 'setg',
        }
        
        if no.operador in mapa_operadores:
            instrucao = mapa_operadores[no.operador]
            
            # Carrega operandos
            if no.esquerda:
                self._carregar_operando("rax", no.esquerda)
            if no.direita:
                self._carregar_operando("rbx", no.direita)
            
            # Executa operação
            self._adicionar_instrucao(instrucao, ["rax", "rbx"], 
                                     f"{no.esquerda.valor} {no.operador} {no.direita.valor}")
    
    def _carregar_operando(self, registrador: str, no: NoAST):
        """Carrega um operando em um registrador."""
        if isinstance(no, NoLiteral):
            self._adicionar_instrucao("mov", [registrador, str(no.valor)],
                                     f"Carrega {no.valor}")
        elif isinstance(no, NoExpressaoBinaria):
            self._gerar_expressao_binaria(no)
    
    def _novo_label(self, prefixo: str) -> str:
        """Gera um label único."""
        self.contador_labels += 1
        label = f".{prefixo}_{self.contador_labels}"
        self.labels.add(label)
        return label
    
    def _adicionar_string_data(self, texto: str) -> str:
        """Adiciona uma string à seção .data e retorna seu label."""
        if texto in self.strings_geradas:
            # Reutiliza string já existente
            for label in self.labels:
                if label.startswith(".str_") and label in self.strings_geradas:
                    return label
        
        label = self._novo_label("str")
        self.strings_geradas.add(label)
        
        # Adiciona à seção .data
        self.secao_data.append(InstrucaoAssembly(
            mnemonico="",
            operandos=[],
            comentario=""
        ))
        self.secao_data.append(InstrucaoAssembly(
            rotulo=label,
            mnemonico="db",
            operandos=[f"'{texto}'", "0"],
            comentario=f"String: {texto}"
        ))
        
        return label
    
    def _registrador_para_tipo(self, tipo) -> str:
        """Retorna o registrador apropriado para um tipo."""
        if isinstance(tipo, TipoPrimitivo):
            if tipo.tamanho <= 8:
                return "al"
            elif tipo.tamanho <= 16:
                return "ax"
            elif tipo.tamanho <= 32:
                return "eax"
            else:
                return "rax"
        return "rax"  # Default: registrador de 64 bits
    
    def _adicionar_instrucao(self, mnemonico: str, operandos: List[str], 
                            comentario: str = "", rotulo: str = None,
                            secao: SecaoAssembly = None):
        """Adiciona uma instrução à seção apropriada."""
        instrucao = InstrucaoAssembly(
            rotulo=rotulo,
            mnemonico=mnemonico,
            operandos=operandos,
            comentario=comentario
        )
        
        if secao == SecaoAssembly.BOOT:
            self.secao_boot.append(instrucao)
        elif secao == SecaoAssembly.DATA:
            self.secao_data.append(instrucao)
        elif secao == SecaoAssembly.BSS:
            self.secao_bss.append(instrucao)
        else:
            self.secao_text.append(instrucao)
    
    def _montar_codigo(self) -> str:
        """Monta o código Assembly completo."""
        linhas = []
        
        # Seção de boot (modo real)
        if self.secao_boot:
            linhas.append("section .boot progbits alloc exec write align=512")
            linhas.append("")
            for inst in self.secao_boot:
                linhas.append(inst.gerar_linha())
            linhas.append("")
        
        # Seção BSS (variáveis não inicializadas)
        if self.secao_bss:
            linhas.append("section .bss nobits alloc noexec write align=16")
            linhas.append("")
            for inst in self.secao_bss:
                linhas.append(inst.gerar_linha())
            linhas.append("")
        
        # Seção DATA (dados inicializados)
        if self.secao_data:
            linhas.append("section .data progbits alloc noexec write align=16")
            linhas.append("")
            for inst in self.secao_data:
                linhas.append(inst.gerar_linha())
            linhas.append("")
        
        # Seção TEXT (código executável)
        if self.secao_text:
            linhas.append("section .text progbits alloc exec nowrite align=16")
            linhas.append("")
            for inst in self.secao_text:
                linhas.append(inst.gerar_linha())
        
        return "\n".join(linhas)
    
    def _salvar_arquivo(self, codigo: str):
        """Salva o código Assembly em um arquivo."""
        with open(self.nome_arquivo, 'w') as f:
            f.write(codigo)
        
        print(f"\n💾 Código Assembly salvo em: {self.nome_arquivo}")
        print(f"   Tamanho: {len(codigo)} caracteres")
        print(f"   Linhas: {codigo.count(chr(10)) + 1}")
    
    def _gerar_escrita_generica(self, no: NoChamadaMetodo, endereco: int):
        """Gera código para escrita genérica em memória."""
        self._adicionar_instrucao(";", [f"Escrita genérica em 0x{endereco:X}"])
    
    def _gerar_escrita_vga_completa(self):
        """Gera a rotina completa de escrita VGA."""
        # Esta seria uma rotina auxiliar no Assembly
        rotina_vga = [
            "escrever_string_vga:",
            "    ; Entrada: RSI = string, RDI = buffer VGA",
            "    push rax",
            "    push rcx",
            "    mov ah, 0x07  ; Atributo: cinza claro",
            ".loop_vga:",
            "    lodsb          ; Carrega próximo caractere",
            "    test al, al    ; Verifica se é null (fim da string)",
            "    jz .fim_vga",
            "    stosw          ; Escreve caractere + atributo",
            "    jmp .loop_vga",
            ".fim_vga:",
            "    pop rcx",
            "    pop rax",
            "    ret",
        ]
        
        for linha in rotina_vga:
            self.secao_text.append(InstrucaoAssembly(mnemonico=linha))


def testar_gerador_codigo():
    """Testa o gerador de código com um exemplo completo."""
    
    from Lexer import Lexer
    from Parser_V2 import ParserComTipos
    
    codigo_fonte = """
    modo 64bits {
        funcao kernel_principal() {
            memoria video = 0xB8000
            video.limpar()
            video.escrever("Yuui-OS Kernel v0.1")
            
            byte contador = 0
            
            enquanto (contador < 10) {
                contador = contador + 1
            }
        }
    }
    """
    
    print("="*70)
    print("YUUI-LANG: TESTE DO GERADOR DE CÓDIGO ASSEMBLY")
    print("="*70)
    
    # Lexer
    print("\n[1] Análise Léxica...")
    lexer = Lexer(codigo_fonte, "teste_asm.yuui")
    tokens = lexer.tokenizar()
    
    if not tokens:
        print("❌ Falha no Lexer!")
        return
    
    # Parser
    print("\n[2] Análise Sintática + Tipos...")
    parser = ParserComTipos(tokens, "teste_asm.yuui")
    ast = parser.parse()
    
    if not ast:
        print("❌ Falha no Parser!")
        return
    
    # Gerador de Código
    print("\n[3] Geração de Código Assembly...")
    gerador = GeradorCodigo(parser.tabela_simbolos, "kernel_output.asm")
    codigo_asm = gerador.gerar_codigo(ast)
    
    # Exibe o código gerado
    print("\n" + "="*70)
    print("📋 CÓDIGO ASSEMBLY GERADO (NASM)")
    print("="*70)
    print(codigo_asm)
    print("="*70)
    
    # Instruções para compilar
    print("\n🔨 Para compilar e testar:")
    print("   nasm -f bin kernel_output.asm -o kernel.bin")
    print("   qemu-system-x86_64 -kernel kernel.bin")


if __name__ == "__main__":
    testar_gerador_codigo()