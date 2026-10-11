# VIN09.3

Vin is a local modular AI assistant designed to run independently on Android/Termux.

## Start

```bash
python main.py
```

## Development checks

```bash
./vin-dev status
./vin-dev compile
./vin-dev test
./vin-dev check
./vin-dev run
./vin-dev backup
```

The self-test uses a temporary isolated state directory, so it does not modify Vin's real memory, conversation, topic, or permission files.

Vin's optional language-model bridge is local-only (`127.0.0.1`) and is not required for the built-in cognitive system to run.

Android actions are permission-controlled and do not bypass Android security.
