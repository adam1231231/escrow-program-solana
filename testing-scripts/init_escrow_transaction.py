from solana.rpc.async_api import AsyncClient
from solana.rpc.api import Client
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
from utils import (
    get_account_info,
    ESCROW_ACCOUNT_SCHEMA,
    EscrowProgramClass,
    ESCROW_ACCOUNT_SIZE,
    construct_payload,
    EscrowInstructions,
)
from solders.pubkey import Pubkey  # type: ignore


async def init_escrow():
    """
        Create a new escrow account and initialize it with the given parameters.
    """
    client = AsyncClient("http://localhost:8899", commitment=Confirmed)
    with open("keys.json", "r") as read_file:
        keys = json.load(read_file)
    with open("config.json", "r") as read_file:
        config = json.load(read_file)
    program_id = PublicKey(config["program_id"])
    wallet_dab = PublicKey(keys["wallet_dab"])
    dab_x_account = PublicKey(keys["dab_x_account"])
    dab_y_account = PublicKey(keys["dab_y_account"])
    amount_to_send = config["initlizer_expected_ammount"]
    expected_amount = config["taker_expected_ammount"]
    token_x_mint = PublicKey(keys["x_mint"])
    minimum_rent = await client.get_minimum_balance_for_rent_exemption(ACCOUNT_LEN)
    minimum_rent_escrow = await client.get_minimum_balance_for_rent_exemption(
        ESCROW_ACCOUNT_SIZE
    )
    temp_account_x = Keypair()
    temp_account_ix = create_account(
        CreateAccountParams(
            from_pubkey=wallet_dab,
            new_account_pubkey=temp_account_x.public_key,
            lamports=minimum_rent.value,
            space=ACCOUNT_LEN,
            program_id=TOKEN_PROGRAM_ID,
        )
    )
    init_temp_account_ix = initialize_account(
        InitializeAccountParams(
            program_id=TOKEN_PROGRAM_ID,
            mint=token_x_mint,
            owner=wallet_dab,
            account=temp_account_x.public_key,
        )
    )
    transfer_x_token_to_temp_acccount_ix = transfer(
        TransferParams(
            program_id=TOKEN_PROGRAM_ID,
            source=dab_x_account,
            dest=temp_account_x.public_key,
            owner=wallet_dab,
            amount=amount_to_send,
        )
    )
    escrow_keypair = Keypair.generate()
    escrow_account_ix = create_account(
        CreateAccountParams(
            space=ESCROW_ACCOUNT_SIZE,
            new_account_pubkey=escrow_keypair.public_key,
            from_pubkey=wallet_dab,
            program_id=program_id,
            lamports=minimum_rent_escrow.value,
        )
    )
    data_payload = construct_payload(EscrowInstructions.INITIALIZE, expected_amount)
    init_escrow_ix = TransactionInstruction(
        keys=[
            AccountMeta(pubkey=wallet_dab, is_signer=True, is_writable=True),
            AccountMeta(
                pubkey=temp_account_x.public_key, is_signer=False, is_writable=True
            ),
            AccountMeta(pubkey=dab_y_account, is_signer=False, is_writable=False),
            AccountMeta(
                pubkey=escrow_keypair.public_key, is_signer=False, is_writable=True
            ),
            AccountMeta(pubkey=SYSVAR_RENT_PUBKEY, is_signer=False, is_writable=False),
            AccountMeta(pubkey=TOKEN_PROGRAM_ID, is_signer=False, is_writable=False),
        ],
        program_id=program_id,
        data=data_payload,
    )
    transaction = Transaction(fee_payer=wallet_dab).add(
        temp_account_ix,
        init_temp_account_ix,
        transfer_x_token_to_temp_acccount_ix,
        escrow_account_ix,
        init_escrow_ix,
    )
    tx_hash = await client.send_transaction(
        transaction,
        Keypair.from_secret_key(bytes(keys["wallet_dab_secret"].encode("latin-1"))),
        escrow_keypair,
        temp_account_x,
    )
    await client.confirm_transaction(tx_hash.value)
    account_info: EscrowProgramClass = await get_account_info(
        escrow_keypair.public_key, ESCROW_ACCOUNT_SCHEMA, client
    )
    if not account_info.is_initialized:
        raise Exception("Escrow account not initialized")
    # comparing string to string since both aren't the same type, one from solders and the other from solana-py
    elif str(Pubkey.from_bytes(account_info.initializer_pubkey)) != str(wallet_dab):
        raise Exception("initializer_pubkey not initialized with correct wallet")
    elif str(
        Pubkey.from_bytes(account_info.initializer_token_to_receive_account_pubkey)
    ) != str(dab_y_account):
        raise Exception("Escrow account not initialized with correct receiver account")
    elif str(Pubkey.from_bytes(account_info.temp_token_account_pubkey)) != str(
        temp_account_x.public_key
    ):
        raise Exception("Escrow account not initialized with correct temp account")
    elif account_info.expected_amount != expected_amount:
        raise Exception("Escrow account not initialized with correct expected amount")

    print(
        f"✨Escrow successfully initialized. Alice is offering {amount_to_send}X for {expected_amount}Y✨\n`"
    )
    keys["escrow_account"] = str(escrow_keypair.public_key)
    with open("keys.json", "w") as write_file:
        json.dump(keys, write_file)


if __name__ == "__main__":
    asyncio.run(init_escrow())
