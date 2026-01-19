cd src

python agent_creative.py \
    --is_api \
    --stuck_steps 50 \
    --models gpt-4o \
    --games game3-2-easy \
    --max_steps 4000 \
    --memory 10 \
    --use_cot \
    --overwrite \
    --stuck_behavior help \
    --output_suffix test_1_1