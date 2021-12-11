from itertools import count
from brownie import Wei, reverts, Contract
import eth_abi
from brownie.convert import to_bytes
from useful_methods import genericStateOfStrat,genericStateOfVault
import random
import brownie

def test_usdc_ib_fresh_convex(usdc, stratms, whale, Strategy, strategy_usdc_ib, live_usdc_vault, accounts, ibyvault, chain, usdc_vault, live_usdc_vault ,live_usdc_vault_old, ychad, gov, strategist, interface):
    
    live_usdc_vault = Contract("0xa354F35829Ae975e850e23e9615b11Da1B3dC4DE")
    router = Contract("0x36822d0b11F4594380181cE6e76bd4986d46c389")
    ssc_old = Contract("0x80af28cb1e44C44662F144475d7667C9C0aaB3C3")
    ssc = strategy_usdc_ib
    vault = live_usdc_vault
    vault_old = live_usdc_vault_old
    currency = interface.ERC20(vault.token())
    decimals = currency.decimals()
    gov = accounts.at(vault.governance(), force=True)
    strategy = strategy_usdc_ib
    convex_deposit = Contract("0xF403C135812408BFbE8713b5A23a04b3D48AAE31")
    yvault = ibyvault
    print("curveid: ", strategy.curveId())
    print("curve token: ", strategy.curveToken())
    print("ytoken: ", strategy.yvToken())
    ibcrvStrat1 = Strategy.at(yvault.withdrawalQueue(0))
    ibcrvStrat2 = Strategy.at(yvault.withdrawalQueue(1))

    # Set Debt Ratios
    debt_old_ssc = vault_old.strategies(ssc_old).dict().["totalDebt"]
    actual_old_ssc_ratio = int(debt_old_ssc / vault_old.totalAssets() * 10_000)
    debt_router = vault_old.strategies(router).dict().["totalDebt"]
    router_ratio = debt_router + actual_ratio # Add this ratio to the router

    vault_old.updateStrategyDebtRatio(router, router_ratio, {"from:" gov})
    vault_old.updateStrategyDebtRatio(ssc_old, 0, {"from:" gov})

    ssc_old.harvest({"from:" gov})

    r_before = router.estimatedTotalAssets()
    router.harvest({"from:" gov})
    r_after = router.estimatedTotalAssets()


    actual_new_ssc_ratio = int(debt_old / vault_old.totalAssets() * 10_000)
    vault.updateStrategyDebtRatio(ssc_new)

    currency.approve(vault, 2 ** 256 - 1, {"from": whale})
    whale_before = currency.balanceOf(whale)
    whale_deposit = 1_000_000 * (10 ** (decimals))
    vault.deposit(whale_deposit, {"from": whale})
    vault.setManagementFee(0, {"from": gov})

    # vault.addStrategy(strategy, 10_000, 0, 2**256-1, 1000, {"from": gov})

    tx = strategy.harvest({'from': gov})
    
    print("Strategy takes funds in:",tx.events["Harvested"])
    chain.sleep(2016000)
    chain.mine(1)

    tx = ibcrvStrat2.harvest({"from": vGov})
    chain.sleep(2016000)
    chain.mine(1)
    
    genericStateOfStrat(strategy, currency, vault)
    #genericStateOfStrat(strategy, currency, vault)
    #genericStateOfVault(vault, currency)
    convex_deposit.earmarkRewards(29, {"from": vGov})
    tx = ibcrvStrat2.harvest({"from": vGov})
    print("ibcrvStrat2",tx.events["Harvested"])
    chain.sleep(2016000)
    chain.mine(1)
    # ibcrvStrat1.harvest({"from": vGov})
    convex_deposit.earmarkRewards(29, {"from": vGov})
    tx = ibcrvStrat2.harvest({"from": vGov})
    print("ibcrvStrat2",tx.events["Harvested"])
    chain.sleep(2016000)
    chain.mine(1)
    tx = strategy.harvest({'from': gov})
    print("Strategy",tx.events["Harvested"])
    print("Stats after first profitable harvest:",vault.strategies(strategy).dict())
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)
    chain.sleep(21600)
    chain.mine(1)
 
    # vault.withdraw({"from": whale})
    bef = currency.balanceOf(whale)
    tx = vault.withdraw(vault.balanceOf(whale),whale,10_000,{"from": whale})
    aft = currency.balanceOf(whale)
    whale_after = currency.balanceOf(whale)
    print("profit =", (whale_after - whale_before)/(10 ** (decimals)))
    print("balance left =", vault.balanceOf(whale))
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)
    vault.updateStrategyDebtRatio(strategy, 0 , {"from": gov})
    #chain.mine(1)

    strategy.harvest({'from': gov})
    genericStateOfStrat(strategy, currency, vault)


def test_usdc_ib_fresh_yearn(usdc, stratms, whale, Strategy, strategy_usdc_ib, accounts, ibyvault, chain, usdc_vault, ychad, gov, strategist, interface):
    
    vault = usdc_vault
    currency = interface.ERC20(vault.token())
    decimals = currency.decimals()
    gov = accounts.at(vault.governance(), force=True)
    strategy = strategy_usdc_ib

    yvault = ibyvault
    #amount = 1000*1e6
    #amounts = [0, 0, amount]
    print("curveid: ", strategy.curveId())
    #print("slip: ", strategy._checkSlip(amount))
    #print("expectedOut: ", amount/strategy.virtualPriceToWant())
    print("curve token: ", strategy.curveToken())
    print("ytoken: ", strategy.yvToken())
    vault.setDepositLimit(2**256 -1 , {'from': vault.governance()})
    yvault.setDepositLimit(2**256 -1 , {'from': yvault.governance()})
    #print("real: ", ibCurvePool.calc_token_amount(amounts, True))
    vGov = accounts.at(yvault.governance(), force=True)
    ibcrvStrat1 = Strategy.at(yvault.withdrawalQueue(0))
    ibcrvStrat2 = Strategy.at(yvault.withdrawalQueue(1))
    
    yvault.updateStrategyDebtRatio(ibcrvStrat2, 0, {"from": vGov})
    yvault.updateStrategyDebtRatio(ibcrvStrat1, 10_000, {"from": vGov})
    tx = ibcrvStrat2.harvest({"from": vGov})
    tx = ibcrvStrat1.harvest({"from": vGov})

    currency.approve(vault, 2 ** 256 - 1, {"from": whale})
    whale_before = currency.balanceOf(whale)
    whale_deposit = 1_000_000 * (10 ** (decimals))
    vault.deposit(whale_deposit, {"from": whale})
    vault.setManagementFee(0, {"from": gov})

    # vault.addStrategy(strategy, 10_000, 0, 2**256-1, 1000, {"from": gov})

    tx = strategy.harvest({'from': gov})
    print("Strategy takes funds in:",tx.events["Harvested"])
    chain.sleep(2016000)
    chain.mine(1)
    chain.sleep(2016000)
    chain.mine(1)
    genericStateOfStrat(strategy, currency, vault)
    #genericStateOfStrat(strategy, currency, vault)
    #genericStateOfVault(vault, currency)
    
    tx = ibcrvStrat1.harvest({"from": vGov})
    print("ibcrvStrat1",tx.events["Harvested"])
    chain.sleep(2016000)
    chain.mine(1)
    # ibcrvStrat1.harvest({"from": vGov})
    tx = ibcrvStrat1.harvest({"from": vGov})
    print("ibcrvStrat1",tx.events["Harvested"])
    chain.sleep(2016000)
    chain.mine(1)
    tx = strategy.harvest({'from': gov})
    print("Strategy",tx.events["Harvested"])
    print("Stats after first profitable harvest:",vault.strategies(strategy).dict())
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)
    chain.sleep(21600)
    chain.mine(1)
 
    # vault.withdraw({"from": whale})
    bef = currency.balanceOf(whale)
    tx = vault.withdraw(vault.balanceOf(whale),whale,10_000,{"from": whale})
    aft = currency.balanceOf(whale)
    whale_after = currency.balanceOf(whale)
    print("profit =", (whale_after - whale_before)/(10 ** (decimals)))
    print("balance left =", vault.balanceOf(whale))
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)
    vault.updateStrategyDebtRatio(strategy, 0 , {"from": gov})
    #chain.mine(1)

    strategy.harvest({'from': gov})
    genericStateOfStrat(strategy, currency, vault)

    

def test_usdc_ib_live(usdc, stratms, whale, Strategy, strategy_usdc_ib, accounts, ibyvault, chain, live_usdc_vault, ychad, gov, strategist, interface):
    # chain.reset()
    deposit_contract = Contract("0xF403C135812408BFbE8713b5A23a04b3D48AAE31")
    vault = live_usdc_vault
    currency = interface.ERC20(vault.token())
    decimals = currency.decimals()
    gov = accounts.at(vault.governance(), force=True)
    strategy = strategy_usdc_ib

    yvault = ibyvault
    #amount = 1000*1e6
    #amounts = [0, 0, amount]
    print("curveid: ", strategy.curveId())
    #print("slip: ", strategy._checkSlip(amount))
    #print("expectedOut: ", amount/strategy.virtualPriceToWant())
    print("curve token: ", strategy.curveToken())
    print("ytoken: ", strategy.yvToken())
    vault.setDepositLimit(2**256 -1 , {'from': vault.governance()})
    yvault.setDepositLimit(2**256 -1 , {'from': yvault.governance()})
    #print("real: ", ibCurvePool.calc_token_amount(amounts, True))
    currency.approve(vault, 2 ** 256 - 1, {"from": whale})
    whale_before = currency.balanceOf(whale)
    whale_deposit = 1_000_000 * (10 ** (decimals))
    vault.deposit(whale_deposit, {"from": whale})
    vault.setManagementFee(0, {"from": gov})

    #idl = Strategy.at(vault.withdrawalQueue(1))
    #vault.updateStrategyDebtRatio(idl, 0 , {"from": gov})
    #debt_ratio = 2000
    #v0.3.0
    gen_lender = interface.IStrat043("0x2216E44fA633ABd2540dB72Ad34b42C7F1557cd4")
    vault.updateStrategyDebtRatio(gen_lender, 0, {"from": gov})
    gen_lender.harvest({"from": gov})
    # vault.addStrategy(strategy, 5_000, 0, 2**256-1, 1000, {"from": gov})

    strategy.harvest({'from': gov})
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
    strategy.harvest({'from': gov})
    print(vault.strategies(strategy))
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)
    chain.sleep(21600)
    #chain.mine(1)
 
    # vault.withdraw({"from": whale})
    bef = currency.balanceOf(whale)
    tx = vault.withdraw(vault.balanceOf(whale),whale,10_000,{"from": whale})
    aft = currency.balanceOf(whale)
    whale_after = currency.balanceOf(whale)
    print("profit =", (whale_after - whale_before)/(10 ** (decimals)))
    print("balance left =", vault.balanceOf(whale))
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)
    vault.updateStrategyDebtRatio(strategy, 0 , {"from": gov})
    #chain.mine(1)

    strategy.harvest({'from': gov})
    genericStateOfStrat(strategy, currency, vault)