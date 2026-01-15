from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from backend.model import risk_model
import uvicorn
import os
from openai import OpenAI

# Initialize Replit AI (OpenAI compatible)
# The integration provides AI_INTEGRATIONS_OPENAI_API_KEY and AI_INTEGRATIONS_OPENAI_BASE_URL automatically
client = OpenAI(
    api_key=os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY"),
    base_url=os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")
)

app = FastAPI(title="Student Study Plan API")

class StudentData(BaseModel):
    attendance: float
    quiz_score: float
    assignment_score: float
    study_hours: float
    midterm_score: float

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    student_data: StudentData

class StudyPlanResponse(BaseModel):
    risk_score: float
    detailed_plan: str

@app.post("/generate-study-plan", response_model=StudyPlanResponse)
def generate_study_plan(request: ChatRequest):
    # 1. Calculate Risk
    try:
        data = request.student_data.dict()
        risk_score = risk_model.predict_risk(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

    # 2. Generate Detailed Plan using AI
    try:
        risk_level = "High Risk" if risk_score > 0.4 else "Low Risk/On Track"
        
        system_prompt = f"""You are an expert academic advisor. 
A student has the following metrics:
- Attendance: {data['attendance']*100}%
- Quiz Score: {data['quiz_score']}/10
- Assignment Score: {data['assignment_score']}/10
- Study Hours: {data['study_hours']} hrs/day
- Midterm Score: {data['midterm_score']}/100
- Calculated Risk Level: {risk_level} (Risk Score: {risk_score:.2f})

Generate a highly detailed, personalized daily study plan. 
Include specific time slots, study techniques (like Pomodoro or Active Recall), and actionable advice to improve their weak areas.
Format the output in clean Markdown.
"""
        
        # Combine system prompt with user messages for context if any
        messages = [{"role": "system", "content": system_prompt}]
        for msg in request.messages:
            messages.append({"role": msg.role, "content": msg.content})

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.7
        )
        
        detailed_plan = response.choices[0].message.content
        
    except Exception as e:
        detailed_plan = f"Error generating detailed plan: {str(e)}. Please try again later."

    return {
        "risk_score": round(risk_score, 2),
        "detailed_plan": detailed_plan
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
