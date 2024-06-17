import datetime
from decimal import Decimal
import sqlite3
from sqlite3 import Connection, Cursor
from pathlib import Path
from typing import Generic, TypeVar, Dict, Iterator
from db import criar_db, criar_conexao
from abc import ABC

def criar_conexao() -> Connection:
    ROOT_PATH = Path(__file__).parent
    return sqlite3.connect(ROOT_PATH / "sql.sqlite")

def criar_db(cursor: Cursor):
    cursor.executescript(
        """
        CREATE TABLE IF NOT EXISTS address (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            street VARCHAR(50) NOT NULL,
            number VARCHAR(8) NOT NULL,
            neighborhood VARCHAR(50) NOT NULL,
            city VARCHAR(50) NOT NULL,
            uf VARCHAR(2) NOT NULL,
            country VARCHAR(50) NOT NULL,
            zip_code VARCHAR(20) NOT NULL
        );

        CREATE TABLE IF NOT EXISTS contact (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(50) NOT NULL,
            email VARCHAR(50) NOT NULL UNIQUE,
            phone VARCHAR(30) NOT NULL,
            date_of_birth DATE NOT NULL,
            cpf VARCHAR(15) NOT NULL UNIQUE,
            address_id INTEGER NOT NULL,
            FOREIGN KEY (address_id) REFERENCES address(id)
        );

        CREATE TABLE IF NOT EXISTS client (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(20) NOT NULL UNIQUE,
            password VARCHAR(20) NOT NULL,
            balance DECIMAL(10, 2) DEFAULT 0.00,
            type INTEGER NOT NULL DEFAULT 0, 
            contact_id INTEGER NOT NULL,
            FOREIGN KEY (contact_id) REFERENCES address(id)
        );

        CREATE TABLE IF NOT EXISTS operation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            datetime DATETIME NOT NULL,
            value DECIMAL(10, 2) NOT NULL,
            type INTEGER NOT NULL,
            client_id INTEGER NOT NULL,
            destination_id INTEGER,
            FOREIGN KEY (client_id) REFERENCES client(id),
            FOREIGN KEY (destination_id) REFERENCES client(id)
        );
        """
    )

conexao = criar_conexao()
cursor = conexao.cursor()
cursor.row_factory = sqlite3.Row
criar_db(cursor)
conexao.commit()

def execute_commit(query: str, params: tuple):
    cursor.execute(query, params)
    conexao.commit()
    return cursor.lastrowid

T = TypeVar('T')
class GList(Generic[T]):
    def __init__(self):
        self.registros: Dict[int, T] = {} 
    def __setitem__(self, id: int, item: T):
        self.registros[id] = item
    def __getitem__(self, id: int) -> T:
        return self.registros[id]
    def __iter__(self) -> Iterator[T]:
        return iter(self.registros.values())
    
class Cache:
    addresses: Dict[int, 'Address'] = {}
    contacts: Dict[int, 'Contact'] = {}
    clients: Dict[int, 'Client'] = {}
    operations: Dict[int, 'Operation'] = {}
    
class Address: # 8 atts e 1 lista
    def __new__(cls, street: str, number: int, neighborhood: str, city: str, uf: str, country: str, zip_code: str, recovery=False):
        dados_address = cursor.execute("""SELECT id FROM address WHERE street = ? AND number = ? AND neighborhood = ? AND city = ? AND
            uf = ? AND country = ? AND zip_code = ?""", (street, number, neighborhood, city, uf, country, zip_code)).fetchone()
        if dados_address and dados_address["id"] in Cache.addresses: return Cache.addresses[dados_address["id"]]
        return super().__new__(cls)
    def __init__(self, street: str, number: int, neighborhood: str, city: str, uf: str, country: str, zip_code: str, recovery = False):
        if hasattr(self, "id"): return
        self.contacts = GList[Contact]()
        dados_address = cursor.execute("""SELECT id FROM address WHERE street = ? AND number = ? AND neighborhood = ? AND city = ? AND
            uf = ? AND country = ? AND zip_code = ?""", (street, number, neighborhood, city, uf, country, zip_code,)).fetchone()
        if dados_address is None: self.id = execute_commit("""INSERT INTO address (street, number, neighborhood, city, uf, country, zip_code) 
                VALUES (?, ?, ?, ?, ?, ?, ?)""", (street, number, neighborhood, city, uf, country, zip_code,))
        else: self.id = dados_address["id"]
        self.street, self.number, self.neighborhood, self.city, self.country = street, number, neighborhood, city, country
        self.uf, self.zip_code = uf, zip_code
        Cache.addresses[self.id] = self
        if recovery: self.recover_contacts()
    def recover_contacts(self):
        contacts = cursor.execute("SELECT id FROM contact WHERE address_id = ?", (self.id,)).fetchall()
        for contact in contacts:
            self.contacts[contact["id"]] = Contact.from_id(contact["id"])
    @staticmethod
    def from_id(id: int, recovery=True):
        if id in Cache.addresses: return Cache.addresses[id]
        dados_address = cursor.execute("SELECT * FROM address WHERE id = ? ", (id,)).fetchone()
        return Address(dados_address["street"],dados_address["number"],dados_address["neighborhood"],dados_address["city"],
            dados_address["uf"],dados_address["country"],dados_address["zip_code"], recovery)
    
class Contact: # 6 atts, 1 lista e 1 referencia
    def __new__(cls, name: str, email: str, phone: str, date_of_birth: datetime, cpf: str, address: Address, recovery = False):
        dados_contact = cursor.execute("SELECT id FROM contact WHERE cpf = ?", (cpf,)).fetchone()
        if dados_contact and dados_contact["id"] in Cache.contacts: return Cache.contacts[dados_contact["id"]]
        return super().__new__(cls)
    def __init__(self, name: str, email: str, phone: str, date_of_birth: datetime, cpf: str, address: Address, recovery = False):
        if hasattr(self, "id"): return
        self.clients = GList[Client]()
        dados_contact = cursor.execute("SELECT * FROM contact WHERE cpf = ?", (cpf,)).fetchone()
        if dados_contact is None:
            self.id = execute_commit("""INSERT INTO contact (name, email, phone, date_of_birth, cpf, address_id) 
                VALUES (?, ?, ?, ?, ?, ?)""", (name, email, phone, date_of_birth, cpf, address.id))
            self.name, self.email, self.phone, self.date_of_birth = name, email, phone, date_of_birth
        else: 
            if self.name == dados_contact["name"] and self.email == dados_contact["email"] and self.phone == dados_contact["phone"]:
                if self.date_of_birth == dados_contact["date_of_birth"]:
                    self.name, self.email, self.phone, self.date_of_birth = name, email, phone, date_of_birth
                else: raise ValueError("Já existe um contato com esse cpf.")
            self.id = dados_contact["id"]
        self.cpf = cpf
        self.address = address
        address.contacts[self.id], Cache.contacts[self.id] = self, self
        if recovery: self.recover_clients()
    def recover_clients(self):
        clients = cursor.execute("SELECT id FROM client WHERE contact_id = ?", (self.id,)).fetchall()
        for client in clients:
            self.clients[client["id"]] = Client.from_id(client["id"])
    @staticmethod
    def from_id(id: int, recovery=True) -> 'Contact':
        if id in Cache.contacts: return Cache.contacts[id]
        dados_contact = cursor.execute("SELECT * FROM contact WHERE id = ?", (id,)).fetchone()
        address = Address.from_id(dados_contact["address_id"])
        return Contact(dados_contact["name"], dados_contact["email"], dados_contact["phone"], dados_contact["date_of_birth"], 
            dados_contact["cpf"], address, recovery)

class Client: # 5 atts, 1 lista e 1 referencia
    def __new__(cls, username: str, password: str, type: int, contact: Contact, recovery = False):
        dados_client = cursor.execute("SELECT id FROM client WHERE username = ?", (username,)).fetchone()
        if dados_client and dados_client["id"] in Cache.clients: return Cache.clients[dados_client["id"]]
        return super().__new__(cls)
    def __init__(self, username: str, password: str, type: int, contact: Contact, recovery = False):
        if hasattr(self, "id"): return
        self.operations = GList[Operation]()
        dados_client = cursor.execute("SELECT id, password, balance, type FROM client WHERE username = ?", (username,)).fetchone()
        if dados_client is None:
            self.id = execute_commit("INSERT INTO client (username, password, type, contact_id) VALUES (?, ?, ?, ?)",
                (username, password, type, contact.id,))
            self.balance, self.type = 0.0, type
        else:
            if dados_client["password"] != password: raise ValueError("Senha inválida.")
            self.id, self.balance, self.type = dados_client["id"], dados_client["balance"], dados_client["type"]
        self.username, self.password, self.contact = username, password, contact
        contact.clients[self.id], Cache.clients[self.id] = self, self
        if recovery: self.recover_operations()
    def recover_operations(self):
        operations = cursor.execute("SELECT id, value, type, destination_id FROM operation WHERE client_id = ?", (self.id,)).fetchall()
        for operation in operations:
            self.operations[operation["id"]] = Operation.from_id(operation["id"])
    def to_adm(self) -> 'Adm':
        if self.type == 1: return self
        else: raise TypeError("Usuário não tem permisão.")
    @staticmethod
    def from_id(id: int, recovery=True) -> 'Client':
        if id in Cache.clients: return Cache.clients[id]
        dados_client = cursor.execute("SELECT * FROM client WHERE id = ?", (id,)).fetchone()
        contact = Contact.from_id(dados_client["contact_id"])
        return Client(dados_client["username"], dados_client["password"], dados_client["type"], contact, recovery)

class Adm(Client):
    @property
    def register_contact(self): pass
    @property
    def register_client(self): pass

class Operation(ABC):
    def __init__(self, value: Decimal, client: Client, recovery_id: int = 0):
        if type(self) == Operation: raise TypeError("Objetos da classe Transaction não podem ser criados diretamente.")
        if value <= 0: raise ValueError("O valor da operação deve ser positivo.")
        if recovery_id == 0:
            self.date = datetime.datetime.now()
            self.value = value
        self.client = client
        if type(self) == Deposit: self.type = 0
        if type(self) == Withdraw: self.type = 1
        if type(self) == Transfer: self.type = 2
    @property
    def to_deposit(self) -> 'Deposit':
        if type(self) == Deposit: return self
        else: raise TypeError("A operação não é um deposito.")
    @property
    def to_withdraw(self) -> 'Withdraw':
        if type(self) == Withdraw: return self
        else: raise TypeError("A operação não é um deposito.")
    @property
    def to_transfer(self) -> 'Transfer':
        if type(self) == Transfer: return self
        else: raise TypeError("A operação não é um deposito.")
    @staticmethod
    def from_id(id: int) -> 'Operation':
        if id in Cache.operations: return Cache.operations[id]
        dados_operation = cursor.execute("SELECT * FROM operation WHERE id = ?", (id,)).fetchone()
        client = Client.from_id(dados_operation["client_id"])
        if dados_operation["type"] == 0: return Deposit(dados_operation["value"], client, dados_operation["id"])
        elif dados_operation["type"] == 1: return Withdraw(dados_operation["value"], client, dados_operation["id"])
        elif dados_operation["type"] == 2:
            destination = Client.from_id(dados_operation["destination_id"])
            return Transfer(dados_operation["value"], client, destination, dados_operation["id"])
        else: raise ValueError("Tipo de operação desconhecido.")

class Deposit(Operation): # 3 atts e 1 referencia
    def __init__(self, value: Decimal, client: Client, recovery_id: int = 0):
        super().__init__(value, client, recovery_id)
        if recovery_id == 0:
            self.id = execute_commit("INSERT INTO operation (datetime, value, type, client_id) VALUES (?, ?, ?, ?)", (self.date, value, self.type, client.id,))
            client.balance += value
            cursor.execute("UPDATE client SET balance = ? WHERE id = ?", (client.balance, client.id,))
            conexao.commit()
        else:
            dados = cursor.execute("SELECT datetime, value, client_id FROM operation where id = ?", (recovery_id,)).fetchone()
            if dados is None: raise ValueError("ID da operação não encontrado.")
            self.id, self.date, self.value = recovery_id, dados["datetime"], dados["value"]
        client.operations[self.id], Cache.operations[self.id] = self, self

class Withdraw(Operation): # 3 atts e 1 referencia
    def __init__(self, value: Decimal, client: Client, recovery_id: int = 0):
        super().__init__(value, client, recovery_id)
        if recovery_id == 0:
            if value <= client.balance:
                self.id = execute_commit("INSERT INTO operation (datetime, value, type, client_id) VALUES (?, ?, ?, ?)", (self.date, value, self.type, client.id,))
                client.balance -= value
                cursor.execute("UPDATE client SET balance = ? WHERE id = ?", (client.balance, client.id,))
                conexao.commit()
            else: raise ValueError("O valor do saque não pode exceder o saldo atual.")
        else:
            dados = cursor.execute("SELECT datetime, value, client_id FROM operation where id = ?", (recovery_id,)).fetchone()
            if dados is None: raise ValueError("ID da operação não encontrado.")
            self.id, self.date, self.value = recovery_id, dados["datetime"], dados["value"]
        client.operations[self.id], Cache.operations[self.id] = self, self

class Transfer(Operation): # 3 atts e 2 referencia
    def __init__(self, value: Decimal, client: Client, destination: Client, recovery_id: int = 0):
        super().__init__(value, client, recovery_id)
        if recovery_id == 0:
            if value <= client.balance:
                self.id = execute_commit("""INSERT INTO operation (datetime, value, type, client_id, destination_id)
                    VALUES (?, ?, ?, ?, ?)""", (self.date, value, self.type, client.id, destination.id,))
                client.balance -= value
                cursor.execute("UPDATE client SET balance = ? WHERE id = ?", (client.balance, client.id,))
                destination.balance += value
                cursor.execute("UPDATE client SET balance = ? WHERE id = ?", (destination.balance, destination.id,))
                conexao.commit()
            else: raise ValueError("O valor da transferência não pode exceder o saldo atual.")
        else:
            dados = cursor.execute("SELECT datetime, value, client_id, destination_id FROM operation where id = ?", (recovery_id,)).fetchone()
            if dados is None: raise ValueError("ID da operação não encontrado.")
            self.id, self.date, self.value = recovery_id, dados["datetime"], dados["value"]
        self.destination, destination.operations[self.id] = destination, self
        client.operations[self.id], Cache.operations[self.id] = self, self

# transferencia = Transfer.from_id(3).to_transfer

endereco1 = Address('rua', '1a', 'bairro1', 'cidade1', 'UF', 'pais', '19214-123')
endereco2 = Address('rua', '2a', 'bairro2', 'cidade2', 'UF', 'pais', '19214-123')
endereco3 = Address('rua', '3a', 'bairro3', 'cidade3', 'UF', 'pais', '19214-123')
contact1 = Contact('contact1', 'joao@email', 'numero_do_telefone', '07/11/1995', '0000001', endereco1)
contact2 = Contact('contact2', 'maria@email', 'outro_numero', '15/03/1987', '0000002', endereco1)
contact3 = Contact('contact3', 'pedro@email', 'outro_numero', '15/03/1987', '0000003', endereco2)
client1 = Client('client1', '111', 1, contact1, True)
client2 = Client('client2', '222', 0, contact2, True)
client3 = Client("client3", "333", 0, contact3, True)
deposito = Deposit(1000, client1)
saque = Withdraw(200, client1)
transf = Transfer(300, client1, client2)

conexao.close()
