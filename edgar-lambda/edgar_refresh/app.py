import boto3
import requests
import os
import json

#to satisfy the SEC Fair Access policy
HEADERS = {"User-Agent": "Kareem Taher kareemtaher25@gmail.com"}
TICKER_URL = "https://www.sec.gov/files/company_tickers.json"
#the bucket name from the enviroment variable we set in template.yaml
BUCKET_NAME = os.environ["BUCKET_NAME"]

#how to talk to AWS services from code
s3 = boto3.client("s3")

def lambda_handler(event, context):
    # Download ticker data from SEC EDGAR
    response = requests.get(TICKER_URL, headers=HEADERS)
    #keep in mind the status from the responce
    response.raise_for_status()
    
    #get the json version of the response (raw data)
    ticker_data = response.json()
    
    # Upload to S3
    s3.put_object(
        Bucket=BUCKET_NAME,
        Key="company_tickers.json",
        Body=json.dumps(ticker_data),
        ContentType="application/json"
    )
    
    return {
        "statusCode": 200,
        "body": f"Successfully uploaded {len(ticker_data)} tickers to S3"
    }