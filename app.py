import streamlit as st

# -----------------------------
# PAGE CONFIGURATION
# -----------------------------
st.set_page_config(
    page_title="Hire2Develop AI",
    page_icon="🤖",
    layout="wide"
)

# -----------------------------
# HEADER
# -----------------------------
st.title("🤖 Hire2Develop AI")
st.subheader("AI-Powered Talent Acquisition, Onboarding & Development System")

st.write(
    "From hiring the right talent to developing the right skills — "
    "an AI-enabled employee journey."
)

st.divider()

# -----------------------------
# WORKFLOW
# -----------------------------
st.markdown("### 🔄 Hire-to-Develop Workflow")

steps = [
    "1️⃣ Screening",
    "2️⃣ Job Matching",
    "3️⃣ Selection Insights",
    "4️⃣ Onboarding",
    "5️⃣ Skill-Gap Analysis",
    "6️⃣ Learning & Development",
    "7️⃣ Progress Tracking"
]

cols = st.columns(7)

for col, step in zip(cols, steps):
    col.markdown(f"**{step}**")

st.divider()

# -----------------------------
# CANDIDATE INPUT
# -----------------------------
st.markdown("### 📋 Candidate Analysis")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### 📄 Job Description")
    job_description = st.file_uploader(
        "Upload Job Description",
        type=["pdf", "docx", "txt"],
        key="job_description"
    )

with col2:
    st.markdown("#### 📄 Candidate Resume")
    resume = st.file_uploader(
        "Upload Candidate Resume",
        type=["pdf", "docx", "txt"],
        key="resume"
    )

st.markdown("#### 📝 Interview / Assessment Results")

interview_results = st.text_area(
    "Enter interview observations, assessment scores, or interviewer comments:",
    placeholder=(
        "Example:\n"
        "Communication: 4.5/5\n"
        "Recruitment Knowledge: 4/5\n"
        "Problem Solving: 3.5/5\n"
        "HR Analytics: 2/5\n"
        "Power BI: 1/5\n"
        "Overall observation: Good recruitment experience but needs improvement in analytics."
    ),
    height=180
)

st.write("")

# -----------------------------
# ANALYZE BUTTON
# -----------------------------
if st.button("🔍 Analyze Candidate", type="primary", use_container_width=True):

    if job_description is None:
        st.warning("Please upload the Job Description.")

    elif resume is None:
        st.warning("Please upload the Candidate Resume.")

    elif not interview_results.strip():
        st.warning("Please enter the Interview / Assessment Results.")

    else:
        st.success("Candidate information received successfully!")

        st.divider()

        # -----------------------------
        # DEMO RESULTS
        # -----------------------------
        st.markdown("## 📊 AI Candidate Analysis")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Overall Job Match", "84%")

        with col2:
            st.metric("Experience Match", "90%")

        with col3:
            st.metric("Skill Match", "82%")

        st.divider()

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### ✅ Strong Matches")

            st.write("• Recruitment & Sourcing")
            st.write("• Communication")
            st.write("• Interview Coordination")
            st.write("• Stakeholder Management")

        with col2:
            st.markdown("### ⚠️ Identified Skill Gaps")

            st.write("• HR Analytics")
            st.write("• Data Interpretation")
            st.write("• Power BI")

        st.divider()

        st.markdown("### 🧠 Selection Insight")

        st.info(
            "The candidate demonstrates strong recruitment experience and "
            "communication skills. The main development areas are HR analytics, "
            "data interpretation and Power BI."
        )

        st.markdown("### 🎯 AI Recommendation")

        st.success(
            "Suitable for the role — proceed with selection and create a "
            "personalized development plan."
        )

        st.divider()

        st.markdown("### 🚀 Next Automated Stage")

        st.write(
            "Once the candidate is selected, the system will automatically "
            "generate a personalized onboarding plan, identify skill gaps, "
            "recommend learning activities and track development progress."
        )

# -----------------------------
# FOOTER
# -----------------------------
st.divider()

st.caption(
    "Hire2Develop AI | Academic Prototype | "
    "AI supports HR decision-making; final decisions remain with human HR professionals."
)
