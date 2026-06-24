import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import math

# Page config with modern editorial design styling
st.set_page_config(
    page_title="ECB Sovereign Churn Index",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Deep custom style injection
st.markdown("""
<style>
    /* Editorial styling */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=JetBrains+Mono:wght@400;500&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .serif-title {
        font-family: 'Playfair Display', serif;
        font-size: 2.5rem;
        font-weight: 700;
        color: #1a1a1a;
        margin-bottom: 0.5rem;
    }
    .serif-subtitle {
        font-family: 'Playfair Display', serif;
        font-style: italic;
        font-size: 1.5rem;
        color: #c53030;
        margin-bottom: 1.5rem;
    }
    
    .mono-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: #718096;
    }
    
    /* Elegant KPI Card borders */
    .kpi-card {
        border: 1px solid #1a1a1a;
        padding: 1.5rem;
        background-color: #fdfdfb;
        margin-bottom: 1rem;
    }
    
    /* Footer */
    .ecb-footer {
        border-top: 1px solid rgba(0,0,0,0.1);
        padding-top: 1rem;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem;
        color: #718096;
        text-transform: uppercase;
        display: flex;
        justify-content: space-between;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# DETERMINISTIC DATA GENERATION ENGINE (REPLICATING TS DATASET)
# -----------------------------------------------------------------------------
class SeededRandom:
    def __init__(self, seed=101):
        self.s = seed
    def next_val(self):
        # Replicating JavaScript: Math.sin(s++) * 10000; x - Math.floor(x)
        x = math.sin(self.s) * 10000
        self.s += 1
        return x - math.floor(x)

def shuffle_array(arr, rnd):
    for i in range(len(arr) - 1, 0, -1):
        j = int(math.floor(rnd.next_val() * (i + 1)))
        arr[i], arr[j] = arr[j], arr[i]

@st.cache_data
def load_and_generate_dataset():
    surnames = [
        "Smith", "Jones", "Taylor", "Brown", "Wilson", "Davies", "Evans", "Thomas", "Roberts", "Hargrave",
        "Hill", "Boni", "Mitchell", "Chu", "Bartlett", "Obinna", "Andrews", "Kay", "Chin", "Scott",
        "Goforth", "Romeo", "Henderson", "Muldrow", "Hao", "McDonald", "Dellucci", "Gerasimov", "Mosman", "Yen"
    ]
    
    rnd = SeededRandom(101)
    customers = []
    current_id = 15560000

    cohorts = [
        # 1. France Exited (810 total)
        {
            'geography': 'France', 'exited': 1, 'count': 810,
            'activeCount': 290,
            'ageGroupSplits': { '<30': 44, '30-45': 400, '46-60': 318, '60+': 48 },
            'creditSplits': { 'Low': 210, 'Medium': 520, 'High': 80 },
            'balanceSplits': { 'Zero': 300, 'LowMid': 90, 'HighBal': 420 },
            'productSplits': { 1: 570, 2: 140, 3: 80, 4: 20 },
            'genderSplits': { 'Female': 410, 'Male': 400 }
        },
        # 2. France Retained (4204 total)
        {
            'geography': 'France', 'exited': 0, 'count': 4204,
            'activeCount': 2330,
            'ageGroupSplits': { '<30': 850, '30-45': 2700, '46-60': 332, '60+': 322 },
            'creditSplits': { 'Low': 1000, 'Medium': 2800, 'High': 404 },
            'balanceSplits': { 'Zero': 1600, 'LowMid': 854, 'HighBal': 1750 },
            'productSplits': { 1: 1930, 2: 2250, 3: 24, 4: 0 },
            'genderSplits': { 'Female': 1900, 'Male': 2304 }
        },
        # 3. Germany Exited (814 total)
        {
            'geography': 'Germany', 'exited': 1, 'count': 814,
            'activeCount': 295,
            'ageGroupSplits': { '<30': 45, '30-45': 387, '46-60': 338, '60+': 44 },
            'creditSplits': { 'Low': 218, 'Medium': 513, 'High': 83 },
            'balanceSplits': { 'Zero': 0, 'LowMid': 109, 'HighBal': 705 },
            'productSplits': { 1: 578, 2: 126, 3: 86, 4: 24 },
            'genderSplits': { 'Female': 448, 'Male': 366 }
        },
        # 4. Germany Retained (1695 total)
        {
            'geography': 'Germany', 'exited': 0, 'count': 1695,
            'activeCount': 955,
            'ageGroupSplits': { '<30': 350, '30-45': 1112, '46-60': 164, '60+': 69 },
            'creditSplits': { 'Low': 400, 'Medium': 1100, 'High': 195 },
            'balanceSplits': { 'Zero': 0, 'LowMid': 293, 'HighBal': 1402 },
            'productSplits': { 1: 771, 2: 914, 3: 10, 4: 0 },
            'genderSplits': { 'Female': 745, 'Male': 950 }
        },
        # 5. Spain Exited (413 total)
        {
            'geography': 'Spain', 'exited': 1, 'count': 413,
            'activeCount': 150,
            'ageGroupSplits': { '<30': 47, '30-45': 81, '46-60': 149, '60+': 136 },
            'creditSplits': { 'Low': 100, 'Medium': 280, 'High': 33 },
            'balanceSplits': { 'Zero': 243, 'LowMid': 84, 'HighBal': 86 },
            'productSplits': { 1: 261, 2: 82, 3: 54, 4: 16 },
            'genderSplits': { 'Female': 217, 'Male': 196 }
        },
        # 6. Spain Retained (2064 total)
        {
            'geography': 'Spain', 'exited': 0, 'count': 2064,
            'activeCount': 1131,
            'ageGroupSplits': { '<30': 472, '30-45': 1148, '46-60': 142, '60+': 302 },
            'creditSplits': { 'Low': 483, 'Medium': 1408, 'High': 173 },
            'balanceSplits': { 'Zero': 1213, 'LowMid': 415, 'HighBal': 436 },
            'productSplits': { 1: 974, 2: 1078, 3: 12, 4: 0 },
            'genderSplits': { 'Female': 950, 'Male': 1114 }
        }
    ]

    for c in cohorts:
        listIsActive = []
        listAgeGroup = []
        listCreditBand = []
        listBalanceSegment = []
        listNumProducts = []
        listGender = []

        for _ in range(c['activeCount']): listIsActive.append(1)
        for _ in range(c['count'] - c['activeCount']): listIsActive.append(0)

        for k, amt in c['ageGroupSplits'].items():
            for _ in range(amt): listAgeGroup.append(k)

        for k, amt in c['creditSplits'].items():
            for _ in range(amt): listCreditBand.append(k)

        for k, amt in c['balanceSplits'].items():
            for _ in range(amt): listBalanceSegment.append(k)

        for k, amt in c['productSplits'].items():
            for _ in range(amt): listNumProducts.append(int(k))

        for k, amt in c['genderSplits'].items():
            for _ in range(amt): listGender.append(k)

        shuffle_array(listIsActive, rnd)
        shuffle_array(listAgeGroup, rnd)
        shuffle_array(listCreditBand, rnd)
        shuffle_array(listBalanceSegment, rnd)
        shuffle_array(listNumProducts, rnd)
        shuffle_array(listGender, rnd)

        for i in range(c['count']):
            gender = listGender[i]
            ageGroup = listAgeGroup[i]
            creditBand = listCreditBand[i]
            balanceSegment = listBalanceSegment[i]
            numProds = listNumProducts[i]
            isActive = listIsActive[i]

            age = 35
            if ageGroup == '<30':
                age = int(math.floor(18 + rnd.next_val() * 12))
            elif ageGroup == '30-45':
                age = int(math.floor(30 + rnd.next_val() * 16))
            elif ageGroup == '46-60':
                age = int(math.floor(46 + rnd.next_val() * 15))
            else:
                age = int(math.floor(61 + rnd.next_val() * 26))

            creditScore = 650
            if creditBand == 'Low':
                creditScore = int(math.floor(350 + rnd.next_val() * 230))
            elif creditBand == 'Medium':
                creditScore = int(math.floor(580 + rnd.next_val() * 141))
            else:
                creditScore = int(math.floor(721 + rnd.next_val() * 130))

            balance = 0.0
            if balanceSegment == 'LowMid':
                balance = round(5000 + rnd.next_val() * 94999, 2)
            elif balanceSegment == 'HighBal':
                balance = round(100000 + rnd.next_val() * 115000, 2)

            salary = 100000
            if c['exited'] == 1:
                salary = round(60000 + rnd.next_val() * 80000, 2)
            else:
                salary = round(1000 + rnd.next_val() * 188000, 2)

            current_id += 1
            customers.append({
                "Year": 2025,
                "CustomerId": current_id,
                "Surname": surnames[int(math.floor(rnd.next_val() * len(surnames)))],
                "CreditScore": creditScore,
                "Geography": c['geography'],
                "Gender": gender,
                "Age": age,
                "Tenure": int(math.floor(rnd.next_val() * 11)),
                "Balance": balance,
                "NumOfProducts": numProds,
                "HasCrCard": 1 if rnd.next_val() < 0.705 else 0,
                "IsActiveMember": isActive,
                "EstimatedSalary": salary,
                "Exited": c['exited']
            })

    # Financial scaling to achieve EXACT statistics
    hv_churned = [c for c in customers if c['Balance'] >= 100000 and c['Exited'] == 1]
    if len(hv_churned) == 1211:
        current_balance_sum = sum(c['Balance'] for c in hv_churned)
        balance_target = 185588094.63
        balance_factor = balance_target / current_balance_sum

        bal_cum_adjustment = 0.0

        for i in range(len(hv_churned)):
            c = hv_churned[i]
            
            new_bal_raw = c['Balance'] * balance_factor
            new_bal_rounded = max(100000.01, round(new_bal_raw, 2))
            bal_cum_adjustment += (new_bal_raw - new_bal_rounded)
            c['Balance'] = new_bal_rounded

        last_c = hv_churned[-1]
        last_c['Balance'] = round(last_c['Balance'] + bal_cum_adjustment, 2)

    shuffle_array(customers, rnd)

    return pd.DataFrame(customers)

# Helper function to categorize variables
def get_age_group(age):
    if age < 30: return '<30'
    if age <= 45: return '30-45'
    if age <= 60: return '46-60'
    return '60+'

def get_credit_score_band(score):
    if score < 580: return 'Low'
    if score <= 720: return 'Medium'
    return 'High'

def get_tenure_group(tenure):
    if tenure <= 2: return 'New'
    if tenure <= 6: return 'Mid-term'
    return 'Long-term'

# Load the data
df = load_and_generate_dataset()

# Inject helper classifications
df['AgeGroup'] = df['Age'].apply(get_age_group)
df['CreditBand'] = df['CreditScore'].apply(get_credit_score_band)
df['TenureGroup'] = df['Tenure'].apply(get_tenure_group)
df['BalanceSegment'] = df['Balance'].apply(lambda b: 'Zero-balance' if b == 0 else ('Low-balance (<100k)' if b < 100000 else 'High-balance (>=100k)'))

# -----------------------------------------------------------------------------
# SIDEBAR FILTERS PANEL
# -----------------------------------------------------------------------------
st.sidebar.markdown("<div class='mono-label'>Control Protocol</div>", unsafe_allow_html=True)
st.sidebar.title("Filter Criteria")

geo_options = sorted(list(df['Geography'].unique()))
sel_geo = st.sidebar.multiselect("Geography Region", geo_options, default=[])

gender_options = sorted(list(df['Gender'].unique()))
sel_gender = st.sidebar.multiselect("Gender", gender_options, default=[])

age_options = ['<30', '30-45', '46-60', '60+']
sel_age = st.sidebar.multiselect("Age Group", age_options, default=[])

credit_options = ['Low', 'Medium', 'High']
sel_credit = st.sidebar.multiselect("Credit Score Band", credit_options, default=[])

tenure_options = ['New', 'Mid-term', 'Long-term']
sel_tenure = st.sidebar.multiselect("Tenure Category", tenure_options, default=[])

balance_options = ['Zero-balance', 'Low-balance (<100k)', 'High-balance (>=100k)']
sel_balance = st.sidebar.multiselect("Balance Segment", balance_options, default=[])

activity_options = [("Active Member", 1), ("Inactive Member", 0)]
sel_activity = st.sidebar.multiselect("Engagement Status", activity_options, format_func=lambda x: x[0], default=[])

card_options = [("Has Credit Card", 1), ("No Credit Card", 0)]
sel_card = st.sidebar.multiselect("Credit Card ownership", card_options, format_func=lambda x: x[0], default=[])

# Apply filters reactively
filtered_df = df.copy()
if sel_geo:
    filtered_df = filtered_df[filtered_df['Geography'].isin(sel_geo)]
if sel_gender:
    filtered_df = filtered_df[filtered_df['Gender'].isin(sel_gender)]
if sel_age:
    filtered_df = filtered_df[filtered_df['AgeGroup'].isin(sel_age)]
if sel_credit:
    filtered_df = filtered_df[filtered_df['CreditBand'].isin(sel_credit)]
if sel_tenure:
    filtered_df = filtered_df[filtered_df['TenureGroup'].isin(sel_tenure)]
if sel_balance:
    filtered_df = filtered_df[filtered_df['BalanceSegment'].isin(sel_balance)]
if sel_activity:
    filtered_df = filtered_df[filtered_df['IsActiveMember'].isin([val[1] for val in sel_activity])]
if sel_card:
    filtered_df = filtered_df[filtered_df['HasCrCard'].isin([val[1] for val in sel_card])]

# -----------------------------------------------------------------------------
# MAIN HEADER
# -----------------------------------------------------------------------------
st.markdown("<span class='mono-label'>European Central Bank — Supervisory Board</span>", unsafe_allow_html=True)
st.markdown("<div class='serif-title'>Banking Churn Pattern Analysis</div>", unsafe_allow_html=True)
st.markdown("<div class='serif-subtitle'>Supervisory Audit of Western European Retail Portfolio (10,000 Clients)</div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# HIGH-LEVEL KEY METRIC HEROES
# -----------------------------------------------------------------------------
col1, col2, col3 = st.columns(3)

# Calculate KPIs
total_customers = len(filtered_df)
churned_df = filtered_df[filtered_df['Exited'] == 1]
retained_df = filtered_df[filtered_df['Exited'] == 0]

overall_churn_rate = (len(churned_df) / total_customers * 100) if total_customers > 0 else 0.0

# High-balance definition (Balance >= 100k)
high_bal_df = filtered_df[filtered_df['Balance'] >= 100000]
high_bal_churn = high_bal_df[high_bal_df['Exited'] == 1]
high_value_risk_rate = (len(high_bal_churn) / len(high_bal_df) * 100) if len(high_bal_df) > 0 else 0.0

assets_at_risk = churned_df['Balance'].sum()

with col1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="mono-label">Overall Churn Index</div>
        <div style="font-size: 2.2rem; font-weight: 700; color: #c53030; margin: 0.2rem 0;">{overall_churn_rate:.2f}%</div>
        <div style="font-size: 0.8rem; color: #4a5568;">Total Portfolio Risk baseline</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="mono-label">High-Value Risk Rate</div>
        <div style="font-size: 2.2rem; font-weight: 700; color: #1a1a1a; margin: 0.2rem 0;">{high_value_risk_rate:.2f}%</div>
        <div style="font-size: 0.8rem; color: #4a5568;">Risk for Balances &ge; 100,000 &euro;</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="mono-label">Assets At Churn Risk</div>
        <div style="font-size: 2.2rem; font-weight: 700; color: #1a1a1a; margin: 0.2rem 0;">&euro;{assets_at_risk:,.0f}</div>
        <div style="font-size: 0.8rem; color: #4a5568;">Total Balance of Exited Clients</div>
    </div>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# INTERACTIVE WORKSPACE TABS
# -----------------------------------------------------------------------------
tab_summary, tab_ledger, tab_geography, tab_premium = st.tabs([
    "📈 Executive Summary", 
    "📊 Segment Churn Ledger", 
    "🌍 Geographic Profile", 
    "💎 High-Value Risk Explorer"
])

# -----------------------------------------------------------------------------
# TAB 1: EXECUTIVE SUMMARY
# -----------------------------------------------------------------------------
with tab_summary:
    col_header, col_btn = st.columns([2, 1])
    with col_header:
        st.markdown("<h3 style='font-family:Playfair Display, serif; italic; margin: 0;'>Portfolio Vulnerability Indicators</h3>", unsafe_allow_html=True)
    with col_btn:
        if not filtered_df.empty:
            csv_data = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Dataset (CSV)",
                data=csv_data,
                file_name=f"ecb_churn_filtered_{len(filtered_df)}_records.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.button("📥 Download Dataset (CSV)", disabled=True, use_container_width=True)
    
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        # Chart 1: Products Churn Rate
        prod_rates = []
        for p in [1, 2, 3, 4]:
            p_df = filtered_df[filtered_df['NumOfProducts'] == p]
            p_churn = len(p_df[p_df['Exited'] == 1])
            p_rate = (p_churn / len(p_df) * 100) if len(p_df) > 0 else 0.0
            prod_rates.append({"Products": f"{p} Product(s)", "Churn Rate (%)": round(p_rate, 2)})
        
        prod_chart_df = pd.DataFrame(prod_rates)
        fig_prod = px.bar(
            prod_chart_df, 
            x="Products", 
            y="Churn Rate (%)",
            title="Product Multiplier Churn Index (Critical Warning for Bloated Accounts)",
            text="Churn Rate (%)",
            color_discrete_sequence=["#1a1a1a"]
        )
        fig_prod.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            yaxis_range=[0, 105]
        )
        fig_prod.update_traces(
            marker_color=["#1a1a1a", "#1a1a1a", "#c53030", "#c53030"],
            textposition="outside"
        )
        st.plotly_chart(fig_prod, use_container_width=True)
        
    with col_right:
        # Member activity churn rate
        act_rates = []
        for state, name in [(1, "Active Member"), (0, "Inactive Member")]:
            a_df = filtered_df[filtered_df['IsActiveMember'] == state]
            a_churn = len(a_df[a_df['Exited'] == 1])
            a_rate = (a_churn / len(a_df) * 100) if len(a_df) > 0 else 0.0
            act_rates.append({"Status": name, "Churn Rate (%)": round(a_rate, 2)})
            
        act_chart_df = pd.DataFrame(act_rates)
        fig_act = px.bar(
            act_chart_df,
            x="Status",
            y="Churn Rate (%)",
            title="Engagement Risk Gap",
            color="Status",
            color_discrete_map={"Active Member": "#1a1a1a", "Inactive Member": "#c53030"}
        )
        fig_act.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            showlegend=False
        )
        st.plotly_chart(fig_act, use_container_width=True)

    st.markdown("""
    <div style="background-color: #f4f3ef; border: 1px solid #1a1a1a; padding: 1.5rem; margin-top: 1rem;">
        <span class="mono-label">ECB Supervisory Findings</span>
        <h4 style="font-family:'Playfair Display', serif; margin: 0.5rem 0;">Product Bloat Churn Correlation</h4>
        <p style="font-size: 0.85rem; line-height: 1.6; color: #2d3748;">
            A key focal point of this supervisory audit is the product utilization profile. While customers holding <strong>two products</strong> represent the most stable client segment with exceptionally low churn rates (~7.58%), customers holding <strong>three or four bank products exhibit catastrophic churn rates near 82.71% and 100% respectively</strong>. This suggests that aggressive cross-selling strategies beyond two products create immediate frictional exits rather than locking in long-term customer value.
        </p>
    </div>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# TAB 2: COMPREHENSIVE SEGMENT CHURN LEDGER
# -----------------------------------------------------------------------------
with tab_ledger:
    st.markdown("<h3 style='font-family:Playfair Display, serif; italic'>Advanced Segment Metrics and Interactions</h3>", unsafe_allow_html=True)
    
    segments_to_analyze = [
        # Geography
        ("France", "Geography", lambda d: d['Geography'] == 'France'),
        ("Spain", "Geography", lambda d: d['Geography'] == 'Spain'),
        ("Germany", "Geography", lambda d: d['Geography'] == 'Germany'),
        
        # Age Groups
        ("<30", "Age Group", lambda d: d['AgeGroup'] == '<30'),
        ("30-45", "Age Group", lambda d: d['AgeGroup'] == '30-45'),
        ("46-60", "Age Group", lambda d: d['AgeGroup'] == '46-60'),
        ("60+", "Age Group", lambda d: d['AgeGroup'] == '60+'),
        
        # Credit Bands
        ("Low Credit Score (<580)", "Credit Rating", lambda d: d['CreditBand'] == 'Low'),
        ("Medium Credit Score (580-720)", "Credit Rating", lambda d: d['CreditBand'] == 'Medium'),
        ("High Credit Score (>720)", "Credit Rating", lambda d: d['CreditBand'] == 'High'),
        
        # Tenure
        ("New (0-2y)", "Tenure", lambda d: d['TenureGroup'] == 'New'),
        ("Mid-term (3-6y)", "Tenure", lambda d: d['TenureGroup'] == 'Mid-term'),
        ("Long-term (7-10y)", "Tenure", lambda d: d['TenureGroup'] == 'Long-term'),
        
        # Balance Segment
        ("Zero Balance", "Financial Segment", lambda d: d['BalanceSegment'] == 'Zero-balance'),
        ("Low Balance (<100k)", "Financial Segment", lambda d: d['BalanceSegment'] == 'Low-balance (<100k)'),
        ("High Balance (>=100k)", "Financial Segment", lambda d: d['BalanceSegment'] == 'High-balance (>=100k)'),
        
        # Gender
        ("Male", "Demographics", lambda d: d['Gender'] == 'Male'),
        ("Female", "Demographics", lambda d: d['Gender'] == 'Female'),
        
        # Activity
        ("Active Member", "Engagement", lambda d: d['IsActiveMember'] == 1),
        ("Inactive Member", "Engagement", lambda d: d['IsActiveMember'] == 0),
        
        # Products
        ("1 Product", "Products Owned", lambda d: d['NumOfProducts'] == 1),
        ("2 Products", "Products Owned", lambda d: d['NumOfProducts'] == 2),
        ("3 Products", "Products Owned", lambda d: d['NumOfProducts'] == 3),
        ("4 Products", "Products Owned", lambda d: d['NumOfProducts'] == 4),
    ]
    
    total_bank_exited = len(filtered_df[filtered_df['Exited'] == 1])
    ledger_records = []
    
    for name, cat, filter_fn in segments_to_analyze:
        seg_df = filtered_df[filter_fn(filtered_df)]
        seg_size = len(seg_df)
        pct_of_bank = (seg_size / len(filtered_df) * 100) if len(filtered_df) > 0 else 0.0
        
        seg_churned_df = seg_df[seg_df['Exited'] == 1]
        seg_churn_count = len(seg_churned_df)
        seg_churn_rate = (seg_churn_count / seg_size * 100) if seg_size > 0 else 0.0
        
        churn_contribution = (seg_churn_count / total_bank_exited * 100) if total_bank_exited > 0 else 0.0
        
        ledger_records.append({
            "Segment Name": name,
            "Category": cat,
            "Population (Count)": seg_size,
            "Bank Share (%)": round(pct_of_bank, 1),
            "Exited (Count)": seg_churn_count,
            "Churn Rate (%)": round(seg_churn_rate, 2),
            "Overall Churn Contribution (%)": round(churn_contribution, 1)
        })
        
    ledger_df = pd.DataFrame(ledger_records)
    
    # Interactive filters for ledger
    st.markdown("<span class='mono-label'>Filter Ledger Grid</span>", unsafe_allow_html=True)
    cols_ledger = st.columns(3)
    with cols_ledger[0]:
        filter_cat = st.selectbox("Select Category", ["All"] + list(ledger_df['Category'].unique()))
    with cols_ledger[1]:
        search_seg = st.text_input("Search Segment", "")
    with cols_ledger[2]:
        sort_by = st.selectbox("Sort Ledger By", ["Churn Rate (%)", "Population (Count)", "Overall Churn Contribution (%)"])
        
    # Apply local ledger filters
    display_ledger = ledger_df.copy()
    if filter_cat != "All":
        display_ledger = display_ledger[display_ledger['Category'] == filter_cat]
    if search_seg:
        display_ledger = display_ledger[display_ledger['Segment Name'].str.lower().str.contains(search_seg.lower())]
        
    display_ledger = display_ledger.sort_values(by=sort_by, ascending=False)
    
    st.dataframe(
        display_ledger,
        column_config={
            "Churn Rate (%)": st.column_config.ProgressColumn(
                "Segment Churn Rate",
                help="Churn percentage within this specific segment",
                format="%.2f%%",
                min_value=0.0,
                max_value=100.0,
            ),
            "Overall Churn Contribution (%)": st.column_config.ProgressColumn(
                "Share of All Bank Churners",
                help="What percentage of total bank exiters belong to this segment",
                format="%.1f%%",
                min_value=0.0,
                max_value=100.0,
            )
        },
        use_container_width=True,
        hide_index=True
    )
    
    # Geography-Age Interaction Bar Chart
    st.markdown("<h4 style='font-family:Playfair Display, serif; margin-top: 2rem;'>Geography x Age Group Interaction Matrix</h4>", unsafe_allow_html=True)
    
    interaction_records = []
    for geo in ['France', 'Spain', 'Germany']:
        for age in ['<30', '30-45', '46-60', '60+']:
            cell_df = filtered_df[(filtered_df['Geography'] == geo) & (filtered_df['AgeGroup'] == age)]
            cell_size = len(cell_df)
            cell_churn = len(cell_df[cell_df['Exited'] == 1])
            cell_rate = (cell_churn / cell_size * 100) if cell_size > 0 else 0.0
            interaction_records.append({
                "Geography": geo,
                "Age Group": age,
                "Churn Rate (%)": round(cell_rate, 2),
                "Active Population": cell_size
            })
            
    interaction_df = pd.DataFrame(interaction_records)
    
    fig_inter = px.bar(
        interaction_df,
        x="Geography",
        y="Churn Rate (%)",
        color="Age Group",
        barmode="group",
        text="Churn Rate (%)",
        title="Localized Churn risk (Geography x Age Interaction)",
        color_discrete_sequence=["#a0aec0", "#4a5568", "#c53030", "#1a1a1a"]
    )
    fig_inter.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig_inter, use_container_width=True)

# -----------------------------------------------------------------------------
# TAB 3: GEOGRAPHIC PROFILE
# -----------------------------------------------------------------------------
with tab_geography:
    st.markdown("<h3 style='font-family:Playfair Display, serif; italic'>Sovereign Jurisdiction Metrics</h3>", unsafe_allow_html=True)
    
    geo_metrics = []
    for geo in ['France', 'Spain', 'Germany']:
        g_df = filtered_df[filtered_df['Geography'] == geo]
        g_size = len(g_df)
        g_churn = len(g_df[g_df['Exited'] == 1])
        g_rate = (g_churn / g_size * 100) if g_size > 0 else 0.0
        g_bal = g_df['Balance'].mean() if g_size > 0 else 0.0
        geo_metrics.append({
            "Geography": geo,
            "Customer Count": g_size,
            "Churn Count": g_churn,
            "Churn Rate (%)": round(g_rate, 2),
            "Average Balance (&euro;)": round(g_bal, 2)
        })
        
    geo_metrics_df = pd.DataFrame(geo_metrics)
    
    col_g1, col_g2 = st.columns([1, 1])
    with col_g1:
        st.dataframe(geo_metrics_df, use_container_width=True, hide_index=True)
        
    with col_g2:
        fig_geo = px.bar(
            geo_metrics_df,
            x="Geography",
            y="Churn Rate (%)",
            title="Baseline Churn Rate by Nation State",
            text="Churn Rate (%)",
            color_discrete_sequence=["#1a1a1a"]
        )
        fig_geo.update_traces(
            marker_color=["#1a1a1a" if g != 'Germany' else '#c53030' for g in geo_metrics_df["Geography"]],
            textposition="outside"
        )
        fig_geo.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_geo, use_container_width=True)

# -----------------------------------------------------------------------------
# TAB 4: HIGH-VALUE RISK EXPLORER
# -----------------------------------------------------------------------------
with tab_premium:
    st.markdown("<h3 style='font-family:Playfair Display, serif; italic'>Balance vs Salary Correlation Analysis</h3>", unsafe_allow_html=True)
    
    positive_bal_df = filtered_df[filtered_df['Balance'] > 0]
    
    if len(positive_bal_df) > 0:
        # Downsample deterministically to avoid plot lag while keeping shape
        stride = max(1, len(positive_bal_df) // 250)
        plot_df = positive_bal_df.iloc[::stride].copy()
        plot_df['Churn Status'] = plot_df['Exited'].apply(lambda x: 'Exited (Churned)' if x == 1 else 'Active (Retained)')
        
        fig_scatter = px.scatter(
            plot_df,
            x="EstimatedSalary",
            y="Balance",
            color="Churn Status",
            hover_data=["Surname", "Age", "Geography"],
            title="Balance vs Estimated Salary Dispersion Map (High Balance clustering)",
            color_discrete_map={"Exited (Churned)": "#c53030", "Active (Retained)": "rgba(26,26,26,0.4)"}
        )
        fig_scatter.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        st.info("No premium accounts with active positive balances in the filtered subset.")
        
    # Table of Top Premium at Risk accounts
    st.markdown("<h4 style='font-family:Playfair Display, serif;'>Top Risk Portfolio Accounts</h4>", unsafe_allow_html=True)
    risk_premium = filtered_df[(filtered_df['Balance'] >= 140000) & (filtered_df['Exited'] == 1)].head(5)
    
    if len(risk_premium) > 0:
        st.dataframe(
            risk_premium[['Surname', 'Geography', 'Gender', 'Age', 'Balance', 'EstimatedSalary']],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No high-risk accounts (&ge; 140,000 &euro; Balance & Exited) matching active filters.")

# -----------------------------------------------------------------------------
# FOOTER
# -----------------------------------------------------------------------------
st.markdown("<br/><br/>", unsafe_allow_html=True)
st.markdown("""
<div class="ecb-footer">
    <span>ECB Churn Index Engine &copy; 2026</span>
    <span>Sovereign Jurisdiction Oversight Framework — Python 3.11 / Streamlit 1.32</span>
</div>
""", unsafe_allow_html=True)
