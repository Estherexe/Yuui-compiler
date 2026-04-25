"""
Tipos.py - Sistema de Tipos da Yuui-Lang
Define como a linguagem lida com variáveis, tipos e memória.
Integração com o Lexer e Parser existentes.
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional, Union, List


class CategoriaTipo(Enum):
    """Categorias fundamentais de tipos na Yuui-Lang."""
    PRIMITIVO = auto()      # Tipos básicos: byte, word, inteiro, etc.
    PONTEIRO = auto()       # Ponteiros para endereços de memória
    COMPOSTO = auto()       # Structs/unions
    FUNCAO = auto()         # Tipos de função
    VOID = auto()           # Tipo vazio (sem retorno)


class TamanhoMemoria(Enum):
    """Tamanhos de dados em bits."""
    BIT8 = 8
    BIT16 = 16
    BIT32 = 32
    BIT64 = 64


@dataclass
class TipoBase:
    """Classe base para todos os tipos."""
    categoria: CategoriaTipo
    nome: str
    tamanho: int  # em bits
    
    def __repr__(self):
        return f"{self.nome}"


# ============================================================
# TIPOS PRIMITIVOS
# ============================================================

class TipoPrimitivo(TipoBase):
    """Tipos primitivos da linguagem."""
    def __init__(self, nome: str, tamanho: int, sinalizado: bool = True):
        super().__init__(CategoriaTipo.PRIMITIVO, nome, tamanho)
        self.sinalizado = sinalizado
    
    @property
    def tamanho_bytes(self) -> int:
        return self.tamanho // 8
    
    @property
    def valor_maximo(self) -> int:
        if self.sinalizado:
            return (2 ** (self.tamanho - 1)) - 1
        else:
            return (2 ** self.tamanho) - 1
    
    @property
    def valor_minimo(self) -> int:
        if self.sinalizado:
            return -(2 ** (self.tamanho - 1))
        else:
            return 0


# Definição dos tipos primitivos da Yuui-Lang
BYTE = TipoPrimitivo("byte", 8, sinalizado=False)
WORD = TipoPrimitivo("word", 16, sinalizado=False)
DWORD = TipoPrimitivo("dword", 32, sinalizado=False)
QWORD = TipoPrimitivo("qword", 64, sinalizado=False)
INTEIRO = TipoPrimitivo("inteiro", 32, sinalizado=True)
INTEIRO64 = TipoPrimitivo("inteiro64", 64, sinalizado=True)
BOOLEANO = TipoPrimitivo("booleano", 8, sinalizado=False)
CARACTERE = TipoPrimitivo("caractere", 8, sinalizado=False)


# ============================================================
# TIPO PONTEIRO (essencial para SOs)
# ============================================================

class TipoPonteiro(TipoBase):
    """
    Representa um ponteiro para outro tipo.
    Ex: ponteiro[byte] -> ponteiro para byte
        ponteiro[0xB8000] -> ponteiro absoluto para endereço de memória
    """
    def __init__(self, tipo_apontado: TipoBase, endereco_absoluto: Optional[int] = None):
        nome_base = f"ponteiro[{tipo_apontado.nome}]"
        if endereco_absoluto is not None:
            nome_base += f"@0x{endereco_absoluto:X}"
        
        super().__init__(CategoriaTipo.PONTEIRO, nome_base, 64)  # Ponteiros são 64 bits no modo longo
        self.tipo_apontado = tipo_apontado
        self.endereco_absoluto = endereco_absoluto
    
    @property
    def eh_absoluto(self) -> bool:
        """Retorna True se o ponteiro aponta para um endereço fixo."""
        return self.endereco_absoluto is not None


# ============================================================
# TIPO STRING (tratamento especial para textos)
# ============================================================

class TipoString(TipoBase):
    """
    Tipo para strings (textos).
    Internamente: ponteiro para sequência de bytes terminados em \0
    """
    def __init__(self):
        super().__init__(CategoriaTipo.COMPOSTO, "texto", 64)  # É um ponteiro
    
    @property
    def tipo_interno(self) -> TipoPonteiro:
        """Uma string é internamente um ponteiro para byte[]"""
        return TipoPonteiro(BYTE)


# ============================================================
# TIPO FUNÇÃO
# ============================================================

class TipoFuncao(TipoBase):
    """Tipo para funções."""
    def __init__(self, parametros: List[TipoBase], retorno: TipoBase):
        params_str = ", ".join([p.nome for p in parametros])
        nome = f"funcao({params_str}) -> {retorno.nome}"
        super().__init__(CategoriaTipo.FUNCAO, nome, 0)
        self.parametros = parametros
        self.tipo_retorno = retorno


# ============================================================
# TIPO VOID
# ============================================================

class TipoVoid(TipoBase):
    """Tipo vazio (ausência de valor)."""
    def __init__(self):
        super().__init__(CategoriaTipo.VOID, "void", 0)


VOID = TipoVoid()


# ============================================================
# SÍMBOLO (representa uma variável/função na tabela de símbolos)
# ============================================================

@dataclass
class Simbolo:
    """Representa um símbolo na tabela de símbolos."""
    nome: str
    tipo: TipoBase
    escopo: str  # 'global', 'local', 'parametro'
    endereco_memoria: Optional[int] = None  # Endereço na memória (se alocado)
    valor_inicial: Optional[Union[int, str]] = None
    linha_declaracao: int = 0
    coluna_declaracao: int = 0
    eh_constante: bool = False
    eh_volatil: bool = False  # Para variáveis de hardware
    
    def __repr__(self):
        const = "const " if self.eh_constante else ""
        vol = "volatile " if self.eh_volatil else ""
        return f"{const}{vol}{self.tipo.nome} {self.nome}"


# ============================================================
# TABELA DE SÍMBOLOS
# ============================================================

class TabelaSimbolos:
    """
    Gerencia todos os símbolos do programa.
    Controla escopos, tipos e endereços de memória.
    """
    def __init__(self):
        self.escopos = [{}]  # Pilha de escopos (o primeiro é global)
        self.escopo_atual_nome = "global"
        self.proximo_endereco = 0x1000  # Endereço base para alocação
        self.strings_literais = {}  # Pool de strings para evitar duplicação
    
    def entrar_escopo(self, nome: str):
        """Entra em um novo escopo (ex: dentro de uma função)."""
        self.escopos.append({})
        self.escopo_atual_nome = nome
    
    def sair_escopo(self):
        """Sai do escopo atual."""
        if len(self.escopos) > 1:
            self.escopos.pop()
            self.escopo_atual_nome = "global" if len(self.escopos) == 1 else "local"
    
    def declarar(self, nome: str, tipo: TipoBase, **kwargs) -> Simbolo:
        """
        Declara um novo símbolo no escopo atual.
        
        Args:
            nome: Nome do símbolo
            tipo: Tipo do símbolo
            **kwargs: Atributos adicionais (valor_inicial, eh_constante, etc.)
        
        Returns:
            Simbolo criado
        
        Raises:
            NameError: Se o símbolo já existe no escopo atual
        """
        if nome in self.escopos[-1]:
            existente = self.escopos[-1][nome]
            raise NameError(
                f"Símbolo '{nome}' já declarado neste escopo "
                f"(linha {existente.linha_declaracao})"
            )
        
        # Aloca endereço para variáveis locais/globais
        endereco = kwargs.get('endereco_memoria', None)
        if endereco is None and tipo.categoria != CategoriaTipo.FUNCAO:
            endereco = self.proximo_endereco
            self.proximo_endereco += tipo.tamanho // 8
        
        simbolo = Simbolo(
            nome=nome,
            tipo=tipo,
            escopo=self.escopo_atual_nome,
            endereco_memoria=endereco,
            linha_declaracao=kwargs.get('linha', 0),
            coluna_declaracao=kwargs.get('coluna', 0),
            valor_inicial=kwargs.get('valor_inicial', None),
            eh_constante=kwargs.get('eh_constante', False),
            eh_volatil=kwargs.get('eh_volatil', False)
        )
        
        self.escopos[-1][nome] = simbolo
        return simbolo
    
    def obter(self, nome: str) -> Optional[Simbolo]:
        """
        Busca um símbolo em todos os escopos (do mais interno ao global).
        
        Returns:
            Simbolo se encontrado, None caso contrário
        """
        for escopo in reversed(self.escopos):
            if nome in escopo:
                return escopo[nome]
        return None
    
    def obter_local(self, nome: str) -> Optional[Simbolo]:
        """Busca símbolo apenas no escopo atual."""
        return self.escopos[-1].get(nome, None)
    
    def declarar_string_literal(self, valor: str) -> int:
        """
        Registra uma string literal e retorna seu endereço.
        Evita duplicação de strings idênticas.
        """
        if valor not in self.strings_literais:
            endereco = self.proximo_endereco
            self.strings_literais[valor] = endereco
            self.proximo_endereco += len(valor) + 1  # +1 para o \0
        return self.strings_literais[valor]
    
    def imprimir_tabela(self):
        """Imprime a tabela de símbolos completa."""
        print("\n" + "="*70)
        print("TABELA DE SÍMBOLOS")
        print("="*70)
        
        for nivel, escopo in enumerate(self.escopos):
            nome_escopo = "global" if nivel == 0 else f"local_{nivel}"
            print(f"\n[Escopo: {nome_escopo}]")
            print(f"{'Nome':<20} {'Tipo':<25} {'Endereço':<12} {'Info'}")
            print("-"*70)
            
            for nome, simbolo in escopo.items():
                endereco = f"0x{simbolo.endereco_memoria:X}" if simbolo.endereco_memoria else "---"
                info = []
                if simbolo.eh_constante:
                    info.append("const")
                if simbolo.eh_volatil:
                    info.append("volatile")
                if simbolo.valor_inicial is not None:
                    info.append(f"= {simbolo.valor_inicial}")
                
                print(f"{nome:<20} {simbolo.tipo.nome:<25} {endereco:<12} {' '.join(info)}")


# ============================================================
# ANALISADOR SEMÂNTICO
# ============================================================

class AnalisadorSemantico:
    """
    Realiza a análise semântica na AST.
    Verifica tipos, declarações, e compatibilidade.
    """
    def __init__(self):
        self.tabela = TabelaSimbolos()
        self.erros = []
        self.avisos = []
    
    def analisar(self, ast) -> bool:
        """
        Analisa semanticamente a AST completa.
        Retorna True se não houver erros.
        """
        print("\n[Analisador Semântico] Iniciando verificação de tipos...")
        
        # Visita cada declaração do programa
        for declaracao in ast.declaracoes:
            self._visitar_no(declaracao)
        
        if self.erros:
            print(f"\n[Analisador Semântico] {len(self.erros)} erro(s) encontrado(s):")
            for erro in self.erros:
                print(f"  ❌ {erro}")
            return False
        
        if self.avisos:
            print(f"\n[Analisador Semântico] {len(self.avisos)} aviso(s):")
            for aviso in self.avisos:
                print(f"  ⚠️ {aviso}")
        
        print("[Analisador Semântico] Verificação concluída com sucesso!")
        return True
    
    def _visitar_no(self, no):
        """Visita um nó da AST recursivamente."""
        if no is None:
            return None
        
        tipo_no = no.tipo
        
        # Mapeamento de visitantes
        visitantes = {
            TipoNo.DECLARACAO_FUNCAO: self._visitar_declaracao_funcao,
            TipoNo.DECLARACAO_INTERRUPCAO: self._visitar_declaracao_interrupcao,
            TipoNo.DECLARACAO_MODO: self._visitar_declaracao_modo,
            TipoNo.ATRIBUICAO_MEMORIA: self._visitar_atribuicao_memoria,
            TipoNo.ATRIBUICAO: self._visitar_atribuicao,
            TipoNo.CHAMADA_METODO: self._visitar_chamada_metodo,
            TipoNo.CHAMADA_FUNCAO: self._visitar_chamada_funcao,
            TipoNo.LITERAL_STRING: self._visitar_literal_string,
            TipoNo.LITERAL_NUMERO: self._visitar_literal_numero,
            TipoNo.LITERAL_HEX: self._visitar_literal_hex,
            TipoNo.BLOCO: self._visitar_bloco,
        }
        
        visitante = visitantes.get(tipo_no)
        if visitante:
            return visitante(no)
        
        # Para nós com filhos, visitar recursivamente
        if hasattr(no, 'filhos'):
            for filho in no.filhos:
                self._visitar_no(filho)
        
        return None
    
    def _visitar_declaracao_funcao(self, no):
        """Visita uma declaração de função."""
        nome = no.nome
        
        # Verifica se já existe
        if self.tabela.obter_local(nome):
            self.erros.append(f"Função '{nome}' já declarada (linha {no.linha})")
            return
        
        # Declara a função na tabela
        tipo_retorno = VOID  # Por enquanto, funções não têm tipo de retorno explícito
        tipo_funcao = TipoFuncao(no.parametros, tipo_retorno)
        
        self.tabela.declarar(nome, tipo_funcao, linha=no.linha)
        
        # Entra no escopo da função
        self.tabela.entrar_escopo(nome)
        
        # Declara parâmetros
        for tipo_param, nome_param in no.parametros:
            tipo = self._resolver_tipo(tipo_param)
            self.tabela.declarar(nome_param, tipo, linha=no.linha)
        
        # Visita o corpo
        if no.corpo:
            self._visitar_no(no.corpo)
        
        # Sai do escopo
        self.tabela.sair_escopo()
    
    def _visitar_declaracao_interrupcao(self, no):
        """Visita uma declaração de interrupção."""
        nome = no.nome
        
        # Interrupções são similares a funções sem parâmetros
        tipo_funcao = TipoFuncao([], VOID)
        self.tabela.declarar(nome, tipo_funcao, linha=no.linha)
        
        # Entra no escopo
        self.tabela.entrar_escopo(nome)
        
        if no.corpo:
            self._visitar_no(no.corpo)
        
        self.tabela.sair_escopo()
    
    def _visitar_declaracao_modo(self, no):
        """Visita uma declaração de modo de CPU."""
        print(f"[Semântico] Entrando em modo {no.modo} bits")
        if no.bloco:
            self._visitar_no(no.bloco)
    
    def _visitar_atribuicao_memoria(self, no):
        """
        Visita uma atribuição de memória.
        Ex: memoria video = 0xB8000
        """
        nome = no.nome
        
        # O tipo é um ponteiro para o endereço especificado
        endereco = int(no.endereco.valor, 16) if 'x' in no.endereco.valor else int(no.endereco.valor)
        
        # Cria tipo ponteiro absoluto
        tipo = TipoPonteiro(BYTE, endereco_absoluto=endereco)
        
        try:
            self.tabela.declarar(
                nome, tipo,
                endereco_memoria=endereco,
                eh_volatil=True,  # Memória mapeada é volátil
                linha=no.linha
            )
            print(f"[Semântico] Memória '{nome}' mapeada em 0x{endereco:X} (tipo: {tipo.nome})")
        except NameError as e:
            self.erros.append(str(e))
    
    def _visitar_atribuicao(self, no):
        """Visita uma atribuição de variável."""
        nome = no.nome
        simbolo = self.tabela.obter(nome)
        
        if not simbolo:
            self.erros.append(f"Variável '{nome}' não declarada (linha {no.linha})")
            return
        
        if simbolo.eh_constante:
            self.erros.append(f"Não é possível atribuir a '{nome}' - é constante (linha {no.linha})")
        
        # Verifica compatibilidade de tipos
        if no.valor_expressao:
            tipo_valor = self._visitar_no(no.valor_expressao)
            if tipo_valor:
                self._verificar_compatibilidade(simbolo.tipo, tipo_valor, no.linha, nome)
    
    def _visitar_chamada_metodo(self, no):
        """Visita uma chamada de método."""
        objeto = no.objeto
        simbolo = self.tabela.obter(objeto)
        
        if not simbolo:
            self.erros.append(f"Objeto '{objeto}' não declarado (linha {no.linha})")
            return None
        
        # Verifica se o método existe para o tipo
        metodo = no.metodo
        metodos_validos = self._obter_metodos_tipo(simbolo.tipo)
        
        if metodo not in metodos_validos:
            self.avisos.append(
                f"Método '{metodo}' pode não existir para o tipo {simbolo.tipo.nome} "
                f"(linha {no.linha})"
            )
        
        return VOID  # Métodos retornam void por padrão
    
    def _visitar_chamada_funcao(self, no):
        """Visita uma chamada de função."""
        nome = no.nome
        simbolo = self.tabela.obter(nome)
        
        if not simbolo:
            self.erros.append(f"Função '{nome}' não declarada (linha {no.linha})")
            return None
        
        if simbolo.tipo.categoria != CategoriaTipo.FUNCAO:
            self.erros.append(f"'{nome}' não é uma função (linha {no.linha})")
            return None
        
        # Verifica número de argumentos
        num_params = len(simbolo.tipo.parametros)
        num_args = len(no.argumentos)
        
        if num_params != num_args:
            self.erros.append(
                f"Função '{nome}' espera {num_params} argumentos, "
                f"mas recebeu {num_args} (linha {no.linha})"
            )
        
        return simbolo.tipo.tipo_retorno
    
    def _visitar_literal_string(self, no):
        """Visita uma literal string."""
        # Registra a string na tabela e retorna seu tipo
        self.tabela.declarar_string_literal(no.valor)
        return TipoString()
    
    def _visitar_literal_numero(self, no):
        """Visita uma literal numérica."""
        return INTEIRO  # Números decimais são inteiros por padrão
    
    def _visitar_literal_hex(self, no):
        """Visita uma literal hexadecimal."""
        valor = int(no.valor, 16)
        if valor <= 0xFF:
            return BYTE
        elif valor <= 0xFFFF:
            return WORD
        elif valor <= 0xFFFFFFFF:
            return DWORD
        else:
            return QWORD
    
    def _visitar_bloco(self, no):
        """Visita um bloco de código."""
        for comando in no.comandos:
            self._visitar_no(comando)
        return VOID
    
    def _resolver_tipo(self, nome_tipo: str) -> TipoBase:
        """Converte nome de tipo em objeto TipoBase."""
        tipos = {
            'byte': BYTE,
            'word': WORD,
            'dword': DWORD,
            'qword': QWORD,
            'inteiro': INTEIRO,
            'booleano': BOOLEANO,
            'caractere': CARACTERE,
        }
        return tipos.get(nome_tipo, INTEIRO)  # Default: inteiro
    
    def _obter_metodos_tipo(self, tipo: TipoBase) -> set:
        """Retorna os métodos disponíveis para um tipo."""
        metodos_comuns = {'escrever', 'limpar', 'ler'}
        
        if isinstance(tipo, TipoPonteiro):
            return metodos_comuns.union({'posicionar', 'copiar', 'preencher'})
        elif isinstance(tipo, TipoString):
            return metodos_comuns.union({'tamanho', 'concatenar', 'comparar'})
        elif tipo.categoria == CategoriaTipo.PRIMITIVO:
            return {'para_texto', 'para_hex'}
        
        return metodos_comuns
    
    def _verificar_compatibilidade(self, tipo_esperado: TipoBase, tipo_recebido: TipoBase, linha: int, nome: str):
        """Verifica se dois tipos são compatíveis."""
        if tipo_esperado.nome != tipo_recebido.nome:
            self.avisos.append(
                f"Possível incompatibilidade de tipos em '{nome}': "
                f"esperado {tipo_esperado.nome}, recebido {tipo_recebido.nome} "
                f"(linha {linha})"
            )


# ============================================================
# EXEMPLO DE USO
# ============================================================

def demonstrar_sistema_tipos():
    """Demonstra o sistema de tipos completo."""
    
    print("="*70)
    print("SISTEMA DE TIPOS DA YUUI-LANG")
    print("="*70)
    
    # 1. Tipos primitivos
    print("\n[1] TIPOS PRIMITIVOS")
    print("-"*40)
    tipos_primitivos = [BYTE, WORD, DWORD, QWORD, INTEIRO, INTEIRO64, BOOLEANO]
    
    for tipo in tipos_primitivos:
        print(f"  {tipo.nome:<15} {tipo.tamanho:>3} bits | "
              f"range: [{tipo.valor_minimo}, {tipo.valor_maximo}] | "
              f"sinalizado: {tipo.sinalizado}")
    
    # 2. Ponteiros
    print("\n[2] TIPOS PONTEIROS")
    print("-"*40)
    
    p_byte = TipoPonteiro(BYTE)
    p_absoluto = TipoPonteiro(WORD, endereco_absoluto=0xB8000)
    
    print(f"  Ponteiro dinâmico: {p_byte.nome}")
    print(f"  Ponteiro absoluto: {p_absoluto.nome}")
    print(f"  É absoluto? {p_absoluto.eh_absoluto}")
    
    # 3. Tabela de símbolos
    print("\n[3] TABELA DE SÍMBOLOS (SIMULAÇÃO)")
    print("-"*40)
    
    tabela = TabelaSimbolos()
    
    # Declarações típicas de um kernel
    tabela.declarar("video_mem", TipoPonteiro(BYTE, 0xB8000), 
                   eh_volatil=True, linha=5)
    tabela.declarar("contador", INTEIRO, 
                   valor_inicial=0, linha=10)
    tabela.declarar("MAX_BUFFER", QWORD, 
                   valor_inicial=4096, eh_constante=True, linha=15)
    tabela.declarar("mensagem", TipoString(), 
                   valor_inicial="Boot OK", linha=20)
    
    tabela.imprimir_tabela()
    
    # 4. Demonstração de inferência de tipo
    print("\n[4] INFERÊNCIA DE TIPOS PARA LITERAIS")
    print("-"*40)
    
    literais = [
        ("42", "decimal"),
        ("0xB8000", "hexadecimal"),
        ('"Hello World"', "string"),
        ("0xFF", "hexadecimal pequeno"),
        ("0xFFFFFFFF", "hexadecimal grande"),
    ]
    
    for valor, descricao in literais:
        if valor.startswith('"'):
            print(f"  '{valor}' ({descricao}) -> TipoString (texto)")
        elif valor.startswith('0x') or valor.startswith('0X'):
            val = int(valor, 16)
            if val <= 0xFF:
                tipo = "BYTE"
            elif val <= 0xFFFF:
                tipo = "WORD"
            elif val <= 0xFFFFFFFF:
                tipo = "DWORD"
            else:
                tipo = "QWORD"
            print(f"  {valor} ({descricao}) -> {tipo} (0x{val:X})")
        else:
            print(f"  {valor} ({descricao}) -> INTEIRO")
    
    return tabela


if __name__ == "__main__":
    demonstrar_sistema_tipos()
