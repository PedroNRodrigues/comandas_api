from infra import database
from sqlalchemy import Column, VARCHAR, Integer, DECIMAL, LargeBinary

# ORM
class ProdutoDB(database.Base):
    __tablename__ = 'tb_produto'

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    nome = Column(VARCHAR(100), nullable=False, index=True)
    descricao = Column(VARCHAR(200), nullable=False)
    foto = Column(LargeBinary, nullable=False)
    valor_unitario = Column(DECIMAL(11, 2), nullable=False)

    def __init__(self, id, nome, descricao, foto, valor_unitario):
        self.id = id
        self.nome = nome
        self.descricao = descricao
        self.foto = foto
        self.valor_unitario = valor_unitario