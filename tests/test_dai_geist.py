from brownie import ZERO_ADDRESS, Contract
from useful_methods import genericStateOfStrat,genericStateOfVault

def test_dai_geist_1(
    chain, strategist, accounts, ftm_dai_vault, strategy_dai_geist, 
    geistyvault, ftm_dai_whale, interface, Strategy
):
    vault = ftm_dai_vault
    token = interface.ERC20(vault.token())
    decimals = token.decimals()
    strategy = strategy_dai_geist
    gov = accounts.at(vault.governance(), force=True)
    whale = ftm_dai_whale

    print("curveid: ", strategy.curveId())
    print("curve token: ", strategy.curveToken())
    print("ytoken: ", strategy.yvToken())

    geistyvault.setDepositLimit(2 **256 -1 , {'from': geistyvault.governance()})
    #print("real: ", ibCurvePool.calc_token_amount(amounts, True))
    token.approve(vault, 2 ** 256 - 1, {"from": whale})
    whale_before = token.balanceOf(whale)
    whale_deposit = 1_000_000 * (10 ** (decimals))
    vault.deposit(whale_deposit, {"from": whale})
    vault.setManagementFee(0, {"from": gov})

    print("Harvest Trigger:", strategy.harvestTrigger(1000000 * 30 * 1e9))
    
    vault.addStrategy(strategy, 1000, 0, 2 ** 256 - 1, 1_000, {"from": gov})

    print("Harvest Trigger:", strategy.harvestTrigger(1000000 * 30 * 1e9))
    
    strategy.harvest({'from': strategist})

    geistcrvStrat = Strategy.at(geistyvault.withdrawalQueue(0))
    
    vGov = accounts.at(geistyvault.governance(), force=True)
    geistcrvStrat.harvest({"from": vGov})
    chain.sleep(201600)
    chain.mine(1)
    geistcrvStrat.harvest({"from": vGov})
    chain.sleep(2000)
    chain.mine(1)
    strategy.harvest({'from': strategist})
    print(vault.strategies(strategy))
    genericStateOfStrat(strategy, token, vault)
    genericStateOfVault(vault, token)
 
    vault.withdraw({"from": whale})
    whale_after = token.balanceOf(whale)
    print("profit =", (whale_after - whale_before)/(10 ** (decimals)))
    print("balance left =", vault.balanceOf(whale))
    genericStateOfStrat(strategy, token, vault)
    genericStateOfVault(vault, token)
    # chain.sleep(21600)
    chain.mine(1)

    strategy.harvest({'from': strategist})
    genericStateOfStrat(strategy, token, vault)

    assert False

