# Cursor MCP Configuration

## Setup Instructions

### 1. Create Your Local Configuration

Copy the example configuration file:

```bash
cp .cursor/mcp.json.example .cursor/mcp.json
```

### 2. Add Your API Keys

Edit `.cursor/mcp.json` and replace the placeholder values:

- `ANTHROPIC_API_KEY`: Your Anthropic API key (get it from https://console.anthropic.com/)
- `PERPLEXITY_API_KEY`: Your Perplexity API key (get it from https://www.perplexity.ai/settings/api)

### 3. Keep Your Secrets Safe

⚠️ **IMPORTANT**: 
- `.cursor/mcp.json` is already in `.gitignore` and will NOT be committed to Git
- Never commit files containing API keys
- Keep your API keys secure and rotate them if exposed

## Configuration Options

You can customize these environment variables in `mcp.json`:

- `MODEL`: The Claude model to use (default: `claude-3-7-sonnet-20250219`)
- `PERPLEXITY_MODEL`: The Perplexity model to use (default: `sonar-pro`)
- `MAX_TOKENS`: Maximum tokens for AI responses (default: `64000`)
- `TEMPERATURE`: Temperature for AI model responses (default: `0.2`)
- `DEFAULT_SUBTASKS`: Default number of subtasks for task expansion (default: `5`)
- `DEFAULT_PRIORITY`: Default priority for new tasks (default: `medium`)

## Troubleshooting

If you encounter issues:

1. Verify your API keys are valid
2. Check that the MCP server is running
3. Restart Cursor after making configuration changes
4. Check the Cursor logs for error messages

## Security Best Practices

- Never share your API keys
- Rotate keys regularly
- Use different keys for development and production
- Monitor your API usage and costs
- Set up billing alerts on your API provider accounts
