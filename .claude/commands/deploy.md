Prepare the AMD MI300X deployment bundle (fallback path).

1. Verify `data/processed/{train,val,test}/{images,masks}` exist with expected counts (999/963).
2. Run (PowerShell): `tar -czf terratwin_deployment.tar.gz --exclude="__pycache__" --exclude="*.pyc" --exclude="terratwin_deployment.tar.gz" src data/processed requirements.txt environment.yml CONTEXT.md`
3. Verify: `tar -tzf terratwin_deployment.tar.gz | head -30` lists `src/...` and `data/processed/...`; `ls -lh terratwin_deployment.tar.gz` shows > 1 GB.
4. Print the exact SCP + extract + train commands the user runs on the cloud (placeholder `$HOST` / `$USER`):
   - `scp terratwin_deployment.tar.gz $USER@$HOST:~/`
   - `ssh $USER@$HOST`
   - `tar -xzf terratwin_deployment.tar.gz`
   - `pip install --index-url https://download.pytorch.org/whl/rocm6.2 torch torchvision`
   - `pip install -r requirements.txt`
   - `python src/stage1_extraction/train_unet.py --data-dir ./data/processed --ckpt-dir ./models --epochs 15 --batch-size 8`
5. Note: on Linux the paths become relative (`./data/processed/...`) because of the `--data-dir` flag added in Phase A. The first run downloads `timm` ImageNet weights (~150 MB) — needs internet on the cloud box.
