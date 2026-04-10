"""
MÓDULO DE CARREGAMENTO DE DADOS
================================
Responsável por carregar dados transformados em um banco de dados PostgreSQL.

Classes:
    - LoaderPCD: Carrega dados no PostgreSQL
"""

import pandas as pd
import logging
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from typing import Dict, Optional
import os
from urllib.parse import quote_plus
import psycopg2
from io import StringIO
from dotenv import load_dotenv

# Carregar .env
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LoaderPCD:
    """
    Carregador de dados para PostgreSQL.
    
    Responsabilidades:
    - Conectar ao banco de dados
    - Criar tabelas
    - Inserir dados
    - Validar carregamento
    
    Exemplo de uso:
        loader = LoaderPCD(user='postgres', password='senha', database='pcd_db')
        loader.carregar(df_transformado)
    """
    
    def __init__(self, database_url: str = None):
        """
        Inicializar conexão com PostgreSQL.
        
        Args:
            database_url (str): URL de conexão do banco
                Exempla: postgresql://user:password@localhost:5432/pcd_database
                Se não informado, lê do .env (DATABASE_URL ou monta a partir de DB_*)
        """
        
        # Se não informar URL, ler do .env
        if database_url is None:
            # Tentar pegar DATABASE_URL pronto
            database_url = os.getenv("DATABASE_URL")
            
            # Se não tiver, montar a partir das variáveis individuais
            if not database_url:
                host = os.getenv('DB_HOST', 'localhost')
                port = os.getenv('DB_PORT', '5432')
                user = os.getenv('DB_USER', 'postgres')
                password = os.getenv('DB_PASSWORD', 'postgres')
                database = os.getenv('DB_NAME', 'pcd_database')
                
                # Usar URL encoding apenas se necessário
                password_safe = quote_plus(password) if password else ''
                database_url = f"postgresql://{user}:{password_safe}@{host}:{port}/{database}"
        
        self.database_url = database_url
        self.engine = None
        
        try:
            # Criar engine SQLAlchemy (para compatibilidade com to_sql)
            self.engine = create_engine(self.database_url)
            logger.info(f"✓ Conexão com PostgreSQL estabelecida")
            logger.info(f"  Database: pcd_database")
        except Exception as e:
            logger.error(f"✗ Erro ao conectar ao PostgreSQL: {e}")
            raise
    
    def carregar(
        self,
        df: pd.DataFrame,
        nome_tabela: str = 'pessoas_com_deficiencia',
        se_existe: str = 'replace'
    ) -> bool:
        """
        Carregar DataFrame no PostgreSQL.
        
        Args:
            df (pd.DataFrame): DataFrame a carregar
            nome_tabela (str): Nome da tabela no banco
            se_existe (str): Estratégia se tabela existe
                - 'fail': Gerar erro
                - 'replace': Substituir tabela
                - 'append': Adicionar dados
                
        Returns:
            bool: True se carregamento bem-sucedido
        """
        
        logger.info("="*70)
        logger.info(f"INICIANDO CARREGAMENTO NO POSTGRESQL")
        logger.info("="*70)
        
        try:
            # Validar dados antes de carregar
            self._validar_dados(df)
            
            logger.info(f"▶ Carregando dados para tabela '{nome_tabela}'...")
            
            # Usar psycopg2 diretamente (como no setup_db.py que funciona)
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()
            
            # Dropar tabela se existente e if_exists='replace'
            if se_existe == 'replace':
                try:
                    cursor.execute(f"DROP TABLE IF EXISTS {nome_tabela}")
                    conn.commit()
                    logger.info(f"  Tabela '{nome_tabela}' recriada")
                except Exception as e:
                    logger.warning(f"  Não foi possível dropar tabela: {e}")
                    conn.rollback()
            
            # Criar tabela com tipos adequados
            sql_create = self._gerar_sql_create_table(df, nome_tabela)
            cursor.execute(sql_create)
            conn.commit()
            
            # Inserir dados linha por linha (seguro com encoding)
            for idx, row in df.iterrows():
                valores = tuple(row)
                placeholders = ','.join(['%s'] * len(row))
                sql_insert = f"INSERT INTO {nome_tabela} ({','.join([f'\"{col}\"' for col in df.columns])}) VALUES ({placeholders})"
                
                cursor.execute(sql_insert, valores)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"✓ Carregamento concluído!")
            logger.info(f"  Tabela: {nome_tabela}")
            logger.info(f"  Linhas carregadas: {len(df)}")
            logger.info(f"  Colunas: {len(df.columns)}")
            
            # Validar carregamento
            self._validar_carregamento(nome_tabela, len(df))
            
            return True
            
        except Exception as e:
            logger.error(f"✗ Erro durante carregamento: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _gerar_sql_create_table(self, df: pd.DataFrame, nome_tabela: str) -> str:
        """
        Gerar SQL para criar tabela baseado no DataFrame.
        
        Args:
            df (pd.DataFrame): DataFrame para inspecionar tipos
            nome_tabela (str): Nome da tabela
            
        Returns:
            str: SQL CREATE TABLE
        """
        colunas = []
        for col, dtype in zip(df.columns, df.dtypes):
            if 'int' in str(dtype):
                sql_type = 'INTEGER'
            elif 'float' in str(dtype):
                sql_type = 'FLOAT'
            else:
                sql_type = 'VARCHAR(500)'
            
            colunas.append(f'"{col}" {sql_type}')
        
        return f"CREATE TABLE IF NOT EXISTS {nome_tabela} ({','.join(colunas)})"
    
    def _validar_dados(self, df: pd.DataFrame) -> None:
        """
        Validar integridade dos dados antes de carregar.
        
        Args:
            df (pd.DataFrame): DataFrame a validar
            
        Raises:
            ValueError: Se dados inválidos
        """
        
        logger.info("▶ Validando dados...")
        
        # Verificar DataFrame não vazio
        if len(df) == 0:
            raise ValueError("DataFrame vazio!")
        
        # Verificar colunas obrigatórias
        colunas_obrigatorias = [
            'estado_sigla', 'estado_nome', 'regiao',
            'total_municipios', 'pessoas_com_deficiencia_aprox'
        ]
        
        for coluna in colunas_obrigatorias:
            if coluna not in df.columns:
                raise ValueError(f"Coluna obrigatória não encontrada: {coluna}")
        
        # Verificar valores nulos
        if df.isnull().any().any():
            nulos = df.isnull().sum().sum()
            logger.warning(f"  ⚠ {nulos} valores nulos encontrados")
        
        logger.info(f"  ✓ Validação OK ({len(df)} registros)")
    
    def _validar_carregamento(self, nome_tabela: str, linhas_esperadas: int) -> None:
        """
        Validar se dados foram carregados corretamente.
        
        Args:
            nome_tabela (str): Nome da tabela
            linhas_esperadas (int): Número esperado de linhas
            
        Raises:
            ValueError: Se validação falhar
        """
        
        logger.info("▶ Validando carregamento...")
        
        try:
            with self.engine.connect() as connection:
                # Contar linhas na tabela
                query = text(f"SELECT COUNT(*) FROM {nome_tabela}")
                resultado = connection.execute(query)
                linhas_carregadas = resultado.scalar()
                
                if linhas_carregadas != linhas_esperadas:
                    logger.warning(
                        f"  ⚠ Discrepância: esperadas {linhas_esperadas}, "
                        f"carregadas {linhas_carregadas}"
                    )
                else:
                    logger.info(f"  ✓ {linhas_carregadas} linhas confirmadas no BD")
                    
        except Exception as e:
            logger.error(f"  ✗ Erro na validação: {e}")
    
    def listar_tabelas(self) -> list:
        """
        Listar tabelas do banco de dados.
        
        Returns:
            list: List de nomes de tabelas
        """
        
        inspector = inspect(self.engine)
        tabelas = inspector.get_table_names()
        logger.info(f"Tabelas no banco: {tabelas}")
        return tabelas
    
    def consultar_tabela(
        self,
        nome_tabela: str = 'pessoas_com_deficiencia',
        limite: int = None
    ) -> pd.DataFrame:
        """
        Consultar dados da tabela.
        
        Args:
            nome_tabela (str): Nome da tabela
            limite (int): Número de linhas a retornar (None = todas)
            
        Returns:
            pd.DataFrame: Dados da tabela
        """
        
        if limite:
            logger.info(f"Consultando {limite} linhas de '{nome_tabela}'...")
            query = f"SELECT * FROM {nome_tabela} LIMIT {limite}"
        else:
            logger.info(f"Consultando todos os dados de '{nome_tabela}'...")
            query = f"SELECT * FROM {nome_tabela}"
        
        df = pd.read_sql_query(query, self.engine)
        
        logger.info(f"✓ {len(df)} linhas recuperadas")
        
        return df
    
    def deletar_tabela(self, nome_tabela: str) -> bool:
        """
        Deletar tabela do banco de dados.
        
        Args:
            nome_tabela (str): Nome da tabela
            
        Returns:
            bool: True se deletada com sucesso
        """
        
        logger.warning(f"⚠ Deletando tabela '{nome_tabela}'...")
        
        try:
            with self.engine.connect() as connection:
                connection.execute(text(f"DROP TABLE IF EXISTS {nome_tabela}"))
                connection.commit()
            logger.info(f"✓ Tabela deletada")
            return True
        except Exception as e:
            logger.error(f"✗ Erro ao deletar tabela: {e}")
            return False
    
    def fechar_conexao(self) -> None:
        """Fechar conexão com banco de dados."""
        self.engine.dispose()
        logger.info("✓ Conexão fechada")
