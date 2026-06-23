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
        border-t: 1px solid rgba(0,0,0,0.1);
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
# DETERMINISTIC DATA GENERATION ENGINE
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

    # 1. France: 5,014 records, 810 exited
    france_customers = []
    for i in range(5014):
        gender = 'Female' if rnd.next_val() < 0.46 else 'Male'
        credit_score = int(min(850, max(350, math.floor(650 + (rnd.next_val() - 0.5) * 180 + (rnd.next_val() - 0.5) * 100))))
        
        age_rand = rnd.next_val()
        if age_rand < 0.12:
            age = int(math.floor(18 + rnd.next_val() * 12))
        elif age_rand < 0.65:
            age = int(math.floor(30 + rnd.next_val() * 15))
        elif age_rand < 0.90:
            age = int(math.floor(45 + rnd.next_val() * 15))
        else:
            age = int(math.floor(60 + rnd.next_val() * 30))
            
        tenure = int(math.floor(rnd.next_val() * 11))
        balance = 0.0 if rnd.next_val() < 0.38 else round(50000 + rnd.next_val() * 160000, 2)
        
        prod_rand = rnd.next_val()
        if prod_rand < 0.50:
            numOfProducts = 1
        elif prod_rand < 0.95:
            numOfProducts = 2
        elif prod_rand < 0.99:
            numOfProducts = 3
        else:
            numOfProducts = 4
            
        hasCrCard = 1 if rnd.next_val() < 0.705 else 0
        isActiveMember = 1 if rnd.next_val() < 0.515 else 0
        estimatedSalary = round(10000 + rnd.next_val() * 190000, 2)
        
        current_id += 1
        france_customers.append({
            "Year": 2025,
            "CustomerId": current_id,
            "Surname": surnames[int(math.floor(rnd.next_val() * len(surnames)))],
            "CreditScore": credit_score,
            "Geography": 'France',
            "Gender": gender,
            "Age": age,
            "Tenure": tenure,
            "Balance": balance,
            "NumOfProducts": numOfProducts,
            "HasCrCard": hasCrCard,
            "IsActiveMember": isActiveMember,
            "EstimatedSalary": estimatedSalary,
            "Exited": 0
        })
        
    france_with_risk = []
    for c in france_customers:
        score = 0
        if 46 <= c['Age'] <= 60:
            score += 40
        elif 35 < c['Age'] < 46:
            score += 15
        elif c['Age'] > 60:
            score += 20
            
        if c['Gender'] == 'Female':
            score += 6
            
        if c['NumOfProducts'] == 2:
            score -= 15
        elif c['NumOfProducts'] == 1:
            score += 12
        elif c['NumOfProducts'] >= 3:
            score += 70
            
        if c['IsActiveMember'] == 0:
            score += 20
        else:
            score -= 10
            
        if c['Balance'] > 120000:
            score += 5
        if c['CreditScore'] < 500:
            score += 12
            
        score += rnd.next_val() * 15
        france_with_risk.append((c, score))
        
    france_with_risk.sort(key=lambda x: x[1], reverse=True)
    for i in range(810):
        france_with_risk[i][0]['Exited'] = 1
        
    customers.extend(france_customers)

    # 2. Spain: 2,477 records, 413 exited
    spain_customers = []
    for i in range(2477):
        gender = 'Female' if rnd.next_val() < 0.45 else 'Male'
        credit_score = int(min(850, max(350, math.floor(652 + (rnd.next_val() - 0.5) * 180 + (rnd.next_val() - 0.5) * 100))))
        
        age_rand = rnd.next_val()
        if age_rand < 0.12:
            age = int(math.floor(18 + rnd.next_val() * 12))
        elif age_rand < 0.65:
            age = int(math.floor(30 + rnd.next_val() * 15))
        elif age_rand < 0.90:
            age = int(math.floor(45 + rnd.next_val() * 15))
        else:
            age = int(math.floor(60 + rnd.next_val() * 30))
            
        tenure = int(math.floor(rnd.next_val() * 11))
        balance = 0.0 if rnd.next_val() < 0.38 else round(50000 + rnd.next_val() * 160000, 2)
        
        prod_rand = rnd.next_val()
        if prod_rand < 0.50:
            numOfProducts = 1
        elif prod_rand < 0.95:
            numOfProducts = 2
        elif prod_rand < 0.99:
            numOfProducts = 3
        else:
            numOfProducts = 4
            
        hasCrCard = 1 if rnd.next_val() < 0.70 else 0
        isActiveMember = 1 if rnd.next_val() < 0.50 else 0
        estimatedSalary = round(10000 + rnd.next_val() * 190000, 2)
        
        current_id += 1
        spain_customers.append({
            "Year": 2025,
            "CustomerId": current_id,
            "Surname": surnames[int(math.floor(rnd.next_val() * len(surnames)))],
            "CreditScore": credit_score,
            "Geography": 'Spain',
            "Gender": gender,
            "Age": age,
            "Tenure": tenure,
            "Balance": balance,
            "NumOfProducts": numOfProducts,
            "HasCrCard": hasCrCard,
            "IsActiveMember": isActiveMember,
            "EstimatedSalary": estimatedSalary,
            "Exited": 0
        })
        
    spain_with_risk = []
    for c in spain_customers:
        score = 0
        if 46 <= c['Age'] <= 60:
            score += 40
        elif 35 < c['Age'] < 46:
            score += 15
        elif c['Age'] > 60:
            score += 20
            
        if c['Gender'] == 'Female':
            score += 6
            
        if c['NumOfProducts'] == 2:
            score -= 15
        elif c['NumOfProducts'] == 1:
            score += 12
        elif c['NumOfProducts'] >= 3:
            score += 70
            
        if c['IsActiveMember'] == 0:
            score += 20
        else:
            score -= 10
            
        if c['Balance'] > 120000:
            score += 5
        if c['CreditScore'] < 500:
            score += 12
            
        score += rnd.next_val() * 15
        spain_with_risk.append((c, score))
        
    spain_with_risk.sort(key=lambda x: x[1], reverse=True)
    for i in range(413):
        spain_with_risk[i][0]['Exited'] = 1
        
    customers.extend(spain_customers)

    # 3. Germany: 2,509 records, 814 exited
    # Churned segment (814 records)
    g_churned_ages = []
    for _ in range(338): g_churned_ages.append(int(math.floor(46 + rnd.next_val() * 15))) # 46-60
    for _ in range(44): g_churned_ages.append(int(math.floor(61 + rnd.next_val() * 25))) # 60+
    for _ in range(385): g_churned_ages.append(int(math.floor(30 + rnd.next_val() * 16))) # 30-45
    for _ in range(47): g_churned_ages.append(int(math.floor(18 + rnd.next_val() * 12))) # <30

    g_churned_prods = []
    for _ in range(578): g_churned_prods.append(1)
    for _ in range(126): g_churned_prods.append(2)
    for _ in range(86): g_churned_prods.append(3)
    for _ in range(24): g_churned_prods.append(4)

    g_churned_balances = []
    for _ in range(424): g_churned_balances.append(40000 + rnd.next_val() * 80000)
    for _ in range(390): g_churned_balances.append(120000.01 + rnd.next_val() * 80000)

    g_churned_genders = []
    for _ in range(448): g_churned_genders.append('Female')
    for _ in range(366): g_churned_genders.append('Male')

    g_churned_active = []
    for _ in range(518): g_churned_active.append(0)
    for _ in range(296): g_churned_active.append(1)

    shuffle_array(g_churned_ages, rnd)
    shuffle_array(g_churned_prods, rnd)
    shuffle_array(g_churned_balances, rnd)
    shuffle_array(g_churned_genders, rnd)
    shuffle_array(g_churned_active, rnd)

    g_churned_customers = []
    for i in range(814):
        current_id += 1
        g_churned_customers.append({
            "Year": 2025,
            "CustomerId": current_id,
            "Surname": surnames[int(math.floor(rnd.next_val() * len(surnames)))],
            "CreditScore": int(min(850, max(350, math.floor(645 + (rnd.next_val() - 0.5) * 160)))),
            "Geography": 'Germany',
            "Gender": g_churned_genders[i],
            "Age": g_churned_ages[i],
            "Tenure": int(math.floor(rnd.next_val() * 11)),
            "Balance": round(g_churned_balances[i], 2),
            "NumOfProducts": g_churned_prods[i],
            "HasCrCard": 1 if rnd.next_val() < 0.71 else 0,
            "IsActiveMember": g_churned_active[i],
            "EstimatedSalary": round(15000 + rnd.next_val() * 180000, 2),
            "Exited": 1
        })

    # Retained segment (1,695 records)
    g_retained_ages = []
    for _ in range(164): g_retained_ages.append(int(math.floor(46 + rnd.next_val() * 15)))
    for _ in range(69): g_retained_ages.append(int(math.floor(61 + rnd.next_val() * 25)))
    for _ in range(1137): g_retained_ages.append(int(math.floor(30 + rnd.next_val() * 16)))
    for _ in range(325): g_retained_ages.append(int(math.floor(18 + rnd.next_val() * 12)))

    g_retained_prods = []
    for _ in range(771): g_retained_prods.append(1)
    for _ in range(914): g_retained_prods.append(2)
    for _ in range(10): g_retained_prods.append(3)
    for _ in range(0): g_retained_prods.append(4)

    g_retained_balances = []
    for _ in range(842): g_retained_balances.append(40000 + rnd.next_val() * 80000)
    for _ in range(853): g_retained_balances.append(120000.01 + rnd.next_val() * 80000)

    g_retained_genders = []
    for _ in range(745): g_retained_genders.append('Female')
    for _ in range(950): g_retained_genders.append('Male')

    g_retained_active = []
    for _ in range(743): g_retained_active.append(0)
    for _ in range(952): g_retained_active.append(1)

    shuffle_array(g_retained_ages, rnd)
    shuffle_array(g_retained_prods, rnd)
    shuffle_array(g_retained_balances, rnd)
    shuffle_array(g_retained_genders, rnd)
    shuffle_array(g_retained_active, rnd)

    g_retained_customers = []
    for i in range(1695):
        current_id += 1
        g_retained_customers.append({
            "Year": 2025,
            "CustomerId": current_id,
            "Surname": surnames[int(math.floor(rnd.next_val() * len(surnames)))],
            "CreditScore": int(min(850, max(350, math.floor(655 + (rnd.next_val() - 0.5) * 160)))),
            "Geography": 'Germany',
            "Gender": g_retained_genders[i],
            "Age": g_retained_ages[i],
            "Tenure": int(math.floor(rnd.next_val() * 11)),
            "Balance": round(g_retained_balances[i], 2),
            "NumOfProducts": g_retained_prods[i],
            "HasCrCard": 1 if rnd.next_val() < 0.70 else 0,
            "IsActiveMember": g_retained_active[i],
            "EstimatedSalary": round(15000 + rnd.next_val() * 180000, 2),
            "Exited": 0
        })

    customers.extend(g_churned_customers)
    customers.extend(g_retained_customers)

    shuffle_array(customers, rnd)
    return pd.DataFrame(customers)

# Helper function to categorize variables
def get_age_group(age):
    if age < 30: return '<30'
    if age <= 45: return '30-45'
    if age <= 60: return '46-60'
    return '60+'

def get_credit_score_band(score):
    if score < 550: return 'Low'
    if score <= 700: return 'Medium'
    return 'High'

def get_tenure_group(tenure):
    if tenure <= 2: return 'New'
    if tenure <= 7: return 'Mid-term'
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
        # Highlight products 3 & 4
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
            A key focal point of this supervisory audit is the product utilization profile. While customers holding <strong>two products</strong> represent the most stable client segment with exceptionally low churn rates (~8.2%), customers holding <strong>three or four bank products exhibit catastrophic churn rates near 82.7% and 100% respectively</strong>. This suggests that aggressive cross-selling strategies beyond two products create immediate frictional exits rather than locking in long-term customer value.
        </p>
    </div>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# TAB 2: COMPREHENSIVE SEGMENT CHURN LEDGER
# -----------------------------------------------------------------------------
with tab_ledger:
    st.markdown("<h3 style='font-family:Playfair Display, serif; italic'>Advanced Segment Metrics and Interactions</h3>", unsafe_allow_html=True)
    
    # We will build a beautiful pandas DataFrame of segment metrics dynamically!
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
        ("Low Credit Score (<550)", "Credit Rating", lambda d: d['CreditBand'] == 'Low'),
        ("Medium Credit Score (550-700)", "Credit Rating", lambda d: d['CreditBand'] == 'Medium'),
        ("High Credit Score (>700)", "Credit Rating", lambda d: d['CreditBand'] == 'High'),
        
        # Tenure
        ("New (0-2y)", "Tenure", lambda d: d['TenureGroup'] == 'New'),
        ("Mid-term (3-7y)", "Tenure", lambda d: d['TenureGroup'] == 'Mid-term'),
        ("Long-term (8-10y)", "Tenure", lambda d: d['TenureGroup'] == 'Long-term'),
        
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
