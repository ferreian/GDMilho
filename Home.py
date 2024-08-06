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
        'estado': 'UF'
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

    selected_hibridos = st.sidebar.multiselect('Selecione os Híbridos', options=hibrido_options, default=[])
    selected_municipio = st.sidebar.selectbox('Selecione o Município', ['Todos'] + list(municipio_options))
    selected_uf = st.sidebar.multiselect('Selecione a UF', options=uf_options, default=[])
    selected_ensaio = st.sidebar.selectbox('Selecione o Ensaio', ['Todos'] + list(ensaio_options))

    # Filtrar o DataFrame com base nas seleções
    df_filtered = df.copy()
    if selected_hibridos:
        df_filtered = df_filtered[df_filtered['Híbridos'].isin(selected_hibridos)]
    if selected_municipio != 'Todos':
        df_filtered = df_filtered[df_filtered['Município'] == selected_municipio]
    if selected_uf:
        df_filtered = df_filtered[df_filtered['UF'].isin(selected_uf)]
    if selected_ensaio != 'Todos':
        df_filtered = df_filtered[df_filtered['Ensaio'] == selected_ensaio]

    # Criar tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Dados Carregados", "Yield", "LxL e Vitrines", "Densidades", "População vs Rendimento"])

    with tab1:
        st.write("Dados do Excel carregados:")
        st.dataframe(df_filtered, width=1500)  # Ajuste o valor de width conforme necessário

    with tab2:
        # Selecionar as colunas especificadas
        cols = [
            'Híbridos', '% Acamadas', '% Quebradas', '% Dominadas', 'Alt Planta', 
            'Alt Espiga', 'Pop Final', 'Colheita', 'Produção (sc/há)', 'Município', 
            'UF', 'Altitude', 'Ensaio', 'Época', 'Investimento', 'PR Maior'
        ]
        if all(col in df_filtered.columns for col in cols):
            df_yield = df_filtered[cols]
            st.write("Yield:")
            st.dataframe(df_yield, width=1500)  # Ajuste o valor de width conforme necessário
        else:
            st.write("O arquivo Excel não contém todas as colunas especificadas.")
    
    with tab3:
        # Filtrar dados onde Ensaio não contém "densidade"
        if 'Ensaio' in df_filtered.columns:
            df_lxl_vitrines = df_filtered[~df_filtered['Ensaio'].str.contains('densidade', case=False, na=False)]
            
            # Reorganizar colunas para colocar PR Maior ao lado de Produção (sc/há)
            cols_order = [
                'Híbridos', '% Acamadas', '% Quebradas', '% Dominadas', 'Alt Planta', 
                'Alt Espiga', 'Pop Final', 'Colheita', 'Produção (sc/há)', 'PR Maior', 'PR Maior Label', 'Município', 
                'UF', 'Altitude', 'Ensaio', 'Época', 'Investimento'
            ]
            df_lxl_vitrines = df_lxl_vitrines[cols_order]
            
            st.write("LxL e Vitrines:")
            st.dataframe(df_lxl_vitrines, width=1500)  # Ajuste o valor de width conforme necessário
            
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

                # Agrupar dados por UF e Híbridos para evitar duplicados
                grouped_data = df_lxl_vitrines.groupby(['UF', 'Híbridos'])['PR Maior'].mean().reset_index()
                grouped_data['PR Maior Label'] = grouped_data['PR Maior'].round(1).astype(str)
                
                # Criar gráfico de calor para PR Maior com UF no eixo y e Híbridos no eixo x
                heatmap_data = grouped_data.pivot(index='UF', columns='Híbridos', values='PR Maior')
                heatmap_data_labels = grouped_data.pivot(index='UF', columns='Híbridos', values='PR Maior Label')
                fig2 = px.imshow(heatmap_data, aspect="auto", color_continuous_scale=['lightcoral', 'lightgreen', 'darkgreen'], 
                                 labels={'color': 'PR Maior'}, title='Mapa de Calor da Produção Relativa (PR Maior)')
                fig2.update_traces(text=heatmap_data_labels, texttemplate="%{text}", textfont_color='white')
                st.plotly_chart(fig2)

                # Filtrar dados para os híbridos específicos
                selected_hybrids = ['9801 VIP3', '9705 VIP3', '9504 VIP3', 'SZE6192 VIP3', 'K1627 VIP3']
                df_selected_hybrids = df_filtered[df_filtered['Híbridos'].isin(selected_hybrids)]
                
                # Agrupar dados por UF e Híbridos para evitar duplicados
                grouped_data_selected = df_selected_hybrids.groupby(['UF', 'Híbridos'])['PR Maior'].mean().reset_index()
                grouped_data_selected['PR Maior Label'] = grouped_data_selected['PR Maior'].round(1).astype(str)
                
                # Criar gráfico de calor para PR Maior com UF no eixo y e Híbridos no eixo x
                heatmap_data_selected = grouped_data_selected.pivot(index='UF', columns='Híbridos', values='PR Maior')
                heatmap_data_labels_selected = grouped_data_selected.pivot(index='UF', columns='Híbridos', values='PR Maior Label')
                fig3 = px.imshow(heatmap_data_selected, aspect="auto", color_continuous_scale=['lightcoral', 'lightgreen', 'darkgreen'], 
                                 labels={'color': 'PR Maior'}, title='Mapa de Calor da Produção Relativa (PR Maior) para Híbridos Selecionados')
                fig3.update_traces(text=heatmap_data_labels_selected, texttemplate="%{text}", textfont_color='white')
                st.plotly_chart(fig3)

            else:
                st.write("A coluna 'Produção (sc/há)' não está presente no DataFrame.")
        else:
            st.write("A coluna 'Ensaio' não está presente no arquivo Excel.")
    
    with tab4:
        # Filtrar dados onde Ensaio contém "densidade"
        if 'Ensaio' in df_filtered.columns:
            df_densidades = df_filtered[df_filtered['Ensaio'].str.contains('densidade', case=False, na=False)]
            st.write("Densidades:")
            st.dataframe(df_densidades, width=1500)  # Ajuste o valor de width conforme necessário
        else:
            st.write("A coluna 'Ensaio' não está presente no arquivo Excel.")
    
    with tab5:
        st.write("População vs Rendimento:")
        
        # Criar box plot para População Final (Pop Final) no eixo x e Produção (sc/há) no eixo y
        fig4 = px.box(df_filtered, x='Pop Final', y='Produção (sc/há)', color='Híbridos',
                      title='Box Plot de População Final vs Produção (sc/há)',
                      labels={'Pop Final': 'População Final', 'Produção (sc/há)': 'Produção (sc/há)'})
        
        st.plotly_chart(fig4)
