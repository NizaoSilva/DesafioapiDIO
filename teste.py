class PlanoTelefone:
    def __init__(self, nome_plano, saldo_inicial):
        self.nome_plano = nome_plano
        self._saldo_inicial = saldo_inicial
    @property
    def verificar_saldo(self):
        return self._saldo_inicial
    @property
    def mensagem_personalizada(self):
        print()
class UsuarioTelefone:
    def __init__(self, nome_usuario, plano_usuario: PlanoTelefone):
        self.nome = nome_usuario
        self.plano = plano_usuario
    def verificar_saldo(self):
        return self.plano.verificar_saldo, self.mensagem_personalizada()
    def mensagem_personalizada(self):
        if self.plano.verificar_saldo < 10:
            return "Seu saldo está baixo. Recarregue e use os serviços do seu plano."
        elif self.plano.verificar_saldo > 50:
            return "Parabéns! Continue aproveitando seu plano sem preocupações."
        else:
            return "Seu saldo está razoável. Aproveite o uso moderado do seu plano."
nome_usuario = input()
nome_plano = input()
saldo_inicial = float(input())

plano_usuario = PlanoTelefone(nome_plano, saldo_inicial) 
usuario = UsuarioTelefone(nome_usuario, plano_usuario)  

saldo_usuario, mensagem_usuario = usuario.verificar_saldo()  
print(mensagem_usuario)