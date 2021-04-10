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

def test_wbtc_1(currency,Strategy,curvePool, accounts, hCRV,yvaultv2, orb,rewards,chain,yhbtcstrategyv2,live_wbtc_vault, ychad, whale,gov,strategist, interface):
    yvault = yvaultv2
    vault = live_wbtc_vault
    currency = interface.ERC20(vault.token())
    gov = accounts.at(vault.governance(), force=True)
    vault.setDepositLimit(2**256-1, {"from": gov})
    #strategy = strategist.deploy(Strategy, vault, 2*1e8)
    strategy = Strategy.at('0x148f64a2BeD9c815EDcD43754d3323283830070c')
    strategist = accounts.at(strategy.strategist(), force=True)
    yvault.setDepositLimit(2**256-1, {'from': ychad})
    debt_ratio = 10_000
    vault.addStrategy(strategy, debt_ratio,0, 2 ** 256 - 1, 1000, {"from": gov})
    vault.setManagementFee(0, {"from": gov})
    vault.setPerformanceFee(0, {"from": gov})

    currency.approve(vault, 2 ** 256 - 1, {"from": whale} )
    whalebefore = currency.balanceOf(whale)
    whale_deposit  = 2 *1e8
    assert currency.balanceOf(whale) > whale_deposit
    vault.deposit(whale_deposit, {"from": whale})
    strategy.harvest({'from': strategist})
    #print(strategy.curveTokenToWant(1e18))
    #print(yvault.totalSupply())
    #assert strategy.curveTokensInYVault() == yvault.balanceOf(strategy)
    #print(yvault.balanceOf(strategy))
    #yvault.earn({'from': ychad})

    yhbtcstrategyv2.harvest({'from': ychad})
    print(hCRV.balanceOf(yvault))
    #yhbtcstrategy.deposit()
    #genericStateOfStrat(strategy, currency, vault)
    #genericStateOfVault(vault, currency)
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)
    chain.sleep(2592000)
    chain.mine(1)

    yhbtcstrategyv2.harvest({'from': orb})
    

    chain.sleep(21600)
    chain.mine(1)
    strategy.harvest({'from': strategist})
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)

    print("\nEstimated APR: ", "{:.2%}".format(((vault.totalAssets()-2*1e8)*12)/(2*1e8)))
    chain.sleep(21600)
    chain.mine(1)
    
    vault.transferFrom(strategy, strategist, vault.balanceOf(strategy), {"from": strategist})
    print("\nWithdraw")
    vault.withdraw(vault.balanceOf(whale), whale, 100, {"from": whale})
    vault.withdraw(vault.balanceOf(strategist), strategist, 100, {"from": strategist})

    #vault.withdraw(vault.balanceOf(rewards), rewards, 100, {"from": rewards})


    #genericStateOfStrat(strategy, currency, vault)
    #genericStateOfVault(vault, currency)
    balanceAfter = currency.balanceOf(whale)
    print("Whale profit: ", (currency.balanceOf(whale) - whalebefore)/1e18)
    print("Whale profit %: ", "{:.2%}".format(((currency.balanceOf(whale) - whalebefore)/whale_deposit)*12))

def _mmEarnAndHarvest(mmKeeper, mmVault, mmStrategy): 
    mmVault.earn({"from": mmKeeper})    

    mmStrategy.harvest({"from": mmKeeper})  

def test_mando(currency,Strategy,Contract, accounts, hCRV,yvaultv2, orb,rewards,chain,yhbtcstrategyv2,live_wbtc_vault, ychad, whale,gov,strategist, interface):
    vault = live_wbtc_vault
    strategy = Contract.from_explorer('0x53a65c8e238915c79a1e5C366Bc133162DBeE34f')
    currency = interface.ERC20(vault.token())
    gov = accounts.at(vault.governance(), force=True)
    vault.setDepositLimit(2**256-1, {"from": gov})
    
    debt_ratio = 10_000
    vault.addStrategy(strategy, debt_ratio,0, 2 ** 256 - 1, 1000, {"from": gov})
    vault.setManagementFee(0, {"from": gov})
    vault.setPerformanceFee(0, {"from": gov})

    currency.approve(vault, 2 ** 256 - 1, {"from": whale} )
    whalebefore = currency.balanceOf(whale)
    whale_deposit  = 2 *1e8
    assert currency.balanceOf(whale) > whale_deposit
    vault.deposit(whale_deposit, {"from": whale})
    strategy.harvest({'from': gov})
    mmVault = Contract.from_explorer("0xb06661A221Ab2Ec615531f9632D6Dc5D2984179A")
    mmKeeper = accounts.at("0x7cDaCBa026DDdAa0bD77E63474425f630DDf4A0D", force=True)
    mmStrategy = Contract.from_explorer("0xc8EBBaAaD5fF2e5683f8313fd4D056b7Ff738BeD")
    _mmEarnAndHarvest(mmKeeper, mmVault, mmStrategy)

    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)

    chain.mine(276)

    _mmEarnAndHarvest(mmKeeper, mmVault, mmStrategy)
    
    strategy.harvest({'from': gov})
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)

    print("\nEstimated APR: ", "{:.2%}".format(((vault.totalAssets()-2*1e8)*8760)/(2*1e8)))
    chain.sleep(21600)
    chain.mine(1)
    
    #vault.transferFrom(strategy, strategist, vault.balanceOf(strategy), {"from": gov})
    print("\nWithdraw")
    #vault.withdraw(vault.balanceOf(whale), whale, 100, {"from": whale})
    #vault.withdraw(vault.balanceOf(strategist), strategist, 100, {"from": gov})
    vault.revokeStrategy(strategy, {"from": gov})
    strategy.harvest({'from': gov})

    #vault.withdraw(vault.balanceOf(rewards), rewards, 100, {"from": rewards})


    #genericStateOfStrat(strategy, currency, vault)
    #genericStateOfVault(vault, currency)
    balanceAfter = currency.balanceOf(whale)
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)
    #print("Whale profit: ", (currency.balanceOf(whale) - whalebefore)/1e18)
    #print("Whale profit %: ", "{:.2%}".format(((currency.balanceOf(whale) - whalebefore)/whale_deposit)*12))


def test_wbtc_live_vault(wbtc, curvePool,Strategy, hCRV,yvault, orb,rewards,chain,yhbtcstrategy,wbtc_vault, ychad, whale,gov,strategist, interface):

    vault = wbtc_vault
    strategy = strategist.deploy(Strategy, vault, 2*1e8)
    currency = interface.ERC20(vault.token())
    debt_ratio = 10_000
    vault.addStrategy(strategy, debt_ratio, 0, 2 ** 256 - 1, 1000, {"from": gov})
    vault.setManagementFee(0, {"from": gov})
    vault.setPerformanceFee(0, {"from": gov})

    currency.approve(vault, 2 ** 256 - 1, {"from": whale} )
    print(currency.balanceOf(whale)/1e8)
    whalebefore = currency.balanceOf(whale)
    whale_deposit  = 2 *1e8
    vault.deposit(whale_deposit, {"from": whale})
    strategy.harvest({'from': gov})
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)
    chain.sleep(1000)
    chain.mine(1)
    strategy.harvest({'from': gov})

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
    strategy.harvest({'from': gov})
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)

    print("\nEstimated APR: ", "{:.2%}".format(((vault.totalAssets()-2*1e8)*12)/(2*1e8)))
    chain.sleep(21600) # wait six hours so we get full harvest
    chain.mine(1)

    vault.withdraw(vault.balanceOf(whale), whale, 100, {"from": whale})
    #vault.withdraw(vault.balanceOf(strategist), strategist, 100, {"from": strategist})

    #vault.withdraw(vault.balanceOf(rewards), rewards, 100, {"from": rewards})

    print("\nWithdraw")
    #genericStateOfStrat(strategy, currency, vault)
    #genericStateOfVault(vault, currency)
    balanceAfter = currency.balanceOf(whale)
    print("Whale profit: ", (currency.balanceOf(whale) - whalebefore)/1e8)
    print("Whale profit %: ", "{:.2%}".format(((currency.balanceOf(whale) - whalebefore)/whale_deposit)*12))