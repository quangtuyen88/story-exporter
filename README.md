## Story Validator Exporter

![Screenshot 2024-10-03 at 21 41 06](https://github.com/user-attachments/assets/76f5ad22-01b7-4cca-ba85-dce7dcfe5dfd)

![Screenshot 2024-10-03 at 21 03 57](https://github.com/user-attachments/assets/c777b620-d385-492a-b108-c4bd13197d0a)


## Grafana dashboard 
Checkout this dashboard : https://github.com/quangtuyen88/story-monitoring/tree/main/prometheus/grafana/dashboards


http://story-grafana.kzvn.xyz:3000/d/validator-gc-monitoring1/validator-and-python-gc-monitoring?orgId=1&refresh=5s

## Install :
```bash
sudo apt update
sudo apt install python3 python3-pip -y
pip3 install prometheus_client pyyaml requests

cd && git clone https://github.com/quangtuyen88/story-exporter && cd story-exporter
```
Update config file `config.yaml`. 
Create a systemd Service File : 

```bash
# create service file
sudo tee /etc/systemd/system/node_exporter.service > /dev/null <<EOF
[Unit]
Description=Node exporter 
After=network-online.target
[Service]
User=$USER
WorkingDirectory=$HOME/story-exporter
ExecStart=$(which python3) $HOME/story-exporter/exporter.py
Restart=on-failure
RestartSec=5
LimitNOFILE=4000
[Install]
WantedBy=multi-user.target
EOF
```
Start service :
```bash
systemctl daemon-reload
systemctl start node_exporter
```

## Metrics expose example :

```bash
# HELP story_validator_uptime_percentage Validator uptime in percentage; -1 value if validator not in active set
# TYPE story_validator_uptime_percentage gauge
story_validator_uptime_percentage{chain_id="iliad-0",consensu_address="storyvalcons1ljcml8a6ee5pjymaljvey4ghtd72y0za7p9f83",validator_address="storyvaloper1ljcml8a6ee5pjymaljvey4ghtd72y0za2jk4ts"} 92.89
# HELP story_validator_state Validator state; 0 - unknown, 1 - active consensus set, 2 - jailed, 3 - inactive
# TYPE story_validator_state gauge
story_validator_state{chain_id="iliad-0",consensu_address="storyvalcons1ljcml8a6ee5pjymaljvey4ghtd72y0za7p9f83",validator_address="storyvaloper1ljcml8a6ee5pjymaljvey4ghtd72y0za2jk4ts"} 1.0
# HELP story_validator_delegators Number of delegators; -1 value if not in active set
# TYPE story_validator_delegators gauge
story_validator_delegators{chain_id="iliad-0",consensu_address="storyvalcons1ljcml8a6ee5pjymaljvey4ghtd72y0za7p9f83",validator_address="storyvaloper1ljcml8a6ee5pjymaljvey4ghtd72y0za2jk4ts"} 268.0
# HELP story_validator_active_set_rank Validator active set rank; -1 value if not in active set
# TYPE story_validator_active_set_rank gauge
story_validator_active_set_rank{chain_id="iliad-0",consensu_address="storyvalcons1ljcml8a6ee5pjymaljvey4ghtd72y0za7p9f83",validator_address="storyvaloper1ljcml8a6ee5pjymaljvey4ghtd72y0za2jk4ts"} -1.0
# HELP story_network_max_set_size Max set size
# TYPE story_network_max_set_size gauge
story_network_max_set_size{chain_id="iliad-0"} 100.0
# HELP story_network_lowest_active_set_stake Lowest active set stake
# TYPE story_network_lowest_active_set_stake gauge
story_network_lowest_active_set_stake{chain_id="iliad-0"} 1.3525e+013
# HELP story_network_stake_threshold Stake threshold
# TYPE story_network_stake_threshold gauge
story_network_stake_threshold{chain_id="iliad-0"} 10000.0
# HELP story_validator_missed_blocks Validator missed blocks in last 120 blocks; -1 value if not in active set
# TYPE story_validator_missed_blocks gauge
story_validator_missed_blocks{chain_id="iliad-0",consensu_address="storyvalcons1ljcml8a6ee5pjymaljvey4ghtd72y0za7p9f83",validator_address="storyvaloper1ljcml8a6ee5pjymaljvey4ghtd72y0za2jk4ts"} 12.0
# HELP story_validator_total_bonds Validator total bonds
# TYPE story_validator_total_bonds gauge
story_validator_total_bonds{chain_id="iliad-0",consensu_address="storyvalcons1ljcml8a6ee5pjymaljvey4ghtd72y0za7p9f83",validator_address="storyvaloper1ljcml8a6ee5pjymaljvey4ghtd72y0za2jk4ts"} 1.0000011e+015
# HELP story_validator_commission Validator commission
# TYPE story_validator_commission gauge
story_validator_commission{chain_id="iliad-0",consensu_address="storyvalcons1ljcml8a6ee5pjymaljvey4ghtd72y0za7p9f83",validator_address="storyvaloper1ljcml8a6ee5pjymaljvey4ghtd72y0za2jk4ts"} 0.1
```

