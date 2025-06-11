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

def get_directory(highlight_index=None) -> pd.DataFrame:
    df = pd.DataFrame(st.session_state['directory'], columns=['Bucket'])

    if highlight_index is not None:
        def highlight(cell):
            styles = pd.DataFrame('', index=df.index, columns=df.columns)
            if 0 <= highlight_index < len(df):
                styles.loc[highlight_index, 'Bucket'] = 'background-color: green'
            return styles
        return df.style.apply(highlight, axis=None)

    return df

def get_buckets(highlight_info=None) -> pd.DataFrame:
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
            # print(bucket_dict[f'Valor {j + 1}'])
        bucket_data.append(bucket_dict)

    df = pd.DataFrame(bucket_data)

    if highlight_info:
        row_idx, col_name, status = highlight_info

        def highlight(cell):
            # Retorna um DataFrame com os estilos
            styles = pd.DataFrame('', index=df.index, columns=df.columns)

            if status == 'found': 
                if col_name in df.columns and 0 <= row_idx < len(df):
                    styles.loc[row_idx, col_name] = 'background-color: green'
            elif status == 'not found' and 0 <= row_idx < len(df):
                # Marca todas as colunas Valor 1 até Valor n em vermelho
                for j in range(st.session_state['elements_per_bucket']):
                    col = f'Valor {j + 1}'
                    if col in df.columns:
                        styles.loc[row_idx, col] = 'background-color: red'

            return styles

        return df.style.apply(highlight, axis=None)

    return df

# --- Funções para inserir e remover elementos da Tabela Hash Extensível --- #

def insert_number(added_number):
    log_step(f"📥 Inserir número: **{added_number}**")  

    # Calcula o índice do diretório usando um hash simples
    directory_index = added_number % (2 ** st.session_state['p_global'])
    log_step(f"Cálcular índice: `{added_number} % {2 ** st.session_state['p_global']} = {directory_index}`")

    # Obtém o bucket correspondente
    bucket_index = st.session_state['directory'][directory_index]
    log_step(f"Acessar: `Diretório[{directory_index}] -> Bucket[{bucket_index}]`")

    bucket = st.session_state['buckets'][bucket_index]
    
    # Verifica se há espaço disponível no bucket
    if bucket[1] < st.session_state['elements_per_bucket']:
        # Insere o número 
        bucket[1] += 1
        bucket[ bucket[1] + 1 ] = added_number 
        log_step(f"✅ Espaço encontrado no Bucket {bucket_index}. Inserido na posição {bucket[1]}")
    else:
        # Se o bucket está cheio, realiza a divisão
        log_step(f"❌ Bucket {bucket_index} está cheio. Iniciando split...")
        split_bucket(directory_index, bucket_index, added_number)

def split_bucket(directory_index, bucket_index, added_number):
    # Obtém profundidade local do bucket e incrementa
    
    local_depth = st.session_state['buckets'][bucket_index][0] + 1

    # Separar o bucket original
    original_bucket = st.session_state['buckets'][bucket_index]

    log_step(f"Atualizar profundidade Local (p') do Bucket {bucket_index}: `{original_bucket[0]} -> {local_depth}`")
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
        log_step(f"Profundidade global aumentada para {st.session_state['p_global']}. Diretório duplicado.")
    else:
        st.session_state['directory'][directory_index] = len(st.session_state['buckets']) - 1

    log_step(f"🔄 Reinserir `{original_bucket[2:len(original_bucket)]}` e depois `{added_number}`")
    # Inserir novamente os valores do bucket original
    for i in range(2, len(original_bucket)):
        insert_number(original_bucket[i])

    # Inserir o valor incialmente pretendido
    insert_number(added_number)


def log_step(text):
    if 'insertion_steps' not in st.session_state:
        st.session_state['insertion_steps'] = []
    st.session_state['insertion_steps'].append(text)



# --- Funções para pesquisar na tabela Hash Extensível --- #

def search_number (searched_number):
     # Calcula o índice do diretório usando um hash simples
    directory_index = searched_number % (2 ** st.session_state['p_global'])

    # Obtém o bucket correspondente
    bucket_index = st.session_state['directory'][directory_index]
    bucket = st.session_state['buckets'][bucket_index]

    # Verifica se o número pesquisado está no bucket
    bucket_length = bucket[1]

    for col, number in enumerate(bucket[2:bucket_length + 2]):
        if number == searched_number:
            return bucket_index, f'Valor {col+1}', 'found' , directory_index

    return bucket_index, None, 'not found', directory_index

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
    col_insert, col_search, col_log = st.columns([1, 1, 1])

    with col_insert:
        added_number = st.number_input(
            label="Número a ser adicionado",
            step=1,
            format="%d",
        )

        if st.button("Adicionar"):
            st.session_state['insertion_steps'] = [] # resetar os passos da inserção
            insert_number(added_number)

    highlight = None
    highlight_dir = None
    search_steps = ""

    with col_search:
        searched_number = st.number_input(
            label="Número a ser pesquisado", 
            step=1, 
            format="%d"
        )
        if st.button("Pesquisar"):
            result = search_number(searched_number)
            highlight = result[:3]      # (bucket_index, col_name, status)
            highlight_dir = result[3]   # directory_index

            modulo_base = 2 ** st.session_state['p_global']
            bucket_value = st.session_state['directory'][highlight_dir]

            if highlight[2] == 'found':
                result_text = f"O número **{searched_number}** foi encontrado no Bucket `{result[0]}` na coluna `{result[1]}`. ✅"
            else:
                result_text = f"O número **{searched_number}** não foi encontrado no Bucket `{result[0]}`. ❌"

            search_steps = f"""
            #### 🔍 Passo a Passo da Busca:
            1. **Procurar {searched_number}**
            2. Calcular índice: `{searched_number} % {modulo_base} = {highlight_dir}`
            3. Acessar: `diretório[{highlight_dir}] = {bucket_value}`
            4. Verificar o bucket `{bucket_value}`
            
            {result_text}
            """

    # Mostrando tabelas lado a lado
    col1, col2, col_log = st.columns([2, max(5, st.session_state['elements_per_bucket']),3])

    with col1:
        p_global = st.session_state['p_global']
        st.subheader(f'Diretório (p = {p_global})')
        st.table(get_directory(highlight_dir))

    with col2:
        st.subheader('Buckets')
        st.table(get_buckets(highlight))
        st.session_state['buckets']

    with col_log:
            if search_steps:
                st.markdown(search_steps)
            if 'insertion_steps' in st.session_state:
                inserir_achados = 0
                with st.expander("#### 📋 Passo a passo da Inserção", expanded=True):
                    for i, step in enumerate(st.session_state['insertion_steps'][0:]):  # pula o título
                        if step.find('📥') != -1: # determinar se escrito é do tipo (inseriondo numero x)
                            st.markdown(f"##### {step}")
                            inserir_achados+=1
                        else:
                            st.markdown(f"{i+1-inserir_achados}. {step}")
    # BOTAO PARA FACILITAR TESTES
    if st.button("Preencher 1 - 14"):
            for i in range(1,15):
                st.session_state['insertion_steps'] = []
                insert_number(i)
                st.session_state['insertion_steps'] = []
                

