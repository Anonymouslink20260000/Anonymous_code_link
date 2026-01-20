# Batch Prompt Optimization Tool

A Python script for batch optimization of prompts using multiple LLM models (Qwen API, OpenAI GPT, Anthropic Claude, and Ollama local models including DeepSeek). Supports both single system prompt mode and dual-variant system prompt mode.

## Features

- **Multi-model support**: Works with Qwen API, OpenAI GPT, Anthropic Claude, and Ollama local models (including DeepSeek)
- **Dual-variant mode**: Supports running prompts with two different system prompt variants (no_opt/opt)
- **Automatic retry**: Built-in retry mechanism for handling network errors and timeouts
- **Result saving**: Saves results for each model separately and generates summary files
- **Error handling**: Robust error handling with detailed logging

## Requirements

- Python 3.8+
- Required packages:
  ```bash
  pip install langchain-openai langchain-core langchain-anthropic pandas openpyxl
  ```
  
  Or install from requirements.txt:
  ```bash
  pip install -r requirements.txt
  ```

## Configuration

### Environment Variables

Set the following environment variables before running:

```bash
# Required for Qwen API models
export QWEN_API_KEY="your_api_key_here"

# Required for OpenAI GPT models
export OPENAI_API_KEY="your_openai_api_key_here"

# Required for Anthropic Claude models
export ANTHROPIC_API_KEY="your_anthropic_api_key_here"

# Optional: Customize API endpoints
export QWEN_API_BASE="https://dashscope.aliyuncs.com/compatible-mode/v1"
export OPENAI_API_BASE="https://api.openai.com/v1"
export OLLAMA_BASE_URL="http://localhost:11434/v1"
```

### Configuration in Code

Edit the following variables in `batch_optimize.py`:

```python
# Input prompts file (one prompt per line)
PROMPTS_FILE = "null_350.txt"

# System prompt file (optional, for dual-variant mode)
# If no optimization variant: import "ablated system prompt.txt"
# Otherwise: import "full system prompt.txt"
SYSTEM_FILE = "system_prompt.txt"

# Model configurations
DEFAULT_MODELS = [
    ("llama3:8b", "ollama"),
    ("qwen-max", "qwen"),
    ("qwen3:4b", "ollama"),
    ("deepseek-coder-v2:16b", "ollama"),  # DeepSeek via Ollama
    ("gpt-4o", "gpt"),  # OpenAI GPT
    ("claude-3-5-sonnet-20241022", "claude"),  # Anthropic Claude
]
```

## Usage

### Basic Usage

1. **Prepare your prompts file**: Create a text file with one prompt per line (e.g., `null_350.txt`)

2. **Set environment variables**: Set `QWEN_API_KEY` if using Qwen models

3. **Run the script**:
   ```bash
   python batch_optimize.py
   ```

### Single System Prompt Mode

By default, the script uses a built-in system prompt. Simply run:

```bash
python batch_optimize.py
```

### Dual-Variant Mode

To use dual-variant mode (no_opt/opt):

1. **Create system prompt file**: Create `system_prompt.txt` with the following format:
   ```
   If no optimization variant：
   import "ablated system prompt.txt"
   
   Otherwise：
   import "full system prompt.txt"
   ```

2. **Run the script**: The script will automatically detect the file and run both variants for each model.

### Model Types

- **Qwen API** (`model_type="qwen"`): Requires `QWEN_API_KEY` environment variable
- **Ollama** (`model_type="ollama"`): Requires Ollama running locally on `http://localhost:11434`
  - Supports all Ollama models including DeepSeek (e.g., `deepseek-coder-v2:16b`)
- **OpenAI GPT** (`model_type="gpt"`): Requires `OPENAI_API_KEY` environment variable
  - Supports GPT-4, GPT-3.5, and other OpenAI models
- **Anthropic Claude** (`model_type="claude"`): Requires `ANTHROPIC_API_KEY` environment variable
  - Supports Claude 3.5 Sonnet, Claude 3 Opus, and other Claude models

## Output

Results are saved in the `optimization_results/` directory:

- **Individual model results**: `{model_name}_optimized.txt` and `{model_name}_optimized.json`
- **Variant results** (if using dual-variant mode): `{model_name}__{variant_name}.txt` and `{model_name}__{variant_name}.json`
- **Summary file**: `all_results_{timestamp}.json`

### Output Format

**Text files** contain:
- Model name and variant (if applicable)
- Optimization timestamp
- For each prompt:
  - Original prompt
  - Optimized prompt

**JSON files** contain:
- Model metadata
- Complete results array with original and optimized prompts

## Retry Mechanism

The script includes automatic retry for:
- HTTP 502, 503, 504 errors
- Timeout errors
- Connection errors

Retry configuration:
- Maximum retries: 3 (configurable via `MAX_RETRIES`)
- Retry delay: Exponential backoff starting at 2 seconds (configurable via `RETRY_DELAY`)

## Error Handling

- Network errors: Automatically retried with exponential backoff
- API errors: Logged with full traceback
- Missing files: Clear error messages indicating what's missing
- Invalid configuration: Validation errors with helpful messages

## Examples

### Example 1: Basic Usage with Qwen

```bash
export QWEN_API_KEY="your_key"
python batch_optimize.py
```

### Example 2: Using Only Ollama Models

Edit `DEFAULT_MODELS` in the script:
```python
DEFAULT_MODELS = [
    ("llama3:8b", "ollama"),
    ("qwen3:4b", "ollama"),
]
```

### Example 3: Custom Prompts File

Edit `PROMPTS_FILE`:
```python
PROMPTS_FILE = "my_custom_prompts.txt"
```

## Troubleshooting

### "QWEN_API_KEY environment variable is not set"
- Set the environment variable: `export QWEN_API_KEY="your_key"`

### "OPENAI_API_KEY environment variable is not set"
- Set the environment variable: `export OPENAI_API_KEY="your_key"`

### "ANTHROPIC_API_KEY environment variable is not set"
- Set the environment variable: `export ANTHROPIC_API_KEY="your_key"`

### "langchain-anthropic package is not installed"
- Install the package: `pip install langchain-anthropic`

### "Prompts file not found"
- Check that `PROMPTS_FILE` points to an existing file
- Verify the file path is correct

### "Connection refused" (Ollama)
- Ensure Ollama is running: `ollama serve`
- Check that `OLLAMA_BASE_URL` is correct
- For DeepSeek models, ensure the model is pulled: `ollama pull deepseek-coder-v2:16b`

### "502/503/504 errors"
- The script will automatically retry
- Check your network connection
- For API models: Verify your API key is valid and has sufficient credits/quota

## File Structure

```
.
├── batch_optimize.py          # Main script
├── README.md                  # This file
├── null_350.txt              # Input prompts (example)
├── system_prompt.txt         # System prompt variants (optional)
└── optimization_results/     # Output directory
    ├── {model}_optimized.txt
    ├── {model}_optimized.json
    └── all_results_{timestamp}.json
```

## Notes

- The script processes prompts sequentially to avoid overwhelming the API
- Each model's results are saved immediately after completion
- Windows filename restrictions are handled automatically (special characters are replaced)
- All output files use UTF-8 encoding

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]

