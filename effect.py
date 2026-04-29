from PIL import Image
import sys

def chromatic_aberration(img, red_shift=(-8, -4), blue_shift=(8, 4)):
    """
    对 PIL 图片施加色散效果。
    red_shift: 红色通道偏移 (x, y)
    blue_shift: 蓝色通道偏移 (x, y)
    返回处理后的新图片。
    """
    # 分离通道
    r, g, b = img.split()
    
    # 偏移红色通道
    r = r.transform(img.size, Image.AFFINE, (1, 0, red_shift[0], 0, 1, red_shift[1]))
    # 偏移蓝色通道
    b = b.transform(img.size, Image.AFFINE, (1, 0, blue_shift[0], 0, 1, blue_shift[1]))
    # 绿色不动
    
    # 合并回去
    return Image.merge("RGB", (r, g, b))

# --- 程序入口 ---
if __name__ == "__main__":
    # 加载图片（假设 input.jpg 在同一文件夹下）
    try:
        original = Image.open("input.jpg").convert("RGB")
    except FileNotFoundError:
        print("错误：找不到 input.jpg，请把图片放到脚本所在文件夹。")
        sys.exit(1)
    
    print(f"图片尺寸：{original.size}")
    
    # 应用色散（你可以改这两个偏移元组，值和之前 C++ 的意义一样）
    result = chromatic_aberration(
        original,
        red_shift=(-6, -3),   # 红色向左上偏移
        blue_shift=(6, 3)     # 蓝色向右下偏移
    )
    
    # 保存结果
    result.save("output_aberration.png")
    print("色散图片已保存为 output_aberration.png")
    
    # 用系统默认图片查看器打开，让你立刻看到效果
    result.show()
