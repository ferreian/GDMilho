import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configurando o layout da página para modo wide
st.set_page_config(layout="wide")

# Função para carregar dados na sessão
def load_data(uploaded_file):
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)
        # Verificando se as colunas necessárias estão presentes
        required_columns = ['latitude', 'longitude', 'estado', 'prod_media_corr_sc', 'hibrido',
                            'cidadeUF', 'conjuntaGeral', 'macroRegiao', 'microRegiao', 'populacao']
        if all(column in df.columns for column in required_columns):
            # Filtrando linhas que possuem valores NaN nas colunas necessárias
            df = df.dropna(subset=required_columns)
            st.session_state['dataframe'] = df
            return df
        else:
            st.error(f"O arquivo deve conter as colunas {', '.join(required_columns)}")
    return None

# Definindo o título da página
st.title('Dashboard Ensaios Comparativos de GD')

# Adicionando o uploader na sidebar
st.sidebar.title("Upload de Arquivo")
uploaded_file = st.sidebar.file_uploader("Escolha um arquivo Excel", type=["xlsx"])

# Carregando os dados na sessão
df = load_data(uploaded_file)

# Verificando se o dataframe está na sessão
if 'dataframe' in st.session_state:
    df = st.session_state['dataframe']

    # Contar híbridos
    st.write("Total de Híbridos:")
    contagem_hibridos = df['hibrido'].nunique()
    st.write(f"{contagem_hibridos}")

    # Gráfico de rosca
    st.write('Distribuição dos ensaios por UF:')
    estado_counts = df['estado'].value_counts().reset_index()
    estado_counts.columns = ['estado', 'count']
    
    fig_pie = px.pie(estado_counts, values='count', names='estado', hole=0.5, 
                     title=f"Total de Estados: {estado_counts['estado'].nunique()}",
                     labels={'estado':'Estado', 'count':'Número de Ensaios'})

    fig_pie.update_traces(textinfo='percent+label', textposition='inside', hoverinfo='label+percent+value')

    # Adicionando o número total de estados no centro do gráfico
    fig_pie.add_annotation(dict(font=dict(size=20),
                                x=0.5,
                                y=0.5,
                                showarrow=False,
                                text=f"Total: {estado_counts['estado'].nunique()}",
                                xanchor='center',
                                yanchor='middle'))

    st.plotly_chart(fig_pie, use_container_width=True)

    # Tabela com a média, maior e menor produtividade por híbrido
    st.write('Média de Produtividade por Híbrido:')
    prod_media = df.groupby('hibrido')['prod_media_corr_sc'].agg(['mean', 'max', 'min']).reset_index()
    prod_media.columns = ['Híbrido', 'Produtividade Média (sc)', 'Maior Produtividade (sc)', 'Menor Produtividade (sc)']
    
    # Calculando a média geral
    media_geral = prod_media['Produtividade Média (sc)'].mean()
    
    # Calculando a porcentagem relativa em relação à média geral
    prod_media['% da Média'] = ((prod_media['Produtividade Média (sc)'] - media_geral) / media_geral * 100).round(2)
    
    # Calculando a porcentagem em relação ao maior valor
    max_value = prod_media['Produtividade Média (sc)'].max()
    prod_media['% do Maior'] = ((prod_media['Produtividade Média (sc)'] - max_value) / max_value * 100).round(2)
    
    # Normalizando os dados
    prod_media_norm = prod_media.copy()
    prod_media_norm['Produtividade Média (sc)'] = (prod_media_norm['Produtividade Média (sc)'] - prod_media_norm['Produtividade Média (sc)'].min()) / (prod_media_norm['Produtividade Média (sc)'].max() - prod_media_norm['Produtividade Média (sc)'].min())
    prod_media_norm['Maior Produtividade (sc)'] = (prod_media_norm['Maior Produtividade (sc)'] - prod_media_norm['Maior Produtividade (sc)'].min()) / (prod_media_norm['Maior Produtividade (sc)'].max() - prod_media_norm['Maior Produtividade (sc)'].min())
    prod_media_norm['Menor Produtividade (sc)'] = (prod_media_norm['Menor Produtividade (sc)'] - prod_media_norm['Menor Produtividade (sc)'].min()) / (prod_media_norm['Menor Produtividade (sc)'].max() - prod_media_norm['Menor Produtividade (sc)'].min())
    
    # Definindo os pesos dos critérios
    weights = {'Produtividade Média (sc)': 0.5, 'Maior Produtividade (sc)': 0.3, 'Menor Produtividade (sc)': 0.2}
    
    # Calculando a pontuação final
    prod_media_norm['Pontuação Final'] = (prod_media_norm['Produtividade Média (sc)'] * weights['Produtividade Média (sc)'] +
                                          prod_media_norm['Maior Produtividade (sc)'] * weights['Maior Produtividade (sc)'] +
                                          prod_media_norm['Menor Produtividade (sc)'] * weights['Menor Produtividade (sc)'])
    
    # Ordenando a matriz de decisão em ordem decrescente pela pontuação final
    prod_media_norm = prod_media_norm.sort_values(by='Pontuação Final', ascending=False)
    
    # Criação das abas
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Produtividade Média", "Percentagem da Média", "% em Relação ao Maior", "Matriz de Decisão", "Head to Head"])

    # Híbridos a serem destacados em azul
    hibridos_azul = ['9504VIP3', '9801VIP3', '9703TG', '9602VIP3', '9705VIP3']

    with tab1:
        st.write('Gráfico de Barras da Produtividade Média por Híbrido (Ordem Decrescente):')
        
        # Ordenando por produtividade média em ordem decrescente
        prod_media_sorted = prod_media.sort_values(by='Produtividade Média (sc)', ascending=False)
        
        # Definindo as cores das barras
        colors = ['blue' if hibrido in hibridos_azul else 'gray' for hibrido in prod_media_sorted['Híbrido']]
        
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            x=prod_media_sorted['Híbrido'], 
            y=prod_media_sorted['Produtividade Média (sc)'],
            marker_color=colors,  # Aplicando as cores
            text=prod_media_sorted['Produtividade Média (sc)'].round(1),  # Adicionando os valores como rótulos
            textposition='outside'  # Posição dos rótulos fora das barras
        ))
        
        # Adicionando linha da média
        fig_bar.add_shape(
            type='line',
            line=dict(dash='dash', color='red'),
            x0=-0.5,
            x1=len(prod_media_sorted)-0.5,
            y0=media_geral,
            y1=media_geral
        )
        
        # Adicionando anotação para a linha da média
        fig_bar.add_annotation(
            x=len(prod_media_sorted)-0.5,
            y=media_geral,
            text=f'Média: {media_geral:.2f}',
            showarrow=False,
            yshift=10,
            font=dict(color='red')
        )
        
        # Configurando o layout do gráfico de barras
        fig_bar.update_layout(
            title='Produtividade Média por Híbrido',
            xaxis_title='Híbrido',
            yaxis_title='Produtividade Média (sc)',
            bargap=0.2,  # Ajustando o espaço entre as barras
            showlegend=False
        )
        
        st.plotly_chart(fig_bar, use_container_width=True)

    with tab2:
        st.write('Gráfico de Barras da Percentagem da Média por Híbrido:')
        
        # Definindo as cores das barras
        colors_pct = ['blue' if hibrido in hibridos_azul else 'gray' for hibrido in prod_media_sorted['Híbrido']]
        
        fig_bar_pct = go.Figure()
        fig_bar_pct.add_trace(go.Bar(
            x=prod_media_sorted['Híbrido'], 
            y=prod_media_sorted['% da Média'],
            marker_color=colors_pct,  # Aplicando as cores
            text=prod_media_sorted['% da Média'].round(1),  # Adicionando os valores como rótulos
            textposition='outside'  # Posição dos rótulos fora das barras
        ))
        
        # Configurando o layout do gráfico de barras de porcentagem
        fig_bar_pct.update_layout(
            title='% da Média por Híbrido',
            xaxis_title='Híbrido',
            yaxis_title='% da Média',
            bargap=0.2,  # Ajustando o espaço entre as barras
            showlegend=False
        )
        
        st.plotly_chart(fig_bar_pct, use_container_width=True)

    with tab3:
        st.write('Gráfico de Barras da Percentagem em Relação ao Maior por Híbrido:')
        
        # Definindo as cores das barras
        colors_max = ['blue' if hibrido in hibridos_azul else 'gray' for hibrido in prod_media_sorted['Híbrido']]
        
        fig_bar_max = go.Figure()
        fig_bar_max.add_trace(go.Bar(
            x=prod_media_sorted['Híbrido'], 
            y=prod_media_sorted['% do Maior'],
            marker_color=colors_max,  # Aplicando as cores
            text=prod_media_sorted['% do Maior'].round(1),  # Adicionando os valores como rótulos
            textposition='outside'  # Posição dos rótulos fora das barras
        ))
        
        # Configurando o layout do gráfico de barras de porcentagem em relação ao maior
        fig_bar_max.update_layout(
            title='% em Relação ao Maior por Híbrido',
            xaxis_title='Híbrido',
            yaxis_title='% do Maior',
            bargap=0.2,  # Ajustando o espaço entre as barras
            showlegend=False
        )
        
        st.plotly_chart(fig_bar_max, use_container_width=True)

    with tab4:
        st.write('Matriz de Decisão:')
        st.dataframe(prod_media_norm)
        
        # Definindo as cores das barras
        colors_decision = ['blue' if hibrido in hibridos_azul else 'gray' for hibrido in prod_media_norm['Híbrido']]
        
        # Gráfico de barras com a pontuação final
        st.write('Pontuação Final por Híbrido:')
        fig_decision = go.Figure(go.Bar(
            x=prod_media_norm['Híbrido'],
            y=prod_media_norm['Pontuação Final'],
            text=prod_media_norm['Pontuação Final'].round(2),
            textposition='outside',
            marker_color=colors_decision  # Aplicando as cores
        ))
        fig_decision.update_layout(title='Pontuação Final por Híbrido',
                                   xaxis_title='Híbrido',
                                   yaxis_title='Pontuação Final',
                                   bargap=0.2)
        st.plotly_chart(fig_decision, use_container_width=True)

    with tab5:
        st.write('Comparação de Produtividade entre Híbridos:')
        col1, col2, col3 = st.columns([3, 1, 3])

        hibridos_head = ['9504VIP3', '9801VIP3', '9703TG', '9602VIP3', '9705VIP3']
        hibridos_check = df[~df['hibrido'].isin(hibridos_head)]['hibrido'].unique()

        with col1:
            hibrido_head = st.selectbox('Head', options=hibridos_head, key='head_hibrido')
        
        with col2:
            st.markdown("<h3 style='text-align: center;'>Versus</h3>", unsafe_allow_html=True)
        
        with col3:
            hibrido_check = st.selectbox('Check', options=hibridos_check, key='check_hibrido')

        # Filtros adicionais para Head to Head
        st.write("Filtros Head to Head:")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            estado_filter = st.selectbox('Filtrar por Estado', options=['Todos'] + list(df['estado'].unique()))

        with col2:
            conjuntaGeral_h2h_filter = st.selectbox('Filtrar por ConjuntaGeral', options=['Todos'] + list(df['conjuntaGeral'].unique()), key='conjuntaGeral_h2h')

        with col3:
            macroRegiao_h2h_filter = st.selectbox('Filtrar por MacroRegião', options=['Todos'] + list(df['macroRegiao'].unique()), key='macroRegiao_h2h')

        with col4:
            microRegiao_h2h_filter = st.selectbox('Filtrar por MicroRegião', options=['Todos'] + list(df['microRegiao'].unique()), key='microRegiao_h2h')

        # Filtrando os dados para os híbridos selecionados e aplicando filtros adicionais
        df_head = df[df['hibrido'] == hibrido_head]
        df_check = df[df['hibrido'] == hibrido_check]

        if estado_filter != 'Todos':
            df_head = df_head[df_head['estado'] == estado_filter]
            df_check = df_check[df_check['estado'] == estado_filter]
        if conjuntaGeral_h2h_filter != 'Todos':
            df_head = df_head[df_head['conjuntaGeral'] == conjuntaGeral_h2h_filter]
            df_check = df_check[df_check['conjuntaGeral'] == conjuntaGeral_h2h_filter]
        if macroRegiao_h2h_filter != 'Todos':
            df_head = df_head[df_head['macroRegiao'] == macroRegiao_h2h_filter]
            df_check = df_check[df_check['macroRegiao'] == macroRegiao_h2h_filter]
        if microRegiao_h2h_filter != 'Todos':
            df_head = df_head[df_head['microRegiao'] == microRegiao_h2h_filter]
            df_check = df_check[df_check['microRegiao'] == microRegiao_h2h_filter]

        df_head = df_head[['cidadeUF', 'prod_media_corr_sc']]
        df_check = df_check[['cidadeUF', 'prod_media_corr_sc']]

        # Calculando a média de produtividade por município para cada híbrido
        df_head_mean = df_head.groupby('cidadeUF')['prod_media_corr_sc'].mean().reset_index()
        df_check_mean = df_check.groupby('cidadeUF')['prod_media_corr_sc'].mean().reset_index()

        # Renomeando as colunas para facilitar a junção
        df_head_mean.columns = ['cidadeUF', 'prod_head_mean']
        df_check_mean.columns = ['cidadeUF', 'prod_check_mean']

        # Mesclando os dados com base na cidadeUF
        df_comparison = pd.merge(df_head_mean, df_check_mean, on='cidadeUF', how='inner')

        # Calculando a diferença média de produtividade
        df_comparison['Diferença'] = df_comparison['prod_head_mean'] - df_comparison['prod_check_mean']

        # Definindo as cores das barras com base na diferença de produtividade
        colors_comparison = ['green' if val > 0 else 'red' for val in df_comparison['Diferença']]

        # Exibindo o gráfico de barras com a diferença média de produtividade
        fig_comparison = go.Figure()
        fig_comparison.add_trace(go.Bar(
            x=df_comparison['cidadeUF'],
            y=df_comparison['Diferença'],
            marker_color=colors_comparison,
            text=df_comparison['Diferença'].round(1),
            textposition='outside'
        ))

        fig_comparison.update_layout(
            title=f'Diferença de Produtividade Média entre {hibrido_head} e {hibrido_check} por Local',
            xaxis_title='Local (cidadeUF)',
            yaxis_title='Diferença de Produtividade Média (sc)',
            bargap=0.2,
            showlegend=False
        )

        st.plotly_chart(fig_comparison, use_container_width=True)

else:
    st.write("Por favor, carregue um arquivo Excel.")
