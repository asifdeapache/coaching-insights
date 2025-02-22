import streamlit as st
from streamlit_option_menu import option_menu

# Define different functionalities
def dashboard():
    st.write("This is the dashboard page.")

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
    <div style="display: flex; align-items: center; justify-content: center;">
        <img src="https://img.icons8.com/ios-filled/50/007bff/train.png" width="50" height="50" style="margin-right: 10px;">
        <h1 id="header-title" style="margin: 0;">Coaching Insights (SDAH)</h1>
    </div>
    <script>
        const headerTitle = document.getElementById('header-title');
        const observer = new MutationObserver(() => {
            const body = document.body;
            const isDarkMode = window.getComputedStyle(body).backgroundColor === 'rgb(0, 0, 0)';
            headerTitle.style.color = isDarkMode ? '#fff' : '#333';
        });
        observer.observe(document.body, { attributes: true, attributeFilter: ['class'] });
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

    st.sidebar.button("Toggle Menu", on_click=toggle_menu)

# Call the selected function
menu_options[menu_selected]["function"]()

# Main content
st.write("This is an example Streamlit app with a collapsible sidebar.")
