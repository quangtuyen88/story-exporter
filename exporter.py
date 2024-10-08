import time
import yaml
import requests
from prometheus_client import start_http_server, Gauge

# Load config.yaml
def load_config():
    with open('config.yaml', 'r') as file:
        return yaml.safe_load(file)

# Fetch validator data from the explorer API
def fetch_validator_data(validator_address):
    url = f"https://testnet.story.api.explorers.guru/api/v1/validators/{validator_address}"

    try:
        response = requests.get(url)
        data = response.json()

        # Extract relevant fields
        commission = data['commission'].get('commission', 0) / 100  # Convert to percentage
        total_bonds = int(data['selfBond']['amount'])  # Extract tokens as total bonds
        consensus_address = data['addresses']['consensusAddress']
           # Determine validator state
        if data['jailed']:
            state = 2  # Jailed
        elif data['bondStatus'] == 'BondStatusUnbonded':
            state = 3  # Inactive (Unbonded)
        elif data['bondStatus'] == 'BondStatusBonded':
            state = 1  # Active consensus set
        else:
            state = 0  # Unknown state
        uptime_percentage = data.get('uptime', -1)  # Uptime percentage

        print(f"Validator: {validator_address}")
        print(f"Total Bonds: {total_bonds}")
        print(f"Commission: {commission}")
        print(f"Consensus Address: {consensus_address}")
        print(f"State: {state}")
        print(f"Uptime Percentage: {uptime_percentage}")

        return total_bonds, commission, consensus_address, state, uptime_percentage

    except Exception as e:
        print(f"Error fetching validator data for {validator_address}: {e}")
        return -1, -1, "", -1, -1  # Return -1 in case of an error

# Fetch validator rank and lowest active set stake from the explorers API with 10-second timeout
# Initialize variables to store the last known valid values
last_known_rank = -1
last_known_lowest_stake = -1

def fetch_validator_data_from_explorer(validator_address):
    global last_known_rank, last_known_lowest_stake
    url = "https://testnet.story.api.explorers.guru/api/v1/validators"

    try:
        # Set timeout to 10 seconds
        response = requests.get(url, timeout=10)
        data = response.json()

        # Find the rank for the specified validator
        validator_info = next((v for v in data if v['operatorAddress'] == validator_address), None)
        rank = validator_info.get('rank', -1) if validator_info else last_known_rank  # Use last known rank if None

        # Find the validator with rank 100 (lowest active set)
        validator_100 = next((v for v in data if v['rank'] == 100), None)
        lowest_stake = int(validator_100['tokens']) if validator_100 else last_known_lowest_stake  # Use last known lowest stake if None

        # Update last known values only if valid data is retrieved
        if validator_info:
            last_known_rank = rank
        if validator_100:
            last_known_lowest_stake = lowest_stake

        print(f"Validator {validator_address} Rank: {rank}")
        print(f"Lowest Active Set Stake: {lowest_stake}")

        return rank, lowest_stake

    except requests.exceptions.Timeout:
        print(f"Request timed out while fetching data from {url}. Using last known values.")
        return last_known_rank, last_known_lowest_stake

    except Exception as e:
        print(f"Error fetching data from {url}: {e}. Using last known values.")
        return last_known_rank, last_known_lowest_stake  # Return last known values in case of an error


# Fetch validator missed blocks and process heatmap data for Grafana
def fetch_validator_block_signing_status(validator_address):
    url = f"https://api.testnet.storyscan.app/blocks/uptime/{validator_address}"

    try:
        response = requests.get(url)
        data = response.json()

        # Process each block, storing whether it was signed or not
        for block in data:
            block_height = block.get('height')
            signed = block.get('signed', False)
            signed_status = 1 if signed else 0  # 1 for signed, 0 for missed

            # Update the Prometheus metric for block signed status
            block_signed_status_metric.labels(block_height=block_height, validator_address=validator_address).set(signed_status)

            print(f"Block {block_height}: {'Signed' if signed else 'Missed'}")

    except Exception as e:
        print(f"Error fetching block signing data for {validator_address}: {e}")
        return -1  # Return -1 in case of an error

# Fetch validator missed blocks
def fetch_validator_missed_blocks(validator_address):
    url = f"https://api.testnet.storyscan.app/blocks/uptime/{validator_address}"

    try:
        response = requests.get(url)
        data = response.json()

        # Count missed blocks where signed is false
        missed_blocks = sum(1 for block in data if not block['signed'])

        print(f"Validator: {validator_address}")
        print(f"Missed Blocks: {missed_blocks}")

        return missed_blocks

    except Exception as e:
        print(f"Error fetching missed blocks for {validator_address}: {e}")
        return -1  # Return -1 in case of an error


# Fetch number of delegators from the correct endpoint
def fetch_validator_delegators(validator_address):
    url = f"https://api.testnet.storyscan.app/validators/{validator_address}/delegators"

    try:
        response = requests.get(url)
        data = response.json()

        # Extract the number of delegators
        delegators = data.get('validatorDelegators', -1)

        print(f"Delegators for {validator_address}: {delegators}")
        return delegators

    except Exception as e:
        print(f"Error fetching delegators for {validator_address}: {e}")
        return -1  # Return -1 in case of an error

# Fetch stake threshold from the parameters endpoint
def fetch_stake_threshold():
    url = "https://api.testnet.storyscan.app/utilities/parameters"

    try:
        response = requests.get(url)
        data = response.json()

        # Extract historicalEntries as the stake threshold
        stake_threshold = data['staking'].get('historicalEntries', 0)
        print(f"Stake Threshold: {stake_threshold}")

        return stake_threshold
    except Exception as e:
        print(f"Error fetching stake threshold: {e}")
        return -1  # Return -1 in case of an error

# Fetch max set size (maxValidators) from the parameters endpoint
def fetch_max_set_size():
    url = "https://api.testnet.storyscan.app/utilities/parameters"

    try:
        response = requests.get(url)
        data = response.json()

        # Extract maxValidators from the response
        max_set_size = data['staking'].get('maxValidators', 0)
        print(f"Max Set Size: {max_set_size}")

        return max_set_size
    except Exception as e:
        print(f"Error fetching max set size: {e}")
        return -1  # Return -1 in case of an error

# Initialize Prometheus metrics
uptime_percentage_metric = Gauge('story_validator_uptime_percentage', 'Validator uptime in percentage; -1 value if validator not in active set', ['validator_address', 'consensu_address', 'chain_id'])
state_metric = Gauge('story_validator_state', 'Validator state; 0 - unknown, 1 - active consensus set, 2 - jailed, 3 - inactive', ['validator_address', 'consensu_address', 'chain_id'])
delegators_metric = Gauge('story_validator_delegators', 'Number of delegators; -1 value if not in active set', ['validator_address', 'consensu_address', 'chain_id'])
rank_metric = Gauge('story_validator_active_set_rank', 'Validator active set rank; -1 value if not in active set', ['validator_address', 'consensu_address', 'chain_id'])
max_set_size_metric = Gauge('story_network_max_set_size', 'Max set size', ['chain_id'])
lowest_active_set_stake_metric = Gauge('story_network_lowest_active_set_stake', 'Lowest active set stake', ['chain_id'])
stake_threshold_metric = Gauge('story_network_stake_threshold', 'Stake threshold', ['chain_id'])
missed_blocks_metric = Gauge('story_validator_missed_blocks', 'Validator missed blocks in last 120 blocks; -1 value if not in active set', ['validator_address', 'consensu_address', 'chain_id'])
total_bonds_metric = Gauge('story_validator_total_bonds', 'Validator total bonds', ['validator_address', 'consensu_address', 'chain_id'])
commission_metric = Gauge('story_validator_commission', 'Validator commission', ['validator_address', 'consensu_address', 'chain_id'])

# New metric for block signing status for heatmap
block_signed_status_metric = Gauge('block_signed_status', 'Block signed status; 1 - signed, 0 - missed', ['block_height', 'validator_address'])

# Update metrics for each validator
def update_validator_metrics(validators, chain_id):
    for validator in validators:
        validator_address = validator['validator_address']

        # Fetch total bonds, commission, consensus address, state, uptime_percentage
        total_bonds, commission, consensu_address, state, uptime_percentage = fetch_validator_data(validator_address)

        # Fetch rank and lowest active set stake with 10s timeout
        rank, lowest_stake = fetch_validator_data_from_explorer(validator_address)

        # # Fetch missed blocks and process for heatmap
        # fetch_validator_block_signing_status(validator_address)

         # Fetch missed blocks
        missed_blocks = fetch_validator_missed_blocks(validator_address)

        # Fetch delegators
        delegators = fetch_validator_delegators(validator_address)

        # Update Prometheus metrics for validator
        total_bonds_metric.labels(validator_address, consensu_address, chain_id).set(total_bonds)
        commission_metric.labels(validator_address, consensu_address, chain_id).set(commission)
        missed_blocks_metric.labels(validator_address, consensu_address, chain_id).set(missed_blocks)  # Missed blocks already processed for heatmap
        uptime_percentage_metric.labels(validator_address, consensu_address, chain_id).set(uptime_percentage)
        state_metric.labels(validator_address, consensu_address, chain_id).set(state)
        delegators_metric.labels(validator_address, consensu_address, chain_id).set(delegators)
        rank_metric.labels(validator_address, consensu_address, chain_id).set(rank)

# Update network metrics
def update_network_metrics(chain_id):
    # Fetch and update stake threshold
    stake_threshold = fetch_stake_threshold()
    stake_threshold_metric.labels(chain_id=chain_id).set(stake_threshold)

    # Fetch and update max set size
    max_set_size = fetch_max_set_size()
    max_set_size_metric.labels(chain_id=chain_id).set(max_set_size)

    # Fetch and update lowest active set stake (reuse the same API call)
    _, lowest_stake = fetch_validator_data_from_explorer(None)  # Fetch for rank 100 (lowest active set)
    lowest_active_set_stake_metric.labels(chain_id=chain_id).set(lowest_stake)


# Main function to start exporter
if __name__ == '__main__':
    config = load_config()
    validators = config['validators']
    chain_id = "iliad-0"  # Hardcoded chain_id, can be customized

    # Start up the server to expose metrics.
    start_http_server(8000)
    print("Exporter started on port 8000")

    # Update metrics every 60 seconds for large data sets like lowest_active_set_stake
    while True:
        update_validator_metrics(validators, chain_id)
        update_network_metrics(chain_id)
        time.sleep(30)
