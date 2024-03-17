import bittensor as bt
import os
import pandas as pd
import time
import libtmux
import argparse

class NetworkException(Exception):
    pass

class RegistrationBot:
    def __init__(self, coldWalletName, model_name, manager, max_registration_cost):
        print("version", bt.__version__)
        self.coldWalletName = coldWalletName
        self.sessionManager = manager
        self.model_name = model_name
        self.max_registration_cost = max_registration_cost
        self.wallet = bt.wallet(self.coldWalletName)

    def init(self):
        self.subtensor = bt.subtensor()
        self.sessionManager.check_session()
        self.wallet.coldkey
        self.address = self.wallet.coldkeypub.ss58_address

    def restart(self):
        self.sync()

        miners = self.df.to_dict(orient='records')
        hotkey_map = self.read_hotkeys()
        key_to_name = {v: k for k, v in hotkey_map.items()}
        for i, miner in enumerate(miners):
            print(f"restarting {i+1}/{len(miners)} miner")
            print("miner parameters", miner)
            hotkey = miner['hotkey']
            if not hotkey in key_to_name:
                raise Exception(f"missing hotkey {hotkey}")
            hotkey_name = key_to_name[hotkey]
            print(f"miner name {hotkey_name}")
            port = miner['port']
            if port is None:
                raise Exception(f"port {port} for hotkey {hotkey_name}, uid {miner['uid']} is unexpected")
            runscript = self.getRunScript(hotkey_name, miner['port'])
            self.sessionManager.run(hotkey_name, runscript)
            print(f"restarted...\n")
            print(f"sleeping 10s")
            time.sleep(10)
        print(f"restarted {len(miners)} miners successfully")

    def run(self):
        # validate that price is below max threshold
        price = self.get_price()
        if self.get_price() > self.max_registration_cost:
            raise NetworkException(f"cost={price} exceeds max={self.max_registration_cost}")
        print(f"registration costs {price}")

        self.sync()
        if self.df.shape[0] > 17:
            raise NetworkException(f"MAX PROCESSES ON INSTANCE REACHED: {self.df.shape[0]}")

        # label wallet with hotkey
        self.resetHotkey()
        hotkey = self.getKeyToUse()
        self.wallet.hotkey_str = hotkey
        print(f"using hotkey {hotkey}")

        # register the hotkey
        uid = self.register(hotkey)
        print(f"uid {uid} registered to {hotkey}")

        # run script
        runscript = self.getRunScript(hotkey)
        self.sessionManager.run(hotkey, runscript)

    def run_hotkey(self, hotkey):
        self.sync()
        runscript = self.getRunScript(hotkey)
        self.sessionManager.run(hotkey, runscript)

    def getRunScript(self, hotkey, port=None):
        if port is None:
            port = self.findAvailablePort()
        # TODO: for SN1. change for different subnets
        type = 'zephyr'
        script = f"python3 neurons/miners/{type}/miner.py \
            --netuid 1 \
            --wallet.name {self.coldWalletName} \
            --wallet.hotkey {hotkey} \
            --logging.debug \
            --wandb.on true \
            --axon.port {port} \
            --neuron.model_id {self.model_name}"
        return script

    def register(self, hotkey):
        print(f"registering {hotkey}")
        registration_success = self.subtensor.burned_register(self.wallet, 1)
        if not registration_success:
            raise NetworkException(f"unable to register {hotkey}")

        print(f"getting UID for {hotkey}")
        uid = self.subtensor.get_uid_for_hotkey_on_subnet(self.wallet.hotkey.ss58_address, 1)
        if uid is None:
            raise NetworkException("Registered UID not detected")
        print(f"UID is {uid}")
        return uid

    def getKeyToUse(self):
        keyMap= self.read_hotkeys()
        activeKeys = set(list(self.df.hotkey))
        for name, key in keyMap.items():
            if key in activeKeys:
                continue
            else:
                return name
        return self.newHot()

    def newHot(self):
        existingNames = self.read_hotkeys().keys()
        proposedName = ''
        for i in range(1, 40):
            proposedName = f"{self.coldWalletName}-{i}"
            if proposedName in existingNames:
                continue
        if proposedName == '':
            raise NetworkException('no hotkey name found')
        print(f"creating new hotkey from {self.wallet.hotkey_str}...")
        self.wallet.hotkey_str = proposedName
        self.wallet.new_hotkey()
        return proposedName

    def sync(self):

        print('syncing metagraph...')
        metagraph = self.subtensor.metagraph(1)
        print('sync complete, dumping metagraph')

        meta_cols = ['I','stake','trust','validator_trust','C','R','E','dividends','last_update']
        df_m = pd.DataFrame({k: getattr(metagraph, k) for k in meta_cols})

        df_m['uid'] = range(metagraph.n.item())
        df_m['hotkey'] = list(map(lambda a: a.hotkey, metagraph.axons))
        df_m['coldkey'] = list(map(lambda a: a.coldkey, metagraph.axons))
        df_m['ip'] = list(map(lambda a: a.ip, metagraph.axons))
        df_m['port'] = list(map(lambda a: a.port, metagraph.axons))
        hotkeys = self.read_hotkeys().values()
        df_m['my_miners'] = df_m.hotkey.isin(hotkeys)

        df_m = df_m.loc[df_m['my_miners'] == True]
        self.df = df_m
        print("current miner distribution")
        print(self.df)

    def get_price(self):
        burnPrice = self.subtensor.burn(1)
        return burnPrice.tao

    def read_hotkeys(self):
        hotkeys_path = os.path.join("~/.bittensor/wallets", self.coldWalletName, "hotkeys")
        hotkeys = next(os.walk(os.path.expanduser(hotkeys_path)))
        nameToAddress = {}
        if len(hotkeys) > 1:
            for h_name in hotkeys[2]:
                wallet = bt.wallet(self.coldWalletName, h_name)
                address = wallet.hotkey.ss58_address
                nameToAddress[h_name] = address
        return nameToAddress

    def findAvailablePort(self):
        usedPorts = set(list(self.df.port))
        availablePorts = [i for i in range(8050, 8080)]
        for port in availablePorts:
            if port in usedPorts:
                continue
            else:
                return port
        raise Exception("no available port")

    def resetHotkey(self):
        self.wallet.hotkey_str = None
        self.wallet._hotkey = None



class TmuxManager:
    def __init__(self):
        self.server = libtmux.Server()
        self.session = self.server.find_where({"session_name": "btmanager"})

    def check_session(self):
        if self.session is None:
            raise Exception("btmanager session does not exist")

    def run(self, windowKey, runscript):
        old_window =  self.session.find_where({"window_name": windowKey})
        if old_window:
            print(f"killing old window for {windowKey}")
            old_window.kill_window()
        window = self.session.new_window(window_name=windowKey, attach=False, start_directory="~/prompting")
        # check if pane is attached already
        pane = window.attached_pane
        if pane is None:
            pane = window.split_window(attach=False)
        pane.send_keys(runscript)


if __name__ == "__main__":
    manager = TmuxManager()

    default_model_name = "gpt-3.5-turbo"
    default_max_registration_cost = 0.15

    parser = argparse.ArgumentParser()
    parser.add_argument("--wallet", type=str, help="cold wallet name", required=True)
    parser.add_argument("--model", type=str, help="model name", default=default_model_name)
    parser.add_argument("--max-cost", type=float, help="maximum cost for registration", default=default_max_registration_cost)
    parser.add_argument("--restart", type=bool, help="restart all miners with updated code/model", default=False)
    args = parser.parse_args()


    registrar = RegistrationBot(args.wallet, args.model, manager, args.max_cost)
    registrar.read_hotkeys()
    registrar.init()

    if args.restart:
        registrar.restart()

    while True:
        try:
            registrar.run()
        except NetworkException as e:
            print(e)
        finally:
            # actions to make sure tmux state is correct
            pass
        print('sleeping for 120s')
        time.sleep(120)
