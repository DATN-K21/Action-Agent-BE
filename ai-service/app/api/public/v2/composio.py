# from fastapi import APIRouter, Depends, Query
#
# from app.schemas.base import PagingRequest, ResponseWrapper
# from app.schemas.composio_client import (
#     FilterComposioAppEnumsResponse,
#     FilterComposioAppsResponse,
#     GetAllAppsComposioEnumsResponse,
#     GetAllAppsComposioResponse,
#     GetSingleAppComposioResponse,
# )
# from app.services.composio.composio_client import ComposioClient
# from app.services.database.connected_app_service import ConnectedAppService, get_connected_app_service
# from app.services.extensions.deps import get_extension_service_manager
# from app.services.extensions.extension_service_manager import ExtensionServiceManager
#
# router = APIRouter(prefix="/composio", tags=["API-V2 | Composio Client"])
#
#
# # Get all apps
# @router.get("/apps", summary="Get all apps.", response_model=ResponseWrapper[GetAllAppsComposioResponse])
# def get_all_apps(
#     extension_service_manager: ExtensionServiceManager = Depends(get_extension_service_manager),
#     integrated: bool = Query(False),
# ):
#     response = ComposioClient.get_all_apps()
#     if not response.success:
#         return ResponseWrapper.wrap(
#             status=500,
#             message=response.message,
#         ).to_response()
#
#     returned_data = FilterComposioAppsResponse(
#         items=response.items,
#         count=response.count,
#     )
#
#     if integrated:
#         # Filter apps that are integrated with the extension service manager
#         integrated_apps = extension_service_manager.get_all_extension_service_names()
#         returned_data.items = [app for app in returned_data.items if app.key in integrated_apps]
#         returned_data.count = len(returned_data.items)
#
#     return ResponseWrapper.wrap(
#         status=200,
#         message="Get all apps successfully",
#         data=returned_data,
#     ).to_response()
#
#
# @router.get("/{user_id}/apps", summary="Get all apps by user id.", response_model=ResponseWrapper[GetAllAppsComposioResponse])
# async def get_all_apps_by_user(
#     user_id: str,
#     paging: PagingRequest = Depends(),
#     connected_app_service: ConnectedAppService = Depends(get_connected_app_service),
#     extension_service_manager: ExtensionServiceManager = Depends(get_extension_service_manager),
# ):
#     response = ComposioClient.get_all_apps()
#     if not response.success:
#         return ResponseWrapper.wrap(
#             status=500,
#             message=response.message,
#         ).to_response()
#
#     returned_data = FilterComposioAppsResponse(
#         items=response.items,
#         count=response.count,
#     )
#
#     # Filter apps that are integrated with the extension service manager
#     integrated_apps = extension_service_manager.get_all_extension_service_names()
#     returned_data.items = [app for app in returned_data.items if app.key in integrated_apps]
#     returned_data.count = len(returned_data.items)
#
#     # Filter apps that are connected to the extension service manager
#     connected_apps = await connected_app_service.list_connected_apps(user_id=user_id, paging=paging)
#     if connected_apps.data and connected_apps.data.connected_apps:
#         connected_app_names = [app.app_name for app in connected_apps.data.connected_apps]
#
#         returned_data.items = [app for app in returned_data.items if app.key in connected_app_names]
#         returned_data.count = len(returned_data.items)
#     else:
#         # If no connected apps, return empty list
#         returned_data.items = []
#         returned_data.count = 0
#
#     return ResponseWrapper.wrap(
#         status=200,
#         message="Get all apps successfully",
#         data=returned_data,
#     ).to_response()
#
#
# # Get single app
# @router.get("/apps/{app_enum}", summary="Get single app.", response_model=ResponseWrapper[GetSingleAppComposioResponse])
# def get_single_app(app_enum: str):
#     response = ComposioClient.get_single_app(app_enum=app_enum)
#     if not response.success or response.data is None:
#         return ResponseWrapper.wrap(
#             status=500,
#             message=response.message,
#         ).to_response()
#
#     return ResponseWrapper.wrap(
#         status=200,
#         message="Get single app successfully",
#         data=response.data,
#     ).to_response()
#
#
# # Get all app enums
# @router.get("/apps/list/enums", summary="Get all app enums.", response_model=ResponseWrapper[GetAllAppsComposioEnumsResponse])
# def get_all_app_enums():
#     response = ComposioClient.get_all_app_enums()
#     if not response.success:
#         return ResponseWrapper.wrap(
#             status=500,
#             message=response.message,
#         ).to_response()
#
#     returned_data = FilterComposioAppEnumsResponse(
#         items=response.items,
#         count=response.count,
#     )
#
#     return ResponseWrapper.wrap(
#         status=200,
#         message="Get all app enums successfully",
#         data=returned_data,
#     ).to_response()
