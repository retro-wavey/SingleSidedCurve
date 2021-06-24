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
    strategy_dai_ib,
    accounts,
    ib3CRV,
    ibyvault,
    orb,
    rewards,
    chain,
    strategy_usdt_ib,
    live_vault_dai,
    ychad,
    gov,
    strategist,
    interface,
):

    vault = live_vault_dai
    currency = interface.ERC20(vault.token())
    decimals = currency.decimals()
    gov = accounts.at(vault.governance(), force=True)
    strategy = strategy_dai_ib

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
    currency.approve(vault, 2 ** 256 - 1, {"from": whale})
    whale_before = currency.balanceOf(whale)
    whale_deposit = 1_000_000 * (10 ** (decimals))
    vault.deposit(whale_deposit, {"from": whale})
    vault.setManagementFee(0, {"from": gov})

    idl = Strategy.at(vault.withdrawalQueue(1))
    vault.updateStrategyDebtRatio(idl, 0, {"from": gov})
    debt_ratio = 2000
    # v0.3.0
    vault.addStrategy(strategy, debt_ratio, 0, 1000, {"from": gov})
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


def test_migrate(
    usdt,
    stratms,
    Strategy,
    live_strat_dai,
    live_strat_dai_migrated,
    accounts,
    ibCurvePool,
    ib3CRV,
    ibyvault,
    orb,
    rewards,
    chain,
    strategy_usdt_ib,
    live_vault_dai,
    strategy_dai_ib,
    ychad,
    gov,
    strategist,
    interface,
):

    vault = live_vault_dai
    currency = interface.ERC20(vault.token())
    decimals = currency.decimals()
    gov = accounts.at(vault.governance(), force=True)
    strategy = live_strat_dai_migrated

    vault.migrateStrategy(live_strat_dai, strategy, {"from": gov})
    assert live_strat_dai.estimatedTotalAssets() == 0

    genericStateOfStrat030(strategy, currency, vault)
    genericStateOfVault(vault, currency)
    print(strategy.curveTokensInYVault())

    strategy.harvest({"from": gov})
    
    genericStateOfStrat030(strategy, currency, vault)
    genericStateOfVault(vault, currency)

    vault.migrateStrategy(strategy, strategy_dai_ib, {"from": gov})
    strategy = strategy_dai_ib

    chain.mine(10)
    chain.sleep(300)

    strategy.harvest({"from": gov})
    
    genericStateOfStrat030(strategy, currency, vault)
    genericStateOfVault(vault, currency)

    vault.updateStrategyDebtRatio(strategy, 1100, {"from": gov})

    strategy.harvest({"from": gov})
    
    genericStateOfStrat030(strategy, currency, vault)
    genericStateOfVault(vault, currency)



def test_snapshot(
    usdt,
    stratms,
    Strategy,
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

    ms = accounts.at("0x16388463d60ffe0661cf7f1f31a7d658ac790ff7", force=True)
    #dai_vault = Contract("0x19D3364A399d251E894aC732651be8B0E4e85001")
    #ssc = "0x6a6B94A78cBA0F55BC4D41b37f2229427800B4dA"
    #lev_comp = "0x4031afd3B0F71Bace9181E554A9E680Ee4AbE7dF"
    #ib_lev_comp = "0x77b7CD137Dd9d94e7056f78308D7F65D2Ce68910"
    #ah2 = "0x7D960F3313f3cB1BBB6BF67419d303597F3E2Fa8"
    #dai_vault.updateStrategyDebtRatio(ah2, 1500, {"from": ms})
    #dai_vault.updateStrategyDebtRatio(lev_comp, 4700, {"from": ms})
    #dai_vault.updateStrategyDebtRatio(ib_lev_comp, 1000, {"from": ms})
    #dai_vault.updateStrategyDebtRatio(ssc, 1000, {"from": ms})
    #assert dai_vault.debtRatio() == 10_000

    #usdc_vault = Contract("0x5f18C75AbDAe578b483E5F43f12a39cF75b973a9")
    #lev_comp = "0x4D7d4485fD600c61d840ccbeC328BfD76A050F87"
    #ib_lev_comp = "0xE68A8565B4F837BDa10e2e917BFAaa562e1cD143"
    #ssc = "0x80af28cb1e44C44662F144475d7667C9C0aaB3C3"
    #ah2 = "0x86Aa49bf28d03B1A4aBEb83872cFC13c89eB4beD"

    #usdc_vault.updateStrategyDebtRatio(lev_comp, 3750, {"from": ms})
    #usdc_vault.updateStrategyDebtRatio(ah2, 1500, {"from": ms})
    #usdc_vault.updateStrategyDebtRatio(ssc, 1000, {"from": ms})
    #usdc_vault.updateStrategyDebtRatio(ib_lev_comp, 1250, {"from": ms})

    #assert usdc_vault.debtRatio() == 10_000

    vault = live_vault_dai
    currency = interface.ERC20(vault.token())
    decimals = currency.decimals()
    gov = accounts.at(vault.governance(), force=True)
    strategy = Strategy.at('0x30010039Ea4a0c4fa1Ac051E8aF948239678353d')
    strategist = accounts.at(strategy.strategist(), force=True)
    #vault.updateStrategyDebtRatio(strategy, 1250, {"from": ms})

    
    genericStateOfStrat030(strategy, currency, vault)
    genericStateOfVault(vault, currency)
    print(strategy.curveTokensInYVault())

    strategy.harvest({"from": strategist})
    
    genericStateOfStrat030(strategy, currency, vault)
    genericStateOfVault(vault, currency)
    