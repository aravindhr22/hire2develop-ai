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
    height=180
)


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
