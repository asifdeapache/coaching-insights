import streamlit as st
from streamlit_option_menu import option_menu
import gspread
# from google.oauth2 import service_account
# from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import pymongo
from pymongo import MongoClient
import os
# Plotly chart to show data points with values
import plotly.express as px

# Set up Google Sheets API credentials
# Load the secrets from secrets.toml
# scope = [
#     "https://www.googleapis.com/auth/spreadsheets",
#     "https://www.googleapis.com/auth/drive"
# ]
# credentials_dict = st.secrets["google_api"]
# credentials = service_account.Credentials.from_service_account_info(credentials_dict, scopes=scope)

# mongodb connection
# MongoDB connection setup
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

# Authorize the client
# client = gspread.authorize(credentials)

# Define different functionalities
def dashboard():
    st.markdown("""
        <div style="display: flex; align-items: center; justify-content: center; flex-direction: column; padding: 0px; border-radius: 1px;">
            <h2 id="dashboard-title" style="margin: 0; font-size: 1.5em;">🚄 Maximum Speed Analysis of EMU Locals</h2>
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
        st.dataframe(filtered_df)
        
        # Plot line graph with Stn and Max Speed
        if not df.empty:
            fig = px.line(df, x="Stn", y="Max Speed", title="Max Speed by Station", markers=True)
            fig.update_traces(text=df["Max Speed"], textposition="top center", mode='lines+markers+text')
            fig.update_layout(xaxis_title="Station", yaxis_title="Max Speed (Kmph)",
                              xaxis=dict(categoryorder='array', categoryarray=df["Stn"]))

            st.plotly_chart(fig)
    else:
        st.write("No data found for the given Train No and Sch Date.")

def punctuality():
    st.write("This is the punctuality page.")

def sectionwise_time():
    st.write("This is the sectionwise time page.")

def sectional_speed():
    st.write("This is the sectional speed page.")

# Sidebar configuration
# Remove whitespace from the top of the page and sidebar
st.markdown("""
        <style>
            .stMarkdownContainer {
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
    "Dashboard": {"icon": "house", "function": dashboard},
    "Punctuality": {"icon": "clock", "function": punctuality},
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

# # Main content
# st.write("This is an example Streamlit app with a collapsible sidebar.")

# # Open the Google Sheet
# spreadsheet_id = "1wQfTF5WMC03hNXYKYZYoFrRFcWs_G8bOhu7g5yYDG6c"
# sheet = client.open_by_key(spreadsheet_id).sheet1

# # Read data from the Google Sheet
# expected_headers = ["TRAINNO", "FROMSTN", "FROMTIME"]  # Replace with your actual headers
# data = sheet.get_all_records(expected_headers=expected_headers)
# df = pd.DataFrame(data)

# # Display data in Streamlit
# st.title("Google Sheets Data in Streamlit")
# st.write(df)
