import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configurar layout da página para modo wide
st.set_page_config(layout="wide")

# Título do aplicativo
st.title('Dados GD Milho')

# Carregar o arquivo Excel na barra lateral
st.sidebar.title('Opções')
uploaded_file = st.sidebar.file_uploader("Escolha um arquivo Excel", type=["xlsx", "xls"])

if uploaded_file is not None:
    # Ler o arquivo Excel
    df = pd.read_excel(uploaded_file)
    
    # Renomear colunas
    column_mapping = {
        'hy': 'Híbridos',
        'ac': '% Acamadas',
        'qb': '% Quebradas',
        'dm': '% Dominadas',
        'alt': 'Alt Planta',
        'ahe': 'Alt Espiga',
        'stdf': 'Pop Final',
        'data_colheita': 'Colheita',
        'yield_sc_ha': 'Produção (sc/há)',
        'altitude': 'Altitude',
        'tipo_ensaio': 'Ensaio',
        'epoca': 'Época',
        'investimento': 'Investimento',
        'municipio': 'Município',
        'estado': 'UF',
        'time': 'Time',
        'u': 'Umidade'  # Adicionando a coluna umidade
    }
    df = df.rename(columns=column_mapping)
    
    # Calcular o maior valor de produção em todo o DataFrame
    max_production_overall = df['Produção (sc/há)'].max()
    
    # Criar a nova coluna PR Maior
    df['PR Maior'] = (df['Produção (sc/há)'] / max_production_overall) * 100
    
    # Criar uma coluna separada para rótulos formatados
    df['PR Maior Label'] = df['PR Maior'].round(1).astype(str)
    
    # Criar filtros na barra lateral
    hibrido_options = df['Híbridos'].unique()
    municipio_options = df['Município'].unique()
    uf_options = df['UF'].unique()
    ensaio_options = df['Ensaio'].unique()
    time_options = df['Time'].unique()

    selected_hibridos = st.sidebar.multiselect('Selecione os Híbridos', options=hibrido_options, default=[])
    selected_municipio = st.sidebar.selectbox('Selecione o Município', ['Todos'] + list(municipio_options))
    selected_uf = st.sidebar.multiselect('Selecione a UF', options=uf_options, default=[])
    selected_ensaio = st.sidebar.multiselect('Selecione o Ensaio', options=ensaio_options, default=[])
    selected_time = st.sidebar.multiselect('Selecione o Time', options=time_options, default=[])

    # Filtrar o DataFrame com base nas seleções
    df_filtered = df.copy()
    if selected_hibridos:
        df_filtered = df_filtered[df_filtered['Híbridos'].isin(selected_hibridos)]
    if selected_municipio != 'Todos':
        df_filtered = df_filtered[df_filtered['Município'] == selected_municipio]
    if selected_uf:
        df_filtered = df_filtered[df_filtered['UF'].isin(selected_uf)]
    if selected_ensaio:
        df_filtered = df_filtered[df_filtered['Ensaio'].isin(selected_ensaio)]
    if selected_time:
        df_filtered = df_filtered[df_filtered['Time'].isin(selected_time)]

    # Criar tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Dados Carregados", "Yield", "LxL e Vitrines", "População vs Rendimento", "Head to Head", "Interpolação"])

    with tab1:
        st.write("Dados do Excel carregados:")
        st.dataframe(df_filtered, width=1500)

    with tab2:
        # Selecionar as colunas especificadas
        cols = [
            'Híbridos', '% Acamadas', '% Quebradas', '% Dominadas', 'Alt Planta', 
            'Alt Espiga', 'Pop Final', 'Colheita', 'Produção (sc/há)', 'Município', 
            'UF', 'Altitude', 'Ensaio', 'Época', 'Investimento', 'PR Maior', 'Time'
        ]
        if all(col in df_filtered.columns for col in cols):
            df_yield = df_filtered[cols]
            st.write("Yield:")
            st.dataframe(df_yield, width=1500)
        else:
            st.write("O arquivo Excel não contém todas as colunas especificadas.")
    
    with tab3:
        # Reorganizar colunas para colocar PR Maior ao lado de Produção (sc/há)
        cols_order = [
            'Híbridos', '% Acamadas', '% Quebradas', '% Dominadas', 'Alt Planta', 
            'Alt Espiga', 'Pop Final', 'Colheita', 'Produção (sc/há)', 'PR Maior', 'PR Maior Label', 'Município', 
            'UF', 'Altitude', 'Ensaio', 'Época', 'Investimento', 'Time', 'Umidade'
        ]
        df_lxl_vitrines = df_filtered[cols_order]
        
        st.write("LxL e Vitrines:")
        st.dataframe(df_lxl_vitrines, width=1500)
        
        # Gerar sumário das principais estatísticas descritivas
        if 'Produção (sc/há)' in df_lxl_vitrines.columns:
            summary_stats = df_lxl_vitrines['Produção (sc/há)'].describe()

            # Calcular estatísticas descritivas para os híbridos específicos
            hybrids = ['9801 VIP3', '9705 VIP3', '9504 VIP3', 'K1627 VIP3', 'SZE6192 VIP3']
            stats_hybrids = {hybrid: df_lxl_vitrines[df_lxl_vitrines['Híbridos'] == hybrid]['Produção (sc/há)'].describe() for hybrid in hybrids}
            
            # Combinar as estatísticas gerais com as dos híbridos específicos
            combined_stats = summary_stats.to_frame(name='Geral')
            for hybrid, stats in stats_hybrids.items():
                combined_stats[hybrid] = stats
            
            st.write("Sumário das Principais Estatísticas Descritivas:")
            st.dataframe(combined_stats)
            
            # Calcular valores médios por híbrido para Produção (sc/há)
            mean_production_by_hybrid = df_lxl_vitrines.groupby('Híbridos')['Produção (sc/há)'].mean().reset_index()
            mean_production_by_hybrid = mean_production_by_hybrid.sort_values(by='Produção (sc/há)', ascending=False)
            
            # Definir cores para os híbridos específicos
            colors = {
                '9705 VIP3': 'darkblue',
                '9801 VIP3': 'darkblue',
                '9504 VIP3': 'darkblue',
                'K1627 VIP3': '#FF8C00',  # Laranja escuro
                'SZE6192 VIP3': 'green'
            }
            mean_production_by_hybrid['Cor'] = mean_production_by_hybrid['Híbridos'].map(colors).fillna('gray')
            
            # Adicionar rótulos sem a diferença para o valor anterior
            mean_production_by_hybrid['Label'] = mean_production_by_hybrid['Produção (sc/há)'].round(1).astype(str)

            # Calcular a média de produção
            media_producao = mean_production_by_hybrid['Produção (sc/há)'].mean()

            # Criar gráfico de barras para Produção (sc/há)
            fig1 = px.bar(mean_production_by_hybrid, x='Híbridos', y='Produção (sc/há)', 
                          title='Produção Média por Híbrido', 
                          labels={'Híbridos': 'Híbridos', 'Produção (sc/há)': 'Produção Média (sc/há)'},
                          color='Cor',
                          color_discrete_map='identity',
                          text='Label')
            
            # Configurar rótulos de dados em branco
            fig1.update_traces(textfont_color='white')
            
            # Adicionar linha tracejada da média em vermelho
            fig1.add_trace(go.Scatter(
                x=mean_production_by_hybrid['Híbridos'],
                y=[media_producao] * len(mean_production_by_hybrid),
                mode="lines",
                name="Média",
                line=dict(color="red", dash="dash")
            ))

            # Adicionar anotação para a média
            fig1.add_annotation(
                x=mean_production_by_hybrid['Híbridos'].iloc[-1],
                y=media_producao,
                text=f"Média: {media_producao:.1f}",
                showarrow=True,
                arrowhead=1,
                ax=0,
                ay=-40
            )
            
            st.plotly_chart(fig1)

            # Agrupar dados por UF, Híbridos e Time para evitar duplicados e calcular a média
            grouped_data = df_lxl_vitrines.groupby(['UF', 'Híbridos', 'Time'], as_index=False)['PR Maior'].mean()
            grouped_data['PR Maior Label'] = grouped_data['PR Maior'].round(1).astype(str)
            
            # Criar gráfico de calor para PR Maior com UF no eixo y e Híbridos no eixo x
            heatmap_data = grouped_data.pivot_table(index='UF', columns='Híbridos', values='PR Maior', aggfunc='mean')
            heatmap_data_labels = grouped_data.pivot_table(index='UF', columns='Híbridos', values='PR Maior Label', aggfunc='first')
            fig2 = px.imshow(heatmap_data, aspect="auto", color_continuous_scale=['lightcoral', 'lightgreen', 'darkgreen'], 
                             labels={'color': 'PR Maior'}, title='Mapa de Calor da Produção Relativa (PR Maior)')
            fig2.update_traces(text=heatmap_data_labels, texttemplate="%{text}", textfont_color='white')
            st.plotly_chart(fig2)

            # Filtrar dados para os híbridos específicos
            selected_hybrids = ['9801 VIP3', '9705 VIP3', '9504 VIP3', 'SZE6192 VIP3', 'K1627 VIP3']
            df_selected_hybrids = df_filtered[df_filtered['Híbridos'].isin(selected_hybrids)]
            
            # Agrupar dados por UF, Híbridos e Time para evitar duplicados e calcular a média
            grouped_data_selected = df_selected_hybrids.groupby(['UF', 'Híbridos', 'Time'], as_index=False)['PR Maior'].mean()
            grouped_data_selected['PR Maior Label'] = grouped_data_selected['PR Maior'].round(1).astype(str)
            
            # Criar gráfico de calor para PR Maior com UF no eixo y e Híbridos no eixo x
            heatmap_data_selected = grouped_data_selected.pivot_table(index='UF', columns='Híbridos', values='PR Maior', aggfunc='mean')
            heatmap_data_labels_selected = grouped_data_selected.pivot_table(index='UF', columns='Híbridos', values='PR Maior Label', aggfunc='first')
            fig3 = px.imshow(heatmap_data_selected, aspect="auto", color_continuous_scale=['lightcoral', 'lightgreen', 'darkgreen'], 
                             labels={'color': 'PR Maior'}, title='Mapa de Calor da Produção Relativa (PR Maior) para Híbridos Selecionados')
            fig3.update_traces(text=heatmap_data_labels_selected, texttemplate="%{text}", textfont_color='white')
            st.plotly_chart(fig3)

        else:
            st.write("A coluna 'Produção (sc/há)' não está presente no DataFrame.")
    
    with tab4:
        st.write("População vs Rendimento:")
        
        # Garantir que o valor máximo da Pop Final seja maior que 85000
        max_pop_final = df_filtered['Pop Final'].max()
        if max_pop_final <= 85000:
            max_pop_final = 85001
        
        # Categorizar a população em 5 faixas
        pop_bins = [0, 55000, 65000, 75000, 85000, max_pop_final]
        pop_labels = ['Menor que 55000', '55001 a 65000', '65001 a 75000', '75001 a 85000', 'Maior que 85000']
        df_filtered['População Categoria'] = pd.cut(df_filtered['Pop Final'], bins=pop_bins, labels=pop_labels, include_lowest=True)
        
        # Transformar a coluna em uma categoria ordenada explicitamente
        df_filtered['População Categoria'] = pd.Categorical(df_filtered['População Categoria'], categories=pop_labels, ordered=True)

        # Criar box plot para População Categoria no eixo x e Produção (sc/há) no eixo y
        fig4 = go.Figure()

        for hibrido in df_filtered['Híbridos'].unique():
            df_hibrido = df_filtered[df_filtered['Híbridos'] == hibrido]
            fig4.add_trace(go.Box(
                y=df_hibrido['Produção (sc/há)'],
                x=df_hibrido['População Categoria'],
                name=hibrido,
                marker_color='white'
            ))
            # Adicionar pontos indicando a média
            mean_values = df_hibrido.groupby('População Categoria')['Produção (sc/há)'].mean().reset_index()
            fig4.add_trace(go.Scatter(
                x=mean_values['População Categoria'],
                y=mean_values['Produção (sc/há)'],
                mode='markers+text',
                marker=dict(color='black', size=10),
                text=mean_values['Produção (sc/há)'].round(1).astype(str),
                textposition="top center",
                name=f'Média {hibrido}'
            ))

            # Adicionar pontos indicando a mediana
            median_values = df_hibrido.groupby('População Categoria')['Produção (sc/há)'].median().reset_index()
            fig4.add_trace(go.Scatter(
                x=median_values['População Categoria'],
                y=median_values['Produção (sc/há)'],
                mode='markers+text',
                marker=dict(color='red', size=10),
                text=median_values['Produção (sc/há)'].round(1).astype(str),
                textposition="bottom center",
                name=f'Mediana {hibrido}'
            ))

        fig4.update_layout(
            title='Box Plot de Produção por Faixa de População',
            xaxis_title='Faixa de População',
            yaxis_title='Produção (sc/há)',
            showlegend=True,
            boxmode='group'  # Garantir que os box plots sejam agrupados por categoria de população
        )

        st.plotly_chart(fig4)
    
    with tab5:
        st.write("Head to Head")
        
        col1, col2, col3 = st.columns([1, 0.1, 1])
        
        head_options = ['9801 VIP3', '9705 VIP3', '9504 VIP3']
        
        with col1:
            selected_head_hibrido = st.selectbox('Selecione o Híbrido para Head', options=head_options)
        
        with col2:
            st.markdown("<h1 style='text-align: center;'>VS</h1>", unsafe_allow_html=True)
        
        with col3:
            selected_check_hibrido = st.selectbox('Selecione o Híbrido para Check', options=hibrido_options)
        
        if selected_head_hibrido and selected_check_hibrido:
            df_head = df_filtered[df_filtered['Híbridos'] == selected_head_hibrido]
            df_check = df_filtered[df_filtered['Híbridos'] == selected_check_hibrido]
            
            # Calcular a diferença média de produção por município
            df_head_avg = df_head.groupby('Município')['Produção (sc/há)'].mean().reset_index()
            df_check_avg = df_check.groupby('Município')['Produção (sc/há)'].mean().reset_index()
            
            df_comparison = pd.merge(df_head_avg, df_check_avg, on='Município', suffixes=('_head', '_check'))
            df_comparison['Diferença'] = df_comparison['Produção (sc/há)_head'] - df_comparison['Produção (sc/há)_check']
            
            # Adicionar coluna para cores
            df_comparison['Cor'] = df_comparison['Diferença'].apply(lambda x: 'green' if x > 1 else ('red' if x < -1 else 'orange'))
            
            # Ajustar rótulo para uma casa decimal
            df_comparison['Diferença Label'] = df_comparison['Diferença'].round(1).astype(str)

            # Contar vitórias, derrotas e empates
            vitorias = df_comparison[df_comparison['Diferença'] > 1].shape[0]
            derrotas = df_comparison[df_comparison['Diferença'] < -1].shape[0]
            empates = df_comparison[(df_comparison['Diferença'] <= 1) & (df_comparison['Diferença'] >= -1)].shape[0]

            # Calcular a maior vitória, a média das vitórias, a maior derrota e a média das derrotas
            maior_vitoria = df_comparison[df_comparison['Diferença'] > 1]['Diferença'].max()
            media_vitorias = df_comparison[df_comparison['Diferença'] > 1]['Diferença'].mean()
            maior_derrota = df_comparison[df_comparison['Diferença'] < -1]['Diferença'].min()
            media_derrotas = df_comparison[df_comparison['Diferença'] < -1]['Diferença'].mean()
            
            # Formatar métricas para exibir "-" quando não houver valores
            maior_vitoria = round(maior_vitoria, 1) if not pd.isna(maior_vitoria) else "-"
            media_vitorias = round(media_vitorias, 1) if not pd.isna(media_vitorias) else "-"
            maior_derrota = round(maior_derrota, 1) if not pd.isna(maior_derrota) else "-"
            media_derrotas = round(media_derrotas, 1) if not pd.isna(media_derrotas) else "-"
            
            # Calcular o total de locais
            total_locais = df_comparison.shape[0]
            
            # Mostrar cards
            col4, col5, col6, col7 = st.columns(4)
            with col4:
                st.metric(label="Número de Vitórias", value=vitorias)
                st.metric(label="Maior Vitória", value=maior_vitoria)
                st.metric(label="Média das Vitórias", value=media_vitorias)
            with col5:
                st.metric(label="Número de Empates", value=empates)
            with col6:
                st.metric(label="Número de Derrotas", value=derrotas)
                st.metric(label="Maior Derrota", value=maior_derrota)
                st.metric(label="Média das Derrotas", value=media_derrotas)
            with col7:
                st.metric(label="Total de Locais", value=total_locais)
            
            # Mostrar gráfico
            fig_head = px.bar(df_comparison, x='Município', y='Diferença', 
                              title='Diferença de Produção por Local',
                              labels={'Diferença': 'Diferença de Produção (sc/há)', 'Município': 'Município'},
                              color='Cor',
                              color_discrete_map={'green': 'green', 'red': 'red', 'orange': 'orange'},
                              text='Diferença Label')
            
            fig_head.update_layout(showlegend=False)  # Remover a legenda
            
            st.plotly_chart(fig_head)

    with tab6:
        st.write("Interpolação")
        
        # Calcular a média de produção e umidade para cada híbrido
        grouped_interp = df_lxl_vitrines.groupby('Híbridos').agg({'Produção (sc/há)': 'mean', 'Umidade': 'mean'}).reset_index()
        
        # Criar scatter plot
        fig_interp = px.scatter(grouped_interp, x='Umidade', y='Produção (sc/há)', text='Híbridos',
                                title='Produção Média por Umidade Média',
                                labels={'Umidade': 'Umidade Média', 'Produção (sc/há)': 'Produção Média (sc/há)'},
                                size_max=10)
        fig_interp.update_traces(textposition='top center')

        st.plotly_chart(fig_interp)
