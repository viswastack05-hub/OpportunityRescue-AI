import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="OpportunityRescue AI",
    page_icon="🎯",
    layout="wide"
)

# Load Premium Dark UI
with open("style.css", "r") as css_file:
    st.markdown(
        f"<style>{css_file.read()}</style>",
        unsafe_allow_html=True
    )


st.title("🎯 OpportunityRescue AI")
st.subheader("Intelligent Sales Opportunity Recovery Agent")
st.caption("Identify risk • Understand objections • Recommend actions • Track outcomes")

sample = pd.DataFrame([
    ["OP001","BluePeak Technologies","Proposal",420000,11,5,"No response","Price concern"],
    ["OP002","GreenLeaf Retail","Negotiation",250000,4,0,"Replied","Implementation timeline"],
    ["OP003","Nova Systems","Qualified",180000,18,12,"No response","Unknown"],
    ["OP004","BrightPath Academy","Proposal",320000,7,2,"Asked for details","Budget approval"],
    ["OP005","Aster Logistics","Negotiation",560000,2,0,"Replied","Contract terms"]
], columns=["ID","Company","Stage","Deal Value","Days Since Contact","Overdue Days","Response","Objection"])

def analyse(r):
    inactivity = min(r["Days Since Contact"]/21,1)
    overdue = min(r["Overdue Days"]/14,1)
    response = 1 if r["Response"]=="No response" else 0.2
    risk = min(0.4*inactivity + 0.35*overdue + 0.25*response,1)
    recoverability = 0.8 if r["Response"]=="Replied" else 0.65
    priority = r["Deal Value"] * risk * recoverability
    return pd.Series([risk,recoverability,priority])

st.sidebar.header("CRM Data")
uploaded = st.sidebar.file_uploader("Upload opportunities CSV", type="csv")

if uploaded:
    df = pd.read_csv(uploaded)
    required = list(sample.columns)
    if not all(c in df.columns for c in required):
        st.error("CSV must contain these columns: " + ", ".join(required))
        st.stop()
else:
    df = sample.copy()
    st.sidebar.info("Using sample demonstration data.")

df[["Risk Score","Recoverability","Priority Value"]] = df.apply(analyse,axis=1)
df["Recommended Action"] = df.apply(
    lambda r: "Discuss pricing and demonstrate value" if "Price" in str(r["Objection"])
    else "Clarify implementation timeline" if "timeline" in str(r["Objection"]).lower()
    else "Discuss budget approval" if "Budget" in str(r["Objection"])
    else "Call customer and understand the blocker" if r["Overdue Days"] > 0
    else "Schedule the next follow-up", axis=1)

a,b,c,d = st.columns(4)
a.metric("Opportunities",len(df))
b.metric("High Risk",int((df["Risk Score"]>=0.65).sum()))
c.metric("Overdue Follow-ups",int((df["Overdue Days"]>0).sum()))
d.metric("Total Deal Value",f"₹{df['Deal Value'].sum():,.0f}")

tab1,tab2,tab3 = st.tabs(["Recovery Dashboard","Opportunity Intelligence","AI Follow-up Assistant"])

with tab1:
    st.header("Prioritised Recovery Queue")
    st.dataframe(df.sort_values("Priority Value",ascending=False),use_container_width=True,hide_index=True)

with tab2:
    st.header("Understand an Opportunity")
    selected = st.selectbox("Select company",df["Company"].tolist())
    r = df[df["Company"]==selected].iloc[0]
    x,y,z = st.columns(3)
    x.metric("Risk Score",f"{r['Risk Score']:.0%}")
    y.metric("Recoverability Estimate",f"{r['Recoverability']:.0%}")
    z.metric("Priority Value",f"₹{r['Priority Value']:,.0f}")
    st.write("**Customer objection:**",r["Objection"])
    st.info("**Recommended next action:** "+r["Recommended Action"])
    st.caption("Scores are illustrative rule-based estimates, not validated AI predictions.")

with tab3:
    st.header("Personalised Follow-up Assistant")
    selected = st.selectbox("Choose customer",df["Company"].tolist(),key="message")
    r = df[df["Company"]==selected].iloc[0]
    draft = f"""Hello,

I hope you are doing well.

I wanted to follow up regarding our discussion with {r['Company']}.
I understand that the current concern is {r['Objection'].lower()}.

{r['Recommended Action']}.

Please let me know a convenient time to discuss this further.

Regards,
Your Sales Team"""
    st.text_area("Review and edit your follow-up message",draft,height=220)
    st.warning("Demo only: Review the message before sending. No email or CRM action is performed.")

st.divider()
st.caption("OpportunityRescue AI | MVP | Sample data | No live Zoho CRM connection")

# ==========================================

# ==========================================

# ==========================================
# LOCAL OLLAMA CONVERSATIONAL AI
# ==========================================

import json
import urllib.request
import urllib.error

st.divider()
st.header("🤖 OpportunityRescue AI — Local Conversational Assistant")
st.caption("Powered by Llama 3.2 | Runs locally on your Mac")

if "ollama_chat_history" not in st.session_state:
    st.session_state.ollama_chat_history = []

for message in st.session_state.ollama_chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

question = st.chat_input("Ask your CRM assistant anything...")

if question:
    st.session_state.ollama_chat_history.append(
        {"role": "user", "content": question}
    )

    with st.chat_message("user"):
        st.markdown(question)

    crm_data = df.head(100).to_json(orient="records")

    system_prompt = """
You are OpportunityRescue AI, an intelligent sales recovery assistant.

Analyse the CRM records supplied by the application.
Identify at-risk opportunities, overdue follow-ups and objections.
Recommend practical sales recovery actions.
Draft professional customer follow-up messages when requested.

Use only supplied CRM data for factual answers.
Never invent customer information or claim to have sent messages.
Clearly distinguish facts from recommendations.
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": "CRM opportunity data:\n" + crm_data
        }
    ]

    messages.extend(st.session_state.ollama_chat_history[-12:])

    payload = json.dumps({
        "model": "llama3.2:3b",
        "messages": messages,
        "stream": False
    }).encode("utf-8")

    request = urllib.request.Request(
        "http://127.0.0.1:11434/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            result = json.loads(response.read().decode("utf-8"))

        answer = result["message"]["content"]

        st.session_state.ollama_chat_history.append(
            {"role": "assistant", "content": answer}
        )

        with st.chat_message("assistant"):
            st.markdown(answer)

    except Exception as e:
        st.error(f"Local AI connection error: {e}")

if st.button("Clear local AI conversation"):
    st.session_state.ollama_chat_history = []
    st.rerun()

# ==========================================
# CUSTOMER OBJECTION INTELLIGENCE
# ==========================================

st.divider()
st.header("🧠 Customer Objection Intelligence")
st.caption("Understand customer hesitation and generate AI-powered recovery strategies.")

with st.form("objection_intelligence_form"):

    objection_company = st.selectbox(
        "Select customer opportunity",
        df["Company"].tolist()
    )

    selected_record = df[
        df["Company"] == objection_company
    ].iloc[0]

    customer_objection = st.text_area(
        "Customer objection",
        value=str(selected_record["Objection"]),
        height=100,
        help="Enter the customer's actual concern or objection."
    )

    additional_context = st.text_area(
        "Additional customer context (optional)",
        placeholder="Example: Customer compared our price with a competitor."
    )

    analyse_objection = st.form_submit_button(
        "Analyse Customer Objection",
        type="primary"
    )

if analyse_objection:

    if not customer_objection.strip():
        st.warning("Please enter a customer objection.")

    else:

        objection_prompt = f"""
You are an expert B2B sales recovery strategist.

Analyse this customer objection using the supplied CRM information.

CUSTOMER: {objection_company}
DEAL VALUE: {selected_record['Deal Value']}
SALES STAGE: {selected_record['Stage']}
DAYS SINCE CONTACT: {selected_record['Days Since Contact']}
OVERDUE FOLLOW-UP DAYS: {selected_record['Overdue Days']}
CUSTOMER RESPONSE: {selected_record['Response']}
OBJECTION: {customer_objection}
ADDITIONAL CONTEXT: {additional_context}

Provide your analysis under these headings:

1. OBJECTION CATEGORY
Classify as Price, Budget, Competition, Timing,
Trust, Product Fit, Contractual or Other.

2. ROOT CAUSE
Explain the likely reason behind the hesitation.
Clearly distinguish assumptions from known facts.

3. SALES IMPACT
Explain how this objection may affect the opportunity.

4. RECOVERY STRATEGY
Give three practical actions for the salesperson.

5. SUGGESTED CUSTOMER RESPONSE
Draft a professional, empathetic customer-facing response.

6. NEXT BEST ACTION
Recommend one immediate action and explain why.

Use the supplied information only.
Do not invent customer facts, competitor prices or commitments.
"""

        payload = json.dumps({
            "model": "llama3.2:3b",
            "messages": [
                {
                    "role": "system",
                    "content": "You are OpportunityRescue AI, a B2B sales recovery specialist."
                },
                {
                    "role": "user",
                    "content": objection_prompt
                }
            ],
            "stream": False
        }).encode("utf-8")

        request = urllib.request.Request(
            "http://127.0.0.1:11434/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"}
        )

        try:
            with st.spinner("AI is analysing the customer objection..."):

                with urllib.request.urlopen(
                    request, timeout=180
                ) as response:

                    result = json.loads(
                        response.read().decode("utf-8")
                    )

            analysis = result["message"]["content"]

            st.success("Customer objection analysis completed!")

            st.markdown(analysis)

            # ==========================================
            # AI CUSTOMER RESPONSE GENERATOR
            # ==========================================

            st.divider()
            st.subheader("✉️ AI Customer Response Generator")

            response_format = st.selectbox(
                "Choose communication format",
                ["Professional Email", "WhatsApp Message"],
                key="customer_response_format"
            )

            if st.button("Generate Customer Response", type="primary"):

                format_instruction = (
                    "Write a professional business email with a subject, "
                    "greeting, concise body and sign-off."
                    if response_format == "Professional Email"
                    else
                    "Write a concise, natural and professional WhatsApp "
                    "message. Do not include an email subject."
                )

                reply_prompt = f"""
You are a professional B2B sales communication assistant.

Write a personalised customer response using these details:

Customer: {objection_company}
Objection: {customer_objection}
Additional context: {additional_context}
Deal value: ₹{selected_record['Deal Value']:,.0f}
Sales stage: {selected_record['Stage']}

AI analysis:
{analysis}

Instructions:
{format_instruction}

Address the customer's concern empathetically.
Demonstrate value without making unsupported claims.
Do not invent discounts, product features or commitments.
End with a clear and polite next step.
Return only the customer-facing draft.
"""

                reply_payload = json.dumps({
                    "model": "llama3.2:3b",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You write accurate, persuasive and ethical B2B sales communications."
                        },
                        {
                            "role": "user",
                            "content": reply_prompt
                        }
                    ],
                    "stream": False
                }).encode("utf-8")

                reply_request = urllib.request.Request(
                    "http://127.0.0.1:11434/api/chat",
                    data=reply_payload,
                    headers={"Content-Type": "application/json"}
                )

                try:
                    with st.spinner("Preparing your customer response..."):
                        with urllib.request.urlopen(
                            reply_request, timeout=180
                        ) as reply_response:
                            reply_result = json.loads(
                                reply_response.read().decode("utf-8")
                            )

                    st.session_state["customer_reply_draft"] = (
                        reply_result["message"]["content"]
                    )
                    st.success("Customer response generated!")

                except Exception as error:
                    st.error(f"Response generation failed: {error}")

            if st.session_state.get("customer_reply_draft"):
                st.markdown("#### Review and edit your response")

                edited_reply = st.text_area(
                    "Customer message",
                    value=st.session_state["customer_reply_draft"],
                    height=260,
                    key="editable_customer_reply"
                )

                st.caption(
                    "Edit the draft above. Select and copy the final "
                    "message when you are satisfied."
                )

                st.code(edited_reply, language="text")

                st.warning(
                    "Human approval required. This application does not "
                    "send emails or WhatsApp messages."
                )


            st.info(
                "Human review required: Verify the AI recommendations "
                "before contacting the customer."
            )

        except Exception as error:
            st.error(f"Objection analysis failed: {error}")


# ==========================================
# SALES RECOVERY ACTION TRACKER
# ==========================================

from datetime import date

st.divider()
st.header("📋 Sales Recovery Action Tracker")
st.caption("Convert AI recommendations into trackable sales activities.")

if "recovery_actions" not in st.session_state:
    st.session_state.recovery_actions = []

with st.form("create_recovery_action"):

    st.subheader("Create a recovery action")

    action_company = st.selectbox(
        "Customer opportunity",
        df["Company"].tolist(),
        key="tracker_company"
    )

    action_type = st.selectbox(
        "Action type",
        [
            "Customer follow-up call",
            "Send proposal clarification",
            "Discuss pricing and value",
            "Schedule customer meeting",
            "Resolve customer objection",
            "Send follow-up email",
            "Other"
        ]
    )

    action_description = st.text_area(
        "Action description",
        placeholder="Describe what the salesperson needs to do..."
    )

    owner = st.text_input(
        "Assigned salesperson",
        placeholder="Enter salesperson name"
    )

    due_date = st.date_input(
        "Follow-up deadline",
        value=date.today()
    )

    submitted = st.form_submit_button(
        "Add Recovery Action",
        type="primary"
    )

    if submitted:

        if not action_description.strip() or not owner.strip():
            st.warning("Please enter an action description and salesperson.")

        else:
            st.session_state.recovery_actions.append({
                "Customer": action_company,
                "Action": action_type,
                "Description": action_description,
                "Owner": owner,
                "Due Date": str(due_date),
                "Status": "Pending",
                "Outcome": ""
            })

            st.success("Recovery action added successfully!")
            st.rerun()


# Display and update actions

st.subheader("Recovery Activity Register")

if st.session_state.recovery_actions:

    tracker_df = pd.DataFrame(
        st.session_state.recovery_actions
    )

    edited_tracker = st.data_editor(
        tracker_df,
        hide_index=True,
        use_container_width=True,
        disabled=[
            "Customer",
            "Action",
            "Description",
            "Owner",
            "Due Date"
        ],
        column_config={
            "Status": st.column_config.SelectboxColumn(
                "Status",
                options=[
                    "Pending",
                    "In Progress",
                    "Completed",
                    "Customer Responded",
                    "Cancelled"
                ],
                required=True
            ),
            "Outcome": st.column_config.TextColumn(
                "Outcome / Remarks"
            )
        },
        key="recovery_action_editor"
    )

    st.session_state.recovery_actions = (
        edited_tracker.to_dict(orient="records")
    )

    pending = sum(
        1 for item in st.session_state.recovery_actions
        if item["Status"] == "Pending"
    )

    completed = sum(
        1 for item in st.session_state.recovery_actions
        if item["Status"] == "Completed"
    )

    responded = sum(
        1 for item in st.session_state.recovery_actions
        if item["Status"] == "Customer Responded"
    )

    m1, m2, m3 = st.columns(3)
    m1.metric("Pending Actions", pending)
    m2.metric("Completed Actions", completed)
    m3.metric("Customer Responses", responded)

    export_df = pd.DataFrame(
        st.session_state.recovery_actions
    )

    st.download_button(
        "Download Action Register (CSV)",
        data=export_df.to_csv(index=False).encode("utf-8"),
        file_name="sales_recovery_actions.csv",
        mime="text/csv"
    )

else:
    st.info(
        "No recovery actions yet. Create your first action above."
    )


# ==========================================
# MODULE 4: LOST DEAL INTELLIGENCE
# ==========================================

st.divider()
st.header("📉 Lost Deal Intelligence")
st.caption(
    "Understand why opportunities are lost and identify "
    "ways to prevent future losses."
)

if "lost_deals" not in st.session_state:
    st.session_state.lost_deals = []

with st.expander("➕ Record a Lost Opportunity", expanded=True):

    with st.form("lost_deal_form"):

        lost_company = st.text_input(
            "Customer / Company Name"
        )

        lost_value = st.number_input(
            "Deal Value (₹)",
            min_value=0,
            value=100000,
            step=10000
        )

        loss_reason = st.selectbox(
            "Primary Reason for Loss",
            [
                "Price",
                "Budget Constraints",
                "Competitor Selected",
                "Implementation Timeline",
                "Lack of Trust",
                "Product Mismatch",
                "No Customer Response",
                "Decision Deferred",
                "Other"
            ]
        )

        competitor = st.text_input(
            "Competitor Name (if applicable)"
        )

        loss_details = st.text_area(
            "Additional Details",
            placeholder="What happened during the sales discussion?"
        )

        loss_submitted = st.form_submit_button(
            "Record Lost Opportunity",
            type="primary"
        )

        if loss_submitted:

            if not lost_company.strip():
                st.warning("Please enter the company name.")

            else:
                st.session_state.lost_deals.append({
                    "Company": lost_company,
                    "Deal Value": lost_value,
                    "Loss Reason": loss_reason,
                    "Competitor": competitor,
                    "Details": loss_details
                })

                st.success("Lost opportunity recorded!")
                st.rerun()


# Analytics section

st.subheader("📊 Lost Deal Analytics")

if st.session_state.lost_deals:

    lost_df = pd.DataFrame(
        st.session_state.lost_deals
    )

    total_lost = len(lost_df)
    total_value_lost = lost_df["Deal Value"].sum()

    top_reason = lost_df["Loss Reason"].value_counts().idxmax()

    c1, c2, c3 = st.columns(3)

    c1.metric("Lost Opportunities", total_lost)
    c2.metric("Total Lost Deal Value", f"₹{total_value_lost:,.0f}")
    c3.metric("Most Common Loss Reason", top_reason)

    st.subheader("Loss Reasons Breakdown")

    reason_counts = (
        lost_df["Loss Reason"]
        .value_counts()
        .reset_index()
    )

    reason_counts.columns = ["Reason", "Count"]

    st.bar_chart(
        reason_counts.set_index("Reason")
    )

    st.subheader("💡 Prevention Insights")

    for reason, count in lost_df["Loss Reason"].value_counts().items():

        if reason == "Price":
            insight = (
                "Strengthen value communication, explain ROI "
                "and understand the customer's budget before quoting."
            )

        elif reason == "Budget Constraints":
            insight = (
                "Explore phased implementation, suitable packages "
                "or a revised commercial proposal."
            )

        elif reason == "Competitor Selected":
            insight = (
                "Improve competitor positioning and communicate "
                "your product's measurable differentiation."
            )

        elif reason == "Implementation Timeline":
            insight = (
                "Set realistic implementation milestones and "
                "address delivery concerns early."
            )

        elif reason == "Lack of Trust":
            insight = (
                "Provide relevant case studies, references "
                "and transparent product information."
            )

        elif reason == "No Customer Response":
            insight = (
                "Establish a structured follow-up process "
                "and identify the correct decision-maker."
            )

        elif reason == "Product Mismatch":
            insight = (
                "Improve requirement discovery and demonstrate "
                "how the product addresses customer needs."
            )

        elif reason == "Decision Deferred":
            insight = (
                "Understand the decision timeline and agree "
                "on a specific next discussion date."
            )

        else:
            insight = (
                "Review the customer interaction and document "
                "the specific reason for the lost opportunity."
            )

        st.markdown(f"**{reason} — {count} occurrence(s)**")
        st.info(insight)

    st.subheader("Lost Opportunity Register")

    st.dataframe(
        lost_df,
        use_container_width=True,
        hide_index=True
    )

    st.download_button(
        "Download Lost Deal Report",
        data=lost_df.to_csv(index=False).encode("utf-8"),
        file_name="lost_deal_report.csv",
        mime="text/csv"
    )

else:
    st.info(
        "No lost opportunities recorded yet. "
        "Add a lost opportunity to generate analytics."
    )

st.caption(
    "Note: Prevention insights are rule-based recommendations, "
    "not validated AI predictions."
)


# ==========================================
# MODULE 5: SALES INTELLIGENCE DASHBOARD
# ==========================================

st.divider()
st.title("📊 Sales Intelligence Dashboard")
st.caption("A unified view of pipeline health, sales risks and lost opportunities.")

active_count = len(df)
pipeline_value = df["Deal Value"].sum()

high_risk = df[df["Risk Score"] >= 0.65]
overdue = df[df["Overdue Days"] > 0]

lost_records = st.session_state.get("lost_deals", [])
lost_df_dashboard = pd.DataFrame(lost_records)

lost_count = len(lost_df_dashboard)
lost_value = lost_df_dashboard["Deal Value"].sum() if lost_count else 0

st.subheader("Business Performance Overview")

c1, c2, c3 = st.columns(3)
c1.metric("Active Opportunities", active_count)
c2.metric("Pipeline Value", f"₹{pipeline_value:,.0f}")
c3.metric("High-Risk Opportunities", len(high_risk))

c4, c5, c6 = st.columns(3)
c4.metric("Overdue Follow-ups", len(overdue))
c5.metric("Lost Opportunities", lost_count)
c6.metric("Lost Deal Value", f"₹{lost_value:,.0f}")

st.divider()

left, right = st.columns(2)

with left:
    st.subheader("Pipeline by Sales Stage")
    stage_data = df.groupby("Stage")["Deal Value"].sum()
    st.bar_chart(stage_data)

with right:
    st.subheader("Risk Distribution")
    risk_categories = pd.Series({
        "High Risk": int((df["Risk Score"] >= 0.65).sum()),
        "Medium Risk": int(
            ((df["Risk Score"] >= 0.35) &
             (df["Risk Score"] < 0.65)).sum()
        ),
        "Low Risk": int((df["Risk Score"] < 0.35).sum())
    })
    st.bar_chart(risk_categories)

st.divider()
st.subheader("🚨 Top Opportunities Requiring Attention")

priority_view = (
    df.sort_values("Priority Value", ascending=False)
    [["Company", "Stage", "Deal Value",
      "Risk Score", "Overdue Days", "Recommended Action"]]
    .head(5).copy()
)

priority_view["Risk Score"] = priority_view["Risk Score"].map(
    lambda x: f"{x:.0%}"
)

st.dataframe(priority_view, use_container_width=True, hide_index=True)

st.caption(
    "Priority value is an illustrative ranking measure, "
    "not guaranteed revenue at risk."
)

st.divider()
st.subheader("📉 Lost Deal Overview")

if lost_count:
    loss_breakdown = lost_df_dashboard["Loss Reason"].value_counts()
    st.write("Most common loss reason:", loss_breakdown.index[0])
    st.bar_chart(loss_breakdown)
else:
    st.info("No lost deals recorded yet. Add records in Lost Deal Intelligence.")

st.divider()
st.caption("OpportunityRescue AI | Management Dashboard | Demonstration data")


# ==========================================
# MODULE 6: AI-POWERED GTM STRATEGY PLANNER
# ==========================================

st.divider()
st.header("🚀 AI-Powered GTM Strategy Planner")
st.caption(
    "Develop a structured go-to-market strategy "
    "using your local Llama AI model."
)

with st.form("gtm_strategy_form"):

    st.subheader("Business Information")

    gtm_product = st.text_input(
        "Product / Service Name",
        placeholder="Example: Wingo Tourism"
    )

    gtm_industry = st.text_input(
        "Industry",
        placeholder="Example: Tourism Technology"
    )

    gtm_market = st.text_input(
        "Target Geography",
        placeholder="Example: Tamil Nadu, India"
    )

    gtm_customer = st.text_area(
        "Target Customer",
        placeholder="Describe your ideal customers..."
    )

    gtm_problem = st.text_area(
        "Customer Problem / Pain Point",
        placeholder="What problem does your product solve?"
    )

    gtm_advantage = st.text_area(
        "Unique Value Proposition",
        placeholder="Why should customers choose your product?"
    )

    gtm_price = st.text_input(
        "Pricing / Business Model",
        placeholder="Example: Monthly subscription"
    )

    gtm_goal = st.text_input(
        "Business Goal",
        placeholder="Example: Acquire 100 paying customers in 6 months"
    )

    gtm_budget = st.selectbox(
        "Estimated Marketing Budget",
        [
            "Not decided",
            "Below ₹25,000",
            "₹25,000 – ₹1 lakh",
            "₹1 lakh – ₹5 lakh",
            "Above ₹5 lakh"
        ]
    )

    gtm_submitted = st.form_submit_button(
        "Generate GTM Strategy",
        type="primary"
    )

if gtm_submitted:

    if not all([
        gtm_product.strip(),
        gtm_industry.strip(),
        gtm_market.strip(),
        gtm_customer.strip(),
        gtm_problem.strip(),
        gtm_goal.strip()
    ]):
        st.warning(
            "Please complete the product, industry, "
            "market, customer, problem and business goal fields."
        )

    else:

        gtm_prompt = f"""
You are a senior Go-To-Market strategy consultant.

Create a practical and realistic GTM strategy using these details.

PRODUCT: {gtm_product}
INDUSTRY: {gtm_industry}
GEOGRAPHY: {gtm_market}
TARGET CUSTOMER: {gtm_customer}
CUSTOMER PROBLEM: {gtm_problem}
UNIQUE VALUE PROPOSITION: {gtm_advantage}
PRICING MODEL: {gtm_price}
BUSINESS GOAL: {gtm_goal}
MARKETING BUDGET: {gtm_budget}

Prepare the strategy using these sections:

1. Executive Summary
2. Ideal Customer Profile (ICP)
3. Customer Segmentation
4. Positioning and Value Proposition
5. Competitor Research Plan
6. Recommended Acquisition Channels
7. Sales and Distribution Strategy
8. Pricing and Packaging Recommendations
9. 30-60-90 Day GTM Roadmap
10. Marketing Budget Allocation
11. Five Measurable KPIs
12. Key Risks and Mitigation

Make recommendations specific to the supplied business.
Give practical actions, not generic motivational statements.
Clearly label assumptions and avoid inventing market research,
competitor prices or verified market statistics.
"""

        with st.spinner(
            "Llama AI is developing your GTM strategy..."
        ):

            try:

                import json
                import urllib.request
                import urllib.error

                payload = {
                    "model": "llama3.2:3b",
                    "prompt": gtm_prompt,
                    "stream": False
                }

                request = urllib.request.Request(
                    "http://127.0.0.1:11434/api/generate",
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )

                with urllib.request.urlopen(
                    request, timeout=240
                ) as response:

                    result = json.loads(
                        response.read().decode("utf-8")
                    )

                gtm_answer = result.get("response", "")

                if gtm_answer.strip():

                    st.session_state["gtm_generated_plan"] = (
                        gtm_answer
                    )

                else:
                    st.error("The AI returned an empty response.")

            except Exception as error:

                st.error(
                    f"Unable to generate the GTM strategy: {error}"
                )

if st.session_state.get("gtm_generated_plan"):

    st.divider()
    st.subheader("📋 Your Generated GTM Strategy")

    st.markdown(
        st.session_state["gtm_generated_plan"]
    )

    st.download_button(
        "Download GTM Strategy",
        data=st.session_state["gtm_generated_plan"],
        file_name="GTM_Strategy.md",
        mime="text/markdown"
    )

    if st.button("Clear Generated Strategy"):
        del st.session_state["gtm_generated_plan"]
        st.rerun()

st.caption(
    "GTM Strategy Planner | Local Llama AI | "
    "Recommendations require business validation."
)


# ==========================================
# MODULE 8: COMPETITOR & WIN-LOSS INTELLIGENCE
# ==========================================

st.divider()
st.header("⚔️ Competitor & Win-Loss Intelligence")
st.caption("Understand competitive losses and develop stronger sales strategies.")

if "competitive_records" not in st.session_state:
    st.session_state.competitive_records = []

with st.expander("➕ Record a Competitive Deal", expanded=True):

    with st.form("competitive_deal_form"):

        comp_company = st.text_input("Customer / Company")

        comp_name = st.text_input("Competitor Name")

        comp_value = st.number_input(
            "Deal Value (₹)",
            min_value=0,
            value=100000,
            step=10000
        )

        comp_result = st.selectbox(
            "Deal Outcome",
            ["Won", "Lost", "Pending"]
        )

        comp_reason = st.selectbox(
            "Primary Decision Factor",
            [
                "Price",
                "Product Features",
                "Customer Service",
                "Brand Reputation",
                "Implementation Time",
                "Relationship / Trust",
                "Product Fit",
                "Other"
            ]
        )

        comp_details = st.text_area(
            "Competitive Information",
            placeholder="Enter known competitor strengths, pricing or customer feedback..."
        )

        comp_submit = st.form_submit_button(
            "Save Competitive Record",
            type="primary"
        )

        if comp_submit:

            if not comp_company.strip() or not comp_name.strip():
                st.warning("Enter both customer and competitor names.")

            else:
                st.session_state.competitive_records.append({
                    "Customer": comp_company,
                    "Competitor": comp_name,
                    "Deal Value": comp_value,
                    "Outcome": comp_result,
                    "Decision Factor": comp_reason,
                    "Details": comp_details
                })

                st.success("Competitive deal recorded!")
                st.rerun()


# ==========================================
# WIN-LOSS ANALYTICS
# ==========================================

st.subheader("📊 Competitive Performance")

if st.session_state.competitive_records:

    comp_df = pd.DataFrame(
        st.session_state.competitive_records
    )

    decided = comp_df[
        comp_df["Outcome"].isin(["Won", "Lost"])
    ]

    won_count = int((decided["Outcome"] == "Won").sum())
    lost_count = int((decided["Outcome"] == "Lost").sum())

    decided_count = won_count + lost_count

    win_rate = (
        won_count / decided_count * 100
        if decided_count else 0
    )

    m1, m2, m3 = st.columns(3)

    m1.metric("Deals Won", won_count)
    m2.metric("Deals Lost", lost_count)
    m3.metric("Win Rate", f"{win_rate:.1f}%")

    st.subheader("Decision Factors")

    factor_counts = (
        comp_df["Decision Factor"].value_counts()
    )

    st.bar_chart(factor_counts)

    st.subheader("Competitor Performance")

    st.dataframe(
        comp_df,
        use_container_width=True,
        hide_index=True
    )

    st.download_button(
        "Download Competitive Analysis CSV",
        data=comp_df.to_csv(index=False).encode("utf-8"),
        file_name="competitor_win_loss_analysis.csv",
        mime="text/csv"
    )

else:
    st.info("No competitive records yet. Add your first deal above.")


# ==========================================
# AI COMPETITOR STRATEGY GENERATOR
# ==========================================

st.divider()
st.subheader("🤖 AI Competitive Strategy Advisor")

with st.form("competitive_ai_form"):

    ai_competitor = st.text_input(
        "Competitor to analyse",
        placeholder="Example: Competitor ABC"
    )

    ai_product = st.text_input(
        "Your product / service",
        placeholder="Describe what your business offers"
    )

    ai_strengths = st.text_area(
        "Your known strengths",
        placeholder="List your actual product or service strengths"
    )

    ai_weaknesses = st.text_area(
        "Your known weaknesses",
        placeholder="Where does the competitor appear stronger?"
    )

    ai_customer_feedback = st.text_area(
        "Customer feedback",
        placeholder="What has the customer said about the competitor?"
    )

    generate_competitor_strategy = st.form_submit_button(
        "Generate Competitive Strategy",
        type="primary"
    )

if generate_competitor_strategy:

    if not ai_competitor.strip() or not ai_product.strip():
        st.warning("Enter your product and competitor name.")

    else:

        records_context = ""

        if st.session_state.competitive_records:
            records_context = pd.DataFrame(
                st.session_state.competitive_records
            ).to_json(orient="records")

        competitor_prompt = f"""
You are a B2B competitive sales intelligence consultant.

Analyse the following supplied information.

OUR PRODUCT: {ai_product}
COMPETITOR: {ai_competitor}
OUR STRENGTHS: {ai_strengths}
OUR WEAKNESSES: {ai_weaknesses}
CUSTOMER FEEDBACK: {ai_customer_feedback}
RECORDED WIN-LOSS DATA: {records_context}

Prepare:

1. Competitive Positioning Summary
2. Our Differentiation Opportunities
3. Customer Decision Factor Analysis
4. Recommended Sales Strategy
5. Three Competitive Talking Points
6. Suggested Response to Competitor Objections
7. Recommended Next Sales Action

Important:
- Do not invent competitor pricing or features.
- Distinguish supplied facts from assumptions.
- Do not make unsupported claims about competitors.
- Recommend ethical and customer-focused selling.
- Give practical actions to improve conversion.
"""

        try:

            competitor_payload = {
                "model": "llama3.2:3b",
                "prompt": competitor_prompt,
                "stream": False
            }

            competitor_request = urllib.request.Request(
                "http://127.0.0.1:11434/api/generate",
                data=json.dumps(competitor_payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )

            with st.spinner("Analysing competitive positioning..."):

                with urllib.request.urlopen(
                    competitor_request, timeout=240
                ) as response:

                    competitor_result = json.loads(
                        response.read().decode("utf-8")
                    )

            strategy = competitor_result.get("response", "")

            if strategy:
                st.session_state["competitor_strategy"] = strategy

        except Exception as error:
            st.error(f"Strategy generation failed: {error}")


if st.session_state.get("competitor_strategy"):

    st.markdown(
        st.session_state["competitor_strategy"]
    )

    st.download_button(
        "Download Competitive Strategy",
        data=st.session_state["competitor_strategy"],
        file_name="competitive_strategy.md",
        mime="text/markdown"
    )

st.caption(
    "Competitor Intelligence | Local Llama AI | "
    "User-supplied competitive information | No live competitor research"
)


# ==========================================================
# SUPPLIER PAYMENT INTELLIGENCE
# ==========================================================

from datetime import date, timedelta
import json
import urllib.request
import urllib.error

st.divider()
st.header("💳 Supplier Payment Intelligence")
st.caption("Track supplier dues, prepare funds and avoid missed payments.")

if "supplier_payments" not in st.session_state:
    st.session_state.supplier_payments = []

payments = st.session_state.supplier_payments

# ---------- MANUAL PURCHASE ENTRY ----------

st.subheader("1. Record a Purchase")

with st.expander("➕ Add purchase manually", expanded=True):
    with st.form("supplier_manual_form"):
        supplier_name = st.text_input("Supplier name")
        purchase_amount = st.number_input(
            "Purchase amount (₹)", min_value=0.0, step=500.0
        )
        purchase_date = st.date_input("Purchase date", value=date.today())
        due_date = st.date_input(
            "Payment due date", value=date.today() + timedelta(days=15)
        )
        purchase_description = st.text_input("Goods purchased / Notes")

        manual_submit = st.form_submit_button("Save Purchase")

        if manual_submit:
            if not supplier_name.strip() or purchase_amount <= 0:
                st.error("Enter a supplier name and a valid amount.")
            elif due_date < purchase_date:
                st.error("Due date cannot be before the purchase date.")
            else:
                payments.append({
                    "Supplier": supplier_name.strip(),
                    "Amount": float(purchase_amount),
                    "Purchase Date": str(purchase_date),
                    "Due Date": str(due_date),
                    "Description": purchase_description,
                    "Status": "Pending"
                })
                st.success("Purchase recorded successfully!")
                st.rerun()

# ---------- VOICE / NATURAL LANGUAGE ENTRY ----------

st.subheader("2. Voice-Based Purchase Entry")
st.caption(
    "Use Mac dictation (press Fn twice) and speak naturally. "
    "Example: I bought goods worth 15000 from ABC Traders today, "
    "payment is due in 15 days."
)

voice_text = st.text_area(
    "Speak or type your purchase details",
    placeholder="I purchased goods worth ₹15,000 from ABC Traders..."
    ,
    key="supplier_voice_text"
)

if st.button("🤖 Extract Purchase Details with AI", key="supplier_ai_extract"):
    if not voice_text.strip():
        st.warning("Please enter or dictate your purchase details first.")
    else:
        try:
            prompt = f"""
Extract purchase information from this sentence.

Return ONLY valid JSON with these fields:
supplier, amount, purchase_date, due_date, description.

Dates must use YYYY-MM-DD format.
If purchase date is not mentioned, use {date.today()}.
If due date is not mentioned, return an empty string.
Amount must be a number without currency symbols.
Do not invent missing information.

Sentence: {voice_text}
"""
            payload = json.dumps({
                "model": "llama3.2:3b",
                "prompt": prompt,
                "stream": False,
                "format": "json"
            }).encode("utf-8")

            request = urllib.request.Request(
                "http://127.0.0.1:11434/api/generate",
                data=payload,
                headers={"Content-Type": "application/json"}
            )

            with urllib.request.urlopen(request, timeout=90) as response:
                result = json.loads(response.read().decode("utf-8"))

            extracted = json.loads(result["response"])

            st.session_state["supplier_extracted"] = extracted
            st.success("AI extracted the purchase details. Please review them below.")

        except Exception as e:
            st.error(
                "Could not extract the details. Check that Ollama is running "
                "and llama3.2:3b is installed."
            )
            st.caption(str(e))

if "supplier_extracted" in st.session_state:
    extracted = st.session_state["supplier_extracted"]

    st.markdown("**Review extracted details before saving:**")

    with st.form("supplier_voice_confirm"):
        ai_supplier = st.text_input(
            "Supplier",
            value=str(extracted.get("supplier", ""))
        )
        ai_amount = st.number_input(
            "Amount (₹)",
            min_value=0.0,
            value=float(extracted.get("amount") or 0)
        )
        ai_purchase_date = st.text_input(
            "Purchase date (YYYY-MM-DD)",
            value=str(extracted.get("purchase_date") or date.today())
        )
        ai_due_date = st.text_input(
            "Due date (YYYY-MM-DD)",
            value=str(extracted.get("due_date") or "")
        )
        ai_description = st.text_input(
            "Description",
            value=str(extracted.get("description") or "")
        )

        confirm_ai = st.form_submit_button("Confirm and Save Purchase")

        if confirm_ai:
            try:
                parsed_purchase = date.fromisoformat(ai_purchase_date)
                parsed_due = date.fromisoformat(ai_due_date)

                if not ai_supplier.strip() or ai_amount <= 0:
                    st.error("Please provide a supplier and valid amount.")
                elif parsed_due < parsed_purchase:
                    st.error("Due date cannot be before purchase date.")
                else:
                    payments.append({
                        "Supplier": ai_supplier.strip(),
                        "Amount": float(ai_amount),
                        "Purchase Date": str(parsed_purchase),
                        "Due Date": str(parsed_due),
                        "Description": ai_description,
                        "Status": "Pending"
                    })
                    del st.session_state["supplier_extracted"]
                    st.success("Voice purchase saved successfully!")
                    st.rerun()

            except ValueError:
                st.error("Please enter both dates in YYYY-MM-DD format.")

# ---------- PAYMENT DASHBOARD ----------

st.divider()
st.subheader("3. Supplier Payment Dashboard")

if payments:
    payment_df = pd.DataFrame(payments)
    payment_df["Due Date Parsed"] = pd.to_datetime(
        payment_df["Due Date"], errors="coerce"
    )
    today = pd.Timestamp(date.today())

    pending_df = payment_df[payment_df["Status"] == "Pending"]
    overdue_df = pending_df[pending_df["Due Date Parsed"] < today]
    upcoming_df = pending_df[
        (pending_df["Due Date Parsed"] >= today) &
        (pending_df["Due Date Parsed"] <= today + pd.Timedelta(days=7))
    ]

    total_pending = pending_df["Amount"].sum()
    total_overdue = overdue_df["Amount"].sum()
    total_upcoming = upcoming_df["Amount"].sum()
    total_paid = payment_df[
        payment_df["Status"] == "Paid"
    ]["Amount"].sum()

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Outstanding", f"₹{total_pending:,.0f}")
    m2.metric("Due in 7 Days", f"₹{total_upcoming:,.0f}")
    m3.metric("Overdue Amount", f"₹{total_overdue:,.0f}")
    m4.metric("Total Paid", f"₹{total_paid:,.0f}")

    # ---------- SMART REMINDERS ----------

    st.subheader("4. Payment Reminders")

    if not pending_df.empty:
        for _, payment in pending_df.iterrows():
            days_left = (payment["Due Date Parsed"] - today).days
            amount = f"₹{payment['Amount']:,.0f}"

            if days_left < 0:
                st.error(
                    f"OVERDUE: {payment['Supplier']} — {amount}. "
                    f"Payment was due {-days_left} days ago."
                )
            elif days_left == 0:
                st.warning(
                    f"DUE TODAY: {payment['Supplier']} — {amount}."
                )
            elif days_left <= 3:
                st.warning(
                    f"UPCOMING: {payment['Supplier']} — {amount}. "
                    f"Due in {days_left} days."
                )
            elif days_left <= 7:
                st.info(
                    f"REMINDER: {payment['Supplier']} — {amount}. "
                    f"Due in {days_left} days."
                )
    else:
        st.success("No pending supplier payments!")

    # ---------- CASH PREPARATION FORECAST ----------

    st.subheader("5. Cash Preparation Forecast")

    if not pending_df.empty:
        forecast = (
            pending_df.groupby("Due Date")["Amount"]
            .sum()
            .reset_index()
            .sort_values("Due Date")
        )
        forecast.columns = ["Payment Due Date", "Amount to Prepare (₹)"]

        st.dataframe(forecast, use_container_width=True, hide_index=True)

        next_seven_days = pending_df[
            pending_df["Due Date Parsed"] <= today + pd.Timedelta(days=7)
        ]["Amount"].sum()

        st.info(
            f"Prepare approximately ₹{next_seven_days:,.0f} "
            f"for pending supplier payments due within the next 7 days."
        )

    # ---------- PAYMENT STATUS MANAGEMENT ----------

    st.subheader("6. Update Payment Status")

    payment_options = [
        f"{i + 1}. {p['Supplier']} — ₹{p['Amount']:,.0f} "
        f"(Due: {p['Due Date']})"
        for i, p in enumerate(payments)
    ]

    selected_payment = st.selectbox(
        "Select a supplier payment",
        range(len(payment_options)),
        format_func=lambda i: payment_options[i]
    )

    selected_status = st.selectbox(
        "Payment status",
        ["Pending", "Paid"]
    )

    if st.button("Update Payment Status"):
        payments[selected_payment]["Status"] = selected_status
        st.success("Payment status updated!")
        st.rerun()

    # ---------- PAYMENT HISTORY ----------

    st.subheader("7. Supplier Payment History")

    display_df = pd.DataFrame(payments)
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    csv_data = display_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download Payment Records",
        data=csv_data,
        file_name="supplier_payment_records.csv",
        mime="text/csv"
    )

else:
    st.info("No supplier purchases recorded yet. Add your first purchase above.")

st.caption(
    "Prototype: reminders are displayed inside the dashboard. "
    "Automatic WhatsApp, SMS and email notifications are not connected. "
    "Records are currently stored in Streamlit session memory."
)


# ==========================================================
# AI INVENTORY & REORDER INTELLIGENCE
# ==========================================================

st.divider()
st.header("📦 AI Inventory & Reorder Intelligence")
st.caption("Monitor stock, track movement and make smarter purchasing decisions.")

if "inventory_products" not in st.session_state:
    st.session_state.inventory_products = []

if "inventory_movements" not in st.session_state:
    st.session_state.inventory_movements = []

products = st.session_state.inventory_products
movements = st.session_state.inventory_movements

# ---------- ADD PRODUCT ----------

st.subheader("1. Product Management")

with st.expander("➕ Add a new product", expanded=True):
    with st.form("inventory_add_product"):
        p_name = st.text_input("Product name")
        p_category = st.text_input("Category")
        p_supplier = st.text_input("Supplier name")
        p_cost = st.number_input("Purchase cost per unit (₹)", min_value=0.0)
        p_price = st.number_input("Selling price per unit (₹)", min_value=0.0)
        p_stock = st.number_input("Opening stock quantity", min_value=0, step=1)
        p_minimum = st.number_input("Minimum stock alert level", min_value=0, value=10, step=1)

        add_product = st.form_submit_button("Save Product")

        if add_product:
            if not p_name.strip():
                st.error("Please enter a product name.")
            elif any(x["Product"].lower() == p_name.strip().lower() for x in products):
                st.error("This product already exists.")
            elif p_price < p_cost:
                st.warning("Selling price is below purchase cost. Please review.")
            else:
                products.append({
                    "Product": p_name.strip(),
                    "Category": p_category.strip(),
                    "Supplier": p_supplier.strip(),
                    "Cost": float(p_cost),
                    "Selling Price": float(p_price),
                    "Stock": int(p_stock),
                    "Minimum Stock": int(p_minimum)
                })
                st.success("Product added successfully!")
                st.rerun()

# ---------- STOCK MOVEMENT ----------

st.divider()
st.subheader("2. Record Stock Movement")

if products:
    product_names = [p["Product"] for p in products]

    with st.form("inventory_movement_form"):
        selected_product = st.selectbox("Select product", product_names)
        movement_type = st.selectbox("Transaction type", ["Stock Purchase", "Sale", "Stock Adjustment"])
        movement_qty = st.number_input("Quantity", min_value=1, step=1)
        movement_note = st.text_input("Reference / Notes")

        save_movement = st.form_submit_button("Update Inventory")

        if save_movement:
            product = next(p for p in products if p["Product"] == selected_product)

            if movement_type == "Sale" and movement_qty > product["Stock"]:
                st.error("Insufficient stock. Sale cannot be recorded.")
            else:
                if movement_type == "Stock Purchase":
                    product["Stock"] += int(movement_qty)
                elif movement_type == "Sale":
                    product["Stock"] -= int(movement_qty)
                else:
                    product["Stock"] = int(movement_qty)

                movements.append({
                    "Date": str(date.today()),
                    "Product": selected_product,
                    "Transaction": movement_type,
                    "Quantity": int(movement_qty),
                    "Notes": movement_note
                })

                st.success("Inventory updated successfully!")
                st.rerun()
else:
    st.info("Add your first product to start recording stock movements.")

# ---------- INVENTORY DASHBOARD ----------

st.divider()
st.subheader("3. Inventory Dashboard")

if products:
    inventory_df = pd.DataFrame(products)

    inventory_value = sum(p["Stock"] * p["Cost"] for p in products)
    total_units = sum(p["Stock"] for p in products)
    low_stock = [p for p in products if p["Stock"] <= p["Minimum Stock"]]
    out_of_stock = [p for p in products if p["Stock"] == 0]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Products", len(products))
    c2.metric("Units in Stock", total_units)
    c3.metric("Inventory Value", f"₹{inventory_value:,.0f}")
    c4.metric("Low Stock Products", len(low_stock))

    st.subheader("4. Current Stock Position")
    st.dataframe(inventory_df, use_container_width=True, hide_index=True)

    # ---------- STOCK ALERTS ----------

    st.subheader("5. Low Stock Alerts")

    if out_of_stock:
        for p in out_of_stock:
            st.error(f"OUT OF STOCK: {p['Product']}")

    if low_stock:
        for p in low_stock:
            st.warning(
                f"{p['Product']}: Only {p['Stock']} units remaining. "
                f"Minimum stock level: {p['Minimum Stock']}."
            )
    else:
        st.success("All products are above their minimum stock levels.")

    # ---------- REORDER RECOMMENDATIONS ----------

    st.subheader("6. Reorder Recommendations")

    reorder_rows = []

    for p in low_stock:
        recommended_qty = max(
            (p["Minimum Stock"] * 2) - p["Stock"], 0
        )
        reorder_rows.append({
            "Product": p["Product"],
            "Supplier": p["Supplier"],
            "Current Stock": p["Stock"],
            "Minimum Level": p["Minimum Stock"],
            "Suggested Reorder": recommended_qty,
            "Estimated Purchase Cost (₹)": recommended_qty * p["Cost"]
        })

    if reorder_rows:
        reorder_df = pd.DataFrame(reorder_rows)
        st.dataframe(reorder_df, use_container_width=True, hide_index=True)

        total_reorder_cost = reorder_df["Estimated Purchase Cost (₹)"].sum()
        st.info(
            f"Estimated funds required for these suggested orders: "
            f"₹{total_reorder_cost:,.0f}"
        )
        st.caption(
            "Reorder quantity is currently a simple rule-based estimate: "
            "target stock is twice the minimum stock level. "
            "It is not yet a demand forecast."
        )
    else:
        st.success("No products currently require replenishment.")

    # ---------- PROFITABILITY SNAPSHOT ----------

    st.subheader("7. Product Margin Snapshot")

    margin_rows = []

    for p in products:
        margin = p["Selling Price"] - p["Cost"]
        margin_percent = (
            margin / p["Selling Price"] * 100
            if p["Selling Price"] > 0 else 0
        )

        margin_rows.append({
            "Product": p["Product"],
            "Purchase Cost (₹)": p["Cost"],
            "Selling Price (₹)": p["Selling Price"],
            "Gross Margin per Unit (₹)": margin,
            "Margin (%)": round(margin_percent, 2)
        })

    st.dataframe(
        pd.DataFrame(margin_rows),
        use_container_width=True,
        hide_index=True
    )

    # ---------- MOVEMENT HISTORY ----------

    st.subheader("8. Stock Movement History")

    if movements:
        movement_df = pd.DataFrame(movements)
        st.dataframe(movement_df, use_container_width=True, hide_index=True)

        st.download_button(
            "⬇️ Download Inventory Records",
            data=inventory_df.to_csv(index=False).encode("utf-8"),
            file_name="inventory_records.csv",
            mime="text/csv"
        )
    else:
        st.info("No stock movements recorded yet.")

else:
    st.info("Add products above to activate your inventory dashboard.")

st.caption(
    "Prototype: Inventory records currently use Streamlit session memory. "
    "Persistent database storage and automated purchase orders will be added later."
)


# ==========================================================
# AI SALES & PROFITABILITY INTELLIGENCE
# ==========================================================

st.divider()
st.header("📈 AI Sales & Profitability Intelligence")
st.caption("Track revenue, understand product profitability and improve sales decisions.")

if "business_sales" not in st.session_state:
    st.session_state.business_sales = []

sales = st.session_state.business_sales

# ---------- SALES ENTRY ----------

st.subheader("1. Record a Sale")

if "inventory_products" in st.session_state and st.session_state.inventory_products:

    products = st.session_state.inventory_products
    product_names = [p["Product"] for p in products]

    with st.form("business_sales_entry"):
        sale_product_name = st.selectbox("Select product", product_names)

        selected_product = next(
            p for p in products if p["Product"] == sale_product_name
        )

        sale_quantity = st.number_input(
            "Quantity sold", min_value=1, step=1
        )

        sale_price = st.number_input(
            "Selling price per unit (₹)",
            min_value=0.0,
            value=float(selected_product["Selling Price"])
        )

        sale_date = st.date_input("Sale date", value=date.today())
        sale_customer = st.text_input("Customer name (optional)")
        sale_notes = st.text_input("Sale reference / Notes")

        record_sale = st.form_submit_button("Record Sale")

        if record_sale:
            if sale_quantity > selected_product["Stock"]:
                st.error("Insufficient stock! Available stock: " +
                         str(selected_product["Stock"]))
            elif sale_price <= 0:
                st.error("Enter a valid selling price.")
            else:
                revenue = float(sale_quantity * sale_price)
                cost = float(sale_quantity * selected_product["Cost"])
                profit = revenue - cost

                # Deduct inventory automatically
                selected_product["Stock"] -= int(sale_quantity)

                sales.append({
                    "Date": str(sale_date),
                    "Product": sale_product_name,
                    "Quantity": int(sale_quantity),
                    "Unit Selling Price": float(sale_price),
                    "Revenue": revenue,
                    "Cost": cost,
                    "Gross Profit": profit,
                    "Customer": sale_customer,
                    "Notes": sale_notes
                })

                # Record stock movement
                st.session_state.inventory_movements.append({
                    "Date": str(sale_date),
                    "Product": sale_product_name,
                    "Transaction": "Sale",
                    "Quantity": int(sale_quantity),
                    "Notes": sale_notes
                })

                st.success("Sale recorded and inventory updated!")
                st.rerun()

else:
    st.warning("Please add products in AI Inventory before recording sales.")

# ---------- SALES DASHBOARD ----------

st.divider()
st.subheader("2. Sales Performance Dashboard")

if sales:

    sales_df = pd.DataFrame(sales)
    sales_df["Date Parsed"] = pd.to_datetime(sales_df["Date"])

    today = pd.Timestamp(date.today())
    week_start = today - pd.Timedelta(days=6)
    month_start = today.replace(day=1)

    daily_df = sales_df[sales_df["Date Parsed"] == today]
    weekly_df = sales_df[sales_df["Date Parsed"] >= week_start]
    monthly_df = sales_df[sales_df["Date Parsed"] >= month_start]

    total_revenue = sales_df["Revenue"].sum()
    total_profit = sales_df["Gross Profit"].sum()
    total_units_sold = sales_df["Quantity"].sum()

    profit_margin = (
        total_profit / total_revenue * 100
        if total_revenue > 0 else 0
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Total Revenue", f"₹{total_revenue:,.0f}")
    c2.metric("Gross Profit", f"₹{total_profit:,.0f}")
    c3.metric("Units Sold", f"{total_units_sold:,}")
    c4.metric("Gross Margin", f"{profit_margin:.1f}%")

    st.subheader("3. Sales by Period")

    p1, p2, p3 = st.columns(3)

    p1.metric("Today's Sales", f"₹{daily_df['Revenue'].sum():,.0f}")
    p2.metric("Last 7 Days", f"₹{weekly_df['Revenue'].sum():,.0f}")
    p3.metric("This Month", f"₹{monthly_df['Revenue'].sum():,.0f}")

    # ---------- PRODUCT PERFORMANCE ----------

    st.divider()
    st.subheader("4. Product-wise Sales & Profitability")

    product_analysis = (
        sales_df.groupby("Product")
        .agg(
            Units_Sold=("Quantity", "sum"),
            Revenue=("Revenue", "sum"),
            Cost=("Cost", "sum"),
            Gross_Profit=("Gross Profit", "sum")
        )
        .reset_index()
    )

    product_analysis["Profit Margin (%)"] = (
        product_analysis["Gross_Profit"] /
        product_analysis["Revenue"].replace(0, np.nan) * 100
    ).fillna(0).round(2)

    product_analysis = product_analysis.sort_values(
        "Revenue", ascending=False
    )

    st.dataframe(
        product_analysis,
        use_container_width=True,
        hide_index=True
    )

    # ---------- BEST SELLERS ----------

    st.subheader("5. Best-Selling Products")

    best_sellers = product_analysis.sort_values(
        "Units_Sold", ascending=False
    ).head(5)

    st.bar_chart(
        best_sellers.set_index("Product")["Units_Sold"]
    )

    # ---------- PROFITABILITY ALERTS ----------

    st.subheader("6. Profitability Intelligence")

    for _, row in product_analysis.iterrows():

        if row["Gross_Profit"] < 0:
            st.error(
                f"{row['Product']}: Loss of "
                f"₹{abs(row['Gross_Profit']):,.0f}. "
                "Review its selling price and purchase cost."
            )
        elif row["Profit Margin (%)"] < 10:
            st.warning(
                f"{row['Product']}: Low gross margin "
                f"({row['Profit Margin (%)']:.1f}%). "
                "Consider reviewing its pricing."
            )

    # ---------- SALES TREND ----------

    st.subheader("7. Daily Revenue Trend")

    daily_sales = (
        sales_df.groupby("Date")["Revenue"]
        .sum()
        .reset_index()
        .sort_values("Date")
    )

    st.line_chart(
        daily_sales.set_index("Date")["Revenue"]
    )

    # ---------- AI SALES ADVISOR ----------

    st.divider()
    st.subheader("8. AI Sales Advisor")

    if st.button("🤖 Generate AI Sales Insights"):

        try:
            summary = product_analysis.to_json(orient="records")

            prompt = f"""
You are a practical small-business sales advisor.

Analyse these actual sales records:
{summary}

Total revenue: ₹{total_revenue:.2f}
Gross profit: ₹{total_profit:.2f}
Gross margin: {profit_margin:.2f}%
Units sold: {total_units_sold}

Provide:
1. Overall sales performance.
2. Best-performing products.
3. Products with weak profitability.
4. Pricing improvement suggestions.
5. Inventory and replenishment suggestions.
6. Three practical actions for the business owner.

Use only the supplied data for factual claims.
Clearly label suggestions as recommendations.
Do not invent missing information.
"""

            payload = json.dumps({
                "model": "llama3.2:3b",
                "prompt": prompt,
                "stream": False
            }).encode("utf-8")

            request = urllib.request.Request(
                "http://127.0.0.1:11434/api/generate",
                data=payload,
                headers={"Content-Type": "application/json"}
            )

            with urllib.request.urlopen(request, timeout=120) as response:
                result = json.loads(response.read().decode("utf-8"))

            st.markdown(result["response"])

        except Exception as e:
            st.error("Unable to generate AI insights. Check Ollama.")
            st.caption(str(e))

    # ---------- TRANSACTION HISTORY ----------

    st.divider()
    st.subheader("9. Sales Transaction History")

    display_sales = sales_df.drop(columns=["Date Parsed"])

    st.dataframe(
        display_sales,
        use_container_width=True,
        hide_index=True
    )

    st.download_button(
        "⬇️ Download Sales Report",
        data=display_sales.to_csv(index=False).encode("utf-8"),
        file_name="business_sales_report.csv",
        mime="text/csv"
    )

else:
    st.info("No sales recorded yet. Record your first sale above.")

st.caption(
    "Note: Profit shown is gross profit based on recorded product purchase "
    "cost and selling price. It excludes rent, salaries, taxes and other "
    "operating expenses. Data is currently stored in Streamlit session memory."
)

# ==========================================
# OPPORTUNITYRESCUE AI - MODULE NAVIGATION
# ==========================================

st.divider()

st.header("🚀 Business Intelligence Platform")

selected_module = st.radio(
    "Select Business Module",
    [
        "Sales Intelligence",
        "Workforce Intelligence"
    ],
    horizontal=True,
    key="main_business_module"
)

if selected_module == "Workforce Intelligence":

    from workforce.interface import show_workforce_dashboard

    show_workforce_dashboard()

elif selected_module == "Sales Intelligence":

    st.success("You are viewing Sales Intelligence.")