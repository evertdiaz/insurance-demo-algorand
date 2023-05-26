from beaker import *
from pyteal import *


class MyState:
    # Local State
    assetName = LocalStateValue(TealType.bytes)
    assetValue = LocalStateValue(TealType.uint64)
    assetDescription = LocalStateValue(TealType.bytes)
    assetState = LocalStateValue(TealType.uint64)
    # Global State
    minterAccount = GlobalStateValue(TealType.bytes)


app = Application("InsuranceApp", state=MyState).apply(
    unconditional_opt_in_approval, initialize_local_state=True
)


@app.create
def create(minter: abi.Address, *, output: abi.String) -> Expr:
    return Seq(
        app.state.minterAccount.set(minter.get()),
        output.set(Concat(Bytes("Cuenta minter seteada a: "), minter.get())),
    )


@app.external
def registerAsset(
    name: abi.String, val: abi.Uint64, desc: abi.String, *, output: abi.String
) -> Expr:
    return Seq(
        app.state.assetName[Txn.sender()].set(name.get()),
        app.state.assetValue[Txn.sender()].set(val.get()),
        app.state.assetDescription[Txn.sender()].set(desc.get()),
        app.state.assetState[Txn.sender()].set(Int(0)),
        output.set("Solicitud recibida con éxito."),
    )


@app.external(authorize=Authorize.only(Global.creator_address()))
def approveAsset(account: abi.Account, *, output: abi.String) -> Expr:
    return Seq(
        app.state.assetState[account.address()].set(Int(1)),
        output.set("Asset verificado, listo para mintear"),
    )


@app.external
def mintInsurance(account: abi.Account, *, output: abi.Uint64) -> Expr:
    return Seq(
        Assert(Txn.sender() == app.state.minterAccount.get()),
        InnerTxnBuilder.Execute(
            {
                TxnField.type_enum: TxnType.AssetConfig,
                TxnField.config_asset_unit_name: Bytes("INS"),
                TxnField.config_asset_name: Bytes("INSURANCE"),
                TxnField.config_asset_decimals: Int(0),
                TxnField.config_asset_total: Int(1),
                TxnField.note: Concat(
                    Bytes("Insurance token for asset: "),
                    app.state.assetName[account.address()].get(),
                    Bytes(" - Description: "),
                    app.state.assetDescription[account.address()].get(),
                    Bytes(" - Value: $"),
                    Itob(app.state.assetValue[account.address()].get()),
                ),
            }
        ),
        output.set(InnerTxn.created_asset_id()),
    )


@app.external
def sendInsurance(asa: abi.Asset, receiver: abi.Account, *, output: abi.String) -> Expr:
    return Seq(
        InnerTxnBuilder.Execute(
            {
                TxnField.type_enum: TxnType.AssetTransfer,
                TxnField.xfer_asset: asa.asset_id(),
                TxnField.asset_receiver: receiver.address(),
                TxnField.asset_amount: Int(1),
            }
        ),
        output.set("Asset sent"),
    )


@app.external
def hello(name: abi.String, *, output: abi.String) -> Expr:
    return output.set(Concat(Bytes("Hello, "), name.get()))


if __name__ == "__main__":
    app.build().export("./artifacts")
