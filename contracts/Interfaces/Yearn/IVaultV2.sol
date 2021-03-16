// SPDX-License-Identifier: MIT

pragma solidity 0.6.12;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

interface IVaultV2 is IERC20 {
    function deposit(uint256) external;

    function deposit() external;

    function withdraw(uint256) external;

    function withdraw() external;

    function pricePerShare() external view returns (uint256);
}
