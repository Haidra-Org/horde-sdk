import argparse

from loguru import logger

from horde_sdk import ANON_API_KEY
from horde_sdk.ai_horde_api.ai_horde_clients import AIHordeAPISimpleClient
from horde_sdk.ai_horde_api.apimodels import (
    AllWorkersDetailsResponse,
    ModifyWorkerRequest,
    ModifyWorkerResponse,
    SingleWorkerDetailsResponse,
)


def all_workers(
    api_key: str,
    simple_client: AIHordeAPISimpleClient,
    filename: str,
    *,
    worker_name: str | None = None,
) -> None:
    all_workers_response: AllWorkersDetailsResponse

    all_workers_response = simple_client.workers_all_details(worker_name=worker_name, api_key=api_key)

    if worker_name is None:
        logger.info("Getting details for all workers.")
    else:
        logger.info(f"Getting details for worker with name: {worker_name}")

    if all_workers_response is None:
        raise ValueError("No workers returned in the response.")

    logger.info(f"Number of workers: {len(all_workers_response)}")

    with open(filename, "w", encoding="utf-8") as f:
        f.write(all_workers_response.model_dump_json(indent=4))

    logger.info(f"Workers written to {filename}")


def single_worker(
    api_key: str,
    simple_client: AIHordeAPISimpleClient,
    worker_id: str,
    filename: str,
) -> None:
    single_worker_response: SingleWorkerDetailsResponse

    single_worker_response = simple_client.worker_details(worker_id=worker_id, api_key=api_key)

    if single_worker_response is None:
        raise ValueError("No worker returned in the response.")

    logger.info(f"Worker: {single_worker_response}")

    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"{single_worker_response}\n")

    logger.info(f"Worker details written to {filename}")


def single_worker_name(
    api_key: str,
    simple_client: AIHordeAPISimpleClient,
    worker_name: str,
    filename: str,
) -> None:
    single_worker_response: SingleWorkerDetailsResponse

    single_worker_response = simple_client.worker_details_by_name(worker_name=worker_name, api_key=api_key)

    if single_worker_response is None:
        raise ValueError("No worker returned in the response.")

    logger.info(f"Worker: {single_worker_response}")

    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"{single_worker_response}\n")

    logger.info(f"Worker details written to {filename}")


def set_maintenance_mode(
    api_key: str,
    simple_client: AIHordeAPISimpleClient,
    worker_id: str,
    maintenance_mode: bool,
) -> None:
    modify_worker_request = ModifyWorkerRequest(
        apikey=api_key,
        worker_id=worker_id,
        maintenance=maintenance_mode,
    )

    modify_worker_response: ModifyWorkerResponse

    modify_worker_response = simple_client.worker_modify(modify_worker_request)

    if modify_worker_response is None:
        raise ValueError("No worker returned in the response.")

    logger.info(f"Worker: {modify_worker_response}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simple text generation example.")
    parser.add_argument(
        "--apikey",
        "--api-key",
        "--api_key",
        "-k",
        type=str,
        default=ANON_API_KEY,
        help="The API key to use for the request.",
    )
    parser.add_argument(
        "--filename",
        "-f",
        type=str,
        default="workers.txt",
        help="The filename to write the workers to.",
    )

    parser.add_argument(
        "--worker_name",
        "-n",
        type=str,
        help="The worker name to get details for.",
        default=None,
    )

    # Either all or worker_id must be specified.
    group = parser.add_mutually_exclusive_group()

    group.add_argument(
        "--all",
        action="store_true",
        help="Get details for all workers.",
    )

    group.add_argument(
        "--worker_id",
        "-w",
        type=str,
        help="The worker ID to get details for.",
    )

    group2 = parser.add_mutually_exclusive_group()
    group2.add_argument(
        "--maintenance-mode-on",
        "-m",
        action="store_true",
        help="Turn on maintenance mode.",
    )
    group2.add_argument(
        "--maintenance-mode-off",
        "-M",
        action="store_true",
        help="Turn off maintenance mode.",
    )

    args = parser.parse_args()

    # If `all` is specified and a maintenance mode flag is specified, raise an error.
    if args.all and (args.maintenance_mode_on or args.maintenance_mode_off):
        raise ValueError("Cannot specify maintenance mode with `all`.")

    simple_client = AIHordeAPISimpleClient()

    if args.all:
        all_workers(
            api_key=args.apikey,
            simple_client=simple_client,
            filename=args.filename,
        )
    elif args.worker_id:
        if args.maintenance_mode_on:
            set_maintenance_mode(
                api_key=args.apikey,
                simple_client=simple_client,
                worker_id=args.worker_id,
                maintenance_mode=True,
            )
        elif args.maintenance_mode_off:
            set_maintenance_mode(
                api_key=args.apikey,
                simple_client=simple_client,
                worker_id=args.worker_id,
                maintenance_mode=False,
            )
        else:
            single_worker(
                api_key=args.apikey,
                simple_client=simple_client,
                worker_id=args.worker_id,
                filename=args.filename,
            )
    elif args.worker_name:
        single_worker_name(
            api_key=args.apikey,
            simple_client=simple_client,
            filename=args.filename,
            worker_name=args.worker_name,
        )
