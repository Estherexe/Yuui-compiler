# Salve como: criar_estrutura.py
import os

print("Criando estrutura Yuui-Lang...")

# Cria diretorios
diretorios = [
    'src/yuui',
    'tests',
    'examples',
    'docs',
    'bin'
]

for d in diretorios:
    os.makedirs(d, exist_ok=True)
    print(f"✅ {d}/")

# Lista de arquivos para renomear
arquivos = {
    'src/yuui/YuuiLexer.py': 'Lexer.py',
    'src/yuui/YuuiParser.py': 'Parser.py',
    'src/yuui/YuuiSemantics.py': 'Tipos.py',
    'src/yuui/YuuiEmitter.py': 'GeradorCodigo.py',
    'src/yuui/YuuiCompiler.py': 'Backend.py',
}

print("\nRenomeando arquivos...")
for novo, antigo in arquivos.items():
    if os.path.exists(antigo):
        # Le o conteudo
        with open(antigo, 'r', encoding='utf-8') as f:
            conteudo = f.read()
        
        # Atualiza imports
        conteudo = conteudo.replace('from Lexer import', 'from .YuuiLexer import')
        conteudo = conteudo.replace('from Parser import', 'from .YuuiParser import')
        conteudo = conteudo.replace('from Parser_V2 import', 'from .YuuiParser import')
        conteudo = conteudo.replace('from Tipos import', 'from .YuuiSemantics import')
        conteudo = conteudo.replace('from GeradorCodigo import', 'from .YuuiEmitter import')
        conteudo = conteudo.replace('from Backend import', 'from .YuuiCompiler import')
        conteudo = conteudo.replace('import Lexer', 'from . import YuuiLexer as Lexer')
        conteudo = conteudo.replace('import Tipos', 'from . import YuuiSemantics as Tipos')
        
        # Salva no novo local
        with open(novo, 'w', encoding='utf-8') as f:
            f.write(conteudo)
        
        print(f"✅ {antigo} → {novo}")
    else:
        print(f"⚠️  {antigo} nao encontrado")

# Cria __init__.py
init_content = '''"""
Yuui-Lang Compiler Toolchain
Linguagem de programacao para sistemas operacionais.
"""

__version__ = '0.2.0'
__author__ = 'Yuui'

from .YuuiCompiler import CompiladorYuui

__all__ = ['CompiladorYuui']
'''

with open('src/yuui/__init__.py', 'w', encoding='utf-8') as f:
    f.write(init_content)
print("✅ src/yuui/__init__.py")

# Cria setup.py
setup_content = '''"""
Setup da Yuui-Lang
Execute: pip install -e .
"""

from setuptools import setup, find_packages

setup(
    name='yuui-lang',
    version='0.2.0',
    description='Linguagem de Programacao para Sistemas Operacionais',
    author='Yuui',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    python_requires='>=3.8',
)
'''

with open('setup.py', 'w', encoding='utf-8') as f:
    f.write(setup_content)
print("✅ setup.py criado")

print("\n🎉 ESTRUTURA CRIADA COM SUCESSO!")
print("\nAgora execute:")
print("  pip install -e .")
print("  python -m yuui.YuuiCompiler examples/kernel_minimo.yuui")