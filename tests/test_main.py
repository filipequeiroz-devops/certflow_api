from main               import get_db, home, register, app
from fastapi.testclient import TestClient
from pydantic           import ValidationError
from sqlalchemy         import create_engine
from sqlalchemy.pool    import StaticPool
from sqlalchemy.orm     import sessionmaker
from database           import Base
import pytest

#Banco sql lite em memória para realização dos testes
SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine
)

#==================
#sessões de DB que serao utilizadas nos testes
#==================
@pytest.fixture(scope="function") #escopo padrão, será executado do início ao fim de cada teste unitário
def db_session():
    """Cria um banco de dados limpo para cada teste e o descarta ao final."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function") #Mesma coisa
def client(db_session):
    """
    Sobrescreve a dependência get_db da FastAPI para usar o banco de testes.
    Retorna o cliente de testes da API.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

def test_home(client):
    """Testa se o endpoint raiz da API está respondendo corretamente."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "CertFlow API online"}
 
def test_register_success(client):
    """Testa o registro de um novo usuário com sucesso."""
    payload = {
        "nome"        : "João Silva",
        "email"       : "joao.silva@example.com",
        "senha"       : "senha123",    
        "device_id"   : "device123",
        "nome_maquina": "maquina123",
        "sistema"     : "Windows"
    }
    response = client.post("/register", json=payload)
    
    assert response.status_code == 200