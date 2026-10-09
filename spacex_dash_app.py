from pathlib import Path
import pandas as pd
import plotly.express as px
from dash import Dash,html,dcc,Input,Output
ROOT=Path(__file__).resolve().parent
data=pd.read_csv(ROOT/'data/spacex_launch_dash.csv')
app=Dash(__name__)
app.layout=html.Div([html.H1('SpaceX Launch Records'),html.P('IBM historical dashboard dataset: 56 launches. Class 1 denotes successful outcome in this snapshot.'),dcc.Dropdown(id='site',options=[{'label':'All sites','value':'ALL'}]+[{'label':s,'value':s} for s in sorted(data['Launch Site'].unique())],value='ALL',clearable=False),dcc.Graph(id='pie'),html.Label('Payload range (kg)'),dcc.RangeSlider(id='payload',min=0,max=float(data['Payload Mass (kg)'].max()),step=100,value=[0,float(data['Payload Mass (kg)'].max())],marks={0:'0',5000:'5000',10000:'10000'}),dcc.Graph(id='scatter')],style={'fontFamily':'Arial','maxWidth':'1100px','margin':'auto'})
@app.callback(Output('pie','figure'),Output('scatter','figure'),Input('site','value'),Input('payload','value'))
def charts(site,payload):
    s=data if site=='ALL' else data[data['Launch Site']==site]
    if site=='ALL':
        counts=s[s['class']==1].groupby('Launch Site').size().reset_index(name='Successful launches')
        pie=px.pie(counts,names='Launch Site',values='Successful launches',title='Share of successful launches by site (counts, not success rates)')
    else:
        counts=s.groupby('class').size().reset_index(name='Launches');counts['Outcome']=counts['class'].map({0:'Class 0',1:'Class 1'})
        pie=px.pie(counts,names='Outcome',values='Launches',title=site+' outcome proportions')
    s=s[s['Payload Mass (kg)'].between(*payload)].copy();s['Outcome']=s['class'].astype(str)
    scatter=px.scatter(s,x='Payload Mass (kg)',y='class',color='Booster Version Category',hover_data=['Launch Site','Flight Number'],title='Payload versus launch outcome',labels={'class':'Class'})
    return pie,scatter
if __name__=='__main__':app.run(debug=False,host='127.0.0.1',port=8050)
