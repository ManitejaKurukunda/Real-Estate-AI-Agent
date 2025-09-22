from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import sys
import traceback
import pandas as pd
from datetime import datetime
import base64

# Fix imports by adding parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Import download utilities
try:
    from src.utils.download_utils import DownloadUtilities
    download_utils_available = True
except ImportError:
    print("Warning: Download utilities not available")
    download_utils_available = False

# Import email utilities
try:
    from src.utils.email_utils import EmailUtilities
    email_sender = EmailUtilities(
        sender_email="test@gmail.com",
        sender_password="xxxxxxxxxxx"
    )
    email_utils_available = True
except ImportError:
    print("Warning: Email utilities not available")
    email_utils_available = False
    email_sender = None

print(f"Project root: {parent_dir}")
print(f"Current directory: {current_dir}")

# Initialize FastAPI app
app = FastAPI(title="Real Estate AI API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
chat_agent = None
agent_error = None

# Store last query results for download
last_query_results = {
    "data": None,
    "question": "",
    "sql_query": "",
    "insights": "",
    "timestamp": None
}

# Initialize chat agent
def initialize_chat_agent():
    global chat_agent, agent_error
    try:
        print("🤖 Loading enhanced chat agent...")
        
        from config.openai_config import get_openai_api_key
        api_key = get_openai_api_key()
        print("✅ OpenAI API key loaded")
        
        from src.agents.portfolio_chat_agent import PortfolioChatAgent
        chat_agent = PortfolioChatAgent(api_key)
        print("✅ Enhanced chat agent initialized successfully")
        return True
        
    except Exception as e:
        agent_error = str(e)
        print(f"❌ Chat agent error: {agent_error}")
        traceback.print_exc()
        return False

# Initialize on startup
initialize_chat_agent()

# Request/Response models
class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    success: bool
    question: str = None
    sql_query: str = None
    data: list = None
    insights: str = None
    row_count: int = None
    error: str = None
    conversation_type: str = None

class EmailRequest(BaseModel):
    recipient_email: str
    subject: str
    message: str
    attachment_format: str = "pdf"

@app.get("/", response_class=HTMLResponse)
async def get_chat_interface():
    """Serve the enhanced chat interface from HTML file"""
    try:
        html_path = os.path.join(current_dir, 'templates', 'chat_interface.html')
        with open(html_path, 'r', encoding='utf-8') as file:
            html_content = file.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Error: chat_interface.html not found in templates folder</h1>", status_code=404)
    except Exception as e:
        return HTMLResponse(content=f"<h1>Error loading interface: {str(e)}</h1>", status_code=500)

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Process enhanced chat requests with conversation memory"""
    try:
        if not chat_agent:
            return ChatResponse(
                success=False,
                error=f"Enhanced chat agent not available. Error: {agent_error or 'Unknown error'}"
            )
        
        print(f"🔍 Processing: {request.question}")
        result = chat_agent.chat(request.question)
        
        if result.get("success"):
            # Convert DataFrame to list of dictionaries for JSON response
            data_list = []
            if isinstance(result.get("data"), pd.DataFrame) and len(result["data"]) > 0:
                data_list = result["data"].to_dict('records')
            
            print(f"✅ Success: {len(data_list)} rows, type: {result.get('conversation_type', 'database')}")
            
            # Store results for download
            global last_query_results
            last_query_results = {
                "data": data_list,
                "question": result["question"],
                "sql_query": result["sql_query"],
                "insights": result["insights"],
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            return ChatResponse(
                success=True,
                question=result["question"],
                sql_query=result["sql_query"],
                data=data_list,
                insights=result["insights"],
                row_count=result["row_count"],
                conversation_type=result.get("conversation_type", "database")
            )
        else:
            print(f"❌ Error: {result.get('error')}")
            return ChatResponse(success=False, error=result.get("error"))
            
    except Exception as e:
        error_msg = f"Server error: {str(e)}"
        print(f"❌ {error_msg}")
        traceback.print_exc()
        return ChatResponse(success=False, error=error_msg)

@app.get("/api/sample-questions")
async def get_sample_questions():
    """Get enhanced sample questions from the agent"""
    try:
        if not chat_agent:
            return {"questions": [
                "Hey, what can you help me with?",
                "Show me all properties in our portfolio",
                "What property types do we have?",
                "List all multifamily properties",
                "What cities do we have properties in?",
                "Show me hospitality properties",
                "Give me total equity for each fund"
            ]}
        
        questions = chat_agent.get_sample_questions()
        return {"questions": questions}
        
    except Exception as e:
        print(f"Error loading sample questions: {e}")
        return {"questions": ["Error loading questions - try typing your own!"]}

@app.get("/api/health")
async def health_check():
    """Enhanced health check with detailed status"""
    return {
        "status": "healthy",
        "chat_agent_available": chat_agent is not None,
        "agent_error": agent_error,
        "version": "2.0.0 - Enhanced",
        "features": [
            "Full data model awareness",
            "Conversation memory",
            "Follow-up question handling",
            "Intelligent SQL generation",
            "Business insights",
            "Download capabilities" if download_utils_available else "Download capabilities (not available)",
            "Email reports" if email_utils_available else "Email reports (not available)",
            "Edit and rerun prompts"
        ]
    }

@app.get("/api/conversation/reset")
async def reset_conversation():
    """Reset conversation memory"""
    try:
        if chat_agent:
            chat_agent.conversation_memory = []
            chat_agent.last_query_result = None
            chat_agent.last_sql_query = None
            chat_agent.last_question = None
            return {"status": "Conversation memory reset successfully"}
        else:
            return {"status": "Chat agent not available"}
    except Exception as e:
        return {"status": f"Error resetting conversation: {e}"}

@app.post("/api/download/csv")
async def download_csv():
    """Download last query results as CSV"""
    if not download_utils_available:
        return JSONResponse({"error": "Download utilities not available. Please install required packages."}, status_code=503)
    
    if last_query_results["data"] is None:
        return JSONResponse({"error": "No data available for download"}, status_code=404)
    
    try:
        df = pd.DataFrame(last_query_results["data"])
        csv_b64 = DownloadUtilities.dataframe_to_csv(df)
        
        if csv_b64:
            return JSONResponse({
                "success": True,
                "data": csv_b64,
                "filename": f"portfolio_query_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            })
        else:
            return JSONResponse({"error": "Failed to generate CSV"}, status_code=500)
    except Exception as e:
        return JSONResponse({"error": f"CSV generation error: {str(e)}"}, status_code=500)

@app.post("/api/download/excel")
async def download_excel():
    """Download last query results as Excel"""
    if not download_utils_available:
        return JSONResponse({"error": "Download utilities not available. Please install required packages."}, status_code=503)
    
    if last_query_results["data"] is None:
        return JSONResponse({"error": "No data available for download"}, status_code=404)
    
    try:
        df = pd.DataFrame(last_query_results["data"])
        excel_b64 = DownloadUtilities.dataframe_to_excel(df)
        
        if excel_b64:
            return JSONResponse({
                "success": True,
                "data": excel_b64,
                "filename": f"portfolio_query_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            })
        else:
            return JSONResponse({"error": "Failed to generate Excel"}, status_code=500)
    except Exception as e:
        return JSONResponse({"error": f"Excel generation error: {str(e)}"}, status_code=500)

@app.post("/api/download/pdf")
async def download_pdf():
    """Download last query results as PDF report"""
    if not download_utils_available:
        return JSONResponse({"error": "Download utilities not available. Please install required packages."}, status_code=503)
    
    if last_query_results["data"] is None:
        return JSONResponse({"error": "No data available for download"}, status_code=404)
    
    try:
        df = pd.DataFrame(last_query_results["data"])
        pdf_b64 = DownloadUtilities.create_pdf_report(
            question=last_query_results["question"],
            sql_query=last_query_results["sql_query"],
            df=df,
            insights=last_query_results["insights"],
            timestamp=last_query_results["timestamp"]
        )
        
        if pdf_b64:
            return JSONResponse({
                "success": True,
                "data": pdf_b64,
                "filename": f"portfolio_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            })
        else:
            return JSONResponse({"error": "Failed to generate PDF"}, status_code=500)
    except Exception as e:
        return JSONResponse({"error": f"PDF generation error: {str(e)}"}, status_code=500)

@app.post("/api/send-email")
async def send_email(request: EmailRequest):
    """Send email with report attachment"""
    if not email_utils_available or not email_sender:
        return JSONResponse({"success": False, "error": "Email functionality not available. Please check email_utils.py exists."}, status_code=503)
    
    if last_query_results["data"] is None:
        return JSONResponse({"success": False, "error": "No data available to send"}, status_code=404)
    
    try:
        # Generate attachment based on format
        df = pd.DataFrame(last_query_results["data"])
        attachment_data = None
        attachment_name = None
        attachment_type = None
        
        if request.attachment_format == "pdf":
            if not download_utils_available:
                return JSONResponse({"success": False, "error": "PDF generation not available"}, status_code=503)
            
            attachment_data = DownloadUtilities.create_pdf_report(
                question=last_query_results["question"],
                sql_query=last_query_results["sql_query"],
                df=df,
                insights=last_query_results["insights"],
                timestamp=last_query_results["timestamp"]
            )
            attachment_name = f"portfolio_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            attachment_type = "application/pdf"
            
        elif request.attachment_format == "excel":
            if not download_utils_available:
                return JSONResponse({"success": False, "error": "Excel generation not available"}, status_code=503)
            
            attachment_data = DownloadUtilities.dataframe_to_excel(df)
            attachment_name = f"portfolio_query_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            attachment_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            
        elif request.attachment_format == "csv":
            if not download_utils_available:
                return JSONResponse({"success": False, "error": "CSV generation not available"}, status_code=503)
            
            attachment_data = DownloadUtilities.dataframe_to_csv(df)
            attachment_name = f"portfolio_query_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            attachment_type = "text/csv"
        
        if not attachment_data:
            return JSONResponse({"success": False, "error": "Failed to generate attachment"}, status_code=500)
        
        # Create enhanced email message
        enhanced_message = f"""
{request.message}

Report Details:
- Query: {last_query_results["question"]}
- Generated: {last_query_results["timestamp"]}
- Total Results: {len(df)} rows

AI Insights:
{last_query_results["insights"]}

This report was generated by the Real Estate AI Portfolio Assistant.
        """
        
        # Send email
        result = email_sender.send_report_email(
            recipient_email=request.recipient_email,
            subject=request.subject,
            message=enhanced_message,
            attachment_data=attachment_data,
            attachment_name=attachment_name,
            attachment_type=attachment_type
        )
        
        if result["success"]:
            return JSONResponse({"success": True, "message": "Email sent successfully"})
        else:
            return JSONResponse({"success": False, "error": result["error"]}, status_code=500)
            
    except Exception as e:
        return JSONResponse({"success": False, "error": f"Email sending error: {str(e)}"}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    print("=" * 70)
    print("🚀 Enhanced Real Estate AI Server Starting...")
    print("🌐 URL: http://localhost:8000")
    print("🌐 Alternative: http://127.0.0.1:8000")
    print(f"🤖 Enhanced agent status: {'✅ Ready' if chat_agent else f'❌ {agent_error}'}")
    print(f"📥 Download features: {'✅ Available' if download_utils_available else '❌ Not available - install reportlab and xlsxwriter'}")
    print(f"📧 Email features: {'✅ Available' if email_utils_available else '❌ Not available - check email_utils.py'}")
    print("🔥 Features: Conversation memory, follow-up questions, data model awareness, edit & rerun, email reports")
    print("=" * 70)
    
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
    except Exception as e:
        print(f"❌ Server failed to start on port 8000: {e}")
        print("💡 Trying port 8001...")
        try:
            uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
        except Exception as e2:
            print(f"❌ Server failed to start on port 8001: {e2}")

            print("💡 Try manually with: python server.py")
