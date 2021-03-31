from itertools import count
from brownie import Wei, reverts
import eth_abi
from brownie.convert import to_bytes
from useful_methods import genericStateOfStrat,genericStateOfVault
import random
import brownie

def test_hbtc_1(currency,Strategy,curvePool, hCRV,yvaultv2, orb,rewards,chain,yhbtcstrategyv2,live_vault, live_strategy, ychad, whale,gov,strategist, interface, samdev):
    vault = live_vault
    strategist = samdev
    #strategy = strategist.deploy(Strategy, vault, 2*1e18)
    strategy = Strategy.at("0x308518f220D5c6FBeF497ac7744D3D1194c7AFF9")
    vault.revokeStrategy(live_strategy, {'from': strategist})

    yvault = yvaultv2
    #yvault.setDepositLimit(10_000 * 1e18, {'from': ychad})
    #debt_ratio = 10_000
    #vault.addStrategy(strategy, debt_ratio,0, 2 ** 256 - 1, 1000, {"from": strategist})
    #vault.setManagementFee(0, {"from": strategist})
    #vault.setPerformanceFee(0, {"from": strategist})

    #currency.approve(vault, 2 ** 256 - 1, {"from": whale} )
    #whalebefore = currency.balanceOf(whale)
    #whale_deposit  = 2 *1e18
    #vault.deposit(whale_deposit, {"from": whale})
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

    print("\nEstimated APR: ", "{:.2%}".format(((vault.totalAssets()-2*1e18)*12)/(2*1e18)))
    
