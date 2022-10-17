from itertools import count
from brownie import Wei, reverts, web3, Contract
import eth_abi
from brownie.convert import to_bytes
from useful_methods import genericStateOfStrat,genericStateOfVault
import random
import brownie


def test_dola_dolafraxbp(dai,stratms, whale,Strategy, strategy_dola_fraxbp, accounts, dola_fraxbp_vault,chain,dola_vault, ychad, gov,strategist, interface):
    
    vault = dola_vault
    currency = interface.ERC20(vault.token())
    decimals = currency.decimals()
    gov = accounts.at(vault.governance(), force=True)
    strategy = strategy_dola_fraxbp

    yvault = dola_fraxbp_vault
    print("curveid: ", strategy.curveId())
    print("curve token: ", strategy.curveToken())
    print("ytoken: ", strategy.yvToken())
    yvault.setDepositLimit(2 **256 -1 , {'from': yvault.governance()})
    currency.approve(vault, 2 ** 256 - 1, {"from": whale})

    whale_before = currency.balanceOf(whale)
    whale_deposit = 1_000_000 * (10 ** (decimals))
    vault.deposit(whale_deposit, {"from": whale})
    vault.setManagementFee(0, {"from": gov})

    vault.addStrategy(strategy, 10000, 0, 2**256-1, 1000, {"from": gov})
    strat1 = Contract(vault.withdrawalQueue(0))
    vault.updateStrategyDebtRatio(strat1, 0, {"from": gov})
    vault.updateStrategyDebtRatio(strategy, 10_000, {"from": gov})

    tx = strategy.harvest({'from': strategist})
    genericStateOfStrat(strategy, currency, vault)
 
    vault.deposit({"from": whale})
    tx = strategy.harvest({'from': strategist})
    chain.sleep(60*60*24)
    chain.mine()
    tx = strategy.harvest({'from': strategist})
    assert strategy.estimatedTotalAssets() > 0
    chain.sleep(60)
    chain.mine()
    vault.updateStrategyDebtRatio(strategy, 0,{'from': gov})
    tx = strategy.harvest({'from': strategist})
    assert strategy.estimatedTotalAssets() < 10_000e18
    genericStateOfStrat(strategy, currency, vault)