import logfire

_telemetry_client_critical_errors_counter = logfire.metric_counter(
    "client_critical_errors",
    unit="1",
    description="The number of critical error for which there is no special handling",
)

_telemetry_client_horde_api_errors_counter = logfire.metric_counter(
    "client_horde_api_errors",
    unit="1",
    description="The number of API errors",
)

_telemetry_client_requests_started_counter = logfire.metric_counter(
    "client_requests_started",
    unit="1",
    description="The number of requests started",
)

_telemetry_client_requests_finished_successfully_counter = logfire.metric_counter(
    "client_requests_finished_successfully",
    unit="1",
    description="The number of requests finished",
)


__all__ = [
    "_telemetry_client_critical_errors_counter",
    "_telemetry_client_horde_api_errors_counter",
    "_telemetry_client_requests_started_counter",
    "_telemetry_client_requests_finished_successfully_counter",
]
