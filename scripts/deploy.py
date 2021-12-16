from pathlib import Path

from brownie import Strategy, accounts, config, network, project, web3
from eth_utils import is_checksum_address


API_VERSION = config["dependencies"][0].split("@")[-1]
Vault = project.load(
    Path.home() / ".brownie" / "packages" / config["dependencies"][0]
).Vault


def get_address(msg: str) -> str:
    while True:
        val = input(msg)
        if is_checksum_address(val):
            return val
        else:
            addr = web3.ens.address(val)
            if addr:
                print(f"Found ENS '{val}' [{addr}]")
                return addr
        print(f"I'm sorry, but '{val}' is not a checksummed address or ENS")

def get_src():
    f = open('/home/wavey/ssc.sol', 'w')
    Strategy.get_verification_info()
    f.write(Strategy._flattener.flattened_source)
    f.close()

def deploy_usdt_frax():
    # strategist = accounts.load("dev")
    strategist = accounts[3]
    frax_yvault = "0xB4AdA607B9d6b2c9Ee07A275e9616B84AC560139"
    yvusdt = "0x7Da96a3891Add058AdA2E826306D812C638D87a7"
    frax_pool = "0xd632f22692FaC7611d2AA1C0D552930D43CAEd3B"
    deposit_frax = "0xA79828DF1850E8a3A3064576f380D90aECDD3359"

    strategy = strategist.deploy(
        Strategy, 
        yvusdt, 
        3_000_000*1e18, 
        3600, 
        500, 
        frax_pool, 
        deposit_frax, 
        frax_yvault,
        "ssc_usdt_frax"
    )

    print("STRATEGY DEPLOYED",strategy)
    
def main():
    print(f"You are using the '{network.show_active()}' network")
    dev = accounts.load("dev")
    print(f"You are using: 'dev' [{dev.address}]")

    if input("Is there a Vault for this strategy already? y/[N]: ").lower() != "y":
        vault = Vault.at(get_address("Deployed Vault: "))
        assert vault.apiVersion() == API_VERSION
    else:
        return  # TODO: Deploy one using scripts from Vault project

    print(
        f"""
    Strategy Parameters

       api: {API_VERSION}
     token: {vault.token()}
      name: '{vault.name()}'
    symbol: '{vault.symbol()}'
    """
    )
    if input("Deploy Strategy? y/[N]: ").lower() != "y":
        return

    strategy = Strategy.deploy(vault, {"from": dev})
