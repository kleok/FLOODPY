import torch
import torch.nn as nn
import einops

class Decoder(nn.Module):
    def __init__(self, input_size, output_channels):
        super(Decoder, self).__init__()

        # Deconvolutional layers
        self.deconv1 = nn.ConvTranspose2d(1024, 128, kernel_size=4, stride=2, padding=1)
        self.relu = nn.ReLU()
        self.up = nn.Upsample(scale_factor=2)

        self.deconv2 = nn.ConvTranspose2d(128, 64, kernel_size=4, stride=2, padding=1)
        self.deconv3 = nn.ConvTranspose2d(
            64, output_channels, kernel_size=4, stride=2, padding=1
        )

    def forward(self, x):
        x = self.deconv1(x)
        x = self.relu(x)

        x = self.up(x)

        x = self.deconv2(x)

        x = self.relu(x)

        x = self.deconv3(x)

        return x


class FinetunerSegmentation(nn.Module):
    def __init__(self, encoder, configs=None, pool=False):
        super().__init__()
        self.configs = configs
        self.model = encoder
        self.model.pool = pool
        self.pool = pool
        if not self.pool:
            if configs["mlp"]:
                self.head = nn.Sequential(
                    nn.Conv2d(encoder.mlp_head.in_features, 512, kernel_size=1),
                    nn.ReLU(),
                    nn.Conv2d(512, configs["num_classes"], kernel_size=1),
                )
            elif configs["decoder"]:
                self.head = Decoder(
                    encoder.mlp_head.in_features, configs["num_classes"]
                )
            else:
                self.head = nn.Conv2d(
                    encoder.mlp_head.in_features, configs["num_classes"], kernel_size=1
                )
        else:
            self.head = nn.Linear(
                encoder.mlp_head.in_features,
                configs["num_classes"] * configs["image_size"] * configs["image_size"],
            )
        self.model.mlp_head = nn.Identity()

    def forward(self, x):
        x = x
        img_size = 224
        GS = img_size // self.configs["finetuning_patch_size"]
        x = self.model(x)

        if self.pool == False:
            x = einops.rearrange(x, "b (h w) c -> b (c) h w", h=GS, w=GS)
            if not self.configs["decoder"]:
                upsample = nn.Upsample(size=(img_size, img_size), mode="bilinear")

                x = upsample(x)

        x = self.head(x)
        return x