import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.express as px
import base64
import io
import plotly.graph_objects as go

# Inicializa a aplicação Dash
app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server  # Importante para o Render

# Layout principal
app.layout = html.Div([
    # Header com logo
    html.Div([
        html.Div([
            html.Img(src='assets/multiplic-logo.png', alt='Multiplic Telecom'),
        ], className='logo-container'),
    ], className='header'),
    
    # Container principal
    html.Div([
        # Título com robô
        html.Div([
            html.Img(src='assets/robot-icon.png', className='robot-icon'),
            html.H1('Sistema de Análise Multiplic'),
        ], className='title-container'),
        
        # Navegação
        dcc.Location(id='url', refresh=False),
        html.Div([
            html.A('Upload de Dados', href='/upload', className='nav-link'),
            html.A('Dashboard', href='/dashboard', className='nav-link'),
        ], className='nav-links'),
        
        # Conteúdo da página
        html.Div(id='page-content', className='content-container')
    ], className='main-container')
])

# Layout da página de upload
def create_upload_layout():
    return html.Div([
        html.H2('Upload de Planilha', className='upload-title'),
        html.Div([
            dcc.Upload(
                id='upload-data',
                children=html.Div([
                    'Arraste e solte ou ',
                    html.A('Selecione uma Planilha')
                ]),
                className='upload-box'
            ),
            html.Div(id='output-data-upload'),
        ], className='upload-area')
    ])

# Layout da página de dashboard
def create_dashboard_layout():
    return html.Div([
        html.H2('Dashboard', className='dashboard-title'),
        html.Div([
            html.Div([
                dcc.Graph(id='grafico1', figure={}),
            ], className='graph-container six columns'),
            html.Div([
                dcc.Graph(id='grafico2', figure={}),
            ], className='graph-container six columns'),
        ], className='row'),
        html.Div([
            dcc.Graph(id='grafico3', figure={}),
        ], className='graph-container'),
    ], className='dashboard-container')

# Callback para atualizar as páginas
@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
def display_page(pathname):
    print(f"Pathname atual: {pathname}")  # Debug
    if pathname == '/upload':
        return create_upload_layout()
    elif pathname == '/dashboard':
        return create_dashboard_layout()
    else:
        return create_upload_layout()  # Página padrão

# Callback para processar o upload do arquivo
@app.callback(
    Output('output-data-upload', 'children'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename')
)
def update_output(contents, filename):
    if contents is not None:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        
        try:
            if 'csv' in filename:
                df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
            elif 'xls' in filename:
                df = pd.read_excel(io.BytesIO(decoded))
            
            df.to_csv('temp_data.csv', index=False)
            
            return html.Div([
                html.H5(f'Arquivo carregado: {filename}'),
                html.H6('Dados carregados com sucesso!')
            ], className='message-success')
        except Exception as e:
            return html.Div([
                'Erro ao processar o arquivo.'
            ], className='message-error')

# Callback para atualizar os gráficos
@app.callback(
    [Output('grafico1', 'figure'),
     Output('grafico2', 'figure'),
     Output('grafico3', 'figure')],
    [Input('url', 'pathname')]
)
def update_graphs(pathname):
    if pathname == '/dashboard':
        try:
            df = pd.read_csv('temp_data.csv', index_col=0)
            
            # Função para converter tempo em minutos
            def convert_to_minutes(time_str):
                # Remove 'min' do final e qualquer espaço
                time_str = time_str.replace('min', '').strip()
                parts = time_str.split(':')
                try:
                    if len(parts) > 1:
                        return float(parts[0]) + float(parts[1])/60
                    return float(parts[0])
                except ValueError:
                    return 0  # Retorna 0 se houver erro na conversão
            
            # Cria novo DataFrame com valores em minutos
            df_minutes = pd.DataFrame()
            df_minutes['Call'] = df['Call'].apply(convert_to_minutes)
            df_minutes['whatsApp'] = df['whatsApp'].apply(convert_to_minutes)
            
            # Gráfico 1: Tempo médio de atendimento (Barras)
            fig1 = go.Figure()
            fig1.add_trace(go.Bar(
                name='Call',
                y=['Tempo'],
                x=[df_minutes.iloc[0]['Call']],
                orientation='h',
                marker_color='#00B2E3'
            ))
            fig1.add_trace(go.Bar(
                name='WhatsApp',
                y=['Tempo'],
                x=[df_minutes.iloc[0]['whatsApp']],
                orientation='h',
                marker_color='#00E396'
            ))
            
            fig1.update_layout(
                title='Tempo Médio de Atendimento',
                xaxis_title='Minutos',
                barmode='group',
                height=400
            )
            
            # Gráfico 2: Tempo médio para aceitar
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(
                name='Call',
                y=['Tempo'],
                x=[df_minutes.iloc[1]['Call']],
                orientation='h',
                marker_color='#00B2E3'
            ))
            fig2.add_trace(go.Bar(
                name='WhatsApp',
                y=['Tempo'],
                x=[df_minutes.iloc[1]['whatsApp']],
                orientation='h',
                marker_color='#00E396'
            ))
            
            fig2.update_layout(
                title='Tempo Médio para Aceitar',
                xaxis_title='Minutos',
                barmode='group',
                height=400
            )
            
            # Gráfico 3: Tempo médio para fechar
            fig3 = go.Figure()
            fig3.add_trace(go.Indicator(
                mode="gauge+number",
                value=df_minutes.iloc[2]['Call'],
                title={'text': "Call"},
                domain={'x': [0, 0.45], 'y': [0, 1]},
                number={'suffix': "min"},
                gauge={
                    'axis': {'range': [None, 30]},
                    'bar': {'color': "#00B2E3"}
                }
            ))
            
            fig3.add_trace(go.Indicator(
                mode="gauge+number",
                value=df_minutes.iloc[2]['whatsApp'],
                title={'text': "WhatsApp"},
                domain={'x': [0.55, 1], 'y': [0, 1]},
                number={'suffix': "min"},
                gauge={
                    'axis': {'range': [None, 30]},
                    'bar': {'color': "#00E396"}
                }
            ))
            
            fig3.update_layout(
                title='Tempo Médio para Fechar Atendimento',
                height=400
            )

            # Personalização comum para todos os gráficos
            for fig in [fig1, fig2, fig3]:
                fig.update_layout(
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    font={'size': 14, 'color': '#2c3e50'},
                    showlegend=True,
                    margin=dict(t=50, l=50, r=30, b=50)
                )
                
                # Adiciona formatação de texto para barras
                if isinstance(fig, go.Figure) and len(fig.data) > 0 and isinstance(fig.data[0], go.Bar):
                    for trace in fig.data:
                        trace.text = [f"{x:.1f}min" for x in trace.x]
                        trace.textposition = 'outside'

            return fig1, fig2, fig3
        except Exception as e:
            print(f"Erro ao gerar gráficos: {e}")
            # Cria gráficos vazios em caso de erro
            empty_fig = go.Figure()
            return empty_fig, empty_fig, empty_fig
    
    # Retorna gráficos vazios se não estiver na página de dashboard
    empty_fig = go.Figure()
    return empty_fig, empty_fig, empty_fig

if __name__ == '__main__':
    app.run_server(debug=False)
