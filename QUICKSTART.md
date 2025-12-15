# Quick Start Guide: AI Queue Insights

## 🚀 Getting Started (5 Minutes)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: (Optional) Configure OpenAI
Create or update `.env`:
```bash
# Optional - Feature works without this!
OPENAI_API_KEY=sk-your-key-here
```

### Step 3: Start the Application
```bash
# Using Docker (recommended)
docker-compose up

# OR using uvicorn
uvicorn app.main:app --reload
```

### Step 4: Use the Feature
1. Go to http://localhost:8000
2. Register or login
3. Click **"AI Queue Insights"** in the navigation menu
4. Click **"+ New Observation"**
5. Fill in the form with sample data:
   ```
   Department: Emergency Room
   Observed At: [select current date/time]
   Number of Patients: 15
   Average Wait Time: 45
   Notes: Busy afternoon shift
   ```
6. Click **"Save Observation"**
7. Repeat steps 4-6 to add 2-3 more observations (vary the department and wait times)
8. Click **"Generate Insights"**
9. View your AI-powered or rule-based insight!

---

## 📊 Sample Test Data

### Scenario 1: High ER Wait Times
```
Observation 1:
  Department: Emergency Room
  Patients: 20
  Wait Time: 75 minutes
  Notes: Post-lunch rush

Observation 2:
  Department: Emergency Room
  Patients: 18
  Wait Time: 68 minutes
  Notes: Still backed up

Observation 3:
  Department: Radiology
  Patients: 5
  Wait Time: 15 minutes
  Notes: Normal operations
```

**Expected Insight**: Should identify ER as a bottleneck and recommend staffing adjustments.

### Scenario 2: Multiple Bottlenecks
```
Observation 1:
  Department: Check-in
  Patients: 25
  Wait Time: 40 minutes

Observation 2:
  Department: Radiology
  Patients: 12
  Wait Time: 65 minutes

Observation 3:
  Department: Emergency Room
  Patients: 15
  Wait Time: 55 minutes
```

**Expected Insight**: Should identify multiple departments with elevated wait times.

---

## 🧪 Testing Both Modes

### Test AI Mode (with OpenAI)
1. Set `OPENAI_API_KEY` in `.env`
2. Restart application
3. Generate insights
4. Look for "AI-Generated" badge
5. Insight should be natural language, conversational

### Test Rule-Based Mode (without OpenAI)
1. Remove or comment out `OPENAI_API_KEY` in `.env`
2. Restart application
3. Generate insights
4. Look for "Rule-Based" badge
5. Insight should be structured with markdown formatting
6. Should include note: "This analysis uses rule-based heuristics..."

---

## 🔍 What to Verify

### ✅ User Scoping
- [ ] Create observations as User A
- [ ] Logout and login as User B
- [ ] User B should NOT see User A's observations
- [ ] Each user has separate insights

### ✅ Validation
- [ ] Try negative patient count → Should show error
- [ ] Try empty department → Should show error
- [ ] Try future date → Should work (observations can be backdated or current)

### ✅ Navigation
- [ ] "AI Queue Insights" link appears only when logged in
- [ ] Clicking brand logo goes to dashboard when logged in
- [ ] Navigation menu has both "Calculator" and "AI Queue Insights"

### ✅ Dashboard Features
- [ ] Recent observations shown in table
- [ ] Wait times color-coded (green < 30, yellow < 60, red ≥ 60)
- [ ] Latest insight displayed at top
- [ ] "Generate Insights" button only appears if observations exist

---

## 📝 Key Files Modified/Added

### New Files
```
app/models/queue_observation.py       # Database models
app/schemas/queue_observation.py      # Pydantic schemas
app/services/queue_insights.py        # AI service with fallback
app/routers/queue_insights.py         # Route handlers
templates/queue_list.html             # Dashboard
templates/queue_form.html             # Observation form
AI_QUEUE_INSIGHTS.md                  # Full documentation
```

### Modified Files
```
app/models/user.py                    # Added relationships
app/core/config.py                    # Added OpenAI settings
app/main.py                           # Registered router
templates/layout.html                 # Added navigation
requirements.txt                      # Added openai package
```

---

## 🎯 Expected Behavior

### With OpenAI API Key
```
User adds 5 observations → Clicks "Generate Insights"
→ OpenAI API called with structured prompt
→ Natural language insight generated
→ Stored with is_ai_generated=True, model_used="gpt-4o-mini"
→ Displayed with "AI-Generated" badge
```

### Without OpenAI API Key
```
User adds 5 observations → Clicks "Generate Insights"
→ Rule-based analysis runs
→ Statistical aggregation by department
→ Deterministic insight generated
→ Stored with is_ai_generated=False, model_used="rule-based"
→ Displayed with "Rule-Based" badge
```

---

## 🐛 Quick Troubleshooting

**Problem**: Navigation menu not showing  
**Fix**: Clear browser localStorage and re-login

**Problem**: OpenAI errors  
**Fix**: Check API key is valid, or let it fall back to rule-based

**Problem**: No observations showing  
**Fix**: Ensure you're logged in as the user who created them

**Problem**: Database errors  
**Fix**: Restart with `docker-compose down -v && docker-compose up`

---

## 💡 Pro Tips

1. **Add observations with different timestamps** to see time-based analysis
2. **Vary wait times significantly** to trigger bottleneck detection
3. **Use different department names** to see comparative analysis
4. **Add notes to observations** - they're included in AI prompts
5. **Generate insights multiple times** to see different analyses

---

## 📚 Next Steps

- Read the full documentation: `AI_QUEUE_INSIGHTS.md`
- Review the code comments in each file
- Experiment with the API endpoints (`/queue-insights/api/*`)
- Try modifying the rule-based heuristics in `app/services/queue_insights.py`
- Customize the AI prompt for different types of insights

---

**Questions?** Check the main documentation or examine the inline code comments!
