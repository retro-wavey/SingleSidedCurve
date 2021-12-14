from itertools import count
from brownie import Wei, reverts, Contract
import eth_abi
from brownie.convert import to_bytes
from useful_methods import genericStateOfStrat,genericStateOfVault
import random, requests
import brownie

# TODO: Add tests here that show the normal operation of this strategy
#       Suggestions to include:
#           - strategy loading and unloading (via Vault addStrategy/revokeStrategy)
#           - change in loading (from low to high and high to low)
#           - strategy operation at different loading levels (anticipated and "extreme")


def make_tenderly_fork(block_number=None):
    fork_base_url = "https://simulate.yearn.network/fork"
    payload = {"network_id": "1"}
    if block_number:
        payload["block_number"] = block_number
    resp = requests.post(fork_base_url, headers={}, json=payload)
    fork_id = resp.json()["simulation_fork"]["id"]
    fork_rpc_url = f"https://rpc.tenderly.co/fork/{fork_id}"
    tenderly_provider = web3.HTTPProvider(fork_rpc_url, {"timeout": 600})
    print("FORK ID", fork_id)
    web3.provider = tenderly_provider
    click.secho(f"https://dashboard.tenderly.co/yearn/yearn-web/fork/{fork_id}", fg='yellow')

def test_frax_fresh_vault(frax, fraxCurvePool,Strategy,strategy_frax,fraxyvault,frax3CRV, rewards,chain,frax_vault, ychad, whale,gov,strategist, interface):
    # make_tenderly_fork()
    vault = frax_vault
    yvault = fraxyvault
    strategy = strategy_frax
    currency = frax
    debt_ratio = 10_000
    vault.addStrategy(strategy, debt_ratio, 0, 2 ** 256 - 1, 1000, {"from": gov})
    vault.setManagementFee(0, {"from": gov})
    vault.setPerformanceFee(0, {"from": gov})

    currency.approve(vault, 2 ** 256 - 1, {"from": whale} )
    print(currency.balanceOf(whale)/10 ** currency.decimals())
    whalebefore = currency.balanceOf(whale)
    whale_deposit  = 100_000 * 10 ** currency.decimals()
    vault.deposit(whale_deposit, {"from": whale})
    strategy.harvest({'from': strategist}) # Invest
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)

    # Setup delegated CRV vault/strat vars
    convex_deposit = Contract("0xF403C135812408BFbE8713b5A23a04b3D48AAE31")
    print("curveid: ", strategy.curveId())
    print("curve token: ", strategy.curveToken())
    print("ytoken: ", strategy.yvToken())
    delegatedStrat1 = Strategy.at(yvault.withdrawalQueue(0))
    delegatedStrat2 = Strategy.at(yvault.withdrawalQueue(1))
    chain.sleep(60*60*24*10) # SLeep 10 days
    chain.mine(1)
    convex_deposit.earmarkRewards(32, {"from": gov})
    tx = delegatedStrat1.harvest({"from": gov})
    tx = delegatedStrat2.harvest({"from": gov})
    print(tx.events["Harvested"])
    chain.sleep(60*60*6)
    chain.mine(1)
    
    tx = strategy.harvest({'from': strategist})
    print("***")
    print(tx.events["Harvested"])
    print("***")
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)

    print("\nEst APR: ", "{:.2%}".format(
            ((vault.totalAssets() - whale_deposit) * 365/2) / (whale_deposit)
        )
    )
    chain.sleep(60*60*24*10) # wait six hours so we get full harvest
    chain.mine(1)
    tx = delegatedStrat2.harvest({"from": gov})
    chain.sleep(60*60*6)
    chain.mine(1)
    vault.updateStrategyDebtRatio(strategy, 0 , {"from": gov})
    tx = strategy.harvest({'from': strategist})
    vault.withdraw(vault.balanceOf(whale), whale, 100, {"from": whale})