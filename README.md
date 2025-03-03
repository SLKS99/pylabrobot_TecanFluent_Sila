# PyLabRobot Tecan Fluent SiLA2 Integration

This repository contains a SiLA2-based integration between PyLabRobot and the Tecan Fluent liquid handling robot. The integration enables automated liquid handling operations with support for multi-channel pipetting and worklist execution.

## Features

- SiLA2-based communication with Tecan Fluent Control
- Multi-channel pipetting support
- Worklist execution support
- Comprehensive test suite for connection verification

## Prerequisites

- Python 3.8 or higher
- Tecan Fluent Control software
- UnitelLabs Tecan Fluent Control package
- SiLA2 Python package

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/SLKS99/pylabrobot_TecanFluent_Sila.git
   cd pylabrobot_TecanFluent_Sila
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Testing the Connection

1. Edit the `test_tecan_connection.py` file to set the correct host and port for your Tecan Fluent:
   ```python
   test = TecanConnectionTest(
       host="your_tecan_host",  # Default: localhost
       port=50051               # Default: 50051
   )
   ```

2. Run the test script:
   ```bash
   python test_tecan_connection.py
   ```

The test script will:
- Verify basic connection to the Tecan Fluent
- Test multi-channel pipetting operations
- Execute a simple worklist file

## Troubleshooting

### Common Issues

1. Connection Failed
   - Verify that the Tecan Fluent Control software is running
   - Check if the host and port settings are correct
   - Ensure the network connection is stable

2. UnitelLabs Package Issues
   - Make sure you have the correct version installed
   - Check if your license is valid and active

### Support

- For PyLabRobot issues: [PyLabRobot Issues](https://github.com/PyLabRobot/pylabrobot/issues)
- For UnitelLabs support: Contact your Tecan representative
- For Tecan Fluent hardware issues: Contact Tecan support