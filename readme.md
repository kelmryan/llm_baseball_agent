1. export HUGGING_FACE_LOGIN
2. hf auth login --token $HUGGINGFACE_HUB_TOKEN --add-to-git-credential 
3. The variable is in  the env
4. huggingface-cli download mistralai/Mistral-7B-Instruct-v0.3 --local-dir ./misteral