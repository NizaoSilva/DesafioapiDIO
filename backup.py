import textwrap
from abc import ABC, abstractclassmethod, abstractproperty
from datetime import datetime
class Lista():
    def __init__(self):
        self.registros = {}
    def __setitem__(self, chave, valor):
        self.registros[chave] = valor
class Pessoa:
    def __init__(self, cpf, nome, data_nascimento, endereco):
        self.cpf = cpf
        self.nome = nome
        self.data_nascimento = data_nascimento
        self.endereco = endereco
        Pessoas._registros[self.cpf] = self
    # def Criar_conta(self, senha) -> 'Conta':
    #     cliente = Cliente(self.cpf, self.nome, self.data_nascimento, self.endereco)
    #     conta = ContaCorrente(self, senha)
    #     cliente.contas.Adicionar(conta)
    #     self.__dict__ = cliente.__dict__
        # return conta
    def __str__(self):
        return self.cpf
class Cliente(Pessoa):
    def __init__(self, cpf, nome, data_nascimento, endereco):
        self.cpf = cpf
        self.nome = nome
        self.data_nascimento = data_nascimento
        self.endereco = endereco
        Pessoas._registros[self.cpf] = self
        self.contas = Contas()
        Clientes._registros[self.cpf] = self
    def Realizar_transacao(self, conta, transacao: 'Transacao'):
        transacao.registrar(conta)
    def Criar_conta(self, senha) -> 'Conta':
        conta = ContaCorrente(self, senha)
        self.contas.Adicionar(conta)
        return conta
class Clientes(Lista):
    _registros = {}
    def Adicionar(self, cliente: Cliente) -> Cliente:
        self.registros[cliente.codigo] = cliente
        print(f"=== Cliente de número {cliente.codigo} criada com sucesso! ===")
        return cliente
    def __getitem__(self, cpf) -> Cliente: # Para obter a posição do objeto na lista: def Index(self, cpf) -> 'Cliente': 
        return self.registros[cpf]              # return self.registros[list(self.registros.keys())[cpf]]
    @staticmethod
    def Index(cpf) -> Cliente:
        return Clientes._registros[cpf]
class Pessoas(Lista):
    _registros = {}
    def __init__(self):
        super().__init__()
        self.clientes = Clientes()
    def Adicionar(self, pessoa: Pessoa):
        if isinstance(pessoa, Pessoa):
            if isinstance(pessoa, Cliente):
                self.clientes[pessoa.cpf] = pessoa
            self.registros[pessoa.cpf] = pessoa
            print(f"=== {pessoa.nome} cadastrado com sucesso! ===")
        else:
            print("@@@@@@@@@ Erro @@@@@@@@@ Erro @@@@@@@@@ Erro @@@@@@@@@ Erro @@@@@@@@@")
    def __getitem__(self, cpf) -> Pessoa:
        return self.registros[cpf]
    @staticmethod
    def Index(cpf) -> Pessoa:
        return Pessoas._registros[cpf]
class Contas(Lista):
    _registros = {}
    def Adicionar(self, conta: 'Conta'):
        # conta.codigo = len(Contas.registros)
        # Contas.registros[conta.codigo] = conta
        self.registros[conta.codigo] = conta
        print(f"=== Conta de número {conta.codigo} criada com sucesso! ===")
        return conta
    def __getitem__(self, numero) -> 'Conta':
        return self._registros[numero]
    @staticmethod
    def Index(numero) -> 'Conta':
        return Contas._registros[numero]
class Conta: 
    def __init__(self, cliente, senha):
        self.senha = senha
        self._saldo = 0
        self.codigo = len(Contas._registros)
        self._agencia = "0001"
        self._cliente = cliente
        self._transacoes = Transacoes()
        Contas._registros[self.codigo] = self
    def __getitem__(self, chave):
        return Conta.contas[chave]
    @property
    def saldo(self):
        return self._saldo
    @property
    def agencia(self):
        return self._agencia
    @property
    def cliente(self):
        return self._cliente
    @property
    def historico(self):
        return self._transacoes
    def sacar(self, valor=0):
        valor = float(input("Informe o valor do depósito: ")) if valor == 0 else valor
        saldo = self.saldo
        if valor > saldo:
            print("@@@ Operação falhou! Você não tem saldo suficiente. @@@")
        elif valor > 0:
            saque = Saque(valor)
            self._transacoes.adicionar_transacao(saque)
            self._saldo -= valor
            print("=== Saque realizado com sucesso! ===")
            return True
        else:
            print("@@@ Operação falhou! O valor informado é inválido. @@@")
        return False
    def depositar(self, valor=0):
        valor = float(input("Informe o valor do depósito: ")) if valor == 0 else valor
        if valor > 0:
            deposito = Deposito(valor)
            self._transacoes.adicionar_transacao(deposito)
            self._saldo += valor
            print("=== Depósito realizado com sucesso! ===")
            return True
        else:
            print("@@@ Operação falhou! O valor informado é inválido. @@@")
            return False
    def exibir_extrato(self):
        print("================ EXTRATO ================")
        transacoes = self.historico.transacoes
        extrato = ""
        if not transacoes:
            extrato = "Não foram realizadas movimentações."
        else:
            for transacao in transacoes:
                extrato += f"{transacao['tipo']}:\n\tR$ {transacao['valor']:.2f}\n"
        print(extrato)
        print(f"Saldo:\n\tR$ {self.saldo:.2f}")
        print("==========================================")
class ContaCorrente(Conta):
    def __init__(self, cliente, senha, limite=500, limite_saques=3):
        super().__init__(cliente, senha)
        self._limite = limite
        self._limite_saques = limite_saques
    def sacar(self, valor=0):
        numero_saques = len(
            [transacao for transacao in self.historico.transacoes if transacao["tipo"] == Saque.__name__])
        excedeu_limite = valor > self._limite
        excedeu_saques = numero_saques >= self._limite_saques
        if excedeu_limite:
            print("\n@@@ Operação falhou! O valor do saque excede o limite. @@@")
        elif excedeu_saques:
            print("\n@@@ Operação falhou! Número máximo de saques excedido. @@@")
        else:
            return super().sacar(valor)
        return False
    def __str__(self):
        return f"""\
            Agência:\t{self.agencia}
            C/C:\t\t{self.codigo}
            Titular:\t{self.cliente.nome}
        """
class Transacoes:
    def __init__(self):
        self._transacoes = []
    @property
    def transacoes(self):
        return self._transacoes
    def adicionar_transacao(self, transacao):
        self._transacoes.append(
            {
                "tipo": transacao.__class__.__name__,
                "valor": transacao.valor,
                "data": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
            }
        )
class Transacao(ABC):
    @property
    @abstractproperty
    def valor(self):
        pass
    @abstractclassmethod
    def registrar(self, conta):
        pass
class Saque(Transacao):
    def __init__(self, valor):
        self._valor = valor
    @property
    def valor(self):
        return self._valor
    def registrar(self, conta):
        sucesso_transacao = conta.sacar(self.valor)
        if sucesso_transacao:
            conta.historico.adicionar_transacao(self)
class Deposito(Transacao):
    def __init__(self, valor):
        self._valor = valor
    @property
    def valor(self):
        return self._valor
    def registrar(self, conta):
        sucesso_transacao = conta.depositar(self.valor)
        if sucesso_transacao:
            conta.historico.adicionar_transacao(self)
class Interface():
    def __init__(self, pessoas):
        # self._pessoas = pessoas
        while True:
            resposta = self.menu()
            if resposta == "lo": #Login
                codigo = int(input("Informe o código da conta: "))
                conta = ContaCorrente.contas[codigo]
                if conta:
                    senha = input("Informe a senha da conta: ")
                    if senha == conta.senha:
                        while True:
                            resposta = self.menulogin()
                            if resposta == "d":
                                conta.depositar()
                            elif resposta == "s":
                                conta.sacar()
                            elif resposta == "e":
                                # Aquiparei
                                conta.exibir_extrato()
                                # exibir_extrato(conta['saldo'], extrato=conta['extrato'])
                            elif resposta == "q":
                                break
                            else:
                                print("Operação inválida, por favor selecione novamente a operação desejada.")
                    else:
                        print("\n@@@ Senha inválida, por favor selecione novamente a operação desejada. @@@")
                else:
                    print("\n@@@ Conta não existe! @@@")
            elif resposta == "nu": #Criar_usuário
                criar_usuario(usuarios)
            elif resposta == "lu": #Listar_usuarios
                listar_usuarios(usuarios)
            elif resposta == "nc": #Criar_conta
                criar_conta(AGENCIA, usuarios, contas)
            elif resposta == "lc": #Listar_contas
                listar_contas(contas)
            elif resposta == "q": #Sair
                break
            else:
                print("Operação inválida, por favor selecione novamente a operação desejada.")
    def menu(self):
        menu = """\n
        ================ MENU ================
        [lo]\tFazer login
        [nu]\tNovo usuário
        [nc]\tNova conta

        [lu]\tLista usuário
        [lc]\tLista contas

        [q]\tSair
        => """
        return input(textwrap.dedent(menu))    
    def menulogin(self):
        menu = """\n
        ================ MENU ================
        [d]\tDepositar
        [s]\tSacar
        [e]\tExtrato

        [q]\tSair
        => """
        return input(textwrap.dedent(menu))
##############################################################################################################################################################################
grupo1 = Pessoas()
grupo1.Adicionar(Pessoa(cpf=0, nome='Nome 0', data_nascimento='01/01/1990', endereco='end1'))
grupo1.Adicionar(Pessoa(cpf=1, nome='Nome 1', data_nascimento='01/01/1990', endereco='end1'))
grupo1.Adicionar(Cliente(cpf=2, nome='Nome 2', data_nascimento='01/01/1990', endereco='end1'))
grupo1.Adicionar(Cliente(cpf=3, nome='Nome 3', data_nascimento='01/01/1990', endereco='end1'))
grupo1.Adicionar(Pessoa(cpf=4, nome='Nome 4', data_nascimento='01/01/1990', endereco='end1'))
grupo1.Adicionar(Cliente(cpf=5, nome='Nome 5', data_nascimento='01/01/1990', endereco='end1'))
conta1 = grupo1.clientes[3].Criar_conta(senha='abc')
conta2 = grupo1.clientes[2].Criar_conta(senha='abc')
grupo1.clientes[2].contas[1].depositar(200)
grupo1.clientes[2].contas[1].sacar(150)
conta2.depositar(100)
grupo1.clientes[2].contas[1].exibir_extrato()
# print(f'contas[0].saldo: {Contas[0].saldo}')
print(f'contas[0].saldo: {Contas.Index(0).saldo}') # Porque não poderia ser: "Contas[0].saldo" ?
print(f'contas[1].saldo: {Contas.Index(1).saldo}')
interface = Interface(joao)
