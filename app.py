import streamlit as st
import pandas as pd

# Configurações iniciais da página
st.set_page_config(
    page_title="Hash Extensível",
    layout="wide",
)

# --- Funções para inicializar valores padrão no session_state --- #

def standard_directory_values():
    # Inicializa o diretório com 2^p_global zeros
    length = 2 ** st.session_state['p_global']
    st.session_state['directory'] = [0] * length

def standard_buckets_values():
    # Inicializa os buckets: cada bucket tem (elements_per_bucket + 2) posições
    size = st.session_state['elements_per_bucket'] + 2
    # Exemplo simples: 1 bucket inicial com profundidade local p' = 0 e todos valores zero
    st.session_state['buckets'] = [[0] + [0] + [0] * st.session_state['elements_per_bucket']]

# --- Funções para montar DataFrames para visualização --- #

def get_directory() -> pd.DataFrame:
    return pd.DataFrame(st.session_state['directory'])

def get_buckets() -> pd.DataFrame:
    # Para cada bucket, monta um dicionário com p' e os valores
    bucket_data = []
    for bucket in st.session_state['buckets']:
        # Pegar valores de controle
        bucket_dict = {"p'": bucket[0], "n": bucket[1]}
        # Pegar valores reais
        for j in range(bucket[1]):
            bucket_dict[f'Valor {j + 1}'] = bucket[j + 2] 
        for j in range(bucket[1], st.session_state['elements_per_bucket']):
            bucket_dict[f'Valor {j + 1}'] = 'X'
            print(bucket_dict[f'Valor {j + 1}'])
        bucket_data.append(bucket_dict)

    df = pd.DataFrame(bucket_data)
    return df

# --- Funções para inserir e remover elementos da Tabela Hash Extensível --- #

def insert_number(added_number):
    # Calcula o índice do diretório usando um hash simples
    directory_index = added_number % (2 ** st.session_state['p_global'])

    # Obtém o bucket correspondente
    bucket_index = st.session_state['directory'][directory_index]
    bucket = st.session_state['buckets'][bucket_index]

    # Verifica se há espaço disponível no bucket
    if bucket[1] < st.session_state['elements_per_bucket']:
        # Insere o número 
        bucket[1] += 1
        bucket[ bucket[1] + 1 ] = added_number 
    else:
        # Se o bucket está cheio, realiza a divisão
        split_bucket(directory_index, bucket_index, added_number)

def split_bucket(directory_index, bucket_index, added_number):
    # Obtém profundidade local do bucket e incrementa
    local_depth = st.session_state['buckets'][bucket_index][0] + 1

    # Separar o bucket original
    original_bucket = st.session_state['buckets'][bucket_index]

    # Esvaziar primeiro bucket
    empty_bucket = [local_depth] + [0] + [0] * st.session_state['elements_per_bucket']
    st.session_state['buckets'][bucket_index] = empty_bucket

    # Criar novo bucket
    new_bucket = [local_depth] + [0] + [0] * st.session_state['elements_per_bucket']
    st.session_state['buckets'].append(new_bucket)

    # Testar se a profundidade local excede p_global
    if local_depth > st.session_state['p_global']:
        # Aumenta a profundidade global
        st.session_state['p_global'] += 1
        # Duplica o diretório
        st.session_state['directory'] *= 2
        # Atualizar o endereço do diretório
        st.session_state['directory'][added_number % (2 ** st.session_state['p_global'])] = len(st.session_state['buckets']) - 1
    else:
        st.session_state['directory'][directory_index] = len(st.session_state['buckets']) - 1

    # Inserir novamente os valores do bucket original
    for i in range(2, len(original_bucket)):
        insert_number(original_bucket[i])

    # Inserir o valor incialmente pretendido
    insert_number(added_number)

def remove_number(removed_number):
    pass

# --- Inicialização das variáveis do session_state (somente se ainda não existirem) --- #

if 'p_global' not in st.session_state:
    st.session_state['p_global'] = 0

if 'elements_per_bucket' not in st.session_state:
    st.session_state['elements_per_bucket'] = 1 

if 'directory' not in st.session_state:
    standard_directory_values()

if 'buckets' not in st.session_state:
    standard_buckets_values()

if 'config' not in st.session_state:
    st.session_state['config'] = True

if 'number_added' not in st.session_state:
    st.session_state['number_added'] = 0

# --- Layout da página --- #

st.title("Tabela Hash Extensível")

if st.session_state['config']:
    st.markdown("""
    A **Tabela Hash Extensível** é uma estrutura dinâmica utilizada para resolver colisões em tabelas hash de maneira eficiente.  
    Ela se baseia no uso de **buckets** (ou cestos), onde os dados são armazenados, e em um **diretório**, que funciona como um mapeamento entre os endereços de hash e os buckets reais.

    Diferente das tabelas hash convencionais com tamanho fixo, a tabela extensível **cresce ou se reorganiza automaticamente** conforme a quantidade de dados aumenta, mantendo um bom desempenho nas operações de inserção, busca e remoção.

    O diretório pode duplicar de tamanho e os buckets podem se dividir conforme necessário, garantindo que não haja necessidade de reorganizar todos os dados existentes.

    A seguir, você poderá configurar e visualizar interativamente o funcionamento dessa estrutura.

    Para começar, escolha a quantidade de elementos que cabem em um cesto:
    """)

    # Input para quantidade de elementos por bucket
    n = st.number_input(
        label="Quantidade máxima de elementos por cesto (bucket)",
        min_value=1,
        step=1,
        format="%d",
    )

    # Botão para iniciar a visualização
    if st.button("Começar"):
        st.session_state['elements_per_bucket'] = n
        standard_buckets_values()
        st.session_state['config'] = False
        st.rerun()

else:
    # Input para adicionar número 
    col_insert, col_remove = st.columns([1, 1])

    with col_insert:
        added_number = st.number_input(
            label="Número a ser adicionado",
            step=1,
            format="%d",
        )

        if st.button("Adicionar"):
            insert_number(added_number)

    with col_remove:
        removed_number = st.number_input(
            label="Número a ser removido",
            step=1,
            format="%d",
        )

        if st.button("Remover"):
            insert_number(removed_number)

    # Mostrando tabelas lado a lado
    col1, spacer, col2 = st.columns([3, 0.5, max(5, st.session_state['elements_per_bucket'])])

    with col1:
        p_global = st.session_state['p_global']
        st.subheader(f'Diretório (p = {p_global})')
        st.table(get_directory())

    with col2:
        st.subheader('Buckets')
        st.table(get_buckets())
        st.session_state['buckets']

