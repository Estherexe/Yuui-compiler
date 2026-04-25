🚀 Visão do Projeto
Diferente das linguagens modernas que se distanciam do hardware, a **Yuui-Lang** abraça o processador. Ela foi criada para eliminar a necessidade de arquivos `.asm` externos, integrando o controle de memória e interrupções diretamente na sintaxe.

### 🛠️ Diferenciais Técnicos
* **Hardware-Aware:** Tipos primitivos baseados em tamanhos de registradores (`byte`, `word`, `dword`, `qword`).
* **Gestão de Memória Absoluta:** Palavra-chave `memoria` para mapeamento direto de endereços fixos (VGA, MMIO, etc.).
* **Multi-Modo Nativo:** Suporte a diretivas de `modo 16bits` e `modo 64bits` no mesmo binário.
* **Inferência Inteligente:** Diferenciação automática entre inteiros, hexadecimais e ponteiros de memória.


📋 Sintaxe da Linguagem

1. Variáveis e Tipos
```text
byte tecla = 0x60          // 8 bits (I/O)
word flags = 0xFFFF        // 16 bits
dword endereco = 0x1000    // 32 bits
inteiro contador = 10      // 32 bits com sinal
```

2. Controle de Hardware (O diferencial Yuui-Lang)
```text
// Acesso direto à memória de vídeo (VGA Text Mode)
memoria video = 0xB8000 

funcao iniciar_so() {
    video.escrever("Yuui-OS carregado com sucesso!")
}
```

3. Modos de Operação
```text
modo 16bits {
    // Código para Bootloader / BIOS
}

modo 64bits {
    // Código para Kernel / Long Mode
}
```


🏗️ Arquitetura do Compilador

O compilador é construído do zero em Python para garantir total controle sobre o fluxo de compilação:

1.  **Lexer (`Lexer.py`):** Análise léxica e geração de tokens.
2.  **Parser (`Parser.py`):** Construção da Árvore de Sintaxe Abstrata (AST) e Tabela de Símbolos.
3.  **Tipos (`Tipos.py`):** Definição da hierarquia de hardware e regras de promoção de tipos.
4.  **Analisador Semântico:** (Em desenvolvimento) Validação de tipos e detecção de conflitos de memória.
5.  **Backend:** Geração direta de código de máquina/Assembly x86_64.


🛠️ Como Contribuir
Este é um projeto autoral e fechado para a visão de **Yuui**. O foco atual é:
* [ ] Finalizar o Analisador Semântico.
* [ ] Implementar o gerador de código Assembly (`Gerador.py`).
* [ ] Criar o sistema de tratamento de erros amigável.


📜 Licença
Projeto Privado - Criado por **Yuui** (2026). Todos os direitos reservados para a dominação mundial via código.

Dica de uso:

Para rodar o lexer e ver os tokens gerados:
```bash
python Lexer.py "seu_codigo.yuui"
```
