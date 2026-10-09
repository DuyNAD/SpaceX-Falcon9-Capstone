"""Rebuild slide-format PDF after adding repository_url.txt."""
from pathlib import Path
import json,textwrap
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor,white
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph,Table,TableStyle
from reportlab.lib.styles import ParagraphStyle
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'results'
pdfmetrics.registerFont(TTFont('ProjectSans',str(ROOT/'assets/fonts/DejaVuSans.ttf')))
pdfmetrics.registerFont(TTFont('ProjectSans-Bold',str(ROOT/'assets/fonts/DejaVuSans-Bold.ttf')))
W,H=960,540
INK=HexColor('#12263b');TEAL=HexColor('#087f8c');GREY=HexColor('#526371')
style=ParagraphStyle('body',fontName='ProjectSans',fontSize=18,leading=25,textColor=INK)
small=ParagraphStyle('small',fontName='ProjectSans',fontSize=12,leading=16,textColor=GREY)
repo=(ROOT/'repository_url.txt').read_text().strip()
source='IBM course snapshots / analysis executed 9 Oct 2026'
summary=json.loads((OUT/'summary.json').read_text());scores=pd.read_csv(OUT/'model_comparison.csv')
c=canvas.Canvas(str(ROOT/'Data_Science_Capstone_Project_Report.pdf'),pagesize=(W,H));c.setTitle('Data Science Capstone Project Report');page=0

def para(text,x,y,w=850,st=style):
    p=Paragraph(text,st);a,h=p.wrap(w,500);p.drawOn(c,x,y-h);return y-h

def begin(title,section='SpaceX Falcon 9',note=source):
    global page
    page+=1;c.setFillColor(white);c.rect(0,0,W,H,fill=1,stroke=0)
    c.setFillColor(TEAL);c.setFont('ProjectSans',12);c.drawString(42,507,section.upper())
    para(title,42,478,870,ParagraphStyle('title',fontName='ProjectSans-Bold',fontSize=30,leading=35,textColor=INK))
    c.setFillColor(GREY);c.setFont('ProjectSans',9);c.drawString(42,25,note[:130]);c.drawRightString(918,25,f'{page:02}')
    c.setStrokeColor(HexColor('#d9e2e8'));c.line(42,41,918,41)

def end():c.showPage()
def bullets(lines,y=402,w=850,x=48,size=18):
    st=ParagraphStyle('body',fontName='ProjectSans',fontSize=size,leading=size*1.35,textColor=INK)
    for line in lines:y=para(line,x,y,w,st)-18

def img(name,x=42,y=95,w=875,h=305):
    p=OUT/(name+'.png');im=ImageReader(str(p));iw,ih=im.getSize();scale=min(w/iw,h/ih);dw,dh=iw*scale,ih*scale;c.drawImage(im,x+(w-dw)/2,y+(h-dh)/2,dw,dh,mask='auto')
def table(df,y=395,widths=None,size=15):
    d=df.copy()
    for col in d:
        if pd.api.types.is_float_dtype(d[col]):d[col]=d[col].map(lambda x:f'{x:,.3f}')
    st=ParagraphStyle('cell',fontName='ProjectSans',fontSize=size,leading=size+4,textColor=INK)
    data=[[Paragraph(str(x),st) for x in d.columns]]+[[Paragraph(str(x),st) for x in row] for row in d.astype(str).values]
    widths=widths or [870/len(d.columns)]*len(d.columns)
    t=Table(data,colWidths=widths);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),HexColor('#eaf5f6')),('FONTNAME',(0,0),(-1,0),'ProjectSans-Bold'),('LINEBELOW',(0,0),(-1,0),1,TEAL),('LINEBELOW',(0,1),(-1,-1),.4,HexColor('#d9e2e8')),('TOPPADDING',(0,0),(-1,-1),9),('BOTTOMPADDING',(0,0),(-1,-1),9),('VALIGN',(0,0),(-1,-1),'TOP')]))
    _,h=t.wrap(870,500);t.drawOn(c,42,y-h);return y-h

def repository(file):
    label=repo if repo else 'Repository URL pending: upload project to GitHub and set repository_url.txt'
    para(label+'<br/>Code: '+file,42,90,870,small)

def chart(title,name,text,section='EDA results'):
    begin(title,section);img(name,y=135,h=272);para(text,48,121,850,small);end()

begin('Data Science Capstone Project Report','IBM Applied Data Science Capstone')
para('SpaceX Falcon 9<br/>First Stage Landing Prediction',48,370,800,ParagraphStyle('cover',fontName='ProjectSans-Bold',fontSize=40,leading=48,textColor=INK))
para('Historical launch analysis and a reproducible classification benchmark',48,215,800,style)
para('9 October 2026<br/>Repository link requires completion before submission',48,130,800,small);end()

begin('Executive summary')
bullets(['The modeling snapshot contains 90 Falcon 9 launches: 60 Class 1 and 30 Class 0.','EDA and SQL describe differences across sites, orbits and years. Folium and Dash use a separate 56-record course snapshot.','SVM leads training CV accuracy at 88.86%. All four models score 77.78% on the 18-record test set.','The model detects all 12 Class 1 test records but misclassifies four Class 0 records. More data and chronological evaluation are needed.'],size=18);end()

begin('Introduction and research problem')
bullets(['A successful first-stage landing can enable booster recovery and later reuse.','Project question: can historical launch features predict the course-defined first-stage landing outcome?','Compare LR, SVM, Decision Tree and KNN using the same data and evaluation protocol.','Explore launch-site geography and payload patterns to support descriptive planning insights.','The project estimates outcome classes. It does not estimate launch prices or financial savings.'],size=18);end()

begin('Data sources and analysis scope','Data collection')
table(pd.DataFrame([['Archived API JSON','107 records','Launch and core fields'],['Modeling CSV','90 launches','EDA, SQL, classification'],['Geo / Dash CSVs','56 records each','Interactive exploration'],['Wikipedia HTML','2010-2019 page','Separate scraped tables']],columns=['Source','Scope','Use']),widths=[230,230,410],size=17)
para('The two course snapshots have different scopes. Their success proportions must remain separate.',48,150,850,style);end()

begin('Data collection: SpaceX API','Methodology')
bullets(['1. Download the archived API JSON from IBM and normalize the launch records.','2. Extract flight number, date, rocket ID and launchpad ID. Read landing_success from each core.','3. Read core landing_success separately from mission success. Align all 90 modeling rows to archived launches by unique date.','4. Use IBM enriched CSV as the fixed modeling reference. Live API calls returned HTTP 525 during preparation.'],y=401,size=18)
repository('notebooks/01_Data_Collection_API.ipynb');end()

begin('API collection output','Data collection results')
api=pd.read_csv(OUT/'api_launch_summary.csv');api['date_utc']=api.date_utc.str[:10];api=api.rename(columns={'flight_number':'Flight','name':'Mission','date_utc':'Date (UTC)','success':'Mission success'});table(api[['Flight','Mission','Date (UTC)','Mission success']].head(6),widths=[115,285,290,180],size=17)
para('Archived response: 107 launch records. These rows show mission success, which differs from core landing_success.',48,112,850,small);end()

begin('Data collection: web scraping','Methodology')
bullets(['1. Retrieve the Wikipedia launch-history HTML for 2010-2019.','2. Parse HTML tables with pandas.read_html and select tables containing payload and launch/date columns.','3. Flatten table headers and export seven selected tables as CSV.','4. Retain source HTML. Tables may contain Falcon Heavy, merged rows and footnotes, so they stay separate from modeling.'],size=18)
repository('notebooks/02_Web_Scraping.ipynb');end()

begin('Data wrangling and target definition','Methodology')
bullets(['Validate unique FlightNumber values and parse dates for yearly summaries.','Class 0: False ASDS, False Ocean, False RTLS, None ASDS or None None. Class 1: other recorded outcomes.','Confirm all 90 recreated labels match IBM dataset_part_2.csv.','Class 0 includes absent/unknown landing outcomes. This label is broader than physical landing failure.','The enriched CSV already includes upstream payload imputation. Model-specific preprocessing fits within training folds.'],size=17)
repository('notebooks/03_Data_Wrangling.ipynb');end()

begin('EDA with visualization','Methodology')
bullets(['Scatter plots: flight number and payload mass against launch site and orbit.','Bar charts: Class 1 proportion by site and orbit, with group sample sizes.','Line chart: yearly Class 1 proportion from the 90-row modeling snapshot.','Descriptive associations identify patterns. Small groups and changing launch practices limit causal interpretation.'],size=18)
repository('notebooks/04_EDA_Visualization.ipynb');end()

begin('EDA with SQL','Methodology')
bullets(['Load the cleaned 90-row snapshot into SQLite as launches.','Query distinct sites, site prefixes, payload totals/averages and outcome counts.','Rank site success proportions and retrieve maximum-payload flights.','Query first successful RTLS, selected ASDS payload ranges, yearly trends and outcome counts within a date window.'],size=18)
repository('notebooks/05_EDA_SQL.ipynb / results/queries.sql');end()

begin('Interactive visual analytics','Methodology')
bullets(['Folium: site circles, launch-record clusters, class colors, measurement controls and a proximity line.','Dash: site dropdown, outcome pie charts and payload range slider controlling the scatter.','The all-sites pie reports shares of successful launch counts. The selected-site pie reports class proportions.','These tools use the 56-record interactive snapshots, independent of the modeling sample.'],size=18)
repository('notebooks/06_Folium_Map.ipynb / notebooks/07_Plotly_Dash.ipynb / spacex_dash_app.py');end()

chart('Flight number and launch site','flight_site','Later flights contain more Class 1 records. Flight number also tracks time and changes in launch configuration.')
chart('Payload mass and launch site','payload_site','Successful and non-successful outcomes overlap across payload values. This plot does not establish a universal payload cutoff.')
chart('Class 1 proportion by orbit','orbit_rate','Group sample sizes appear above the bars. A high rate from a small orbit group is weak evidence of future performance.')
chart('Flight number and orbit','flight_orbit','Flight sequence and orbital missions vary together. Orbit differences may reflect time and mission selection.')
chart('Payload mass and orbit','payload_orbit','Payload ranges differ across orbits. Descriptive comparisons should account for orbit and mission requirements.')
chart('Yearly Class 1 proportion','yearly','Historical proportions generally improve in later years, with year-to-year variation. Future launches require a chronological evaluation.')

begin('SQL results: launch sites and payloads','SQL results')
table(pd.read_csv(OUT/'sql_payloads.csv'),widths=[230,140,240,260],size=17)
para('Payload totals and means use the enriched IBM snapshot, including its upstream payload imputation.',48,175,850,style)
repository('results/sql_payloads.csv / results/sql_launch_sites.csv');end()

begin('SQL results: site ranking','SQL results')
table(pd.read_csv(OUT/'sql_success_rates.csv'),widths=[280,170,170,250],size=17)
para('KSC LC 39A: 17/22 Class 1. VAFB SLC 4E: 10/13. CCAFS SLC 40: 33/55. Different mission mixes and sample sizes prevent a causal site ranking.',48,175,850,style);end()

begin('SQL results: outcomes and time','SQL results')
first=pd.read_csv(OUT/'sql_first_rtls.csv').iloc[0,0];maximum=pd.read_csv(OUT/'sql_max_payload.csv').iloc[0]
bullets([f'First successful RTLS in this snapshot: {first}.',f'Maximum payload: {maximum.PayloadMass:,.0f} kg, flight {int(maximum.FlightNumber)}, booster {maximum.Serial}.','Yearly counts, 2015 ASDS failures and date-window outcome rankings appear in the executed SQL notebook.','Full CSV outputs preserve all query results. Customer-specific SQL requires a customer field absent from this modeling snapshot.'],size=18)
repository('results/sql_*.csv / notebooks/05_EDA_SQL.ipynb');end()

begin('Folium launch sites and records','Interactive results','IBM geography snapshot / Esri / OpenStreetMap contributors / GIS User Community')
img('launch_map',x=42,y=110,w=585,h=295)
bullets(['CCAFS LC-40','CCAFS SLC-40','KSC LC-39A','VAFB SLC-4E','Cluster counts preserve overlapping records.'],x=650,y=375,w=265,size=17);para('Four site labels in the 56-record geography snapshot. Marker clusters preserve overlapping launch records. Green marks Class 1 and red marks Class 0.',48,98,850,small);end()

begin('Folium individual launch records','Interactive results','IBM geography snapshot / Esri / OpenStreetMap contributors / GIS User Community')
img('launch_records',y=110,h=295);para('KSC LC-39A cluster expanded into individual launch records. Green markers denote Class 1 and red markers denote Class 0. Tooltips and popups identify each record.',48,98,850,small);end()

begin('Folium proximity analysis','Interactive results','IBM geography snapshot / Esri / OpenStreetMap contributors / GIS User Community')
img('proximity_map',y=140,h=265);pr=json.loads((OUT/'proximity.json').read_text());para(f'CCAFS SLC-40 to the selected approximate coastline point: {pr["km"]:.2f} km using Haversine distance. This is a point-to-point illustration, not the shortest distance to the coastline.',48,123,850,small);end()

begin('Dash: successful launch counts by site','Interactive results')
img('dash_pie',y=135,h=270);para('All-sites view: share of successful launch counts in the 56-row dashboard dataset. A larger pie slice does not necessarily mean a higher success rate.',48,121,850,small);end()

begin('Dash: site filter and payload scatter','Interactive results')
img('dash_scatter',x=42,y=145,w=560,h=260);img('dash_ksc',x=615,y=145,w=303,h=260)
para('The dropdown changes the site view. The payload slider filters scatter points. Booster-version categories distinguish groups; their associations do not prove a causal effect.',48,122,850,small);end()

begin('Predictive analysis protocol','Methodology')
bullets(['Stratified 80/20 split: 72 training records and 18 test records, seed 42.','Fivefold stratified CV on training data selects hyperparameters and the final model.','Numerical median imputation and scaling fit inside each CV fold. Categorical values use one-hot encoding.','Predictors: PayloadMass, Flights, Block, Orbit, LaunchSite, GridFins, Reused and Legs.','Exclude outcome/landing-pad information and fields with possible later reuse history. Inspect feature availability before deployment.'],size=17)
repository('notebooks/08_Predictive_Analysis.ipynb');end()

begin('Model comparison','Predictive results')
dis=scores[['model','cv_accuracy','test_accuracy','test_f1']].copy();dis.columns=['Model','CV accuracy','Test accuracy','Test F1'];table(dis,widths=[300,190,190,190],size=17)
para('SVM leads training CV and uses an RBF kernel with C=1 and gamma=scale. All four test accuracies tie at 14/18. This small test does not support a definitive model ranking.',48,170,850,style);end()

begin('SVM confusion matrix','Predictive results')
img('confusion_matrix',x=42,y=110,w=525,h=295)
bullets(['True Class 0: 2 correct, 4 predicted Class 1.','True Class 1: 12 correct, 0 predicted Class 0.','Accuracy: 77.78%. Class 1 F1: 85.71%.','Class 0 recall: 33.33%. Performance differs strongly by class.'],x=600,y=380,w=315,size=17);end()

begin('Conclusion and next steps')
bullets(['The workflow links source collection, label validation, exploration and a reproducible four-model benchmark.','Site, orbit and time patterns provide descriptive context. Payload alone does not separate the outcomes.','The selected SVM performs better than the 66.67% majority baseline on this test, but misses four Class 0 cases.','Next: verify pre-launch feature availability, expand the data and evaluate a chronological holdout. Audit subgroup errors before operational use.'],size=18);end()

begin('Repository and source references','Submission completion')
bullets([repo or 'GitHub URL pending. Create a public repository and add its URL to repository_url.txt.', 'Run python build_report.py to regenerate this PDF with the URL on the required methodology slides.','IBM source files, their SHA256 checksums and URLs: results/data_provenance.json.','Archived API source: IBM datasets/API_call_spacex_api.json. Wikipedia source HTML and scraped CSVs are included.','Full code: eight executed notebooks, pipeline.py and spacex_dash_app.py.'],size=17)
para('Wikipedia: List of Falcon 9 and Falcon Heavy launches (2010-2019)<br/>API archive and CSVs: cf-courses-data / IBM-DS0321EN-SkillsNetwork/datasets',48,100,850,small);end()
c.save();print('PDF pages:',page)
