from solana.rpc.async_api import AsyncClient
import json
from spl.token.constants import  TOKEN_PROGRAM_ID
from solana.publickey import PublicKey
from solana.keypair import Keypair
from solana.transaction import TransactionInstruction, AccountMeta, Transaction
from solana.rpc.commitment import Confirmed
import asyncio
from solders.pubkey import Pubkey  # type: ignore
from utils import (
    get_account_info,
    ESCROW_ACCOUNT_SCHEMA,
    EscrowProgramClass,
    construct_payload,
    EscrowInstructions,
)
from pprint import pprint as pp
from tabulate import tabulate


async def take_trade():
    client = AsyncClient("http://localhost:8899", commitment=Confirmed)
    keys = json.load(open("keys.json", "r"))
    config = json.load(open("config.json", "r"))
    program_id = PublicKey(config["program_id"])
    expected_amount = config["initlizer_expected_ammount"]
    taker_wallet = PublicKey(keys["taker_wallet"])
    taker_y_account = PublicKey(keys["taker_y_account"])
    taker_x_account = PublicKey(keys["taker_x_account"])
    escrow_account = PublicKey(keys["escrow_account"])
    initlizer_x_account = PublicKey(keys["initializer_x_account"])

    account_info: EscrowProgramClass = await get_account_info(
        escrow_account, ESCROW_ACCOUNT_SCHEMA, client
    )
    initlizer_y_account = Pubkey.from_bytes(
        account_info.initializer_token_to_receive_account_pubkey
    )
    initlizer_wallet = Pubkey.from_bytes(account_info.initializer_pubkey)
    temp_token_account = Pubkey.from_bytes(account_info.temp_token_account_pubkey)
    pda, _ = PublicKey.find_program_address(
        [bytes("escrow", encoding="utf8")], program_id
    )
    take_trade_ix = TransactionInstruction(
        keys=[
            AccountMeta(taker_wallet, is_signer=True, is_writable=False),
            AccountMeta(taker_y_account, is_signer=False, is_writable=True),
            AccountMeta(taker_x_account, is_signer=False, is_writable=True),
            AccountMeta(
                PublicKey(temp_token_account), is_signer=False, is_writable=True
            ),
            AccountMeta(PublicKey(initlizer_wallet), is_signer=False, is_writable=True),
            AccountMeta(
                PublicKey(initlizer_y_account), is_signer=False, is_writable=True
            ),
            AccountMeta(escrow_account, is_signer=False, is_writable=True),
            AccountMeta(TOKEN_PROGRAM_ID, is_signer=False, is_writable=False),
            AccountMeta(pda, is_signer=False, is_writable=False),
        ],
        program_id=program_id,
        data=construct_payload(EscrowInstructions.EXCHANGE, expected_amount),
    )
    taker_keypair = Keypair.from_secret_key(
        bytes(keys["taker_wallet_secret"].encode("latin-1"))
    )
    tx = Transaction().add(take_trade_ix)

    transaction = await client.send_transaction(tx, taker_keypair)
    await client.confirm_transaction(transaction.value)
    data= [[(await client.get_token_account_balance(initlizer_x_account)).value.amount,
    (await client.get_token_account_balance(PublicKey(initlizer_y_account))).value.amount,
    (await client.get_token_account_balance(taker_x_account)).value.amount,
    (await client.get_token_account_balance(taker_y_account)).value.amount]]

    print(tabulate(data,headers=["initlizer x account", "initlizer y account", "taker x account", "taker y account"]))
    print("✨Trade successfully executed. All temporary accounts closed✨\n")


if __name__ == "__main__":
    asyncio.run(take_trade())
