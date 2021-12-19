from itertools import count
from brownie import Wei, reverts, Contract
import eth_abi
from brownie.convert import to_bytes
from useful_methods import genericStateOfStrat,genericStateOfVault
import random
import brownie

def test_ops(dai,stratms, whale,Strategy, strategy_usdc_ib_no_fees_strategy, accounts, ibyvault,chain,live_usdc_vault, ychad, gov,strategist, interface):
    
    vault = live_usdc_vault
    currency = interface.ERC20(vault.token())
    decimals = currency.decimals()
    gov = accounts.at(vault.governance(), force=True)
    strategy = strategy_usdc_ib_no_fees_strategy

    yvault = ibyvault
    #amount = 1000*1e6
    #amounts = [0, 0, amount]
    print("curveid: ", strategy.curveId())
    #print("slip: ", strategy._checkSlip(amount))
    #print("expectedOut: ", amount/strategy.virtualPriceToWant())
    print("curve token: ", strategy.curveToken())
    print("ytoken: ", strategy.yvToken())
    yvault.setDepositLimit(2 **256 -1 , {'from': yvault.governance()})
    #print("real: ", ibCurvePool.calc_token_amount(amounts, True))
    currency.approve(vault, 2 ** 256 - 1, {"from": whale})
    whale_before = currency.balanceOf(whale)
    whale_deposit = 1_000_000 * (10 ** (decimals))
    vault.deposit(whale_deposit, {"from": whale})
    vault.setManagementFee(0, {"from": gov})

    #idl = Strategy.at(vault.withdrawalQueue(1))
    genlev = Strategy.at("0x342491C093A640c7c2347c4FFA7D8b9cBC84D1EB")
    genlevflashmint = Strategy.at("0xd4E94061183b2DBF24473F28A3559cf4dE4459Db")
    vault.updateStrategyDebtRatio(genlev, 0, {"from": gov})
    vault.updateStrategyDebtRatio(genlevflashmint, 0, {"from": gov})
    genlev.tend({"from": gov})
    genlevflashmint.tend({"from": gov})
    genlevflashmint.harvest({"from": gov})
    genlev.harvest({"from": gov})
    vault.addStrategy(strategy, 1000, 0, 2**256-1, 1000, {"from": gov})
    # zeroaddress = "0x0000000000000000000000000000000000000000"
    # for i in range(0,20):
    #     s = vault.withdrawalQueue(i)
    #     if s == zeroaddress:
    #         break
    #     s = Strategy.at(s)
    #     print(vault.creditAvailable(s))
    bef = vault.pricePerShare() / 10**vault.decimals()
    tx = strategy.harvest({'from': strategist})
    print("🧑‍🌾 INVEST")
    print("pps gain",vault.pricePerShare() / 10**vault.decimals() - bef)
    print(tx.events["Harvested"])
    print("🧑‍🌾")
    genericStateOfStrat(strategy, currency, vault)
    #genericStateOfStrat(strategy, currency, vault)
    #genericStateOfVault(vault, currency)

    ibcrvStrat1 = Strategy.at(yvault.withdrawalQueue(0))
    ibcrvStrat2 = Strategy.at(yvault.withdrawalQueue(1))
    
    vGov = accounts.at(yvault.governance(), force=True)
    ibcrvStrat1.harvest({"from": vGov})
    ibcrvStrat2.harvest({"from": vGov})
    chain.sleep(2016000)
    #chain.mine(1)
    ibcrvStrat1.harvest({"from": vGov})
    ibcrvStrat2.harvest({"from": vGov})
    chain.sleep(21600)
    #chain.mine(1)
    bef = vault.pricePerShare() / 10**vault.decimals()
    tx = strategy.harvest({'from': strategist})
    print("🧑‍🌾 EARN")
    print("pps gain",vault.pricePerShare() / 10**vault.decimals() - bef)
    print(tx.events["Harvested"])
    print("🧑‍🌾")
    print(vault.strategies(strategy))
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)
    chain.sleep(21600)
    #chain.mine(1)
 
    vault.withdraw({"from": whale})
    whale_after = currency.balanceOf(whale)
    print("profit =", (whale_after - whale_before)/(10 ** (decimals)))
    print("balance left =", vault.balanceOf(whale))
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)
    vault.updateStrategyDebtRatio(strategy, 0 , {"from": gov})
    #chain.mine(1)

    tx = strategy.harvest({'from': strategist})
    print("🧑‍🌾")
    print(tx.events["Harvested"])
    print("🧑‍🌾")
    genericStateOfStrat(strategy, currency, vault)
