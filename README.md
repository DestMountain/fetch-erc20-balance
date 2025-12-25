# Base Sepolia 历史余额查询脚本

基于 `web3.py` 的简单脚本，用于查询指定地址在 **Base Sepolia** 测试网多个区块高度的多种 ERC-20 代币历史余额，并输出可读结果与 JSON 文件。

## 功能

- 批量查询多个代币、多个区块高度的历史余额
- 自动读取代币小数位并换算成人类可读金额
- 异步请求并带有基础节流，降低公共 RPC 限流风险
- 结果输出到终端并保存为 `balances_result.json`

## 环境要求

- Python 3.8+
- web3.py

## 安装依赖

```bash
pip install web3
```

## 使用方式

1. 修改 `fetch.py` 中的配置：
   - `RPC_URL`：RPC 节点地址
   - `YOUR_ADDRESS`：你的钱包地址（建议使用小写地址）
   - `TOKEN_ADDRESSES`：要查询的代币合约地址列表
   - `BLOCK_NUMBERS`：要查询的区块高度列表
2. 运行脚本：

```bash
python fetch.py
```

## 输出说明

脚本会打印每个代币在各区块的余额，并把结果写入 `balances_result.json`。示例结构：

```json
{
  "0xTokenAddress": {
    "5000000": {
      "raw": 123456789,
      "human": 123.456789
    }
  }
}
```

字段含义：

- `raw`：链上原始整数余额
- `human`：根据代币 `decimals` 换算后的可读余额

## 备注

- `decimals` 默认只在第一个区块读取一次（代币小数位通常不可变）。
- 使用公共 RPC 可能出现限流或连接失败，可适当提高 `asyncio.sleep` 的间隔或更换 RPC。
