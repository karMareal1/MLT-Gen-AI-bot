import boto3
import requests
import os
import json
import time

HEADERS = {"User-Agent": "Kareem Taher kareemtaher25@gmail.com"}
BUCKET_NAME = os.environ["BUCKET_NAME"]
MODEL_ID = os.environ["MODEL_ID"]

s3 = boto3.client("s3")
bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")

VALID_PERIODS = {"Q1", "Q2", "Q3", "Q4", "FY"}

#make sure the request has all four fields
def validate_request(event):
    errors = []
    
    if not event.get("question") or not isinstance(event["question"], str):
        errors.append("'question' must be a non-empty string")
    
    if not event.get("ticker") or not isinstance(event["ticker"], str) or not event["ticker"].isupper():
        errors.append("'ticker' must be a non-empty uppercase string")
    
    if not isinstance(event.get("year"), int) or event["year"] < 1900:
        errors.append("'year' must be a four-digit integer (1900 or later)")
    
    if event.get("period") not in VALID_PERIODS:
        errors.append(f"Invalid value for 'period': '{event.get('period')}'. Must be one of: Q1, Q2, Q3, Q4, FY.")
    
    return errors

def lambda_handler(event, context):
    # Validate input
    errors = validate_request(event)
    if errors:
        return {
            "error": "ValidationError",
            "message": errors[0]
        }
    
    question = event["question"]
    ticker = event["ticker"]
    year = event["year"]
    period = event["period"]
    
    # Read ticker data from S3
    s3_response = s3.get_object(Bucket=BUCKET_NAME, Key="company_tickers.json")
    ticker_data = json.loads(s3_response["Body"].read().decode("utf-8"))
    
    # Find the company name for the ticker
    company_name = None
    for entry in ticker_data.values():
        if entry.get("ticker") == ticker:
            company_name = entry.get("title")
            break
    
    if not company_name:
        return {
            "error": "ValidationError",
            "message": f"Ticker '{ticker}' not found in EDGAR database"
        }
    
    # Build prompt for Claude
    prompt = f"""You are a financial analyst assistant. Answer the following question about {company_name} ({ticker}) 
for the {period} {year} filing period.

Question: {question}

Provide a concise, accurate answer based on typical SEC filing data for this company and period."""

    # Call Claude on Bedrock
    start_time = time.time()
    
    bedrock_response = bedrock.invoke_model(
        modelId=MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1024,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        })
    )
    
    latency_ms = int((time.time() - start_time) * 1000)
    
    # Parse Bedrock response
    response_body = json.loads(bedrock_response["body"].read())
    answer = response_body["content"][0]["text"]
    input_tokens = response_body["usage"]["input_tokens"]
    output_tokens = response_body["usage"]["output_tokens"]
    
    # Return contract-compliant response
    return {
        "answer": answer,
        "meta": {
            "model": MODEL_ID,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "latency_ms": latency_ms
        }
    }