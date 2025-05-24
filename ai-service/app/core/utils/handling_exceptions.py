from logging import Logger
from sqlite3 import DataError as SQLiteDataError
from sqlite3 import IntegrityError as SQLiteIntegrityError
from sqlite3 import OperationalError as SQLiteOperationalError

from composio.client.exceptions import ComposioClientError, HTTPError
from composio.exceptions import ApiKeyNotProvidedError, ComposioSDKError
from langchain_core.exceptions import LangChainException
from langgraph.errors import EmptyInputError, GraphRecursionError, InvalidUpdateError
from openai import APIError as OpenAIAPIError
from openai import RateLimitError as OpenAIRateLimitError
from psycopg.errors import ConnectionTimeout as PsycopgConnectionTimeout
from psycopg.errors import DataError as PsycopgDataError
from psycopg.errors import IntegrityError as PsycopgIntegrityError
from psycopg.errors import OperationalError as PsycopgOperationalError
from sqlalchemy.exc import DataError as SQLAlchemyDataError
from sqlalchemy.exc import DisconnectionError as SQLAlchemyDisconnectionError
from sqlalchemy.exc import IntegrityError as SQLAlchemyIntegrityError
from sqlalchemy.exc import InvalidRequestError as SQLAlchemyInvalidRequestError
from sqlalchemy.exc import OperationalError as SQLAlchemyOperationalError

from app.schemas.base import ResponseWrapper


def handle_exceptions(logger: Logger, exc: Exception):
    if (
            isinstance(exc, SQLAlchemyIntegrityError)
            or isinstance(exec, PsycopgIntegrityError)
            or isinstance(exec, SQLiteIntegrityError)
    ):
        logger.error("Request data violates a database constraint.", exc_info=exc)
        return ResponseWrapper.wrap(
            status=400,
            message=f"Request data violates a database constraint: {str(exc)}",
        ).to_response()

    if (
            isinstance(exec, SQLAlchemyOperationalError)
            or isinstance(exec, PsycopgOperationalError)
            or isinstance(exec, SQLiteOperationalError)
    ):
        logger.error("Database connection issues or operational errors.", exc_info=exc)
        return ResponseWrapper.wrap(
            status=503,
            message=f"Database connection issues or operational errors: {str(exc)}",
        ).to_response()

    if isinstance(exc, SQLAlchemyDataError) or isinstance(exc, PsycopgDataError) or isinstance(exc, SQLiteDataError):
        logger.error("Invalid data (e.g., numeric value exceeds column limit).", exc_info=exc)
        return ResponseWrapper.wrap(
            status=422,
            message=f"Invalid data (e.g., numeric value exceeds column limit): {str(exc)}",
        ).to_response()

    if isinstance(exc, SQLAlchemyInvalidRequestError):
        logger.error(
            "Inconsistent state or invalid request for query construction.",
            exc_info=exc,
        )
        return ResponseWrapper.wrap(
            status=400,
            message=f"Inconsistent state or invalid request for query construction: {str(exc)}",
        ).to_response()

    if isinstance(exc, SQLAlchemyDisconnectionError):
        logger.error("Database disconnection during operation", exc_info=exc)
        return ResponseWrapper.wrap(status=503,
                                    message=f"Database disconnection during operation: {str(exc)}").to_response()

    if isinstance(exc, TimeoutError):
        logger.error("A timeout occurred during execution.", exc_info=exc)
        return ResponseWrapper.wrap(status=504,
                                    message=f"A timeout occurred during execution: {str(exc)}").to_response()

    if isinstance(exc, ConnectionError):
        logger.error("A connection error occurred during execution.", exc_info=exc)
        return ResponseWrapper.wrap(
            status=503,
            message=f"A connection error occurred during execution: {str(exc)}",
        ).to_response()

    if isinstance(exc, PsycopgConnectionTimeout):
        logger.error("A connection timeout occurred during execution.", exc_info=exc)
        return ResponseWrapper.wrap(
            status=522,
            message=f"A connection timeout occurred during execution: {str(exc)}",
        ).to_response()

    if isinstance(exc, GraphRecursionError):
        logger.error(
            "The graph has surpassed the maximum number of execution steps.",
            exc_info=exc,
        )
        return ResponseWrapper.wrap(
            status=500,
            message=f"The graph has surpassed the maximum number of execution steps: {str(exc)}",
        ).to_response()

    if isinstance(exc, InvalidUpdateError):
        logger.error(
            "Attempted to update the channel with an invalid sequence of updates.",
            exc_info=exc,
        )
        return ResponseWrapper.wrap(
            status=400,
            message=f"Attempted to update the channel with an invalid sequence of updates: {str(exc)}",
        ).to_response()

    if isinstance(exc, EmptyInputError):
        logger.error("The graph received an empty input.", exc_info=exc)
        return ResponseWrapper.wrap(status=400, message=f"The graph received an empty input: {str(exc)}").to_response()

    if isinstance(exc, LangChainException):
        logger.error("An unknown error that is related to the Langchain occurred .", exc_info=exc)
        return ResponseWrapper.wrap(
            status=500,
            message=f"An unknown error that is related to the Langchain occurred: {str(exc)}",
        ).to_response()

    if isinstance(exc, OpenAIRateLimitError):
        logger.error("The request has exceeded the rate limit.", exc_info=exc)
        return ResponseWrapper.wrap(status=429,
                                    message=f"The request has exceeded the rate limit: {str(exc)}").to_response()

    if isinstance(exc, OpenAIAPIError):
        logger.error("An error occurred during the OpenAI API request.", exc_info=exc)
        return ResponseWrapper.wrap(
            status=500,
            message=f"An error occurred during the OpenAI API request: {str(exc)}",
        ).to_response()

    if isinstance(exc, ApiKeyNotProvidedError):
        logger.error("The composio API key is not provided.", exc_info=exc)
        return ResponseWrapper.wrap(status=401,
                                    message=f"The composio API key is not provided: {str(exc)}").to_response()

    if isinstance(exc, ComposioSDKError):
        logger.error("An error occurred within the Composio SDK.", exc_info=exc)
        return ResponseWrapper.wrap(status=500,
                                    message=f"An error occurred within the Composio SDK: {str(exc)}").to_response()

    if isinstance(exc, ComposioClientError):
        logger.error("An error occurred in the Composio client.", exc_info=exc)
        return ResponseWrapper.wrap(status=400,
                                    message=f"An error occurred in the Composio client: {str(exc)}").to_response()

    if isinstance(exc, HTTPError):
        logger.error("An HTTP error that is related to the Composio occurred.", exc_info=exc)
        return ResponseWrapper.wrap(
            status=exc.status_code,
            message=f"An HTTP error that is related to the Composio occurred: {str(exc)}",
        ).to_response()

    if isinstance(exc, Exception):
        logger.error("An unknown error occurred.", exc_info=exc)
        return ResponseWrapper.wrap(status=500, message=f"An unknown error occurred: {str(exc)}").to_response()
