"""
Parser.py - Analisador Sintático da Yuui-Lang
Transforma a sequência de tokens em uma Árvore de Sintaxe Abstrata (AST).
Totalmente compatível com o Lexer existente.
"""

from Lexer import TipoToken, Token, Lexer
from enum import Enum, auto

class TipoNo(Enum):
    """Tipos de nós da AST."""
    # Estruturas de programa
    PROGRAMA = auto()
    BLOCO = auto()
    
    # Declarações
    DECLARACAO_FUNCAO = auto()
    DECLARACAO_VARIAVEL = auto()
    DECLARACAO_INTERRUPCAO = auto()
    DECLARACAO_MODO = auto()
    
    # Comandos
    ATRIBUICAO = auto()
    ATRIBUICAO_MEMORIA = auto()
    CHAMADA_FUNCAO = auto()
    CHAMADA_METODO = auto()
    RETORNO = auto()
    
    # Estruturas de controle
    SE = auto()
    ENQUANTO = auto()
    PARA = auto()
    
    # Expressões
    EXPRESSAO_BINARIA = auto()
    EXPRESSAO_UNARIA = auto()
    ACESSO_PORTA = auto()
    
    # Literais
    LITERAL_NUMERO = auto()
    LITERAL_HEX = auto()
    LITERAL_STRING = auto()
    LITERAL_IDENTIFICADOR = auto()
    
    # Operadores
    OPERADOR = auto()


class NoAST:
    """Classe base para todos os nós da AST."""
    def __init__(self, tipo, linha=0, coluna=0):
        self.tipo = tipo
        self.linha = linha
        self.coluna = coluna
        self.filhos = []
    
    def adicionar_filho(self, no):
        """Adiciona um nó filho."""
        self.filhos.append(no)
        return self
    
    def __repr__(self):
        return f"NoAST({self.tipo.name}, linha={self.linha}, filhos={len(self.filhos)})"
    
    def imprimir_arvore(self, nivel=0):
        """Imprime a AST de forma hierárquica."""
        indentacao = "  " * nivel
        resultado = f"{indentacao}├─ {self.tipo.name}"
        if hasattr(self, 'valor') and self.valor is not None:
            resultado += f" [{self.valor}]"
        resultado += f" (L{self.linha})"
        print(resultado)
        
        for i, filho in enumerate(self.filhos):
            if i == len(self.filhos) - 1:
                print(f"{indentacao}   └─", end="")
            filho.imprimir_arvore(nivel + 1)


class NoPrograma(NoAST):
    """Nó raiz do programa."""
    def __init__(self):
        super().__init__(TipoNo.PROGRAMA)
        self.declaracoes = []
    
    def adicionar_declaracao(self, declaracao):
        self.declaracoes.append(declaracao)
        self.adicionar_filho(declaracao)


class NoBloco(NoAST):
    """Bloco de código { ... }."""
    def __init__(self, linha=0):
        super().__init__(TipoNo.BLOCO, linha)
        self.comandos = []
    
    def adicionar_comando(self, comando):
        self.comandos.append(comando)
        self.adicionar_filho(comando)


class NoDeclaracaoFuncao(NoAST):
    """Declaração de função."""
    def __init__(self, nome, parametros, corpo, linha=0):
        super().__init__(TipoNo.DECLARACAO_FUNCAO, linha)
        self.nome = nome
        self.parametros = parametros
        self.corpo = corpo
        self.valor = nome
        if corpo:
            self.adicionar_filho(corpo)


class NoDeclaracaoInterrupcao(NoAST):
    """Declaração de rotina de interrupção."""
    def __init__(self, nome, corpo, linha=0):
        super().__init__(TipoNo.DECLARACAO_INTERRUPCAO, linha)
        self.nome = nome
        self.corpo = corpo
        self.valor = nome
        if corpo:
            self.adicionar_filho(corpo)


class NoDeclaracaoModo(NoAST):
    """Declaração de modo de CPU (16/32/64 bits)."""
    def __init__(self, modo, bloco, linha=0):
        super().__init__(TipoNo.DECLARACAO_MODO, linha)
        self.modo = modo
        self.bloco = bloco
        self.valor = f"modo_{modo}bits"
        if bloco:
            self.adicionar_filho(bloco)


class NoDeclaracaoVariavel(NoAST):
    """Declaração de variável com tipo."""
    def __init__(self, tipo, nome, valor_inicial=None, linha=0):
        super().__init__(TipoNo.DECLARACAO_VARIAVEL, linha)
        self.tipo_variavel = tipo
        self.nome = nome
        self.valor_inicial = valor_inicial
        self.valor = f"{tipo} {nome}"


class NoAtribuicaoMemoria(NoAST):
    """Atribuição especial para memória mapeada (ex: memoria video = 0xB8000)."""
    def __init__(self, nome_variavel, endereco, linha=0):
        super().__init__(TipoNo.ATRIBUICAO_MEMORIA, linha)
        self.nome = nome_variavel
        self.endereco = endereco
        self.valor = f"{nome_variavel} = {endereco.valor}"


class NoAtribuicao(NoAST):
    """Atribuição de variável."""
    def __init__(self, nome, valor, linha=0):
        super().__init__(TipoNo.ATRIBUICAO, linha)
        self.nome = nome
        self.valor_expressao = valor
        self.valor = nome
        if valor:
            self.adicionar_filho(valor)


class NoChamadaMetodo(NoAST):
    """Chamada de método em objeto (ex: video.escrever("texto"))."""
    def __init__(self, objeto, metodo, argumentos, linha=0):
        super().__init__(TipoNo.CHAMADA_METODO, linha)
        self.objeto = objeto
        self.metodo = metodo
        self.argumentos = argumentos or []
        self.valor = f"{objeto}.{metodo}()"


class NoChamadaFuncao(NoAST):
    """Chamada de função."""
    def __init__(self, nome, argumentos, linha=0):
        super().__init__(TipoNo.CHAMADA_FUNCAO, linha)
        self.nome = nome
        self.argumentos = argumentos or []
        self.valor = nome


class NoRetorno(NoAST):
    """Comando de retorno."""
    def __init__(self, expressao=None, linha=0):
        super().__init__(TipoNo.RETORNO, linha)
        self.expressao = expressao
        if expressao:
            self.adicionar_filho(expressao)


class NoSe(NoAST):
    """Estrutura condicional se/senao."""
    def __init__(self, condicao, bloco_verdadeiro, bloco_falso=None, linha=0):
        super().__init__(TipoNo.SE, linha)
        self.condicao = condicao
        self.bloco_verdadeiro = bloco_verdadeiro
        self.bloco_falso = bloco_falso
        if condicao:
            self.adicionar_filho(condicao)
        if bloco_verdadeiro:
            self.adicionar_filho(bloco_verdadeiro)
        if bloco_falso:
            self.adicionar_filho(bloco_falso)


class NoEnquanto(NoAST):
    """Estrutura de loop enquanto."""
    def __init__(self, condicao, corpo, linha=0):
        super().__init__(TipoNo.ENQUANTO, linha)
        self.condicao = condicao
        self.corpo = corpo
        if condicao:
            self.adicionar_filho(condicao)
        if corpo:
            self.adicionar_filho(corpo)


class NoPara(NoAST):
    """Estrutura de loop para."""
    def __init__(self, inicializacao, condicao, incremento, corpo, linha=0):
        super().__init__(TipoNo.PARA, linha)
        self.inicializacao = inicializacao
        self.condicao = condicao
        self.incremento = incremento
        self.corpo = corpo


class NoExpressaoBinaria(NoAST):
    """Expressão com operador binário."""
    def __init__(self, esquerda, operador, direita, linha=0):
        super().__init__(TipoNo.EXPRESSAO_BINARIA, linha)
        self.esquerda = esquerda
        self.operador = operador
        self.direita = direita
        self.valor = operador


class NoExpressaoUnaria(NoAST):
    """Expressão com operador unário."""
    def __init__(self, operador, expressao, linha=0):
        super().__init__(TipoNo.EXPRESSAO_UNARIA, linha)
        self.operador = operador
        self.expressao = expressao
        self.valor = operador


class NoAcessoPorta(NoAST):
    """Acesso a portas I/O (inb, outb, etc.)."""
    def __init__(self, tipo_operacao, porta, valor=None, linha=0):
        super().__init__(TipoNo.ACESSO_PORTA, linha)
        self.tipo_operacao = tipo_operacao  # 'in' ou 'out'
        self.tamanho = None  # 'b', 'w', 'd'
        self.porta = porta
        self.valor_enviar = valor
        self.valor = f"{tipo_operacao}"


class NoLiteral(NoAST):
    """Nó para valores literais."""
    def __init__(self, tipo, valor, linha=0):
        super().__init__(tipo, linha)
        self.valor = valor


class ParserError(Exception):
    """Exceção personalizada para erros sintáticos."""
    def __init__(self, mensagem, token=None):
        self.token = token
        if token:
            local = f"linha {token.linha}, coluna {token.coluna}"
            mensagem_completa = f"Erro sintático em {local}: {mensagem}\n  Token: {token}"
        else:
            mensagem_completa = f"Erro sintático: {mensagem}"
        super().__init__(mensagem_completa)


class Parser:
    """
    Analisador sintático da Yuui-Lang.
    Implementa um parser de descida recursiva (Recursive Descent Parser).
    """
    
    def __init__(self, tokens):
        """
        Inicializa o parser com uma lista de tokens.
        
        Args:
            tokens: Lista de objetos Token do Lexer
        """
        self.tokens = tokens
        self.posicao = 0
        self.token_atual = tokens[0] if tokens else None
        self.funcoes_declaradas = set()  # Para verificar duplicatas
        self.modo_atual = None  # Controla o modo de CPU atual
    
    def _avancar(self):
        """Avança para o próximo token."""
        self.posicao += 1
        if self.posicao < len(self.tokens):
            self.token_atual = self.tokens[self.posicao]
        else:
            self.token_atual = None
    
    def _verificar(self, tipo_esperado):
        """Verifica se o token atual é do tipo esperado e avança."""
        if self.token_atual and self.token_atual.tipo == tipo_esperado:
            token = self.token_atual
            self._avancar()
            return token
        raise ParserError(f"Esperado {tipo_esperado.name}, encontrado {self.token_atual.tipo.name if self.token_atual else 'EOF'}", self.token_atual)
    
    def _verificar_opcional(self, tipo_esperado):
        """Verifica se o token atual é do tipo esperado e avança se for."""
        if self.token_atual and self.token_atual.tipo == tipo_esperado:
            token = self.token_atual
            self._avancar()
            return token
        return None
    
    def parse(self):
        """
        Inicia a análise sintática e retorna a AST completa.
        
        Returns:
            NoPrograma: Nó raiz do programa
        """
        programa = NoPrograma()
        
        print("\n[Parser] Iniciando análise sintática...")
        
        try:
            # Continua parseando declarações até o fim do arquivo
            while self.token_atual and self.token_atual.tipo != TipoToken.FIM_ARQUIVO:
                declaracao = self._parse_declaracao()
                if declaracao:
                    programa.adicionar_declaracao(declaracao)
            
            print(f"[Parser] Análise concluída com sucesso!")
            print(f"[Parser] {len(programa.declaracoes)} declarações encontradas.")
            
        except ParserError as e:
            print(f"\n{'='*60}")
            print(f"ERRO DE COMPILAÇÃO")
            print(f"{'='*60}")
            print(e)
            return None
        
        return programa
    
    def _parse_declaracao(self):
        """Analisa uma declaração de nível superior."""
        token = self.token_atual
        
        if not token:
            return None
        
        # Declaração de modo de CPU
        if token.tipo == TipoToken.MODO:
            return self._parse_declaracao_modo()
        
        # Declaração de função
        elif token.tipo == TipoToken.FUNCAO:
            return self._parse_declaracao_funcao()
        
        # Declaração de interrupção
        elif token.tipo == TipoToken.INTERRUPCAO:
            return self._parse_declaracao_interrupcao()
        
        else:
            raise ParserError(f"Declaração inesperada: {token.tipo.name}", token)
    
    def _parse_declaracao_modo(self):
        """Analisa declaração de modo de CPU: modo 16bits { ... }"""
        token_modo = self._verificar(TipoToken.MODO)
        linha = token_modo.linha
        
        # Determina qual modo (16, 32 ou 64 bits)
        if self.token_atual.tipo == TipoToken.MODO_16BITS:
            modo = 16
        elif self.token_atual.tipo == TipoToken.MODO_32BITS:
            modo = 32
        elif self.token_atual.tipo == TipoToken.MODO_64BITS:
            modo = 64
        else:
            raise ParserError(f"Modo de CPU inválido", self.token_atual)
        
        self.modo_atual = modo
        self._avancar()
        
        # Parse do bloco
        bloco = self._parse_bloco()
        
        print(f"[Parser] Declaração de modo {modo} bits na linha {linha}")
        return NoDeclaracaoModo(modo, bloco, linha)
    
    def _parse_declaracao_funcao(self):
        """Analisa declaração de função: funcao nome(parametros) { ... }"""
        token_funcao = self._verificar(TipoToken.FUNCAO)
        linha = token_funcao.linha
        
        # Nome da função
        token_nome = self._verificar(TipoToken.IDENTIFICADOR)
        nome_funcao = token_nome.valor
        
        # Verifica se a função já foi declarada
        if nome_funcao in self.funcoes_declaradas:
            raise ParserError(f"Função '{nome_funcao}' já foi declarada anteriormente", token_nome)
        
        self.funcoes_declaradas.add(nome_funcao)
        
        # Parâmetros
        self._verificar(TipoToken.PARENTESE_ABRE)
        parametros = self._parse_parametros()
        self._verificar(TipoToken.PARENTESE_FECHA)
        
        # Corpo da função
        corpo = self._parse_bloco()
        
        print(f"[Parser] Função '{nome_funcao}' declarada na linha {linha}")
        return NoDeclaracaoFuncao(nome_funcao, parametros, corpo, linha)
    
    def _parse_declaracao_interrupcao(self):
        """Analisa declaração de interrupção: interrupcao nome() { ... }"""
        token_interrupcao = self._verificar(TipoToken.INTERRUPCAO)
        linha = token_interrupcao.linha
        
        # Nome da interrupção
        token_nome = self._verificar(TipoToken.IDENTIFICADOR)
        nome_interrupcao = token_nome.valor
        
        # Parâmetros (interrupções geralmente não têm)
        self._verificar(TipoToken.PARENTESE_ABRE)
        self._verificar(TipoToken.PARENTESE_FECHA)
        
        # Corpo da interrupção
        corpo = self._parse_bloco()
        
        print(f"[Parser] Interrupção '{nome_interrupcao}' declarada na linha {linha}")
        return NoDeclaracaoInterrupcao(nome_interrupcao, corpo, linha)
    
    def _parse_parametros(self):
        """Analisa lista de parâmetros: (tipo nome, tipo nome, ...)"""
        parametros = []
        
        if self.token_atual.tipo != TipoToken.PARENTESE_FECHA:
            while True:
                # tipo nome
                if self.token_atual.tipo in [TipoToken.BYTE, TipoToken.WORD, TipoToken.DWORD, 
                                            TipoToken.QWORD, TipoToken.INTEIRO]:
                    tipo = self.token_atual.valor
                    self._avancar()
                else:
                    # Tipo implícito (inteiro)
                    tipo = 'inteiro'
                
                nome = self._verificar(TipoToken.IDENTIFICADOR).valor
                parametros.append((tipo, nome))
                
                # Verifica se há mais parâmetros
                if self.token_atual.tipo != TipoToken.VIRGULA:
                    break
                self._avancar()  # Pula a vírgula
        
        return parametros
    
    def _parse_bloco(self):
        """Analisa um bloco de código: { comandos... }"""
        self._verificar(TipoToken.CHAVE_ABRE)
        linha = self.token_atual.linha if self.token_atual else 0
        
        bloco = NoBloco(linha)
        
        # Parse comandos até encontrar fecha chaves
        while self.token_atual and self.token_atual.tipo != TipoToken.CHAVE_FECHA:
            comando = self._parse_comando()
            if comando:
                bloco.adicionar_comando(comando)
        
        self._verificar(TipoToken.CHAVE_FECHA)
        return bloco
    
    def _parse_comando(self):
        """Analisa um comando dentro de um bloco."""
        token = self.token_atual
        
        if not token:
            return None
        
        # Comandos de memória (memoria video = 0xB8000)
        if token.tipo == TipoToken.MEMORIA:
            return self._parse_atribuicao_memoria()
        
        # Comandos de port I/O
        elif token.tipo in [TipoToken.PORT_IN, TipoToken.PORT_OUT]:
            return self._parse_acesso_porta()
        
        # Estruturas de controle
        elif token.tipo == TipoToken.SE:
            return self._parse_estrutura_se()
        
        elif token.tipo == TipoToken.ENQUANTO:
            return self._parse_estrutura_enquanto()
        
        elif token.tipo == TipoToken.PARA:
            return self._parse_estrutura_para()
        
        # Retorno
        elif token.tipo == TipoToken.RETORNO:
            return self._parse_retorno()
        
        # Chamada de método ou função, ou atribuição
        elif token.tipo == TipoToken.IDENTIFICADOR:
            return self._parse_expressao_ou_atribuicao()
        
        else:
            raise ParserError(f"Comando inesperado: {token.tipo.name}", token)
    
    def _parse_atribuicao_memoria(self):
        """Analisa atribuição de memória: memoria video = 0xB8000"""
        token_memoria = self._verificar(TipoToken.MEMORIA)
        linha = token_memoria.linha
        
        nome_variavel = self._verificar(TipoToken.IDENTIFICADOR).valor
        self._verificar(TipoToken.ATRIBUICAO)
        
        # O endereço deve ser um número (hexadecimal ou decimal)
        endereco = self._parse_expressao_primaria()
        
        self._verificar_opcional(TipoToken.PONTO_VIRGULA)  # Opcional
        
        print(f"[Parser] Atribuição de memória: {nome_variavel} = {endereco.valor}")
        return NoAtribuicaoMemoria(nome_variavel, endereco, linha)
    
    def _parse_acesso_porta(self):
        """Analisa acesso a portas: port.inb(0x60) ou port.outb(0x20, 0x20)"""
        token_port = self._verificar(TipoToken.PORT)
        linha = token_port.linha
        
        # Ponto obrigatório
        self._verificar(TipoToken.PONTO)
        
        # Tipo de operação (in/out com tamanho)
        token_operacao = self.token_atual
        if token_operacao.tipo == TipoToken.PORT_IN:
            operacao = 'in'
            tamanho = token_operacao.valor[2:]  # 'b', 'w', 'd'
        elif token_operacao.tipo == TipoToken.PORT_OUT:
            operacao = 'out'
            tamanho = token_operacao.valor[3:]  # 'b', 'w', 'd'
        else:
            raise ParserError(f"Operação de porta inválida", token_operacao)
        
        self._avancar()
        
        # Parênteses e argumentos
        self._verificar(TipoToken.PARENTESE_ABRE)
        
        porta = self._parse_expressao()
        
        valor = None
        if operacao == 'out':
            self._verificar(TipoToken.VIRGULA)
            valor = self._parse_expressao()
        
        self._verificar(TipoToken.PARENTESE_FECHA)
        self._verificar_opcional(TipoToken.PONTO_VIRGULA)
        
        print(f"[Parser] Acesso a porta: {operacao}{tamanho} porta={porta.valor}")
        no = NoAcessoPorta(f"{operacao}{tamanho}", porta, valor, linha)
        return no
    
    def _parse_estrutura_se(self):
        """Analisa estrutura condicional: se (condicao) { ... } senao { ... }"""
        token_se = self._verificar(TipoToken.SE)
        linha = token_se.linha
        
        self._verificar(TipoToken.PARENTESE_ABRE)
        condicao = self._parse_expressao()
        self._verificar(TipoToken.PARENTESE_FECHA)
        
        bloco_verdadeiro = self._parse_bloco()
        
        # Verifica se tem senao
        bloco_falso = None
        if self.token_atual and self.token_atual.tipo == TipoToken.SENAO:
            self._avancar()
            bloco_falso = self._parse_bloco()
        
        print(f"[Parser] Estrutura se/senao na linha {linha}")
        return NoSe(condicao, bloco_verdadeiro, bloco_falso, linha)
    
    def _parse_estrutura_enquanto(self):
        """Analisa estrutura de loop: enquanto (condicao) { ... }"""
        token_enquanto = self._verificar(TipoToken.ENQUANTO)
        linha = token_enquanto.linha
        
        self._verificar(TipoToken.PARENTESE_ABRE)
        condicao = self._parse_expressao()
        self._verificar(TipoToken.PARENTESE_FECHA)
        
        corpo = self._parse_bloco()
        
        print(f"[Parser] Loop enquanto na linha {linha}")
        return NoEnquanto(condicao, corpo, linha)
    
    def _parse_estrutura_para(self):
        """Analisa estrutura de loop: para (inicializacao; condicao; incremento) { ... }"""
        token_para = self._verificar(TipoToken.PARA)
        linha = token_para.linha
        
        self._verificar(TipoToken.PARENTESE_ABRE)
        inicializacao = self._parse_expressao()
        self._verificar(TipoToken.PONTO_VIRGULA)
        condicao = self._parse_expressao()
        self._verificar(TipoToken.PONTO_VIRGULA)
        incremento = self._parse_expressao()
        self._verificar(TipoToken.PARENTESE_FECHA)
        
        corpo = self._parse_bloco()
        
        print(f"[Parser] Loop para na linha {linha}")
        return NoPara(inicializacao, condicao, incremento, corpo, linha)
    
    def _parse_retorno(self):
        """Analisa comando de retorno: retorno expressao;"""
        token_retorno = self._verificar(TipoToken.RETORNO)
        linha = token_retorno.linha
        
        # Expressão opcional (pode ser retorno vazio)
        expressao = None
        if self.token_atual and self.token_atual.tipo != TipoToken.PONTO_VIRGULA and self.token_atual.tipo != TipoToken.CHAVE_FECHA:
            expressao = self._parse_expressao()
        
        self._verificar_opcional(TipoToken.PONTO_VIRGULA)
        return NoRetorno(expressao, linha)
    
    def _parse_expressao_ou_atribuicao(self):
        """
        Analisa uma expressão que começa com identificador.
        Pode ser: chamada de método, chamada de função, ou atribuição.
        """
        token_nome = self._verificar(TipoToken.IDENTIFICADOR)
        nome = token_nome.valor
        linha = token_nome.linha
        
        # Chamada de método: objeto.metodo(args)
        if self.token_atual and self.token_atual.tipo == TipoToken.PONTO:
            return self._parse_chamada_metodo(nome, linha)
        
        # Atribuição: nome = expressao
        elif self.token_atual and self.token_atual.tipo == TipoToken.ATRIBUICAO:
            self._avancar()
            valor = self._parse_expressao()
            self._verificar_opcional(TipoToken.PONTO_VIRGULA)
            return NoAtribuicao(nome, valor, linha)
        
        # Chamada de função: nome(args)
        elif self.token_atual and self.token_atual.tipo == TipoToken.PARENTESE_ABRE:
            self._avancar()
            argumentos = self._parse_argumentos()
            self._verificar(TipoToken.PARENTESE_FECHA)
            self._verificar_opcional(TipoToken.PONTO_VIRGULA)
            return NoChamadaFuncao(nome, argumentos, linha)
        
        else:
            raise ParserError(f"Uso inválido do identificador '{nome}'", self.token_atual)
    
    def _parse_chamada_metodo(self, objeto, linha):
        """Analisa chamada de método: objeto.metodo(argumentos)"""
        self._verificar(TipoToken.PONTO)
        
        metodo = self._verificar(TipoToken.IDENTIFICADOR).valor
        
        self._verificar(TipoToken.PARENTESE_ABRE)
        argumentos = self._parse_argumentos()
        self._verificar(TipoToken.PARENTESE_FECHA)
        self._verificar_opcional(TipoToken.PONTO_VIRGULA)
        
        print(f"[Parser] Chamada de método: {objeto}.{metodo}()")
        return NoChamadaMetodo(objeto, metodo, argumentos, linha)
    
    def _parse_argumentos(self):
        """Analisa lista de argumentos de função/método."""
        argumentos = []
        
        # Se o próximo token não é fecha parênteses, há argumentos
        if self.token_atual and self.token_atual.tipo != TipoToken.PARENTESE_FECHA:
            while True:
                argumento = self._parse_expressao()
                argumentos.append(argumento)
                
                if self.token_atual.tipo != TipoToken.VIRGULA:
                    break
                self._avancar()
        
        return argumentos
    
    def _parse_expressao(self):
        """
        Analisa uma expressão completa.
        Implementa precedência de operadores.
        """
        return self._parse_expressao_atribuicao()
    
    def _parse_expressao_atribuicao(self):
        """Menor precedência: = """
        esquerda = self._parse_expressao_logica_ou()
        
        if self.token_atual and self.token_atual.tipo == TipoToken.ATRIBUICAO:
            operador = self.token_atual.valor
            linha = self.token_atual.linha
            self._avancar()
            direita = self._parse_expressao_atribuicao()
            return NoExpressaoBinaria(esquerda, operador, direita, linha)
        
        return esquerda
    
    def _parse_expressao_logica_ou(self):
        """Precedência: ||"""
        esquerda = self._parse_expressao_logica_e()
        
        while self.token_atual and self.token_atual.tipo == TipoToken.OU_LOGICO:
            operador = self.token_atual.valor
            linha = self.token_atual.linha
            self._avancar()
            direita = self._parse_expressao_logica_e()
            esquerda = NoExpressaoBinaria(esquerda, operador, direita, linha)
        
        return esquerda
    
    def _parse_expressao_logica_e(self):
        """Precedência: &&"""
        esquerda = self._parse_expressao_comparacao()
        
        while self.token_atual and self.token_atual.tipo == TipoToken.E_LOGICO:
            operador = self.token_atual.valor
            linha = self.token_atual.linha
            self._avancar()
            direita = self._parse_expressao_comparacao()
            esquerda = NoExpressaoBinaria(esquerda, operador, direita, linha)
        
        return esquerda
    
    def _parse_expressao_comparacao(self):
        """Precedência: == != < > <= >="""
        esquerda = self._parse_expressao_bitwise()
        
        operadores_comparacao = [
            TipoToken.IGUAL, TipoToken.DIFERENTE, 
            TipoToken.MENOR, TipoToken.MAIOR,
            TipoToken.MENOR_IGUAL, TipoToken.MAIOR_IGUAL
        ]
        
        if self.token_atual and self.token_atual.tipo in operadores_comparacao:
            operador = self.token_atual.valor
            linha = self.token_atual.linha
            self._avancar()
            direita = self._parse_expressao_bitwise()
            return NoExpressaoBinaria(esquerda, operador, direita, linha)
        
        return esquerda
    
    def _parse_expressao_bitwise(self):
        """Precedência: & | ^ << >>"""
        esquerda = self._parse_expressao_aditiva()
        
        operadores_bitwise = [
            TipoToken.E_BIT, TipoToken.OU_BIT, TipoToken.XOR_BIT,
            TipoToken.SHIFT_ESQUERDA, TipoToken.SHIFT_DIREITA
        ]
        
        while self.token_atual and self.token_atual.tipo in operadores_bitwise:
            operador = self.token_atual.valor
            linha = self.token_atual.linha
            self._avancar()
            direita = self._parse_expressao_aditiva()
            esquerda = NoExpressaoBinaria(esquerda, operador, direita, linha)
        
        return esquerda
    
    def _parse_expressao_aditiva(self):
        """Precedência: + -"""
        esquerda = self._parse_expressao_multiplicativa()
        
        while self.token_atual and self.token_atual.tipo in [TipoToken.SOMA, TipoToken.SUBTRACAO]:
            operador = self.token_atual.valor
            linha = self.token_atual.linha
            self._avancar()
            direita = self._parse_expressao_multiplicativa()
            esquerda = NoExpressaoBinaria(esquerda, operador, direita, linha)
        
        return esquerda
    
    def _parse_expressao_multiplicativa(self):
        """Precedência: * / %"""
        esquerda = self._parse_expressao_unaria()
        
        while self.token_atual and self.token_atual.tipo in [TipoToken.MULTIPLICACAO, TipoToken.DIVISAO, TipoToken.MODULO]:
            operador = self.token_atual.valor
            linha = self.token_atual.linha
            self._avancar()
            direita = self._parse_expressao_unaria()
            esquerda = NoExpressaoBinaria(esquerda, operador, direita, linha)
        
        return esquerda
    
    def _parse_expressao_unaria(self):
        """Precedência: ! - ~ (operadores unários)"""
        token = self.token_atual
        
        if token and token.tipo in [TipoToken.NAO_LOGICO, TipoToken.SUBTRACAO, TipoToken.NAO_BIT]:
            operador = token.valor
            linha = token.linha
            self._avancar()
            expressao = self._parse_expressao_unaria()
            return NoExpressaoUnaria(operador, expressao, linha)
        
        return self._parse_expressao_primaria()
    
    def _parse_expressao_primaria(self):
        """
        Analisa expressões primárias: literais, identificadores, parênteses.
        """
        token = self.token_atual
        
        if not token:
            raise ParserError("Expressão incompleta", None)
        
        # Números
        if token.tipo == TipoToken.NUMERO:
            self._avancar()
            return NoLiteral(TipoNo.LITERAL_NUMERO, token.valor, token.linha)
        
        # Números hexadecimais
        elif token.tipo == TipoToken.NUMERO_HEX:
            self._avancar()
            return NoLiteral(TipoNo.LITERAL_HEX, token.valor, token.linha)
        
        # Strings
        elif token.tipo == TipoToken.STRING:
            self._avancar()
            return NoLiteral(TipoNo.LITERAL_STRING, token.valor, token.linha)
        
        # Identificadores
        elif token.tipo == TipoToken.IDENTIFICADOR:
            self._avancar()
            return NoLiteral(TipoNo.LITERAL_IDENTIFICADOR, token.valor, token.linha)
        
        # Parênteses (expressão agrupada)
        elif token.tipo == TipoToken.PARENTESE_ABRE:
            self._avancar()
            expressao = self._parse_expressao()
            self._verificar(TipoToken.PARENTESE_FECHA)
            return expressao
        
        else:
            raise ParserError(f"Token inesperado em expressão: {token.tipo.name}", token)


def testar_parser_completo():
    """Testa o parser com um código completo da Yuui-Lang."""
    
    # Código de exemplo que mistura várias funcionalidades
    codigo_fonte = """
    // Kernel de teste da Yuui-OS
    
    modo 16bits {
        funcao bootloader() {
            memoria video = 0xB8000
            video.limpar()
            video.escrever("Yuui-OS Bootloader v0.1")
            
            sistema.a20_habilitar()
            disco.carregar(2, 10, 0x100000)
            sistema.modo_transicionar(64)
        }
    }
    
    modo 64bits {
        interrupcao teclado_handler() {
            byte scancode = port.inb(0x60)
            
            se (scancode == 0x1C) {
                tela.escrever("Enter pressionado!")
            } senao {
                tela.escrever("Outra tecla")
            }
            
            port.outb(0x20, 0x20)
        }
        
        funcao kernel_principal() {
            tela.limpar()
            tela.escrever("Yuui-OS Kernel v0.1 >>")
            
            enquanto (verdadeiro) {
                cpu.halt()
            }
        }
    }
    """
    
    print("="*70)
    print("PARSER DA YUUI-LANG - TESTE COMPLETO")
    print("="*70)
    print("\nCódigo fonte:")
    print("-"*70)
    print(codigo_fonte)
    print("-"*70)
    
    # Lexer
    print("\n[1] Executando Lexer...")
    lexer = Lexer(codigo_fonte, "kernel_teste.yuui")
    tokens = lexer.tokenizar()
    
    if not tokens:
        print("[ERRO] Falha na análise léxica!")
        return
    
    print(f"[OK] Lexer gerou {len(tokens)} tokens")
    
    # Parser
    print("\n[2] Executando Parser...")
    parser = Parser(tokens)
    ast = parser.parse()
    
    if ast:
        print("\n[3] AST gerada com sucesso!")
        print("\nÁrvore Sintática Abstrata:")
        print("="*70)
        ast.imprimir_arvore()
        
        # Estatísticas da AST
        print(f"\n{'='*70}")
        print("ESTATÍSTICAS DA AST")
        print(f"{'='*70}")
        print(f"Declarações no nível superior: {len(ast.declaracoes)}")
        
        for i, decl in enumerate(ast.declaracoes):
            print(f"  [{i}] {decl.tipo.name}: {decl.valor}")
        
        print(f"Total de nós na árvore: {contar_nos(ast)}")
    else:
        print("[ERRO] Falha na análise sintática!")


def contar_nos(no):
    """Conta recursivamente o número de nós na AST."""
    if no is None:
        return 0
    
    contagem = 1
    if hasattr(no, 'filhos'):
        for filho in no.filhos:
            contagem += contar_nos(filho)
    
    return contagem


if __name__ == "__main__":
    testar_parser_completo()