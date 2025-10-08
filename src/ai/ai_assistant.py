from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from langchain.prompts import PromptTemplate

from langchain_core.tools import tool
from langchain.agents import initialize_agent, Tool

from .ai_models import llama_3_70b_free_together_model_deterministic
from ..integrations.gmail_service import get_gmail_service
from ..integrations.gcalendar_service import get_gcal_service
from ..utils.messaging import send_message


@tool
def get_today_calendar_events():
    """
    Get today's events from Google Calendar
    """
    gcal = get_gcal_service()
    events = gcal.get_events_for_date()
    return events


@tool
def fetch_and_read_newsletters()->dict:
    """
    Fetch newsletter emails from predefined email addressses, format the content as text, and mark the emails as read.
    """
    newsletters_email_addresses = [
        "crew@morningbrew.com",
        "superhuman@mail.joinsuperhuman.ai",
    ]

    try:
        gmail = get_gmail_service()

        newsletters = []
        for email_address in newsletters_email_addresses:
            emails_from_newsletter = gmail.get_daily_emails_from_newsletter(email_address)
            newsletters.extend(emails_from_newsletter)
        
        if not newsletters:
            print("[Assistant] No newsletters found")
            return

        newsletters_text = []
        for email in newsletters:
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
        print(f"[Assistant] Error fetching newsletters: {e}")
        return {}


async def agentic_send_daily_newsletter_summaries():
    """
    Runs an agent which reads and summarizes today's newsletters
    """
    tools = [
        Tool(
            name="fetch_and_read_newsletters",
            func=fetch_and_read_newsletters,
            description="Fetch newsletter emails from predefined email addressses, format the content as text, and mark the emails as read."
        )
    ]

    agent = initialize_agent(
        tools,
        llama_3_70b_free_together_model_deterministic,
        agent="zero-shot-react-description",
        verbose=True,
        handle_parsing_errors=True,
    )

    completion = "Agent is unable to read and summarize today's newsletters."
    try:
        prompt = """Produce a summary for each of today's email newsletters.
For each summary, title it with the newsletter name, subtitle it with the newsletter email title, and extract the most important points to form bullet points.
Each summary should be less than 200 words, bold key words, and use emojis to indicate the topic.
Do not preface your response. Use "📰 Newsletters for" along with one newsletter's date as the response title bolded.
Don't include promotional info."""
        llm_response = await agent.arun(prompt)

        completion = llm_response if isinstance(llm_response, str) else str(llm_response)
        print(f"[Assistant] Daily newsletters summaries generated: {completion}")

    except Exception as e:
        print(f"[Assistant] Error generating newsletter summaries: {e}")

    # Send summary to Discord & iMessage
    await send_message(completion)


def start_assistant():
    """
    Start assistant to retrieve email newsletters and generate summaries for them daily at 8am PT
    """
    scheduler = AsyncIOScheduler()
    scheduler.add_job(agentic_send_daily_newsletter_summaries, CronTrigger(hour=9, minute=30), id="agentic_daily_assistant_completion")
    scheduler.start()
    return scheduler
