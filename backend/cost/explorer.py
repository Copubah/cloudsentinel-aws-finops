"""Read-only AWS Cost Explorer queries used by CloudSentinel."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError


COST_METRIC = "NetUnblendedCost"
FORECAST_METRIC = "NET_UNBLENDED_COST"
CURRENCY = "USD"


def _money(value: str | None) -> float:
    """Return a JSON-safe monetary amount without binary float artifacts."""
    try:
        return float(Decimal(value or "0").quantize(Decimal("0.000001")))
    except (InvalidOperation, ValueError):
        return 0.0


def _period(today: date) -> dict[str, str]:
    """Build a month-to-date Cost Explorer period; End is exclusive."""
    return {
        "Start": today.replace(day=1).isoformat(),
        "End": (today + timedelta(days=1)).isoformat(),
    }


def _forecast_period(today: date) -> dict[str, str]:
    """Forecast from today through the end of the current month."""
    next_month = (today.replace(day=28) + timedelta(days=4)).replace(day=1)
    return {"Start": today.isoformat(), "End": next_month.isoformat()}


def _results_by_time(
    client: Any,
    *,
    time_period: dict[str, str],
    granularity: str,
    group_by: list[dict[str, str]] | None = None,
) -> list[dict[str, Any]]:
    """Request every page of a Cost Explorer query."""
    request: dict[str, Any] = {
        "TimePeriod": time_period,
        "Granularity": granularity,
        "Metrics": [COST_METRIC],
    }
    if group_by:
        request["GroupBy"] = group_by

    results: list[dict[str, Any]] = []
    next_page_token: str | None = None
    while True:
        if next_page_token:
            request["NextPageToken"] = next_page_token

        response = client.get_cost_and_usage(**request)
        results.extend(response.get("ResultsByTime", []))
        next_page_token = response.get("NextPageToken")
        if not next_page_token:
            return results


def _amount(group: dict[str, Any]) -> tuple[float, str]:
    metrics = group.get("Metrics", group)
    metric = metrics.get(COST_METRIC, {})
    return _money(metric.get("Amount")), metric.get("Unit", CURRENCY)


def _grouped_costs(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize grouped Cost Explorer results and combine paginated totals."""
    totals: dict[str, Decimal] = {}
    currency_by_key: dict[str, str] = {}
    estimated_by_key: dict[str, bool] = {}

    for result in results:
        for group in result.get("Groups", []):
            key = group.get("Keys", ["Uncategorized"])[0]
            amount, currency = _amount(group)
            totals[key] = totals.get(key, Decimal("0")) + Decimal(str(amount))
            currency_by_key[key] = currency
            estimated_by_key[key] = estimated_by_key.get(key, False) or bool(
                result.get("Estimated", False)
            )

    return [
        {
            "name": name,
            "amount": float(amount.quantize(Decimal("0.000001"))),
            "currency": currency_by_key[name],
            "estimated": estimated_by_key[name],
        }
        for name, amount in sorted(totals.items(), key=lambda item: item[1], reverse=True)
    ]


def _daily_trend(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    trend = []
    for result in results:
        amount, currency = _amount(result.get("Total", {}))
        trend.append(
            {
                "date": result.get("TimePeriod", {}).get("Start"),
                "amount": amount,
                "currency": currency,
                "estimated": bool(result.get("Estimated", False)),
            }
        )
    return trend


def _forecast(client: Any, today: date) -> dict[str, Any]:
    """Retrieve a best-effort remaining-month forecast without masking costs."""
    time_period = _forecast_period(today)
    try:
        response = client.get_cost_forecast(
            TimePeriod=time_period,
            Metric=FORECAST_METRIC,
            Granularity="DAILY",
            PredictionIntervalLevel=80,
        )
    except (AttributeError, BotoCoreError, ClientError, KeyError, TypeError) as error:
        return {"status": "unavailable", "time_period": time_period, "error": str(error)}

    total = response.get("Total", {})
    return {
        "status": "available",
        "time_period": time_period,
        "total": {
            "amount": _money(total.get("Amount")),
            "currency": total.get("Unit", CURRENCY),
        },
        "daily": [
            {
                "date": item.get("TimePeriod", {}).get("Start"),
                "amount": _money(item.get("MeanValue")),
                "lower_bound": _money(item.get("PredictionIntervalLowerBound")),
                "upper_bound": _money(item.get("PredictionIntervalUpperBound")),
            }
            for item in response.get("ForecastResultsByTime", [])
        ],
    }


def get_cost_summary(
    client: Any | None = None, *, today: date | None = None
) -> dict[str, Any]:
    """Retrieve account-level month-to-date Cost Explorer data.

    Costs are account and service level only. The result intentionally makes no
    claim that a service-level cost belongs to an individual resource.
    """
    today = today or date.today()
    time_period = _period(today)
    client = client or boto3.client("ce", region_name="us-east-1")

    try:
        total_results = _results_by_time(
            client, time_period=time_period, granularity="MONTHLY"
        )
        service_results = _results_by_time(
            client,
            time_period=time_period,
            granularity="MONTHLY",
            group_by=[{"Type": "DIMENSION", "Key": "SERVICE"}],
        )
        usage_type_results = _results_by_time(
            client,
            time_period=time_period,
            granularity="MONTHLY",
            group_by=[{"Type": "DIMENSION", "Key": "USAGE_TYPE"}],
        )
        daily_results = _results_by_time(
            client, time_period=time_period, granularity="DAILY"
        )
    except (BotoCoreError, ClientError, KeyError, TypeError) as error:
        return {
            "status": "unavailable",
            "time_period": time_period,
            "error": str(error),
            "month_to_date": None,
            "by_service": [],
            "by_usage_type": [],
            "daily_trend": [],
            "attribution": "account-level only",
        }

    total = total_results[-1] if total_results else {}
    amount, currency = _amount(total.get("Total", {}))
    return {
        "status": "available",
        "time_period": time_period,
        "month_to_date": {
            "amount": amount,
            "currency": currency,
            "estimated": bool(total.get("Estimated", False)),
        },
        "by_service": _grouped_costs(service_results),
        "by_usage_type": _grouped_costs(usage_type_results),
        "daily_trend": _daily_trend(daily_results),
        "forecast": _forecast(client, today),
        "attribution": "account-level only",
    }
