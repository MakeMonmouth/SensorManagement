import secrets
import string
import random
import requests
import json
import logging
import base64
import binascii

from netaddr import EUI, mac_bare


logger = logging.getLogger(__name__)


def get_ttn_details(device_id=None, app_name=None, auth_token=None):
    auth_token = auth_token

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {auth_token}",
        "Accept": "application/json",
    }

    ns_field_mask = "ids.device_id,ids.dev_eui,ids.join_eui"
    ns_uri = f"https://eu1.cloud.thethings.network/api/v3/ns/applications/{app_name}/devices/{device_id}?field_mask={ns_field_mask}"

    nsresponse = requests.get(
        ns_uri,
        headers=headers,
    )

    as_field_mask = "ids.device_id,ids.dev_eui,ids.join_eui"
    as_uri = f"https://eu1.cloud.thethings.network/api/v3/as/applications/{app_name}/devices/{device_id}?field_mask={as_field_mask}"

    asresponse = requests.get(
        as_uri,
        headers=headers,
    )

    js_field_mask = "ids.device_id,ids.dev_eui,ids.join_eui,root_keys.app_key.key,root_keys.nwk_key.key"
    js_uri = f"https://eu1.cloud.thethings.network/api/v3/js/applications/{app_name}/devices/{device_id}?field_mask={js_field_mask}"

    jsresponse = requests.get(
        js_uri,
        headers=headers,
    )

    if nsresponse.status_code == 200:
        logger.info("Network server returned a response, compiling data...")
        rj = nsresponse.json()
        aj = asresponse.json()
        jj = jsresponse.json()

        logger.info(f"Name Server: {json.dumps(rj, indent=2)}")
        logger.info(f"App Server: {json.dumps(aj, indent=2)}")
        logger.info(f"Join Server: {json.dumps(jj, indent=2)}")

        chunk_size = 2
        response_dev_eui = jj["ids"]["dev_eui"]
        dev_eui = [
            response_dev_eui[i : i + chunk_size]
            for i in range(0, len(response_dev_eui), chunk_size)
        ]
        response_app_eui = "0000000000000000"
        app_eui = [
            response_app_eui[i : i + chunk_size]
            for i in range(0, len(response_app_eui), chunk_size)
        ]
        response_app_key = jj["root_keys"]["app_key"]["key"]
        app_key = [
            response_app_key[i : i + chunk_size]
            for i in range(0, len(response_app_key), chunk_size)
        ]

        return {
            "dev_eui": response_dev_eui,
            "app_key": response_app_key,
            "app_eui": response_app_eui,
        }
    else:
        logger.info(f"Error: {nsresponse.status_code}")
        print(nsresponse.json())
        print(asresponse.json())
        print(jsresponse.json())
        return {"error": nsresponse.status_code}


def ttn_registration(
    device_mac=None, device_name=None, app_name=None, app_key=None, auth_token=None
):

    if device_name is None:
        return 1
    if device_mac is None:
        return 2
    if app_name is None:
        return 3
    if app_key is None:
        return 4

    app_name = app_name
    app_key = app_key

    padding = "".join(random.choice(string.digits) for i in range(4))
    dev_eui = f"{device_mac}" # {padding}"
    join_eui = "0000000000000000"
    device_id = device_name
    device_name = device_name

    logger.info(f"DevEUI: {dev_eui} - DevID: {device_id}")

    auth_token = auth_token

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {auth_token}",
        "Accept": "application/json",
    }

    create_device = {
        "end_device": {
            "name": f"{device_id}",
            "ids": {
                "device_id": f"{device_id}",
                "dev_eui": f"{dev_eui}",
                "join_eui": f"{join_eui}",
                "application_ids": {"application_id": f"{app_name}"},
            },
            "version_ids": {
                "brand_id": "heltec",
                "model_id": "wifi-lora-32-class-a-abp",
                "hardware_version": "_unknown_hw_version_",
                "firmware_version": "1.0",
                "band_id": "EU_863_870",
            },
            "join_server_address": "eu1.cloud.thethings.network",
            "network_server_address": "eu1.cloud.thethings.network",
            "application_server_address": "eu1.cloud.thethings.network",
        },
        "field_mask": {
            "paths": [
                "join_server_address",
                "network_server_address",
                "application_server_address",
                "version_ids.brand_id",
                "version_ids.model_id",
                "version_ids.hardware_version",
                "version_ids.firmware_version",
                "version_ids.band_id",
            ]
        },
    }

    logger.info(f"Device Creation: {create_device}")

    register_name_server = {
        "end_device": {
            "frequency_plan_id": "EU_863_870_TTN",
            "lorawan_phy_version": "PHY_V1_0",
            "supports_join": True,
            "lorawan_version": "MAC_V1_0",
            "ids": {
                "device_id": f"{device_id}",
                "dev_eui": f"{dev_eui}",
                "join_eui": f"{join_eui}",
            },
            "version_ids": {
                "brand_id": "heltec",
                "model_id": "wifi-lora-32-class-a-abp",
                "hardware_version": "_unknown_hw_version_",
                "firmware_version": "1.0",
                "band_id": "EU_863_870",
            },
            "supports_class_c": False,
            "supports_class_b": False,
            "mac_settings": {
                "rx2_data_rate_index": 0,
                "rx2_frequency": 869525000,
                "rx1_delay": 1,
                "rx1_data_rate_offset": 0,
                "resets_f_cnt": False,
            },
        },
        "field_mask": {
            "paths": [
                "supports_join",
                "lorawan_version",
                "ids.device_id",
                "ids.dev_eui",
                "ids.join_eui",
                "ids.application_ids.application_id",
                "frequency_plan_id",
                "version_ids.brand_id",
                "version_ids.model_id",
                "version_ids.hardware_version",
                "version_ids.firmware_version",
                "version_ids.band_id",
                "lorawan_phy_version",
                "mac_settings.class_c_timeout",
                "mac_settings.supports_32_bit_f_cnt",
            ]
        },
    }

    logger.info(f"Nameserver Registration: {register_name_server}")
    register_application_server = {
        "end_device": {
            "ids": {
                "device_id": f"{device_id}",
                "dev_eui": f"{dev_eui}",
                "join_eui": f"{join_eui}",
            },
            "version_ids": {
                "brand_id": "heltec",
                "model_id": "wifi-lora-32-class-a-abp",
                "hardware_version": "_unknown_hw_version_",
                "firmware_version": "1.0",
                "band_id": "EU_863_870",
            },
        },
        "root_keys": {"app_key": {"key": f"{app_key}"}},
        "field_mask": {
            "paths": [
                "ids.device_id",
                "ids.dev_eui",
                "ids.join_eui",
                "ids.application_ids.application_id",
                "version_ids.brand_id",
                "version_ids.model_id",
                "version_ids.hardware_version",
                "version_ids.firmware_version",
                "version_ids.band_id",
            ]
        },
    }
    logger.info(f"AppServer Registration: {register_application_server}")

    register_join_server = {
        "end_device": {
            "ids": {
                "device_id": f"{device_id}",
                "dev_eui": f"{dev_eui}",
                "join_eui": f"{join_eui}",
                "application_ids": {"application_id": f"{app_name}"},
            },
            "network_server_address": "eu1.cloud.thethings.network",
            "application_server_address": "eu1.cloud.thethings.network",
            "root_keys": {"app_key": {"key": f"{app_key}"}},
        },
        "field_mask": {
            "paths": [
                "network_server_address",
                "application_server_address",
                "root_keys.app_key.key",
                "ids.device_id",
                "ids.dev_eui",
                "ids.join_eui",
                "ids.application_ids.application_id",
            ]
        },
    }
    logger.info(f"JoinServer Registration: {register_join_server}")

    # try:
    create_device_response = requests.post(
        f"https://eu1.cloud.thethings.network/api/v3/applications/{app_name}/devices",
        data=json.dumps(create_device),
        headers=headers,
    )

    if create_device_response.status_code == 200:
        logger.info("Device Creation Successful, moving on to Name Server Registration")
        register_name_response = requests.put(
            f"https://eu1.cloud.thethings.network/api/v3/ns/applications/{app_name}/devices/{device_id}",
            data=json.dumps(register_name_server),
            headers=headers,
        )
    else:
        print("Device Creation Failed")
        print(create_device_response.json())

    if register_name_response.status_code == 200:
        logger.info(
            "Name Server Registration Successful, moving on to Application Server Registration"
        )
        register_app_response = requests.put(
            f"https://eu1.cloud.thethings.network/api/v3/as/applications/{app_name}/devices/{device_id}",
            data=json.dumps(register_application_server),
            headers=headers,
        )
    else:
        print("Name Server Registration Failed")
        print(register_name_response.json())

    if register_app_response.status_code == 200:
        logger.info(
            "Application Server Registration Successful, moving on to Join Server Registration"
        )
        register_join_response = requests.put(
            f"https://eu1.cloud.thethings.network/api/v3/js/applications/{app_name}/devices/{device_id}",
            data=json.dumps(register_join_server),
            headers=headers,
        )
    else:
        print("App Server Registration Failed")
        print(register_app_response.json())

    if register_join_response and register_join_response.status_code == 200:
        logger.info("Join Server Registration Successful, returning data")
        return get_ttn_details(device_id, app_name, auth_token)
    else:
        logger.info("Join Server Registration failed")
        logger.info(register_join_response.json())

    # except:
    #    return {"error": "Registration failed"}
