from solana.rpc.async_api import AsyncClient
import json
from solana.system_program import create_account, CreateAccountParams
from spl.token.constants import ACCOUNT_LEN, TOKEN_PROGRAM_ID
from solana.publickey import PublicKey
from solana.keypair import Keypair
from spl.token.instructions import (
    initialize_account,
    InitializeAccountParams,
    transfer,
    TransferParams,
)
from solana.transaction import TransactionInstruction, AccountMeta, Transaction
from solana.sysvar import SYSVAR_RENT_PUBKEY
from solana.rpc.commitment import Confirmed
import asyncio
from borsh_construct import CStruct, U64, U8  # type: ignore
from enum import IntEnum
from solders.pubkey import Pubkey  # type: ignore
from utils import (
    get_account_info,
    ESCROW_ACCOUNT_SCHEMA,
    EscrowProgramClass,
    construct_payload,
    EscrowInstructions,
)
from pprint import pprint as pp


async def take_trade():
    client = AsyncClient("http://localhost:8899", commitment=Confirmed)
    keys = json.load(open("keys.json", "r"))
    config = json.load(open("config.json", "r"))
    program_id = PublicKey(config["program_id"])
    amount_to_send = config["taker_expected_ammount"]
    expected_amount = config["initlizer_expected_ammount"]
    taker_wallet = PublicKey(keys["wallet_other_Side"])
    taker_y_account = PublicKey(keys["other_side_x_account"])
    taker_x_account = PublicKey(keys["other_side_x_account"])
    escrow_account = PublicKey(keys["escrow_account"])

    account_info: EscrowProgramClass = await get_account_info(
        escrow_account, ESCROW_ACCOUNT_SCHEMA, client
    )
    initlizer_y_account = Pubkey.from_bytes(
        account_info.initializer_token_to_receive_account_pubkey
    )
    initlizer_wallet = Pubkey.from_bytes(account_info.initializer_pubkey)
    print(initlizer_wallet)
    print(initlizer_y_account)
    temp_token_account = Pubkey.from_bytes(account_info.temp_token_account_pubkey)
    pda, _ = PublicKey.find_program_address([bytes("escrow",encoding="utf8")], program_id)
    print(pda)
    take_trade_ix = TransactionInstruction(
        keys=[
            AccountMeta(taker_wallet, is_signer=True, is_writable=False),
            AccountMeta(taker_y_account, is_signer=False, is_writable=True),
            AccountMeta(taker_x_account, is_signer=False, is_writable=True),
            AccountMeta(PublicKey(temp_token_account), is_signer=False, is_writable=True),
            AccountMeta(PublicKey(initlizer_wallet), is_signer=False, is_writable=True),
            AccountMeta(PublicKey(initlizer_y_account), is_signer=False, is_writable=True),
            AccountMeta(escrow_account, is_signer=False, is_writable=True),
            AccountMeta(TOKEN_PROGRAM_ID, is_signer=False, is_writable=False),
            AccountMeta(pda, is_signer=False, is_writable=False),
        ],
        program_id=program_id,
        data=construct_payload(EscrowInstructions.EXCHANGE, expected_amount),
    )
    taker_keypair = Keypair.from_secret_key(bytes(keys["wallet_other_Side_secret"].encode("latin-1")))
    tx = Transaction().add(take_trade_ix)
    try:
        await client.send_transaction(tx, taker_keypair)
    except Exception as e:
        pp(e)
    print("Trade taken")


if __name__ == "__main__":
    asyncio.run(take_trade())