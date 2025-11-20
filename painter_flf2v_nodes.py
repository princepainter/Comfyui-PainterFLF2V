import torch
import comfy.model_management as mm
import comfy.utils
import node_helpers
import torch.nn.functional as F
from comfy_api.latest import io, ComfyExtension
from typing_extensions import override

class PainterFLF2V(io.ComfyNode):
    """
    PainterFLF2V boosts first-last frame motion with inverse structural repulsion.
    PainterFLF2V: Dynamically enhances the original first-last frame node, allowing you to customize the dynamic enhancement intensity.
    Now you can create first-last-frame videos with smoother, more natural motion.
    
    """

    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="PainterFLF2V",
            category="conditioning/video_models",
            inputs=[
                io.Conditioning.Input("positive"),
                io.Conditioning.Input("negative"),
                io.Vae.Input("vae"),
                io.Int.Input("width", default=832, min=16, max=4096, step=16),
                io.Int.Input("height", default=480, min=16, max=4096, step=16),
                io.Int.Input("length", default=81, min=1, max=4096, step=4),
                io.Int.Input("batch_size", default=1, min=1, max=4096),
                # 修改：限制范围 1.0 - 2.0
                io.Float.Input("motion_amplitude", default=1.0, min=1.0, max=2.0, step=0.05, 
                               tooltip="1.0=官方原版，2.0=极速动态(消除慢动作)"),
                io.ClipVisionOutput.Input("clip_vision_start_image", optional=True),
                io.ClipVisionOutput.Input("clip_vision_end_image", optional=True),
                io.Image.Input("start_image", optional=True),
                io.Image.Input("end_image", optional=True),
            ],
            outputs=[
                io.Conditioning.Output(display_name="positive"),
                io.Conditioning.Output(display_name="negative"),
                io.Latent.Output(display_name="latent"),
            ],
        )

    @classmethod
    def execute(cls, positive, negative, vae, width, height, length, batch_size,
                motion_amplitude=1.0,
                start_image=None, end_image=None,
                clip_vision_start_image=None, clip_vision_end_image=None) -> io.NodeOutput:

        spacial_scale = vae.spacial_compression_encode()
        latent_frames = ((length - 1) // 4) + 1
        
        # 初始化 Latent
        latent = torch.zeros([batch_size, vae.latent_channels, latent_frames, height // spacial_scale, width // spacial_scale], 
                             device=mm.intermediate_device())

        # 1. 图像预处理
        if start_image is not None:
            start_image = comfy.utils.common_upscale(
                start_image[:length].movedim(-1, 1), width, height, "bilinear", "center"
            ).movedim(1, -1)
        if end_image is not None:
            end_image = comfy.utils.common_upscale(
                end_image[-length:].movedim(-1, 1), width, height, "bilinear", "center"
            ).movedim(1, -1)

        # 2. 构建基准 Latent
        # [官方基准]: 中间填 0.5 (灰色)
        official_image = torch.ones((length, height, width, 3), device=mm.intermediate_device()) * 0.5
        mask = torch.ones((1, 1, latent_frames * 4, height // spacial_scale, width // spacial_scale), device=mm.intermediate_device())

        if start_image is not None:
            official_image[:start_image.shape[0]] = start_image
            mask[:, :, :start_image.shape[0] + 3] = 0.0
        if end_image is not None:
            official_image[-end_image.shape[0]:] = end_image
            mask[:, :, -end_image.shape[0]:] = 0.0
            
        official_latent = vae.encode(official_image[:, :, :, :3])

        # [线性基准]: 用来计算"慢动作"特征
        if start_image is not None and end_image is not None and length > 2:
            start_l = official_latent[:, :, 0:1]
            end_l   = official_latent[:, :, -1:]
            t = torch.linspace(0.0, 1.0, official_latent.shape[2], device=official_latent.device).view(1, 1, -1, 1, 1)
            linear_latent = start_l * (1 - t) + end_l * t
        else:
            linear_latent = official_latent 

        # ==================== 核心算法：反向结构斥力 (Inverse Structural Repulsion) ====================
        
        # 仅当 amplitude > 1.0 时触发增强逻辑
        if length > 2 and motion_amplitude > 1.001 and start_image is not None and end_image is not None:
            
            # A. 计算差异向量 (Anti-Ghost Vector)
            # diff = 官方(灰) - 线性(PPT)
            # 这个向量实际上包含了"去除PPT重影"所需的信息
            diff = official_latent - linear_latent
            
            # B. 频率分离 (绝对保护颜色)
            h, w = diff.shape[-2], diff.shape[-1]
            # 提取低频 (颜色)
            low_freq_diff = F.interpolate(diff.view(-1, vae.latent_channels, h, w), 
                                         size=(h // 8, w // 8), mode='area')
            low_freq_diff = F.interpolate(low_freq_diff, size=(h, w), mode='bilinear')
            low_freq_diff = low_freq_diff.view_as(diff)
            
            # 提取高频 (结构/重影)
            high_freq_diff = diff - low_freq_diff
            
            # C. 暴力增强系数计算
            # 将 1.0-2.0 的输入映射到 0.0-4.0 的内部强度
            # 你觉得之前不明显，是因为系数太小。现在 2.0 对应 4倍 强度。
            boost_scale = (motion_amplitude - 1.0) * 4.0
            
            # D. 最终合成
            # Base: 官方 Latent (保证 1.0 时一致)
            # Boost: 高频差异 * 强度
            # 注意：我们完全丢弃了 low_freq_diff 的增强，这意味着颜色永远不动。
            # 我们只把 high_freq_diff (反向去除重影) 疯狂放大。
            
            concat_latent_image = official_latent + (high_freq_diff * boost_scale)
            
        else:
            # 1.0 模式：直接输出官方 Latent
            concat_latent_image = official_latent
            
        # ========================================================================================

        # Mask 格式调整
        mask = mask.view(1, mask.shape[2] // 4, 4, mask.shape[3], mask.shape[4]).transpose(1, 2)

        # 注入 Conditioning
        positive = node_helpers.conditioning_set_values(
            positive, {"concat_latent_image": concat_latent_image, "concat_mask": mask}
        )
        negative = node_helpers.conditioning_set_values(
            negative, {"concat_latent_image": concat_latent_image, "concat_mask": mask}
        )

        # Clip Vision (不变)
        clip_vision_output = None
        if clip_vision_start_image is not None:
            clip_vision_output = clip_vision_start_image

        if clip_vision_end_image is not None:
            if clip_vision_output is not None:
                states = torch.cat([clip_vision_output.penultimate_hidden_states, 
                                   clip_vision_end_image.penultimate_hidden_states], dim=-2)
                clip_vision_output = comfy.clip_vision.Output()
                clip_vision_output.penultimate_hidden_states = states
            else:
                clip_vision_output = clip_vision_end_image

        if clip_vision_output is not None:
            positive = node_helpers.conditioning_set_values(positive, {"clip_vision_output": clip_vision_output})
            negative = node_helpers.conditioning_set_values(negative, {"clip_vision_output": clip_vision_output})

        out_latent = {"samples": latent}
        return io.NodeOutput(positive, negative, out_latent)


class PainterFLF2VExtension(ComfyExtension):
    @override
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        return [PainterFLF2V]

async def comfy_entrypoint() -> PainterFLF2VExtension:
    return PainterFLF2VExtension()

NODE_CLASS_MAPPINGS = {"PainterFLF2V": PainterFLF2V}
NODE_DISPLAY_NAME_MAPPINGS = {"PainterFLF2V": "PainterFLF2V"}
