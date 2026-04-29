#define _CRT_SECURE_NO_WARNINGS
#define STB_IMAGE_IMPLEMENTATION
#include "stb_image.h"
#define STB_IMAGE_WRITE_IMPLEMENTATION
#include "stb_image_write.h"
#include <iostream>
#include <algorithm>  // min/max

// 色散函数
unsigned char* chromatic_aberration(
    const unsigned char* src,
    int width, int height, int channels,
    int shift_x = -4,  // 红通道X偏移（负=左）
    int shift_y = -2,  // 红通道Y偏移（负=上）
    int blue_shift_x = 4,  // 蓝通道X偏移（正=右）
    int blue_shift_y = 2   // 蓝通道Y偏移（正=下）
) {
    // 分配输出图像内存
    unsigned char* dst = new unsigned char[width * height * channels];

    // 遍历输出图像的每一个像素
    for (int y = 0; y < height; ++y) {
        for (int x = 0; x < width; ++x) {
            int dst_idx = (y * width + x) * channels;  // 输出像素索引

            // --- 绿色通道：直接从原图同位置取 ---
            int g_sx = x;
            int g_sy = y;

            // --- 红色通道：偏移取样 ---
            int r_sx = x - shift_x;  // 注意符号：因为我们定义的偏移是“红移”，取原图像素时要反过来
            int r_sy = y - shift_y;

            // --- 蓝色通道：偏移取样 ---
            int b_sx = x - blue_shift_x;
            int b_sy = y - blue_shift_y;

            // 边界检查，防止越界（越界就用边缘像素）
            auto clamp = [width, height](int val, int max_val) -> int {
                if (val < 0) return 0;
                if (val >= max_val) return max_val - 1;
                return val;
                };

            r_sx = clamp(r_sx, width);
            r_sy = clamp(r_sy, height);
            g_sx = clamp(g_sx, width);
            g_sy = clamp(g_sy, height);
            b_sx = clamp(b_sx, width);
            b_sy = clamp(b_sy, height);

            // 计算源像素索引
            int src_r_idx = (r_sy * width + r_sx) * channels;
            int src_g_idx = (g_sy * width + g_sx) * channels;
            int src_b_idx = (b_sy * width + b_sx) * channels;

            // 填充输出像素（假设channels >= 3，即RGB或RGBA）
            dst[dst_idx] = src[src_r_idx];     // R
            dst[dst_idx + 1] = src[src_g_idx + 1]; // G
            dst[dst_idx + 2] = src[src_b_idx + 2]; // B

            // 如果还有 alpha 通道，原样复制
            if (channels == 4) {
                dst[dst_idx + 3] = src[src_g_idx + 3]; // A 不偏移
            }
        }
    }
    return dst;
}

int main() {
    int width, height, channels;
    unsigned char* img = stbi_load("input.jpg", &width, &height, &channels, 0);

    if (!img) {
        std::cout << "错误：无法加载 input.jpg，请确认文件存在。" << std::endl;
        return -1;
    }

    std::cout << "已加载图片：" << width << " x " << height
        << "，通道数：" << channels << std::endl;

    // 调用色散效果（可以自己改偏移值）
    int red_shift_x = -5;   // 红色左移像素
    int red_shift_y = -3;   // 红色上移像素
    int blue_shift_x = 5;   // 蓝色右移像素
    int blue_shift_y = 3;   // 蓝色下移像素

    unsigned char* result = chromatic_aberration(
        img, width, height, channels,
        red_shift_x, red_shift_y,
        blue_shift_x, blue_shift_y
    );

    // 保存结果
    stbi_write_png("output_aberration.png", width, height, channels,
        result, width * channels);

    std::cout << "色散效果已生成：output_aberration.png" << std::endl;

    // 释放内存
    stbi_image_free(img);
    delete[] result;

    return 0;
}