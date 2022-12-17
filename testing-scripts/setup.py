import asyncio
from datetime import datetime
import time
from solana.rpc.api import Client
from solana.rpc.async_api import AsyncClient
from solana.transaction import TransactionInstruction, Transaction, AccountMeta
from solana.keypair import Keypair
from solana.publickey import PublicKey
from spl.token.client import Token
from solana.sysvar import SYSVAR_RENT_PUBKEY
from spl.token.constants import TOKEN_PROGRAM_ID
from solana.rpc.commitment import Confirmed, Finalized
from spl.token.client import Token as spl_client
from spl.token.async_client import AsyncToken
from mnemonic import Mnemonic
from solana.system_program import CreateAccountParams, create_account, SYS_PROGRAM_ID
import json
from pprint import pprint as pp
from solders.signature import Signature


client = AsyncClient("http://localhost:8899", commitment=Confirmed)
sync_client = Client("http://localhost:8899",)


program_id = "8vkMxzM5P6fMXpVL9ZdTYpcyR7BuM4EnzxfYw2k9pCAg"


#creating 2 wallets and 2 tokens for the transaction, all is saved in the keys.json file
async def setup():
    start = datetime.now()
    keys = {}
    print("---generating wallets---")
    wallet_dab = Keypair.generate()
    wallet_other_Side = Keypair.generate()
    keys["wallet_dab"] = str(wallet_dab.public_key)
    keys["wallet_other_Side"] = str(wallet_other_Side.public_key)
    keys["wallet_dab_secret"] = wallet_dab.secret_key.decode("latin-1")
    keys["wallet_other_Side_secret"] = wallet_other_Side.secret_key.decode("latin-1")
    print("---requesting airdrop---")
    await client.request_airdrop(wallet_other_Side.public_key, 1 *
                           10**8, commitment=Confirmed)
    airdrop1 = await client.request_airdrop(wallet_dab.public_key,
                           10*10**9, commitment=Confirmed)
    # sometimes localhost doesn't airdrop immediately, so wait for transaction to be confirmed
    while sync_client.get_transaction(airdrop1.value).value == None:
        time.sleep(1)
    print("---creating x mint and accounts---")
    mint_x = await AsyncToken.create_mint(conn=client, payer=wallet_dab, decimals=9, mint_authority=wallet_dab.public_key,
                               freeze_authority=None, program_id=TOKEN_PROGRAM_ID)
    print(mint_x.program_id)
    print(mint_x.pubkey)
    keys["x_mint"] = str(mint_x.pubkey)
    dab_x_account = await  mint_x.create_account(wallet_dab.public_key)
    keys["dab_x_account"] = str(dab_x_account)
    other_side_x_account = await mint_x.create_account(wallet_other_Side.public_key)
    keys["other_side_x_account"] = str(other_side_x_account)
    await mint_x.mint_to(dab_x_account,
                   mint_authority=wallet_dab, amount=50000000000)
    print("---creating y mint and accounts---")
    mint_y = await AsyncToken.create_mint(conn=client, payer=wallet_other_Side, decimals=9,
                            mint_authority=wallet_other_Side.public_key, program_id=TOKEN_PROGRAM_ID)
    keys["y_mint"] = str(mint_y.pubkey)
    dab_y_account = await mint_y.create_account(wallet_dab.public_key)
    keys["dab_y_account"] = str(dab_y_account)
    other_side_y_account = await mint_y.create_account(wallet_other_Side.public_key)
    keys["other_side_y_account"] = str(other_side_y_account)
    await mint_y.mint_to(other_side_y_account,
                   mint_authority=wallet_other_Side, amount=50000000000)
    print("---saving json to keys")
    insertion1 = json.dumps(keys, indent=4, sort_keys=False, default=str)

    with open("keys.json", "w") as outfile:
        json.dump(keys, outfile)
    print("end_Time = ", datetime.now() - start)


# runnning this function as async is upto 40% faster than sync, despite having 1 blocking call
asyncio.run(setup())

