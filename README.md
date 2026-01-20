# ATS Resume Optimizer

A Multi-Agent AI System for optimizing resumes to improve ATS (Applicant Tracking System) compatibility.

## Features

- **Multi-Agent Architecture**: Three specialized AI agents work together:
  - **ATS Evaluation Agent**: Analyzes job descriptions and scores resume alignment
  - **Resume Handling Agent**: Optimizes resume content while preserving accuracy
  - **Master Agent**: Reviews and approves changes, ensuring no fabrication

- **Weighted ATS Scoring**: Uses a practical rubric:
  - Keyword Match (35%)
  - Skills Alignment (25%)
  - Experience Relevance (20%)
  - Formatting (10%)
  - Completeness (10%)

- **Local Storage**: All data stays on your machine:
  - Baseline resume storage
  - Skills list management
  - Job history with versioned results

- **Streamlit UI**: Simple, clean interface for:
  - Pasting job descriptions and resumes
  - Managing skills
  - Running quick ATS scores
  - Full optimization with review cycles

## Quick Start

### 1. Install Dependencies

```bash
cd web_extension/server
pip install -r requirements.txt
```

### 2. Set Up Environment

```bash
# Copy the example env file
cp .env.example .env

# Edit .env and add your OpenRouter API key
# Get a key at: https://openrouter.ai/keys
```

### 3. Run the Application

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## Usage

### Quick ATS Score

1. Paste a job description in the left panel
2. Paste your resume in the right panel
3. Click "Calculate Quick Score"
4. View your score and missing keywords

### Full Optimization

1. Enter job description and resume
2. Optionally add skills you have (that may not be in your resume)
3. Choose optimization mode:
   - **Conservative**: Minimal changes, only critical keywords
   - **Balanced**: Moderate optimization (recommended)
   - **Aggressive**: Maximum keyword alignment
4. Click "Optimize Resume"
5. Review the optimized result
6. Download the optimized resume

### Managing Your Data

- **Save as Baseline**: Save your current resume as the baseline for future optimizations
- **Skills**: Add skills you have that aren't explicitly in your resume
- **Job History**: Access previous optimizations from the sidebar

## Project Structure

```
web_extension/
├── server/
│   ├── agents/
│   │   ├── base.py              # Base agent class
│   │   ├── ats_evaluation_agent.py
│   │   ├── resume_handling_agent.py
│   │   └── master_agent.py
│   ├── config/
│   │   ├── settings.py          # Application settings
│   │   └── llm_factory.py       # LLM initialization
│   ├── services/
│   │   ├── ats_scorer.py        # Weighted ATS scoring
│   │   └── resume_parser.py     # Resume parsing
│   ├── storage/
│   │   └── local_storage.py     # Local data management
│   ├── tools/
│   │   ├── ats_tools.py         # ATS analysis tools
│   │   └── resume_tools.py      # Resume handling tools
│   ├── app.py                   # Streamlit UI
│   ├── orchestrator.py          # Multi-agent orchestration
│   └── requirements.txt
├── data/                        # Local data storage
│   ├── baseline/                # Your baseline resume
│   └── jobs/                    # Job-specific results
└── README.md
```

## How It Works

### Optimization Flow

1. **ATS Evaluation Agent** analyzes the job description:
   - Extracts requirements and keywords
   - Calculates baseline ATS score
   - Identifies keyword gaps

2. **Resume Handling Agent** optimizes the resume:
   - Rewrites sections to incorporate keywords naturally
   - Maintains factual accuracy
   - Follows ATS-friendly formatting

3. **Master Agent** reviews the optimization:
   - Validates no fabrication occurred
   - Checks quality criteria
   - Approves or requests revisions

4. If not approved, the cycle repeats (up to max iterations)

### Safety Rules

The system enforces strict rules to maintain resume integrity:

- **No fabrication**: Never invents experience, skills, or achievements
- **No false claims**: Never adds quantifiable claims (percentages, dollar amounts)
- **Preserve facts**: Never changes job titles, companies, or dates
- **Natural language**: Incorporates keywords naturally, no stuffing

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENROUTER_API_KEY` | Your OpenRouter API key | Required |
| `DEFAULT_MODEL` | LLM model to use | `google/gemini-2.0-flash-exp:free` |

### Settings (in UI)

- **Optimization Mode**: conservative / balanced / aggressive
- **Max Iterations**: 1-5 review cycles

## Troubleshooting

### "OPENROUTER_API_KEY not found"

Make sure you've created a `.env` file with your API key:

```bash
OPENROUTER_API_KEY=your_key_here
```

### "Failed to initialize agents"

1. Check your API key is valid
2. Ensure you have internet connectivity
3. Check the OpenRouter service status

### Slow optimization

- The free model tier may have rate limits
- Try reducing max iterations
- Consider using a paid model for faster responses

## Future Enhancements

- [ ] Browser extension for automatic JD extraction
- [ ] DOCX/PDF export
- [ ] Multiple resume templates
- [ ] Batch optimization for multiple jobs
- [ ] Resume comparison view

## License

MIT License - See LICENSE file for details.
