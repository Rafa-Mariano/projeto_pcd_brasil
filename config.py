"""
ARQUIVO DE CONFIGURAÇÕES
=========================
Centraliza variáveis de ambiente e configurações do projeto.

Use .env para definir valores customizados:
    DB_HOST=localhost
    DB_PORT=5432
    DB_USER=postgres
    DB_PASSWORD=sua_senha
    DB_NAME=pcd_database
"""

import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env com encoding UTF-8
load_dotenv(encoding='utf-8')

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÕES DO BANCO DE DADOS
# ═══════════════════════════════════════════════════════════════════════════

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', 5432))
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')
DB_NAME = os.getenv('DB_NAME', 'pcd_database')

# String de conexão completa
DATABASE_URL = (
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÕES DA API
# ═══════════════════════════════════════════════════════════════════════════

API_BASE_URL = "https://servicodados.ibge.gov.br/api/v1/localidades"
API_TIMEOUT = int(os.getenv('API_TIMEOUT', 10))

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÕES DE LOGGING
# ═══════════════════════════════════════════════════════════════════════════

LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÕES DE DADOS
# ═══════════════════════════════════════════════════════════════════════════

TABELA_SAUDE = 'pessoas_com_deficiencia'
CHUNK_SIZE = 1000  # Tamanho dos chunks para carregamento

# Percentual de deficiência (estimativa)
TAXA_DEFICIENCIA = 0.08

# Estabelecimentos por município (estimativa)
ESTABELECIMENTOS_POR_MUNICIPIO = 2

# ═══════════════════════════════════════════════════════════════════════════
# VALIDAÇÃO DE CONFIGURAÇÕES
# ═══════════════════════════════════════════════════════════════════════════

def validar_configuracoes():
    """
    Validar se configurações estão corretas.
    
    Raises:
        ValueError: Se alguma configuração for inválida
    """
    
    if not DB_HOST:
        raise ValueError("DB_HOST não configurado")
    
    if not DB_USER:
        raise ValueError("DB_USER não configurado")
    
    if TAXA_DEFICIENCIA < 0 or TAXA_DEFICIENCIA > 1:
        raise ValueError("TAXA_DEFICIENCIA deve estar entre 0 e 1")
    
    print("✓ Configurações validadas")


# Validar ao importar
if __name__ != "__main__":
    try:
        validar_configuracoes()
    except Exception as e:
        print(f"⚠️ Aviso de configuração: {e}")
