# ETL: Pessoas Com Deficiência no Brasil

## 📖 Visão Geral

Sistema completo de **Extração, Transformação e Carregamento (ETL)** de dados sobre pessoas com deficiência no Brasil, utilizando a **API pública do IBGE**. O projeto implementa boas práticas de engenharia de software com foco didático.

---

## 🎯 Objetivos

- ✅ **Ensinar** conceitos de ETL de forma prática e didática
- ✅ **Demonstrar** arquitetura profissional em Python
- ✅ **Fornecer** acesso a dados públicos sobre acessibilidade
- ✅ **Criar** dashboard interativo com visualizações

---

## 🏗️ Arquitetura do Sistema

```
┌──────────────────────────────────────────────────────────────────────┐
│                     PIPELINE ETL - FLUXO DE DADOS                    │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────┐
│  API do IBGE │  ← Fonte de dados
└──────┬───────┘
       │
       ├─ Estados
       ├─ Municípios
       └─ Regiões
       │
       ▼
┌──────────────────────────────────┐
│    1. EXTRAÇÃO (extracao.py)     │
├──────────────────────────────────┤
│ • Conecta à API do IBGE          │
│ • Extrai dados de 27 estados     │
│ • Busca municípios por estado    │
│ • Armazena em DataFrame bruto    │
└──────────────┬───────────────────┘
               │
               ▼
┌──────────────────────────────────┐
│  2. TRANSFORMAÇÃO (transf...)    │
├──────────────────────────────────┤
│ • Valida dados                   │
│ • Remove valores nulos           │
│ • Normaliza tipos de dados       │
│ • Calcula métricas derivadas     │
│ • Enriquece com status           │
└──────────────┬───────────────────┘
               │
               ▼
┌──────────────────────────────────┐
│   3. CARREGAMENTO (carrega...)   │
├──────────────────────────────────┤
│ • Conecta ao PostgreSQL optional │
│ • Cria/atualiza tabelas          │
│ • Insere dados transformados     │
│ • Valida carregamento            │
└──────────────┬───────────────────┘
               │
               ▼
┌──────────────────────────────────┐
│   4. ANÁLISE (main.py/Streamlit) │
├──────────────────────────────────┤
│ • Dashboard interativo           │
│ • Visualizações com Plotly      │
│ • Filtros e análises dinâmicas  │
│ • Download de dados em CSV       │
└──────────────────────────────────┘
```

---

## 📊 Fluxo de Tarefas Detalhado

### **Fase 1: EXTRAÇÃO**
```
ExtractorPCD.extrair_todos_estados()
    ├─ Para cada um dos 27 estados:
    │   ├─ GET /api/v1/localidades/estados/{sigla}
    │   │   └─ Obtém: Nome, Região, ID
    │   │
    │   ├─ GET /api/v1/localidades/estados/{sigla}/municipios
    │   │   └─ Obtém: Lista de municípios
    │   │
    │   └─ Calcula:
    │       ├─ total_municipios
    │       ├─ pessoas_com_deficiencia_aprox (8% pop.)
    │       └─ estabelecimentos_saude_aprox (2 por município)
    │
    └─ Retorna: DataFrame com 27 registros

Tempo estimado: 30-60 segundos
```

### **Fase 2: TRANSFORMAÇÃO**
```
TransformerPCD.transformar(df_bruto)
    ├─ _validar_dados()
    │   └─ Verifica colunas obrigatórias e integridade
    │
    ├─ _limpar_valores_ausentes()
    │   └─ Remove linhas com NaN
    │
    ├─ _normalizar_colunas()
    │   └─ Lowercase, tipos de dados corretos
    │
    ├─ _calcular_metricas()
    │   ├─ pcd_por_municipio (PCD / municípios)
    │   ├─ saude_por_pcd (estabelecimentos / PCD)
    │   └─ pct_pcd_nacional (% em relação ao total)
    │
    └─ _enriquecer_dados()
        ├─ data_processamento (timestamp)
        └─ status_saude (Crítico/Baixo/Normal)

Saída: DataFrame com 33 colunas (6 originais + 3 calculadas + enriquecimento)
```

### **Fase 3: CARREGAMENTO**
```
LoaderPCD.carregar(df_transformado)
    ├─ _validar_dados()
    │   └─ Verifica integridade antes de carregar
    │
    ├─ Conecta: postgresql://user:password@host:5432/database
    │
    ├─ df.to_sql('pessoas_com_deficiencia', ...)
    │   ├─ Cria tabela se não existir
    │   ├─ Carrega dados em chunks de 1000
    │   └─ Método: multi (otimizado)
    │
    └─ _validar_carregamento()
        └─ Verifica se todas linhas foram carregadas

Destino: Tabela 'pessoas_com_deficiencia' no PostgreSQL
```

### **Fase 4: ANÁLISE (Streamlit)**
```
main.py - Dashboard Interativo
    ├─ Modo 1: Executar Pipeline
    │   ├─ Botão para iniciar ETL completo
    │   ├─ Mostrar progresso em tempo real
    │   └─ Opção de carregar no PostgreSQL
    │
    ├─ Modo 2: Análise Exploratória
    │   ├─ Top 10 estados com mais PCD
    │   ├─ Gráfico de pizza: PCD por região
    │   ├─ Scatter plot: Municípios vs PCD
    │   ├─ Status de saúde por estado
    │   ├─ Tabela interativa com filtros
    │   └─ Download em CSV
    │
    └─ Modo 3: Informações
        └─ Sobre o projeto, arquitetura, links
```

---

## 📁 Estrutura de Arquivos

```
Aula_Teste_ETL/
├── README.md                 # Este arquivo
├── requirements.txt          # Dependências Python
│
├── extracao.py              # Módulo 1: ExtractorPCD
├── transformacao.py         # Módulo 2: TransformerPCD
├── carregamento.py          # Módulo 3: LoaderPCD
├── main.py                  # Módulo 4: Dashboard Streamlit
│
├── etl.ipynb                # Notebook de referência (opcional)
│
└── dados_saude_brasil.csv   # Output: Dados exportados (gerado)
```

---

## 🚀 Como Usar

### **Pré-requisitos**

```bash
# Python 3.8+ instalado
python --version

# pip disponível
pip --version
```

### **Instalação**

```bash
# 1. Clone ou baixe os arquivos
cd Aula_Teste_ETL

# 2. Crie um ambiente virtual (recomendado)
python -m venv venv

# No Windows:
venv\Scripts\activate

# No Linux/Mac:
source venv/bin/activate

# 3. Instale dependências
pip install -r requirements.txt
```

### **Executar o Dashboard (Recomendado)**

```bash
streamlit run main.py
```

Abre automaticamente em `http://localhost:8501`

### **Executar Manualmente**

```python
from extracao import ExtractorPCD
from transformacao import TransformerPCD
from carregamento import LoaderPCD

# 1. EXTRAÇÃO
extrator = ExtractorPCD()
df_bruto = extrator.extrair_todos_estados()

# 2. TRANSFORMAÇÃO
transformer = TransformerPCD()
df_transformado = transformer.transformar(df_bruto)

# 3. CARREGAMENTO (Opcional - requer PostgreSQL)
try:
    loader = LoaderPCD(
        host='localhost',
        user='postgres',
        password='sua_senha',
        database='pcd_database'
    )
    loader.carregar(df_transformado)
except Exception as e:
    print(f"PostgreSQL não disponível: {e}")

# 4. ANÁLISE
print(transformer.gerar_resumo(df_transformado))
df_transformado.to_csv('dados_pcd_brasil.csv', index=False)
```

---

## 🔧 Configuração do PostgreSQL (Opcional)

### **Instalar PostgreSQL**

**Windows:**
```bash
# Usar instalador oficial
# https://www.postgresql.org/download/windows/
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install postgresql postgresql-contrib
```

**MacOS:**
```bash
brew install postgresql
```

### **Iniciar Servidor**

```bash
# Windows (PostgreSQL instalado como serviço)
# Já inicia automaticamente

# Linux/Mac
pg_ctl -D /usr/local/var/postgres start
```

### **Criar Database**

```bash
# Conectar ao PostgreSQL
psql -U postgres

# Criar banco de dados
CREATE DATABASE pcd_database;

# Sair
\q
```

### **Usar no Código**

```python
loader = LoaderPCD(
    host='localhost',
    port=5432,
    user='postgres',
    password='sua_senha',
    database='pcd_database'
)
loader.carregar(df_transformado)
```

---

## 📊 Descrição dos Dados

### **Colunas Originais**

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| estado_sigla | string | Sigla do estado (ex: 'SP', 'MG') |
| estado_nome | string | Nome completo do estado |
| regiao | string | Região (Norte, Nordeste, Centro-Oeste, Sudeste, Sul) |
| total_municipios | int | Quantidade de municípios no estado |
| pessoas_com_deficiencia_aprox | float | Estimativa de PCDs (~8% população) |
| estabelecimentos_saude_aprox | float | Estimativa de estabelecimentos (~2 por município) |

### **Colunas Calculadas (Transformação)**

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| pcd_por_municipio | float | PCD / total_municipios |
| saude_por_pcd | float | estabelecimentos / pcd |
| pct_pcd_nacional | float | % do total nacional de PCD |
| status_saude | string | Crítico/Baixo/Normal (saude_por_pcd) |
| data_processamento | datetime | Timestamp do processamento |

### **Exemplo de Dados**

```
estado_sigla | estado_nome    | regiao   | total_municipios | pcd_aprox
–––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
SP           | São Paulo      | Sudeste  | 645              | 516,000
MG           | Minas Gerais   | Sudeste  | 853              | 682,400
RJ           | Rio de Janeiro | Sudeste  | 92               | 73,600
BA           | Bahia          | Nordeste | 417              | 333,600
```

---

## 📈 Métricas e Resumo

Após executar o pipeline, você terá:

```
Total de Estados: 27
Total de Municípios: 5,571
Total de PCD (estimado): ~4,456,800
Total de Estabelecimentos: ~11,142

Por Região:
  - Norte: 449 municípios, ~359,200 PCD
  - Nordeste: 1,794 municípios, ~1,435,200 PCD
  - Centro-Oeste: 467 municípios, ~373,600 PCD
  - Sudeste: 1,668 municípios, ~1,334,400 PCD
  - Sul: 1,193 municípios, ~954,400 PCD
```

---

## 🎓 Conceitos Didáticos

Este projeto ensina:

### **Engenharia de Software**
- Programação Orientada a Objetos (POO)
- Documentação com Docstrings
- Tratamento de exceções
- Logging estruturado

### **ETL**
- Arquitetura de pipelines
- Validação de dados
- Transformações
- Carregamento em banco

### **Python Data**
- `requests`: Requisições HTTP
- `pandas`: Análise de dados
- `SQLAlchemy`: ORM para banco de dados
- `streamlit`: Dashboards web
- `plotly`: Visualizações interativas

### **Boas Práticas**
- Código limpo e legível
- Comentários explicativos
- Tipo hints
- Separação de responsabilidades

---

## 🐛 Troubleshooting

### **Erro: ConnectionError ao acessar API**

```
Solução: Verificar conexão de internet
         Verificar se API do IBGE está disponível
         Tentar aumentar timeout em ExtractorPCD(timeout=30)
```

### **Erro: ModuleNotFoundError**

```bash
# Solução: Reinstalar dependências
pip install -r requirements.txt --force-reinstall
```

### **Erro: PostgreSQL - connection refused**

```
Solução: Verificar se PostgreSQL está rodando
         No Linux: sudo service postgresql start
         Verificar credenciais (user, password)
         Verificar se database existe: CREATE DATABASE pcd_database;
```

### **Streamlit: Port já em uso**

```bash
# Solução: Usar porta diferente
streamlit run main.py --server.port 8502
```

---

## 📚 Recursos Adicionais

### **API do IBGE**
- Documentação: https://servicodados.ibge.gov.br/
- Endpoint de Estados: `/api/v1/localidades/estados`
- Endpoint de Municípios: `/api/v1/localidades/Estados/{UF}/municipios`

### **Bibliotecas Utilizadas**
- Pandas: https://pandas.pydata.org/docs/
- Streamlit: https://docs.streamlit.io/
- Plotly: https://plotly.com/python/
- SQLAlchemy: https://docs.sqlalchemy.org/

### **Tópicos Relacionados**
- [ETL - Extract Transform Load](https://en.wikipedia.org/wiki/Extract,_load,_transform)
- [REST API Concepts](https://restfulapi.net/)
- [Data Warehousing](https://en.wikipedia.org/wiki/Data_warehouse)

---

## 📝 Notas Importantes

1. **Dados Aproximados**: As estimativas de PCD (8%) são baseadas em média nacional. Dados reais devem vir de fontes específicas do IBGE ou Ministério da Saúde.

2. **API Públicos**: Não requer autenticação, mas tem limite de requisições.

3. **Performance**: O pipeline completo leva ~60 segundos para 27 estados.

4. **PostgreSQL Opcional**: Pode usar com CSV apenas (sem BD).

---

## 👨‍💻 Autor

Projeto educacional desenvolvido para ensino de ETL em Python.

---

## 📄 Licença

Código aberto para fins educacionais. Livre para modificar e distribuir.

---

## ❓ Dúvidas?

Consulte:
1. Docstrings no código Python
2. Comentários no Notebook
3. Logs de execução (modo verbose)
4. Arquivo README.md (este arquivo)

---

**Última atualização**: 2024
**Versão**: 1.0
**Status**: ✅ Funcional e Testado
