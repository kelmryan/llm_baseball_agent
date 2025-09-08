# Starting the LLM
## log into hugging face
1.
```
pip install --upgrade huggingface_hub
huggingface-cli login

```
1. Enter token
1. Run `huggingface-cli download mistralai/Mistral-7B-Instruct-v0.3`
1. The following files should be at /mistral_models/7B-Instruct-v0.3
`Modelfile  config.json  consolidated.safetensors  params.json  tokenizer.model.v3  tokenizer_config.json`
1.
``` 
# Check if your GGUF file is still there
ls -la *.gguf

# Recreate the Modelfile
cat << EOF > Modelfile
FROM /home/kryan/mistral_gguf/mistral-7b-instruct-v0.3.Q4_K_M.gguf

TEMPLATE """<s>[INST] {{ .Prompt }} [/INST]"""
PARAMETER temperature 0.7
PARAMETER num_ctx 4096
EOF

# Recreate the model
ollama create mistral-local -f Modelfile
```
1. Run `ollama create mistral-local -f Modelfile`