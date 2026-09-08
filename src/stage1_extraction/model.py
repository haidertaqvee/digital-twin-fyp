"""
U-Net for binary building-footprint segmentation.

Takes the 3-channel tensors produced by SpaceNetDataset (already normalized
against the fixed dataset-wide NORM_MAX) and returns raw logits at the same
spatial size as the input. Logits, not probabilities -- the training loop uses
BCEWithLogitsLoss, which is numerically safer than sigmoid + BCE.

Handles odd input sizes. SpaceNet SN2 Vegas tiles are 650x650, which is not
divisible by 32, so four rounds of max-pooling produce feature maps whose sizes
do not line up with their skip connections (650 -> 325 -> 162 -> 81 -> 40).
`Up` pads the upsampled tensor to match its skip before concatenating, so any
input size works without cropping the tiles.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class DoubleConv(nn.Module):
    """(conv -> BN -> ReLU) x 2, the standard U-Net building block."""

    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
        )

    def forward(self, x):
        return self.block(x)


class Down(nn.Module):
    """Halve spatial size, then DoubleConv."""

    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.pool_conv = nn.Sequential(
            nn.MaxPool2d(2),
            DoubleConv(in_channels, out_channels),
        )

    def forward(self, x):
        return self.pool_conv(x)


class Up(nn.Module):
    """Upsample, pad to match the skip connection, concatenate, then DoubleConv."""

    def __init__(self, in_channels, out_channels, bilinear=True):
        super().__init__()
        if bilinear:
            # Bilinear upsampling has no parameters, so it trains faster and
            # overfits less on a dataset this small (~673 training tiles).
            self.up = nn.Upsample(scale_factor=2, mode="bilinear", align_corners=True)
            self.conv = DoubleConv(in_channels, out_channels)
        else:
            self.up = nn.ConvTranspose2d(
                in_channels // 2, in_channels // 2, kernel_size=2, stride=2
            )
            self.conv = DoubleConv(in_channels, out_channels)

    def forward(self, x, skip):
        x = self.up(x)

        # Odd input sizes leave the upsampled tensor 1px short of its skip.
        diff_y = skip.size(2) - x.size(2)
        diff_x = skip.size(3) - x.size(3)
        if diff_y != 0 or diff_x != 0:
            x = F.pad(
                x,
                [diff_x // 2, diff_x - diff_x // 2, diff_y // 2, diff_y - diff_y // 2],
            )

        return self.conv(torch.cat([skip, x], dim=1))


class UNet(nn.Module):
    """
    Args:
        in_channels: 3 for RGB-PanSharpen bands 1-3.
        out_channels: 1 -- single logit per pixel, buildings vs. background.
        base_channels: width of the first encoder stage; each stage doubles it.
            64 is the canonical U-Net width. Drop to 32 if VRAM is tight.
        bilinear: bilinear upsampling (default) vs. learned transposed convs.
    """

    def __init__(self, in_channels=3, out_channels=1, base_channels=64, bilinear=True):
        super().__init__()
        c = base_channels
        factor = 2 if bilinear else 1

        self.inc = DoubleConv(in_channels, c)
        self.down1 = Down(c, c * 2)
        self.down2 = Down(c * 2, c * 4)
        self.down3 = Down(c * 4, c * 8)
        self.down4 = Down(c * 8, c * 16 // factor)

        self.up1 = Up(c * 16, c * 8 // factor, bilinear)
        self.up2 = Up(c * 8, c * 4 // factor, bilinear)
        self.up3 = Up(c * 4, c * 2 // factor, bilinear)
        self.up4 = Up(c * 2, c, bilinear)
        self.outc = nn.Conv2d(c, out_channels, kernel_size=1)

    def forward(self, x):
        x1 = self.inc(x)
        x2 = self.down1(x1)
        x3 = self.down2(x2)
        x4 = self.down3(x3)
        x5 = self.down4(x4)

        x = self.up1(x5, x4)
        x = self.up2(x, x3)
        x = self.up3(x, x2)
        x = self.up4(x, x1)
        return self.outc(x)


if __name__ == "__main__":
    # Shape check at the real tile size -- this is the case that breaks a
    # naive U-Net, so it is the one worth asserting.
    model = UNet()
    n_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Trainable parameters: {n_params:,}")

    for size in (650, 512, 256):
        dummy = torch.randn(1, 3, size, size)
        with torch.no_grad():
            out = model(dummy)
        status = "OK" if out.shape[-2:] == dummy.shape[-2:] else "SIZE MISMATCH"
        print(f"  {size}x{size}: in {tuple(dummy.shape)} -> out {tuple(out.shape)}  [{status}]")
