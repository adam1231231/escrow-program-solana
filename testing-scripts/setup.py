import asyncio
from datetime import datetime
import time
from solana.rpc.api import Client
from solana.rpc.async_api import AsyncClient
from solana.keypair import Keypair
from spl.token.constants import TOKEN_PROGRAM_ID
from spl.token.async_client import AsyncToken
import json
from tabulate import tabulate
from solana.rpc.commitment import Confirmed


client = AsyncClient("http://localhost:8899", commitment=Confirmed)
sync_client = Client("http://localhost:8899",)


program_id = "8vkMxzM5P6fMXpVL9ZdTYpcyR7BuM4EnzxfYw2k9pCAg"


#creating 2 wallets and 2 tokens for the transaction, all is saved in the keys.json file
async def setup():
    start = datetime.now()
    keys = {}
    print("---generating wallets---")
    initializer_wallet = Keypair.generate()
    taker_wallet = Keypair.generate()
    keys["initializer_wallet"] = str(initializer_wallet.public_key)
    keys["taker_wallet"] = str(taker_wallet.public_key)
    keys["initializer_wallet_secret"] = initializer_wallet.secret_key.decode("latin-1")
    keys["taker_wallet_secret"] = taker_wallet.secret_key.decode("latin-1")
    print("---requesting airdrop---")
    await client.request_airdrop(taker_wallet.public_key, 1 *
                           10**8, commitment=Confirmed)
    airdrop1 = await client.request_airdrop(initializer_wallet.public_key,
                           10*10**9, commitment=Confirmed)
    # sometimes localhost doesn't airdrop immediately, so wait for transaction to be confirmed
    while sync_client.get_transaction(airdrop1.value).value == None:
        time.sleep(1)
    print("---creating x mint and accounts---")
    mint_x = await AsyncToken.create_mint(conn=client, payer=initializer_wallet, decimals=9, mint_authority=initializer_wallet.public_key,
                               freeze_authority=None, program_id=TOKEN_PROGRAM_ID)
    keys["x_mint"] = str(mint_x.pubkey)
    initializer_x_account = await  mint_x.create_account(initializer_wallet.public_key)
    keys["initializer_x_account"] = str(initializer_x_account)
    taker_x_account = await mint_x.create_account(taker_wallet.public_key)
    keys["taker_x_account"] = str(taker_x_account)
    await mint_x.mint_to(initializer_x_account,
                   mint_authority=initializer_wallet, amount=500)
    print("---creating y mint and accounts---")
    mint_y = await AsyncToken.create_mint(conn=client, payer=taker_wallet, decimals=9,
                            mint_authority=taker_wallet.public_key, program_id=TOKEN_PROGRAM_ID)
    keys["y_mint"] = str(mint_y.pubkey)
    initializer_y_account = await mint_y.create_account(initializer_wallet.public_key)
    keys["initializer_y_account"] = str(initializer_y_account)
    taker_y_account = await mint_y.create_account(taker_wallet.public_key)
    keys["taker_y_account"] = str(taker_y_account)
    mint_y = await mint_y.mint_to(taker_y_account,
                   mint_authority=taker_wallet, amount=500)
    await client.confirm_transaction(mint_y.value)
    print("---saving json to keys")
    with open("keys.json", "w") as outfile:
        json.dump(keys, outfile)
    data= [[(await client.get_token_account_balance(initializer_x_account)).value.amount,
    (await client.get_token_account_balance(initializer_y_account)).value.amount,
    (await client.get_token_account_balance(taker_x_account)).value.amount,
    (await client.get_token_account_balance(taker_y_account)).value.amount]]

    print(tabulate(data,headers=["initlizer x account", "initlizer y account", "taker x account", "taker y account"]))
    print("end_Time = ", datetime.now() - start)


# runnning this function as async is upto 40% faster than sync, despite having 1 blocking call
asyncio.run(setup())

