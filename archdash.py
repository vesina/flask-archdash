import logging
import sys
import os
from logging import Logger
import pandas as pd
import glob

import chart_studio.tools as tls

import plotly.graph_objects as go
import plotly.express as px
import matplotlib.pyplot as plt
import chart_studio.plotly as py
import plotly.figure_factory as ff

FORMAT = "%(asctime)s — %(levelname)-8s %(name)-15s %(module)s.%(funcName)s:%(lineno)d — %(message)s"
LOG_FILE = "app.log"
DATASET_FOLDER = 'dataset'

logger = Logger(name='archdash', level=logging.INFO)
logger.addHandler(logging.StreamHandler(sys.stdout))
 
ENV = 'dev'
APPNAME = 'archdash'

def list_csv_files(path: str, ext: str=".csv"):
    search_pattern = os.path.join(path,"*"+ ext)
    return glob.glob(search_pattern)

#### GLOBAL VALUES #####################################
MONTHS = ["JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE", "JULY", "AUGUST", "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER"]

# create a list of the desired CATEGORIES
CATEGORIES = ["Office", "K-12 School", "Multifamily Housing", "Residence Hall/Dormitory", "Hotel", "College/University", "Fitness Center/Health Club/Gym"]

def get_monthlist(type: str):
    return [f'{type.upper()}USE_KBTU_{m}' for m in MONTHS]

MONTHLIST_EL = [
    'ELECTRICITYUSE_KBTU_JANUARY',
    'ELECTRICITYUSE_KBTU_FEBRUARY',
    'ELECTRICITYUSE_KBTU_MARCH',
    'ELECTRICITYUSE_KBTU_APRIL',
    'ELECTRICITYUSE_KBTU_MAY',
    'ELECTRICITYUSE_KBTU_JUNE',
    'ELECTRICITYUSE_KBTU_JULY',
    'ELECTRICITYUSE_KBTU_AUGUST',
    'ELECTRICITYUSE_KBTU_SEPTEMBER',
    'ELECTRICITYUSE_KBTU_OCTOBER',
    'ELECTRICITYUSE_KBTU_NOVEMBER',
    'ELECTRICITYUSE_KBTU_DECEMBER',
]

MONTHLIST_GAS = ['NATURALGAS_KBTU_JANUARY',
 'NATURALGAS_KBTU_FEBRUARY',
 'NATURALGAS_KBTU_MARCH',
 'NATURALGAS_KBTU_APRIL',
 'NATURALGAS_KBTU_MAY',
 'NATURALGAS_KBTU_JUNE',
 'NATURALGAS_KBTU_JULY',
 'NATURALGAS_KBTU_AUGUST',
 'NATURALGAS_KBTU_SEPTEMBER',
 'NATURALGAS_KBTU_OCTOBER',
 'NATURALGAS_KBTU_NOVEMBER',
 'NATURALGAS_KBTU_DECEMBER']

INFOLIST = [
    'PID',
    'PRIMARYPROPERTYTYPE_SELFSELECT',
    'TAXRECORDFLOORAREA',
    'REPORTEDBUILDINGGROSSFLOORAREA',
]


#### END GLOBAL VALUES #################################

##### DATASETS #########################################
project_file = "dataset\\data_export_projects.csv"
benchmark_file = "dataset\\Building_Energy_Benchmarking.csv"

def get_project_data(csvfile: str):
    project_data = pd.read_csv(csvfile)
    project_data.head()
    # print(len(project_data))

    filter_project_data= project_data[["type_list_text","name_text", "completion_date_date"]]
    df2 = pd.DataFrame(filter_project_data.groupby(["type_list_text", "completion_date_date"])["name_text"].count().reset_index())
    df2.columns = ["Building Type","Year", "Number of Buildings" ]
    # df2["Year"] = df2["Year"].dt.year # added RR 09/24/25

    return df2

def load_benchmark_file(csvfile: str):
    # print(os.path.basename(csvfile))
    data = pd.read_csv(csvfile, low_memory=False)
    filtered_data = data[data["PRIMARYPROPERTYTYPE_SELFSELECT"].isin(CATEGORIES)]
    # data["PRIMARYPROPERTYTYPE_SELFSELECT"].dropna().value_counts()[:20]
    return filtered_data # data 

def get_usage_data(data, monthlist,  debug: bool=True):
    filtered_data = data[INFOLIST + monthlist]

    long_df = filtered_data.melt(id_vars=INFOLIST, var_name='usage_month', value_vars=monthlist, value_name='usage')

    long_df = long_df[long_df['usage'] > 0]   # remove buildings with zero usage
    long_df['usage_per_sqft'] = long_df['usage'] / long_df['TAXRECORDFLOORAREA']

    if debug:
        print("AFTER long_df") 
    # use `groupby` to get the median stats per building type per month
    agg_df = long_df.groupby(by=['PRIMARYPROPERTYTYPE_SELFSELECT', 'usage_month'], as_index=False).median(numeric_only=True)

    # `pivot` the results so that each row is one month and each column is usage for a building type
    buildtype_median_usage_gas = agg_df[['PRIMARYPROPERTYTYPE_SELFSELECT', 'usage_month', 'usage_per_sqft']].pivot(
        index='usage_month', columns='PRIMARYPROPERTYTYPE_SELFSELECT')

    # correct the order of the MONTHS
    buildtype_median_usage_gas = buildtype_median_usage_gas.reindex(monthlist)
    buildtype_median_usage_gas

    # buildtype_median_usage.plot(figsize=(15, 9), rot=330)
    return buildtype_median_usage_gas

#### END DATASETS ######################################

#### FIGURES ###########################################

def get_usage_figure(df, title: str=None, yaxistitle: str=None, debug: bool=True) -> go.Figure:

    if title:
        _title = title
    else:
        _title = f'Building Type vs. Median Monthly Usage per SQFT'

    if yaxistitle:
        _yaxstitle = yaxistitle
    else:
        _yaxstitle = f'Median Use (KBTU) per SQFT'

    Y_vals = []
    for category in CATEGORIES:
        Y_vals.append(df.loc[:, ('usage_per_sqft', category)].values)

    # create a sample dataframe with monthly values for each building type
    data = {
        'buildtype': CATEGORIES,
        'x_values': [MONTHS] * len(CATEGORIES),
        'y_values': Y_vals
    }
    df = pd.DataFrame(data)

    # create a dictionary of traces for each building category
    traces = {}
    for category in df['buildtype']:
        trace = go.Scatter(x=df.loc[df['buildtype'] == category, 'x_values'].values[0],
                        y=df.loc[df['buildtype'] == category, 'y_values'].values[0],
                        mode='lines+markers', name=category)
        traces[category] = trace

    # create the buttons for the graph
    buttons=list([
                    dict(
                        label=category,
                        method='update',
                        args=[{'x': [df.loc[df['buildtype'] == category, 'x_values'].values[0]],
                            'y': [df.loc[df['buildtype'] == category, 'y_values'].values[0]]},
                            {'title': 'Building Type: ' + category}]
                    )
                    for category in df['buildtype']
                ])

    buttons.append(
        dict(
            label='All',
            method='update',
            args=[{'x': [df.loc[df['buildtype'] == category, 'x_values'].values[0] for category in df['buildtype']],
                'y': [df.loc[df['buildtype'] == category, 'y_values'].values[0] for category in df['buildtype']],
                'title': 'All Building Types'}]
        )
    )


    # create a layout for the graph with buttons
    layout = go.Layout(
        title=_title, #'Building Type vs. Median Monthly Natural Gas Usage per SQFT',
        xaxis=dict(title='Month'),
        yaxis=dict(title=_yaxstitle), #'Median Natural Gas Usage (KBTU) per SQFT'),
        width=1200,
        height=600,
        updatemenus=[
            dict(
                buttons=buttons,
                direction='down',
                showactive=True,
                x=0.1,
                y=1.2
            ),
        ]
    )

    # create a figure and add the traces and layout
    fig = go.Figure(data=list(traces.values()), layout=layout)
  
    return fig
    # show the graph
    # fig.show()

def get_project_figure(df, debug: bool=True) -> go.Figure:
    # Prepare DataFrame
    df["Year"] = pd.to_datetime(df["Year"], format="%b %d, %Y %I:%M %p").dt.year

    # Get unique years
    years = sorted(df["Year"].unique())

    # Get unique building types
    building_types = sorted(df["Building Type"].unique())

    # Assign consistent colors
    colors = px.colors.qualitative.Plotly
    color_map = {b_type: colors[i % len(colors)] for i, b_type in enumerate(building_types)}

    # Precompute pie chart data
    pie_charts = []
    for year in [None] + list(years):  # None = All Years
        if year is None:
            filtered_df = df
            title = "Building Type Distribution for All Years"
        else:
            filtered_df = df[df["Year"] == year]
            title = f"Building Type Distribution for {year}"
        
        pie_charts.append(dict(
            labels=filtered_df["Building Type"],
            values=filtered_df["Number of Buildings"],
            title=title
        ))

    # Create initial figure
    fig = go.Figure(
        data=[go.Pie(
            labels=pie_charts[0]["labels"],
            values=pie_charts[0]["values"],
            textinfo="percent",
            marker=dict(colors=[color_map[label] for label in pie_charts[0]["labels"]]), 
            domain=dict(x=[0.2, 0.8], y=[0.2, 0.8])

        )]
    )

    # Build dropdown buttons properly
    buttons = []
    for i, year in enumerate(["All Years"] + list(years)):
        buttons.append(dict(
            label=str(year),
            method="update",
            args=[
                {"labels": [pie_charts[i]["labels"]],
                "values": [pie_charts[i]["values"]],
                "marker": [dict(colors=[color_map[label] for label in pie_charts[i]["labels"]])]},
                {"title": {"text": pie_charts[i]["title"]}}  # <-- Important fix: set title.text
            ]
        ))


    # CHat GPT
    fig.update_layout(
        title={"text": pie_charts[0]["title"], "x": 0.5, "xanchor": "center"},
        updatemenus=[dict(
            buttons=buttons,
            direction="down",
            showactive=True,
            x=0.001,
            y=1.1,
            xanchor="left",
            yanchor="top"
        )],
        
        margin=dict(t=150, b=50, l=50, r=150),  # extra right margin for legend
        legend=dict(
            orientation="v",
            x=1.05,
            y=0.5,
            xanchor="left",
            yanchor="middle",  
        ),
        autosize=True
    )
    return fig

def main(logger):
    DEBUG = False
    logger.info(f'Initializing {APPNAME.upper()} application.')
    path = os.path.dirname(__file__)
    datapath = os.path.join(path, DATASET_FOLDER)
    benchmark_file = "Building_Energy_Benchmarking.csv"
    benchmark_path = os.path.join(datapath,benchmark_file)
    logger.info(f'Dataset folder: {datapath}')

    # show project data
    df = get_project_data(csvfile=project_file)
    if DEBUG: 
        print(df)
    tls.get_embed('http://127.0.0.1:5000/archdash/') 
    py.iplot(fig)

    fig = get_project_figure(df)
    fig.show()
    return
    # show usage data
    fdf = load_benchmark_file(csvfile=benchmark_path)
    if DEBUG: 
        print(fdf)

    ## show Electrical usage
    label = "Electricity"

    el_usage_df= get_usage_data(data=fdf, monthlist=MONTHLIST_EL, debug=False)

    if DEBUG:
        print(el_usage_df)
        el_usage_df.plot(figsize=(15, 9), rot=330)
        plt.show()
    
    title = f'Building Type vs. Median Monthly {label} Use per SQFT'
    yaxis_title = f'Building Type vs. Median Monthly {label} Use per SQFT'
    fig = get_usage_figure(df=el_usage_df, title=title, yaxistitle=yaxis_title)
    fig.show()

    # show natural gas usage
    label = "Natural Gas"
    gas_usage_df= get_usage_data(data=fdf, monthlist=MONTHLIST_GAS, debug=False)

    if DEBUG: 
        print(gas_usage_df)
        gas_usage_df.plot(figsize=(15, 9), rot=330)
        plt.show()
    
    title = f'Building Type vs. Median Monthly {label} Use per SQFT'
    yaxis_title = f'Building Type vs. Median Monthly {label} Use per SQFT'
    fig = get_usage_figure(df=gas_usage_df, title=title, yaxistitle=yaxis_title)
    fig.show()

if __name__ == "__main__":
    main(logger=logger)