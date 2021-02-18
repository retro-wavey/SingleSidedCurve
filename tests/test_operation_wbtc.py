from itertools import count
from brownie import Wei, reverts
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

def test_wbtc_1(wbtc, curvePool,Strategy, hCRV,yvault, orb,rewards,chain,yhbtcstrategy,wbtc_vault, ychad, whale,gov,strategist, interface):

    vault = wbtc_vault
    strategy = strategist.deploy(Strategy, vault)
    currency = wbtc
    debt_ratio = 10_000
    vault.addStrategy(strategy, debt_ratio, 0, 2 ** 256 - 1, 1000, {"from": gov})
    vault.setManagementFee(0, {"from": gov})
    vault.setPerformanceFee(0, {"from": gov})

    currency.approve(vault, 2 ** 256 - 1, {"from": whale} )
    print(currency.balanceOf(whale)/1e8)
    whalebefore = currency.balanceOf(whale)
    whale_deposit  = 2 *1e8
    vault.deposit(whale_deposit, {"from": whale})
    strategy.harvest({'from': strategist})
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)
    chain.sleep(1000)
    chain.mine(1)
    strategy.harvest({'from': strategist})

    #print(strategy.curveTokenToWant(1e8))
    #print(yvault.totalSupply())
    #assert strategy.curveTokensInYVault() == yvault.balanceOf(strategy)
    print(yvault.balanceOf(strategy)/1e18)
    yvault.earn({'from': ychad})
    print(hCRV.balanceOf(yvault))
    #print("Virtual price: ", hCRV.get_virtual_price())
    #yhbtcstrategy.deposit()
    #genericStateOfStrat(strategy, currency, vault)
    #genericStateOfVault(vault, currency)

    chain.sleep(2591000)
    chain.mine(1)
    yhbtcstrategy.harvest({'from': orb})
    strategy.harvest({'from': strategist})
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)

    print("\nEstimated APR: ", "{:.2%}".format(((vault.totalAssets()-2*1e8)*12)/(2*1e8)))
    chain.sleep(21600) # wait six hours so we get full harvest
    chain.mine(1)

    vault.withdraw(vault.balanceOf(whale), whale, 100, {"from": whale})
    vault.withdraw(vault.balanceOf(strategist), strategist, 100, {"from": strategist})

    #vault.withdraw(vault.balanceOf(rewards), rewards, 100, {"from": rewards})

    print("\nWithdraw")
    #genericStateOfStrat(strategy, currency, vault)
    #genericStateOfVault(vault, currency)
    balanceAfter = currency.balanceOf(whale)
    print("Whale profit: ", (currency.balanceOf(whale) - whalebefore)/1e8)
    print("Whale profit %: ", "{:.2%}".format(((currency.balanceOf(whale) - whalebefore)/whale_deposit)*12))


def test_wbtc_live_vault(wbtc, curvePool,Strategy, hCRV,yvault, orb,rewards,chain,yhbtcstrategy,wbtc_vault, ychad, whale,gov,strategist, interface):

    vault = wbtc_vault
    strategy = strategist.deploy(Strategy, vault)
    currency = wbtc
    debt_ratio = 10_000
    vault.addStrategy(strategy, debt_ratio, 0, 2 ** 256 - 1, 1000, {"from": gov})
    vault.setManagementFee(0, {"from": gov})
    vault.setPerformanceFee(0, {"from": gov})

    currency.approve(vault, 2 ** 256 - 1, {"from": whale} )
    print(currency.balanceOf(whale)/1e8)
    whalebefore = currency.balanceOf(whale)
    whale_deposit  = 2 *1e8
    vault.deposit(whale_deposit, {"from": whale})
    strategy.harvest({'from': strategist})
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)
    chain.sleep(1000)
    chain.mine(1)
    strategy.harvest({'from': strategist})

    #print(strategy.curveTokenToWant(1e8))
    #print(yvault.totalSupply())
    #assert strategy.curveTokensInYVault() == yvault.balanceOf(strategy)
    print(yvault.balanceOf(strategy)/1e18)
    yvault.earn({'from': ychad})
    print(hCRV.balanceOf(yvault))
    #print("Virtual price: ", hCRV.get_virtual_price())
    #yhbtcstrategy.deposit()
    #genericStateOfStrat(strategy, currency, vault)
    #genericStateOfVault(vault, currency)

    chain.sleep(2591000)
    chain.mine(1)
    yhbtcstrategy.harvest({'from': orb})
    strategy.harvest({'from': strategist})
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)

    print("\nEstimated APR: ", "{:.2%}".format(((vault.totalAssets()-2*1e8)*12)/(2*1e8)))
    chain.sleep(21600) # wait six hours so we get full harvest
    chain.mine(1)

    vault.withdraw(vault.balanceOf(whale), whale, 100, {"from": whale})
    vault.withdraw(vault.balanceOf(strategist), strategist, 100, {"from": strategist})

    #vault.withdraw(vault.balanceOf(rewards), rewards, 100, {"from": rewards})

    print("\nWithdraw")
    #genericStateOfStrat(strategy, currency, vault)
    #genericStateOfVault(vault, currency)
    balanceAfter = currency.balanceOf(whale)
    print("Whale profit: ", (currency.balanceOf(whale) - whalebefore)/1e8)
    print("Whale profit %: ", "{:.2%}".format(((currency.balanceOf(whale) - whalebefore)/whale_deposit)*12))