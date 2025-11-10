# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Memex is a personal LLM that leverages your personal data corpus (emails, messages, notes, calendar) as its knowledge base. It uses RAG (Retrieval-Augmented Generation) with vector embeddings and autonomous agents to provide contextual responses and proactive assistance through Discord and iMessage interfaces.

**Core Technologies**: FastAPI, LangChain, ChromaDB, Together.ai (Llama-3.3-70B, Qwen2.5-7B), Unstructured.io

## Common Commands

### Development & Running
```bash
# Setup
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with required credentials

# Run the FastAPI server (hot reload enabled)
python3 -m src.app

# Generate embeddings from data directory
python3 src/scripts/generate_embeddings.py --folder_path ./data --chunk_max_characters 1500

# Process specific data sources
python3 src/scripts/read_imessages_db.py  # Extract from macOS chat.db
python3 src/scripts/process_mbox_file.py  # Convert Gmail mbox to EML
python3 src/scripts/read_vcards.py        # Parse vCard contacts
```

### Deployment (Fly.io)
```bash
fly auth login
fly deploy  # or fly launch for first time

# Transfer ChromaDB to volume (manual SFTP)
fly ssh sftp shell
put ./chroma_db/chroma.sqlite3 /chroma_db/chroma.sqlite3
# Create collection directory and transfer remaining files
```

### Dependencies
```bash
# Install SSL certificates (macOS) if nltk fails
sudo /Applications/Python\ 3.12/Install\ Certificates.command

# Install poppler for PDF processing
brew install poppler
```

## Architecture

### Data Flow: Two-Path Routing System

**Offline Phase (Embedding Generation)**:
```
Raw Data → Scripts → Unstructured.io → Chunking → BAAI/bge-large-en-v1.5 → ChromaDB
```

**Runtime Phase (Query Processing)**:
```
User Message → Intent Classifier (Qwen2.5-7B) → Router → [RAG Path OR Agent Path]
```

1. **RAG Path** (`intent="rag_query"`): Similarity search in ChromaDB (k=8) → Llama-3.3-70B generates response
2. **Agent Path** (`intent="tool_action"`): LangChain ReAct agent executes tools (calendar, email) → Llama-3.3-70B

### Key Components

#### Entry Point: [src/app.py](src/app.py)
FastAPI server with `lifespan` context manager that orchestrates:
- Discord client (if `ENABLE_DISCORD_CLIENT=true`)
- iMessage WebSocket listener (if `ENABLE_WEBSOCKET_LISTENER=true`)
- Agent scheduler for daily jobs (if `ENABLE_AGENT_JOBS=true`)

#### Core AI Modules: [src/ai/](src/ai/)
- **[chat.py](src/ai/chat.py)**: Query orchestrator with intent detection (`process_message()`)
- **[rag_engine.py](src/ai/rag_engine.py)**: RAG implementation (ChromaDB retrieval + Llama-3.3-70B)
- **[ai_agent.py](src/ai/ai_agent.py)**: LangChain zero-shot-react-description agent with tools
- **[ai_models.py](src/ai/ai_models.py)**: Model configurations (embedding, creative/deterministic LLMs)

#### Integration Layer: [src/integrations/](src/integrations/)
- **[discord_client.py](src/integrations/discord_client.py)**: Discord bot (filters by app_id)
- **[gmail_service.py](src/integrations/gmail_service.py)**: Gmail API wrapper (OAuth2, fetch/read emails)
- **[gcalendar_service.py](src/integrations/gcalendar_service.py)**: Google Calendar API (OAuth2, get/create events)

#### Routes: [src/routes/](src/routes/)
- **[api.py](src/routes/api.py)**: REST endpoints (`/api/v1/completion`, `/api/v1/completion/imessage`) with localhost-only security
- **[ws_listener.py](src/routes/ws_listener.py)**: iMessage integration via BlueBubbles WebSocket (Socket.IO)

#### Utilities: [src/utils/](src/utils/)
- **[constants.py](src/utils/constants.py)**: Configuration (ChromaDB path, credentials, newsletter addresses)
- **[helpers.py](src/utils/helpers.py)**: Date parsing, file metadata, text cleaning, phone normalization
- **[messaging.py](src/utils/messaging.py)**: Unified messaging abstraction (`send_message()` dispatches to Discord + iMessage)

### Data Sources & Processing

**Supported Sources**:
- Apple: Notes (txt), Contacts (vcf), Messages (CSV from chat.db), Calendar (ics)
- Google: Gmail (mbox→eml), Calendar (ics), Maps (CSV), Search/YouTube History (HTML/JSON), Drive (docx), Contacts (vcf)

**Currently Included**: Apple notes/contacts/messages, Google calendar/maps

**Processing Scripts**: [src/scripts/](src/scripts/)
- **[generate_embeddings.py](src/scripts/generate_embeddings.py)**: Main orchestrator (glob → UnstructuredLoader → chunk → embed → store)
- **[read_imessages_db.py](src/scripts/read_imessages_db.py)**: Extracts from macOS SQLite `chat.db`, decodes Apple's proprietary typedstream format, chunks with 3-row overlap
- **[process_mbox_file.py](src/scripts/process_mbox_file.py)**: Converts Gmail mbox to EML files, filters content types
- **[read_vcards.py](src/scripts/read_vcards.py)**: Parses vCard files

**Chunking Strategy**:
- Method: `by_title` for semantic coherence
- Max characters: 1500 (configurable via `--chunk_max_characters`)
- Overlap: 3 rows for messages to maintain conversation context

**ChromaDB Metadata Schema**:
- `type`: Data source identifier (e.g., "apple/notes", "google/gmail")
- `created_at`, `updated_at`: Timestamps (epoch or string)
- `sent_from`, `subject`: Email-specific fields
- `location`: Maps-specific field

### Agent System

**Framework**: LangChain with zero-shot-react-description pattern

**Available Tools** ([src/ai/ai_agent.py](src/ai/ai_agent.py)):
1. `fetch_and_read_newsletter`: Fetches today's emails from specified sender, parses HTML, marks as read
2. `get_calendar_events`: Queries Google Calendar for today's events
3. `create_calendar_event`: Creates calendar events with Pydantic validation (CalendarEventFields)

**Scheduled Jobs** (APScheduler):
- **Trigger**: CronTrigger daily at 9:30 AM
- **Job ID**: `agentic_daily_assistant`
- **Tasks**:
  1. Newsletter summaries (iterates `NEWSLETTER_EMAIL_ADDRESSES`, formats <200 words)
  2. Calendar events (formats chronologically with location/description)
  3. Sends combined summary to Discord + iMessage via `send_message()`

### iMessage Integration (BlueBubbles)

**Two Methods**:
1. **WebSocket Listener** ([ws_listener.py](src/routes/ws_listener.py)): Real-time Socket.IO events
   - Validates handshake before connecting
   - Filters by service type and sender whitelist
   - Echo prevention: Uses invisible marker `\u200B\u200C\u200D` to detect self-sent messages
2. **REST API**: Direct send via BlueBubbles HTTP API (`send_imessage()`)

**Configuration**: Requires `BLUEBUBBLES_PORT`, `BLUEBUBBLES_TOKEN`, `VALID_IMESSAGE_SENDERS`, `IMESSAGE_RECIPIENT`

### Environment Configuration

**Feature Flags** (see [.env.example](.env.example)):
- `ENABLE_DISCORD_CLIENT`: Start Discord bot
- `ENABLE_WEBSOCKET_LISTENER`: Start iMessage WebSocket listener
- `ENABLE_AGENT_JOBS`: Enable daily scheduled agent tasks
- `ENABLE_REST_API`: Enable REST endpoints
- `USE_UNSTRUCTURED_API`: Use Unstructured.io API vs. local processing

**Required Credentials**:
- `TOGETHER_API_KEY`: For LLM inference and embeddings
- `DISCORD_BOT_TOKEN`: Discord bot authentication
- `BLUEBUBBLES_TOKEN`: iMessage API access
- Google OAuth tokens in `src/utils/token.json` (generated on first run)

## Development Guidelines

### RAG Query Response Style
- Casual, friendly tone
- Never mention "context" explicitly
- Censor sensitive info (passwords, API keys, personal identifiers)
- Deduplicate information across retrieved documents
- Target <200 word responses

### Agent Tool Development
1. Define tool function in [src/ai/ai_agent.py](src/ai/ai_agent.py)
2. Use Pydantic for input validation (see `CalendarEventFields` example)
3. Return structured data or error messages
4. Add tool to `tools` list in `ScheduledAiAgent.__init__()`
5. Update tool description for LLM (clear, concise, includes parameters)

### Adding New Data Sources
1. Create processing script in [src/scripts/](src/scripts/)
2. Use `UnstructuredLoader` for parsing
3. Apply chunking strategy (typically `by_title`, 1500 chars max)
4. Clean metadata with helpers from [src/utils/helpers.py](src/utils/helpers.py)
5. Run `generate_embeddings.py` with `--folder_path` pointing to new data

### Security Notes
- REST API endpoints use IP whitelist (127.0.0.1 only) in [api.py](src/routes/api.py:15-17)
- Discord filters by `app_id` to prevent cross-talk in [discord_client.py](src/integrations/discord_client.py:39)
- iMessage validates sender against `VALID_IMESSAGE_SENDERS` in [ws_listener.py](src/routes/ws_listener.py:56-58)
- OAuth tokens stored in `src/utils/token.json` (add to `.gitignore`)

### Model Selection
- **Intent Classification**: `Qwen2.5-7B-Instruct-Turbo` (fast, deterministic)
- **RAG Responses**: `Llama-3.3-70B-Instruct-Turbo` with temperature=0.4 (creative)
- **Agent Execution**: `Llama-3.3-70B-Instruct-Turbo` with temperature=0 (deterministic)
- **Embeddings**: `BAAI/bge-large-en-v1.5` (1024 dimensions)

All models accessed via Together.ai API.

## Common Pitfalls

1. **ChromaDB Path**: Default is `./chroma_db/`. Change via `CHROMA_DIRNAME` in `.env`
2. **BlueBubbles Connection**: Requires local server running on macOS. Validate handshake endpoint before connecting WebSocket.
3. **Google OAuth**: First run prompts browser authentication. Token stored in `src/utils/token.json`.
4. **iMessage Echo Loops**: The system uses invisible Unicode markers. Don't modify the echo prevention logic in [ws_listener.py](src/routes/ws_listener.py:105-107).
5. **Embedding Generation**: Use `--dry_run` flag for testing. Large datasets can take hours and consume significant API credits.
6. **Agent Timeout**: Agent execution has 120s timeout. Long-running tasks will fail.
7. **Newsletter Fetching**: Requires emails received "today" (uses `after:YYYY/MM/DD` Gmail query). Test with recent newsletters.

## Testing

**Current State**: No formal test suite. Manual testing via:
- Development mode: `python3 -m src.app` (hot reload enabled)
- Script dry runs: `--dry_run` flags in scripts
- Verbose logging throughout codebase

## References

- **BlueBubbles API**: https://documenter.getpostman.com/view/765844/UV5RnfwM
- **Inspiration**: Linus's personal corpus LLM (https://x.com/thesephist/status/1629272600156176386)
