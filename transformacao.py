"""
MÓDULO DE TRANSFORMAÇÃO DE DADOS
==================================
Responsável por limpar, normalizar e transformar os dados de PCD brutos
em informações estruturadas e prontas para análise.

Classes:
    - TransformerPCD: Transforma dados brutos em dados limpos
"""

import pandas as pd
import numpy as np
import logging
from typing import Tuple, Dict

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TransformerPCD:
    """
    Classe para transformação e limpeza de dados de Pessoas Com Deficiência.
    
    Responsabilidades:
    - Validar dados
    - Limpar valores ausentes
    - Normalizar colunas
    - Calcular métricas
    - Enriquecer dados com informações derivadas
    
    Exemplo de uso:
        transformer = TransformerPCD()
        df_limpo = transformer.transformar(df_bruto)
    """
    
    def __init__(self):
        """Inicializar o transformador."""
        logger.info("TransformerPCD inicializado")
    
    def transformar(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aplicar todas as transformações no DataFrame.
        
        Args:
            df (pd.DataFrame): DataFrame bruto da extração
            
        Returns:
            pd.DataFrame: DataFrame transformado e limpo
        """
        
        logger.info("="*70)
        logger.info("INICIANDO TRANSFORMAÇÃO DE DADOS")
        logger.info("="*70)
        
        # Copiar DataFrame para não modificar o original
        df_transformado = df.copy()
        
        # Aplicar transformações
        df_transformado = self._validar_dados(df_transformado)
        df_transformado = self._limpar_valores_ausentes(df_transformado)
        df_transformado = self._normalizar_colunas(df_transformado)
        df_transformado = self._calcular_metricas(df_transformado)
        df_transformado = self._enriquecer_dados(df_transformado)
        
        logger.info("="*70)
        logger.info("✓ TRANSFORMAÇÃO CONCLUÍDA")
        logger.info("="*70)
        
        return df_transformado
    
    def _validar_dados(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Validar dados e verificar integridade.
        
        Args:
            df (pd.DataFrame): DataFrame a validar
            
        Returns:
            pd.DataFrame: DataFrame validado
        """
        
        logger.info("▶ Validando dados...")
        
        # Verificar se tem dados
        if len(df) == 0:
            raise ValueError("DataFrame vazio! Nenhum dado foi extraído.")
        
        # Verificar colunas obrigatórias
        colunas_obrigatorias = [
            'estado_sigla', 'estado_nome', 'regiao',
            'total_municipios', 'pessoas_com_deficiencia_aprox'
        ]
        
        colunas_faltantes = [col for col in colunas_obrigatorias if col not in df.columns]
        
        if colunas_faltantes:
            colunas_presentes = list(df.columns)
            mensagem = f"Colunas obrigatórias não encontradas: {colunas_faltantes}\n"
            mensagem += f"Colunas disponíveis: {colunas_presentes}\n"
            mensagem += f"Forma do DataFrame: {df.shape}"
            logger.error(mensagem)
            raise ValueError(mensagem)
        
        logger.info(f"  ✓ Validação OK ({len(df)} registros, {len(df.columns)} colunas)")
        
        return df
    
    def _limpar_valores_ausentes(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Lidar com valores ausentes/nulos.
        
        Args:
            df (pd.DataFrame): DataFrame com possíveis valores nulos
            
        Returns:
            pd.DataFrame: DataFrame sem valores nulos
        """
        
        logger.info("▶ Limpando valores ausentes...")
        
        # Verificar valores NaN
        nulos_antes = df.isnull().sum().sum()
        
        # Remover linhas com valores nulos
        df = df.dropna()
        
        nulos_depois = df.isnull().sum().sum()
        
        logger.info(f"  ✓ Removidos {nulos_antes - nulos_depois} valores nulos")
        
        return df
    
    def _normalizar_colunas(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalizar nomes e tipos de colunas.
        
        Args:
            df (pd.DataFrame): DataFrame com colunas a normalizar
            
        Returns:
            pd.DataFrame: DataFrame com colunas normalizadas
        """
        
        logger.info("▶ Normalizando colunas...")
        
        # Renomear colunas para padrão (lowercase com underscore)
        df.columns = df.columns.str.lower().str.replace(' ', '_')
        
        # Garantir tipos de dados corretos
        tipos_esperados = {
            'estado_sigla': 'object',
            'estado_nome': 'object',
            'regiao': 'object',
            'total_municipios': 'int64',
            'pessoas_com_deficiencia_aprox': 'float64',
            'estabelecimentos_saude_aprox': 'float64',
        }
        
        for coluna, tipo in tipos_esperados.items():
            if coluna in df.columns:
                try:
                    if tipo == 'int64':
                        df[coluna] = df[coluna].astype(tipo)
                    elif tipo == 'float64':
                        df[coluna] = pd.to_numeric(df[coluna], errors='coerce')
                except Exception as e:
                    logger.warning(f"  ⚠ Não foi possível converter {coluna}: {e}")
        
        logger.info(f"  ✓ {len(df.columns)} colunas normalizadas")
        
        return df
    
    def _calcular_metricas(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcular métricas derivadas.
        
        Args:
            df (pd.DataFrame): DataFrame para calcular métricas
            
        Returns:
            pd.DataFrame: DataFrame com novas métricas
        """
        
        logger.info("▶ Calculando métricas...")
        
        # PCD por município
        df['pcd_por_municipio'] = (
            df['pessoas_com_deficiencia_aprox'] / df['total_municipios']
        ).round(2)
        
        # Estabelecimentos de saúde por PCD
        df['saude_por_pcd'] = (
            df['estabelecimentos_saude_aprox'] / df['pessoas_com_deficiencia_aprox']
        ).round(4)
        
        # Percentual de concentração (em relação ao total nacional)
        total_nacional = df['pessoas_com_deficiencia_aprox'].sum()
        df['pct_pcd_nacional'] = (
            (df['pessoas_com_deficiencia_aprox'] / total_nacional) * 100
        ).round(2)
        
        logger.info("  ✓ 3 novas métricas calculadas")
        
        return df
    
    def _enriquecer_dados(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Enriquecer dados com informações adicionais.
        
        Args:
            df (pd.DataFrame): DataFrame para enriquecer
            
        Returns:
            pd.DataFrame: DataFrame enriquecido
        """
        
        logger.info("▶ Enriquecendo dados...")
        
        # Adicionar data de processamento
        df['data_processamento'] = pd.Timestamp.now()
        
        # Status de saúde: razão de estabelecimentos por pessoa
        df['status_saude'] = df['saude_por_pcd'].apply(
            lambda x: 'Crítico' if x < 0.0001 else 'Baixo' if x < 0.0005 else 'Normal'
        )
        
        logger.info("  ✓ Dados enriquecidos com status e timestamp")
        
        return df
    
    def gerar_resumo(self, df: pd.DataFrame) -> Dict:
        """
        Gerar resumo estatístico dos dados.
        
        Args:
            df (pd.DataFrame): DataFrame para resumir
            
        Returns:
            Dict: Dicionário com estatísticas
        """
        
        resumo = {
            'total_estados': len(df),
            'total_municipios': int(df['total_municipios'].sum()),
            'total_pcd_estimado': float(df['pessoas_com_deficiencia_aprox'].sum()),
            'total_estabelecimentos': float(df['estabelecimentos_saude_aprox'].sum()),
            'regiao_com_mais_pcd': df.groupby('regiao')['pessoas_com_deficiencia_aprox'].sum().idxmax(),
            'estado_com_mais_pcd': df.loc[df['pessoas_com_deficiencia_aprox'].idxmax(), 'estado_nome'],
            'data_processamento': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        
        return resumo



