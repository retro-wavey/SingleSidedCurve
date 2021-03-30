import pytest
from brownie import config

@pytest.fixture
def andre(accounts):
    # Andre, giver of tokens, and maker of yield
    yield accounts[0]

@pytest.fixture
def currency(interface):
    #this one is hbtc
    yield interface.ERC20('0x0316EB71485b0Ab14103307bf65a021042c6d380')

@pytest.fixture
def wbtc(interface):
    #this one is hbtc
    yield interface.ERC20('0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599')

@pytest.fixture
def whale(accounts, web3, currency, chain, wbtc):
    #big binance7 wallet
    #acc = accounts.at('0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8', force=True)
    #big binance8 wallet
    #acc = accounts.at('0x006d0f31a00e1f9c017ab039e9d0ba699433a28c', force=True)
    #big bridge wallet
    acc = accounts.at('0xA929022c9107643515F5c777cE9a910F0D1e490C', force=True)

    #wbtc account
    wb = accounts.at('0x3dfd23A6c5E8BbcFc9581d2E864a68feb6a076d3', force=True)
    wbtc.transfer(acc, wbtc.balanceOf(wb),  {'from': wb})



    assert currency.balanceOf(acc)  > 0
    assert wbtc.balanceOf(acc)  > 0
    yield acc


@pytest.fixture
def yvaultv1(interface):
    yield interface.IVaultV1('0x46AFc2dfBd1ea0c0760CAD8262A5838e803A37e5')
@pytest.fixture
def yvaultv2(interface):
    yield interface.IVaultV2('0x625b7DF2fa8aBe21B0A976736CDa4775523aeD1E')

@pytest.fixture
def yhbtcstrategyv1(interface):
    yield interface.IStratV1('0xE02363cB1e4E1B77a74fAf38F3Dbb7d0B70F26D7')

@pytest.fixture
def yhbtcstrategyv2(Strategy):
    yield Strategy.at('0x91cBf0014a966615e1050c90A1aBf1d1d5d8cffd')

@pytest.fixture
def hCRV(interface):
    yield interface.ICrvV3('0xb19059ebb43466C323583928285a49f558E572Fd')
@pytest.fixture
def curvePool(interface):
    yield interface.ICurveFi('0x4CA9b3063Ec5866A4B82E437059D2C43d1be596F')

@pytest.fixture
def devms(accounts):
    acc = accounts.at('0x846e211e8ba920B353FB717631C015cf04061Cc9', force=True)
    yield acc
@pytest.fixture
def orb(accounts):
    acc = accounts.at('0x710295b5f326c2e47e6dd2e7f6b5b0f7c5ac2f24', force=True)
    yield acc
    

@pytest.fixture
def ychad(accounts):
    acc = accounts.at('0xFEB4acf3df3cDEA7399794D0869ef76A6EfAff52', force=True)
    yield acc

@pytest.fixture
def samdev(accounts):
    #big binance7 wallet
    #acc = accounts.at('0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8', force=True)
    #big binance8 wallet
    acc = accounts.at('0xC3D6880fD95E06C816cB030fAc45b3ffe3651Cb0', force=True)


    
    yield acc

@pytest.fixture
def token(andre, Token):
    yield andre.deploy(Token)


@pytest.fixture
def gov(accounts):
    # yearn multis... I mean YFI governance. I swear!
    yield accounts[1]


@pytest.fixture
def rewards(gov):
    yield gov  # TODO: Add rewards contract


@pytest.fixture
def guardian(accounts):
    # YFI Whale, probably
    yield accounts[2]


@pytest.fixture
def vault(pm, gov, rewards, guardian, currency):
    Vault = pm(config["dependencies"][0]).Vault
    vault = gov.deploy(Vault)
    vault.initialize(currency, gov, rewards, "", "", guardian)
    vault.setDepositLimit(2 ** 256 - 1, {"from": gov})
    yield vault
    
@pytest.fixture
def wbtc_vault(pm, gov, rewards, guardian, wbtc):
    currency = wbtc
    Vault = pm(config["dependencies"][0]).Vault
    vault = gov.deploy(Vault)
    vault.initialize(currency, gov, rewards, "", "", guardian)
    vault.setDepositLimit(2 ** 256 - 1, {"from": gov})
    yield vault

@pytest.fixture
def live_wbtc_vault(pm, gov, rewards, guardian, wbtc):
    currency = wbtc
    Vault = pm(config["dependencies"][0]).Vault
    vault = gov.deploy(Vault)
    vault.initialize(currency, gov, rewards, "", "", guardian)
    vault.setDepositLimit(2 ** 256 - 1, {"from": gov})
    yield vault

@pytest.fixture
def strategist(accounts):
    # You! Our new Strategist!
    yield accounts[3]


@pytest.fixture
def keeper(accounts):
    # This is our trusty bot!
    yield accounts[4]

@pytest.fixture
def live_strategy(Strategy):
    strategy = Strategy.at('0xa371fC9d259c614258e8eEc066D9eB74C58b8247')

    yield strategy


@pytest.fixture
def live_strategy2(Strategy):
    strategy = Strategy.at('0x308518f220D5c6FBeF497ac7744D3D1194c7AFF9')

    yield strategy

@pytest.fixture
def live_vault(pm):
    Vault = pm(config["dependencies"][0]).Vault
    vault = Vault.at('0xBF7AA989192b020a8d3e1C65a558e123834325cA')
    yield vault

@pytest.fixture
def strategy(strategist, keeper, vault, Strategy):
    strategy = strategist.deploy(Strategy, vault, 2*1e18)
    strategy.setKeeper(keeper)
    yield strategy

@pytest.fixture
def zapper(strategist, ZapSteth):
    zapper = strategist.deploy(ZapSteth)
    yield zapper


@pytest.fixture
def nocoiner(accounts):
    # Has no tokens (DeFi is a ponzi scheme!)
    yield accounts[5]


@pytest.fixture
def pleb(accounts, andre, token, vault):
    # Small fish in a big pond
    a = accounts[6]
    # Has 0.01% of tokens (heard about this new DeFi thing!)
    bal = token.totalSupply() // 10000
    token.transfer(a, bal, {"from": andre})
    # Unlimited Approvals
    token.approve(vault, 2 ** 256 - 1, {"from": a})
    # Deposit half their stack
    vault.deposit(bal // 2, {"from": a})
    yield a


@pytest.fixture
def chad(accounts, andre, token, vault):
    # Just here to have fun!
    a = accounts[7]
    # Has 0.1% of tokens (somehow makes money trying every new thing)
    bal = token.totalSupply() // 1000
    token.transfer(a, bal, {"from": andre})
    # Unlimited Approvals
    token.approve(vault, 2 ** 256 - 1, {"from": a})
    # Deposit half their stack
    vault.deposit(bal // 2, {"from": a})
    yield a


@pytest.fixture
def greyhat(accounts, andre, token, vault):
    # Chaotic evil, will eat you alive
    a = accounts[8]
    # Has 1% of tokens (earned them the *hard way*)
    bal = token.totalSupply() // 100
    token.transfer(a, bal, {"from": andre})
    # Unlimited Approvals
    token.approve(vault, 2 ** 256 - 1, {"from": a})
    # Deposit half their stack
    vault.deposit(bal // 2, {"from": a})
    yield a


