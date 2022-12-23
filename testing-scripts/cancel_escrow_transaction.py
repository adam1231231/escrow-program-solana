from solana.rpc.async_api import AsyncClient
import json
from solana.rpc.commitment import Confirmed
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta, Transaction
from utils import (
    EscrowProgramClass,
    get_account_info,
    ESCROW_ACCOUNT_SCHEMA,
    cancel_payload,
)
from solders.pubkey import Pubkey  # type: ignore
from spl.token.constants import TOKEN_PROGRAM_ID
import asyncio
from solana.keypair import Keypair
from pprint import pprint as pp


async def cancel_trade():
    client = AsyncClient("http://localhost:8899", commitment=Confirmed)
    keys = json.load(open("keys.json", "r"))
    config = json.load(open("config.json", "r"))
    program_id = PublicKey(config["program_id"])
    initializer_wallet = PublicKey(keys["initializer_wallet"])
    escrow_account = PublicKey(keys["escrow_account"])
    initializer_x_account = PublicKey(keys["initializer_x_account"])
    account_info: EscrowProgramClass = await get_account_info(
        escrow_account, ESCROW_ACCOUNT_SCHEMA, client
    )
    pda_temp_account = Pubkey.from_bytes(account_info.temp_token_account_pubkey)
    pda, _ = PublicKey.find_program_address(
        [bytes("escrow", encoding="utf8")], program_id
    )
    cancel_trade_ix = TransactionInstruction(
        keys=[
            AccountMeta(initializer_wallet, is_signer=True, is_writable=False),
            AccountMeta(PublicKey(pda_temp_account), is_signer=False, is_writable=True),
            AccountMeta(initializer_x_account, is_signer=False, is_writable=True),
            AccountMeta(escrow_account, is_signer=False, is_writable=True),
            AccountMeta(TOKEN_PROGRAM_ID, is_signer=False, is_writable=False),
            AccountMeta(pda, is_signer=False, is_writable=False),
        ],
        program_id=program_id,
        data=cancel_payload.build({"instruction": 2}),
    )

    tx = Transaction().add(cancel_trade_ix)
    tx.sign(
        Keypair.from_secret_key(
            bytes(keys["initializer_wallet_secret"].encode("latin-1"))
        )
    )
    try:
        result = await client.send_transaction(
        tx,
        Keypair.from_secret_key(
            bytes(keys["initializer_wallet_secret"].encode("latin-1"))
        ),
    )
    except Exception as e:
        pp(e)


if __name__ == "__main__":
    asyncio.run(cancel_trade())
