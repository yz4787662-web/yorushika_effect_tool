from PIL import Image
import sys

def black_to_transparent(input_path, output_path, threshold=30):
    """
    将接近黑色的像素变为透明。
    threshold: 判断黑色的阈值（0~255），越小越严格（只有纯黑才透明）。
    """
    img = Image.open(input_path).convert("RGBA")
    data = img.getdata()
    new_data = []
    for item in data:
        r, g, b, a = item
        # 如果红绿蓝都小于阈值，判定为“黑色”，将其透明度设为0
        if r < threshold and g < threshold and b < threshold:
            new_data.append((r, g, b, 0))  # 完全透明
        else:
            new_data.append((r, g, b, a))  # 保留原样
    img.putdata(new_data)
    img.save(output_path, "PNG")
    print(f"已保存透明PNG：{output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法：python make_transparent.py 输入.jpg 输出.png [阈值(默认30)]")
        sys.exit(1)
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    thres = 30
    if len(sys.argv) > 3:
        thres = int(sys.argv[3])
    black_to_transparent(input_file, output_file, thres)