"""
Lexer.py - Analisador Léxico da Yuui-Lang
Transforma código fonte em uma sequência de tokens para o compilador.
"""

import re
from enum import Enum, auto

class TipoToken(Enum):
    """Enumeração de todos os tipos de tokens da linguagem."""
    # Palavras-chave de estrutura
    FUNCAO = auto()
    SE = auto()
    SENAO = auto()
    ENQUANTO = auto()
    PARA = auto()
    RETORNO = auto()
    
    # Palavras-chave de sistema (essenciais para SO)
    MEMORIA = auto()
    INTERRUPCAO = auto()
    MODO = auto()
    PORT = auto()
    DISCO = auto()
    SISTEMA = auto()
    CPU = auto()
    
    # Modos de operação da CPU
    MODO_16BITS = auto()
    MODO_32BITS = auto()
    MODO_64BITS = auto()
    
    # Tipos de dados primitivos
    BYTE = auto()
    WORD = auto()
    DWORD = auto()
    QWORD = auto()
    INTEIRO = auto()
    
    # Literais
    IDENTIFICADOR = auto()
    NUMERO = auto()
    NUMERO_HEX = auto()
    STRING = auto()
    CARACTERE = auto()
    
    # Operadores
    ATRIBUICAO = auto()      # =
    SOMA = auto()            # +
    SUBTRACAO = auto()       # -
    MULTIPLICACAO = auto()   # *
    DIVISAO = auto()         # /
    MODULO = auto()          # %
    
    # Operadores de comparação
    IGUAL = auto()           # ==
    DIFERENTE = auto()       # !=
    MENOR = auto()           # <
    MAIOR = auto()           # >
    MENOR_IGUAL = auto()     # <=
    MAIOR_IGUAL = auto()     # >=
    
    # Operadores lógicos
    E_LOGICO = auto()        # &&
    OU_LOGICO = auto()       # ||
    NAO_LOGICO = auto()      # !
    
    # Operadores bit a bit (cruciais para programação de SO)
    E_BIT = auto()           # &
    OU_BIT = auto()          # |
    XOR_BIT = auto()         # ^
    NAO_BIT = auto()         # ~
    SHIFT_ESQUERDA = auto()  # <<
    SHIFT_DIREITA = auto()   # >>
    
    # Delimitadores
    PARENTESE_ABRE = auto()  # (
    PARENTESE_FECHA = auto() # )
    CHAVE_ABRE = auto()      # {
    CHAVE_FECHA = auto()     # }
    COLCHETE_ABRE = auto()   # [
    COLCHETE_FECHA = auto()  # ]
    
    # Pontuação
    PONTO = auto()           # .
    VIRGULA = auto()         # ,
    PONTO_VIRGULA = auto()   # ;
    DOIS_PONTOS = auto()     # :
    
    # Acesso a portas (essencial para SO)
    PORT_IN = auto()         # inb, inw, ind
    PORT_OUT = auto()        # outb, outw, outd
    
    # Controle de compilação
    DIRETIVA = auto()        # #include, #define, etc.
    COMENTARIO = auto()      # // ou /* */
    
    # Especiais
    FIM_ARQUIVO = auto()
    DESCONHECIDO = auto()


class Token:
    """Representa um token com tipo, valor, linha e coluna."""
    def __init__(self, tipo, valor, linha, coluna):
        self.tipo = tipo
        self.valor = valor
        self.linha = linha
        self.coluna = coluna
    
    def __repr__(self):
        return f"Token({self.tipo.name}, '{self.valor}', L{self.linha}:C{self.coluna})"
    
    def __str__(self):
        return f"[{self.tipo.name}] {self.valor}"


class LexerError(Exception):
    """Exceção personalizada para erros léxicos."""
    def __init__(self, mensagem, linha, coluna, caractere):
        self.linha = linha
        self.coluna = coluna
        self.caractere = caractere
        super().__init__(f"Erro léxico na linha {linha}, coluna {coluna}: {mensagem} (caractere: '{caractere}')")


class Lexer:
    """
    Analisador léxico da Yuui-Lang.
    
    Características especiais para programação de sistemas:
    - Suporte a números hexadecimais (0xB8000)
    - Suporte a operadores bit a bit
    - Palavras-chave para acesso a portas I/O
    - Modos de CPU (16/32/64 bits)
    """
    
    def __init__(self, codigo_fonte, nome_arquivo="<desconhecido>"):
        self.codigo = codigo_fonte
        self.nome_arquivo = nome_arquivo
        self.posicao = 0
        self.linha = 1
        self.coluna = 1
        self.tokens = []
        
        # Palavras reservadas da linguagem
        self.palavras_reservadas = {
            # Estruturas de controle
            'funcao': TipoToken.FUNCAO,
            'se': TipoToken.SE,
            'senao': TipoToken.SENAO,
            'enquanto': TipoToken.ENQUANTO,
            'para': TipoToken.PARA,
            'retorno': TipoToken.RETORNO,
            
            # Palavras-chave do sistema
            'memoria': TipoToken.MEMORIA,
            'interrupcao': TipoToken.INTERRUPCAO,
            'modo': TipoToken.MODO,
            'port': TipoToken.PORT,
            'disco': TipoToken.DISCO,
            'sistema': TipoToken.SISTEMA,
            'cpu': TipoToken.CPU,
            
            # Modos de operação
            'bits16': TipoToken.MODO_16BITS,
            'bits32': TipoToken.MODO_32BITS,
            'bits64': TipoToken.MODO_64BITS,
            
            # Tipos de dados
            'byte': TipoToken.BYTE,
            'word': TipoToken.WORD,
            'dword': TipoToken.DWORD,
            'qword': TipoToken.QWORD,
            'inteiro': TipoToken.INTEIRO,
            
            # Port I/O
            'inb': TipoToken.PORT_IN,
            'inw': TipoToken.PORT_IN,
            'ind': TipoToken.PORT_IN,
            'outb': TipoToken.PORT_OUT,
            'outw': TipoToken.PORT_OUT,
            'outd': TipoToken.PORT_OUT,
        }
    
    def _caractere_atual(self):
        """Retorna o caractere atual ou None se fim do arquivo."""
        if self.posicao < len(self.codigo):
            return self.codigo[self.posicao]
        return None
    
    def _avancar(self):
        """Avança para o próximo caractere e atualiza linha/coluna."""
        if self.posicao < len(self.codigo):
            if self.codigo[self.posicao] == '\n':
                self.linha += 1
                self.coluna = 1
            else:
                self.coluna += 1
            self.posicao += 1
    
    def _pular_espacos_branco(self):
        """Pula espaços em branco e comentários."""
        while self.posicao < len(self.codigo):
            char = self.caractere_atual()
            
            # Espaços em branco
            if char in ' \t\r':
                self._avancar()
            
            # Quebra de linha
            elif char == '\n':
                self._avancar()
            
            # Comentários de linha única //
            elif char == '/' and self.posicao + 1 < len(self.codigo) and self.codigo[self.posicao + 1] == '/':
                self._pular_comentario_linha()
            
            # Comentários de múltiplas linhas /* */
            elif char == '/' and self.posicao + 1 < len(self.codigo) and self.codigo[self.posicao + 1] == '*':
                self._pular_comentario_bloco()
            
            else:
                break
    
    def _pular_comentario_linha(self):
        """Pula um comentário de linha única (//)."""
        while self.posicao < len(self.codigo) and self.codigo[self.posicao] != '\n':
            self._avancar()
        # Não avança a nova linha aqui, será tratada no próximo _pular_espacos_branco
    
    def _pular_comentario_bloco(self):
        """Pula um comentário de bloco (/* */)."""
        self._avancar()  # Pula /
        self._avancar()  # Pula *
        
        while self.posicao < len(self.codigo):
            if self.codigo[self.posicao] == '*' and self.posicao + 1 < len(self.codigo) and self.codigo[self.posicao + 1] == '/':
                self._avancar()  # Pula *
                self._avancar()  # Pula /
                return
            self._avancar()
        
        raise LexerError("Comentário de bloco não fechado", self.linha, self.coluna, 'EOF')
    
    def _ler_numero(self, primeiro_char):
        """Lê um número (decimal ou hexadecimal)."""
        inicio_coluna = self.coluna
        inicio_linha = self.linha
        valor = primeiro_char
        
        # Verifica se é hexadecimal (0x ou 0X)
        if primeiro_char == '0' and self.posicao + 1 < len(self.codigo) and self.codigo[self.posicao + 1] in 'xX':
            self._avancar()  # Pula 0
            self._avancar()  # Pula x
            valor = '0x'
            
            # Lê os dígitos hexadecimais
            while self.posicao < len(self.codigo) and self.caractere_atual() in '0123456789ABCDEFabcdef':
                valor += self.caractere_atual()
                self._avancar()
            
            if len(valor) == 2:  # Apenas '0x'
                raise LexerError("Número hexadecimal incompleto", inicio_linha, inicio_coluna, valor)
            
            return Token(TipoToken.NUMERO_HEX, valor, inicio_linha, inicio_coluna)
        
        # Número decimal
        self._avancar()  # Pula o primeiro dígito
        
        while self.posicao < len(self.codigo) and self.caractere_atual() in '0123456789':
            valor += self.caractere_atual()
            self._avancar()
        
        # Verifica se não tem identificador colado no número (ex: 123abc)
        if self.posicao < len(self.codigo) and self.caractere_atual().isalpha():
            raise LexerError("Identificador inválido começando com número", inicio_linha, inicio_coluna, valor)
        
        return Token(TipoToken.NUMERO, valor, inicio_linha, inicio_coluna)
    
    def _ler_string(self):
        """Lê uma string literal entre aspas duplas."""
        inicio_coluna = self.coluna
        inicio_linha = self.linha
        self._avancar()  # Pula aspas de abertura
        valor = ''
        
        while self.posicao < len(self.codigo):
            char = self.caractere_atual()
            
            # Encontrou aspas de fechamento
            if char == '"':
                self._avancar()
                return Token(TipoToken.STRING, valor, inicio_linha, inicio_coluna)
            
            # Sequências de escape
            if char == '\\':
                self._avancar()
                escape_char = self.caractere_atual()
                if escape_char == 'n':
                    valor += '\n'
                elif escape_char == 't':
                    valor += '\t'
                elif escape_char == 'r':
                    valor += '\r'
                elif escape_char == '\\':
                    valor += '\\'
                elif escape_char == '"':
                    valor += '"'
                elif escape_char == '0':
                    valor += '\0'  # Null terminator, comum em SO
                elif escape_char == 'x':
                    # Escape hexadecimal (\xHH)
                    hex_valor = ''
                    self._avancar()
                    for _ in range(2):
                        if self.posicao < len(self.codigo) and self.caractere_atual() in '0123456789ABCDEFabcdef':
                            hex_valor += self.caractere_atual()
                            self._avancar()
                        else:
                            raise LexerError("Escape hexadecimal incompleto", self.linha, self.coluna, '\\x' + hex_valor)
                    try:
                        valor += chr(int(hex_valor, 16))
                    except ValueError:
                        raise LexerError("Escape hexadecimal inválido", inicio_linha, inicio_coluna, '\\x' + hex_valor)
                    continue
                else:
                    raise LexerError(f"Sequência de escape desconhecida: \\{escape_char}", self.linha, self.coluna, escape_char)
            
            # Quebra de linha dentro de string (não permitido)
            elif char == '\n':
                raise LexerError("String não fechada - quebra de linha encontrada", inicio_linha, inicio_coluna, '\\n')
            
            else:
                valor += char
            
            self._avancar()
        
        raise LexerError("String não fechada", inicio_linha, inicio_coluna, 'EOF')
    
    def _ler_identificador(self, primeiro_char):
        """Lê um identificador ou palavra reservada."""
        inicio_coluna = self.coluna
        inicio_linha = self.linha
        valor = primeiro_char
        
        while self.posicao < len(self.codigo) and (self.caractere_atual().isalnum() or self.caractere_atual() == '_'):
            valor += self.caractere_atual()
            self._avancar()
        
        # Verifica se é uma palavra reservada
        tipo = self.palavras_reservadas.get(valor, TipoToken.IDENTIFICADOR)
        
        return Token(tipo, valor, inicio_linha, inicio_coluna)
    
    def _tratar_operador(self, primeiro_char):
        """Trata operadores simples e compostos."""
        inicio_coluna = self.coluna
        inicio_linha = self.linha
        
        # Mapeamento de operadores compostos (dois caracteres)
        operadores_compostos = {
            '==': TipoToken.IGUAL,
            '!=': TipoToken.DIFERENTE,
            '<=': TipoToken.MENOR_IGUAL,
            '>=': TipoToken.MAIOR_IGUAL,
            '&&': TipoToken.E_LOGICO,
            '||': TipoToken.OU_LOGICO,
            '<<': TipoToken.SHIFT_ESQUERDA,
            '>>': TipoToken.SHIFT_DIREITA,
        }
        
        # Verifica se é um operador composto
        if self.posicao + 1 < len(self.codigo):
            dois_chars = primeiro_char + self.codigo[self.posicao + 1]
            if dois_chars in operadores_compostos:
                self._avancar()  # Pula primeiro char
                self._avancar()  # Pula segundo char
                return Token(operadores_compostos[dois_chars], dois_chars, inicio_linha, inicio_coluna)
        
        # Operadores simples
        operadores_simples = {
            '=': TipoToken.ATRIBUICAO,
            '+': TipoToken.SOMA,
            '-': TipoToken.SUBTRACAO,
            '*': TipoToken.MULTIPLICACAO,
            '/': TipoToken.DIVISAO,
            '%': TipoToken.MODULO,
            '!': TipoToken.NAO_LOGICO,
            '<': TipoToken.MENOR,
            '>': TipoToken.MAIOR,
            '&': TipoToken.E_BIT,
            '|': TipoToken.OU_BIT,
            '^': TipoToken.XOR_BIT,
            '~': TipoToken.NAO_BIT,
        }
        
        if primeiro_char in operadores_simples:
            self._avancar()
            return Token(operadores_simples[primeiro_char], primeiro_char, inicio_linha, inicio_coluna)
        
        return None
    
    def _proximo_token(self):
        """Extrai o próximo token do código fonte."""
        self._pular_espacos_branco()
        
        # Verifica fim do arquivo
        if self.posicao >= len(self.codigo):
            return Token(TipoToken.FIM_ARQUIVO, 'EOF', self.linha, self.coluna)
        
        char = self.caractere_atual()
        
        # Strings
        if char == '"':
            return self._ler_string()
        
        # Números
        if char.isdigit():
            return self._ler_numero(char)
        
        # Identificadores e palavras reservadas
        if char.isalpha() or char == '_':
            return self._ler_identificador(char)
        
        # Operadores e delimitadores
        operador = self._tratar_operador(char)
        if operador:
            return operador
        
        # Delimitadores e pontuação
        delimitadores = {
            '(': TipoToken.PARENTESE_ABRE,
            ')': TipoToken.PARENTESE_FECHA,
            '{': TipoToken.CHAVE_ABRE,
            '}': TipoToken.CHAVE_FECHA,
            '[': TipoToken.COLCHETE_ABRE,
            ']': TipoToken.COLCHETE_FECHA,
            '.': TipoToken.PONTO,
            ',': TipoToken.VIRGULA,
            ';': TipoToken.PONTO_VIRGULA,
            ':': TipoToken.DOIS_PONTOS,
        }
        
        if char in delimitadores:
            token = Token(delimitadores[char], char, self.linha, self.coluna)
            self._avancar()
            return token
        
        # Caractere desconhecido
        raise LexerError("Caractere inválido encontrado", self.linha, self.coluna, char)
    
    def tokenizar(self):
        """
        Analisa todo o código fonte e retorna a lista de tokens.
        
        Returns:
            list: Lista de objetos Token
        """
        self.tokens = []
        
        try:
            while True:
                token = self._proximo_token()
                self.tokens.append(token)
                if token.tipo == TipoToken.FIM_ARQUIVO:
                    break
        except LexerError as e:
            print(f"Erro de compilação: {e}")
            return None
        
        return self.tokens
    
    def imprimir_tokens(self):
        """Imprime a lista de tokens de forma formatada."""
        if not self.tokens:
            print("Nenhum token gerado.")
            return
        
        print(f"\n{'='*80}")
        print(f"Tokens gerados para: {self.nome_arquivo}")
        print(f"{'='*80}")
        print(f"{'Tipo':<20} {'Valor':<20} {'Posição':<15}")
        print(f"{'-'*55}")
        
        for token in self.tokens:
            posicao = f"L{token.linha}:C{token.coluna}"
            print(f"{token.tipo.name:<20} {token.valor:<20} {posicao:<15}")
        
        print(f"{'='*80}")
        print(f"Total de tokens: {len(self.tokens)}")
        print(f"{'='*80}\n")


# Função auxiliar para testar o Lexer
def testar_lexer():
    """Testa o Lexer com um código exemplo da Yuui-Lang."""
    
    codigo_exemplo = """
    // Kernel básico da Yuui-OS
    funcao entrada_boot() {
        memoria video = 0xB8000
        video.limpar()
        video.escrever("Yuui-OS Kernel v0.1")
        
        // Habilita A20 e prepara modo 64 bits
        sistema.a20_habilitar()
        port.outb(0x64, 0xFE)  // Reset CPU
    }
    """
    
    print(f"\n{'='*80}")
    print("LEXER DA YUUI-LANG - TESTE")
    print(f"{'='*80}")
    print("Código fonte:")
    print(f"{'='*80}")
    print(codigo_exemplo)
    
    lexer = Lexer(codigo_exemplo, "teste.kernel")
    tokens = lexer.tokenizar()
    
    if tokens:
        lexer.imprimir_tokens()
        
        # Demonstração de acesso a tokens específicos
        print("Demonstração de análise:")
        for token in tokens[:10]:  # Primeiros 10 tokens
            if token.tipo == TipoToken.IDENTIFICADOR:
                print(f"  Identificador encontrado: {token.valor} na linha {token.linha}")
            elif token.tipo == TipoToken.NUMERO_HEX:
                print(f"  Número hexadecimal: {token.valor} = {int(token.valor, 16)}")


if __name__ == "__main__":
    testar_lexer()