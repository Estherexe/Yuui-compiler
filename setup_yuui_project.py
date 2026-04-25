"""
setup_yuui_project.py - Script de Reestruturação do Projeto Yuui-Lang
Cria a nova estrutura profissional e atualiza todos os imports.
"""

import os
import shutil
from pathlib import Path

def criar_estrutura_profissional():
    """Cria a estrutura de diretórios profissional da Yuui-Lang."""
    
    print("""
    ╔══════════════════════════════════════════════════════╗
    ║     🏗️  REESTRUTURAÇÃO YUUI-LANG TOOLCHAIN         ║
    ║     De Projeto Pessoal → Ferramenta Profissional     ║
    ╚══════════════════════════════════════════════════════╝
    """)
    
    # Estrutura de diretórios
    estrutura = {
        'src/yuui': {
            'descricao': 'Código fonte principal do compilador',
            'arquivos': {
                'YuuiLexer.py': 'Lexer.py',
                'YuuiParser.py': 'Parser.py',
                'YuuiSemantics.py': 'Tipos.py',
                'YuuiEmitter.py': 'GeradorCodigo.py',
                'YuuiCompiler.py': 'Backend.py',
                '__init__.py': None  # Será criado novo
            }
        },
        'tests': {
            'descricao': 'Testes automatizados',
            'arquivos': {
                'test_bootloader.py': 'bootloader_test_v2.py',
                'test_compiler.py': 'testar_compilador.py'
            }
        },
        'examples': {
            'descricao': 'Exemplos de código Yuui-Lang',
            'arquivos': {
                'kernel_minimo.yuui': None,
                'boot_test.yuui': 'boot_test.yuui'
            }
        },
        'docs': {
            'descricao': 'Documentação do projeto',
            'arquivos': {}
        },
        'bin': {
            'descricao': 'Binários compilados (gerados automaticamente)',
            'arquivos': {}
        }
    }
    
    print("📁 Criando estrutura de diretórios...\n")
    
    for diretorio, info in estrutura.items():
        print(f"   📂 {diretorio}/")
        print(f"      └─ {info['descricao']}")
        os.makedirs(diretorio, exist_ok=True)
    
    # Mapeamento de arquivos para renomear
    mapeamento = {
        'src/yuui/YuuiLexer.py': 'Lexer.py',
        'src/yuui/YuuiParser.py': 'Parser.py',
        'src/yuui/YuuiSemantics.py': 'Tipos.py',
        'src/yuui/YuuiEmitter.py': 'GeradorCodigo.py',
        'src/yuui/YuuiCompiler.py': 'Backend.py'
    }
    
    print("\n📝 Renomeando e movendo arquivos...\n")
    
    for novo_nome, nome_antigo in mapeamento.items():
        if os.path.exists(nome_antigo):
            # Lê o conteúdo
            with open(nome_antigo, 'r', encoding='utf-8') as f:
                conteudo = f.read()
            
            # Atualiza os imports no conteúdo
            conteudo = atualizar_imports(conteudo, nome_antigo, novo_nome)
            
            # Salva no novo local
            with open(novo_nome, 'w', encoding='utf-8') as f:
                f.write(conteudo)
            
            print(f"   ✅ {nome_antigo} → {novo_nome}")
        else:
            print(f"   ⚠️  {nome_antigo} não encontrado (pulando)")
    
    # Cria __init__.py
    print("\n📦 Criando pacotes Python...")
    
    init_content = """'''
Yuui-Lang Compiler Toolchain
============================
Uma linguagem de programação para sistemas operacionais.
Desenvolvida para ser extremamente fácil, mas poderosa o suficiente
para recriar um SO do zero.

Modulos:
    YuuiLexer     - Analisador léxico
    YuuiParser    - Analisador sintático
    YuuiSemantics - Verificador de tipos
    YuuiEmitter   - Gerador de código Assembly
    YuuiCompiler  - Compilador principal
'''

__version__ = '0.2.0'
__author__ = 'Yuui'
__description__ = 'Linguagem de Programação para Sistemas Operacionais'

from .YuuiCompiler import CompiladorYuui

__all__ = ['CompiladorYuui']
"""
    
    with open('src/yuui/__init__.py', 'w', encoding='utf-8') as f:
        f.write(init_content)
    print("   ✅ src/yuui/__init__.py criado")
    
    # Cria __init__.py para tests
    with open('tests/__init__.py', 'w') as f:
        f.write('# Testes da Yuui-Lang\n')
    print("   ✅ tests/__init__.py criado")
    
    # Move arquivos de exemplo
    print("\n📋 Movendo exemplos...")
    for exemplo in ['boot_test.yuui', 'kernel.yuui']:
        if os.path.exists(exemplo):
            shutil.copy2(exemplo, f'examples/{exemplo}')
            print(f"   ✅ {exemplo} → examples/{exemplo}")
    
    return True


def atualizar_imports(conteudo, nome_antigo, novo_nome):
    """Atualiza as declarações de import nos arquivos."""
    
    # Mapeamento de imports antigos para novos
    substituicoes = {
        'from Lexer import': 'from YuuiLexer import',
        'import Lexer': 'import YuuiLexer as Lexer',
        'from Parser import': 'from YuuiParser import',
        'from Parser_V2 import': 'from YuuiParser import',
        'from Tipos import': 'from YuuiSemantics import',
        'import Tipos': 'import YuuiSemantics as Tipos',
        'from GeradorCodigo import': 'from YuuiEmitter import',
        'import GeradorCodigo': 'import YuuiEmitter as GeradorCodigo',
        'from Backend import': 'from YuuiCompiler import',
    }
    
    for antigo, novo in substituicoes.items():
        conteudo = conteudo.replace(antigo, novo)
    
    return conteudo


def criar_readme():
    """Cria um README.md profissional."""
    
    readme = """# 🚀 Yuui-Lang

[![Versão](https://img.shields.io/badge/versão-0.2.0-blue.svg)]()
[![Licença](https://img.shields.io/badge/licença-MIT-green.svg)]()
[![Status](https://img.shields.io/badge/status-em%20desenvolvimento-orange.svg)]()

**Yuui-Lang** é uma linguagem de programação para sistemas operacionais.  
Projetada para ser **extremamente fácil**, mas poderosa o suficiente para **recriar um SO do zero**.

---

## ✨ Características

- 🎯 **Sintaxe limpa e intuitiva** (inspirada no português)
- ⚡ **Compilação direta para Assembly NASM**
- 🖥️ **Suporte a múltiplos modos de CPU** (16/32/64 bits)
- 🔧 **Pipeline de compilação completo**: Lexer → Parser → Semântico → Emitter → Compilador
- 💾 **Geração de bootloaders e kernels executáveis**

---

## 📂 Estrutura do Projeto
