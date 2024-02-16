import datetime

# import os
import json
import uuid
import lorem
from fastapi import Request, Response

# dictionary of submitted operations keyed on operation ID
# operations = {}

document_analysis_config = {}


async def doc_intelligence_analyze(context, request: Request) -> Response | None:
    global operations
    is_match, path_params = context.is_route_match(
        request=request, path="/formrecognizer/documentModels/{modelId}:analyze", methods=["POST"]
    )
    if not is_match:
        return None

    # Required parameters (modelId, api-version)
    model_id = path_params["modelId"]
    api_version = request.query_params.get("api-version")

    # Get the size of the request body
    content_length = request.headers.get("Content-Length")

    # Optional parameters
    features = request.query_params.get("features")
    locale = request.query_params.get("locale")
    pages = request.query_params.get("pages")
    string_index_type = request.query_params.get("stringIndexType")

    result_id = str(uuid.uuid4())
    # Build the response header
    # TODO - get base address from config to allow for running in ACA/AKS/... (but default to localhost and current port)
    document_analysis_result_location = f"http://localhost:8000/formrecognizer/documentModels/{model_id}/analyzeResults/{result_id}?api-version={api_version}"

    # Set the HTTP response headers.
    headers = {"Operation-Location": document_analysis_result_location}

    # Build a dictionary of values related to the original document analysis request.
    document_analysis_config[result_id] = {
        "model_id": model_id,
        "api_version": api_version,
        "string_index_type": string_index_type,
        "locale": locale,
        "pages": pages,
        "features": features,
        "content_length": int(content_length),
    }

    # Return the response
    return Response(status_code=202, headers=headers)


async def doc_intelligence_analyze_result(context, request: Request) -> Response | None:
    global operations
    is_match, path_params = context.is_route_match(
        request=request,
        path="/formrecognizer/documentModels/{model_id}/analyzeResults/{result_id}",
        methods=["GET"],
    )
    if not is_match:
        return None

    # Get the model ID from the request path
    model_id = path_params["model_id"]

    # Get the api version from the request query parameters
    api_version = request.query_params.get("api-version")

    result_id = path_params["result_id"]
    doc_config = document_analysis_config.get(result_id)
    if not doc_config:
        return Response(status_code=404)
    del document_analysis_config[result_id]  # TODO - should we delete or leave to allow multiple queries of the result?

    # Pass the dictionary of operation values to the get_response function to build the response body.
    response_content = json.dumps(build_result(doc_config), default=datetime_handler)

    # Set the HTTP response headers.
    headers = {
        "Content-Length": f"{len(response_content)}",
        "Content-Type": "application/json; charset=utf-8",
    }

    # Return the response.
    return Response(status_code=200, content=response_content, headers=headers)


def datetime_handler(x):
    if isinstance(x, datetime.datetime):
        # TODO: Is this the right way to format the datetime?
        return x.isoformat(timespec="seconds") + "Z"
    raise TypeError("Unknown type")


def build_result(analyze_result_dict):
    content_length = analyze_result_dict["content_length"]

    # TODO: Determine how to handle the response content length.
    #       For now, just use a fraction of the original content length.
    response_content_length = round(content_length * 0.001)

    content = "".join(lorem.get_word(count=response_content_length))

    # TODO: Should we build a different response based on the model ID?

    # TODO: Vary the pages, words, documents based on the desired response size.

    # Based on https://learn.microsoft.com/en-us/rest/api/aiservices/document-models/get-analyze-result?view=rest-aiservices-2023-07-31&tabs=HTTP,
    # Many fields appear to be optional (likely varying by model), so we can just return a minimal response for now.

    response_body = {
        "status": "succeeded",
        "createdDateTime": datetime.datetime.now(),
        "lastUpdatedDateTime": datetime.datetime.now(),
        "analyzeResult": {
            "apiVersion": analyze_result_dict["api_version"],
            "modelId": analyze_result_dict["model_id"],
            "stringIndexType": analyze_result_dict.get("string_index_type", "textElements"),
            "content": content,
            "keyValuePairs": [],
            "languages": [],
            "paragraphs": [],
            "tables": [],
            "pages": [
                {
                    "angle": 0,
                    "barcodes": [],
                    "formulas": [],
                    "height": 3264,
                    "lines": [
                        {
                            "content": "Contoso",
                            "polygon": [863, 270, 1605, 269, 1605, 412, 863, 416],
                            "spans": [{"offset": 0, "length": 7}],
                        }
                    ],
                    "pageNumber": 1,
                    "selectionMarks": [],
                    "spans": [{"offset": 0, "length": 188}],
                    "unit": "pixel",
                    "width": 2448,
                    "words": [
                        {
                            "content": "Contoso",
                            "polygon": [863, 276, 1572, 274, 1581, 409, 868, 416],
                            "confidence": 0.994,
                            "span": {"offset": 0, "length": 7},
                        }
                    ],
                }
            ],
            "styles": [],
            "documents": [
                {
                    "docType": "receipt.retailMeal",
                    "boundingRegions": [{"pageNumber": 1, "polygon": [0, 0, 2448, 0, 2448, 3264, 0, 3264]}],
                    "fields": {},
                    "confidence": 0.981,
                    "spans": [{"offset": 0, "length": 188}],
                }
            ],
        },
    }

    return response_body
