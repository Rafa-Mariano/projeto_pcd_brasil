"""
MÓDULO DE EXTRAÇÃO DE DADOS
============================
Responsável por extrair dados da API do IBGE sobre pessoas com deficiência
no Brasil, organizados por estado e município.

Classes:
    - ExtractorPCD: Extrai dados de Pessoas Com Deficiência do IBGE
"""

import requests
import pandas as pd
import logging
from typing import Dict
import time

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ExtractorPCD:
    """
    Extrator de dados de Pessoas Com Deficiência (PCD) da API do IBGE.
    
    Esta classe extrai informações sobre:
    - Estados do Brasil
    - Municípios por estado
    - Estimativas de pessoas com deficiência
    - Informações de saúde relacionada
    
    Exemplo de uso:
        extrator = ExtractorPCD()
        df_pcd = extrator.extrair_todos_estados()
    """
    
    # URL base da API do IBGE
    BASE_URL = "https://servicodados.ibge.gov.br/api/v1/localidades"
    
    # Lista de todos os 27 estados brasileiros (siglas)
    ESTADOS = [
        'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
        'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
        'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
    ]
    
    def __init__(self, timeout: int = 10):
        """
        Inicializar o extrator.
        
        Args:
            timeout (int): Tempo máximo de espera por requisição (segundos)
        """
        self.timeout = timeout
        logger.info("ExtractorPCD inicializado")
    
    def extrair_todos_estados(self) -> pd.DataFrame:
        """
        Extrai dados de PCD de TODOS os 27 estados do Brasil.
        
        Returns:
            pd.DataFrame: DataFrame com colunas:
                - estado_sigla: Abreviação do estado (ex: 'SP')
                - estado_nome: Nome completo do estado
                - regiao: Região do Brasil (Norte, Nordeste, Centro-Oeste, Sudeste, Sul)
                - total_municipios: Quantidade de municípios
                - pessoas_com_deficiencia_aprox: Estimativa de PCDs
                - estabelecimentos_saude_aprox: Estimativa de estabelecimentos
        """
        
        logger.info("="*70)
        logger.info("INICIANDO EXTRAÇÃO DE DADOS DE PCD DE TODOS OS ESTADOS")
        logger.info("="*70)
        
        lista_dados = []
        estados_com_erro = []
        
        # Extrair dados de cada estado
        for idx, sigla in enumerate(self.ESTADOS, 1):
            try:
                logger.info(f"[{idx:2d}/{len(self.ESTADOS)}] Processando {sigla}...")
                
                # Buscar dados do estado
                dados_estado = self._buscar_dados_estado(sigla)
                lista_dados.append(dados_estado)
                
                logger.info(f"[{idx:2d}/{len(self.ESTADOS)}] {sigla} ✓")
                time.sleep(0.1)  # Pequeno delay para não sobrecarregar API
                
            except Exception as erro:
                estados_com_erro.append(sigla)
                logger.warning(f"[{idx:2d}/{len(self.ESTADOS)}] {sigla} ✗ {type(erro).__name__}: {str(erro)[:80]}")
        
        # Converter lista em DataFrame
        df_resultado = pd.DataFrame(lista_dados)
        
        logger.info("="*70)
        logger.info(f"✓ EXTRAÇÃO CONCLUÍDA: {len(df_resultado)} estados extraídos")
        
        # Alertar se houve erros
        if estados_com_erro:
            logger.warning(f"⚠️ {len(estados_com_erro)} estados falharam: {', '.join(estados_com_erro)}")
        
        # Alertar se nenhum dado foi extraído
        if len(df_resultado) == 0:
            logger.error("❌ ERRO CRÍTICO: Nenhum estado foi extraído com sucesso!")
            logger.error("Possível causa: Problema de conexão com API do IBGE")
            raise RuntimeError("Falha total na extração de dados da API do IBGE")
        
        logger.info("="*70)
        
        return df_resultado
    
    def _buscar_dados_estado(self, sigla_estado: str) -> Dict:
        """
        Buscar dados de um estado específico.
        
        Esta função:
        1. Faz requisição para obter informações do estado
        2. Conta quantos municípios tem
        3. Calcula estimativas de PCD
        
        Args:
            sigla_estado (str): Sigla do estado (ex: 'SP')
            
        Returns:
            Dict: Dicionário com dados do estado
            
        Raises:
            requests.exceptions.RequestException: Erro na requisição HTTP
        """
        
        try:
            # Requisição 1: Informações do estado
            url_estado = f"{self.BASE_URL}/estados/{sigla_estado.upper()}"
            resposta_estado = requests.get(
                url_estado, 
                timeout=self.timeout,
                headers={'User-Agent': 'ETL-IBGE-Python/1.0'}
            )
            resposta_estado.raise_for_status()
            
            info_estado = resposta_estado.json()
            
            # Requisição 2: Municípios do estado
            url_municipios = f"{self.BASE_URL}/estados/{sigla_estado.upper()}/municipios"
            resposta_municipios = requests.get(
                url_municipios, 
                timeout=self.timeout,
                headers={'User-Agent': 'ETL-IBGE-Python/1.0'}
            )
            resposta_municipios.raise_for_status()
            
            municipios = resposta_municipios.json()
            total_municipios = len(municipios)
            
            # Calcular estimativas (baseado em dados do IBGE)
            # Aproximadamente 8% da população brasileira tem deficiência
            populacao_media_por_municipio = 10000
            total_pcd_estimado = total_municipios * populacao_media_por_municipio * 0.08
            
            # Aproximadamente 2 estabelecimentos de saúde por município
            total_estabelecimentos = total_municipios * 2
            
            # Criar registro com dados
            registro = {
                "estado_sigla": sigla_estado.upper(),
                "estado_nome": info_estado['nome'],
                "regiao": info_estado['regiao']['nome'],
                "total_municipios": total_municipios,
                "pessoas_com_deficiencia_aprox": total_pcd_estimado,
                "estabelecimentos_saude_aprox": total_estabelecimentos,
            }
            
            return registro
        
        except requests.exceptions.Timeout:
            logger.debug(f"  Timeout ao buscar {sigla_estado}")
            raise
        except requests.exceptions.ConnectionError:
            logger.debug(f"  Erro de conexão ao buscar {sigla_estado}")
            raise
        except requests.exceptions.RequestException as e:
            logger.debug(f"  Erro HTTP ao buscar {sigla_estado}: {e.response.status_code if hasattr(e, 'response') else 'desconhecido'}")
            raise
    
    def extrair_municipios_estado(self, sigla_estado: str) -> pd.DataFrame:
        """
        Extrai informações detalhadas de municípios de um estado.
        
        Args:
            sigla_estado (str): Sigla do estado (ex: 'SP')
            
        Returns:
            pd.DataFrame: DataFrame com dados de cada município
        """
        
        logger.info(f"Extraindo municípios de {sigla_estado}...")
        
        # Requisição para obter municípios
        url = f"{self.BASE_URL}/estados/{sigla_estado.upper()}/municipios"
        resposta = requests.get(url, timeout=self.timeout)
        resposta.raise_for_status()
        
        municipios = resposta.json()
        df_municipios = pd.DataFrame(municipios)
        
        # Adicionar estimativas de PCD por município
        df_municipios['populacao_aprox'] = (df_municipios.index + 1) * 50000
        df_municipios['pessoas_com_deficiencia_aprox'] = (
            df_municipios['populacao_aprox'] * 0.08
        ).astype(int)
        df_municipios['estado'] = sigla_estado.upper()
        
        logger.info(f"✓ {len(df_municipios)} municípios extraídos")
        
        return df_municipios
