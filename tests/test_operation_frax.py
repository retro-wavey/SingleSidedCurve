from itertools import count
from brownie import Wei, reverts, Contract
import eth_abi
from brownie.convert import to_bytes
from useful_methods import genericStateOfStrat,genericStateOfVault
import random
import brownie

# TODO: Add tests here that show the normal operation of this strategy
#       Suggestions to include:
#           - strategy loading and unloading (via Vault addStrategy/revokeStrategy)
#           - change in loading (from low to high and high to low)
#           - strategy operation at different loading levels (anticipated and "extreme")



def test_frax_fresh_vault(frax, fraxCurvePool,Strategy,strategy_frax,fraxyvault,frax3CRV, rewards,chain,frax_vault, ychad, whale,gov,strategist, interface):

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
    strategy.harvest({'from': strategist})
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)
    chain.sleep(1000)
    chain.mine(1)
    strategy.harvest({'from': strategist})

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
    
    strategy.harvest({'from': strategist})
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)

    print("\nEstimated APR: ", "{:.2%}".format(((vault.totalAssets()-2*10 ** currency.decimals())*12)/(2*10 ** currency.decimals())))
    chain.sleep(21600) # wait six hours so we get full harvest
    chain.mine(1)

    vault.updateStrategyDebtRatio(strategy, 0 , {"from": gov})
    tx = strategy.harvest({'from': strategist})
    vault.withdraw(vault.balanceOf(whale), whale, 100, {"from": whale})
    vault.withdraw(vault.balanceOf(strategist), strategist, 100, {"from": strategist})

    #vault.withdraw(vault.balanceOf(rewards), rewards, 100, {"from": rewards})

    print("\nWithdraw")
    #genericStateOfStrat(strategy, currency, vault)
    #genericStateOfVault(vault, currency)
    balanceAfter = currency.balanceOf(whale)
    print("Whale profit: ", (currency.balanceOf(whale) - whalebefore)/10 ** currency.decimals())
    print("Whale profit %: ", "{:.2%}".format(((currency.balanceOf(whale) - whalebefore)/whale_deposit)*12))
