import streamlit as st
from streamlit_option_menu import option_menu
# import gspread
# from google.oauth2 import service_account
# from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import pymongo
from pymongo import MongoClient
import os
# Plotly chart to show data points with values
import plotly.express as px
import plotly.graph_objects as go

mongo_uri = os.getenv("mongo")
client = MongoClient(mongo_uri)
db = client['CoachingInsights']
collection = db['CTR_DB']

# Initialize connection.
@st.cache_resource
def init_connection():
    return pymongo.MongoClient(st.secrets["mongo"]["uri"])

# Pull data from the collection.
@st.cache_data(ttl=600)
def get_all_data():
    client = init_connection()
    db = client["CoachingInsights"]
    collection = db["CTR_DB"]
    items = collection.find()
    items = list(items)  # make hashable for st.cache_data
    return items

@st.cache_data(ttl=600)
def get_data(train_no, sch_date):
    client = init_connection()
    db = client["CoachingInsights"]
    collection = db["CTR_DB"]
    if sch_date is None:
        query = {"Train No": str(train_no)}
    elif train_no is None:
        query = {"Sch date": sch_date}
    else:
        query = {"Train No": str(train_no), "Sch date": sch_date}
    items = collection.find(query)
    items = list(items)  # make hashable for st.cache_data
    return items

@st.cache_data(ttl=600)
def check_stn_for_train(train_no, sch_date, stn):
    client = init_connection()
    db = client["CoachingInsights"]
    collection = db["CTR_DB"]
    query = {"Train No": str(train_no), "Sch date": sch_date, "Stn": stn}
    items = list(collection.find(query))
    return(bool(items))
# Authorize the client
# client = gspread.authorize(credentials)

def filter_and_plot_data(Stn_A, Stn_B, total_items_on_date):
    stnb_sl_no = 0
    stnb_train_no = ""
    stna_sl_no = 0
    stna_train_no = ""
    filtered_df = []
    filtered_df_temp = []
    hold_train_no = ""

    for idx, item in enumerate(total_items_on_date):
        if item["Train No"] != hold_train_no:
            stna_train_no = ""
            stnb_train_no = ""
            stna_sl_no = 0
            stnb_sl_no = 0
            filtered_df_temp = []
        if item["Stn"] == Stn_A:
            stna_sl_no = int(item["SL/No"])
            stna_train_no = item["Train No"]
        if item["Stn"] == Stn_B:
            stnb_sl_no = int(item["SL/No"])
            stnb_train_no = item["Train No"]
        if stna_train_no:
            filtered_df_temp.append(item)
        if stna_train_no and stnb_train_no and stna_train_no != stnb_train_no:
            stna_train_no = ""
            stnb_train_no = ""  
            filtered_df_temp = []
        elif stna_train_no == stnb_train_no and stna_sl_no < stnb_sl_no:         
            filtered_df.extend(filtered_df_temp)
            filtered_df_temp = []
            stna_train_no = ""
            stnb_train_no = ""
            stna_sl_no = 0
            stnb_sl_no = 0
        hold_train_no = item["Train No"]

    # Convert filtered_df to pandas DataFrame
    final_df = pd.DataFrame(filtered_df, columns=["Train No", "Stn", "Max Speed"])

    if not final_df.empty:
        # Pivot the DataFrame to have Stn as columns and Train No as rows
        max_length_train_no = final_df.groupby("Train No").size().idxmax()
        max_length_stn_sequence = final_df[final_df["Train No"] == max_length_train_no]["Stn"].unique()

        pivot_df = final_df.pivot(index="Train No", columns="Stn", values="Max Speed")
        pivot_df = pivot_df.reindex(columns=max_length_stn_sequence)

        st.write(f"Max Speed Analysis between {Stn_A} and {Stn_B}:")
        st.dataframe(pivot_df)

        final_df["Max Speed"] = pd.to_numeric(final_df["Max Speed"], errors='coerce')
        grouped_df = final_df.groupby("Stn")["Max Speed"].agg(["max", "min", "mean"]).reset_index()
        grouped_df.columns = ["Stn", "Max Speed", "Min Speed", "Avg Speed"]

        candlestick_fig = go.Figure(data=[
            go.Candlestick(x=grouped_df["Stn"],
                            open=grouped_df["Min Speed"],
                            high=grouped_df["Max Speed"],
                            low=grouped_df["Min Speed"],
                            close=grouped_df["Avg Speed"],
                            increasing_line_color='green', decreasing_line_color='red', showlegend=False)
        ])
        candlestick_fig.update_layout(
            title=f"Max Speed Chart Analysis between {Stn_A} and {Stn_B} :",
            xaxis_title="Station",
            yaxis_title="Speed (Kmph)",
            xaxis=dict(categoryorder='array', categoryarray=max_length_stn_sequence),
            dragmode=False
        )

        for i, row in grouped_df.iterrows():
            candlestick_fig.add_annotation(x=row["Stn"], y=row["Max Speed"],
                                            text=f"{row['Max Speed']:.2f}", showarrow=False,
                                            yshift=10, font=dict(color="white", size=12))
            candlestick_fig.add_annotation(x=row["Stn"], y=row["Min Speed"],
                                            text=f"{row['Min Speed']:.2f}", showarrow=False,
                                            yshift=-10, font=dict(color="white", size=12))
            candlestick_fig.add_annotation(x=row["Stn"], y=row["Avg Speed"],
                                            text=f"{row['Avg Speed']:.2f}", showarrow=False,
                                            yshift=0, font=dict(color="white", size=12))

        st.plotly_chart(candlestick_fig)
    else:
        st.write("No data found for the given Sch Date.")

# Define different functionalities
def max_speed_trains():
    st.markdown("""
        <div style="display: flex; align-items: center; justify-content: center; flex-direction: column; padding: 0px; border-radius: 1px;">
            <h2 id="dashboard-title" style="margin: 0; font-size: 1.5em;">🚄 Maximum Speed Analysis of EMU Locals (Trains)</h2>
        </div>
        <script>
            const dashboardTitle = document.getElementById('dashboard-title');
            const observer = new MutationObserver(() => {
                const body = document.body;
                const isDarkMode = window.getComputedStyle(body).backgroundColor === 'rgb(0, 0, 0)';
                dashboardTitle.style.color = isDarkMode ? '#fff' : '#333';
            });
            observer.observe(document.body, { attributes: true, attributeFilter: ['class'] });
        </script>
        """, unsafe_allow_html=True)
    
    # Input field for Sch Date
    # Fetch distinct Sch Date values from the database
    sch_date_list = [item["Sch date"] for item in get_all_data()]
    distinct_sch_date = sorted(set(sch_date_list))

    # Date input for Sch Date with default value set to the first date in distinct_sch_date
    sch_date = st.date_input("Enter Sch Date:", value=max(distinct_sch_date), min_value=min(distinct_sch_date), max_value=max(distinct_sch_date))

    # Fetch distinct Train No values for the selected Sch Date from the database
    train_no_list = [item["Train No"] for item in get_data(None, sch_date.strftime("%Y-%m-%d"))]
    distinct_train_no = sorted(set(train_no_list))

    # Dropdown for Train No
    train_no = st.selectbox("Select Train No:", distinct_train_no)

    # Convert Sch Date to YYYY-MM-DD format
    sch_date_str = sch_date.strftime("%Y-%m-%d")
    
    data = get_data(train_no=train_no, sch_date=sch_date_str)  # Convert cursor to list

    if data:
        # Convert data to DataFrame
        df = pd.DataFrame(data)
        
        df["Stn"]  = pd.Categorical(df["Stn"], categories=df["Stn"].unique(), ordered=True)
        df = df.sort_values("Stn")
        df["Max Speed"] = pd.to_numeric(df["Max Speed"], errors='coerce')

        # Display data in Streamlit
        # Select only the required columns
        filtered_df = df[["Train No", "Sch date", "Stn", "S/Arr", "S/Dep", "A/Arr", "A/Dep", "Max Speed"]]

       
        st.write(f"Showing data for: Train no={train_no}, Sch date={sch_date_str} :")
   
        st.markdown(
            """
            <div class="dataframe-container">
            """,
            unsafe_allow_html=True
        )
        st.dataframe(filtered_df, width=1500, height=600)
        st.markdown(
            """
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Plot line graph with Stn and Max Speed
        if not df.empty:
            fig = px.line(df, x="Stn", y="Max Speed", title="Max Speed by Station", markers=True)
            
            fig.update_traces(text=df["Max Speed"], textposition="top center", mode='lines+markers+text')

            # Add neon glow effect to the line
            fig.update_traces(line=dict(color='cyan', width=0.5))
            fig.update_layout(
                paper_bgcolor='black',
                plot_bgcolor='black',
                font_color='white',
                title_font=dict(size=24, color='white'),
                xaxis=dict(showgrid=False, zeroline=False),
                yaxis=dict(showgrid=False, zeroline=False),
                shapes=[
                    dict(
                        type='line',
                        x0=df["Stn"].iloc[i],
                        y0=df["Max Speed"].iloc[i],
                        x1=df["Stn"].iloc[i+1],
                        y1=df["Max Speed"].iloc[i+1],
                        line=dict(color='cyan', width=1, dash='solid')
                    ) for i in range(len(df)-1)
                ]
            )
            fig.update_layout(
                xaxis_title="Station", 
                yaxis_title="Max Speed (Kmph)",
                xaxis=dict(categoryorder='array', categoryarray=df["Stn"]),
                dragmode=False,  # Disable zoom
                font=dict(size=17),  # Increase font size
                height=600,  # Increase height
                width=1800  # Increase width
            )

            st.plotly_chart(fig)
    else:
        st.write("No data found for the given Train No and Sch Date.")

def max_speed_sections():
    st.markdown("""
    <div style="display: flex; align-items: center; justify-content: center; flex-direction: column; padding: 0px; border-radius: 1px;">
        <h2 id="dashboard-title" style="margin: 0; font-size: 1.5em;">🚄 Maximum Speed Analysis of EMU Locals (Sections)</h2>
    </div>
    <script>
        const dashboardTitle = document.getElementById('dashboard-title');
        const observer = new MutationObserver(() => {
            const body = document.body;
            const isDarkMode = window.getComputedStyle(body).backgroundColor === 'rgb(0, 0, 0)';
            dashboardTitle.style.color = isDarkMode ? '#fff' : '#333';
        });
        observer.observe(document.body, { attributes: true, attributeFilter: ['class'] });
    </script>
    """, unsafe_allow_html=True)
    
    # Input field for Sch Date
    # Fetch distinct Sch Date values from the database
    sch_date_list = [item["Sch date"] for item in get_all_data()]
    distinct_sch_date = sorted(set(sch_date_list))

    # Date input for Sch Date with default value set to the first date in distinct_sch_date
    sch_date = st.date_input("Enter Sch Date:", value=max(distinct_sch_date), min_value=min(distinct_sch_date), max_value=max(distinct_sch_date))

    # Fetch distinct Train No values for the selected Sch Date from the database
    total_items_on_date = get_data(None, sch_date.strftime("%Y-%m-%d"))

    # Call the function with appropriate parameters
    Stn_A = "SDAH"
    Stn_B = "RHA"
    # Dropdowns for Stn_A and Stn_B
    stn_list = sorted(set(item["Stn"] for item in total_items_on_date))
    Stn_A = st.selectbox("Select Station A:", stn_list)
    Stn_B = st.selectbox("Select Station B:", stn_list)
    filter_and_plot_data(Stn_A, Stn_B, total_items_on_date)
    

def sectionwise_time():
    st.write("This is the sectionwise time page.")

def sectional_speed():
    st.write("This is the sectional speed page.")

# Sidebar configuration
# Remove whitespace from the top of the page and sidebar
st.set_page_config(layout="wide")

st.markdown("""
        <style>
            html {
                font-size: 20px !important;  /* Change the font size */
            }

            .stMarkdownContainer, .stAppHeader {
                display: none;
            }
            .stMainBlockContainer {
                margin: 0;
                padding-top: 25px;
                border: 0;
            }
            @media (max-width: 768px) {
                .stSidebar {
                    width: 100% !important;
                    position: relative !important;
                }
                .stSidebar .css-1d391kg {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                }
                .stSidebar .css-1d391kg .css-1v3fvcr {
                    width: 100%;
                }
                .stSidebar .css-1d391kg .css-1v3fvcr .css-1v3fvcr {
                    width: 100%;
                }
                .stSidebar .css-1d391kg .css-1v3fvcr .css-1v3fvcr .css-1v3fvcr {
                    width: 100%;
                }
            }
        </style>
        """, unsafe_allow_html=True)

st.markdown("""
    <div style="display: flex; align-items: center; justify-content: center; flex-direction: column;">
        <h1 id="header-title" style="margin: 0; font-size: 2em;">Coaching Insights (SDAH)</h1>
        <hr style="border: none; height: 2px; background: linear-gradient(to right, red, orange, yellow, green, blue, indigo, violet); width: 100%; margin-top: 0px;">
    </div>
    <script>
        const headerTitle = document.getElementById('header-title');
        const observer = new MutationObserver(() => {
            const body = document.body;
            const isDarkMode = window.getComputedStyle(body).backgroundColor === 'rgb(0, 0, 0)';
            headerTitle.style.color = isDarkMode ? '#fff' : '#333';
        });
        observer.observe(document.body, { attributes: true, attributeFilter: ['class'] });

        function adjustHeaderFontSize() {
            const width = window.innerWidth;
            if (width < 768) {
                headerTitle.style.fontSize = '1.5em';
            } else {
                headerTitle.style.fontSize = '2em';
            }
        }

        window.addEventListener('resize', adjustHeaderFontSize);
        adjustHeaderFontSize();
    </script>
    """, unsafe_allow_html=True)

st.sidebar.title("Menu")
menu_options = {
    "Max Speed (Trains)": {"icon": "speedometer", "function": max_speed_trains},
    "Max Speed (Sections)": {"icon": "clock", "function": max_speed_sections},
    "Sectionwise Time": {"icon": "clock-history", "function": sectionwise_time},
    "Sectional Speed": {"icon": "speedometer", "function": sectional_speed},
}

if "menu_expanded" not in st.session_state:
    st.session_state["menu_expanded"] = True

def toggle_menu():
    st.session_state["menu_expanded"] = not st.session_state["menu_expanded"]

def select_menu_item(menu_item):
    st.session_state["menu_expanded"] = False
    return menu_item

with st.sidebar:
    if st.session_state["menu_expanded"]:
        menu_selected = option_menu(
            "Menu",
            options=list(menu_options.keys()),
            icons=[item["icon"] for item in menu_options.values()],
            menu_icon="cast",
            default_index=0,
            on_change=select_menu_item,
            key="menu_option"
        )
    else:
        menu_selected = option_menu(
            "",
            options=list(menu_options.keys()),
            icons=[item["icon"] for item in menu_options.values()],
            menu_icon="",
            default_index=0,
            on_change=select_menu_item,
            key="menu_option"
        )

# Call the selected function
menu_options[menu_selected]["function"]()