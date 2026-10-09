"""Run reproducible IBM SpaceX analysis from the project root."""
from pathlib import Path
import json, sqlite3, hashlib, urllib.request, io
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split, StratifiedKFold, GridSearchCV
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix, ConfusionMatrixDisplay
ROOT=Path(__file__).resolve().parent
DATA=ROOT/'data'; OUT=ROOT/'results'; OUT.mkdir(exist_ok=True)
BASE='https://cf-courses-data.s3.us.cloud-object-storage.appdomain.cloud/IBM-DS0321EN-SkillsNetwork/datasets/'
plt.rcParams.update({'figure.figsize':(10,5),'font.size':12,'axes.spines.top':False,'axes.spines.right':False})

def collect():
    """Fetch IBM course snapshots. Existing local copies support offline reruns."""
    records=[]
    for n in ['dataset_part_1.csv','dataset_part_2.csv','spacex_launch_geo.csv','spacex_launch_dash.csv']:
        p=DATA/n
        if not p.exists(): p.write_bytes(urllib.request.urlopen(BASE+n,timeout=45).read())
        records.append({'file':n,'source':BASE+n,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'rows':len(pd.read_csv(p))})
    (OUT/'data_provenance.json').write_text(json.dumps(records,indent=2))
    return pd.DataFrame(records)

def api_collection(refresh=False):
    """Load the IBM archived SpaceX API response, separate from fixed modeling data."""
    p=DATA/'api_snapshot.json'
    if refresh or not p.exists():
        p.write_bytes(urllib.request.urlopen(BASE+'API_call_spacex_api.json',timeout=45).read())
    launches=json.loads(p.read_text())
    df=pd.json_normalize(launches)
    cols=[c for c in ['id','name','date_utc','rocket','launchpad','success','flight_number'] if c in df]
    df[cols].to_csv(OUT/'api_launch_summary.csv',index=False)
    df['Date']=df.date_utc.str[:10]
    course=pd.read_csv(DATA/'dataset_part_1.csv')
    aligned=course[['FlightNumber','Date']].merge(df[['flight_number','Date','rocket','name']],on='Date',how='left',validate='one_to_one')
    assert aligned.flight_number.notna().all(), 'Course rows do not all align to API archive'
    aligned.to_csv(OUT/'api_course_alignment.csv',index=False)
    # success is mission success, not first-stage landing. cores carry landing_success.
    return df[cols]

def scrape():
    url='https://en.wikipedia.org/wiki/List_of_Falcon_9_and_Falcon_Heavy_launches_(2010%E2%80%932019)'
    p=DATA/'wikipedia.html'
    if not p.exists(): p.write_bytes(urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=45).read())
    tables=pd.read_html(io.StringIO(p.read_text()))
    selected=[]
    for i,t in enumerate(tables):
        cols=[' '.join(map(str,c)) if isinstance(c,tuple) else str(c) for c in t.columns]
        if any('Payload' in c for c in cols) and any('Launch' in c or 'Date' in c for c in cols):
            t=t.copy();t.columns=cols;t.to_csv(OUT/f'wikipedia_table_{i:02}.csv',index=False)
            selected.append({'table':i,'rows':len(t),'columns':'; '.join(cols)})
    summary=pd.DataFrame(selected);summary.to_csv(OUT/'scraping_summary.csv',index=False)
    return summary

def wrangle():
    d=pd.read_csv(DATA/'dataset_part_1.csv')
    # Course label mapping includes unsuccessful, absent and unknown landings.
    bad={'False ASDS','False Ocean','False RTLS','None ASDS','None None'}
    d['Class']=(~d.Outcome.isin(bad)).astype(int)
    expected=pd.read_csv(DATA/'dataset_part_2.csv')
    assert d.Class.tolist()==expected.Class.tolist(), 'Label mapping differs from course reference'
    assert not d.FlightNumber.duplicated().any()
    assert len(d)==90 and set(d.Class)=={0,1}
    d['Year']=pd.to_datetime(d.Date).dt.year
    d.to_csv(OUT/'cleaned_launches.csv',index=False)
    d.isna().sum().rename('missing').to_csv(OUT/'missingness.csv')
    return d

def save(name):
    plt.tight_layout();plt.savefig(OUT/(name+'.png'),dpi=170,bbox_inches='tight');plt.close()

def eda(d):
    for x,name in [('FlightNumber','flight_site'),('PayloadMass','payload_site')]:
        fig,ax=plt.subplots()
        for label,color in [(0,'#de7854'),(1,'#168a96')]:
            s=d[d.Class==label];ax.scatter(s[x],s.LaunchSite,c=color,label=f'Class {label}',alpha=.75)
        ax.set_xlabel('Flight number' if x=='FlightNumber' else 'Payload mass (kg)');ax.set_ylabel('Launch site');ax.legend();save(name)
    for x,name in [('FlightNumber','flight_orbit'),('PayloadMass','payload_orbit')]:
        fig,ax=plt.subplots()
        for label,color in [(0,'#de7854'),(1,'#168a96')]:
            s=d[d.Class==label];ax.scatter(s[x],s.Orbit,c=color,label=f'Class {label}',alpha=.75)
        ax.set_xlabel('Flight number' if x=='FlightNumber' else 'Payload mass (kg)');ax.set_ylabel('Orbit');ax.legend();save(name)
    for col,name in [('Orbit','orbit_rate'),('LaunchSite','site_rate')]:
        s=d.groupby(col).Class.agg(['mean','count']);s.to_csv(OUT/(name+'.csv'))
        ax=s['mean'].plot.bar(color='#168a96');ax.set_ylim(0,1.1);ax.set_ylabel('Class 1 proportion')
        for i,r in enumerate(s.itertuples()):ax.text(i,r.mean+.03,f'n={r.count}',ha='center',fontsize=9)
        save(name)
    s=d.groupby('Year').Class.agg(['mean','count']);s.to_csv(OUT/'yearly.csv')
    ax=s['mean'].plot(marker='o',color='#168a96');ax.set_ylim(0,1.1);ax.set_ylabel('Class 1 proportion');ax.set_xlabel('Year');save('yearly')
    return s

def sql_analysis(d):
    con=sqlite3.connect(OUT/'spacex.sqlite');d.to_sql('launches',con,if_exists='replace',index=False)
    queries={
      'launch_sites':'SELECT DISTINCT LaunchSite FROM launches ORDER BY LaunchSite',
      'site_prefix':"SELECT FlightNumber,Date,LaunchSite FROM launches WHERE LaunchSite LIKE 'CCA%' LIMIT 5",
      'payloads':'SELECT LaunchSite,COUNT(*) AS launches,SUM(PayloadMass) AS total_kg,AVG(PayloadMass) AS mean_kg FROM launches GROUP BY LaunchSite',
      'success_rates':'SELECT LaunchSite,COUNT(*) AS launches,SUM(Class) AS class1,ROUND(AVG(Class),4) AS class1_rate FROM launches GROUP BY LaunchSite ORDER BY class1_rate DESC',
      'first_rtls':"SELECT MIN(Date) AS first_successful_RTLS FROM launches WHERE Outcome='True RTLS'",
      'asds_payload':"SELECT FlightNumber,Date,PayloadMass FROM launches WHERE Outcome='True ASDS' AND PayloadMass BETWEEN 4000 AND 6000",
      'outcome_counts':'SELECT Outcome,COUNT(*) AS launches FROM launches GROUP BY Outcome ORDER BY launches DESC',
      'max_payload':'SELECT FlightNumber,Date,Serial,PayloadMass FROM launches WHERE PayloadMass=(SELECT MAX(PayloadMass) FROM launches)',
      'yearly':'SELECT Year,COUNT(*) AS launches,SUM(Class) AS class1,ROUND(AVG(Class),4) AS class1_rate FROM launches GROUP BY Year ORDER BY Year',
      'time_window':"SELECT Outcome,COUNT(*) AS launches FROM launches WHERE Date BETWEEN '2010-06-04' AND '2017-03-20' GROUP BY Outcome ORDER BY launches DESC",
      '2015_asds_failures':"SELECT Date,Serial,LaunchSite FROM launches WHERE Outcome='False ASDS' AND substr(Date,1,4)='2015'"}
    results={}
    for n,q in queries.items():
        r=pd.read_sql_query(q,con);r.to_csv(OUT/('sql_'+n+'.csv'),index=False);results[n]=r
    (OUT/'queries.sql').write_text('\n\n'.join('-- '+n+'\n'+q+';' for n,q in queries.items()))
    con.close();return results

def haversine(a,b):
    a,b=np.radians(a),np.radians(b);delta=b-a
    return float(6371*2*np.arcsin(np.sqrt(np.sin(delta[0]/2)**2+np.cos(a[0])*np.cos(b[0])*np.sin(delta[1]/2)**2)))

def map_analysis():
    import folium
    from folium.plugins import MarkerCluster, MousePosition, MeasureControl
    d=pd.read_csv(DATA/'spacex_launch_geo.csv');sites=d.groupby('Launch Site')[['Lat','Long']].first()
    m=folium.Map(location=[30,-96],zoom_start=4,tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}', attr='Tiles: Esri. Sources: Esri, HERE, Garmin, USGS, Intermap, INCREMENT P, NRCAN, Esri Japan, METI, Esri China (Hong Kong), OpenStreetMap contributors, GIS User Community')
    cluster=MarkerCluster(name='Launch records').add_to(m)
    for row in d.itertuples(index=False,name=None):
        r=dict(zip(d.columns,row));folium.Marker([r['Lat'],r['Long']],popup=f"{r['Launch Site']} / flight {r['Flight Number']} / class {r['class']}",icon=folium.DivIcon(html=f"<div style='background:{'#168a55' if r['class']==1 else '#cc4433'};color:white;border:2px solid white;border-radius:50%;width:28px;height:28px;text-align:center;line-height:24px;font: bold 12px Arial;'>{r['Flight Number']}</div>",icon_size=(28,28),icon_anchor=(14,14))).add_to(cluster)
    for site,r in sites.iterrows():folium.CircleMarker([r.Lat,r.Long],radius=8,color='blue',tooltip=site).add_to(m)
    # Manually selected approximate coastline point, not a nearest-coast GIS estimate.
    coast=[28.56367,-80.5696];start=sites.loc['CCAFS SLC-40'].tolist();km=haversine(start,coast)
    folium.Marker(coast,popup='Approximate selected coastline point').add_to(m)
    folium.PolyLine([start,coast],color='orange',tooltip=f'Selected coastline distance: {km:.2f} km').add_to(m)
    MousePosition().add_to(m);MeasureControl().add_to(m);folium.LayerControl().add_to(m)
    m.save(OUT/'launch_map.html')
    detail=folium.Map(location=start,zoom_start=14,tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}', attr='Tiles: Esri. Sources: Esri, HERE, Garmin, USGS, Intermap, INCREMENT P, NRCAN, Esri Japan, METI, Esri China (Hong Kong), OpenStreetMap contributors, GIS User Community')
    folium.Marker(start,popup='CCAFS SLC-40',tooltip=folium.Tooltip('CCAFS SLC-40',permanent=True)).add_to(detail);folium.Marker(coast,popup='Selected coastline point',tooltip=folium.Tooltip('Approximate coastline point',permanent=True)).add_to(detail)
    folium.PolyLine([start,coast],tooltip=f'{km:.2f} km',color='orange').add_to(detail);detail.save(OUT/'proximity_map.html')
    sites.to_csv(OUT/'map_sites.csv');(OUT/'proximity.json').write_text(json.dumps({'site':'CCAFS SLC-40','start':start,'coastline_point':coast,'km':km,'method':'Haversine to manually selected approximate coastline point'}))
    return sites

def train(d):
    # Exclude Outcome and LandingPad (post-outcome). ReusedCount can contain later reuse history.
    nums=['PayloadMass','Flights','Block'];cats=['Orbit','LaunchSite','GridFins','Reused','Legs']
    X=d[nums+cats];y=d.Class
    Xtrain,Xtest,ytrain,ytest=train_test_split(X,y,test_size=.2,random_state=42,stratify=y)
    prep=ColumnTransformer([('numeric',Pipeline([('impute',SimpleImputer(strategy='median')),('scale',StandardScaler())]),nums),('categorical',OneHotEncoder(handle_unknown='ignore'),cats)])
    candidates={
     'Logistic Regression':(LogisticRegression(max_iter=2000),{'model__C':[.01,.1,1,10]}),
     'SVM':(SVC(),{'model__C':[.1,1,10],'model__kernel':['linear','rbf','sigmoid'],'model__gamma':['scale',.1]}),
     'Decision Tree':(DecisionTreeClassifier(random_state=42),{'model__max_depth':[2,3,4,6,None],'model__min_samples_leaf':[1,2,4]}),
     'KNN':(KNeighborsClassifier(),{'model__n_neighbors':[3,5,7,9],'model__weights':['uniform','distance']})}
    rows=[];models={};cv=StratifiedKFold(5,shuffle=True,random_state=42)
    for n,(model,grid) in candidates.items():
        search=GridSearchCV(Pipeline([('prep',prep),('model',model)]),grid,cv=cv,scoring='accuracy',n_jobs=1)
        search.fit(Xtrain,ytrain);pred=search.predict(Xtest)
        rows.append({'model':n,'cv_accuracy':search.best_score_,'test_accuracy':accuracy_score(ytest,pred),'test_f1':f1_score(ytest,pred),'best_params':json.dumps(search.best_params_)})
        models[n]=search
    scores=pd.DataFrame(rows).sort_values('cv_accuracy',ascending=False).reset_index(drop=True);scores.to_csv(OUT/'model_comparison.csv',index=False)
    best=scores.iloc[0]['model'];pred=models[best].predict(Xtest)
    pd.DataFrame({'row_index':Xtest.index,'true':ytest,'predicted':pred}).to_csv(OUT/'test_predictions.csv',index=False)
    cm=confusion_matrix(ytest,pred,labels=[0,1]);ConfusionMatrixDisplay(cm,display_labels=['Class 0','Class 1']).plot(cmap='Blues',colorbar=False);plt.title(best+' selected by training CV');save('confusion_matrix')
    ax=scores.set_index('model')[['cv_accuracy','test_accuracy']].plot.bar(color=['#168a96','#e8a34d']);ax.set_ylim(0,1);ax.set_ylabel('Accuracy');save('models')
    summary={'rows':len(d),'class1':int(y.sum()),'class0':int((y==0).sum()),'train_n':len(ytrain),'test_n':len(ytest),'selected_model':best,'cm':cm.tolist(),'test_accuracy':accuracy_score(ytest,pred),'features':nums+cats,'excluded':['Outcome','LandingPad','ReusedCount','Serial','Date','FlightNumber','BoosterVersion','Longitude','Latitude'],'protocol':'Stratified 80/20 split, seed 42, fivefold stratified training CV, preprocessing fit within CV'}
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2));return scores

def run():
    collect();d=wrangle();eda(d);sql_analysis(d);map_analysis();print(train(d).to_string(index=False));print(scrape().to_string(index=False))
    try: print('API records:',len(api_collection()))
    except Exception as e: (OUT/'api_status.txt').write_text('API fetch unavailable: '+str(e));print('API fetch unavailable:',e)
if __name__=='__main__':run()
