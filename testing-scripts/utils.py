from enum import IntEnum
from solana.rpc.async_api import AsyncClient
from solana.publickey import PublicKey
from borsh_construct import CStruct, U8, U64  # type: ignore
from construct import Bytes
import base64
import httpx
from dataclasses import dataclass


async def get_account_info(pubkey: PublicKey | str, schema: CStruct, client: AsyncClient):
    headers = {
        "Content-Type": "application/json",
    }

    json_data = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getAccountInfo",
        "params": [
            str(pubkey),
            {
                "encoding": "base64",
            },
        ],
    }
    async with httpx.AsyncClient() as http_client:
        escrow_account_info = await http_client.post(
            client._provider.endpoint_uri, headers=headers, json=json_data
        )
    while escrow_account_info.json()["result"]["value"] == None:
        async with httpx.AsyncClient() as http_client:
            escrow_account_info = await http_client.post(
                client._provider.endpoint_uri, headers=headers, json=json_data
            )
    data = escrow_account_info.json()["result"]
    if isinstance(data, dict):
        return ESCROW_ACCOUNT_SCHEMA.parse(
            base64.urlsafe_b64decode(data["value"]["data"][0])
        )
    else:
        raise AttributeError(f"Unknown RPC result {data}")


ESCROW_ACCOUNT_SCHEMA = CStruct(
    "is_initialized" / U8,
    "initializer_pubkey" / Bytes(32),
    "temp_token_account_pubkey" / Bytes(32),
    "initializer_token_to_receive_account_pubkey" / Bytes(32),
    "expected_amount" / U64,
)

@dataclass
class EscrowProgramClass:
    is_initialized: int
    initializer_pubkey : bytes
    temp_token_account_pubkey : bytes
    initializer_token_to_receive_account_pubkey : bytes
    expected_amount : int
ESCROW_ACCOUNT_SIZE = 1 + 32 + 32 + 32 + 8


class EscrowInstructions(IntEnum):
    INITIALIZE = 0
    EXCHANGE = 1


payload_schema = CStruct("instruction" / U8, "amount" / U64)


def construct_payload(instruction_variant: EscrowInstructions, key: int):
    return payload_schema.build({"instruction": instruction_variant, "amount": key})


