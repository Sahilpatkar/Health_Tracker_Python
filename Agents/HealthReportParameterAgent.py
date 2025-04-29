import asyncio
import json

from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic_ai import Agent
from pydantic_ai.models.groq import GroqModel
from typing import Union
from pydantic import BaseModel, field_validator
from langsmith import traceable
import os
from dotenv import load_dotenv
load_dotenv()

os.environ['GROQ_API_KEY']=os.getenv("GROQ_API_KEY")
os.environ["LANGCHAIN_API_KEY"]=os.getenv("LANGCHAIN_API_KEY")
os.environ["LANGCHAIN_TRACING_V2"]="true"
os.environ["LANGCHAIN_PROJECT"]="Health Monitoring"

class ReportParameter(BaseModel):
    name: str
    value: Union[float, str]
    unit: str

    @field_validator("value")
    def parse_value(cls, v):
        # if it’s already a float/int, leave it
        if isinstance(v, (float, int)):
            return float(v)
        # if it’s a string that looks like a number, cast it
        if isinstance(v, str):
            try:
                return float(v)
            except ValueError:
                return v  # non-numeric string stays as-is
        # otherwise, let Pydantic error out
        return v

@traceable
async def extract_from_pdf(pdf_path: str):

    model = GroqModel("llama-3.3-70b-versatile")  # or your chosen Groq model
    agent: Agent[
    None,  # no deps
    Union[list[ReportParameter], str]  # type: ignore
    ] = Agent(
        "openai:gpt-4o-mini",
        system_prompt=(
            "Extract all parameters from the health report.json and return _only_ a JSON array of "
            "objects like `[{{\"name\":\"…\",\"unit\":\"…\",\"value\":…}}, …]`, with no extra text."
        ),
        output_type=Union[list[ReportParameter], str],  # type: ignore
    )
    print("PDF_PATH",pdf_path)
    docs = PyPDFDirectoryLoader(pdf_path).load()
    chunks = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200).split_documents(docs)

    result_dict = {}
    #all_params: list[ReportParameter] = []
    # for chunk in chunks:
    #     params = await agent.run(chunk.page_content)
    #     for p in params.output:
    #         try:# now iterating over your list[ReportParameter]
    #             print(p.name, p.value, p.unit)
    #             if p.name:
    #                 #all_params.append(ReportParameter(name=p.name, value=p.value, unit=p.unit))
    #                 result_dict[p.name] = {"value": p.value, "unit": p.unit}
    #         except:
    #             pass

    tasks = [agent.run(chunk.page_content) for chunk in chunks]
    all_responses = await asyncio.gather(*tasks)
    for response in all_responses:
        for p in response.output:
            try:  # now iterating over your list[ReportParameter]
                print(p.name, p.value, p.unit)
                if p.name:
                    # all_params.append(ReportParameter(name=p.name, value=p.value, unit=p.unit))
                    result_dict[p.name] = {"value": p.value, "unit": p.unit}
            except:
                pass

    return result_dict

if __name__ == "__main__":
    results = asyncio.run(extract_from_pdf("/Users/spatkar/PycharmProjects/Health_Monitoring_project/pdfs"))
    print(results)
    file_path = f"ParametersResult.json"
    with open(file_path, "w") as f:
        json.dump(results,f,indent=4)