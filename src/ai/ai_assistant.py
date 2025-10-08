import asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from langchain.prompts import PromptTemplate

from langchain_core.tools import tool
from langchain.agents import initialize_agent, Tool

from .ai_models import llama_3_70b_free_together_model_deterministic
from ..integrations.gmail_service import get_gmail_service
from ..integrations.gcalendar_service import get_gcal_service
from ..utils.messaging import send_message


ai_agent = None

def get_ai_agent():
    """Get or create AI agent"""
    global ai_agent
    if ai_agent is None:
        tools = [
            Tool(
                name="fetch_and_read_newsletter",
                func=fetch_and_read_newsletter,
                description="""Fetches newsletter emails from a specified email address, formats the content as text, and marks the emails as read.
Args:
    newsletter_email_address: The email address of the newsletter."""
            )
        ]
        ai_agent = initialize_agent(
            tools,
            llama_3_70b_free_together_model_deterministic,
            agent="zero-shot-react-description",
            verbose=True,
            handle_parsing_errors=True,
        )
        return ai_agent


@tool
def get_today_calendar_events():
    """
    Get today's events from Google Calendar
    """
    gcal = get_gcal_service()
    events = gcal.get_events_for_date()
    return events


@tool
def fetch_and_read_newsletter(newsletter_email_address: str)->list:
    """
    Fetches newsletter emails from a specified email addresss, formats the content as text, and marks the emails as read.
    Args:
        newsletter_email_address: The email address of the newsletter.
    """

    try:
        gmail = get_gmail_service()

        emails_from_newsletter = gmail.get_daily_emails_from_newsletter(newsletter_email_address)
        
        if not emails_from_newsletter:
            print("[Assistant] No newsletters found")
            return

        newsletters_text = []
        for email in emails_from_newsletter:
            email_text = f"""
            From: {email["from"]}
            Subject: {email["subject"]}
            Date: {email["date"]}
            Content: {email["body"]}
            """
            newsletters_text.append(email_text)
            gmail.mark_as_read(email["id"])
            print(f"[Assistant] Email {email['id']} marked as read")
        
        return newsletters_text

    except Exception as e:
        print(f"[Assistant] Error fetching newsletter emails: {e}")
        return []


async def agentic_send_daily_newsletter_summaries():
    """
    Runs an agent which reads and summarizes today's newsletters
    """
    agent = get_ai_agent()

    newsletters_email_addresses = [
        "crew@morningbrew.com",
        "superhuman@mail.joinsuperhuman.ai",
    ]

    def generate_prompt(newsletter_address):
        prompt = f"""Summarize newsletter from {newsletter_address} for today.
For the summary, title it with the newsletter name, subtitle it with the newsletter email title, and extract the most important points to form bullet points.
Bold both the title and subtitle. It should use less than 200 words, bold key words, and use emojis to indicate the topic.
Do not preface your response. Don't include promotional info."""
        return prompt

    completion = "Agent is unable to read and summarize today's newsletters."
    responses = []
    try:
        for email_address in newsletters_email_addresses:
            try:
                prompt = generate_prompt(email_address)
                llm_response = await asyncio.wait_for(agent.arun(prompt), timeout=60)
                completion = llm_response if isinstance(llm_response, str) else str(llm_response)
                responses.append(completion)
                print(f"[Assistant] Daily newsletter summary generated for {email_address}: {completion}")
            except Exception as e:
                print(f"[Assistant] Error generating newsletter summary for {email_address}: {e}")

    except Exception as e:
        print(f"[Assistant] Error generating newsletter summaries: {e}")

    # Send summary to Discord & iMessage
    if responses:
        today = datetime.now().strftime('%m/%d/%Y')
        combined_response = f"## 📰 Newsletters for {today}\n\n" + "\n\n".join(responses)
        await send_message(combined_response)
    else:
        await send_message("Unable to retrieve & summarize today's newsletters")


def start_assistant():
    """
    Start assistant to retrieve email newsletters and generate summaries for them daily at 8am PT
    """
    scheduler = AsyncIOScheduler()
    scheduler.add_job(agentic_send_daily_newsletter_summaries, CronTrigger(hour=9, minute=30), id="agentic_daily_assistant_completion")
    scheduler.start()
    return scheduler
