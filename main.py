"""
MÓDULO PRINCIPAL - ORCHESTRAÇÃO E ANÁLISE
===========================================
Executa todo o pipeline ETL e cria visualizações interativas com Streamlit.

Este arquivo:
1. Orquestra extração, transformação e carregamento
2. Cria dashboard interativo com Streamlit
3. Gera relatórios e análises

Para executar:
    streamlit run main.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from extracao import ExtractorPCD
from transformacao import TransformerPCD
from carregamento import LoaderPCD
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO STREAMLIT
# ═══════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="ETL Pessoas com Deficiência - Brasil",
    page_icon="♿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .header-style {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 20px;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)



@st.cache_data
def executar_pipeline_etl():
    """
    Executar todo o pipeline ETL.
    
    Etapas:
    1. Extrair dados da API
    2. Transformar dados
    3. Carregar no PostgreSQL
    
    Returns:
        tuple: (df_transformado, resumo)
    """
    
    with st.spinner("Executando pipeline ETL..."):
        # ETAPA 1: EXTRAÇÃO
        st.info("Etapa 1: Extraindo dados da API do IBGE...")
        extrator = ExtractorPCD(timeout=30)  # Timeout aumentado
        df_bruto = extrator.extrair_todos_estados()
        
        if len(df_bruto) == 0:
            raise ValueError("Nenhum dado foi extraído da API IBGE. Verifique sua conexão.")
        
        st.success(f"{len(df_bruto)} estados extraídos com sucesso!")
        
        # ETAPA 2: TRANSFORMAÇÃO
        st.info("Etapa 2: Transformando dados...")
        transformer = TransformerPCD()
        df_transformado = transformer.transformar(df_bruto)
        resumo = transformer.gerar_resumo(df_transformado)
        st.success("Dados transformados")
        
    return df_transformado, resumo


def carregar_no_banco(df_transformado: pd.DataFrame):
    """
    Carregar dados no PostgreSQL.
    
    Args:
        df_transformado (pd.DataFrame): DataFrame transformado
    """
    try:
        st.info("📤 Etapa 3: Carregando no PostgreSQL...")
        loader = LoaderPCD()
        loader.carregar(df_transformado)
        st.success("Dados carregados no PostgreSQL com sucesso!")
        st.balloons()
    except Exception as e:
        st.error(f"Erro ao carregar no PostgreSQL: {str(e)}")
        import traceback
        with st.expander("Ver detalhes do erro"):
            st.code(traceback.format_exc())


def criar_graficos(df: pd.DataFrame):
    """
    Criar visualizações interativas.
    
    Args:
        df (pd.DataFrame): DataFrame transformado
    """
    
    # Gráfico 1: PCD por Estado (Top 10)
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏆 Top 10 Estados com Mais PCD")
        top_10 = df.nlargest(10, 'pessoas_com_deficiencia_aprox')
        
        fig1 = px.bar(
            top_10,
            x='estado_nome',
            y='pessoas_com_deficiencia_aprox',
            title='Pessoas com Deficiência por Estado',
            labels={
                'estado_nome': 'Estado',
                'pessoas_com_deficiencia_aprox': 'PCD (estimado)'
            },
            color='pessoas_com_deficiencia_aprox',
            color_continuous_scale='Blues',
            text_auto='.0f'
        )
        fig1.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig1, use_container_width=True)
    
    # Gráfico 2: Distribuição por Região
    with col2:
        st.subheader("📍 Distribuição por Região")
        por_regiao = df.groupby('regiao')['pessoas_com_deficiencia_aprox'].sum()
        
        fig2 = px.pie(
            values=por_regiao.values,
            names=por_regiao.index,
            title='PCD por Região do Brasil',
            hole=0.4
        )
        fig2.update_layout(height=400)
        st.plotly_chart(fig2, use_container_width=True)
    
    # Gráfico 3: Municípios vs PCD
    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("🏙️ Relação: Municípios vs PCD")
        fig3 = px.scatter(
            df,
            x='total_municipios',
            y='pessoas_com_deficiencia_aprox',
            hover_name='estado_nome',
            hover_data={'estado_sigla': True},
            title='Análise de Dispersão',
            labels={
                'total_municipios': 'Total de Municípios',
                'pessoas_com_deficiencia_aprox': 'PCD (estimado)'
            },
            size='total_municipios',
            color='regiao',
            height=400
        )
        st.plotly_chart(fig3, use_container_width=True)
    
    # Gráfico 4: Status de Saúde por Estado
    with col4:
        st.subheader("🏥 Status de Saúde")
        status_count = df['status_saude'].value_counts()
        
        fig4 = px.bar(
            x=status_count.index,
            y=status_count.values,
            title='Distribuição de Status de Saúde',
            labels={'x': 'Status', 'y': 'Quantidade de Estados'},
            color=status_count.index,
            color_discrete_map={
                'Crítico': '#ff0000',
                'Baixo': '#ffaa00',
                'Normal': '#00cc00'
            },
            text_auto=True
        )
        fig4.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig4, use_container_width=True)


def criar_tabelas_analise(df: pd.DataFrame, resumo: dict):
    """
    Criar tabelas e análises.
    
    Args:
        df (pd.DataFrame): DataFrame transformado
        resumo (dict): Resumo dos dados
    """
    
    # Métricas principais
    st.subheader("📊 Métricas Principais")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total de Estados",
            f"{resumo['total_estados']}"
        )
    
    with col2:
        st.metric(
            "Total de Municípios",
            f"{resumo['total_municipios']:,}"
        )
    
    with col3:
        st.metric(
            "PCD Estimado",
            f"{resumo['total_pcd_estimado']:,.0f}"
        )
    
    with col4:
        st.metric(
            "Estabelecimentos",
            f"{resumo['total_estabelecimentos']:,.0f}"
        )
    
    # Tabela de dados
    st.subheader("📋 Dados Completos")
    
    # Seletor de colunas
    colunas_disponiveis = st.multiselect(
        "Selecione as colunas a exibir:",
        options=df.columns.tolist(),
        default=['estado_sigla', 'estado_nome', 'regiao', 'pessoas_com_deficiencia_aprox']
    )
    
    # Tabela formatada
    df_exibicao = df[colunas_disponiveis].copy()
    
    # Formatar números
    for col in df_exibicao.columns:
        if df_exibicao[col].dtype in ['float64', 'int64']:
            df_exibicao[col] = df_exibicao[col].apply(
                lambda x: f"{x:,.2f}" if isinstance(x, float) else f"{x:,}"
            )
    
    st.dataframe(df_exibicao, use_container_width=True)
    
    # Download CSV
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 Baixar dados em CSV",
        data=csv,
        file_name="dados_pcd_brasil.csv",
        mime="text/csv"
    )


# ═══════════════════════════════════════════════════════════════════════════
# MAIN - INTERFACE STREAMLIT
# ═══════════════════════════════════════════════════════════════════════════

def main():
    """Função principal da aplicação Streamlit."""
    
    # Header
    st.markdown(
        "<div class='header-style'>♿ ETL: Pessoas Com Deficiência no Brasil</div>",
        unsafe_allow_html=True
    )
    
    st.markdown("""
    Sistema de extração, transformação e análise de dados sobre pessoas com deficiência
    no Brasil, utilizando dados públicos do IBGE (Instituto Brasileiro de Geografia e Estatística).
    """)
    
    st.divider()
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configurações")
        
        opcao = st.radio(
            "Escolha o modo:",
            options=["🏃 Executar Pipeline", "📊 Análise Exploratória", "ℹ️ Sobre"]
        )
    
    # MODO 1: Executar Pipeline
    if opcao == "🏃 Executar Pipeline":
        st.header("Executar Pipeline ETL Completo")
        
        if st.button("🚀 Iniciar Extração, Transformação e Carregamento"):
            df_transformado, resumo = executar_pipeline_etl()
            
            st.success("✅ Pipeline executado com sucesso!")
            
            # Salvar em session state
            st.session_state.df_transformado = df_transformado
            st.session_state.resumo = resumo
            
            # Mostrar resumo
            st.info(f"📅 Processado em: {resumo['data_processamento']}")
        
        # Mostrar opção de carregamento se dados estão em session
        if 'df_transformado' in st.session_state:
            st.divider()
            st.subheader("📤 Carregar Dados no PostgreSQL")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"Total de registros: **{len(st.session_state.df_transformado)}** estados")
            
            with col2:
                if st.button("💾 Carregar", use_container_width=True):
                    carregar_no_banco(st.session_state.df_transformado)
    
    # MODO 2: Análise Exploratória
    elif opcao == "📊 Análise Exploratória":
        st.header("Análise Exploratória de Dados")
        
        # Verificar se dados foram carregados
        if 'df_transformado' in st.session_state:
            df = st.session_state.df_transformado
            resumo = st.session_state.resumo
            
            # Criar visualizações
            criar_graficos(df)
            
            st.divider()
            
            # Criar tabelas e análises
            criar_tabelas_analise(df, resumo)
            
        else:
            st.warning("⚠️ Nenhum dado carregado. Execute o pipeline primeiro!")
    
    # MODO 3: Sobre
    elif opcao == "ℹ️ Sobre":
        st.header("Sobre Este Projeto")
        
        st.markdown("""
        ### 📖 Descrição
        
        Este projeto implementa um **pipeline ETL completo** focado em dados de pessoas com deficiência no Brasil.
        
        ### 🎯 Objetivos
        
        - **Educação**: Ensinar conceitos de ETL de forma didática
        - **Prática**: Implementação profissional com boas práticas
        - **Acessibilidade**: Dados sobre pessoas com deficiência
        
        ### 📡 Fonte de Dados
        
        - **API**: IBGE (Instituto Brasileiro de Geografia e Estatística)
        - **Dados**: Estados, municípios e estimativas populacionais
        - **Frequência**: Atualizado a cada execução
        
        
        ### 📚 Módulos
        
        1. **extracao.py**: Extrai dados da API do IBGE
        2. **transformacao.py**: Limpa e normaliza dados
        3. **carregamento.py**: Persiste dados em PostgreSQL
        4. **main.py**: Interface Streamlit e análises
        
        ### 🔗 Links Úteis
        
        - [IBGE API](https://servicodados.ibge.gov.br/)
        - [Streamlit Docs](https://docs.streamlit.io/)
        - [Pandas Docs](https://pandas.pydata.org/)
        
        ### 👨‍💻 Autor
        
        Projeto didático para ensino de ETL em Python
        
        ### 📄 Licença
        
        Código aberto para fins educacionais
        """)


if __name__ == "__main__":
    main()
