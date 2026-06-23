import requests


class EdgarCIKLookup:
    """
    Lookup a company's CIK number by name or ticker using SEC EDGAR data.
    Fetches a fresh copy of the data on initialization.
    """

    TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
    #Header you send with every request (like a cover sheet)
    HEADERS = {
        "User-Agent": "MLT GS kareemtaher25@gmail.com",
        "Accept-Encoding": "gzip, deflate",
        "Host": "www.sec.gov",
    }

    def __init__(self):
        self._by_name = {}    # company name (lowercase) -> entry
        self._by_ticker = {}  # ticker (lowercase) -> entry
        self._load()

    def _load(self):
        response = requests.get(self.TICKERS_URL, headers=self.HEADERS)
        response.raise_for_status()
        data = response.json()

        for entry in data.values():
            cik    = str(entry["cik_str"]).zfill(10)  # SEC pads CIKs to 10 digits
            name   = entry["title"]
            ticker = entry["ticker"]

            normalized = {
                "cik": cik,
                "name": name,
                "ticker": ticker,
            }

            self._by_name[name.lower()] = normalized
            self._by_ticker[ticker.lower()] = normalized

    def name_to_cik(self, company_name: str) -> tuple | None:
        """
        Look up a company by name.
        Returns (cik, name, ticker) or None if not found.
        """
        entry = self._by_name.get(company_name.lower())
        if entry is None:
            return None
        return (entry["cik"], entry["name"], entry["ticker"])

    def ticker_to_cik(self, ticker: str) -> tuple | None:
        """
        Look up a company by stock ticker.
        Returns (cik, name, ticker) or None if not found.
        """
        entry = self._by_ticker.get(ticker.lower())
        if entry is None:
            return None
        return (entry["cik"], entry["name"], entry["ticker"])


class EdgarFilingFetcher:
    """
    Given a CIK, fetch 10-K and 10-Q filing URLs.
    """

    SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
    DOCUMENT_URL = "https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{document}"
    HEADERS = {
        "User-Agent": "MLT GS kareemtaher25@gmail.com",
        "Accept-Encoding": "gzip, deflate",
    }

    def __init__(self, cik: str):
        self.cik = cik
        self._filings = []
        self._load()

    def _load(self):
        url = self.SUBMISSIONS_URL.format(cik=self.cik)
        response = requests.get(url, headers=self.HEADERS)
        response.raise_for_status()
        data = response.json()

        recent = data["filings"]["recent"]
        forms = recent["form"]
        accessions = recent["accessionNumber"]
        documents = recent["primaryDocument"]

        for i in range(len(forms)):
            if forms[i] in ("10-K", "10-Q"):
                clean_accession = accessions[i].replace("-", "")
                url = self.DOCUMENT_URL.format(
                    cik=int(self.cik),  # URL uses CIK without leading zeros
                    accession=clean_accession,
                    document=documents[i]
                )
                self._filings.append({
                    "form": forms[i],
                    "accession": accessions[i],
                    "url": url
                })

    def get_filings(self):
        return self._filings
    

if __name__ == "__main__":
    lookup = EdgarCIKLookup()

    # Step 1 - get CIK
    result = lookup.ticker_to_cik("AAPL")
    print(f"Ticker lookup → {result}")

    cik = result[0]  # "0000320193"

    # Step 2 - get filing URLs
    fetcher = EdgarFilingFetcher(cik)
    for filing in fetcher.get_filings():
        print(f"Form: {filing['form']}  URL: {filing['url']}")