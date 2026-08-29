from datetime import date
from pathlib import Path
import sys

from botocore.exceptions import ClientError


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from cost.explorer import get_cost_summary


class FakeCostExplorer:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    def get_cost_and_usage(self, **kwargs):
        self.requests.append(kwargs)
        return self.responses.pop(0)

    def get_cost_forecast(self, **kwargs):
        self.forecast_request = kwargs
        return {
            "Total": {"Amount": "3.00", "Unit": "USD"},
            "ForecastResultsByTime": [],
        }


def total_result(amount, *, estimated=False, start="2026-08-01"):
    return {
        "TimePeriod": {"Start": start, "End": "2026-08-02"},
        "Estimated": estimated,
        "Total": {"NetUnblendedCost": {"Amount": amount, "Unit": "USD"}},
    }


def grouped_result(name, amount, *, estimated=False):
    return {
        "Estimated": estimated,
        "Groups": [
            {
                "Keys": [name],
                "Metrics": {"NetUnblendedCost": {"Amount": amount, "Unit": "USD"}},
            }
        ],
    }


def test_cost_summary_returns_normalized_costs_and_uses_exclusive_end_date():
    client = FakeCostExplorer(
        [
            {"ResultsByTime": [total_result("1.2000001", estimated=True)]},
            {"ResultsByTime": [grouped_result("Amazon EC2", "1.00")]},
            {"ResultsByTime": [grouped_result("USE1-BoxUsage:t3.micro", "0.50")]},
            {"ResultsByTime": [total_result("0.20", start="2026-08-01")]},
        ]
    )

    result = get_cost_summary(client, today=date(2026, 8, 29))

    assert result["status"] == "available"
    assert result["time_period"] == {"Start": "2026-08-01", "End": "2026-08-30"}
    assert result["month_to_date"] == {
        "amount": 1.2,
        "currency": "USD",
        "estimated": True,
    }
    assert result["by_service"][0]["name"] == "Amazon EC2"
    assert result["daily_trend"][0]["amount"] == 0.2
    assert result["forecast"]["total"]["amount"] == 3.0
    assert client.forecast_request["Metric"] == "NET_UNBLENDED_COST"
    assert client.forecast_request["TimePeriod"]["End"] == "2026-09-01"
    assert client.requests[-1]["Granularity"] == "DAILY"


def test_cost_summary_combines_paginated_group_results_and_preserves_credits():
    client = FakeCostExplorer(
        [
            {"ResultsByTime": [total_result("-0.10")]},
            {
                "ResultsByTime": [grouped_result("Amazon S3", "1.00")],
                "NextPageToken": "next",
            },
            {"ResultsByTime": [grouped_result("Amazon S3", "-0.25")]},
            {"ResultsByTime": [grouped_result("TimedStorage-ByteHrs", "0")]},
            {"ResultsByTime": [total_result("-0.10")]},
        ]
    )

    result = get_cost_summary(client, today=date(2026, 8, 29))

    assert result["month_to_date"]["amount"] == -0.1
    assert result["by_service"] == [
        {"name": "Amazon S3", "amount": 0.75, "currency": "USD", "estimated": False}
    ]
    assert client.requests[2]["NextPageToken"] == "next"


def test_cost_summary_reports_unavailable_when_cost_explorer_fails():
    class DeniedCostExplorer:
        def get_cost_and_usage(self, **_kwargs):
            raise ClientError(
                {"Error": {"Code": "AccessDeniedException", "Message": "Access denied"}},
                "GetCostAndUsage",
            )

    result = get_cost_summary(DeniedCostExplorer(), today=date(2026, 8, 29))

    assert result["status"] == "unavailable"
    assert result["month_to_date"] is None
    assert result["by_service"] == []
