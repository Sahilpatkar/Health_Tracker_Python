import asyncio
import os
from typing import Optional
from datetime import date, datetime
from pydantic import BaseModel, field_validator
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic_ai import Agent
from pydantic_ai.models.groq import GroqModel
from langsmith import traceable
from dotenv import load_dotenv

load_dotenv()
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
os.environ["LANGCHAIN_API_KEY"]   = os.getenv("LANGCHAIN_API_KEY")
os.environ["LANGSMITH_TRACING"]   = "true"           # enable LangSmith
os.environ["LANGCHAIN_PROJECT"]   = "ContextExtractor"

class ReportContext(BaseModel):
    name: str
    date: date
    gender: str
    location: str

    @field_validator("name", "gender", "location")
    def strip_fields(cls, v: str) -> str:
        return v.strip()

    @field_validator("date", mode="before")
    def parse_date(cls, v: str) -> date:
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%d %b %Y"):
            try:
                return datetime.strptime(v.strip(), fmt).date()
            except ValueError:
                continue
        raise ValueError("Invalid date format. Expected a valid date like YYYY-MM-DD.")

SYSTEM_PROMPT = """
You are given a chunk of a medical report. 
Extract **only** the following fields and return _exactly_ a JSON object with keys:
  - "name": patient’s name
  - "date": report date (any reasonable date format)
  - "gender": patient’s gender
  - "location": patient’s location
Do not include anything else.
"""

@traceable
async def extract_context_from_pdf(pdf_dir: str) -> ReportContext:
    # Use a deterministic JSON-output model
    #model = GroqModel("llama-3.3-70b-versatile", temperature=0)
    agent: Agent[None, ReportContext] = Agent(
        "openai:gpt-4o-mini",
        system_prompt=SYSTEM_PROMPT,
        output_type=ReportContext,
    )

    # load & split
    docs   = PyPDFDirectoryLoader(pdf_dir).load()

    for doc in docs:
        doc.page_content = clean_text(doc.page_content)

    splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=100)
    chunks = splitter.split_documents(docs)

    # iterate until we capture all four fields
    for chunk in chunks:
        resp = await agent.run(chunk.page_content)
        if isinstance(resp.output, ReportContext):
            ctx = resp.output
            # if all fields are non-empty, return immediately
            if all(getattr(ctx, f) for f in ("name", "date", "gender", "location")):
                return ReportContext(
                    name=ctx.name,
                    date=ctx.date.isoformat().strip(),
                    gender=ctx.gender,
                    location=ctx.location,
                )

    raise RuntimeError("Failed to extract all context fields from PDF.")

def clean_text(text: str) -> str:
    lines = text.splitlines()
    cleaned = []
    for line in lines:
        # Ignore lines that are likely garbage (like QR hash codes)
        if not (len(line.strip()) > 20 and all(c.isalnum() for c in line.strip())):
            cleaned.append(line)
    return "\n".join(cleaned)


if __name__ == "__main__":
    out = asyncio.run(extract_context_from_pdf("/Users/spatkar/PycharmProjects/Health_Tracker_Python/datastore/"))
    print("context =", out)
    print("context =", out.date)
