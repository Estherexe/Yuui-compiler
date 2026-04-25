from lark import Transformer

class YuuiTransformer(Transformer):
    def exibir_cmd(self, tokens):
        # Aqui você decide o que o comando faz
        texto = tokens[0].strip('"')
        return f'PRINT_STRING "{texto}"' # Ou o código em Assembly

# Usando o Transformer
transformador = YuuiTransformer()
resultado = transformador.transform(arvore)
print(resultado)