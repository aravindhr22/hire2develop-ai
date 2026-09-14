import streamlit as st
from google import genai
from pypdf import PdfReader
from docx import Document

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Hire2Develop AI",
    page_icon="🤖",
    layout="wide"
)

# ============================================================
# GEMINI CONNECTION
# ============================================================

try:
    api_key = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key)
except Exception:
    client = None


# ============================================================
# SUPABASE CONNECTION
# ============================================================

from supabase import create_client

supabase = None

try:
    supabase = create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )
except Exception as e:
    st.warning(f"Supabase history is unavailable: {e}")


# ============================================================
# DOCUMENT TEXT EXTRACTION
# ============================================================

def extract_text(uploaded_file):

    if uploaded_file is None:
        return ""

    file_name = uploaded_file.name.lower()

    try:

        # PDF
        if file_name.endswith(".pdf"):

            reader = PdfReader(uploaded_file)

            text = ""

            for page in reader.pages:
                page_text = page.extract_text()

                if page_text:
                    text += page_text + "\n"

            return text

        # DOCX
        elif file_name.endswith(".docx"):

            document = Document(uploaded_file)

            text = "\n".join(
                paragraph.text
                for paragraph in document.paragraphs
            )

            return text

        # TXT
        elif file_name.endswith(".txt"):

            return uploaded_file.read().decode(
                "utf-8",
                errors="ignore"
            )

        return ""

    except Exception as e:

        st.error(f"Could not read {uploaded_file.name}: {e}")

        return ""


# ============================================================
# GEMINI AI ANALYSIS
# ============================================================

def analyze_candidate(job_text, resume_text, interview_text):

    prompt = f"""

You are an AI assistant supporting a Human Resources professional.

You are analyzing a candidate for a job.

IMPORTANT:
You are providing decision SUPPORT only.
Do not make decisions based on protected characteristics such as
age, gender, religion, caste, race, disability, marital status,
or other sensitive personal characteristics.

Analyze ONLY job-relevant information.

==================================================
JOB DESCRIPTION
==================================================

{job_text}

==================================================
CANDIDATE RESUME
==================================================

{resume_text}

==================================================
INTERVIEW / ASSESSMENT RESULTS
==================================================

{interview_text}

==================================================
TASK
==================================================

Perform the following analysis.

1. CANDIDATE SCREENING

Identify:
- Education relevant to the role
- Relevant experience
- Relevant skills
- Certifications
- Major job-related strengths

2. JOB MATCHING

Calculate an approximate match score from 0–100 based on:
- Skills
- Experience
- Qualifications
- Role responsibilities

Give:
- Overall match %
- Skill match %
- Experience match %
- Qualification match %

3. STRENGTHS

List the candidate's strongest job-related capabilities.

4. SKILL GAPS

Identify important skills required by the job that the candidate
currently appears to lack or needs to strengthen.

Classify each as:
- High priority
- Medium priority
- Low priority

5. INTERVIEW INSIGHTS

Combine the interview/assessment results with the resume.

Identify:
- Strong competencies
- Development areas
- Relevant concerns

6. SELECTION SUPPORT

Give one of these:
- Strong fit
- Potential fit
- Needs further assessment

Explain the reasoning briefly.

Do NOT make the final hiring decision.

7. DEVELOPMENT PRIORITIES

Suggest the most important skills that should later be used
for onboarding and employee development.

==================================================
OUTPUT FORMAT
==================================================

# AI Candidate Analysis

## 1. Candidate Screening

[summary]

## 2. Job Matching

Overall Match: XX%
Skill Match: XX%
Experience Match: XX%
Qualification Match: XX%

## 3. Key Strengths

- ...
- ...
- ...

## 4. Skill Gaps

| Skill | Priority | Reason |
|---|---|---|
| ... | High/Medium/Low | ... |

## 5. Interview Insights

[summary]

## 6. Selection Support

Recommendation: ...

Reason:
...

## 7. Development Priorities

- ...
- ...
- ...

Remember:
AI supports HR decision-making. Final decisions remain with
qualified human HR professionals.
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt
    )

    return response.text


# ============================================================
# HEADER
# ============================================================

st.title("🤖 Hire2Develop AI")

st.subheader(
    "AI-Powered Talent Acquisition, Onboarding & Development System"
)

st.write(
    "From hiring the right talent to developing the right skills — "
    "an AI-enabled employee journey."
)

st.divider()


# ============================================================
# CANDIDATE HISTORY SIDEBAR
# ============================================================

# Version number used to force fresh upload boxes when starting a new candidate.
if "candidate_form_version" not in st.session_state:
    st.session_state["candidate_form_version"] = 0


def reset_candidate():
    """Clear the current candidate and prepare a completely fresh form."""
    for key in [
        "candidate_id", "candidate_name", "position",
        "job_text", "resume_text", "interview_results",
        "analysis", "onboarding", "skillgap", "learning",
        "progress_review", "saved_progress", "development_progress",
        "history_selector"
    ]:
        st.session_state.pop(key, None)

    # Changing the uploader key guarantees that old uploaded files disappear.
    st.session_state["candidate_form_version"] += 1


if supabase is not None:
    st.sidebar.markdown("## 🗂 Candidate History")

    try:
        history_response = (
            supabase
            .table("candidates")
            .select("id,candidate_name,position,progress,updated_at")
            .order("updated_at", desc=True)
            .execute()
        )

        history_rows = history_response.data or []

        if history_rows:
            history_labels = [
                f"{row['candidate_name']} — {row['position']}"
                for row in history_rows
            ]

            selected_label = st.sidebar.selectbox(
                "Select a saved candidate",
                history_labels,
                key="history_selector"
            )

            selected_index = history_labels.index(selected_label)
            selected_candidate_id = history_rows[selected_index]["id"]

            if st.sidebar.button(
                "📂 Load Candidate",
                use_container_width=True
            ):
                full_response = (
                    supabase
                    .table("candidates")
                    .select("*")
                    .eq("id", selected_candidate_id)
                    .limit(1)
                    .execute()
                )

                if full_response.data:
                    row = full_response.data[0]

                    st.session_state["candidate_id"] = row["id"]
                    st.session_state["candidate_name"] = row.get("candidate_name", "") or ""
                    st.session_state["position"] = row.get("position", "") or ""
                    st.session_state["job_text"] = row.get("job_description", "") or ""
                    st.session_state["resume_text"] = row.get("resume_text", "") or ""
                    st.session_state["interview_results"] = row.get("interview_results", "") or ""

                    saved_outputs = {
                        "analysis": "candidate_analysis",
                        "onboarding": "onboarding_plan",
                        "skillgap": "skill_gap_analysis",
                        "learning": "learning_plan",
                        "progress_review": "progress_review"
                    }

                    for session_key, database_key in saved_outputs.items():
                        saved_value = row.get(database_key)
                        if saved_value:
                            st.session_state[session_key] = saved_value
                        else:
                            st.session_state.pop(session_key, None)

                    saved_progress = row.get("progress") or 0
                    st.session_state["saved_progress"] = int(saved_progress)
                    st.session_state["development_progress"] = int(saved_progress)

                    # Force fresh upload boxes while keeping the loaded candidate data.
                    st.session_state["candidate_form_version"] += 1

                    st.rerun()
                else:
                    st.sidebar.error("Could not load the selected candidate.")

            st.sidebar.caption(
                "Select a candidate and load their saved AI analysis, onboarding, "
                "skill gaps, learning plan and progress."
            )
        else:
            st.sidebar.info("No saved candidates yet.")

        st.sidebar.button(
            "➕ Start New Candidate",
            use_container_width=True,
            on_click=reset_candidate,
            key="start_new_candidate_button"
        )

    except Exception as e:
        st.sidebar.error(f"Could not load candidate history: {e}")


# ============================================================
# WORKFLOW
# ============================================================

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


# ============================================================
# CANDIDATE INPUT
# ============================================================

st.markdown("### 📋 Candidate Analysis")

profile_col1, profile_col2 = st.columns(2)

with profile_col1:
    candidate_name = st.text_input(
        "Candidate Name",
        value=st.session_state.get("candidate_name", ""),
        key="candidate_name"
    )

with profile_col2:
    position = st.text_input(
        "Position",
        value=st.session_state.get("position", ""),
        key="position"
    )

col1, col2 = st.columns(2)

with col1:

    st.markdown("#### 📄 Job Description")

    job_description = st.file_uploader(
        "Upload Job Description",
        type=["pdf", "docx", "txt"],
        key=f"job_description_{st.session_state['candidate_form_version']}"
    )


with col2:

    st.markdown("#### 📄 Candidate Resume")

    resume = st.file_uploader(
        "Upload Candidate Resume",
        type=["pdf", "docx", "txt"],
        key=f"resume_{st.session_state['candidate_form_version']}"
    )


st.markdown("#### 📝 Interview / Assessment Results")

# Use a fresh widget key for each candidate/session so the text box
# remains editable on every device and does not get stuck with an
# old candidate's widget state.
interview_widget_key = f"interview_results_{st.session_state['candidate_form_version']}"

if interview_widget_key not in st.session_state:
    st.session_state[interview_widget_key] = st.session_state.get(
        "interview_results", ""
    )

interview_results = st.text_area(
    "Enter interview observations, assessment scores, "
    "or interviewer comments:",
    placeholder=(
        "Example:\n"
        "Communication: 4.5/5\n"
        "Recruitment Knowledge: 4/5\n"
        "Problem Solving: 3.5/5\n"
        "HR Analytics: 2/5\n"
        "Power BI: 1/5\n"
        "Overall observation: Good recruitment experience "
        "but needs improvement in analytics."
    ),
    height=180,
    key=interview_widget_key
)

# Keep the latest typed value available for analysis and history saving.
st.session_state["interview_results"] = interview_results


st.write("")


# ============================================================
# ANALYZE BUTTON
# ============================================================

if st.button(
    "🔍 Analyze Candidate",
    type="primary",
    use_container_width=True
):

    if client is None:

        st.error(
            "Gemini AI is not connected. "
            "Please check the Streamlit Secret named GEMINI_API_KEY."
        )

    elif job_description is None:

        st.warning(
            "Please upload the Job Description."
        )

    elif resume is None:

        st.warning(
            "Please upload the Candidate Resume."
        )

    elif not interview_results.strip():

        st.warning(
            "Please enter the Interview / Assessment Results."
        )

    else:

        with st.spinner(
            "🤖 AI is analyzing the candidate..."
        ):

            job_text = extract_text(job_description)
            resume_text = extract_text(resume)

            # Store candidate source data for history
            st.session_state["job_text"] = job_text
            st.session_state["resume_text"] = resume_text
            st.session_state["interview_results"] = interview_results

            if not job_text:
                st.error(
                    "Could not extract text from the Job Description."
                )
                st.stop()

            if not resume_text:

                st.error(
                    "Could not extract text from the Resume."
                )
                st.stop()

            try:

                result = analyze_candidate(
                    job_text,
                    resume_text,
                    interview_results
                )

                st.session_state["analysis"] = result

            except Exception as e:

                st.error(
                    f"AI analysis failed: {e}"
                )


# ============================================================
# DISPLAY AI RESULT
# ============================================================

if "analysis" in st.session_state:

    st.divider()

    st.markdown("## 🧠 AI Candidate Analysis")

    st.markdown(
        st.session_state["analysis"]
    )

    st.divider()

    st.info(
        "⚠️ Human Oversight: AI provides structured decision "
        "support. Final hiring decisions must remain with "
        "qualified HR professionals."
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Hire2Develop AI | Academic Prototype | "
    "AI supports HR decision-making; final decisions remain "
    "with human HR professionals."
)
# ============================================================
# STAGE 4 - AI PERSONALIZED ONBOARDING
# ============================================================

st.divider()

st.markdown("## 🤝 AI-Personalized Onboarding")

st.write(
    "Generate a personalized onboarding plan using the candidate's "
    "job requirements, resume, interview insights and AI analysis."
)

if "analysis" in st.session_state:

    if st.button(
        "🚀 Generate Onboarding Plan",
        type="primary",
        use_container_width=True
    ):

        try:

            # Use saved candidate data when continuing from history.
            onboarding_job_text = (
                st.session_state.get("job_text")
                or extract_text(job_description)
            )
            onboarding_resume_text = (
                st.session_state.get("resume_text")
                or extract_text(resume)
            )

            onboarding_prompt = f"""
You are an AI assistant supporting Human Resources professionals.

Create a personalized 90-day employee onboarding plan using the information below.

IMPORTANT:
- Make the plan specific to the job and candidate.
- Use the candidate's strengths and skill gaps.
- Do not use sensitive personal characteristics.
- AI supports HR and managers; humans remain responsible for final decisions.

========================
JOB DESCRIPTION
========================
{onboarding_job_text}

========================
CANDIDATE RESUME
========================
{onboarding_resume_text}

========================
INTERVIEW / ASSESSMENT
========================
{interview_results}

========================
AI CANDIDATE ANALYSIS
========================
{st.session_state["analysis"]}

========================
CREATE THE ONBOARDING PLAN
========================

Provide these sections:

1. ONBOARDING OBJECTIVE
Explain the main objective for this employee's onboarding.

2. FIRST WEEK
Give practical activities for the first week.

3. FIRST 30 DAYS
Give important learning and work priorities.

4. DAYS 31-60
Explain responsibilities and skills to be developed.

5. DAYS 61-90
Explain how the employee should move toward independent performance.

6. TRAINING PRIORITIES
Recommend training areas based on the candidate's skill gaps.

7. STAKEHOLDER CONNECTIONS
Suggest important teams or people the employee should interact with.

8. EARLY PERFORMANCE GOALS
Give 4-5 measurable and realistic goals.

9. MANAGER CHECK-INS
Suggest a schedule for manager feedback and progress reviews.

10. PERSONALIZED DEVELOPMENT FOCUS
Explain how this plan addresses the candidate's strengths and development areas.

Keep the answer practical, structured and suitable for an HR demonstration.
"""

            with st.spinner(
                "🤖 AI is creating the personalized onboarding plan..."
            ):

                onboarding_response = client.models.generate_content(
                    model="gemini-3.5-flash-lite",
                    contents=onboarding_prompt
                )

                st.session_state["onboarding"] = onboarding_response.text

        except Exception as e:

            st.error(f"Onboarding plan generation failed: {e}")

else:

    st.info(
        "Please analyze the candidate first. "
        "The onboarding plan will use the AI candidate analysis."
    )


# ============================================================
# DISPLAY ONBOARDING PLAN
# ============================================================

if "onboarding" in st.session_state:

    st.divider()

    st.markdown("## 📋 Personalized 90-Day Onboarding Plan")

    st.markdown(st.session_state["onboarding"])

    st.success(
        "✅ Personalized onboarding plan generated successfully."
    )

    st.caption(
        "AI provides onboarding recommendations. "
        "HR and the reporting manager should review and customize the plan."
    )

    st.caption(
        "AI provides onboarding recommendations. "
        "HR and the reporting manager should review and customize the plan."
    )
# ============================================================
# STAGE 5 - AI SKILL-GAP ANALYSIS
# ============================================================

st.divider()

st.markdown("## 🎯 AI Skill-Gap Analysis")

st.write(
    "Identify the candidate's current skill levels, compare them with "
    "job requirements, and prioritize the areas that need development."
)

if "analysis" in st.session_state:

    if st.button(
        "🔍 Analyze Skill Gaps",
        type="primary",
        use_container_width=True
    ):

        try:

            # Use saved candidate data when continuing from history.
            skillgap_job_text = (
                st.session_state.get("job_text")
                or extract_text(job_description)
            )
            skillgap_resume_text = (
                st.session_state.get("resume_text")
                or extract_text(resume)
            )

            skillgap_prompt = f"""
You are an AI-powered Talent Development assistant supporting HR professionals.

Perform a detailed skill-gap analysis for the candidate using the Job
Description, Resume, Interview/Assessment Results and AI Candidate Analysis.

IMPORTANT:
- Compare the skills actually required for the job with the candidate's
  demonstrated skills.
- Do not assume skills that are not supported by the information provided.
- Do not use sensitive personal characteristics.
- AI provides recommendations; HR and managers make the final decisions.

========================
JOB DESCRIPTION
========================
{skillgap_job_text}

========================
CANDIDATE RESUME
========================
{skillgap_resume_text}

========================
INTERVIEW / ASSESSMENT
========================
{interview_results}

========================
AI CANDIDATE ANALYSIS
========================
{st.session_state["analysis"]}

========================
SKILL-GAP ANALYSIS
========================

Analyze the candidate against the job requirements.

For each important skill, provide:

- Skill
- Required Level
- Current Level
- Gap Level
- Priority
- Development Recommendation

Use these levels where appropriate:

Required Level:
Beginner / Intermediate / Advanced

Current Level:
Limited / Basic / Moderate / Strong / Advanced

Gap Level:
Low / Medium / High

Priority:
Low / Medium / High

Then provide these sections:

1. SKILL-GAP SUMMARY
Give a short overall assessment.

2. STRENGTHS
List the skills where the candidate already meets or exceeds the requirement.

3. HIGH-PRIORITY GAPS
Identify the most important skills that require development.

4. MEDIUM-PRIORITY GAPS
Identify skills that should be improved but are less urgent.

5. DEVELOPMENT RECOMMENDATIONS
Recommend practical ways to improve the identified gaps.

6. READINESS ASSESSMENT
Explain whether the candidate appears ready for the role immediately,
ready with targeted development, or requires significant development.

7. HR ACTION POINTS
Give practical next steps for HR and the reporting manager.

Make the analysis clear, structured and suitable for an HR presentation.
"""

            with st.spinner(
                "🤖 AI is analyzing the candidate's skill gaps..."
            ):

                skillgap_response = client.models.generate_content(
                    model="gemini-3.5-flash-lite",
                    contents=skillgap_prompt
                )

                st.session_state["skillgap"] = skillgap_response.text

        except Exception as e:

            st.error(f"Skill-gap analysis failed: {e}")

else:

    st.info(
        "Please analyze the candidate first. "
        "The skill-gap analysis will use the AI candidate analysis."
    )


# ============================================================
# DISPLAY SKILL-GAP ANALYSIS
# ============================================================

if "skillgap" in st.session_state:

    st.divider()

    st.markdown("## 📊 Skill-Gap Analysis Result")

    st.markdown(st.session_state["skillgap"])

    st.success(
        "✅ Skill-gap analysis generated successfully."
    )
# ============================================================
# STAGE 6 - AI LEARNING & DEVELOPMENT PLAN
# ============================================================

st.divider()

st.markdown("## 📚 AI Learning & Development Plan")

st.write(
    "Create a personalized learning path based on the candidate's "
    "identified skill gaps and development priorities."
)

if "skillgap" in st.session_state:

    if st.button(
        "📚 Generate Learning Plan",
        type="primary",
        use_container_width=True
    ):

        try:

            learning_prompt = f"""
You are an AI-powered Learning and Development assistant supporting HR
professionals.

Create a personalized employee learning and development plan using the
candidate's Skill-Gap Analysis and Candidate Analysis.

IMPORTANT:
- Prioritize learning based on the identified skill gaps.
- Focus on practical workplace development.
- Do not use sensitive personal characteristics.
- AI provides recommendations; HR and managers should validate the plan.

========================
AI CANDIDATE ANALYSIS
========================
{st.session_state["analysis"]}

========================
SKILL-GAP ANALYSIS
========================
{st.session_state["skillgap"]}

========================
CREATE THE LEARNING PLAN
========================

Provide the following:

1. DEVELOPMENT OBJECTIVE
Explain the main development objective.

2. PRIORITY SKILLS
Identify the top skills that should be developed first.

3. LEARNING ROADMAP
Create a structured learning roadmap.

For each learning area provide:
- Skill
- Learning objective
- Recommended learning activity
- Practical workplace activity
- Suggested duration
- Expected outcome

4. 30-DAY LEARNING PLAN
Give specific learning activities for the first 30 days.

5. 60-DAY LEARNING PLAN
Give development activities for days 31-60.

6. 90-DAY LEARNING PLAN
Give development activities for days 61-90.

7. PRACTICAL PROJECTS
Suggest practical projects that can help the employee apply the new skills.

8. MANAGER / MENTOR SUPPORT
Explain how the manager or mentor can support development.

9. EXPECTED OUTCOMES
Describe what the employee should be able to do after completing the plan.

Keep the plan practical, measurable and suitable for an HR demonstration.
"""

            with st.spinner(
                "🤖 AI is creating the personalized learning plan..."
            ):

                learning_response = client.models.generate_content(
                    model="gemini-3.5-flash-lite",
                    contents=learning_prompt
                )

                st.session_state["learning"] = learning_response.text

        except Exception as e:

            st.error(f"Learning plan generation failed: {e}")

else:

    st.info(
        "Please complete the Skill-Gap Analysis first."
    )


# ============================================================
# DISPLAY LEARNING PLAN
# ============================================================

if "learning" in st.session_state:

    st.divider()

    st.markdown("## 🗺️ Personalized Learning Roadmap")

    st.markdown(st.session_state["learning"])

    st.success(
        "✅ Personalized learning and development plan generated successfully."
    )

    st.caption(
        "HR and managers should review and customize the recommended "
        "learning activities based on organizational requirements."
    )


# ============================================================
# STAGE 7 - EMPLOYEE PROGRESS TRACKING
# ============================================================

st.divider()

st.markdown("## 📈 Employee Development Progress Tracking")

st.write(
    "Track progress against the personalized development plan and "
    "identify areas requiring additional support."
)

if "learning" in st.session_state:

    st.markdown("### 🎯 Update Development Progress")

    progress = st.slider(
        "Overall Development Progress (%)",
        min_value=0,
        max_value=100,
        value=st.session_state.get("saved_progress", 25),
        step=5,
        key="development_progress"
    )

    st.session_state["saved_progress"] = progress

    col1, col2 = st.columns(2)

    with col1:

        completed_training = st.number_input(
            "Completed Learning Activities",
            min_value=0,
            max_value=20,
            value=1,
            step=1
        )

    with col2:

        total_training = st.number_input(
            "Total Planned Learning Activities",
            min_value=1,
            max_value=20,
            value=5,
            step=1
        )

    manager_feedback = st.text_area(
        "Manager / Mentor Feedback",
        placeholder="Enter feedback about the employee's development..."
    )

    if st.button(
        "📊 Generate Progress Review",
        type="primary",
        use_container_width=True
    ):

        try:

            progress_prompt = f"""
You are an AI-powered Talent Development assistant.

Evaluate an employee's development progress using the information below.

========================
LEARNING & DEVELOPMENT PLAN
========================
{st.session_state["learning"]}

========================
CURRENT PROGRESS
========================
Overall Progress: {progress}%

Completed Learning Activities:
{completed_training}

Total Planned Learning Activities:
{total_training}

Manager / Mentor Feedback:
{manager_feedback}

========================
CREATE PROGRESS REVIEW
========================

Provide:

1. PROGRESS SUMMARY
Give a concise assessment of current development progress.

2. COMPLETION STATUS
Comment on the employee's learning activity completion.

3. AREAS OF PROGRESS
Identify areas where the employee is improving.

4. AREAS REQUIRING ATTENTION
Identify areas that still need development.

5. RECOMMENDED NEXT ACTIONS
Suggest practical next steps.

6. MANAGER ACTION
Suggest what the manager or mentor should do next.

7. DEVELOPMENT STATUS
Classify the employee's current development status as:

- On Track
- Needs Attention
- Requires Additional Support

Explain the reason for the classification.

Do not make decisions based on sensitive personal characteristics.
AI provides recommendations and HR/managers remain responsible for
development decisions.
"""

            with st.spinner(
                "🤖 AI is evaluating development progress..."
            ):

                progress_response = client.models.generate_content(
                    model="gemini-3.5-flash-lite",
                    contents=progress_prompt
                )

                st.session_state["progress_review"] = progress_response.text

        except Exception as e:

            st.error(f"Progress review failed: {e}")

else:

    st.info(
        "Complete the Learning & Development Plan first to enable progress tracking."
    )


# ============================================================
# DISPLAY PROGRESS REVIEW
# ============================================================

if "progress_review" in st.session_state:

    st.divider()

    st.markdown("## 📊 AI Development Progress Review")

    st.progress(progress / 100)

    st.markdown(
        f"### Current Progress: {progress}%"
    )

    st.markdown(st.session_state["progress_review"])

    st.success(
        "✅ Development progress reviewed successfully."
    )

    st.caption(
        "AI provides progress insights and recommendations. "
        "HR and managers should validate the review before taking action."
    )
    st.caption(
        "AI identifies potential development needs. "
        "HR and managers should validate the findings before taking action."
    )
# ============================================================
# STAGES 8-11 - PROFESSIONAL HR DASHBOARD
# ============================================================

import io
import re
from xml.sax.saxutils import escape
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak
)


# ============================================================
# STAGES 8-10 - RICH HR DASHBOARD
# ============================================================

import io
import re
from xml.sax.saxutils import escape
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak
)

# ============================================================
# STAGE 8 - PROFESSIONAL HR DASHBOARD
# ============================================================

st.divider()

# Dashboard styling - keeps the app clean while adding a modern HR
# command-center look.
st.markdown("""
<style>
/* ============================================================
   DARK/LIGHT MODE SAFE DASHBOARD STYLING
   Uses Streamlit's theme variables instead of hard-coded white
   backgrounds and dark text. This keeps the dashboard readable
   in both light and dark mode.
   ============================================================ */
.dashboard-hero {
    padding: 22px 24px;
    border-radius: 16px;
    background: var(--secondary-background-color);
    border: 1px solid rgba(128, 128, 128, 0.25);
    margin-bottom: 18px;
    color: var(--text-color);
}
.dashboard-hero h2 {
    margin-bottom: 4px;
    color: var(--text-color) !important;
}
.kpi-card {
    padding: 16px;
    border-radius: 14px;
    border: 1px solid rgba(128, 128, 128, 0.25);
    background: var(--secondary-background-color);
    box-shadow: 0 3px 12px rgba(0, 0, 0, 0.08);
    min-height: 105px;
    color: var(--text-color);
}
.kpi-label {
    font-size: 0.82rem;
    color: var(--text-color);
    opacity: 0.72;
    margin-bottom: 5px;
}
.kpi-value {
    font-size: 1.35rem;
    font-weight: 700;
    color: var(--text-color);
}
.section-card {
    padding: 18px 20px;
    border-radius: 14px;
    border: 1px solid rgba(128, 128, 128, 0.25);
    background: var(--secondary-background-color);
    color: var(--text-color);
    margin-top: 10px;
}
.journey-card {
    padding: 12px 10px;
    border-radius: 12px;
    text-align: center;
    border: 1px solid rgba(128, 128, 128, 0.25);
    background: var(--secondary-background-color);
    color: var(--text-color);
    min-height: 92px;
}
.journey-done {
    background: rgba(22, 163, 74, 0.12);
    border-color: rgba(22, 163, 74, 0.35);
}
.journey-pending {
    background: var(--secondary-background-color);
    border-color: rgba(128, 128, 128, 0.25);
}
.insight-card {
    padding: 15px;
    border-radius: 13px;
    border: 1px solid rgba(128, 128, 128, 0.25);
    background: var(--secondary-background-color);
    color: var(--text-color);
    min-height: 105px;
}
.insight-card b,
.insight-card span {
    color: var(--text-color);
}
.small-muted {
    color: var(--text-color);
    opacity: 0.72;
    font-size: 0.86rem;
}

/* Vega-Lite charts: inherit the active Streamlit theme. */
[data-testid="stVegaLiteChart"] {
    background: transparent !important;
    border-radius: 14px;
}
[data-testid="stVegaLiteChart"] text {
    fill: var(--text-color) !important;
}
[data-testid="stVegaLiteChart"] .mark-text {
    fill: var(--text-color) !important;
}
[data-testid="stVegaLiteChart"] .role-axis-grid {
    stroke: rgba(128, 128, 128, 0.22) !important;
}

/* Streamlit alert/info boxes also look better with the active theme. */
[data-testid="stAlert"] {
    border-radius: 12px;
}

/* Extra protection for dark mode in browsers where CSS variables
   are not inherited into SVG text immediately. */
@media (prefers-color-scheme: dark) {
    .dashboard-hero,
    .kpi-card,
    .section-card,
    .journey-card,
    .insight-card {
        color: #f5f7fa;
    }
    .dashboard-hero h2,
    .kpi-value,
    .insight-card b,
    .insight-card span {
        color: #f5f7fa !important;
    }
    .kpi-label,
    .small-muted {
        color: #cbd5e1 !important;
    }
}
</style>
""", unsafe_allow_html=True)

# Extract basic candidate/job information.
# Prefer saved profile/history values when available.
dashboard_candidate = st.session_state.get("candidate_name", "").strip()
dashboard_job = st.session_state.get("position", "").strip()

if not dashboard_candidate:
    dashboard_candidate = "Candidate"

if not dashboard_job:
    dashboard_job = "Target Role"

if dashboard_candidate == "Candidate":
    try:
        dashboard_resume_text = (
            st.session_state.get("resume_text")
            or extract_text(resume)
        )
        name_match = re.search(
            r"(?:Name|Candidate Name)\s*[:\-]\s*([A-Za-z .]+)",
            dashboard_resume_text,
            re.IGNORECASE
        )
        if name_match:
            dashboard_candidate = name_match.group(1).strip()
    except Exception:
        pass

if dashboard_job == "Target Role":
    try:
        dashboard_job_text = (
            st.session_state.get("job_text")
            or extract_text(job_description)
        )
        role_match = re.search(
            r"(?:Position|Role|Job Title)\s*[:\-]\s*([A-Za-z &/\-]+)",
            dashboard_job_text,
            re.IGNORECASE
        )
        if role_match:
            dashboard_job = role_match.group(1).strip()
    except Exception:
        pass

analysis_done = "analysis" in st.session_state
onboarding_done = "onboarding" in st.session_state
skillgap_done = "skillgap" in st.session_state
learning_done = "learning" in st.session_state
progress_done = "progress_review" in st.session_state

completed_stages = sum([
    analysis_done,
    onboarding_done,
    skillgap_done,
    learning_done,
    progress_done
])

dashboard_progress = int(st.session_state.get(
    "development_progress",
    st.session_state.get("saved_progress", 0)
) or 0)

# ------------------------------------------------------------
# Dashboard hero
# ------------------------------------------------------------

st.markdown(f"""
<div class="dashboard-hero">
    <h2>🏢 Hire2Develop HR Command Center</h2>
    <div class="small-muted">
        Candidate journey from AI-assisted hiring to personalized employee development.
    </div>
</div>
""", unsafe_allow_html=True)

# Candidate profile cards
k1, k2, k3, k4 = st.columns(4)

with k1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">👤 Candidate</div>
        <div class="kpi-value">{escape(dashboard_candidate)}</div>
    </div>
    """, unsafe_allow_html=True)

with k2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">💼 Target Role</div>
        <div class="kpi-value">{escape(dashboard_job)}</div>
    </div>
    """, unsafe_allow_html=True)

with k3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">🔄 AI Outputs Completed</div>
        <div class="kpi-value">{completed_stages} / 5</div>
    </div>
    """, unsafe_allow_html=True)

with k4:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">📈 Development Progress</div>
        <div class="kpi-value">{dashboard_progress}%</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("### 📊 Talent Insights")

# ------------------------------------------------------------
# Extract AI job-match scores for the bar chart.
# ------------------------------------------------------------

analysis_text = st.session_state.get("analysis", "")

def get_score(label):
    match = re.search(
        rf"{re.escape(label)}\s*:\s*(\d{{1,3}})%?",
        analysis_text,
        re.IGNORECASE
    )
    return int(match.group(1)) if match else None

overall_match = get_score("Overall Match")
skill_match = get_score("Skill Match")
experience_match = get_score("Experience Match")
qualification_match = get_score("Qualification Match")

fit_data = []
for label, value in [
    ("Overall Match", overall_match),
    ("Skill Match", skill_match),
    ("Experience Match", experience_match),
    ("Qualification Match", qualification_match),
]:
    if value is not None:
        fit_data.append({"metric": label, "score": value})

# ------------------------------------------------------------
# Interview competency scores for the second bar chart.
# ------------------------------------------------------------

interview_text = st.session_state.get("interview_results", "")

interview_data = []
score_pattern = re.compile(
    r"^\s*([^:\n]+?)\s*:\s*(\d+(?:\.\d+)?)\s*/\s*5\s*$",
    re.MULTILINE
)

for match in score_pattern.finditer(interview_text):
    label = match.group(1).strip()
    score = float(match.group(2))
    if label.lower() not in {"overall observation", "overall score"}:
        level = "Strong" if score >= 4 else ("Moderate" if score >= 3 else "Development Need")
        interview_data.append({
            "competency": label,
            "score": score,
            "level": level
        })

# Two rich chart panels
chart_left, chart_right = st.columns(2)

with chart_left:
    st.markdown("#### 🎯 Candidate–Role Fit")
    if fit_data:
        st.vega_lite_chart(
            fit_data,
            {
                "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
                "mark": {
                    "type": "bar",
                    "cornerRadiusEnd": 7,
                    "size": 28
                },
                "encoding": {
                    "y": {
                        "field": "metric",
                        "type": "nominal",
                        "sort": "-x",
                        "title": None
                    },
                    "x": {
                        "field": "score",
                        "type": "quantitative",
                        "scale": {"domain": [0, 100]},
                        "title": "Match Score (%)"
                    },
                    "color": {
                        "field": "metric",
                        "type": "nominal",
                        "scale": {
                            "range": ["#2563eb", "#16a34a", "#7c3aed", "#f59e0b"]
                        },
                        "legend": None
                    },
                    "tooltip": [
                        {"field": "metric", "type": "nominal"},
                        {"field": "score", "type": "quantitative", "format": ".0f"}
                    ]
                },
                "config": {
                    "background": "transparent",
                    "view": {"stroke": None},
                    "axis": {
                        "labelFontSize": 12,
                        "titleFontSize": 12,
                        "labelColor": "#94a3b8",
                        "titleColor": "#94a3b8",
                        "gridColor": "#475569"
                    }
                }
            },
            use_container_width=True
        )
    else:
        st.info("Complete AI Candidate Analysis to populate the fit chart.")

with chart_right:
    st.markdown("#### 🧠 Interview Competency Profile")
    if interview_data:
        st.vega_lite_chart(
            interview_data,
            {
                "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
                "mark": {
                    "type": "bar",
                    "cornerRadiusEnd": 7,
                    "size": 25
                },
                "encoding": {
                    "y": {
                        "field": "competency",
                        "type": "nominal",
                        "sort": "-x",
                        "title": None
                    },
                    "x": {
                        "field": "score",
                        "type": "quantitative",
                        "scale": {"domain": [0, 5]},
                        "title": "Score (/5)"
                    },
                    "color": {
                        "field": "level",
                        "type": "nominal",
                        "scale": {
                            "domain": ["Strong", "Moderate", "Development Need"],
                            "range": ["#16a34a", "#f59e0b", "#dc2626"]
                        },
                        "legend": {"title": "Competency Level"}
                    },
                    "tooltip": [
                        {"field": "competency", "type": "nominal"},
                        {"field": "score", "type": "quantitative", "format": ".1f"},
                        {"field": "level", "type": "nominal"}
                    ]
                },
                "config": {
                    "background": "transparent",
                    "view": {"stroke": None},
                    "axis": {
                        "labelFontSize": 12,
                        "titleFontSize": 12,
                        "labelColor": "#94a3b8",
                        "titleColor": "#94a3b8",
                        "gridColor": "#475569"
                    }
                }
            },
            use_container_width=True
        )
    else:
        st.info("Enter interview/assessment scores to populate the competency chart.")

# ------------------------------------------------------------
# Development Progress Donut
# ------------------------------------------------------------

progress_col, status_col = st.columns([1, 1])

with progress_col:
    st.markdown("#### 🍩 Development Progress")
    progress_data = [
        {"status": "Completed", "value": dashboard_progress},
        {"status": "Remaining", "value": max(0, 100 - dashboard_progress)}
    ]

    st.vega_lite_chart(
        progress_data,
        {
            "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
            "mark": {
                "type": "arc",
                "innerRadius": 62,
                "outerRadius": 105
            },
            "encoding": {
                "theta": {
                    "field": "value",
                    "type": "quantitative"
                },
                "color": {
                    "field": "status",
                    "type": "nominal",
                    "scale": {
                        "domain": ["Completed", "Remaining"],
                        "range": ["#2563eb", "#e8edf5"]
                    },
                    "legend": {"title": None}
                },
                "tooltip": [
                    {"field": "status", "type": "nominal"},
                    {"field": "value", "type": "quantitative", "format": ".0f"}
                ]
            },
            "view": {"stroke": None},
            "background": "transparent"
        },
        use_container_width=True
    )

with status_col:
    st.markdown("#### 🚦 Development Status")
    if dashboard_progress >= 70:
        st.success(f"🟢 Strong Progress — {dashboard_progress}%")
        status_message = "The employee is progressing well against the development plan."
    elif dashboard_progress >= 40:
        st.warning(f"🟡 Needs Attention — {dashboard_progress}%")
        status_message = "Some additional support or follow-up may be useful."
    else:
        st.error(f"🔴 Requires Support — {dashboard_progress}%")
        status_message = "The employee may need closer manager/mentor support."

    st.markdown(
        f'<div class="section-card"><b>HR Interpretation</b><br>'
        f'<span class="small-muted">{status_message}</span></div>',
        unsafe_allow_html=True
    )

    st.markdown("#### 📌 Workflow Completion")
    workflow_completion_pct = round((completed_stages / 5) * 100)
    st.progress(workflow_completion_pct / 100)
    st.caption(
        f"{completed_stages}/5 major AI outputs completed "
        f"({workflow_completion_pct}%)"
    )

# ============================================================
# STAGE 9 - CONNECTED WORKFLOW
# ============================================================

st.markdown("### 🔄 Connected Hire-to-Develop Journey")

workflow_status = [
    ("1️⃣ Screening", analysis_done),
    ("2️⃣ Job Matching", analysis_done),
    ("3️⃣ Selection Insights", analysis_done),
    ("4️⃣ Onboarding", onboarding_done),
    ("5️⃣ Skill-Gap Analysis", skillgap_done),
    ("6️⃣ Learning & Development", learning_done),
    ("7️⃣ Progress Tracking", progress_done)
]

workflow_cols = st.columns(7)

for index, (stage_name, completed) in enumerate(workflow_status):
    with workflow_cols[index]:
        card_class = "journey-done" if completed else "journey-pending"
        icon = "✅" if completed else "⏳"
        st.markdown(
            f'<div class="journey-card {card_class}">'
            f'<div style="font-size:1.3rem">{icon}</div>'
            f'<div style="font-size:0.82rem;font-weight:600">{stage_name}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

st.markdown("")

# ============================================================
# STAGE 10 - FINAL HR DASHBOARD
# ============================================================

st.markdown("### 🧾 HR Decision-Support Overview")

if analysis_done:

    recommendation_match = re.search(
        r"Recommendation\s*:\s*(.+)",
        analysis_text,
        re.IGNORECASE
    )
    recommendation = (
        recommendation_match.group(1).strip()
        if recommendation_match
        else "See AI Candidate Analysis"
    )

    # Decision-support metrics
    d1, d2, d3 = st.columns(3)

    with d1:
        st.markdown(
            f'<div class="insight-card">'
            f'<b>🎯 AI Recommendation</b><br>'
            f'<span style="font-size:1.05rem">{escape(recommendation)}</span>'
            f'</div>',
            unsafe_allow_html=True
        )

    with d2:
        match_display = f"{overall_match}%" if overall_match is not None else "N/A"
        st.markdown(
            f'<div class="insight-card">'
            f'<b>📊 Overall Role Match</b><br>'
            f'<span style="font-size:1.5rem;font-weight:700">{match_display}</span>'
            f'</div>',
            unsafe_allow_html=True
        )

    with d3:
        st.markdown(
            f'<div class="insight-card">'
            f'<b>🧩 Development Focus</b><br>'
            f'<span class="small-muted">'
            f'{"Skill gaps identified" if skillgap_done else "Pending skill-gap analysis"}'
            f'</span></div>',
            unsafe_allow_html=True
        )

    st.markdown("#### 📋 Recommended HR Action Summary")

    action_items = []
    if analysis_done:
        action_items.append("Review AI screening and job-match insights.")
    if skillgap_done:
        action_items.append("Review high-priority skill gaps before finalizing development priorities.")
    if onboarding_done:
        action_items.append("Customize the 90-day onboarding plan with the reporting manager.")
    if learning_done:
        action_items.append("Assign or validate the recommended learning activities.")
    if progress_done:
        action_items.append("Review the latest development progress and manager feedback.")

    if action_items:
        for item in action_items:
            st.markdown(f"• {item}")

    st.info(
        "🛡️ Responsible AI: The dashboard is designed for HR decision support. "
        "It should use job-relevant information only, avoid protected characteristics, "
        "and keep final hiring and development decisions with qualified human professionals."
    )

else:
    st.info("Complete Candidate Analysis to activate the HR Dashboard.")

# ============================================================
# STAGE 11 - DOWNLOADABLE HR REPORT
# ============================================================

st.divider()

st.markdown("## 📄 Download HR Talent Report")

st.write(
    "Generate a consolidated PDF report containing the AI candidate "
    "analysis, onboarding plan, skill-gap analysis, learning plan "
    "and development progress review."
)


def create_hr_report():

    buffer = io.BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    title_style = styles["Title"]
    title_style.alignment = TA_CENTER

    heading_style = styles["Heading2"]
    body_style = styles["BodyText"]

    story = []

    # Report title
    story.append(
        Paragraph(
            "Hire2Develop AI - HR Talent Report",
            title_style
        )
    )

    story.append(Spacer(1, 15))

    story.append(
        Paragraph(
            f"<b>Candidate:</b> {escape(dashboard_candidate)}",
            body_style
        )
    )

    story.append(
        Paragraph(
            f"<b>Target Role:</b> {escape(dashboard_job)}",
            body_style
        )
    )

    story.append(Spacer(1, 20))


    # Candidate Analysis
    if "analysis" in st.session_state:

        story.append(
            Paragraph(
                "1. AI Candidate Analysis",
                heading_style
            )
        )

        analysis_text = st.session_state["analysis"]

        for line in analysis_text.split("\n"):

            clean_line = line.strip()

            if clean_line:

                story.append(
                    Paragraph(
                        escape(clean_line),
                        body_style
                    )
                )

                story.append(Spacer(1, 4))


    # Onboarding
    if "onboarding" in st.session_state:

        story.append(PageBreak())

        story.append(
            Paragraph(
                "2. Personalized Onboarding Plan",
                heading_style
            )
        )

        onboarding_text = st.session_state["onboarding"]

        for line in onboarding_text.split("\n"):

            clean_line = line.strip()

            if clean_line:

                story.append(
                    Paragraph(
                        escape(clean_line),
                        body_style
                    )
                )

                story.append(Spacer(1, 4))


    # Skill Gap
    if "skillgap" in st.session_state:

        story.append(PageBreak())

        story.append(
            Paragraph(
                "3. Skill-Gap Analysis",
                heading_style
            )
        )

        skillgap_text = st.session_state["skillgap"]

        for line in skillgap_text.split("\n"):

            clean_line = line.strip()

            if clean_line:

                story.append(
                    Paragraph(
                        escape(clean_line),
                        body_style
                    )
                )

                story.append(Spacer(1, 4))


    # Learning
    if "learning" in st.session_state:

        story.append(PageBreak())

        story.append(
            Paragraph(
                "4. Learning & Development Plan",
                heading_style
            )
        )

        learning_text = st.session_state["learning"]

        for line in learning_text.split("\n"):

            clean_line = line.strip()

            if clean_line:

                story.append(
                    Paragraph(
                        escape(clean_line),
                        body_style
                    )
                )

                story.append(Spacer(1, 4))


    # Progress
    if "progress_review" in st.session_state:

        story.append(PageBreak())

        story.append(
            Paragraph(
                "5. Development Progress Review",
                heading_style
            )
        )

        story.append(
            Paragraph(
                f"<b>Current Development Progress:</b> "
                f"{dashboard_progress}%",
                body_style
            )
        )

        story.append(Spacer(1, 10))

        progress_text = st.session_state["progress_review"]

        for line in progress_text.split("\n"):

            clean_line = line.strip()

            if clean_line:

                story.append(
                    Paragraph(
                        escape(clean_line),
                        body_style
                    )
                )

                story.append(Spacer(1, 4))


    # Human oversight
    story.append(PageBreak())

    story.append(
        Paragraph(
            "6. Human Oversight & Responsible AI",
            heading_style
        )
    )

    story.append(
        Paragraph(
            "AI is used as a decision-support tool for HR and Talent "
            "Development. Final hiring, onboarding and employee "
            "development decisions remain with qualified human "
            "HR professionals and managers.",
            body_style
        )
    )

    document.build(story)

    buffer.seek(0)

    return buffer


if analysis_done:

    try:

        pdf_file = create_hr_report()

        st.download_button(
            label="📥 Download Complete HR Report (PDF)",
            data=pdf_file,
            file_name="Hire2Develop_HR_Talent_Report.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    except Exception as e:

        st.error(
            f"Could not generate the HR report: {e}"
        )

else:

    st.info(
        "Complete Candidate Analysis first to enable the HR Report."
    )


# ============================================================
# SAVE / UPDATE CANDIDATE HISTORY
# ============================================================

st.divider()
st.markdown("## 💾 Save Candidate to History")

st.write(
    "Save this candidate's current HR journey to Supabase so it can be "
    "opened and continued later."
)

if supabase is None:
    st.warning("Supabase is not connected, so candidate history is unavailable.")
else:
    if st.button(
        "💾 Save Candidate to History",
        type="primary",
        use_container_width=True
    ):
        save_name = st.session_state.get("candidate_name", "").strip()
        save_position = st.session_state.get("position", "").strip()

        if not save_name:
            st.warning("Please enter the Candidate Name above.")
        elif not save_position:
            st.warning("Please enter the Position above.")
        elif not st.session_state.get("job_text"):
            st.warning(
                "Please analyze the candidate first so the Job Description is saved."
            )
        elif not st.session_state.get("resume_text"):
            st.warning(
                "Please analyze the candidate first so the Resume is saved."
            )
        else:
            candidate_data = {
                "candidate_name": save_name,
                "position": save_position,
                "job_description": st.session_state.get("job_text", ""),
                "resume_text": st.session_state.get("resume_text", ""),
                "interview_results": st.session_state.get("interview_results", ""),
                "candidate_analysis": st.session_state.get("analysis", ""),
                "onboarding_plan": st.session_state.get("onboarding", ""),
                "skill_gap_analysis": st.session_state.get("skillgap", ""),
                "learning_plan": st.session_state.get("learning", ""),
                "progress_review": st.session_state.get("progress_review", ""),
                "progress": int(
                    st.session_state.get("development_progress", 0)
                )
            }

            try:
                existing_id = st.session_state.get("candidate_id")

                if existing_id:
                    response = (
                        supabase
                        .table("candidates")
                        .update(candidate_data)
                        .eq("id", existing_id)
                        .execute()
                    )

                    if response.data:
                        st.success(
                            f"✅ {save_name}'s history was updated successfully."
                        )
                    else:
                        st.warning(
                            "No row was updated. The candidate may no longer exist "
                            "in Supabase."
                        )
                else:
                    response = (
                        supabase
                        .table("candidates")
                        .insert(candidate_data)
                        .execute()
                    )

                    if response.data:
                        st.session_state["candidate_id"] = response.data[0]["id"]
                        st.success(
                            f"✅ {save_name} was saved to candidate history successfully."
                        )
                    else:
                        st.error("The candidate could not be saved.")

            except Exception as e:
                st.error(f"❌ Could not save candidate history: {e}")
