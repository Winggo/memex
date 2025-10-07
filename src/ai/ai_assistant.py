from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from langchain_core.tools import tool
from langchain.prompts import PromptTemplate
import os

from .ai_models import llama_3_70b_free_together_model_deterministic
from ..integrations.gmail_service import get_gmail_service
from ..utils.messaging import send_discord_message, send_imessage


@tool
def get_calendar_events():
    """
    Get today's events from Google Calendar
    """
    creds = None
    if os.path.exists("google_oauth_credentials.json"):
        creds = Credentials.from_authorized_user_file("google_oauth_credentials.json", GOOGLE_OAUTH_SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("google_oauth_credentials.json", GOOGLE_OAUTH_SCOPES)
            creds = flow.run_local_server(port=0)

        with open("google_oauth_credentials.json", "w") as token:
            token.write(creds.to_json())
        if not newsletters:
            print("[Assistant] No newsletters found")
            return

    try:
        service = build("calendar", "v3", credentials=creds)
        now = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()

        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=now,
                maxResults=10,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])

        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            print(start, event["summary"])

    except HttpError as error:
        print(f"A Google calendar http error occurred: {error}")


newsletters_email_addresses = [
    "crew@morningbrew.com",
    "superhuman@mail.joinsuperhuman.ai",
]


email_newslatters_summary_template = PromptTemplate(
    input_variables=["emails"],
    template="""For each of the given email newsletters, extract the most important points to produce a summary.
For each summary, title it with the newsletter name. Each summary should be less than 200 words. Use bullet points whenever appropriate, bold key words, and emojis to encapsulate bulletpoint topic.
Do not preface the response. Use "📰 Newsletters for" along with one newsletter's date as the response title, and make it bold.
Don't include promotional info.

*Emails:*
{emails}"""
)


async def generate_daily_newsletter_summaries():
    """Generate daily newsletter summaries from Gmail"""

    newsletters_content = None
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
        
        newsletters_content = "\n\n".join(newsletters_text)
    except Exception as e:
        print(f"[Assistant] Error getting newsletters: {e}")
        return

    if not newsletters_content:
        print("[Assistant] No newsletters content found")
        return

    chain = email_newslatters_summary_template | llama_3_70b_free_together_model_deterministic
    llm_response = chain.invoke({"emails": newsletters_content})

    completion = llm_response.content if hasattr(llm_response, 'content') else str(llm_response)
    print(f"[Assistant] Daily newsletters summaries generated: {completion}")

    # Send to summary to Discord
    if os.environ.get("ENABLE_DISCORD_CLIENT") == "true":
        await send_discord_message(completion)

    # Send to summary to iMessage
    if os.environ.get("ENABLE_WEBSOCKET_LISTENER") == "true":
        send_imessage(completion)


def start_assistant():
    """
    Start assistant to retrieve email newsletters and generate summaries for them daily at 8am PT
    """
    scheduler = AsyncIOScheduler()
    scheduler.add_job(generate_daily_newsletter_summaries, CronTrigger(hour=9, minute=30), id="daily_completion")
    scheduler.start()
    return scheduler
