from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
from emergentintegrations.llm.chat import LlmChat, UserMessage
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Demo scenarios data - 60 scenarios from the document
DEMO_SCENARIOS = [
    {"id": 1, "category": "Pricing & Commission Objections", "objection": "Your commission is too high.", "context": "The merchant is comparing your fee structure to a competitor or their current margins.", "suggested_response": "Reframe as an investment, not a cost. Show value vs. price."},
    {"id": 2, "category": "Pricing & Commission Objections", "objection": "Bahut mehenga hai, itna budget nahi hai mera.", "context": "A small business owner is concerned about upfront costs or monthly fees.", "suggested_response": "Offer a trial period, a smaller starter package, or break down the cost per day/week."},
    {"id": 3, "category": "Pricing & Commission Objections", "objection": "Is there any discount? Can you give me a better price?", "context": "The merchant is trying to negotiate for a lower rate.", "suggested_response": "Explain the value included. Hold firm but offer a non-monetary value-add (e.g., extra support)."},
    {"id": 4, "category": "Pricing & Commission Objections", "objection": "The other company is offering a 5% lower commission.", "context": "Direct comparison with a known competitor's pricing.", "suggested_response": "Differentiate on features, service, and reliability, not just price. \"Cheaper isn't always better.\""},
    {"id": 5, "category": "Pricing & Commission Objections", "objection": "Are there any hidden charges I should know about?", "context": "The merchant is skeptical about the pricing transparency.", "suggested_response": "Be upfront. Show a clear pricing table. Build trust by highlighting what's included."},
    {"id": 6, "category": "Pricing & Commission Objections", "objection": "Itna paisa lagane ke baad, sales nahi badhi toh?", "context": "The merchant is worried about the return on their investment.", "suggested_response": "Share case studies, testimonials, or offer a performance-based incentive if possible."},
    {"id": 7, "category": "Pricing & Commission Objections", "objection": "GST include karke final price batao.", "context": "The merchant wants the all-inclusive final cost to avoid surprises.", "suggested_response": "Provide a clear, final quote immediately to demonstrate transparency."},
    {"id": 8, "category": "Pricing & Commission Objections", "objection": "Payment terms flexible hain? Can I pay in installments?", "context": "A merchant with cash flow concerns is asking for flexible payment options.", "suggested_response": "Explain the available payment plans. Show empathy for their cash flow needs."},
    {"id": 9, "category": "Competition & Loyalty Objections", "objection": "I'm already working with [Competitor Name] and I'm happy.", "context": "The merchant is satisfied with their current provider and sees no reason to switch.", "suggested_response": "Acknowledge and respect the relationship. Ask \"What if we could improve X by 10%?\" Spark curiosity."},
    {"id": 10, "category": "Competition & Loyalty Objections", "objection": "Mera purana vendor hai, usse aacha relation hai.", "context": "The objection is based on a long-standing personal relationship, not business logic.", "suggested_response": "Don't attack the relationship. Suggest a small, parallel trial. \"No need to switch, just try us.\""},
    {"id": 11, "category": "Competition & Loyalty Objections", "objection": "Everyone in the market uses their platform, why should I use yours?", "context": "The competitor has a dominant market share.", "suggested_response": "Focus on your unique selling proposition (USP). Highlight your niche, better service, or specific feature."},
    {"id": 12, "category": "Competition & Loyalty Objections", "objection": "I tried a similar service before and it didn't work for me.", "context": "The merchant had a bad experience with a different provider in the same category.", "suggested_response": "Differentiate your service clearly. \"I understand, here's how we are different and avoid that problem...\""},
    {"id": 13, "category": "Competition & Loyalty Objections", "objection": "Suna hai [Competitor Name] ka customer support bahut accha hai.", "context": "The merchant is comparing perceived service quality.", "suggested_response": "Showcase your support strength. Provide testimonials, mention dedicated account managers, or SLAs."},
    {"id": 14, "category": "Competition & Loyalty Objections", "objection": "Just leave your brochure, I'll compare and get back to you.", "context": "A polite way of dismissing the salesperson to compare with others later.", "suggested_response": "Secure a follow-up meeting. \"Of course, can we schedule 10 minutes next Tuesday to review it together?\""},
    {"id": 15, "category": "Competition & Loyalty Objections", "objection": "They are a big, well-known brand. Are you new?", "context": "The merchant trusts established brands more than a newer company.", "suggested_response": "Highlight your agility, modern tech, and personalized service. Frame \"new\" as \"more advanced\"."},
    {"id": 16, "category": "Trust & Reliability Objections", "objection": "How can I trust that your system won't fail during peak hours?", "context": "The merchant is concerned about technical reliability and potential business loss.", "suggested_response": "Discuss uptime statistics, server infrastructure, and fail-safes. Offer a Service Level Agreement (SLA)."},
    {"id": 17, "category": "Trust & Reliability Objections", "objection": "Aapki company kab tak tikegi? What if you shut down?", "context": "A startup or new company facing skepticism about its long-term stability.", "suggested_response": "Talk about your funding, vision, and the team's experience. Show long-term commitment."},
    {"id": 18, "category": "Trust & Reliability Objections", "objection": "I need to see a live demo with my own products.", "context": "The merchant wants proof that the system works as promised, not just a generic presentation.", "suggested_response": "\"Great idea.\" Be prepared to offer a customized or sandboxed demo."},
    {"id": 19, "category": "Trust & Reliability Objections", "objection": "Do you have any clients in my area? Can I speak to them?", "context": "The merchant is looking for social proof and local references.", "suggested_response": "\"Absolutely.\" Provide references of happy, non-competing clients."},
    {"id": 20, "category": "Trust & Reliability Objections", "objection": "Your marketing promises sound too good to be true.", "context": "The merchant is cynical about the marketing claims being made.", "suggested_response": "Back up every claim with data, a case study, or a logical explanation. Tone down the hype."},
    {"id": 21, "category": "Trust & Reliability Objections", "objection": "Mera data safe rahega? What about data security?", "context": "A critical concern for any business adopting a digital platform.", "suggested_response": "Explain your security protocols, data encryption, and privacy policies in simple terms."},
    {"id": 22, "category": "Trust & Reliability Objections", "objection": "Pehle bhi log aaye the, promise karke service nahi di.", "context": "The merchant is jaded from past negative experiences with other salespeople.", "suggested_response": "Acknowledge their frustration. Differentiate with a clear, documented onboarding and support plan."},
    {"id": 23, "category": "Value & ROI Objections", "objection": "I don't think I'll get enough return on this investment.", "context": "The merchant is unable to see the tangible financial benefits.", "suggested_response": "Use an ROI calculator. Show a clear, conservative projection of increased revenue or cost savings."},
    {"id": 24, "category": "Value & ROI Objections", "objection": "My business is very small, I don't need all these features.", "context": "The merchant feels the product is too complex or powerful for their needs.", "suggested_response": "Focus on the 1-2 key features that will have the biggest impact on their specific business."},
    {"id": 25, "category": "Value & ROI Objections", "objection": "Isse mera fayda kya hoga, seedhe seedhe batao.", "context": "The merchant wants a no-nonsense, bottom-line value proposition.", "suggested_response": "Give a clear, concise \"what's in it for you\" statement. \"You get more customers and save 5 hours a week.\""},
    {"id": 26, "category": "Value & ROI Objections", "objection": "We are doing fine without it, why do we need this?", "context": "The business is profitable and the merchant doesn't feel any urgent pain point.", "suggested_response": "Introduce the concept of \"opportunity cost.\" \"You're doing well, but you could be doing great.\""},
    {"id": 27, "category": "Value & ROI Objections", "objection": "This seems like a 'nice to have', not a 'must have'.", "context": "The merchant doesn't see the product as essential for their operations.", "suggested_response": "Connect your product to a core business goal (e.g., \"This isn't about fancy tech, it's about reducing customer wait times\")."},
    {"id": 28, "category": "Value & ROI Objections", "objection": "Free mein jo mil raha hai, uske liye main pay kyun karoon?", "context": "The merchant is comparing your paid service with a free alternative.", "suggested_response": "Clearly articulate the limitations of the free tool and the premium benefits of yours (support, features, reliability)."},
    {"id": 29, "category": "Value & ROI Objections", "objection": "How long will it take to see results?", "context": "The merchant is concerned about the time it takes to realize the value.", "suggested_response": "Set realistic expectations. Provide a typical timeline based on other clients. \"Usually, clients see X in 30-60 days.\""},
    {"id": 30, "category": "Procrastination & Time-Related Objections", "objection": "I don't have time for this right now.", "context": "A very common brush-off when the merchant is busy.", "suggested_response": "Respect their time. \"I understand. What's a better time in the next 2 days for a 15-min call?\""},
    {"id": 31, "category": "Procrastination & Time-Related Objections", "objection": "Send me an email with the details.", "context": "Often a polite way to end the conversation without committing.", "suggested_response": "\"I will, right away. Can we also book a 10-min slot for tomorrow to discuss any questions you might have?\""},
    {"id": 32, "category": "Procrastination & Time-Related Objections", "objection": "I need to discuss this with my partner/manager.", "context": "The decision-maker is not in the room or is deferring the decision.", "suggested_response": "\"That makes sense. When are you meeting with them? I can provide a summary sheet to help your discussion.\""},
    {"id": 33, "category": "Procrastination & Time-Related Objections", "objection": "Abhi season ka time hai, baad mein dekhte hain.", "context": "The merchant is too overwhelmed with current business to consider new things.", "suggested_response": "Frame it as a way to manage the peak season better. \"This could actually help you handle the rush more efficiently.\""},
    {"id": 34, "category": "Procrastination & Time-Related Objections", "objection": "Call me back next quarter.", "context": "The merchant is pushing the decision far into the future.", "suggested_response": "Create a sense of urgency. Mention a limited-time offer or a new feature release."},
    {"id": 35, "category": "Procrastination & Time-Related Objections", "objection": "We are planning a renovation, so we'll decide after that.", "context": "The merchant has other major projects taking priority.", "suggested_response": "Acknowledge their priority. Ask for permission to follow up on a specific date post-renovation."},
    {"id": 36, "category": "Procrastination & Time-Related Objections", "objection": "Let me think about it.", "context": "A vague stall that often means \"no.\"", "suggested_response": "Try to uncover the real objection. \"When people say that, they usually have a concern about either price or implementation. Which one is it for you?\""},
    {"id": 37, "category": "Technical & Implementation Objections", "objection": "This seems too complicated. My staff won't be able to use it.", "context": "The merchant is worried about the learning curve for their non-technical employees.", "suggested_response": "Emphasize ease of use. \"It's as simple as using WhatsApp.\" Offer free, on-site training."},
    {"id": 38, "category": "Technical & Implementation Objections", "objection": "Mere paas iske liye proper computer/internet nahi hai.", "context": "The merchant lacks the necessary infrastructure.", "suggested_response": "Clarify the minimum requirements. Suggest lightweight/mobile-first versions if available."},
    {"id": 39, "category": "Technical & Implementation Objections", "objection": "How long will the setup and installation take?", "context": "The merchant is concerned about business disruption during the implementation phase.", "suggested_response": "Provide a clear, step-by-step timeline. \"The setup is less than 30 minutes and can be done after hours.\""},
    {"id": 40, "category": "Technical & Implementation Objections", "objection": "Will this integrate with my existing billing software?", "context": "The merchant wants to ensure the new system works with their current tools.", "suggested_response": "Be honest about integration capabilities. Highlight existing integrations or API options."},
    {"id": 41, "category": "Technical & Implementation Objections", "objection": "After-sales service kon dega? Who will provide support if something goes wrong?", "context": "The merchant is worried about getting help after the initial purchase.", "suggested_response": "Explain your support channels (phone, chat, ticket), hours of operation, and typical response times."},
    {"id": 42, "category": "Technical & Implementation Objections", "objection": "Mujhe technology samajh nahi aati.", "context": "The merchant is intimidated by the technical aspect of the product.", "suggested_response": "Reassure them. Use analogies. \"Don't worry, we handle all the technical parts. You just focus on your business.\""},
    {"id": 43, "category": "Technical & Implementation Objections", "objection": "Yeh mobile pe aache se chalega?", "context": "The merchant primarily operates their business using a smartphone.", "suggested_response": "Showcase the mobile app or responsive mobile website. Confirm its full functionality."},
    {"id": 44, "category": "Technical & Implementation Objections", "objection": "Software update ka kya? Will there be extra charges?", "context": "The merchant is concerned about future costs for maintenance and updates.", "suggested_response": "Clarify that updates are included in the subscription/price. Frame it as a benefit."},
    {"id": 45, "category": "Need & Relevance Objections", "objection": "My business is different, this won't work for me.", "context": "The merchant believes their business is too unique for a standardized solution.", "suggested_response": "Use case studies from similar, niche businesses. \"We work with another bakery just like yours, and they saw...\""},
    {"id": 46, "category": "Need & Relevance Objections", "objection": "Mere customers online nahi hain.", "context": "A traditional business owner who doesn't believe their clientele is digitally savvy.", "suggested_response": "Share local stats on internet and smartphone usage. Even if they aren't online, you can improve efficiency."},
    {"id": 47, "category": "Need & Relevance Objections", "objection": "I don't have a problem with my current process.", "context": "The merchant is unaware of the inefficiencies in their existing workflow.", "suggested_response": "Ask discovery questions to uncover hidden pain points. \"How much time do you spend on manual inventory checks?\""},
    {"id": 48, "category": "Need & Relevance Objections", "objection": "This is only for big restaurants/shops, not for my small cafe.", "context": "The merchant perceives the product as an enterprise solution.", "suggested_response": "Highlight features specifically for small businesses. Offer a SMB-specific pricing tier."},
    {"id": 49, "category": "Need & Relevance Objections", "objection": "We get most of our business from word-of-mouth.", "context": "The merchant relies on traditional marketing and doesn't see the need for a new platform.", "suggested_response": "Frame your tool as a way to amplify word-of-mouth and manage their reputation online."},
    {"id": 50, "category": "Need & Relevance Objections", "objection": "Is this just another app that I have to manage?", "context": "The merchant is feeling overwhelmed by \"app fatigue.\"", "suggested_response": "Position it as a tool that consolidates or simplifies tasks, reducing the need for other apps."},
    {"id": 51, "category": "Need & Relevance Objections", "objection": "Mera walk-in customer base aacha hai, I don't need more.", "context": "The merchant is content with their current footfall and lacks ambition to grow.", "suggested_response": "Talk about future-proofing the business and creating a more resilient revenue stream."},
    {"id": 52, "category": "Need & Relevance Objections", "objection": "What is the point of this? Main jaise kar raha hoon theek hai.", "context": "A fundamental lack of understanding of the product's core purpose.", "suggested_response": "Go back to basics. Use a simple analogy to explain the core problem you solve."},
    {"id": 53, "category": "Miscellaneous & Specific Scenarios", "objection": "The decision is up to my son, he handles all the tech.", "context": "The salesperson is talking to a non-decision-maker.", "suggested_response": "\"Great, when can the three of us connect for a brief call? I'd love to show him the demo.\""},
    {"id": 54, "category": "Miscellaneous & Specific Scenarios", "objection": "I'll do it, but only if you give me exclusivity in my area.", "context": "The merchant is asking for a special deal that may not be feasible.", "suggested_response": "Explain the business model and why exclusivity isn't possible, but offer other forms of partnership."},
    {"id": 55, "category": "Miscellaneous & Specific Scenarios", "objection": "I read a bad review about your company online.", "context": "The merchant has seen negative feedback and is concerned.", "suggested_response": "Acknowledge it, don't be defensive. \"Thank you for bringing that up. It was an issue we have since resolved by doing X.\""},
    {"id": 56, "category": "Miscellaneous & Specific Scenarios", "objection": "Your salesperson last year promised me something you didn't deliver.", "context": "A past negative experience with your own company.", "suggested_response": "Apologize sincerely. Rebuild trust. Explain what has changed in the company since then."},
    {"id": 57, "category": "Miscellaneous & Specific Scenarios", "objection": "Sab kuch theek hai, par I need it in Gujarati/Kannada/Tamil.", "context": "A specific language requirement that may or may not be supported.", "suggested_response": "Be clear about your current language support and your roadmap for adding new languages."},
    {"id": 58, "category": "Miscellaneous & Specific Scenarios", "objection": "The contract is too long, I don't want to be locked in.", "context": "The merchant is hesitant to commit to a long-term agreement.", "suggested_response": "Offer a quarterly or semi-annual plan, even if it's at a slightly higher price point."},
    {"id": 59, "category": "Miscellaneous & Specific Scenarios", "objection": "Okay, let's start with a free trial.", "context": "The merchant wants to try before buying, which may or may not be your standard policy.", "suggested_response": "If you offer trials, agree immediately. If not, explain why and offer a detailed, live demo instead."},
    {"id": 60, "category": "Miscellaneous & Specific Scenarios", "objection": "The person who came before you was very pushy.", "context": "The merchant is reacting to a previous salesperson's aggressive style.", "suggested_response": "Set a collaborative tone. \"I'm not here to push you. My goal is just to see if there's a fit. If not, that's okay.\""}
]

# Define Models
class Scenario(BaseModel):
    id: int
    category: str
    objection: str
    context: str
    suggested_response: str

class ObjectionRequest(BaseModel):
    objection_text: str
    language: Optional[str] = "English"
    scenario_id: Optional[int] = None

class PracticeResponse(BaseModel):
    scenario_id: int
    user_response: str
    response_type: str  # "voice" or "text"

class AIResponse(BaseModel):
    response: str
    scenario_used: Optional[Scenario] = None

class PracticeFeedback(BaseModel):
    feedback: str
    score: Optional[int] = None
    suggestions: List[str] = []

# Routes
@api_router.get("/")
async def root():
    return {"message": "Sales Training Assistant API"}

@api_router.get("/scenarios", response_model=List[Scenario])
async def get_all_scenarios():
    """Get all 60 demo scenarios"""
    return [Scenario(**scenario) for scenario in DEMO_SCENARIOS]

@api_router.get("/scenarios/categories")
async def get_scenario_categories():
    """Get unique categories of scenarios"""
    categories = list(set([scenario["category"] for scenario in DEMO_SCENARIOS]))
    return {"categories": categories}

@api_router.get("/scenarios/practice")
async def get_practice_scenarios():
    """Get 10 random scenarios for practice mode"""
    import random
    practice_scenarios = random.sample(DEMO_SCENARIOS, 10)
    return [Scenario(**scenario) for scenario in practice_scenarios]

@api_router.post("/objection/handle", response_model=AIResponse)
async def handle_objection(request: ObjectionRequest):
    """Handle merchant objection and provide AI-generated response"""
    try:
        # Find matching scenario if scenario_id provided
        scenario_used = None
        if request.scenario_id:
            scenario_used = next((s for s in DEMO_SCENARIOS if s["id"] == request.scenario_id), None)
        
        # Create language-specific system message
        language_instruction = ""
        if request.language in ["Hindi", "Hinglish"]:
            language_instruction = "Respond in Hindi/Hinglish mixing as appropriate for the input language."
        elif request.language in ["Marathi", "Kannada", "Tamil", "Telugu", "Bangla"]:
            language_instruction = f"Respond in {request.language} language to match the input."
        else:
            language_instruction = "Respond in English."
        
        # Initialize Gemini chat with concise system message
        chat = LlmChat(
            api_key=os.environ.get('GEMINI_API_KEY'),
            session_id=f"objection_{uuid.uuid4()}",
            system_message=f"""You are a sales coach providing quick, actionable responses to sales objections.

            RESPONSE FORMAT REQUIREMENTS:
            1. Keep responses under 200 words
            2. Be direct and practical
            3. Provide 2-3 specific phrases the agent can use
            4. {language_instruction}
            5. Use simple, clear language
            
            Structure your response as:
            **Quick Strategy:** [1-2 sentences]
            **What to Say:** [2-3 specific phrases]
            **Why This Works:** [1 sentence explanation]"""
        ).with_model("gemini", "gemini-2.5-pro")
        
        # Create concise prompt for AI
        prompt = f"""Handle this objection: "{request.objection_text}"
        
        Context: {scenario_used["context"] if scenario_used else "General sales objection"}
        
        Give a brief, practical response strategy."""
        
        user_message = UserMessage(text=prompt)
        ai_response = await chat.send_message(user_message)
        
        return AIResponse(
            response=ai_response,
            scenario_used=Scenario(**scenario_used) if scenario_used else None
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating AI response: {str(e)}")

@api_router.post("/practice/feedback", response_model=PracticeFeedback)
async def get_practice_feedback(response: PracticeResponse):
    """Provide AI feedback on practice response"""
    try:
        # Find the scenario
        scenario = next((s for s in DEMO_SCENARIOS if s["id"] == response.scenario_id), None)
        if not scenario:
            raise HTTPException(status_code=404, detail="Scenario not found")
        
        # Initialize Gemini chat with concise feedback system
        chat = LlmChat(
            api_key=os.environ.get('GEMINI_API_KEY'),
            session_id=f"practice_{uuid.uuid4()}",
            system_message="""You are a sales trainer providing concise feedback on practice responses.

            FEEDBACK FORMAT:
            1. Keep feedback under 150 words
            2. Be encouraging but honest
            3. Provide specific, actionable suggestions
            4. Rate responses 1-10 based on effectiveness
            
            Structure:
            **Score:** [X/10]
            **What worked:** [1-2 strengths]
            **Improve:** [2-3 specific suggestions]"""
        ).with_model("gemini", "gemini-2.5-pro")
        
        prompt = f"""Objection: "{scenario["objection"]}"
        Context: {scenario["context"]}
        Expected approach: {scenario["suggested_response"]}
        
        Agent's response: "{response.user_response}"
        
        Provide brief, actionable feedback with a score 1-10."""
        
        user_message = UserMessage(text=prompt)
        ai_response = await chat.send_message(user_message)
        
        # Parse the AI response more reliably
        lines = ai_response.strip().split('\n')
        feedback_text = ""
        score = 7  # default score
        suggestions = []
        
        # Extract score if present
        for line in lines:
            if "score:" in line.lower() or "/10" in line:
                try:
                    import re
                    score_match = re.search(r'(\d+)(?:/10)?', line)
                    if score_match:
                        score = int(score_match.group(1))
                        score = min(10, max(1, score))  # Ensure score is 1-10
                except:
                    score = 7
                break
        
        # Use full response as feedback if parsing fails
        feedback_text = ai_response
        
        # Extract suggestions if present
        in_suggestions = False
        for line in lines:
            line = line.strip()
            if "improve:" in line.lower() or "suggestions:" in line.lower():
                in_suggestions = True
                continue
            if in_suggestions and line.startswith(("-", "•", "1.", "2.", "3.")):
                suggestions.append(line.lstrip("-•123456789. "))
        
        return PracticeFeedback(
            feedback=feedback_text,
            score=score,
            suggestions=suggestions[:3]  # Limit to 3 suggestions
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating feedback: {str(e)}")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()