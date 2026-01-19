cd src

python agent_base.py \
    --is_api \
    --stuck_steps 50 \
    --models gpt-4o \
    --games game3-2-hard \
    --max_steps 4000 \
    --memory 10 \
    --use_cot \
    --overwrite \
    --stuck_behavior help \
    --output_suffix base_test_1_1