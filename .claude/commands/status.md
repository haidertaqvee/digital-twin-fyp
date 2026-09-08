Summarize the current state of the TerraTwin project:

- Read CONTEXT.md for mission, stack, and next steps.
- Check `data/processed/{train,val,test}/{images,masks}` counts (999/963 expected, 673 train masks).
- Whether `models/` has any checkpoints (presence/size of `unet_resnet34_best.pth` or `last.pt`).
- Whether `envs/digital-twin/python.exe` can import `segmentation_models_pytorch==0.5.0` and whether `torch.cuda.is_available()` is true.
- Deadline Sept 15, 2026 11:00 PM EDT — say how many days remain.
- Any `git status --short` surprises (untracked or uncommitted work).

Present it as a short status paragraph: which stage we're in, what's still blocking, and what to run next.
