from itertools import count
from brownie import Wei, reverts
import eth_abi
from brownie.convert import to_bytes
from useful_methods import (
    genericStateOfStrat,
    genericStateOfVault,
    genericStateOfStrat030,
)
import random
import brownie

# TODO: Add tests here that show the normal operation of this strategy
#       Suggestions to include:
#           - strategy loading and unloading (via Vault addStrategy/revokeStrategy)
#           - change in loading (from low to high and high to low)
#           - strategy operation at different loading levels (anticipated and "extreme")


def test_dai_1(
    usdt,
    stratms,
    whale,
    Strategy,
    ibCurvePool,
    strategy_usdc_ib,
    accounts,
    ib3CRV,
    ibyvault,
    orb,
    rewards,
    chain,
    strategy_usdt_ib,
    live_vault_usdc,
    ychad,
    gov,
    strategist,
    interface,
):

    vault = live_vault_usdc
    currency = interface.ERC20(vault.token())
    decimals = currency.decimals()
    gov = accounts.at(vault.governance(), force=True)
    strategy = strategy_usdc_ib

    yvault = ibyvault
    # amount = 1000*1e6
    # amounts = [0, 0, amount]
    print("curveid: ", strategy.curveId())
    # print("slip: ", strategy._checkSlip(amount))
    # print("expectedOut: ", amount/strategy.virtualPriceToWant())
    print("curve token: ", strategy.curveToken())
    print("ytoken: ", strategy.yvToken())
    yvault.setDepositLimit(2 ** 256 - 1, {"from": yvault.governance()})
    # print("real: ", ibCurvePool.calc_token_amount(amounts, True))

    vault.setManagementFee(0, {"from": gov})

    idl = Strategy.at(vault.withdrawalQueue(0))
    vault.updateStrategyDebtRatio(idl, 0, {"from": gov})
    debt_ratio = 2000
    # v0.3.0
    vault.addStrategy(strategy, 0, 0, 1000, {"from": gov})
    vault.updateStrategyDebtRatio(strategy, debt_ratio, {"from": gov})
    idl.harvest({"from": gov})
    idl.harvest({"from": gov})

    strategy.harvest({"from": strategist})
    ppsB = strategy.estimatedTotalAssets()
    print("est ", strategy.estimatedTotalAssets() / 1e18)
    # genericStateOfStrat(strategy, currency, vault)
    # genericStateOfVault(vault, currency)

    ibcrvStrat = Strategy.at(ibyvault.withdrawalQueue(0))

    vGov = accounts.at(ibyvault.governance(), force=True)
    ibcrvStrat.harvest({"from": vGov})
    chain.sleep(604800)
    chain.mine(1)
    ibcrvStrat.harvest({"from": vGov})
    chain.sleep(21600)
    chain.mine(1)
    print(
        "profit ", (((strategy.estimatedTotalAssets() - ppsB) * 52) / ppsB) * 100, "%"
    )

    strategy.harvest({"from": strategist})
    print(vault.strategies(strategy))
    genericStateOfStrat030(strategy, currency, vault)
    genericStateOfVault(vault, currency)
    vault.updateStrategyDebtRatio(strategy, 0, {"from": gov})
    strategy.updateDontInvest(True, {"from": strategist})
    strategy.harvest({"from": strategist})
    strategy.harvest({"from": strategist})
    genericStateOfStrat030(strategy, currency, vault)
    genericStateOfVault(vault, currency)

def test_snapshot(
    usdt,
    stratms,
    whale,
    Strategy,
    ibCurvePool,
    live_vault_usdc,
    live_strat_usdc,
    accounts,
    ib3CRV,
    ibyvault,
    orb,
    rewards,
    chain,
    Contract,
    live_vault_dai,
    ychad,
    gov,
    strategist,
    interface,
):
    vault = live_vault_usdc
    currency = interface.ERC20(vault.token())
    decimals = currency.decimals()
    gov = accounts.at(vault.governance(), force=True)
    strategy = live_strat_usdc
    strategist = accounts.at(strategy.strategist(), force=True)

    print("BEFORE HARVEST")
    genericStateOfStrat030(strategy, currency, vault)
    genericStateOfVault(vault, currency)

    strategy.harvest({"from": strategist})
    
    print("\nAFTER HARVEST")
    genericStateOfStrat030(strategy, currency, vault)
    genericStateOfVault(vault, currency)