#  "model": "black-forest-labs/FLUX.1-schnell",
#  "model": "stabilityai/stable-diffusion-3-5-large",
MODEL="black-forest-labs/FLUX.1-schnell"
PROMPT="【古代.唐朝】苍茫意境 大漠孤烟直，长河落日圆"
curl --request POST \
  --url https://api.siliconflow.cn/v1/images/generations \
  --header "Authorization: Bearer $OPENAI_API_KEY" \
  --header 'Content-Type: application/json' \
  --data '{
  "model": "black-forest-labs/FLUX.1-schnell",
  "prompt": "【古代.唐朝】苍茫意境 大漠孤烟直，长河落日圆",
  "image_size": "768x512",
  "batch_size": 1,
  "seed": 4999999999,
  "num_inference_steps": 20,
  "guidance_scale": 7.5,
  "prompt_enhancement": true
}' | jq .images[0].url
