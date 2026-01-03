import streamlit as st
from PIL import Image
import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

# PAGE CONFIGURATION
st.set_page_config(
    page_title="DigitizeBills | Receipt & Invoice Digitizer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add root directory to path so we can import 'src'
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Files IMPORTS
try:
    from src.preprocessing import preprocess_image
    from src.ocr import run_ocr
except ImportError as e:
    st.warning(f"⚠️ Module Import Warning: {e}")

# SESSION STATE SETUP
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Dashboard"

if 'processed' not in st.session_state:
    st.session_state.processed = False
if 'ocr_result' not in st.session_state:
    st.session_state.ocr_result = ""
if 'confidence' not in st.session_state:
    st.session_state.confidence = 0
if 'processed_image' not in st.session_state:
    st.session_state.processed_image = None

# SIDEBAR NAVIGATION
with st.sidebar:
    st.title("Digitizer")
    st.caption("Receipt & Invoice Digitizer")
    st.divider()
    
    st.subheader("Navigation")
    
    # Page selection buttons
    if st.button("📊 Dashboard", key="nav_dashboard", use_container_width=True):
        st.session_state.current_page = "Dashboard"
        st.rerun()
    
    if st.button("🧾 Upload & Process", key="nav_upload", use_container_width=True):
        st.session_state.current_page = "Upload & Process"
        st.rerun()
    
    if st.button("🕒 History", key="nav_history", use_container_width=True):
        st.session_state.current_page = "History"
        st.rerun()
    
    st.divider()
    st.subheader("System")
    st.link_button(label="Repo", url="https://github.com/abhay1maurya/Receipt-and-Invoice-Digitizer")
    st.info("ℹ️ v1.0.0-beta")

# PAGE: DASHBOARD
def page_dashboard():
    st.title("My Spending Dashboard")
    st.markdown("Personal overview of your receipts, invoices and spending patterns.")
    st.divider()

    # KEY METRICS ROW
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(label="Total Spent", value="$4,589.50", delta="+$234 this week")

    with col2:
        st.metric(label="Avg. Spent/Month", value="$1,229.88", delta="+5.2%")

    with col3:
        st.metric(label="Total Vendors", value="34", delta="+3 new")

    with col4:
        st.metric(label="Total Transactions", value="156", delta="+12 this week")

    st.divider()

    # SPENDING ANALYSIS CHARTS
    col_chart1, col_chart2 = st.columns(2)

    # Chart 1: Monthly Spending Trend
    with col_chart1:
        st.subheader("📈 Monthly Spending Trend")
        
        months = ['Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan']
        spending = [950, 1050, 1200, 1100, 1350, 1289]
        
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=months, y=spending, mode='lines+markers',
                                  name='Spending', line=dict(color='#3498db', width=3),
                                  marker=dict(size=8)))
        fig1.update_layout(
            hovermode='x unified',
            height=350,
            margin=dict(l=0, r=0, t=20, b=0),
            yaxis_title='Amount ($)',
            xaxis_title='Month',
            showlegend=False
        )
        st.plotly_chart(fig1, use_container_width=True)

    # Chart 2: Spending by Category
    with col_chart2:
        st.subheader("🛍️ Spending by Category")
        
        categories = ['Groceries', 'Electronics', 'Dining', 'Shopping', 'Utilities', 'Others']
        amounts = [1200, 950, 850, 680, 520, 389]
        colors = ['#2ecc71', '#3498db', '#e74c3c', '#f39c12', '#9b59b6', '#95a5a6']
        
        fig2 = go.Figure(data=[go.Pie(
            labels=categories,
            values=amounts,
            marker=dict(colors=colors),
            hole=0.3
        )])
        fig2.update_layout(
            height=350,
            margin=dict(l=0, r=0, t=20, b=0),
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    # TOP VENDORS & ITEMS
    col_vendors, col_items = st.columns(2)

    # Top Vendors
    with col_vendors:
        st.subheader("🏪 Top Vendors")
        
        vendor_data = {
            'Vendor': ['Walmart', 'Amazon', 'Target', 'Whole Foods', 'Best Buy'],
            'Spent': [850, 750, 680, 520, 450],
            'Transactions': [28, 15, 22, 18, 9]
        }
        df_vendors = pd.DataFrame(vendor_data)
        
        fig3 = px.bar(df_vendors, x='Vendor', y='Spent',
                     color='Spent',
                     color_continuous_scale='Blues',
                     text_auto='$',
                     height=300)
        fig3.update_layout(
            margin=dict(l=0, r=0, t=20, b=0),
            yaxis_title='Amount Spent ($)',
            xaxis_title='Vendor',
            showlegend=False
        )
        st.plotly_chart(fig3, use_container_width=True)

    # Top Purchased Items
    with col_items:
        st.subheader("⭐ Top Purchased Items")
        
        items_data = {
            'Item': ['Milk/Dairy', 'Fresh Produce', 'Electronics', 'Coffee', 'Household'],
            'Count': [42, 38, 15, 28, 22],
            'Avg Price': [8.50, 12.30, 45.00, 5.20, 15.80]
        }
        df_items = pd.DataFrame(items_data)
        
        fig4 = px.bar(df_items, x='Item', y='Count',
                     color='Avg Price',
                     color_continuous_scale='Oranges',
                     text_auto=True,
                     height=300)
        fig4.update_layout(
            margin=dict(l=0, r=0, t=20, b=0),
            yaxis_title='Purchase Count',
            xaxis_title='Item Category',
            showlegend=False
        )
        st.plotly_chart(fig4, use_container_width=True)

    st.divider()

    # SPENDING INSIGHTS
    col_insight1, col_insight2, col_insight3 = st.columns(3)
    
    with col_insight1:
        st.success("💚 **Budget Goal**: On track! 78% of monthly budget spent")
    
    with col_insight2:
        st.info("📌 **Top Category**: Groceries account for 26% of your spending")
    
    with col_insight3:
        st.warning("⚠️ **Highest Vendor**: Walmart is your most frequent vendor (28 visits)")

    st.divider()

    # RECENT TRANSACTIONS=
    st.subheader("📋 Recent Transactions")
    
    transactions_data = {
        'Date': ['2026-01-03', '2026-01-03', '2026-01-02', '2026-01-02', '2026-01-01', '2025-12-31', '2025-12-30', '2025-12-29'],
        'Vendor': ['Walmart', 'Starbucks', 'Amazon', 'Whole Foods', 'Target', 'Best Buy', 'CVS', 'Chipotle'],
        'Category': ['Groceries', 'Dining', 'Electronics', 'Groceries', 'Shopping', 'Electronics', 'Health', 'Dining'],
        'Amount': ['$45.99', '$5.50', '$89.99', '$62.30', '$78.50', '$125.00', '$22.15', '$14.75'],
        'Payment Method': ['Credit Card', 'Debit Card', 'Credit Card', 'Credit Card', 'Debit Card', 'Credit Card', 'Credit Card', 'Debit Card']
    }
    df_transactions = pd.DataFrame(transactions_data)
    
    st.dataframe(df_transactions, use_container_width=True, hide_index=True)

    st.divider()

    # CATEGORY BREAKDOWN
    st.subheader("📊 Detailed Category Breakdown")
    
    category_breakdown = {
        'Category': ['Groceries', 'Electronics', 'Dining', 'Shopping', 'Utilities', 'Health & Beauty', 'Entertainment', 'Travel'],
        'Amount': [1200, 950, 850, 680, 520, 280, 200, 329],
        'Transactions': [45, 18, 32, 28, 12, 15, 8, 5],
        'Avg per Transaction': [26.67, 52.78, 26.56, 24.29, 43.33, 18.67, 25.00, 65.80]
    }
    df_breakdown = pd.DataFrame(category_breakdown)
    
    st.dataframe(df_breakdown, use_container_width=True, hide_index=True)

    st.divider()

    # MONTHLY COMPARISON
    st.subheader("📅 Category Spending Comparison (Last 3 Months)")
    
    comparison_data = {
        'Category': ['Groceries', 'Electronics', 'Dining', 'Shopping', 'Utilities'],
        'November': [350, 450, 280, 220, 200],
        'December': [400, 280, 350, 200, 150],
        'January': [450, 220, 220, 260, 170]
    }
    df_comparison = pd.DataFrame(comparison_data)
    
    fig5 = px.bar(df_comparison, x='Category', 
                  y=['November', 'December', 'January'],
                  barmode='group',
                  title='Category Spending Trends',
                  height=350,
                  color_discrete_sequence=['#3498db', '#2ecc71', '#e74c3c'])
    fig5.update_layout(
        margin=dict(l=0, r=0, t=40, b=0),
        yaxis_title='Amount ($)',
        xaxis_title='Category',
        hovermode='x unified'
    )
    st.plotly_chart(fig5, use_container_width=True)


# PAGE: UPLOAD & PROCESS
def page_upload_process():
    st.title("🧾 Document Upload")
    st.markdown("Upload receipts or invoices for automated digitization.")
    st.divider()

    # MAIN LAYOUT
    col1, col2 = st.columns([1, 2])

    # COLUMN 1: UPLOAD
    with col1:
        st.subheader("1. Input")
        uploaded_file = st.file_uploader(
            "Select File", 
            type=["jpg", "jpeg", "png"], 
            help="Supported formats: JPG, PNG. Max size 5MB."
        )

        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(image, caption="Original", use_container_width=True)
            
            if st.button("🚀 Process Document", type="primary", use_container_width=True):
                with st.spinner("Processing..."):
                    try:
                        processed_img = preprocess_image(image)
                        st.session_state.processed_image = processed_img
                        text, conf = run_ocr(processed_img)
                        st.session_state.ocr_result = text
                        st.session_state.confidence = conf
                        st.session_state.processed = True
                    except Exception as e:
                        st.error(f"Error: {e}")

    # COLUMN 2: RESULTS
    with col2:
        if st.session_state.processed:
            st.subheader("2. Results")
            
            tab_view, tab_raw, tab_data = st.tabs(["👁️ Visual", "📝 Text", "📝 Data"])
            
            with tab_view:
                c1, c2 = st.columns(2)
                with c1:
                    st.image(st.session_state.processed_image, caption="Preprocessed", use_container_width=True)
                with c2:
                    # CONFIDENCE METRIC
                    st.markdown("**Confidence Metrics**")
                    if st.session_state.confidence > 80:
                        st.metric("OCR Confidence", f"{st.session_state.confidence}%", "High")
                    elif st.session_state.confidence > 50:
                        st.metric("OCR Confidence", f"{st.session_state.confidence}%", delta_color="off")
                    else:
                        st.metric("OCR Confidence", f"{st.session_state.confidence}%", "Low", delta_color="inverse")
                    st.progress(st.session_state.confidence / 100)

            with tab_raw:
                st.text_area("Extracted Text", value=st.session_state.ocr_result, height=400)
                st.download_button("Download .txt", st.session_state.ocr_result, "invoice.txt")

            with tab_data:
                st.json({"filename": uploaded_file.name if uploaded_file else "N/A", "image_mode": image.mode if uploaded_file else "N/A"})
                
        else:
            st.info("👈 Upload a document to begin.")

# PAGE: HISTORY
def page_history():
    st.title("🕒 Upload History")
    st.markdown("View previously digitized documents and export reports.")
    st.divider()

    # Placeholder Table
    st.info("🚧 Database Connection Pending (Milestone 3)")

    # Example of what this will look like later
    st.text("Preview of future data structure:")
    st.dataframe({
        "Date": ["2023-10-01", "2023-10-02"],
        "Vendor": ["Walmart", "Amazon"],
        "Total": ["$45.20", "$12.99"],
        "Status": ["Verified", "Pending Review"]
    })

# MAIN APP ROUTING
if st.session_state.current_page == "Dashboard":
    page_dashboard()
elif st.session_state.current_page == "Upload & Process":
    page_upload_process()
elif st.session_state.current_page == "History":
    page_history()