# ComfyUI-PainterFLF2V  
### 增强视频动态，让首尾帧丝滑过渡！让首尾帧视频“动”得更自然、更干净！现在你可以用PainterFLF2V来制作顺滑的首尾帧视频，就像这样：
*Enhance video dynamics for smooth transitions between the first and last frames！Make first-last-frame videos move smoother & cleaner，Now you can use PainterFLF2V to create smooth first-and-last-frame videos, just like this:*

---
<table>
  <tr>
    <td><img src="image-6/wan2-2_00004.gif" alt="图1" width="400"></td>
  </tr>
  <tr>
    <td>motion_amplitude=1.3</td>
  </tr>
</table>
## 🎬 简介 | Intro
PainterFLF2V 是对官方 WAN 首尾帧节点的“动态增强升级版”，你可以调节Motion Amplitude的数值，自定义视频的动态增强幅度。 
通过**反向结构斥力**算法，一键消除慢动作与重影，同时保护颜色不失真。  
PainterFLF2V is the "dynamically enhanced upgraded version" of the official WAN first-last frame node. You can adjust the value of Motion Amplitude to customize the dynamic enhancement intensity of the video.  
Using **inverse structural repulsion**, it erases ghosting & sluggish motion while keeping colors intact.

---

<table>
  <tr>
    <td><img src="image-6/1.gif" alt="图1" width="400"></td>
    <td><img src="image-6/2.gif" alt="图2" width="400"></td>
  </tr>
  <tr>
    <td>motion_amplitude=1.3</td>
    <td>motion_amplitude=1.3</td>
  </tr>
</table>

## ✨ 核心亮点 | Highlights
| 功能 | 效果 | Feature | Result |
|---|---|---|---|
| 动态增强幅度 | 1.0→2.0 无级滑杆 | Motion Amplitude | 1.0 (stock) – 2.0 (max boost) |
| 推荐“日常”值 | **1.2~1.3** 动静平衡 | Sweet-spot | **1.2~1.3** for natural yet punchy moves |
| 颜色锁定 | 零偏移 | Color Lock | Zero hue shift |
| 4× 去重影 | 中间帧更清晰 | Ghost Kill | 4× high-freq diff amplification |

---

## 🚀 快速开始 | Quick Start
1. 克隆到 `custom_nodes`  
   ```bash
   git clone https://github.com/princepainter/Comfyui-PainterFLF2V.git
2. 重启 ComfyUI  
   Restart ComfyUI
3. 工作流中把 `PainterFLF2V` 替换掉原生首尾帧节点即可  
   Drop `PainterFLF2V` in place of the stock first-last-frame node.
   ![替换原节点](image-6/QQ20251120153818.jpg)

---

## 🎛️ 参数速查 | Params Cheat-Sheet
| 参数 | 范围 | 推荐 | Tips |
|---|---|---|---|
| motion_amplitude | 1.0 – 2.0 | **1.2~1.3** | 1.0=原版，1.2~1.3=日常，1.5=极客测试 |

---

## 📈 效果对比 | Before vs After
| 场景 | 原版 1.0 | PainterFLF2V 1.3 |
|---|---|---|
| 人物转身 | 慢半拍 / 残影 | 干净利落 / 动作饱满 |
| 风景推拉 | 色块拖尾 | 线条清晰 / 颜色稳定 |

---

## 📜 许可证 | License
[MIT](./LICENSE) – 随意商用 & 魔改，点个⭐ 就好 :)  
Feel free to commercialize & fork; just give us a star ⭐
```
