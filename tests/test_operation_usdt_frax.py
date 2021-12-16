from itertools import count
from brownie import Wei, reverts, Contract
import eth_abi
from brownie.convert import to_bytes
from useful_methods import genericStateOfStrat,genericStateOfVault
import random
import brownie

def test_usdt_frax_fresh_convex(usdt, stratms, whale, Strategy, strategy_usdt_frax, accounts, fraxyvault, chain, live_usdt_vault, ychad, gov, strategist, interface):
    strategy = strategy_usdt_frax
    vault = live_usdt_vault
    currency = interface.ERC20(vault.token())
    decimals = currency.decimals()
    gov = accounts.at(vault.governance(), force=True)
    whale = accounts.at("0x36822d0b11F4594380181cE6e76bd4986d46c389", force=True)

    # Setup vault/strat
    vault.addStrategy(strategy, 0, 0, 2**256-1, 1000, {"from": gov})
    strategy.updateMinTimePerInvest(0,{'from':gov})
    free_ratio = 10_000 - vault.debtRatio()
    vault.updateStrategyDebtRatio(strategy, free_ratio, {"from": gov})
    tx = strategy.harvest({'from': gov})
    
    # Setup delegated CRV vault/strat vars
    convex_deposit = Contract("0xF403C135812408BFbE8713b5A23a04b3D48AAE31")
    yvault = fraxyvault
    print("curveid: ", strategy.curveId())
    print("curve token: ", strategy.curveToken())
    print("ytoken: ", strategy.yvToken())
    delegatedStrat1 = Strategy.at(yvault.withdrawalQueue(0))
    delegatedStrat2 = Strategy.at(yvault.withdrawalQueue(1))
    chain.sleep(2016000)
    chain.mine(1)
    tx = delegatedStrat1.harvest({"from": gov})
    tx = delegatedStrat2.harvest({"from": gov})
    chain.sleep(2016000)
    chain.mine(1)
    
    genericStateOfStrat(strategy, currency, vault)
    convex_deposit.earmarkRewards(32, {"from": gov})
    tx = delegatedStrat1.harvest({"from": gov})
    print("Delegated strat1",tx.events["Harvested"])
    tx = delegatedStrat2.harvest({"from": gov})
    print("Delegated strat2",tx.events["Harvested"])
    chain.sleep(2016000)
    chain.mine(1)

    # Harvest strategy and expect Profits
    strategy.updateSlippageProtectionIn(0,{'from': gov})
    strategy.updateSlippageProtectionOut(0,{'from': gov})
    tx = strategy.harvest({'from': gov})
    print("Strategy",tx.events["Harvested"])
    assert tx.events["Harvested"]["profit"] > 0
    assert tx.events["Harvested"]["loss"] == 0
    print("Stats after first profitable harvest:",vault.strategies(strategy).dict())
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)
    chain.sleep(21600)
    chain.mine(1)

    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)
    vault.updateStrategyDebtRatio(strategy, 0 , {"from": gov})
    # #chain.mine(1)
    # strategy.updateSlippageProtectionIn(0,{'from': gov})
    # strategy.updateSlippageProtectionOut(0,{'from': gov})
    tx = strategy.harvest({'from': gov})
    print("Strategy",tx.events["Harvested"])
    genericStateOfStrat(strategy, currency, vault)