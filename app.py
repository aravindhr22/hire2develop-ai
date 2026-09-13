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

            # Extract the uploaded documents again
            onboarding_job_text = extract_text(job_description)
            onboarding_resume_text = extract_text(resume)

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

            # Extract the uploaded documents again
            skillgap_job_text = extract_text(job_description)
            skillgap_resume_text = extract_text(resume)

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
        value=25,
        step=5
    )

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
